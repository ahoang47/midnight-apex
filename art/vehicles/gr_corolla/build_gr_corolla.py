"""Toyota GR Corolla (2022) LEAN CLAY build: <= 2,000 triangles TOTAL (body + aero + mirrors + liners + floor + wheels +
struts + FX), one mono body mesh, Godot VehicleBody3D / VehicleWheel3D rig.  Grey clay only (no texture) for the shape
sign-off.  Blueprint-only: every body line is a faired curve from the Dimensions.com vector drawing (bp/).
  python3 bp/extract.py && python3 bp/fair.py                     (cd bp)
  blender -b --factory-startup -P build_gr_corolla.py -- [--render]
  python3 bp/iou.py && python3 bp/deliver.py
or: python3 make_all.py
Rig:  GRC-vehicle (root, ground, mid-wheelbase)
        +- GRC_Body          ONE mesh, origin at the centre-of-mass estimate (x COM_X, z COM_Z) at ride height
        +- Hub_FL-wheel ...  empties at the static hub centres (Godot VehicleWheel3D)
        |    +- Steer_FL/FR  front only, rotates about local Z (vertical axis through the hub)
        |         +- GRC_Wheel_FL   10-sided wheel, origin = hub, spins about local X
        +- Susp_FL ...       follow nodes (godot/susp_follow.gd): hub position + steer, never spin
             +- GRC_Susp_FL  strut + lower arm (16 tris)"""
import bpy, bmesh, sys, os, math, json, importlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'parts')); os.chdir(HERE)
import numpy as np
import gr_geo as G; importlib.reload(G)
CAP = 2000; P = 'GRC'
COM_X, COM_Z = 0.26, 0.52          # estimate: ~60/40 front weight split (FF-based AWD, engine ahead of the front axle) x WB; z typical C-segment hatch
BUMP_F, BUMP_R, DROOP = 0.035, 0.045, 0.050
LOCK, ROLL = 30.0, 3.0
D = G.D
# ------------------------------------------------------------------ helpers (same as the WRX lean build)
def to_bl(p): return Vector((p[1], -p[0], p[2]))
def car(v): return np.array([-v[1], v[0], v[2]])
def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1); return m
def obj_from_bm(name, bm, mats, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    if parent is not None: ob.parent = parent
    return ob
def smooth(ob, angle=40):
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle), keep_sharp_edges=True); ob.select_set(False)
def empty(name, loc, parent=None, size=0.12, kind='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    bpy.context.collection.objects.link(e); e.parent = parent; e.location = loc; return e
def tri_count(ob): ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)
QC = {}
def face_check(bm, faces):
    flipped = skew = degen = 0; worst = 0.0; where = []
    for f in faces:
        if f.calc_area() < 1e-7: degen += 1; continue
        c = car(f.calc_center_median()); nc = car(f.normal)
        if abs(c[1]) > 0.05 and abs(nc[1]) > 0.3 and np.sign(nc[1]) != np.sign(c[1]): flipped += 1
        if len(f.verts) == 4:
            p = [v.co for v in f.verts]; nn = (p[1] - p[0]).cross(p[2] - p[0])
            if nn.length < 1e-12: continue
            dev = 100 * abs((p[3] - p[0]).dot(nn.normalized())) / max((p[2] - p[0]).length, (p[3] - p[1]).length)
            worst = max(worst, dev); skew += dev > 5
            if dev > 5: where.append((round(dev, 1), [round(float(v), 3) for v in c]))
    return dict(faces=len(faces), flipped=flipped, degenerate=degen, nonplanar_gt5pct=int(skew), worst_nonplanar_pct=round(worst, 1), worst_at=sorted(where, reverse=True)[:6])
# ------------------------------------------------------------------ body loft
def xr(cls, src='side'):
    a = np.array(D[src][cls]); return float(a[:, 0].min()), float(a[:, 0].max())
