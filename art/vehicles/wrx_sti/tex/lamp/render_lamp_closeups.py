"""Head lamp review renders from lean/wrx_lean.blend (read-only): a close front ortho and a close front 3/4 of the
left lamp, with the glow FX off and on.  blender -b lean/wrx_lean.blend -P tex/lamp/render_lamp_closeups.py"""
import bpy, os, sys
from mathutils import Vector
_W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(_W, 'parts')); import render_lean as RL
OUT = os.path.join(_W, 'lean', 'renders', 'clay_raw')
def cam(loc, tgt, lens=None, ortho=None):
    c = bpy.data.objects.get('CAM_hl') or bpy.data.objects.new('CAM_hl', bpy.data.cameras.new('CAM_hl'))
    if c.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(c)
    c.location = loc; c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    else: c.data.type = 'PERSP'; c.data.lens = lens
    bpy.context.scene.camera = c
def shoot(p): bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True)
for im in bpy.data.images:                      # unpacked images (env map) by absolute path
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        im.filepath = os.path.join(_W, 'lean', 'tex', os.path.basename(im.filepath)); im.reload()
glow = bpy.data.objects['WRX_FX_HeadGlow']
RL.setup((640, 448))
# Blender frame: X = car left, -Y = forward.  Left lamp centre ~ car (2.04, .60, .70) -> Blender (.60, -2.04, .70)
for g in (False, True):
    glow.hide_render = not g; sfx = '_glow' if g else ''
    cam((0.60, -6.0, 0.70), (0.60, 0.0, 0.70), ortho=0.62); shoot(os.path.join(OUT, f'hl_close_front{sfx}.png'))
    cam((1.75, -3.35, 0.95), (0.55, -2.0, 0.66), lens=55); shoot(os.path.join(OUT, f'hl_close_front34{sfx}.png'))
glow.hide_render = True
