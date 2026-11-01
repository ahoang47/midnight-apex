"""Textured PSX renders for the lean cars: EEVEE Next, 640x448, 1 sample, filter 0, Standard view (the fake-shine
materials are emission, no scene lights), saved raw; the deliver step applies RGB555 + 4x4 Bayer + 2x nearest.
Cameras: same Blender-frame 3/4s as the clay sheets + side / front / rear orthos (5 m, centre z .65)."""
import bpy, math, os
from mathutils import Vector
import render_clay as RC
SHOTS = {'front34': ((5.0, -5.6, 1.35), (0.0, -0.25, 0.60), 55), 'rear34': ((-4.8, 5.8, 1.45), (0.0, 0.25, 0.62), 55)}
def setup(res=(640, 448)):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (0.20, 0.21, 0.24, 1); bg.inputs['Strength'].default_value = 1.0
def render_textured(out_root, rig, set_pose, name):
    out = os.path.join(out_root, 'renders', 'clay_raw'); os.makedirs(out, exist_ok=True); set_pose(rig); setup()
    for k, (loc, tgt, lens) in SHOTS.items():
        RC.cam('CAM_t' + k, loc, ortho=None, lens=lens, target=tgt); RC.shoot(os.path.join(out, f'tex_{k}.png'))
    setup((1000, 1000))
    for k, (loc, rot) in RC.ORTHO.items():
        RC.cam('CAM_to' + k, loc, rot, ortho=5.0); RC.shoot(os.path.join(out, f'tex_{k}.png'))