GL_SIDE = xr('DLO_GLASS'); PILLAR_B = xr('DLO_PILLAR'); HATCH = xr('HATCH_GLASS_S')
WS = (0.30, G.XWS - 0.02)
def build_body(M):
    X = G.stations(); secs = [G.section(x) for x in X]; NPn = G.NP; C = 2 * NPn - 1; S_ = len(X)
    bm = bmesh.new(); vv = []
    for s in range(S_):
        row = [None] * C
        for i in range(NPn):
            y, z = secs[s][i]; row[i] = bm.verts.new(to_bl((X[s], y, z)))
            if i < NPn - 1: row[C - 1 - i] = bm.verts.new(to_bl((X[s], -y, z)))
        vv.append(row)
    F = []
    for s in range(S_ - 1):
        for c in range(C - 1):
            q = (vv[s][c], vv[s + 1][c], vv[s + 1][c + 1], vv[s][c + 1])
            F.append((bm.faces.new(q), s, c))
    for s in range(S_ - 1):                                        # floor plates under the overhangs only
        xa, xb = X[s], X[s + 1]
        if not (min(xa, xb) > G.ARCH_F['xc'] + G.ARCH_F['r'] - 0.01 or max(xa, xb) < G.ARCH_R['xc'] - G.ARCH_R['r'] + 0.01): continue
        F.append((bm.faces.new((vv[s][0], vv[s][C - 1], vv[s + 1][C - 1], vv[s + 1][0])), s, -1))
    for s, rev in ((0, False), (S_ - 1, True)):
        ring = vv[s][:]; F.append((bm.faces.new(ring[::-1] if rev else ring), s, -2))
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _, _ in F])
    for f, s, c in F:                                              # clay classes: 0 paint, 1 glass, 2 under, 4 trim
        x = 0.5 * (X[s] + X[min(s + 1, S_ - 1)]); i = c if c < NPn - 1 else C - 2 - c; m = 0
        if c == -1: m = 2
        elif c >= 0 and i == 4:                                    # belt -> glass top strip
            if PILLAR_B[0] - 0.01 < x < PILLAR_B[1] + 0.01: m = 4
            elif GL_SIDE[0] + 0.01 < x < GL_SIDE[1] - 0.01: m = 1
        elif c >= 0 and i >= 5 and WS[0] < x < WS[1]: m = 1          # windshield
        elif c >= 0 and i >= 4 and HATCH[0] + 0.02 < x < G.XROOF - 0.15: m = 1   # hatch glass (under the wing)
        f.material_index = m
    def mark(col, s0, s1):
        for cc in (col, C - 1 - col):
            for s in range(max(s0, 0), min(s1, S_ - 1)):
                e = bm.edges.get((vv[s][cc], vv[s + 1][cc]))
                if e: e.smooth = False
    idx = lambda x: int(np.argmin(np.abs(X - x)))
    mark(4, 0, S_); mark(5, idx(1.06), idx(-1.20))
    QC['body'] = face_check(bm, [f for f, s, c in F if c >= 0])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    ob = obj_from_bm(P + '_Body', bm, [M['paint'], M['glass'], M['under'], M['lamp'], M['trim']]); smooth(ob, 42)
    return ob, X
# ------------------------------------------------------------------ parts
MATS = None
def tube(name, rings, mats, parent=None, cap=(True, True), angle=40, mi=None):
    bm = bmesh.new(); R = [[bm.verts.new(to_bl(p)) for p in r] for r in rings]; n = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if cap[0]: bm.faces.new(R[0])
    if cap[1]: bm.faces.new(R[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.material_index = mi(f) if mi else 0
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    ob = obj_from_bm(name, bm, mats, parent); smooth(ob, angle); return ob
def _dp(P, eps):
    if len(P) < 3: return P
    a, b = P[0], P[-1]; d = b - a; L = np.linalg.norm(d) + 1e-12
    dist = np.abs(d[0] * (P[:, 1] - a[1]) - d[1] * (P[:, 0] - a[0])) / L; i = int(np.argmax(dist))
    if dist[i] > eps: return np.vstack([_dp(P[:i + 1], eps)[:-1], _dp(P[i:], eps)])
    return np.vstack([a, b])
def simplify(poly, eps):
    """Douglas-Peucker on a closed polygon (split at the two farthest-apart vertices)."""
    P = np.asarray(poly, float); i = 0; j = int(np.argmax(np.linalg.norm(P - P[0], axis=1)))
    A = _dp(P[i:j + 1], eps); B = _dp(np.vstack([P[j:], P[:1]]), eps)
    return np.vstack([A[:-1], B[:-1]])
def hull2d(P):
    pts = sorted(map(tuple, np.asarray(P, float))); cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])
