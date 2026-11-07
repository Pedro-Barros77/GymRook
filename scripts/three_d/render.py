"""Build, save and render fully articulated Blender exercise scenes.

blender --background --python scripts/three_d/render.py -- --exercise pec-deck --preview
Remove --preview to render the complete 72-frame, 24-fps cycle.
"""
from pathlib import Path
import sys
import argparse
import json
import math
import hashlib
import time
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from human import create_human
from equipment import build_equipment
from poses import exercise_pose, phase_at, validate_joints


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exercise', choices=['pec-deck', 'incline-dumbbell-press', 'push-up', 'reverse-cable-curl'], required=True)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--size', type=int, default=512)
    parser.add_argument('--samples', type=int, default=32)
    parser.add_argument('--engine', choices=['eevee', 'cycles'], default='eevee')
    parser.add_argument('--frames', default='')
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def material(name, color, roughness=.7):
    item = bpy.data.materials.new(name)
    item.use_nodes = True
    node = item.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Roughness'].default_value = roughness
    return item


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def light(name, position, power, size, target=(0, .1, 1)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)
    return obj


def studio(exercise, args):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if args.engine == 'eevee' else 'CYCLES'
    if args.engine == 'cycles':
        scene.cycles.samples = args.samples
        scene.cycles.use_denoising = True
        try:
            preferences = bpy.context.preferences.addons['cycles'].preferences
            preferences.compute_device_type = 'OPTIX'
            preferences.get_devices()
            for device in preferences.devices:
                device.use = device.type != 'CPU'
            scene.cycles.device = 'GPU'
        except Exception as error:
            print('GPU selection:', error, flush=True)
    elif hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = args.samples
    scene.render.resolution_x = scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.fps = 24
    scene.render.fps_base = 1.0
    scene.frame_start, scene.frame_end = 1, 72
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.image_settings.compression = 20
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    world = bpy.data.worlds.new('Fixed warm studio environment')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.78, .77, .72, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .55
    scene.world = world
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = 'Fixed seamless studio floor'
    floor.data.materials.append(material('Warm ivory floor', (.77, .75, .69), .82))
    light('Fixed large key softbox', (3, 4, 5.5), 850, 4)
    light('Fixed front fill softbox', (-3.5, 2, 3.4), 500, 3.5)
    light('Fixed rear rim softbox', (0, -3, 4.5), 700, 3)
    camera_data = bpy.data.cameras.new('Fixed orthographic three-quarter camera')
    camera = bpy.data.objects.new('Fixed orthographic three-quarter camera', camera_data)
    bpy.context.collection.objects.link(camera)
    if exercise == 'pec-deck':
        camera.location = (3.3, 5.4, 2.65)
        target, scale = (0, .05, 1.02), 2.45
    elif exercise == 'reverse-cable-curl':
        camera.location = (4.7, 3.4, 2.55)
        target, scale = (0, .57, 1.02), 2.65
    elif exercise == 'incline-dumbbell-press':
        camera.location = (4.8, 4.1, 2.6)
        target, scale = (0, -.08, .87), 2.25
    else:
        camera.location = (4.4, 2.8, 2.2)
        target, scale = (0, -.04, .50), 2.25
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = scale
    camera_data.lens = 55
    aim(camera, target)
    scene.camera = camera
    return scene, camera


def serial(value):
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (Vector, tuple, list)):
        return [serial(item) for item in value]
    if isinstance(value, float):
        return round(value, 8)
    return value


def flatten(matrix):
    return [round(float(item), 8) for row in matrix for item in row]


def main():
    args = arguments()
    started = time.monotonic()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene, camera = studio(args.exercise, args)
    equipment = build_equipment(args.exercise)
    human = create_human()
    low, options = exercise_pose(args.exercise, 0, equipment)
    equipment.calibrate_rest(low)
    records = []
    # Persist actual animation curves, not just a static scene plus render script.
    for frame in range(1, 73):
        scene.frame_set(frame)
        phase = phase_at(frame)
        joints, options = exercise_pose(args.exercise, phase, equipment)
        errors = validate_joints(joints)
        human.pose(joints, **options)
        equipment.update(phase, joints)
        human.keyframe(frame)
        equipment.keyframe(frame)
        records.append({'frame': frame, 'phase': phase, 'joints': serial(joints),
                        'equipment': serial(equipment.state), 'boneLengthErrors': errors,
                        'cameraMatrix': flatten(camera.matrix_world),
                        'equipmentRootMatrix': flatten(equipment.root.matrix_world)})
    scene.frame_set(1)
    scene['gymrook_exercise'] = args.exercise
    scene['gymrook_fps'] = 24
    scene['gymrook_frame_count'] = 72
    scene['gymrook_motion'] = 'Periodic cosine; fixed geometry/materials/camera; no independent image generation'
    scenes = ROOT / 'assets/3d/scenes'
    scenes.mkdir(parents=True, exist_ok=True)
    blend = scenes / (args.exercise + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    out = ROOT / 'output/3d' / args.exercise
    frames_dir = out / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)
    manifest = {'id': args.exercise, 'blender': bpy.app.version_string, 'fps': 24, 'frameCount': 72,
                'resolution': [args.size, args.size], 'engine': scene.render.engine,
                'scene': blend.relative_to(ROOT).as_posix(),
                'sceneSha256': hashlib.sha256(blend.read_bytes()).hexdigest(),
                'humanVertexCount': sum(len(obj.data.vertices) for obj in human.objects if obj.type == 'MESH'),
                'humanBoneCount': len(human.armature.pose.bones), 'frames': records}
    (out / 'motion.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    if args.frames:
        selected = [int(frame) for frame in args.frames.split(',')]
    else:
        selected = [1, 19, 37] if args.preview else list(range(1, 73))
    for frame in selected:
        scene.frame_set(frame)
        # The saved native keyframes drive all rendered poses and equipment.
        scene.render.filepath = str(frames_dir / f'frame_{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'GYMROOK {args.exercise} frame {frame}/72 ready; elapsed {time.monotonic()-started:.1f}s', flush=True)
    print('GYMROOK_DONE ' + args.exercise, flush=True)


if __name__ == '__main__':
    main()
