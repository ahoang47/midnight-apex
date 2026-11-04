"""MX-5 (ND) clay renders (Workbench, headless): orthos (silhouette + clay), beauty 3/4s, steering-clearance
close-ups.  Raw frames into out/renders/raw/; bp/deliver.py composes the 800-px sheets."""
import bpy, math, os, json
from mathutils import Vector, Euler, Matrix
ORTHO = {'side': ((8, 0, 0.70), (90, 0, 90)), 'front': ((0, -8, 0.70), (90, 0, 0)), 'rear': ((0, 8, 0.70), (90, 0, 180)), 'top': ((0, 0, 8), (0, 0, 90))}
def setup(sil=False, res=(1600, 1000), xray=False):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100; sh = sc.display.shading; sc.display.render_aa = 'OFF' if sil else '8'
    sc.world = sc.world or bpy.data.worlds.new('W')
    if sil:
        sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = (1, 1, 1); sh.show_cavity = False; sh.show_shadows = False
        sh.background_type = 'VIEWPORT'; sc.world.color = (0, 0, 0); sh.show_object_outline = False; sh.show_specular_highlight = False
    else:
        sh.light = 'STUDIO'; sh.studio_light = 'Default'; sh.use_world_space_lighting = False; sh.color_type = 'MATERIAL'
        sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 1.0; sh.cavity_valley_factor = 1.5
        sh.show_shadows = False; sh.show_specular_highlight = True; sh.show_object_outline = True; sh.object_outline_color = (0.08, 0.08, 0.08)
        sh.background_type = 'WORLD'; sc.world.color = (0.92, 0.92, 0.92)
    sh.show_xray = xray; sh.xray_alpha = 0.35
    sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'
def cam(name, loc, rot=None, ortho=None, lens=50, target=None):
    c = bpy.data.objects.get(name)
    if c is None: c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = Vector(loc)
    if target is not None: c.rotation_euler = (Vector(target) - c.location).to_track_quat('-Z', 'Y').to_euler()
    else: c.rotation_euler = Euler([math.radians(a) for a in rot])
    cd = c.data; cd.clip_start = 0.05; cd.clip_end = 200; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.type = 'PERSP'; cd.lens = lens
    bpy.context.scene.camera = c; return c
def shoot(path): bpy.context.scene.render.filepath = path; bpy.ops.render.render(write_still=True)
def render_all(here, rig, set_pose, P_):
    out = os.path.join(here, 'renders', 'raw'); os.makedirs(out, exist_ok=True); set_pose(rig)
    for sil in (False, True):
        setup(sil, (1000, 1000))
        for k, (loc, rot) in ORTHO.items(): cam('CAM_' + k, loc, rot, ortho=5.0); shoot(os.path.join(out, f'{"sil" if sil else "clay"}_{k}.png'))
    setup(False, (1600, 1000))
    for k, (loc, tgt, lens) in {'front34': ((5.2, -5.8, 1.45), (0.0, -0.20, 0.62), 52), 'rear34': ((-5.0, 6.0, 1.55), (0.0, 0.25, 0.65), 52),
                                'side_low': ((7.5, -0.4, 0.75), (0.0, -0.4, 0.70), 45), 'high34': ((5.6, -4.8, 4.6), (0.0, 0.0, 0.50), 50)}.items():
        cam('CAM_' + k, loc, lens=lens, target=tgt); shoot(os.path.join(out, f'clay_{k}.png'))
    L, B, D = P_['LOCK'], P_['BUMP'], P_['DROOP']
    for name, st, dz in (('lockL_bump', L, B), ('lockR_bump', -L, B), ('static', 0, 0)):
        set_pose(rig, steer=st, wheel_dz={'FL': dz, 'FR': dz, 'RL': dz, 'RR': dz}); setup(False, (900, 700))
        cam('CAM_c1', (2.4, -3.2, 0.70), lens=40, target=(0.80, -1.30, 0.45)); shoot(os.path.join(out, f'clr_{name}_34.png'))
        setup(False, (900, 700), xray=True); cam('CAM_c2', (0.6, -1.33, 6.0), (0, 0, 90), ortho=2.0); shoot(os.path.join(out, f'clr_{name}_top_xray.png'))
    set_pose(rig)