def build_wing(M):
    """roof wing (traced): side-view outline of the wing (WING_S, simplified) swept across the plan width (WING_T) and
    tilted to the rear-view span at its top (WING_R).  One closed prism."""
    poly = max(D['side_poly']['WING_S'], key=len); S2 = simplify(poly, 0.012)
    if np.sum(S2[:, 0] * np.roll(S2[:, 1], -1) - np.roll(S2[:, 0], -1) * S2[:, 1]) < 0: S2 = S2[::-1]
    wt = np.array(D['top_left']['WING_T']); wx = np.unique(np.round(wt[:, 0], 2)); wy = np.array([wt[np.abs(wt[:, 0] - q) < 0.006, 2].max() for q in wx])
    span = lambda x: float(np.interp(x, wx, wy))
    rL = [(x, span(x), z) for x, z in S2]; rR = [(x, -span(x), z) for x, z in S2]
    ob = tube(P + '_Wing', [rL, rR], [M['paint']], cap=(True, True), angle=35)
    return ob, len(S2)
def build_fin(M):
    """shark-fin antenna: the bump on the side-silhouette top over the roof (x -1.33..-1.12), 3 visible tris + base."""
    sc = np.array(D['side_cols']); m = (sc[:, 0] > -1.36) & (sc[:, 0] < -1.08)
    rise = sc[m, 2] - np.array([G.ZT(x) for x in sc[m, 0]]); k = rise > 0.006; xs = sc[m, 0][k]
    x0, x1 = float(xs.min()), float(xs.max()); ip = int(np.argmax(rise)); xp = float(sc[m, 0][ip]); zp = float(sc[m, 2][ip])
    bm = bmesh.new()
    a = bm.verts.new(to_bl((x1, 0.0, G.ZT(x1) - 0.004))); b = bm.verts.new(to_bl((x0, 0.035, G.ZT(x0) - 0.004)))
    c = bm.verts.new(to_bl((x0, -0.035, G.ZT(x0) - 0.004))); t = bm.verts.new(to_bl((xp, 0.0, zp)))
    for f in ((a, b, t), (b, c, t), (c, a, t), (a, c, b)): bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(P + '_Fin', bm, [M['paint']]), (x0, x1, zp)
def build_mirror(name, s, M):
    """door mirror: front view y .825-1.024, z .848-1.052; side x .516-.782; plan x .525-.705 (traced boxes)."""
    fm = [np.array(p) for p in D['front_poly']['MIRROR_F'] if np.mean(np.array(p)[:, 0]) > 0]; fy = np.vstack(fm)
    sm = np.vstack([np.array(p) for p in D['side_poly']['MIRROR_S']])
    y0, y1 = 0.80, float(fy[:, 0].max()); z0, z1 = float(fy[:, 1].min()), float(fy[:, 1].max()); xa, xb = float(sm[:, 0].min()), float(sm[:, 0].max())
    r0 = [(xb, s * y0, z0 + 0.05), (xb, s * y0, z1 - 0.04), (xb - 0.10, s * y0, z1 - 0.04), (xb - 0.10, s * y0, z0 + 0.05)]
    r1 = [(xb - 0.07, s * y1, z0), (xb - 0.07, s * y1, z1), (xa, s * y1, z1), (xa, s * y1, z0)]
    return tube(name, [r0, r1], [M['trim']], angle=30)
def liner_spec(front):
    reach = math.hypot(G.TIRE_R, G.TIRE_W / 2)
    R = reach + (BUMP_F if front else BUMP_R) + 0.018
    yin = G.TRACK_F / 2 - (G.TIRE_R * math.sin(math.radians(LOCK)) + G.TIRE_W / 2 * math.cos(math.radians(LOCK))) - 0.02 if front else G.TRACK_R / 2 - G.TIRE_W / 2 - 0.03
    return R, yin, 0.896
