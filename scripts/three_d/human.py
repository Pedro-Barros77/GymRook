"""MakeHuman CC0 athlete with a real weighted deformation armature.

The fixed human topology, male/muscular morphs, source weights and skeleton are
MakeHuman core assets (CC0). This small Blender adapter is project code.
World axes: X anatomical left, Y forward, Z up; units are metres.

Public API:
    athlete = create_human()
    athlete.pose(world_joints, grip=1, hand_roll={'left': 0, 'right': 0})
    athlete.keyframe(frame)
Optional `left_hand`/`right_hand` points locate the middle of each grip, and
`palm_normals={'left': (0,0,-1), ...}` provides explicit palm orientation.
"""
from pathlib import Path
import json
import math
import re
from collections import defaultdict

import bpy
from mathutils import Matrix, Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets' / '3d' / 'human'
HEIGHT = 1.80
REST_JOINTS = json.loads((ASSETS / 'rest-joints.json').read_text(encoding='utf-8'))
SEGMENT_LENGTHS = {'upperarm': 0.2641399345, 'forearm': 0.2771257280,
                   'thigh': 0.4377518023, 'shin': 0.4620636996}


def _asset_data():
    vertices, groups, group = [], defaultdict(list), ''
    for line in (ASSETS / 'base.obj').read_text(encoding='utf-8').splitlines():
        if line.startswith('v '):
            vertices.append(Vector(map(float, line.split()[1:4])))
        elif line.startswith('g '):
            group = line[2:].strip()
        elif line.startswith('f '):
            groups[group].append(tuple(int(piece.split('/')[0]) - 1 for piece in line.split()[1:]))
    factors = {'caucasian-male-young.target': .55, 'african-male-young.target': .30,
               'asian-male-young.target': .15,
               'universal-male-young-maxmuscle-averageweight.target': .8,
               'universal-male-young-averagemuscle-averageweight.target': .2,
               'male-young-maxmuscle-averageweight-idealproportions.target': .6}
    for side in ('l', 'r'):
        for part in ('upperarm', 'upperarm-shoulder', 'lowerarm', 'upperleg', 'lowerleg'):
            factors[f'{side}-{part}-muscle-incr.target'] = .25
    for name, factor in factors.items():
        for line in (ASSETS / name).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            values = line.split()
            vertices[int(values[0])] += factor * Vector(map(float, values[1:4]))
    body_ids = {index for face in groups['body'] for index in face}
    ground = min(vertices[i].y for i in body_ids)
    scale = HEIGHT / (max(vertices[i].y for i in body_ids) - ground)
    vertices = [Vector((v.x * scale, v.z * scale, (v.y - ground) * scale)) for v in vertices]
    skeleton = json.loads((ASSETS / 'default.mhskel').read_text(encoding='utf-8'))
    weights = json.loads((ASSETS / 'default_weights.mhw').read_text(encoding='utf-8'))['weights']
    return vertices, groups, skeleton, weights


