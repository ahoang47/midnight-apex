"""Textured PSX renders of the GR Corolla detail build: EEVEE Next, 640x448 (reference frame aspect), 1 sample,
filter 0, Standard view (fake-shine materials are emission, no scene lights); deliver step applies RGB555 + 4x4
Bayer + 2x nearest.  Also 1000^2 orthos (5 m) for the overlay sheet and a lights-on pair (glow FX visible)."""
import bpy, math, os
from mathutils import Vector
import render_gr as RC
SHOTS = {'front34': ((5.2, -5.8, 1.45), (0.0, -0.20, 0.62), 52), 'rear34': ((-5.0, 6.0, 1.55), (0.0, 0.25, 0.65), 52),
         'side': ((7.6, -0.3, 0.80), (0.0, -0.3, 0.68), 42), 'front_low': ((1.6, -6.4, 0.65), (0.0, -0.4, 0.55), 50)}
def setup(res=(640, 448), bg=(0.20, 0.21, 0.24)):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    b = w.node_tree.nodes.get('Background'); b.inputs['Color'].default_value = (*bg, 1); b.inputs['Strength'].default_value = 1.0
def render_textured(out_root, rig, set_pose, glow_name='GRC_FX_LampGlow'):
    out = os.path.join(out_root, 'renders', 'tex_raw'); os.makedirs(out, exist_ok=True); set_pose(rig); setup()
    glow = bpy.data.objects.get(glow_name)
    for k, (loc, tgt, lens) in SHOTS.items():
        RC.cam('CAM_t' + k, loc, lens=lens, target=tgt); RC.shoot(os.path.join(out, f'tex_{k}.png'))
    setup((640, 448), (0.03, 0.035, 0.05))                                   # lights on (night backdrop): glow FX visible
    if glow: glow.hide_render = False
    for k in ('front34', 'rear34'):
        loc, tgt, lens = SHOTS[k]; RC.cam('CAM_n' + k, loc, lens=lens, target=tgt); RC.shoot(os.path.join(out, f'lit_{k}.png'))
    if glow: glow.hide_render = True
    setup((1000, 1000), (0.92, 0.92, 0.92))
    for k, (loc, rot) in RC.ORTHO.items():
        RC.cam('CAM_to' + k, loc, rot, ortho=5.0); RC.shoot(os.path.join(out, f'tex_{k}.png'))
    for k, st in (('lockL', 30.0), ('lockR', -30.0)):
        set_pose(rig, steer=st); setup((640, 448)); RC.cam('CAM_tl' + k, (2.4, -3.2, 0.70), lens=40, target=(0.80, -1.30, 0.45)); RC.shoot(os.path.join(out, f'tex_wheel_{k}.png'))
    set_pose(rig)
