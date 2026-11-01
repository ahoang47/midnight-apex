"""BRZ LEAN build: <= 2,000 triangles TOTAL (lower body + greenhouse + mirrors + liners as ONE mono mesh, 4 x 10-sided
wheels, 4 x strut/arm).  Shape = the approved pass-4 geometry (parts/brz_geo.py with the gated BRZ_REAR_TWEAK, exactly
as build_brz_detail.py): lean subset of its blueprint section points on fewer, evenly spread stations + the pass-4
greenhouse rings (base / glass bottom / glass top / roof edge) and roof grid.  Detail (lamps, grille, intakes, panel
lines, badges, plate) is baked from the approved textured brz_lowpoly.blend (opened read-only, never saved over) into a
1024^2 body texture; wheels use the existing made-up 256^2 atlas.  Colour = the approved blue.
  blender -b --factory-startup -P build_brz_lean.py -- [--render]      (python3 make_lean.py runs everything)
Rig (Godot VehicleBody3D / VehicleWheel3D naming), Blender axes as the BRZ build (X = car left, -Y = forward):
  BRZ-vehicle (root, ground, car origin = mid-wheelbase)
  +- BRZ_Body        ONE mesh, origin at the COM estimate (x +.077 = 53 % front, z .46) at ride height
  +- Hub_FL-wheel .. empties at the static hub centres (-> VehicleWheel3D)
  |    +- Steer_FL/FR (front only, about local Z)  +- BRZ_Wheel_XX (origin = hub, spins about the axle)
  +- Susp_FL ..      empties: hub position + steer only, never spin  +- BRZ_Susp_XX (strut + lower arm)"""
