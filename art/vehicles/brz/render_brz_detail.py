"""Renders for the detail pass.  Run:  blender -b brz_lowpoly.blend -P render_brz_detail.py -- [TAG]
Clean Cycles 1280x960 (fake-shine emission materials, no scene lights) -> renders/brz_{view}_{TAG}.png + _800.jpg for
front34 / rear34 / side / front; PSX pipeline: EEVEE 640x448, 1 sample, no filter -> RGB555 + 4x4 Bayer -> 2x nearest
-> renders/brz_psx_{view}_{TAG}.png.  Then builds the blueprint compare sheet and the photo-vs-render sheet."""
import bpy, sys, os, math, subprocess, shutil
PY3 = shutil.which('python3') or '/usr/bin/python3'
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)); R = os.path.join(HERE, 'renders'); os.makedirs(R, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TAG = ARGS[0] if ARGS else 'detail'
to_bl = lambda p: Vector((p[1], -p[0], p[2]))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name.startswith('Blueprint_'): o.hide_render = True
# ground: flat emission grey with a soft radial falloff (the blob shadow sits on it)
gm = bpy.data.materials.new('Ground'); gm.use_nodes = True; nt = gm.node_tree; nd = nt.nodes; nd.clear(); L = nt.links.new
tc = nd.new('ShaderNodeTexCoord'); gr = nd.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mp = nd.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.09, 0.09, 1); L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs[0], gr.inputs['Vector'])
ramp = nd.new('ShaderNodeValToRGB'); L(gr.outputs['Fac'], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.10, 0.11, 0.13, 1); ramp.color_ramp.elements[1].color = (0.36, 0.37, 0.40, 1)
em = nd.new('ShaderNodeEmission'); o_ = nd.new('ShaderNodeOutputMaterial'); L(ramp.outputs[0], em.inputs['Color']); L(em.outputs[0], o_.inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=60); gp = bpy.context.object; gp.name = 'Ground'; gp.data.materials.append(gm)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.16, 0.18, 0.23, 1)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('Tgt', None); sc.collection.objects.link(tgt)
con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
VIEWS = {'front34': ((4.55, 3.85, 1.35), (0.05, 0, 0.55), 40, None), 'rear34': ((-4.55, -3.85, 1.45), (-0.05, 0, 0.55), 40, None),
         'side': ((0, 9, 0.66), (0, 0, 0.66), None, 4.75), 'front': ((9, 0, 0.66), (0, 0, 0.66), None, 2.25),
         'rear': ((-9, 0, 0.66), (0, 0, 0.66), None, 2.25)}
def set_view(v):
    loc, t, lens, orth = VIEWS[v]; cam.location = to_bl(loc); tgt.location = to_bl(t)
    if orth: cam.data.type = 'ORTHO'; cam.data.ortho_scale = orth
    else: cam.data.type = 'PERSP'; cam.data.lens = lens
def cycles():
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 12; sc.render.resolution_x, sc.render.resolution_y = 1280, 960
    sc.render.resolution_percentage = 100; sc.render.filter_size = 1.2; sc.render.image_settings.file_format = 'PNG'
def eevee():
    sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
    sc.render.resolution_x, sc.render.resolution_y = 640, 448; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
def jpg800(src, dst):
    subprocess.run([PY3, '-c', f"from PIL import Image; im=Image.open('{src}').convert('RGB'); im.thumbnail((800,800), Image.LANCZOS); im.save('{dst}', quality=90)"], check=True)
cycles()
for v in ('front34', 'rear34', 'side', 'front'):
    set_view(v); out = os.path.join(R, f'brz_{v}_{TAG}.png'); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
    jpg800(out, out.replace('.png', '_800.jpg'))
set_view('rear'); sc.render.filepath = os.path.join(HERE, 'tex', 'build', f'rear_{TAG}.png'); bpy.ops.render.render(write_still=True)
eevee()
for v in ('front34', 'rear34'):
    set_view(v); raw = os.path.join(HERE, 'tex', 'build', f'psx_raw_{v}.png'); sc.render.filepath = raw; bpy.ops.render.render(write_still=True)
    out = os.path.join(R, f'brz_psx_{v}_{TAG}.png')
    subprocess.run([PY3, '-c', f"""
import sys; sys.path.insert(0,'{HERE}/tex'); from quant import rgb555_bayer; from PIL import Image
im=rgb555_bayer(Image.open('{raw}').convert('RGB')); im.resize((im.width*2,im.height*2), Image.NEAREST).save('{out}')"""], check=True)
subprocess.run([PY3, os.path.join(HERE, 'bp', 'detail_sheets.py'), TAG], check=True, cwd=HERE)
print('RENDER DONE')