def build_liner(name, xc, side, front, M):
    R, yin, yout = liner_spec(front); ang = np.radians(np.linspace(-8, 188, 6)); bm = bmesh.new()
    o = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yout, G.HUB_Z + R * math.sin(a)))) for a in ang]
    i = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yin, G.HUB_Z + R * math.sin(a)))) for a in ang]
    for k in range(len(ang) - 1): bm.faces.new((o[k], o[k + 1], i[k + 1], i[k]))
    bm.faces.new(i[::-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.normal_flip(); f.material_index = 0
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return obj_from_bm(name, bm, [M['under']])
def build_floor(M):
    x0 = G.ARCH_R['xc'] + 0.40; x1 = G.ARCH_F['xc'] - 0.42
    bm = bmesh.new(); v = [bm.verts.new(to_bl(p)) for p in ((x1, 0.48, 0.30), (x1, -0.48, 0.30), (x0, -0.48, 0.30), (x0, 0.48, 0.30))]
    f = bm.faces.new(v); f.normal_update()
    if f.normal.z > 0: f.normal_flip()
    return obj_from_bm(P + '_Under', bm, [M['under']])
def build_exhaust(M, tree):
    """triple exhaust (rear view circles: y -.50 / 0 / +.50 at z .283), 6-sided pipes standing 4 cm proud of the
    traced diffuser face + a dark back cap inside."""
    obs = []
    for y, r in ((0.50, 0.040), (0.0, 0.045), (-0.50, 0.040)):
        z = 0.283; hit = tree.ray_cast(to_bl((-3.0, y, z)), to_bl((1, 0, 0)) - to_bl((0, 0, 0)), 3.0)[0]
        xf = car(hit)[0] if hit is not None else -2.08
        ring = lambda x: [(x, y + r * math.cos(a), z + r * math.sin(a)) for a in np.radians(np.arange(0, 360, 60) + 30)]
        bm = bmesh.new(); R0 = [bm.verts.new(to_bl(p)) for p in ring(xf - 0.040)]; R1 = [bm.verts.new(to_bl(p)) for p in ring(xf + 0.03)]
        for k in range(6): bm.faces.new((R0[k], R0[(k + 1) % 6], R1[(k + 1) % 6], R1[k]))
        Rc = [bm.verts.new(to_bl(p)) for p in ring(xf - 0.015)]; cf = bm.faces.new(Rc[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        for f in bm.faces: f.material_index = 1 if f is cf else 0
        if cf.normal.dot(to_bl((-1, 0, 0)) - to_bl((0, 0, 0))) < 0: cf.normal_flip()
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        o = obj_from_bm(P + f'_Exhaust_{"L" if y > 0 else ("R" if y < 0 else "C")}', bm, [M['trim'], M['under']]); smooth(o, 70); obs.append(o)
    return obs
def build_wheel(name, M, parent, side, seg=10):
    r = G.TIRE_R; h = G.TIRE_W / 2; bm = bmesh.new(); ro, ri = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        ro.append(bm.verts.new(Vector((side * h, r * math.cos(a), r * math.sin(a))))); ri.append(bm.verts.new(Vector((-side * h, r * math.cos(a), r * math.sin(a)))))
    for k in range(seg): bm.faces.new((ro[k], ro[(k + 1) % seg], ri[(k + 1) % seg], ri[k]))
    fo = bm.faces.new(ro); fi = bm.faces.new(ri[::-1]); fo.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bmesh.ops.triangulate(bm, faces=[fo, fi])
    ob = obj_from_bm(name, bm, [M['wheel'], M['rim']], parent); smooth(ob, 40); return ob
def build_susp(name, M, parent, side, front):
    bm = bmesh.new()
    def beam(p0, p1, w, t):
        p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized(); up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1))
        a = d.cross(up).normalized() * w; b = d.cross(a).normalized() * t
        R0 = [bm.verts.new(p0 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        R1 = [bm.verts.new(p1 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for k in range(4): bm.faces.new((R0[k], R0[(k + 1) % 4], R1[(k + 1) % 4], R1[k]))
    ins = -side
    beam((ins * 0.19, 0.0, 0.0), (ins * 0.17, 0.0, 0.30 if front else 0.27), 0.035, 0.035)
    beam((ins * 0.17, 0.0, -0.13), (ins * 0.47, 0.0, -0.12), 0.06, 0.012)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(name, bm, [M['under']], parent)
# ------------------------------------------------------------------ light molding: pockets cut from traced outlines
def _resample(Pl, n):
    Pl = np.asarray(Pl, float); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([Pl, Pl[:1]]), axis=0), axis=1))]
    t = np.linspace(0, L[-1], n, endpoint=False)
    return np.c_[np.interp(t, L, np.r_[Pl[:, 0], Pl[0, 0]]), np.interp(t, L, np.r_[Pl[:, 1], Pl[0, 1]])]
def _smooth_outline(Pl, n):
    """Fourier low-pass of a traced closed outline (keeps the first n//2 harmonics), then n even points."""
    Q = _resample(Pl, 256); z = Q[:, 0] + 1j * Q[:, 1]; Fz = np.fft.fft(z); k = max(3, n // 2)
    Fz[k + 1:-k] = 0; zz = np.fft.ifft(Fz); Q = np.c_[zz.real, zz.imag]; return _resample(Q, n)
POCKETS = []          # report
def pocket_cutter(name, outline2d, view, depth, n, tree, mats=(3, 4), mirror=False):
    """prism along the view axis: rim = traced outline (view plane, smoothed, n points); the floor = the body surface hit
    along the axis, stepped `depth` inward (capped at 2.5x depth along the axis); front cap 0.4 m outside.  Returns
    (bm verts/faces added to `bm_all`).  view: front (axis -x), rear (+x), top (-z), side (-y, car's left; mirrored)."""
    O = _smooth_outline(outline2d, n)
    if np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) < 0: O = O[::-1]
    def P3(a, b, t):          # 2D (a, b) + axis coordinate t -> car xyz
        if view in ('front', 'rear'): return np.array([t, a, b])
        if view == 'top': return np.array([a, b, t])
        return np.array([a, t, b])
    ax = {'front': np.array([-1., 0, 0]), 'rear': np.array([1., 0, 0]), 'top': np.array([0, 0, -1.]), 'side': np.array([0, -1., 0])}[view]
    far = {'front': 3.0, 'rear': -3.0, 'top': 2.5, 'side': 1.5}[view]
    hits, nrm = [], []
    for a, b in np.vstack([O, O.mean(0)[None]]):
        o = P3(a, b, far); h = tree.ray_cast(to_bl(o), to_bl(ax) - to_bl((0, 0, 0)), 6.0)
        if h[0] is None: raise RuntimeError(f'{name}: ray missed at {a:.3f},{b:.3f}')
        hits.append(car(h[0])); nn = car(h[1]); nrm.append(nn if nn @ ax < 0 else -nn)
    hits, nrm = np.array(hits), np.array(nrm)
    step = np.minimum(depth / np.maximum(-(nrm @ ax), 0.4), 1.6 * depth)
    floor = hits + step[:, None] * ax[None]
    front = np.array([P3(a, b, far * 0.15 + (hits[:, {'front': 0, 'rear': 0, 'top': 2, 'side': 1}[view]].max() if far > 0 else hits[:, {'front': 0, 'rear': 0, 'top': 2, 'side': 1}[view]].min()) * 0.0) for a, b in O])
    # front cap: 12 cm outside the outermost rim hit along the axis
    k_ax = {'front': 0, 'rear': 0, 'top': 2, 'side': 1}[view]; ext = hits[:, k_ax].max() + 0.12 if far > 0 else hits[:, k_ax].min() - 0.12
    front = np.array([P3(a, b, ext) for a, b in O])
    POCKETS.append(dict(name=name, view=view, n=n, depth_m=depth, step_mm=np.round(step * 1000, 1).tolist()))
    out = [(floor, front)]
    if mirror: out.append((floor * np.array([1, -1, 1]), front * np.array([1, -1, 1])))
    return out
def cutter_object(specs, M):
    bm = bmesh.new()
    for floor, front, fm, wm in specs:
        n = len(front); fl = [bm.verts.new(to_bl(tuple(p))) for p in floor[:-1]]; vc = bm.verts.new(to_bl(tuple(floor[-1])))
        fr = [bm.verts.new(to_bl(tuple(p))) for p in front]
        fs = []
        for k in range(n): f = bm.faces.new((fl[k], fl[(k + 1) % n], vc)); f.material_index = fm; fs.append(f)
        f = bm.faces.new(fr); f.material_index = wm; fs.append(f)
        for k in range(n): f = bm.faces.new((fl[k], fr[k], fr[(k + 1) % n], fl[(k + 1) % n])); f.material_index = wm; fs.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    return obj_from_bm('POCKET_CUTTER', bm, [M['paint'], M['glass'], M['under'], M['lamp'], M['trim']])
def cut(body, cutter):
    n0 = tri_count(body)
    md = body.modifiers.new('pocket', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = cutter
    md.material_mode = 'TRANSFER'; md.use_hole_tolerant = True
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier='pocket')
    bpy.data.objects.remove(cutter, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), use_dissolve_boundaries=False, verts=bm.verts[:], edges=bm.edges[:], delimit={'MATERIAL'})
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(body.data); bm.free(); n1 = tri_count(body); print('POCKETS cut: tris', n0, '->', n1); return n0, n1
def bvh_of(objs):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    tr = BVHTree.FromBMesh(bm); bm.free(); return tr
def glow_quads(M, lamp_poly):
    """FX head lamp glow quads (WRX convention: separate object, hidden in clay renders, counted in the budget)."""
    O = np.array(lamp_poly); c = O.mean(0); s = 0.5 * (O.max(0) - O.min(0)).max()
    tree = bvh_of([bpy.data.objects[P + '_Body']]); h = tree.ray_cast(to_bl((3.0, c[0], c[1])), to_bl((-1, 0, 0)) - to_bl((0, 0, 0)), 6.0)[0]
    x = car(h)[0] + 0.02; bm = bmesh.new()
    for sd in (1, -1):
        q = [(x, sd * (c[0] - s), c[1] - s * 0.5), (x, sd * (c[0] + s), c[1] - s * 0.5), (x, sd * (c[0] + s), c[1] + s * 0.5), (x, sd * (c[0] - s), c[1] + s * 0.5)]
        vs = [bm.verts.new(to_bl(p)) for p in q]; f = bm.faces.new(vs if sd < 0 else vs[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if car(f.normal)[0] < 0: f.normal_flip()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    o = obj_from_bm(P + '_FX_HeadGlow', bm, [M['glow']]); o.hide_render = True; return o
# ------------------------------------------------------------------ rig
def set_pose(rig, heave=0.0, roll=0.0, pitch=0.0, steer=0.0, wheel_dz=None):
    body = rig['body']; body.location = (to_bl((COM_X, 0, 0)).x, to_bl((COM_X, 0, 0)).y, COM_Z + heave)
    body.rotation_euler = (math.radians(-pitch), math.radians(-roll), 0)
    for k, st in rig['steer'].items(): st.rotation_euler = (0, 0, math.radians(steer))
    for k, hb in rig['hub'].items(): hb.location = Vector(rig['hub_rest'][k]) + Vector((0, 0, (wheel_dz or {}).get(k, 0.0)))
    for k, sp in rig['susp'].items():
        sp.location = rig['hub'][k].location; sp.rotation_euler = (0, 0, math.radians(steer) if k[0] == 'F' else 0.0)
    bpy.context.view_layer.update()
def rel_travel(rig):
    inv = rig['body'].matrix_world.inverted()
    return {k: round((inv @ hb.matrix_world.translation).z - rig['hub_body_rest'][k], 4) for k, hb in rig['hub'].items()}
def clearance(rig):
    """9-pose test: steer {-LOCK, 0, +LOCK} x travel {bump, static, droop} on all four corners at once (front bump BUMP_F,
    rear BUMP_R); tyre vs the mono body (shell, liners, floor, aero, mirrors): BVH overlap + nearest tyre-vertex gap."""
    body = rig['body']; rep = {'spec': dict(bump_front=BUMP_F, bump_rear=BUMP_R, droop=DROOP, lock_deg=LOCK), 'poses': []}
    worst = None; wf = None
    for st in (-LOCK, 0.0, LOCK):
        for tv in ('bump', 'static', 'droop'):
            dz = {k: (BUMP_F if k[0] == 'F' else BUMP_R) if tv == 'bump' else (0.0 if tv == 'static' else -DROOP) for k in ('FL', 'FR', 'RL', 'RR')}
            set_pose(rig, steer=st, wheel_dz=dz); tb = bvh_of([body]); row = {'pose': f'steer {st:+.0f} deg, {tv}', 'corners': {}}
            for k in ('FL', 'FR', 'RL', 'RR'):
                w = bpy.data.objects[P + '_Wheel_' + k]; bm = bmesh.new(); bm.from_mesh(w.data); bm.transform(w.matrix_world)
                tw = BVHTree.FromBMesh(bm)
                # densify the tyre surface for the gap estimate (rim rings + tread midpoints)
                pts = [v.co.copy() for v in bm.verts] + [f.calc_center_median() for f in bm.faces] + [(e.verts[0].co + e.verts[1].co) / 2 for e in bm.edges]
                bm.free(); ov = len(tw.overlap(tb)); dmin = 9.0
                for p in pts:
                    r = tb.find_nearest(p, 0.3)
                    if r[0] is not None and r[3] < dmin: dmin = r[3]
                row['corners'][k] = dict(overlaps=ov, min_gap_m=round(dmin, 4))
                if worst is None or dmin < worst[0]: worst = (dmin, row['pose'], k)
                if k[0] == 'F' and (wf is None or dmin < wf[0]): wf = (dmin, row['pose'], k)
            rep['poses'].append(row)
    rep['all_clear'] = all(c['overlaps'] == 0 for r in rep['poses'] for c in r['corners'].values())
    rep['tightest'] = dict(gap_m=round(worst[0], 4), pose=worst[1], corner=worst[2])
    rep['tightest_front'] = dict(gap_m=round(wf[0], 4), pose=wf[1], corner=wf[2])
    set_pose(rig); print('CLEARANCE all_clear', rep['all_clear'], rep['tightest'], rep['tightest_front'])
    for r in rep['poses']:
        bad = {k: c['overlaps'] for k, c in r['corners'].items() if c['overlaps']}
        if bad: print('   overlap', r['pose'], bad)
    return rep
# ------------------------------------------------------------------ main
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = dict(paint=mat('clay', (0.66, 0.66, 0.66), 0.55), glass=mat('clay_glass', (0.16, 0.17, 0.19), 0.3),
             under=mat('under', (0.02, 0.02, 0.02), 1.0), trim=mat('clay_trim', (0.08, 0.08, 0.085), 0.8),
             wheel=mat('clay_wheel', (0.12, 0.12, 0.12), 0.8), rim=mat('clay_rim', (0.30, 0.30, 0.31), 0.6),
             lamp=mat('clay_lampcap', (0.75, 0.77, 0.80), 0.2), glow=mat('clay_glow', (1.0, 0.95, 0.85), 1.0))
    os.makedirs('out/bp', exist_ok=True)
    root = empty(P + '-vehicle', (0, 0, 0), size=0.5, kind='ARROWS')
    body, X = build_body(M)
    # ---- pockets (light molding + intakes + vents), traced outlines
    tree = bvh_of([body]); specs = []
    def L(polys, k=0): return [np.array(p) for p in polys if np.mean(np.array(p)[:, k]) > 0]
    fp, rp, sp, tp = D['front_poly'], D['rear_poly'], D['side_poly'], D['top_poly']
    head = max(L(fp['HEADLAMP_F']), key=len)
    for nm, poly, view, dep, n, fm, wm in (
            ('headlamp', head, 'front', 0.030, 8, 3, 4),
            ('grille', max(fp['GRILLE_F'], key=len), 'front', 0.050, 8, 4, 4),
            ('side_intake', max(L(fp['SIDE_INTAKE_F']), key=len), 'front', 0.040, 6, 4, 4),
            ('hood_vent', max(L(tp['HOOD_VENT_T'], 1), key=len), 'top', 0.022, 4, 4, 4),
            ('fender_vent', np.vstack(sp['FENDER_VENT_S']), 'side', 0.018, 4, 4, 4),
            ('rear_diffuser', max([np.array(p) for p in rp['DIFFUSER_R'] if np.mean(np.array(p)[:, 0]) > 0.2], key=len), 'rear', 0.040, 4, 4, 4)):
        if nm not in os.environ.get('GRC_POCKETS', nm).split(','): continue
        if nm == 'fender_vent':                                         # two slots drawn: one convex vent opening
            poly = hull2d(poly)
        sym = nm != 'grille'
        if view == 'side': poly = np.c_[poly[:, 0], poly[:, 1]]
        for floor, front in pocket_cutter(nm, poly, view, dep, n, tree, mirror=sym):
            specs.append((floor, front, fm, wm))
    cutter = cutter_object(specs, M); n_pre, n_post = cut(body, cutter)
    if os.environ.get('GRC_PROBE'): print('PROBE', os.environ.get('GRC_POCKETS'), n_pre, n_post); return
    body.parent = root
    tree = bvh_of([body])
    wing, nw = build_wing(M); fin, fin_box = build_fin(M)
    parts = [wing, fin, build_mirror(P + '_Mirror_L', 1, M), build_mirror(P + '_Mirror_R', -1, M), build_floor(M)] + build_exhaust(M, tree)
    for nm, xc, sd, fr in (('FL', G.AXF, 1, True), ('FR', G.AXF, -1, True), ('RL', G.AXR, 1, False), ('RR', G.AXR, -1, False)):
        parts.append(build_liner(P + '_Liner_' + nm, xc, sd, fr, M))
    for o in parts: o.parent = root
    glow = glow_quads(M, head); glow.parent = root
    rig = dict(body=body, hub={}, steer={}, hub_rest={}, susp={})
    for nm, xc, yc in (('FL', G.AXF, G.TRACK_F / 2), ('FR', G.AXF, -G.TRACK_F / 2), ('RL', G.AXR, G.TRACK_R / 2), ('RR', G.AXR, -G.TRACK_R / 2)):
        loc = to_bl((xc, yc, G.HUB_Z)); hb = empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F': st = empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        sd = 1 if yc > 0 else -1; sp_ = empty(f'Susp_{nm}', loc, root, 0.15, 'PLAIN_AXES'); rig['susp'][nm] = sp_
        build_wheel(P + '_Wheel_' + nm, M, par, sd); build_susp(P + '_Susp_' + nm, M, sp_, sd, nm[0] == 'F')
    bpy.context.view_layer.update()
    lines = []; per = {}
    for ob in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
        n = tri_count(ob); per[ob.name] = n; lines.append(f'{ob.name:18s} {n:5d}')
    T, TO = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or '_Susp_' in ob.name or '_FX_' in ob.name: continue
        me = ob.data; mw = ob.matrix_world
        for t in me.loop_triangles: T.append([list(car(mw @ me.vertices[i].co)) for i in t.vertices]); TO.append(ob.name)
    np.save('out/bp/tris_carframe.npy', np.array(T, np.float32)); np.save('out/bp/tris_object.npy', np.array(TO))
    # ---- mono body: join everything except wheels / struts / FX; origin to the COM estimate
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    off = to_bl((COM_X, 0, COM_Z)); body.data.transform(Matrix.Translation(-off)); body.location = off; bpy.context.view_layer.update()
    rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
    mono = tri_count(body)
    wheels = sum(tri_count(o) for o in bpy.data.objects if '_Wheel_' in o.name); susp = sum(tri_count(o) for o in bpy.data.objects if '_Susp_' in o.name)
    fx = tri_count(glow); tot = mono + wheels + susp + fx
    loft = per.get(P + '_Body', 0)
    lines += ['', f'MONO {P}_Body {mono}  (loft + pockets {loft} [loft before pockets {n_pre}], wing {per[P + "_Wing"]}, fin {per[P + "_Fin"]}, mirrors {per[P + "_Mirror_L"] + per[P + "_Mirror_R"]}, '
              f'exhaust {sum(v for k, v in per.items() if "_Exhaust_" in k)}, liners {sum(v for k, v in per.items() if "_Liner_" in k)}, floor {per[P + "_Under"]})',
              f'wheels (4 x 10-sided) {wheels}', f'suspension (4 x strut + arm) {susp}', f'FX head lamp glow quads ({P}_FX_HeadGlow, hidden) {fx}',
              f'TOTAL rendered {tot}  (cap {CAP}: {"OK" if tot <= CAP else "OVER"})', f'stations {len(X)}, half-section points {G.NP}',
              f'shading QC (loft quads): {json.dumps(QC)}', f'pockets: {json.dumps(POCKETS)}']
    open('out/tri_count.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    rep = clearance(rig); json.dump(rep, open('out/bp/clearance.json', 'w'), indent=1)
    json.dump(dict(COM=[COM_X, COM_Z], bump_front=BUMP_F, bump_rear=BUMP_R, droop=DROOP, lock=LOCK, tyre_r=G.TIRE_R, tyre_w=G.TIRE_W,
                   track=G.TRACK_F, wheel_x=[G.AXF, G.AXR], liner_front=liner_spec(True), liner_rear=liner_spec(False), fin=fin_box,
                   wing_ring_points=nw), open('out/bp/rig_meta.json', 'w'), indent=1)
    set_pose(rig)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'gr_corolla_clay.blend'), compress=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'out', 'gr_corolla_clay.glb'), export_format='GLB', use_visible=True)
    if '--render' in sys.argv:
        import render_gr; importlib.reload(render_gr); render_gr.render_all(os.path.join(HERE, 'out'), rig, set_pose, dict(BUMP=BUMP_F, DROOP=DROOP, LOCK=LOCK, ROLL=ROLL))
if __name__ == '__main__': main()
