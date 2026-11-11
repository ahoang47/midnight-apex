import bpy, math
from mathutils import Vector
sc=bpy.context.scene
for ob in bpy.data.objects:
    if ob.type=='MESH':
        ob.hide_render=not (ob.name in ['M_Body','M_Head','M_Hair_B','M_Hood'])
        if ob.data.shape_keys and 'Bulky' in ob.data.shape_keys.key_blocks: ob.data.shape_keys.key_blocks['Bulky'].value=.45
    elif ob.type in ['CAMERA','LIGHT']: ob.hide_render=True
sc.frame_set(1)
m=bpy.data.materials.get('M_M_Outfit')
if m:
    t=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'); t.image=bpy.data.images['m_outfit_hoodie']
# Retain painted character atlas. Fixed two-colour fake dashboard lighting, no PBR.
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt=m.node_tree; t=next((n for n in nt.nodes if n.type=='TEX_IMAGE'),None)
    if not t: continue
    t.interpolation='Closest'
    for n in list(nt.nodes):
        if n!=t: nt.nodes.remove(n)
    g=nt.nodes.new('ShaderNodeNewGeometry'); dot=nt.nodes.new('ShaderNodeVectorMath'); dot.operation='DOT_PRODUCT'; dot.inputs[1].default_value=(.5,-.65,.6); nt.links.new(g.outputs['Normal'],dot.inputs[0])
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.0; ramp.color_ramp.elements[0].color=(.12,.25,.48,1); ramp.color_ramp.elements[1].position=.8; ramp.color_ramp.elements[1].color=(1,.72,.43,1); ramp.color_ramp.interpolation='CONSTANT'
    e=ramp.color_ramp.elements.new(.3); e.color=(.45,.52,.65,1)
    nt.links.new(dot.outputs['Value'],ramp.inputs[0]); mul=nt.nodes.new('ShaderNodeMixRGB'); mul.blend_type='MULTIPLY'; mul.inputs[0].default_value=1; nt.links.new(t.outputs['Color'],mul.inputs[1]); nt.links.new(ramp.outputs[0],mul.inputs[2]); em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(mul.outputs[0],em.inputs[0]); out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],out.inputs[0])
cam=bpy.data.objects.new('PortraitCam',bpy.data.cameras.new('PortraitCam')); sc.collection.objects.link(cam); sc.camera=cam
cam.location=(.20,-2.2,1.74); cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=.48
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=1; sc.render.filter_size=0
sc.render.resolution_x=sc.render.resolution_y=72; sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.render.film_transparent=False
sc.world=bpy.data.worlds.new("PortraitWorld"); sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.003,.006,.015,1)
sc.render.image_settings.file_format='PNG'; sc.render.filepath='/workspace/mockups/pattern_read/raw/portrait.png'
bpy.ops.render.render(write_still=True)
print('PORTRAIT_DONE')
