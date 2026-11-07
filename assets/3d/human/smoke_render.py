import sys,math
from pathlib import Path
import bpy
from mathutils import Vector
root=Path.cwd();sys.path.insert(0,str(root/'scripts/three_d'))
from human import create_human
from equipment import build_equipment
from poses import exercise_pose
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
h=create_human();eq=build_equipment('pec-deck',{'grip_z':1.09})
j,opts=exercise_pose('pec-deck',0,eq);h.pose(j,**opts);eq.update(0,j)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.76,.76,.73,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.55
for loc,power,size in [((3,4,5),650,4),((-3,1,3),350,4),((0,-3,4),450,3)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera');camera=bpy.data.objects.new('Camera',d);scene.collection.objects.link(camera);camera.location=(3,4.5,2.6);camera.rotation_euler=(Vector((0,.05,1))-camera.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.55;scene.camera=camera
bpy.ops.mesh.primitive_plane_add(size=200);plane=bpy.context.object;m=bpy.data.materials.new('Floor');m.diffuse_color=(.86,.85,.81,1);plane.data.materials.append(m);plane.location.z=-.01
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
for phase in (0,1):
 j,opts=exercise_pose('pec-deck',phase,eq);h.pose(j,**opts);eq.update(phase,j)
 scene.render.filepath=str(root/'assets/3d/human'/f'smoke-pecdeck-{phase}.png');bpy.ops.render.render(write_still=True)
print('RENDER_OK')