import bpy, bmesh, sys, os, math, json, importlib, shutil, subprocess
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'lean'); SRC = os.path.join(HERE, 'brz_lowpoly.blend')
os.environ.setdefault('BRZ_REAR_TWEAK', json.dumps({'p4': [-2.085, 0.95], 'p5': [-2.050, 1.00], 'p6': [-2.012, 0.92], 'p7': [-2.015, 0.80]}))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lean_common')); sys.path.insert(0, os.path.join(HERE, 'parts'))
import leanlib as LL, brz_geo as G
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'wrx_sti', 'parts')); import psx_mat as PM
for m in (LL,): importlib.reload(m)
for d in ('bp', 'tex', 'renders/raw'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
FR = LL.Frame('xleft'); P = 'BRZ'; CAP = 2000
AXF, AXR = G.AXF, G.AXR; TIRE_R, TIRE_W = G.TIRE_OD / 2, G.TIRE_W
TR_F, TR_R = G.TRACK_F / 2, G.TRACK_R / 2
COM = (0.077, 0.46)
BUMP, DROOP, LOCK = 0.045, 0.050, 30.0          # art doc: about +/-4-5 cm travel, +/-30 deg lock
R_WELL, R_LINER = 0.395, 0.405
ARCHES = [dict(xc=G.ARCH_F['xc'], zc=G.ARCH_F['zc'], r=G.ARCH_F['r']), dict(xc=G.ARCH_R['xc'], zc=G.ARCH_R['zc'], r=G.ARCH_R['r'])]
SUB = [0, 1, 3, 4, 5, 6, 7, 9, 11]     # lean subset of the 12-point pass-4 half-section (p5/p6 fender ridge, p7 hood edge)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def stations():
    nose = [2.163, 2.11, 2.058, 1.995, 1.935, 1.85, 1.76]
    fa = [AXF + d for d in (0.368, 0.33, 0.19, 0.0, -0.19, -0.33, -0.368)]
    mid = [0.78, 0.56, 0.32, 0.06, -0.20, -0.45, -0.70]
    ra = [AXR + d for d in (0.376, 0.34, 0.19, 0.0, -0.19, -0.34, -0.376)]
    tail = [-1.72, -1.80, -1.882, -1.963, -2.023, -2.071, -2.11, -2.12]
    return np.array(sorted(set(np.round(nose + fa + mid + ra + tail, 4)), reverse=True))
def lower_grid(X):
    out = []; LOWER_FLOOR.clear()
    for x in X:                                   # = brz_geo.build() for one station (arch lift + flush lip)
        sec, wc = G.section(x); sec = sec.copy(); dx = G.section_dx(x); LOWER_FLOOR.append(float(sec[0, 1]))
        az = G.arch_z(np.array([x]))[0]
        if az > 0:
            ymax = sec[:4, 0].max(); off = [0.0, 0.012, 0.03, 0.055, 0.085]
            for i in range(5):
                if sec[i, 1] < az + off[i]: sec[i, 1] = az + off[i]; sec[i, 0] = ymax - (0.006 if i == 0 else 0)
            for i in range(1, 7): sec[i, 1] = max(sec[i, 1], sec[i - 1, 1] + 0.01)
        out.append([(x + dx[i], sec[i, 0], sec[i, 1]) for i in SUB])
    return np.array(out, float)
LOWER_FLOOR = []
WELL_BOTTOM = {'F': (0.50, 0.40), 'R': (0.60, 0.50)}     # wheel-well floor: roof edge y, wall-foot y (inboard of the tyre)
def loft_open_bottom(P_, X):
    """ring = left p0..p11, right p10..p0 (p0 is off the centre line: the bottom closes across).  Where the arch code
    lifted p0 (wheel wells) the bottom does NOT span across at arch height (that would be a ceiling through the tyre):
    it runs p0 -> well roof (R_WELL about the hub, inboard of the tyre) -> wall foot at the floor -> across -> mirror."""
    S, K, _ = P_.shape; bm = bmesh.new(); rings = []
    for s in range(S):
        half = [P_[s, k] for k in range(K)]
        full = half + [np.array((p[0], -p[1], p[2])) for p in half[-2::-1]]
        rings.append([bm.verts.new(FR.to_bl(p)) for p in full])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n - 1): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    lifted = [P_[s, 0, 2] > LOWER_FLOOR[s] + 0.01 for s in range(S)]
    def bottom(s):                                 # 8-point bottom polyline, left p0 .. right p0
        x = X[s]; p0 = P_[s, 0]; fz = LOWER_FLOOR[s]
        ax = min(ARCHES, key=lambda A: abs(A['xc'] - x)); key = 'F' if ax is ARCHES[0] else 'R'
        ya, yf = WELL_BOTTOM[key]; dx = x - ax['xc']
        za = max(p0[2], ax['zc'] + math.sqrt(max(R_WELL ** 2 - dx * dx, 0))) if lifted[s] else fz
        yl = p0[1] - 0.012
        if not lifted[s]: yl, ya, yf = p0[1] * 0.8, p0[1] * 0.66, p0[1] * 0.52
        pts = [(x, yl, za), (x, ya, za), (x, yf, fz), (x, -yf, fz), (x, -ya, za), (x, -yl, za)]
        return [rings[s][0]] + [bm.verts.new(FR.to_bl(p)) for p in pts] + [rings[s][n - 1]]
    for s in range(S - 1):
        if lifted[s] or lifted[s + 1]:
            A = bottom(s); B = bottom(s + 1)
            for k in range(len(A) - 1): bm.faces.new((A[k + 1], A[k], B[k], B[k + 1]))
        else: bm.faces.new((rings[s][n - 1], rings[s][0], rings[s + 1][0], rings[s + 1][n - 1]))
    for s in (0, S - 1):
        bm.faces.new(rings[s])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0005)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    return bm
