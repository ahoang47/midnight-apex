"""WRX clay renders (Workbench, headless): orthos, beauty 3/4s, suspension + steering pose sheet frames and
steering-clearance close-ups.  Everything into renders/clay_raw/; bp/deliver.py composes the 800-px sheets."""
import bpy, math, os, json
from mathutils import Vector
import render_clay as RC
ORTHO = RC.ORTHO            # side (+X), front (-Y), rear (+Y), top; 5 m ortho over 1000 px, centre z .65
def persp(name, loc, target, lens, res=(1600, 1000)):
    RC.setup_scene(False, res); RC.cam(name, loc, ortho=None, lens=lens, target=target)
def render_all(here, rig, set_pose, rel_travel, P):
    out = os.path.join(here, 'renders', 'clay_raw'); os.makedirs(out, exist_ok=True)
    set_pose(rig)
    for sil in (False, True):
        RC.setup_scene(sil)
        for k, (loc, rot) in ORTHO.items():
            RC.cam('CAM_' + k, loc, rot, ortho=5.0); RC.shoot(os.path.join(out, f'{"sil" if sil else "clay"}_{k}.png'))
    # beauty 3/4s (Blender coords: X = car left, -Y = car forward)
    shots = {'front34': ((5.0, -5.6, 1.35), (0.0, -0.25, 0.60), 55), 'rear34': ((-4.8, 5.8, 1.45), (0.0, 0.25, 0.62), 55),
             'high34': ((5.4, -4.6, 4.6), (0.0, 0.0, 0.50), 50)}
    for k, (loc, tgt, lens) in shots.items():
        persp('CAM_' + k, loc, tgt, lens); RC.shoot(os.path.join(out, f'clay_{k}.png'))
    # pass 2 surface checks: raking-light side (Cycles, one sun 6 deg above the horizon skimming along the flank; any
    # station-to-station ripple shows up as vertical bands) + reflection-stripe "zebra" matcaps (Workbench) top / side
    raking(out); zebra(out)
    # suspension / steering pose sheet frames (front 3/4 low + front ortho for roll read)
    B, D, L, R = P['BUMP'], P['DROOP'], P['LOCK'], P['ROLL']
    rollz = math.sin(math.radians(R)) * 0.74       # wheel travel at the track from R deg of roll
    poses = [('static', {}), ('full_bump', dict(heave=-B)), ('full_droop', dict(heave=D)),
             ('roll_right', dict(roll=R)), ('roll_left', dict(roll=-R)), ('dive', dict(pitch=-2.0, heave=-0.02)),
             ('squat', dict(pitch=1.6, heave=-0.01)),
             ('left_lock_roll', dict(steer=L, roll=R)), ('right_lock_roll', dict(steer=-L, roll=-R))]
    meta = {}
    for name, kw in poses:
        set_pose(rig, **kw); meta[name] = dict(kw, travel=rel_travel(rig))
        persp('CAM_p34', (5.6, -6.6, 1.25), (0.25, 0.1, 0.55), 50, (900, 600)); RC.shoot(os.path.join(out, f'pose_{name}_34.png'))
        RC.setup_scene(False, (900, 600)); RC.cam('CAM_pf', (0, -8, 0.75), (90, 0, 0), ortho=2.6); RC.shoot(os.path.join(out, f'pose_{name}_front.png'))
    # steering clearance close-ups: front-left corner at full lock both ways x full bump (wheel-only travel)
    clr = [('lockL_bump', L, B), ('lockR_bump', -L, B), ('lockL_droop', L, -D), ('lockR_droop', -L, -D)]
    for name, st, dz in clr:
        set_pose(rig, steer=st, wheel_dz={'FL': dz, 'FR': dz})
        persp('CAM_c1', (2.2, -2.9, 0.55), (0.75, -1.25, 0.42), 40, (900, 700)); RC.shoot(os.path.join(out, f'clr_{name}_34.png'))
        # x-ray from below / above: body see-through, tyre solid
        RC.setup_scene(False, (900, 700)); sh = bpy.context.scene.display.shading; sh.show_xray = True; sh.xray_alpha = 0.35
        RC.cam('CAM_c2', (0.6, -1.25, 6.0), (0, 0, 90), ortho=2.2); RC.shoot(os.path.join(out, f'clr_{name}_top_xray.png'))
        RC.cam('CAM_c3', (6.0, -1.25, 0.5), (90, 0, 90), ortho=1.9); RC.shoot(os.path.join(out, f'clr_{name}_side_xray.png'))
        sh.show_xray = False
    set_pose(rig)
    json.dump(meta, open(os.path.join(here, 'bp', 'pose_meta.json'), 'w'), indent=1)

def raking(out):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48
    sc.cycles.use_denoising = False; sc.render.resolution_x, sc.render.resolution_y = 1600, 700
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.06, 0.06, 0.065, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.get('RAKE_SUN')
    if sun is None:
        sun = bpy.data.objects.new('RAKE_SUN', bpy.data.lights.new('RAKE_SUN', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 7.0; sun.data.angle = math.radians(1.0)
    # light travel direction in Blender coords (X = car left, -Y = car fwd): coming from ahead (or behind) of the car,
    # 20 deg outboard of the flank, 7 deg above the horizon -> grazes the doors along their length
    for name, d in (('raking_side_fwd', Vector((-0.34, 0.93, -0.12))), ('raking_side_rear', Vector((-0.34, -0.93, -0.12)))):
        sun.rotation_euler = d.normalized().to_track_quat('-Z', 'Y').to_euler(); sun.hide_render = False
        RC.cam('CAM_rake', (7.5, 0.0, 0.62), (90, 0, 90), ortho=4.9); sc.render.resolution_x, sc.render.resolution_y = 1600, 700
        RC.shoot(os.path.join(out, f'clay_{name}.png'))
    sun.hide_render = True; sc.render.engine = 'BLENDER_WORKBENCH'
def zebra(out):
    for name, loc, rot, osz in (('zebra_top', (0, 0, 8), (0, 0, 90), 5.0), ('zebra_side', (8, 0, 0.62), (90, 0, 90), 5.0),
                                ('zebra_34', None, None, None)):
        RC.setup_scene(False, (1600, 900) if loc is None else (1600, 800)); sh = bpy.context.scene.display.shading
        sh.light = 'MATCAP'; sh.studio_light = 'reflection_check_horizontal.exr'; sh.color_type = 'SINGLE'; sh.single_color = (1, 1, 1)
        sh.show_cavity = False; sh.show_object_outline = False
        if loc is None: RC.cam('CAM_z34', (5.0, -5.0, 2.6), None, lens=50, target=(0.0, 0.0, 0.6))
        else: RC.cam('CAM_' + name, loc, rot, ortho=osz)
        RC.shoot(os.path.join(out, f'clay_{name}.png'))
