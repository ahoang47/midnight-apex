import bpy,os
sc=bpy.context.scene
m=bpy.data.materials.get('U_WornLanePaint')
if m:
 nt=m.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.18,.19,.17,1);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],out.inputs[0])
# One longer worn dash marks the judgement zone; the rival can visibly straddle it.
for ob in bpy.data.objects:
 if ob.name.startswith('LaneDivider') and min(v.co.x for v in ob.data.vertices)<0:
  ys=[v.co.y for v in ob.data.vertices]
  if abs(min(ys)+16)<.01:
   for v in ob.data.vertices: v.co.y=-18.5 if v.co.y<-15 else -11.8
bpy.ops.wm.save_as_mainfile(filepath='/workspace/mockups/pattern_read/battle_base.blend')
sc.render.filepath='/workspace/mockups/pattern_read/raw/raw_entry_blend50.png';bpy.ops.render.render(write_still=True)
glows=[ob for ob in bpy.data.objects if ob.name.startswith(('LampGlow','GRC_Head','GRC_Tail','WRX_Head','WRX_Tail'))]
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob not in glows and not ob.hide_render:ob.is_holdout=True
sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.render.filepath='/workspace/mockups/pattern_read/raw/glow_entry_blend50.png';bpy.ops.render.render(write_still=True)
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.is_holdout=False
exec(compile(open('/workspace/mockups/pattern_read/build_variant_b.py').read(),'/workspace/mockups/pattern_read/build_variant_b.py','exec'))
