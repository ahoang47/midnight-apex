import bpy, math, os
from mathutils import Vector
O='/workspace/mockups/pattern_read/raw'; sc=bpy.context.scene
r=bpy.data.objects['WRX-vehicle']; r.rotation_mode='XYZ'; r.location.x=-1.65; r.rotation_euler.z=math.pi-.19
for ob in bpy.data.objects:
 if ob.name.startswith('WRX') and ob.type=='MESH' and 'body' in ob.name.lower(): ob.rotation_euler.x=0
 if ob.name=='Backfire': ob.hide_render=True
bpy.context.view_layer.update()
# Rear lamps still face camera, head sprites stay culled.
for ob in bpy.data.objects:
 if 'face' in ob and ob.parent:
  v=ob.parent.matrix_world.to_3x3()@Vector(ob['face']); pos=ob.matrix_world.translation; ob.hide_render=v.dot((sc.camera.location-pos).normalized())<.15
sc.render.film_transparent=False;sc.render.image_settings.color_mode='RGB';sc.render.filepath=O+'/raw_entry_b_blend50.png';bpy.ops.render.render(write_still=True)
neon=[ob for ob in bpy.data.objects if ob.name.startswith(('LampGlow','GRC_Head','GRC_Tail','WRX_Head','WRX_Tail'))]
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob not in neon and not ob.hide_render: ob.is_holdout=True
sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.render.filepath=O+'/glow_entry_b_blend50.png';bpy.ops.render.render(write_still=True)
print('VARIANT_B_DONE')