KR = [0, 1, 3, 5]                     # greenhouse rings kept: base, glass bottom (belt), glass top, roof edge
def build_cabin(M):
    """pass-4 greenhouse, lean: 4 of its 6 rings (DLO lines kept exactly), full roof grid, 3-tri shark fin."""
    R = G.gh_rings()[KR]; nR, nJ = R.shape[0], R.shape[1]
    bm = bmesh.new(); order = list(range(nJ)) + list(range(nJ - 2, 0, -1)); sgn = [1] * nJ + [-1] * (nJ - 2); n = len(order)
    loops = [[bm.verts.new(FR.to_bl(R[k, j] * [1, s_, 1])) for j, s_ in zip(order, sgn)] for k in range(nR)]
    gtop = KR.index(3)
    for k in range(nR - 1):
        for q in range(n):
            ja, jb = order[q], order[(q + 1) % n]
            f = bm.faces.new((loops[k][q], loops[k][(q + 1) % n], loops[k + 1][(q + 1) % n], loops[k + 1][q]))
            lo, hi = min(ja, jb), max(ja, jb); ws_rg = (hi <= 3) or (lo >= 10); side = (lo >= 4 and hi <= 8)
            f.material_index = 1 if ((ws_rg and k < gtop) or (side and 1 <= k < gtop)) else 0
    RR = G.roof_rows(); nr, nc = RR.shape[0], RR.shape[1]; top = loops[-1]
    def ring_vert(j, left): return top[j] if (left or j in (0, nJ - 1)) else top[n - j]
    grid = [[None] * nc for _ in range(nr)]
    for r in range(nr):
        for c in range(nc):
            left = c < 3; m = abs(c - 3)
            if r == 0: grid[r][c] = ring_vert(m, left)
            elif r == nr - 1: grid[r][c] = ring_vert(nJ - 1 - m, left)
            elif m == 3: grid[r][c] = ring_vert(3 + r, left)
            else: grid[r][c] = bm.verts.new(FR.to_bl(RR[r, c]))
    for r in range(nr - 1):
        for c in range(nc - 1): bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c])).material_index = 0
    zr = lambda x: float(G.genv(np.array([x]))[0]) - 0.004
    A = bm.verts.new(FR.to_bl((-0.66, 0, zr(-0.66)))); Bl = bm.verts.new(FR.to_bl((-0.87, 0.035, zr(-0.87)))); Br = bm.verts.new(FR.to_bl((-0.87, -0.035, zr(-0.87))))
    Tp = bm.verts.new(FR.to_bl((-0.835, 0, 1.325)))
    for fv in ((A, Bl, Tp), (Br, A, Tp), (Bl, Br, Tp)): bm.faces.new(fv).material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = LL.obj_from_bm(P + '_Cabin', bm, [M['paint'], M['glass'], M['under']]); LL.smooth(ob, 62); return ob
def geometry(M):
    X = stations(); Gd = lower_grid(X)
    Gd = LL.raise_wells(Gd, X, ARCHES, TIRE_R, R_WELL, edge_keep=0.012)
    body = LL.obj_from_bm(P + '_Body', loft_open_bottom(Gd, X), [M['paint'], M['glass'], M['under']]); LL.smooth(body, 45)
    cab = build_cabin(M)
    out = [cab]
    for s in (1, -1):            # minimal mirror (12 tris) on the pass-4 housing: x .26-.445, out to y .995, z .925-1.03
        r0 = [(0.445, s * 0.85, 0.950), (0.445, s * 0.85, 1.010), (0.445, s * 0.95, 1.010), (0.445, s * 0.95, 0.950)]
        r1 = [(0.26, s * 0.835, 0.928), (0.26, s * 0.835, 1.027), (0.26, s * 0.995, 1.027), (0.26, s * 0.995, 0.928)]
        out.append(LL.tube(FR, P + ('_Mirror_L' if s > 0 else '_Mirror_R'), [r0, r1], [M['paint']], None, (True, True), 30))
    for nm, xc, yc in corner_list():
        s_ = int(np.argmin(np.abs(X - xc))); yout = Gd[s_, :, 1].max() - 0.025
        yin = 0.48 if nm[0] == 'F' else abs(yc) - TIRE_W / 2 - 0.035
        out.append(LL.liner(FR, f'{P}_Liner_{nm}', xc, TIRE_R, 1 if yc > 0 else -1, R_LINER, yin, yout, [M['under']], seg=7))
    return body, out, Gd, X
def corner_list():
    return (('FL', AXF, TR_F), ('FR', AXF, -TR_F), ('RL', AXR, TR_R), ('RR', AXR, -TR_R))
