"""S2000 LEAN build: <= 2,000 triangles TOTAL (body + soft top + windscreen + mirrors + liners as ONE mono mesh,
4 x 10-sided wheels, 4 x strut/arm).  Shape source = the approved blueprint build s2000_lowpoly.blend (opened
read-only, never saved over): every lean section is re-sampled from it by star rays (leanlib), so the soft-top
roadster silhouette is kept; detail (lamps, grille, panel lines, badges, fabric, plates) is baked from the approved
textured meshes into a 1024^2 body texture (+ the 256^2 parts/wheel atlas), RGB555 + Bayer.
  blender -b --factory-startup -P build_s2000_lean.py -- [--render]      then python3 make_lean.py does the rest
Outputs in lean/.  Rig (Godot VehicleBody3D / VehicleWheel3D naming):
  S2000-vehicle (root, ground, car origin)
  +- S2000_Body       ONE mesh, origin at the COM estimate (x .058 = mid-wheelbase, 50:50; z .46) at ride height
  +- Hub_FL-wheel ..  empties at the static hub centres (-> VehicleWheel3D)
  |    +- Steer_FL/FR (front only, about local Z)  +- S2000_Wheel_XX (origin = hub, spins about the axle)
  +- Susp_FL ..       empties: hub position + steer only, never spin  +- S2000_Susp_XX (strut + lower arm)"""