def _material(name, color, roughness=.65, subsurface=0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    if 'Subsurface Weight' in shader.inputs:
        shader.inputs['Subsurface Weight'].default_value = subsurface
    return material


def _frame(longitudinal, normal):
    y = Vector(longitudinal).normalized()
    z = Vector(normal) - y * Vector(normal).dot(y)
    if z.length < 1e-6:
        z = y.cross(Vector((0, 1, 0)))
        if z.length < 1e-6:
            z = y.cross(Vector((1, 0, 0)))
    z.normalize()
    x = y.cross(z).normalized()
    z = x.cross(y).normalized()
    return Matrix((x, y, z)).transposed()


def _transform(a, b, c, d, normal_a, normal_b, roll=0):
    rotation = _frame(Vector(d) - Vector(c), normal_b) @ _frame(Vector(b) - Vector(a), normal_a).transposed()
    if roll:
        rotation = Quaternion((Vector(d) - Vector(c)).normalized(), roll).to_matrix() @ rotation
    return Matrix.Translation(Vector(c)) @ rotation.to_4x4() @ Matrix.Translation(-Vector(a))


def _rotation_about(point, axis, angle):
    return Matrix.Translation(point) @ Quaternion(axis.normalized(), angle).to_matrix().to_4x4() @ Matrix.Translation(-point)


class Human:
    def __init__(self, name='Athlete'):
        self.name = name
        self.collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.collection)
        self.vertices, self.groups, self.skeleton, self.weights = _asset_data()
        self.rest_joints = {key: Vector(value) for key, value in REST_JOINTS.items()}
        self.rest = self.rest_joints
        self.objects = []
        self._head = {}
        self._tail = {}
        for bone, spec in self.skeleton['bones'].items():
            self._head[bone] = self._joint(spec['head'])
            self._tail[bone] = self._joint(spec['tail'])
        self._make_armature()
        self.skin = _material(name + '_WarmTanSkin', (.34, .155, .074), .64, .035)
        self.hair = _material(name + '_ShortDarkHair', (.015, .009, .006), .92)
        self.fabric = _material(name + '_CharcoalShorts', (.025, .031, .039), .88)
        self.shoe_mat = _material(name + '_BlackTrainer', (.018, .023, .029), .72)
        self.sole_mat = _material(name + '_TrainerSole', (.63, .65, .63), .78)
        self.eye_white = _material(name + '_EyeWhite', (.76, .75, .69), .34)
        self.eye_iris = _material(name + '_BrownIris', (.055, .028, .012), .30)
        self.eye_pupil = _material(name + '_Pupil', (.004, .003, .002), .24)
        # The trainer fully covers the foot. Removing the hidden foot surface
        # avoids naked toes breaking through its shell after ankle deformation.
        body_faces = []
        for face in self.groups['body']:
            center = sum((self.vertices[i] for i in face), Vector()) / len(face)
            if center.z < .112 and abs(center.x) > .12:
                continue
            body_faces.append(face)
        self.body = self._source_mesh(name + '_Body', body_faces, [self.skin, self.hair], subdivisions=1)
        # Short cropped hair follows the same skinned scalp vertices, so it never
        # floats or changes texture between frames.
        for polygon in self.body.data.polygons:
            center = sum((self.body.data.vertices[i].co for i in polygon.vertices), Vector()) / len(polygon.vertices)
            if center.z > 1.747 or (center.z > 1.69 and center.y < .031):
                polygon.material_index = 1
        self._make_shorts()
        self._make_shoes()
        self._make_eyes()
        self.grip_centers, self.palm_centers, self.palm_normals = {}, {}, {}
        for side, suffix in [('left', 'L'), ('right', 'R')]:
            wrist = self.rest_joints[f'{side}_wrist']
            index = self._head[f'finger2-1.{suffix}']
            pinky = self._head[f'finger5-1.{suffix}']
            middle = self._head[f'finger3-1.{suffix}']
            normal = (middle - wrist).cross(index - pinky).normalized()
            if normal.dot(self.rest_joints['pelvis'] - wrist) < 0:
                normal.negate()
            # A cylindrical handle lies inside the concavity of a closed fist,
            # rather than on the plane of the metacarpal bones. This offset puts
            # the bar between palm and curled phalanges instead of above them.
            self.palm_centers[side] = wrist.lerp(middle, .78)
            center = self.palm_centers[side] + normal * .030
            self.grip_centers[side] = center
            self.palm_normals[side] = normal
        self.pose(self.rest_joints, grip=0)

    def _joint(self, name):
        indices = self.skeleton['joints'][name]
        return sum((self.vertices[i] for i in indices), Vector()) / len(indices)

    def _link(self, obj):
        self.collection.objects.link(obj)
        self.objects.append(obj)
        return obj

    def _make_armature(self):
        data = bpy.data.armatures.new(self.name + '_Skeleton')
        self.armature = self._link(bpy.data.objects.new(self.name + '_Rig', data))
        self.armature.show_in_front = True
        self.armature['asset_license'] = 'MakeHuman core assets: CC0-1.0'
        self.armature['axes'] = 'metres; X anatomical left; Y forward; Z up'
        bpy.context.view_layer.objects.active = self.armature
        self.armature.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        for name in self.skeleton['bones']:
            bone = data.edit_bones.new(name)
            bone.head = self._head[name]
            bone.tail = self._tail[name]
            if (bone.tail - bone.head).length < .00001:
                bone.tail.z += .0001
        for name, spec in self.skeleton['bones'].items():
            if spec.get('parent'):
                data.edit_bones[name].parent = data.edit_bones[spec['parent']]
        bpy.ops.object.mode_set(mode='OBJECT')
        self.armature.select_set(False)
        self._rest_matrices = {bone.name: bone.matrix_local.copy() for bone in data.bones}
        self._order = sorted(self.skeleton['bones'], key=lambda name: len(data.bones[name].parent_recursive))
        for posebone in self.armature.pose.bones:
            posebone.rotation_mode = 'QUATERNION'

    def _bind(self, obj, ids=None, rigid=None):
        if rigid:
            group = obj.vertex_groups.new(name=rigid)
            group.add(list(range(len(obj.data.vertices))), 1, 'REPLACE')
        else:
            remap = {source: index for index, source in enumerate(ids)}
            # The supplied MakeHuman weights also cover the clothing helpers.
            for name, pairs in self.weights.items():
                buckets = defaultdict(list)
                for source, weight in pairs:
                    if source in remap and weight > 0:
                        buckets[weight].append(remap[source])
                if buckets:
                    group = obj.vertex_groups.new(name=name)
                    for weight, indices in buckets.items():
                        group.add(indices, weight, 'REPLACE')
        modifier = obj.modifiers.new('Anatomical skin deformation', 'ARMATURE')
        modifier.object = self.armature
        modifier.use_deform_preserve_volume = True
        return obj

    def _source_mesh(self, name, faces, materials, subdivisions=1, inflate=0):
        ids = sorted({i for face in faces for i in face})
        remap = {source: index for index, source in enumerate(ids)}
        coords = []
        for source in ids:
            point = self.vertices[source].copy()
            if inflate:
                center_x = (1 if point.x >= 0 else -1) * (.11 if point.z < .98 else 0)
                point.x = center_x + (point.x - center_x) * (1 + inflate)
                point.y *= 1 + inflate
            coords.append(point)
        mesh = bpy.data.meshes.new(name + '_Mesh')
        mesh.from_pydata(coords, [], [tuple(remap[i] for i in face) for face in faces])
        mesh.update()
        obj = self._link(bpy.data.objects.new(name, mesh))
        for material in materials:
            mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        self._bind(obj, ids=ids)
        if subdivisions:
            modifier = obj.modifiers.new('Smooth anatomical surface', 'SUBSURF')
            modifier.levels = subdivisions
            modifier.render_levels = subdivisions
        return obj

    def _make_shorts(self):
        faces = []
        for face in self.groups['helper-tights']:
            center = sum((self.vertices[i] for i in face), Vector()) / len(face)
            if .675 < center.z < 1.045 and abs(center.x) < .29:
                faces.append(face)
        self.shorts = self._source_mesh(self.name + '_TrainingShorts', faces, [self.fabric], subdivisions=1, inflate=.065)
        thick = self.shorts.modifiers.new('Cloth hem thickness', 'SOLIDIFY')
        thick.thickness = .0022
        thick.offset = 1

    def _make_shoes(self):
        # Purpose-modelled trainer shells, not coloured individual human toes.
        for side, suffix in [('left', 'L'), ('right', 'R')]:
            ankle = self.rest_joints[f'{side}_ankle']
            toe = self.rest_joints[f'{side}_toe']
            direction = Vector((toe.x - ankle.x, toe.y - ankle.y, 0)).normalized()
            lateral = Vector((direction.y, -direction.x, 0))
            positions = [(-.073, .023, .060), (-.060, .041, .106), (-.018, .051, .121),
                         (.028, .054, .103), (.09, .057, .081), (.151, .056, .061),
                         (.207, .044, .047), (.237, .019, .036)]
            vertices = []
            count = 16
            for distance, width, top in positions:
                for k in range(count):
                    angle = 2 * math.pi * k / count
                    x = width * math.cos(angle)
                    z = .013 + (top - .013) * max(0, math.sin(angle))
                    if math.sin(angle) < 0:
                        z = .013 + .010 * math.sin(angle)
                    point = Vector((ankle.x, ankle.y, 0)) + direction * distance + lateral * x
                    point.z = z
                    vertices.append(point)
            faces = []
            for row in range(len(positions) - 1):
                for k in range(count):
                    faces.append((row * count + k, row * count + (k+1) % count,
                                  (row+1) * count + (k+1) % count, (row+1) * count + k))
            faces += [tuple(range(count - 1, -1, -1)), tuple((len(positions)-1) * count + k for k in range(count))]
            mesh = bpy.data.meshes.new(self.name + '_TrainerMesh.' + suffix)
            mesh.from_pydata(vertices, [], faces)
            mesh.materials.append(self.shoe_mat)
            mesh.materials.append(self.sole_mat)
            obj = self._link(bpy.data.objects.new(self.name + '_Trainer.' + suffix, mesh))
            for polygon in mesh.polygons:
                polygon.use_smooth = True
                if sum(mesh.vertices[i].co.z for i in polygon.vertices) / len(polygon.vertices) < .020:
                    polygon.material_index = 1
            self._bind(obj, rigid='foot.' + suffix)
            sub = obj.modifiers.new('Rounded trainer shell', 'SUBSURF')
            sub.levels = sub.render_levels = 2

    def _ellipsoid(self, name, center, scale, material):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=center)
        obj = bpy.context.object
        obj.name = name
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        self.collection.objects.link(obj)
        self.objects.append(obj)
        # Bake shape and translation into vertices so the armature uses the same
        # world rest coordinates as the body, even after head rotation.
        for vertex in obj.data.vertices:
            vertex.co = Vector((vertex.co.x * scale[0], vertex.co.y * scale[1], vertex.co.z * scale[2])) + Vector(center)
        obj.location = (0, 0, 0)
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        self._bind(obj, rigid='head')
        return obj

    def _make_eyes(self):
        for side in ('l', 'r'):
            ids = {i for face in self.groups[f'helper-{side}-eye'] for i in face}
            center = sum((self.vertices[i] for i in ids), Vector()) / len(ids)
            self._ellipsoid(self.name + '_Eye.' + side, center, (.013, .013, .013), self.eye_white)
            iris = center + Vector((0, .0120, 0))
            self._ellipsoid(self.name + '_Iris.' + side, iris, (.0054, .0017, .0054), self.eye_iris)
            self._ellipsoid(self.name + '_Pupil.' + side, iris + Vector((0, .0015, 0)), (.0027, .0007, .0027), self.eye_pupil)
            self._ellipsoid(self.name + '_Eyebrow.' + side, center + Vector((0, .009, .021)), (.016, .0024, .0021), self.hair)

    def pose_positions(self, joints, **kwargs):
        return self.pose(joints, **kwargs)

    def pose(self, joints, grip=1.0, hand_roll=None, palm_normals=None):
        rest = self.rest_joints
        points = {key: Vector(joints.get(key, value)) for key, value in rest.items()}
        for extra in ('left_hand', 'right_hand'):
            if extra in joints:
                points[extra] = Vector(joints[extra])
        hand_roll = hand_roll or {}
        palm_normals = palm_normals or {}
        if isinstance(hand_roll, (float, int)):
            hand_roll = {'left': hand_roll, 'right': hand_roll}
        body = _transform(rest['pelvis'], rest['chest'], points['pelvis'], points['chest'],
                          rest['left_shoulder'] - rest['right_shoulder'],
                          points['left_shoulder'] - points['right_shoulder'])
        neck = _transform(rest['neck'], rest['head'], points['neck'], points['head'],
                          Vector((1, 0, 0)), body.to_3x3() @ Vector((1, 0, 0)))
        transforms = {'body': body, 'head': neck}
        for side in ('left', 'right'):
            shoulder, elbow, wrist = (rest[f'{side}_{key}'] for key in ('shoulder', 'elbow', 'wrist'))
            s, e, w = (points[f'{side}_{key}'] for key in ('shoulder', 'elbow', 'wrist'))
            normal = (elbow - shoulder).cross(wrist - elbow)
            posed_normal = (e - s).cross(w - e)
            if posed_normal.length < .00001:
                posed_normal = body.to_3x3() @ normal
            upper = _transform(shoulder, elbow, s, e, normal, posed_normal)
            forearm = _transform(elbow, wrist, e, w, normal, posed_normal)
            grip_amount = float(grip.get(side, 1) if isinstance(grip, dict) else grip)
            center = self.palm_centers[side] + self.palm_normals[side] * (.030 * max(0, min(1, grip_amount)))
            hand_center = points.get(f'{side}_hand', forearm @ center)
            hand = _transform(wrist, center, w, hand_center, self.palm_normals[side],
                              forearm.to_3x3() @ self.palm_normals[side], float(hand_roll.get(side, 0)))
            if side in palm_normals:
                axis = (hand_center - w).normalized()
                current = hand.to_3x3() @ self.palm_normals[side]
                desired = Vector(palm_normals[side])
                current = (current - axis * current.dot(axis)).normalized()
                desired = (desired - axis * desired.dot(axis)).normalized()
                angle = math.atan2(axis.dot(current.cross(desired)), current.dot(desired))
                hand = _rotation_about(w, axis, angle) @ hand
            transforms[side + '_upperarm'] = upper
            transforms[side + '_forearm'] = forearm
            transforms[side + '_hand'] = hand
            hip, knee, ankle, toe = (rest[f'{side}_{key}'] for key in ('hip', 'knee', 'ankle', 'toe'))
            h, k, a, t = (points[f'{side}_{key}'] for key in ('hip', 'knee', 'ankle', 'toe'))
            leg_normal = (knee - hip).cross(ankle - knee)
            posed_leg_normal = (k - h).cross(a - k)
            if leg_normal.length < .00001:
                leg_normal = Vector((1, 0, 0))
            if posed_leg_normal.length < .00001:
                posed_leg_normal = body.to_3x3() @ leg_normal
            transforms[side + '_thigh'] = _transform(hip, knee, h, k, leg_normal, posed_leg_normal)
            transforms[side + '_shin'] = _transform(knee, ankle, k, a, leg_normal, posed_leg_normal)
            transforms[side + '_foot'] = _transform(ankle, toe, a, t, Vector((0, 0, 1)),
                                                   Vector((0, 0, 1)) if 'foot_up' not in joints else Vector(joints['foot_up']))
        targets = {}
        for name in self._order:
            suffix = name[-1] if name.endswith(('.L', '.R')) else None
            side = 'left' if suffix == 'L' else 'right' if suffix == 'R' else None
            group = 'body'
            if name.startswith(('head', 'jaw', 'eye', 'special', 'temporalis', 'tongue', 'levator', 'oris', 'oculi')):
                group = 'head'
            elif name.startswith('neck'):
                group = 'head'
            elif side:
                if name.startswith('upperarm'):
                    group = side + '_upperarm'
                elif name.startswith('lowerarm'):
                    group = side + '_forearm'
                elif name.startswith(('wrist', 'metacarpal', 'finger')):
                    group = side + '_hand'
                elif name.startswith('upperleg'):
                    group = side + '_thigh'
                elif name.startswith('lowerleg'):
                    group = side + '_shin'
                elif name.startswith(('foot', 'toe')):
                    group = side + '_foot'
            targets[name] = transforms[group] @ self._rest_matrices[name]
            match = re.match(r'finger([1-5])-([1-3])\.([LR])$', name)
            amount = float(grip.get(side, 1) if isinstance(grip, dict) else grip)
            if match:
                digit, segment = int(match[1]), int(match[2])
                parent_name = self.skeleton['bones'][name].get('parent')
                if segment > 1 and parent_name in targets:
                    targets[name] = targets[parent_name] @ self._rest_matrices[parent_name].inverted() @ self._rest_matrices[name]
                effective = targets[name] @ self._rest_matrices[name].inverted()
                direction = (self._tail[name] - self._head[name]).normalized()
                if amount <= .00001:
                    # The MakeHuman A-pose already has relaxed finger flexion.
                    # For floor support, straighten every phalanx into the palm
                    # plane instead of treating that relaxed pose as a flat hand.
                    first = f'finger{digit}-1.{suffix}'
                    flat = self._tail[first] - self._head[first]
                    flat -= self.palm_normals[side] * flat.dot(self.palm_normals[side])
                    flat.normalize()
                    desired = (transforms[side + '_hand'].to_3x3() @ flat).normalized()
                    current = (targets[name].to_3x3() @ Vector((0, 1, 0))).normalized()
                    rotation = current.rotation_difference(desired).to_matrix().to_4x4()
                    head = targets[name].translation.copy()
                    targets[name] = Matrix.Translation(head) @ rotation @ Matrix.Translation(-head) @ targets[name]
                else:
                    if digit == 1:
                        # Thumb opposition goes toward the middle knuckle, not
                        # in the same flexion direction as the four fingers.
                        middle = self._head[f'finger3-1.{suffix}']
                        toward_palm = (middle - self._head[name]).normalized()
                        hinge = direction.cross(toward_palm).normalized()
                    else:
                        hinge = direction.cross(self.palm_normals[side]).normalized()
                    axis = (effective.to_3x3() @ hinge).normalized()
                    angle = ((.90, .80, .65) if digit == 1 else (.90, 1.12, .78))[segment - 1] * amount
                    targets[name] = _rotation_about(targets[name].translation, axis, angle) @ targets[name]
        # Set matrix_basis analytically to avoid stale parent-matrix evaluation
        # while assigning 163 bones in one frame. One depsgraph update follows.
        for name in self._order:
            rest_matrix = self._rest_matrices[name]
            parent = self.skeleton['bones'][name].get('parent')
            if parent:
                basis = rest_matrix.inverted() @ self._rest_matrices[parent] @ targets[parent].inverted() @ targets[name]
            else:
                basis = rest_matrix.inverted() @ targets[name]
            self.armature.pose.bones[name].matrix_basis = basis
        self.current_joints = {key: tuple(point) for key, point in points.items()}
        bpy.context.view_layer.update()
        return self

    def keyframe(self, frame):
        for bone in self.armature.pose.bones:
            bone.keyframe_insert('location', frame=frame)
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            bone.keyframe_insert('scale', frame=frame)


def create_human(name='Athlete'):
    return Human(name)