def build_rig(body, mono_parts, M):
    root = LL.empty(P + '-vehicle', (0, 0, 0), None, 0.5, 'ARROWS')
    lines = []
    for ob in [body] + mono_parts:
        ob.data.calc_loop_triangles(); lines.append(f'{ob.name:18s} {len(ob.data.loop_triangles):5d}')
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in mono_parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    c = FR.to_bl((COM[0], 0, COM[1])); body.data.transform(Matrix.Translation(-c)); body.location = c; body.parent = root
    rig = dict(FR=FR, body=body, com=COM, hub={}, steer={}, susp={}, hub_rest={})
    for nm, xc, yc in corner_list():
        loc = FR.to_bl((xc, yc, TIRE_R)); hb = LL.empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F': st = LL.empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        LL.wheel(FR, f'{P}_Wheel_{nm}', M['wheel'], par, 1 if yc > 0 else -1, TIRE_R, TIRE_W, (0.0, 0.5, 0.5, 1.0), (0.0, 0.0, 0.5, 0.25), (0.885, 0.33))
        sp = LL.empty(f'Susp_{nm}', loc, root, 0.15, 'PLAIN_AXES'); rig['susp'][nm] = sp
        LL.susp(FR, f'{P}_Susp_{nm}', M['under'], sp, 1 if yc > 0 else -1, nm[0] == 'F')
    bpy.context.view_layer.update()
    rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
    body.data.calc_loop_triangles(); mono = len(body.data.loop_triangles)
    wl = [o for o in bpy.data.objects if o.name.startswith(P + '_Wheel_')]; sl = [o for o in bpy.data.objects if o.name.startswith(P + '_Susp_')]
    for o in wl + sl: o.data.calc_loop_triangles()
    wheels = sum(len(o.data.loop_triangles) for o in wl); susp = sum(len(o.data.loop_triangles) for o in sl)
    lines += ['', f'MONO {P}_Body {mono} (lower body + greenhouse + mirrors + liners)', f'wheels (4 x 10-sided) {wheels}',
              f'suspension (4 x strut + arm) {susp}', f'TOTAL rendered {mono + wheels + susp}  (cap {CAP}: {"OK" if mono + wheels + susp <= CAP else "OVER"})']
    open(os.path.join(OUT, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    return rig, root
REF = lambda o: o.name.startswith('BP') or o.name.startswith('Blueprint')
def render_set(hide, prefix, textured=True):
    import render_kit as RK
    rd = os.path.join(OUT, 'renders', 'raw')
    for o in bpy.data.objects:
        if o.type == 'MESH' and not REF(o): o.hide_render = (o in hide) or o.name.startswith('orig_BRZ_FX')
    shots = {'front34': ((5.6, 5.0, 1.35), (0.25, 0.0, 0.60), 55), 'rear34': ((-5.8, -4.8, 1.45), (-0.25, 0.0, 0.62), 55)}
    ORTHO = {'side': ((0, 8, 0.65), (0, 0, 0.65), None), 'front': ((8, 0, 0.65), (0, 0, 0.65), None), 'rear': ((-8, 0, 0.65), (0, 0, 0.65), None),
             'top': ((0, 0, 8), (0, 0, 0), (-1, 0, 0))}
    if textured:
        RK.eevee()
        for k, (loc, tg, lens) in shots.items(): RK.cam(FR, 'CAMt', loc, tg, lens); RK.shoot(os.path.join(rd, f'{prefix}tex_{k}.png'), (640, 448))
        for k, (loc, tg, ir) in ORTHO.items():
            RK.cam(FR, 'CAMo', loc, tg, ortho=5.0, image_right=ir); RK.shoot(os.path.join(rd, f'{prefix}tex_{k}.png'), (1000, 1000))
    RK.clay(sil=True)
    for k, (loc, tg, ir) in ORTHO.items():
        RK.cam(FR, 'CAMs', loc, tg, ortho=5.0, image_right=ir); RK.shoot(os.path.join(rd, f'{prefix}sil_{k}.png'), (1000, 1000))
    RK.clay()
    RK.cam(FR, 'CAMc', (0, 8, 0.65), (0, 0, 0.65), ortho=5.0); RK.shoot(os.path.join(rd, f'{prefix}clay_side.png'), (1000, 450))
    RK.cam(FR, 'CAMc', *shots['front34'][:2], shots['front34'][2]); RK.shoot(os.path.join(rd, f'{prefix}clay_front34.png'), (1000, 700))
    for o in bpy.data.objects: o.hide_render = REF(o)
def main():
    import render_kit as RK; importlib.reload(RK)
    bpy.ops.wm.open_mainfile(filepath=SRC)
    for o in bpy.data.objects:
        if REF(o): o.hide_render = True; o.hide_set(True)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and not REF(o): o.name = 'orig_' + o.name
    M = {k: bpy.data.materials.new('lean_' + k) for k in ('paint', 'glass', 'under', 'wheel')}
    for m in M.values(): m.use_nodes = True
    body, pp, Gd, X = geometry(M)
    if '--render' in ARGS:
        render_set(set([body] + pp), 'old_', textured=False)
    rig, root = build_rig(body, pp, M)
    rep = LL.clearance(rig, P, [P + '_Body'], BUMP, DROOP, LOCK)
    json.dump(rep, open(os.path.join(OUT, 'bp', 'clearance.json'), 'w'), indent=1); LL.set_pose(rig)
    lean_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(P + '_')]
    T = LL.tri_soup(FR, [o for o in lean_meshes if '_Susp_' not in o.name])
    np.save(os.path.join(OUT, 'bp', 'tris_carframe.npy'), T)
    # bake sources: the approved textured meshes; the parts object minus its wheels (they would print onto the arch lips)
    parts = bpy.data.objects['orig_BRZ_Parts']; pc = parts.copy(); pc.data = parts.data.copy(); pc.name = 'orig_BRZ_Parts_nowheels'
    bpy.context.scene.collection.objects.link(pc)
    bm = bmesh.new(); bm.from_mesh(pc.data); bm.verts.ensure_lookup_table(); seen = set(); drop = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; isl = []; seen.add(v.index)
        while st:
            a = st.pop(); isl.append(a)
            for e in a.link_edges:
                o_ = e.other_vert(a)
                if o_.index not in seen: seen.add(o_.index); st.append(o_)
        co = np.array([a.co[:] for a in isl])
        if np.linalg.norm(co.max(0) - co.min(0)) > 0.4: drop += isl
    bmesh.ops.delete(bm, geom=list(set(drop)), context='VERTS'); bm.to_mesh(pc.data); bm.free()
    srcs = [bpy.data.objects[n] for n in ('orig_BRZ_Body', 'orig_BRZ_Lamps', 'orig_BRZ_Under', 'orig_BRZ_Exhaust_L', 'orig_BRZ_Exhaust_R')] + [pc]
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('orig_') and o not in srcs: o.hide_render = True
    body_png = LL.bake_lean(body, srcs, os.path.join(OUT, 'tex'), 'brz', extrusion=0.04, ray=0.09)
    env_png = os.path.join(OUT, 'tex', 'env.png'); shutil.copy(os.path.join(HERE, 'brz_env.png'), env_png)
    atlas_png = os.path.join(OUT, 'tex', 'brz_wheel_atlas.png'); shutil.copy(os.path.join(HERE, 'brz_atlas.png'), atlas_png)
    PM.set_env(bpy.data.images.load(env_png)); bimg = bpy.data.images.load(body_png); aimg = bpy.data.images.load(atlas_png)
    F = dict(paint=PM.fake_mat('BRZ_Paint_Body', img=bimg, ambient=0.48, key=0.62, spec=0.45, shin=55, env=0.38),
             glass=PM.fake_mat('BRZ_Glass', rgb=(0.010, 0.014, 0.022), ambient=1.0, key=0.0, spec=0.6, shin=90, env=0.45, env_tint=(0.55, 0.70, 1.0)),
             under=PM.fake_mat('BRZ_Under', rgb=(0.006, 0.006, 0.007), ambient=1.0, key=0.0, spec=0.0, env=0.0),
             wheel=PM.fake_mat('BRZ_Wheel_Atlas', img=aimg, ambient=0.55, key=0.55, spec=0.25, shin=30, env=0.15))
    for o in lean_meshes:
        for sl in o.material_slots:
            if sl.material and sl.material.name.startswith('lean_'): sl.material = F[sl.material.name[5:]]
    for o in list(bpy.data.objects):
        if o.name.startswith('orig_'): bpy.data.objects.remove(o)
    for k in M: bpy.data.materials.remove(M[k])
    bpy.context.preferences.filepaths.save_version = 0
    for im in (bimg, aimg): im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'brz_lean.blend'), compress=True)
    PM.use_principled(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'brz_lean.glb'), export_format='GLB', use_visible=True)
    PM.use_principled(False)
    if '--render' in ARGS:
        render_set(set(), '')
        RK.raking(FR, os.path.join(OUT, 'renders', 'raw', 'clay_raking_side.png'), (0, 7.5, 0.62))
if __name__ == '__main__': main()