import bpy, bmesh, sys, os, math, json, importlib
import numpy as np
from mathutils import Vector, Matrix
_VEH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(_VEH, 'lean_common')); sys.path.insert(0, os.path.join(_VEH, 'wrx_sti', 'parts'))
import leanlib as LL, psx_mat as PM
importlib.reload(LL)
HERE = os.path.join(_VEH, 's2000'); OUT = os.path.join(HERE, 'lean'); SRC = os.path.join(HERE, 's2000_lowpoly.blend')
for d in ('bp', 'tex', 'renders/raw'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
FR = LL.Frame('xfwd'); P = 'S2000'; CAP = 2000
WB_F, WB_R, TR_F, TR_R = 1.265, -1.148, 0.72, 0.755          # hub x, hub y (= half track as built)
TIRE_R, TIRE_W, ARCH = 0.315, 0.215, 0.365
COM = (round((WB_F + WB_R) / 2, 4), 0.46)
BUMP, DROOP, LOCK = 0.040, 0.050, 30.0          # art doc: about +/-4-5 cm travel, +/-30 deg lock (blueprint arch is only 5 cm above the tyre)
R_WELL = 0.405
R_LINER = 0.415                 # 7-segment tunnel: chord mid-radius .403
ARCHES = [dict(xc=WB_F, zc=TIRE_R, r=ARCH), dict(xc=WB_R, zc=TIRE_R, r=ARCH)]
ANG = [-90, -62, -38, -22, -8, 6, 18, 32, 48, 66, 90]
ZC = 0.70
# anchors: bottom-outer corner, max width, upper shoulder (support directions); FILL = extra rows between anchors
ANCH = [(0.6, -0.8), (1.0, 0.0), (0.75, 0.66)]
FILL = [1, 1, 1, 1]
SOFT_FILL = [2, 2]
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def stations():
    nose = [2.066, 2.035, 1.995, 1.935, 1.855, 1.755]
    fa = [WB_F + d for d in (0.378, 0.33, 0.20, 0.0, -0.20, -0.33, -0.378)]
    mid = [0.80, 0.62, 0.43, 0.38, 0.20, 0.0, -0.22, -0.45, -0.66, -0.83, -0.87]
    ra = [WB_R + d for d in (0.378, 0.33, 0.20, 0.0, -0.20, -0.33, -0.378)]
    tail = [-1.64, -1.76, -1.86, -1.94, -1.975, -2.005, -2.04, -2.066]
    return np.array(sorted(nose + fa + mid + ra + tail, reverse=True))
CP_FRONT, CP_REAR = 0.40, -0.845          # open cockpit (approved build); the lean lower loft gets a hidden lid here
def in_cockpit(x): return CP_REAR + 0.005 < x < CP_FRONT - 0.005
def shoulder(yz, ang, hit, x):
    """upper shoulder anchor; inside the cockpit only the rim (outer 40 %) counts, never seats or tub."""
    sc = yz @ np.array(ANCH[2]); sc[~hit] = -9
    if in_cockpit(x): sc[yz[:, 0] < 0.6 * yz[hit, 0].max()] = -9
    return ang[int(np.argmax(sc))]
def soft_stations(x0, x1):
    """windscreen base .. soft-top tail: denser where the screen rakes and where the top drops to the deck"""
    return np.array([x0, x0 - 0.10, x0 - 0.22, 0.10, 0.0, -0.25, -0.50, -0.70, -0.90, -1.05, x1 + 0.17, x1])
def outward(bm, FR, zref):
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        c = FR.to_car(f.calc_center_median()); n = FR.to_car(f.normal + FR.to_bl((0, 0, 0)))
        if (c[1] * n[1] + (c[2] - zref) * n[2]) < 0: f.normal_flip()
def approved_sections():
    """the approved build's blueprint section function (bp/curves.json -> section(x)), executed from its source text
    (dimensions + curve block only: no scene changes, no file writes), so the lean loft uses the very same faired
    blueprint curves without importing / running build_s2000.py."""
    src = open(os.path.join(HERE, 'build_s2000.py')).read()
    a = src[src.index('# ---------------------------------------------------------------- dimensions'):src.index('# ---------------------------------------------------------------- texture atlas')]
    b = src[src.index('def lerp_keys'):src.index('def build_body')]
    ns = dict(np=np, math=math, os=os, json=__import__('json'), OUT=HERE)
    exec(a, ns); exec(b, ns); return ns
SUB = [0, 1, 2, 4, 5, 7, 8, 9, 11]      # lean subset of the approved 12-point half-section (5 = character line, 7 = shoulder)
KSH = SUB.index(7)
def geometry(M):
    src = {o.name[5:]: o for o in bpy.data.objects if o.name.startswith('orig_')}
    # lower body: the approved blueprint section function, lean subset of its points (faired by construction)
    A = approved_sections(); X = stations()
    G = np.array([[A['section'](x)[0][i] for i in SUB] for x in X], float)
    bvh_b, names_b, _ = LL.target_bvh([src['S2000_Body']], 0.6)
    for s_, x in enumerate(X):            # hidden lid over the cockpit, at shoulder height (soft top covers it)
        if not (CP_REAR < x < CP_FRONT): continue
        y0, z0 = G[s_, KSH, 1], G[s_, KSH, 2]; K = G.shape[1]
        for k in range(KSH + 1, K): t = (k - KSH) / (K - 1 - KSH); G[s_, k, 1] = y0 * (1 - t); G[s_, k, 2] = z0
    G = LL.raise_wells(G, X, ARCHES, TIRE_R, R_WELL, edge_keep=0.012)
    body = LL.obj_from_bm(P + '_Body', LL.loft_mesh(FR, G, P + '_Body'), [M['paint'], M['glass'], M['under']])
    # soft top + windscreen: open strip from the belt edge (first hit) to the top centre
    tg = [src[n] for n in ('S2000_SoftTop', 'S2000_Windshield', 'S2000_WindshieldFrame')]
    bvh_t, names_t, _ = LL.target_bvh(tg, 0.3)
    xe = [x for x in np.linspace(1.0, -1.6, 521) if bvh_t.ray_cast(FR.to_bl((x, 0.0, 3.0)), Vector((0, 0, -1)), 5)[0] is not None]
    XT = soft_stations(xe[0] - 0.004, xe[-1] + 0.004); print('SOFT extent', round(xe[0], 3), round(xe[-1], 3))
    T, ANGT, AT, OKT = LL.feature_grid(FR, bvh_t, XT, lambda x: 0.72, [(0.6, 0.8)], SOFT_FILL, a_lo=-25.0, start_at_first_hit=True, sigma=0.10)
    print('SOFT misses', int((~OKT).sum()), 'start angles', np.round(AT[:, 0], 1))
    for s_ in range(len(XT)):            # seat the strip's belt edge on the body (no see-through slit under it)
        y0, z0 = T[s_, 0, 1], T[s_, 0, 2]
        h = bvh_b.ray_cast(FR.to_bl((XT[s_], y0 - 0.01, 3.0)), Vector((0, 0, -1)), 5)
        if h[0] is not None and FR.to_car(h[0])[2] < z0: T[s_, 0, 2] = FR.to_car(h[0])[2] - 0.006
    for s_ in (0, len(XT) - 1):          # end rows sit on the cowl / rear deck
        for k in range(T.shape[1]):
            h = bvh_b.ray_cast(FR.to_bl((XT[s_], T[s_, k, 1] * 0.98, 3.0)), Vector((0, 0, -1)), 5)
            if h[0] is not None: T[s_, k, 2] = FR.to_car(h[0])[2] - 0.004
    bm = LL.strip_mesh(FR, T); outward(bm, FR, 0.72)
    top = LL.obj_from_bm(P + '_SoftTop', bm, [M['paint'], M['glass'], M['under']])
    bvh_all, names_all, _ = LL.target_bvh([src[n] for n in ('S2000_Body', 'S2000_SoftTop', 'S2000_Windshield', 'S2000_WindshieldFrame')], 0.3)
    for ob in (body, top):
        LL.classify_faces(FR, ob, bvh_all, names_all, [('Glass', 1)]); LL.smooth(ob, 42)
    return body, top, G, X
def parts(M, G, X, root):
    out = []
    for s in (1, -1):        # minimal door mirror (12 tris) at the approved pod (x .10, y .835, z .945, k 1.25)
        r0 = [(0.16, s * 0.80, 0.915), (0.16, s * 0.80, 0.965), (0.16, s * 0.86, 0.965), (0.16, s * 0.86, 0.915)]
        r1 = [(0.05, s * 0.78, 0.890), (0.05, s * 0.78, 0.990), (0.05, s * 0.915, 0.990), (0.05, s * 0.915, 0.890)]
        out.append(LL.tube(FR, P + ('_Mirror_L' if s > 0 else '_Mirror_R'), [r0, r1], [M['paint']], None, (True, True), 30))
    for nm, xc, yc in (('FL', WB_F, TR_F), ('FR', WB_F, -TR_F), ('RL', WB_R, TR_R), ('RR', WB_R, -TR_R)):
        s_ = int(np.argmin(np.abs(X - xc))); yout = G[s_, :, 1].max() - 0.025
        yin = 0.44 if nm[0] == 'F' else abs(yc) - TIRE_W / 2 - 0.035
        out.append(LL.liner(FR, f'{P}_Liner_{nm}', xc, TIRE_R, 1 if yc > 0 else -1, R_LINER, yin, yout, [M['under']], seg=7))
    return out
def cmp_renders(objs, rd):
    """orthographic alpha silhouettes in the approved build's 4 mm/px compare frames (bp/compare_lean.py)."""
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
    sc.display.render_aa = 'OFF'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'
    keep = set(o.name for o in objs)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name not in keep
    cam = bpy.data.objects.new('CMP', bpy.data.cameras.new('CMP')); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    CV = {"side": ((0, 9, .70), (math.pi / 2, 0, math.pi), 4.6, 1150, 375), "top": ((0, 0, 9), (0, 0, math.pi / 2), 4.6, 550, 1150),
          "front": ((9, 0, .70), (math.pi / 2, 0, math.pi / 2), 2.2, 550, 375), "rear": ((-9, 0, .70), (math.pi / 2, 0, -math.pi / 2), 2.2, 550, 375)}
    for name, (loc, rot, osc, rx, ry) in CV.items():
        cam.location = loc; cam.rotation_euler = rot; cam.data.ortho_scale = osc
        sc.render.resolution_x, sc.render.resolution_y = rx, ry; sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(rd, f'cmp_{name}.png'); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    for o in bpy.data.objects: o.hide_render = o.name.startswith('BP') or o.name.startswith('Blueprint')
def corner_list():
    return (('FL', WB_F, TR_F), ('FR', WB_F, -TR_F), ('RL', WB_R, TR_R), ('RR', WB_R, -TR_R))
def build_rig(body, mono_parts, M):
    root = LL.empty(P + '-vehicle', (0, 0, 0), None, 0.5, 'ARROWS')
    lines = []; tot = 0
    for ob in [body] + mono_parts:
        ob.data.calc_loop_triangles(); n = len(ob.data.loop_triangles); tot += n; lines.append(f'{ob.name:18s} {n:5d}')
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in mono_parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    c = FR.to_bl((COM[0], 0, COM[1])); body.data.transform(Matrix.Translation(-c)); body.location = c; body.parent = root
    rig = dict(FR=FR, body=body, com=COM, hub={}, steer={}, susp={}, hub_rest={})
    for nm, xc, yc in corner_list():
        loc = FR.to_bl((xc, yc, TIRE_R)); hb = LL.empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F': st = LL.empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        # 10-sided wheel, vertex radius = tyre radius (as the WRX lean), atlas disc = wheel tile, tread = dark weave tile
        LL.wheel(FR, f'{P}_Wheel_{nm}', M['wheel'], par, 1 if yc > 0 else -1, TIRE_R, TIRE_W, (0.5, 0.0, 1.0, 0.5), (0.0, 0.0, 0.5, 0.25), (0.40, 0.336))
        sp = LL.empty(f'Susp_{nm}', loc, root, 0.15, 'PLAIN_AXES'); rig['susp'][nm] = sp
        LL.susp(FR, f'{P}_Susp_{nm}', M['under'], sp, 1 if yc > 0 else -1, nm[0] == 'F')
    bpy.context.view_layer.update()
    rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
    body.data.calc_loop_triangles(); mono = len(body.data.loop_triangles)
    wl = [o for o in bpy.data.objects if o.name.startswith(P + '_Wheel_')]; sl = [o for o in bpy.data.objects if o.name.startswith(P + '_Susp_')]
    for o in wl + sl: o.data.calc_loop_triangles()
    wheels = sum(len(o.data.loop_triangles) for o in wl); susp = sum(len(o.data.loop_triangles) for o in sl)
    lines += ['', f'MONO {P}_Body {mono} (lower body + soft top/screen strip + mirrors + liners)', f'wheels (4 x 10-sided) {wheels}',
              f'suspension (4 x strut + arm) {susp}', f'TOTAL rendered {mono + wheels + susp}  (cap {CAP}: {"OK" if mono + wheels + susp <= CAP else "OVER"})']
    open(os.path.join(OUT, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    return rig, root
def render_set(rig, tag_objs_hide, prefix, textured=True, clay_too=True):
    import render_kit as RK
    rd = os.path.join(OUT, 'renders', 'raw')
    REF = lambda o: o.name.startswith('BP') or o.name.startswith('Blueprint')
    for o in bpy.data.objects:
        if o.type == 'MESH' and not REF(o): o.hide_render = o in tag_objs_hide
    shots = {'front34': ((5.6, 5.0, 1.35), (0.25, 0.0, 0.60), 55), 'rear34': ((-5.8, -4.8, 1.45), (-0.25, 0.0, 0.62), 55)}
    if textured:
        RK.eevee()
        for k, (loc, tg, lens) in shots.items(): RK.cam(FR, 'CAMt', loc, tg, lens); RK.shoot(os.path.join(rd, f'{prefix}tex_{k}.png'), (640, 448))
        CV = {"side": ((0, 9, .70), (0, 0, .70), 4.6, (1150, 375), None), "top": ((0, 0, 9), (0, 0, 0), 4.6, (550, 1150), (0, 1, 0)),
              "front": ((9, 0, .70), (0, 0, .70), 2.2, (550, 375), None), "rear": ((-9, 0, .70), (0, 0, .70), 2.2, (550, 375), None)}
        for k, (loc, tg, osc, res, ir) in CV.items():
            c_ = RK.cam(FR, 'CAMo', loc, tg, ortho=osc, image_right=ir); c_.data.sensor_fit = 'AUTO'; RK.shoot(os.path.join(rd, f'{prefix}tex_cmp_{k}.png'), res)
    if clay_too:
        RK.clay()
        RK.cam(FR, 'CAMc', (0, 8, 0.65), (0, 0, 0.65), ortho=5.0); RK.shoot(os.path.join(rd, f'{prefix}clay_side.png'), (1000, 450))
        RK.cam(FR, 'CAMc', *shots['front34'][:2], shots['front34'][2]); RK.shoot(os.path.join(rd, f'{prefix}clay_front34.png'), (1000, 700))
    for o in bpy.data.objects: o.hide_render = REF(o)
def main():
    import render_kit as RK; importlib.reload(RK)
    bpy.ops.wm.open_mainfile(filepath=SRC)
    for o in bpy.data.objects:
        if o.name.startswith('BP') or o.name.startswith('Blueprint'): o.hide_render = True; o.hide_set(True)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and not (o.name.startswith('BP') or o.name.startswith('Blueprint')): o.name = 'orig_' + o.name
    PM.KEY_L = Vector((0.45, 0.55, 0.70)).normalized()          # car frame == Blender frame for the S2000
    M = {k: bpy.data.materials.new('lean_' + k) for k in ('paint', 'glass', 'under', 'tire', 'wheel')}
    for m in M.values(): m.use_nodes = True
    body, top, G, X = geometry(M)
    pp = [top] + parts(M, G, X, None)
    origs = [o for o in bpy.data.objects if o.name.startswith('orig_')]
    if '--render' in ARGS:     # approved build, same cameras, for the lean-vs-old sheet
        render_set(None, set([body] + pp), 'old_', textured=False)
    rig, root = build_rig(body, pp, M)
    rep = LL.clearance(rig, P, [P + '_Body'], BUMP, DROOP, LOCK)
    json.dump(rep, open(os.path.join(OUT, 'bp', 'clearance.json'), 'w'), indent=1); LL.set_pose(rig)
    lean_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(P + '_')]
    cmp_renders([o for o in lean_meshes if '_Susp_' not in o.name], os.path.join(OUT, 'renders', 'raw') + '/')
    # texture: bake the approved textured meshes into the lean body
    srcs = [bpy.data.objects['orig_' + n] for n in ('S2000_Body', 'S2000_SoftTop', 'S2000_Windshield', 'S2000_WindshieldFrame', 'S2000_Lights', 'S2000_Trim')]
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('orig_') and o not in srcs: o.hide_render = True
    import shutil, subprocess
    atlas_png = os.path.join(OUT, 'tex', 's2000_atlas_lean.png')
    subprocess.run(['python3', os.path.join(HERE, 'tex', 'debrand_atlas.py'), os.path.join(HERE, 's2000_atlas.png'), atlas_png], check=True)
    aimg = bpy.data.images.load(atlas_png); aimg.name = 'S2000_Atlas_Lean'
    for m in bpy.data.materials:                        # bake the de-branded atlas, not the approved one
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeTexImage' and n.image and n.image.name == 'S2000_Atlas': n.image = aimg
    body_png = LL.bake_lean(body, srcs, os.path.join(OUT, 'tex'), 's2000', extrusion=0.045, ray=0.10)
    env_png = os.path.join(OUT, 'tex', 'env.png'); shutil.copy(os.path.join(_VEH, 'wrx_sti', 'lean', 'tex', 'wrx_env.png'), env_png)
    PM.set_env(bpy.data.images.load(env_png)); bimg = bpy.data.images.load(body_png)
    F = dict(paint=PM.fake_mat('S2000_Paint_Body', img=bimg, ambient=0.48, key=0.62, spec=0.45, shin=55, env=0.38),
             glass=PM.fake_mat('S2000_Glass', rgb=(0.010, 0.014, 0.022), ambient=1.0, key=0.0, spec=0.6, shin=90, env=0.45, env_tint=(0.55, 0.70, 1.0)),
             under=PM.fake_mat('S2000_Under', rgb=(0.006, 0.006, 0.007), ambient=1.0, key=0.0, spec=0.0, env=0.0),
             tire=PM.fake_mat('S2000_Tire', rgb=(0.035, 0.035, 0.038), ambient=0.6, key=0.5, spec=0.08, shin=20, env=0.0),
             wheel=PM.fake_mat('S2000_Wheel_Atlas', img=aimg, ambient=0.55, key=0.55, spec=0.25, shin=30, env=0.15))
    for o in lean_meshes:
        for sl in o.material_slots:
            k = sl.material.name[5:] if sl.material and sl.material.name.startswith('lean_') else None
            if k: sl.material = F[k]
    for o in origs + [bpy.data.objects.get('S2000_Root')]:
        if o: bpy.data.objects.remove(o)
    for k in M: bpy.data.materials.remove(M[k])
    bpy.ops.outliner.orphans_purge(do_recursive=True) if False else None
    bpy.context.preferences.filepaths.save_version = 0
    for im in (bimg, aimg): im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 's2000_lean.blend'), compress=True)
    PM.use_principled(True)
    # .glb in the same Godot axes as the WRX/BRZ leans (+Z forward, +X left, +Y up): the build is X-forward in Blender,
    # so the rig is re-expressed rotated -90 deg about Z (Blender +X -> -Y -> glTF +Z) for the export only, then restored
    ROT = Matrix.Rotation(-math.pi / 2, 4, 'Z'); rootob = bpy.data.objects['S2000-vehicle']
    LL.conjugate_rig(rootob, ROT)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 's2000_lean.glb'), export_format='GLB', use_visible=True)
    LL.conjugate_rig(rootob, ROT.inverted())
    PM.use_principled(False)
    if '--render' in ARGS:
        render_set(rig, set(), '')
        RK.raking(FR, os.path.join(OUT, 'renders', 'raw', 'clay_raking_side.png'), (0, 7.5, 0.62))
        RK.raking(FR, os.path.join(OUT, 'renders', 'raw', 'clay_raking_side_rear.png'), (0, 7.5, 0.62)) if False else None
if __name__ == '__main__': main()
