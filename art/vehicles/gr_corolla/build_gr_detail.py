"""Toyota GR Corolla (2022) DETAIL PASS: the signed-off lean clay (build_gr_corolla.py, same loft, stations, rig and
budget) + clean-up of the flagged clay issues + UVs, baked AO, painted 1024^2 body texture, 256^2 parts atlas
(wheel / tyre / headlamp art), lamp glow FX, PSX fake-shine materials, game-ready .glb.
  python3 bp/vectors.py                                         # blueprint vectors for the painter (once)
  blender -b --factory-startup -P build_gr_detail.py -- [--render]
  GRC_OUT=detail python3 bp/iou.py && python3 bp/deliver_detail.py
Geometry changes vs the clay (silhouette unchanged, IoU + 9-pose clearance re-run):
  * smooth shading: every loft face carries the UN-CUT loft's split normals (custom normals interpolated from the
    pre-boolean loft), so the pocket re-triangulation can no longer facet the nose; pocket walls / floors are flat.
  * grille / side intakes / diffuser / vents: pocket rims are the traced outlines Douglas-Peucker'd to their real
    corners (straight edges instead of Fourier wobble) and the floors are planar (plane fit to the rim, offset by
    the depth) -> clean dark openings; the mesh / slats / fins are painted (body texture).
  * roof wing: finer side profile (upturned tip kept), mirrors: 3-ring tapered shell (stalk -> head).
  * FX: head AND tail lamp glow quads (one hidden object, own 128x64 sprite).
Rig, COM, travel, lock: unchanged (build_gr_corolla.py constants)."""
import bpy, bmesh, sys, os, math, json, importlib, subprocess, shutil
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'parts')); sys.path.insert(0, HERE); os.chdir(HERE)
import numpy as np
import build_gr_corolla as B; importlib.reload(B)
import gr_geo as G, psx_mat as PM
for m in (G, PM): importlib.reload(m)
OUT = os.path.join(HERE, 'detail'); os.makedirs(os.path.join(OUT, 'bp'), exist_ok=True); os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True)
PY3 = shutil.which('python3') or '/usr/bin/python3'; TS = 1024
P, D, to_bl, car = B.P, B.D, B.to_bl, B.car
CAP = 2000
# material slot order of the mono body (clay materials; textured mapping in TEXM below)
SLOTS = ['clay', 'clay_glass', 'under', 'clay_lampcap', 'clay_trim', 'clay_pocket', 'clay_pocketfloor', 'clay_chrome']
def run(*a): subprocess.run([PY3, *a], check=True)
# ------------------------------------------------------------------ pockets: clean outlines, planar floors
def corners(poly, n):
    """traced outline -> its real corners: Douglas-Peucker with the smallest tolerance that leaves <= n vertices."""
    Pl = np.asarray(poly, float); eps = 0.002
    while True:
        S2 = B.simplify(Pl, eps)
        if len(S2) <= n: return S2
        eps *= 1.25
POCKETS = []
def pocket(name, outline2d, view, depth, n, tree, mode, mirror):
    """prism along the view axis.  mode 'fourier' (curved lamp outline) or 'corners' (DP).  Floor: planar for
    'corners' (plane through the rim hits, pushed back so every floor point is >= depth behind its rim hit), dish
    (rim hits stepped `depth` inward) for the lamp."""
    O = B._smooth_outline(outline2d, n) if mode == 'fourier' else corners(outline2d, n)
    if np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) < 0: O = O[::-1]
    def P3(a, b, t):
        if view in ('front', 'rear'): return np.array([t, a, b])
        if view == 'top': return np.array([a, b, t])
        return np.array([a, t, b])
    k_ax = {'front': 0, 'rear': 0, 'top': 2, 'side': 1}[view]
    ax = {'front': np.array([-1., 0, 0]), 'rear': np.array([1., 0, 0]), 'top': np.array([0, 0, -1.]), 'side': np.array([0, -1., 0])}[view]
    far = {'front': 3.0, 'rear': -3.0, 'top': 2.5, 'side': 1.5}[view]
    hits, nrm = [], []
    for a, b in O:
        h = tree.ray_cast(to_bl(P3(a, b, far)), to_bl(ax) - to_bl((0, 0, 0)), 6.0)
        if h[0] is None: raise RuntimeError(f'{name}: ray missed at {a:.3f},{b:.3f}')
        hits.append(car(h[0])); nn = car(h[1]); nrm.append(nn if nn @ ax < 0 else -nn)
    hits, nrm = np.array(hits), np.array(nrm)
    if mode == 'fourier':
        step = np.minimum(depth / np.maximum(-(nrm @ ax), 0.4), 1.6 * depth); floor = hits + step[:, None] * ax[None]
    else:
        A = np.c_[np.ones(len(O)), O]; t = hits[:, k_ax]; c = np.linalg.lstsq(A, t, rcond=None)[0]
        plane = A @ c; s = -ax[k_ax]                                       # +1: surface toward +axis coord (front/top/side)
        off = max(depth, float(np.max(s * (plane - t))) + depth * 0.6)       # every floor point >= depth*.6 behind its hit
        floor = np.array([P3(a, b, pl - s * off) for (a, b), pl in zip(O, plane)]); step = s * (hits[:, k_ax] - floor[:, k_ax])
    ext = hits[:, k_ax].max() + 0.12 if far > 0 else hits[:, k_ax].min() - 0.12
    front = np.array([P3(a, b, ext) for a, b in O])
    POCKETS.append(dict(name=name, view=view, mode=mode, rim_points=len(O), depth_m=depth, step_mm=[round(float(q) * 1000, 1) for q in step]))
    out = [(floor, front, name)]
    if mirror: out.append((floor * np.array([1, -1, 1]), front * np.array([1, -1, 1]), name))
    return out
def cutter_object(specs, M):
    """floors: lamp -> clay_lampcap, others -> clay_pocketfloor; walls -> clay_pocket.  Floors are one n-gon."""
    bm = bmesh.new(); I = {n: i for i, n in enumerate(SLOTS)}
    for floor, front, name in specs:
        n = len(front); fl = [bm.verts.new(to_bl(tuple(p))) for p in floor]; fr = [bm.verts.new(to_bl(tuple(p))) for p in front]; fs = []
        f = bm.faces.new(fl); f.material_index = I['clay_lampcap'] if name == 'headlamp' else I['clay_pocketfloor']; fs.append(f)
        f = bm.faces.new(fr); f.material_index = I['clay_pocket']; fs.append(f)
        for k in range(n):
            f = bm.faces.new((fl[k], fr[k], fr[(k + 1) % n], fl[(k + 1) % n])); f.material_index = I['clay_pocket']; fs.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    return B.obj_from_bm('POCKET_CUTTER', bm, [M[k] for k in SLOTS])
def diffuser_outline(rp):
    """rear diffuser opening = hull of the centre diffuser strip + the three exhaust openings (rear view, car y / z);
    the big angular corner vents (DIFFUSER_R side regions) are painted (vent mesh), not cut: cutting them gave the
    saw-tooth clay read.  Bottom edge kept 2 cm above the bumper's lower edge so the rim stays on the body."""
    cen = [np.array(p) for p in rp['DIFFUSER_R'] if abs(np.mean(np.array(p)[:, 0])) < 0.2]
    H = B.hull2d(np.vstack(cen + [np.array(p) for p in rp['EXHAUST_R']]))
    zmin = max(G.ZB(x) for x in np.linspace(-2.05, -1.80, 6)) + 0.02
    H[:, 1] = np.maximum(H[:, 1], zmin); return H
# ------------------------------------------------------------------ smooth shading: loft normals onto the cut body
def loft_normal_source(body):
    me = body.data.copy(); me.calc_loop_triangles(); cn = me.corner_normals
    V = [v.co.copy() for v in me.vertices]; T = [tuple(lt.vertices) for lt in me.loop_triangles]
    LN = [[Vector(cn[l].vector) for l in lt.loops] for lt in me.loop_triangles]
    tree = BVHTree.FromPolygons(V, T); bpy.data.meshes.remove(me); return tree, V, T, LN
def apply_loft_normals(body, src):
    tree, V, T, LN = src; me = body.data; out = []
    flat = {SLOTS.index(k) for k in ('clay_pocket', 'clay_pocketfloor', 'clay_lampcap')}
    nloft = 0
    for p in me.polygons:
        if p.material_index in flat:
            out += [p.normal.copy() for _ in p.loop_indices]; continue
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            hit, _, ti, dist = tree.find_nearest(co)
            if hit is None or dist > 0.01: out.append(p.normal.copy()); continue
            a, b, c = (V[i] for i in T[ti])
            v0, v1, v2 = b - a, c - a, hit - a; d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1); d20, d21 = v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01 or 1e-12; w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
            n = (LN[ti][0] * w0 + LN[ti][1] * w1 + LN[ti][2] * w2).normalized()
            if n.dot(p.normal) < 0.2: n = p.normal.copy()                     # guard: never flip a face's shading
            out.append(n); nloft += 1
    for p in me.polygons: p.use_smooth = True
    me.normals_split_custom_set([tuple(n) for n in out]); print('LOFT NORMALS on', nloft, 'loops')
# ------------------------------------------------------------------ parts with the flagged fixes
def build_wing(M):
    poly = max(D['side_poly']['WING_S'], key=len); S2 = B.simplify(poly, 0.0055)
    if np.sum(S2[:, 0] * np.roll(S2[:, 1], -1) - np.roll(S2[:, 0], -1) * S2[:, 1]) < 0: S2 = S2[::-1]
    wt = np.array(D['top_left']['WING_T']); wx = np.unique(np.round(wt[:, 0], 2)); wy = np.array([wt[np.abs(wt[:, 0] - q) < 0.006, 2].max() for q in wx])
    span = lambda x: float(np.interp(x, wx, wy))
    rL = [(x, span(x), z) for x, z in S2]; rR = [(x, -span(x), z) for x, z in S2]
    return B.tube(P + '_Wing', [rL, rR], [M['paint']], cap=(True, True), angle=35), len(S2)
def build_mirror(name, s, M):
    """3-ring shell, 20 tris: stalk on the door (small) -> head inner face -> head outer face (tapered, rounded
    corners chamfered).  Traced extents: front y .825-1.024, z .848-1.052; side x .516-.782; plan x .525-.705."""
    fm = [np.array(p) for p in D['front_poly']['MIRROR_F'] if np.mean(np.array(p)[:, 0]) > 0]; fy = np.vstack(fm)
    sm = np.vstack([np.array(p) for p in D['side_poly']['MIRROR_S']])
    y1 = float(fy[:, 0].max()); z0, z1 = float(fy[:, 1].min()), float(fy[:, 1].max()); xa, xb = float(sm[:, 0].min()), float(sm[:, 0].max())
    zm = 0.5 * (z0 + z1)
    stalk = [(xb, s * 0.80, z0 + 0.02), (xb, s * 0.80, z0 + 0.075), (xb - 0.09, s * 0.80, z0 + 0.075), (xb - 0.09, s * 0.80, z0 + 0.02)]
    inner = [(xb - 0.02, s * 0.87, z0 + 0.012), (xb - 0.03, s * 0.87, z1 - 0.010), (xa + 0.03, s * 0.87, z1 - 0.004), (xa + 0.01, s * 0.87, z0 + 0.02)]
    outer = [(xb - 0.07, s * y1, z0 + 0.03), (xb - 0.075, s * y1, z1 - 0.025), (xa, s * (y1 - 0.01), z1 - 0.03), (xa, s * (y1 - 0.01), z0 + 0.04)]
    return B.tube(name, [stalk, inner, outer], [M['trim']], angle=50)
def build_exhaust(M, tree):
    obs = B.build_exhaust(M, tree)
    for o in obs:
        o.data.materials.clear(); o.data.materials.append(M['chrome']); o.data.materials.append(M['under'])
    return obs
def glow_quads(M, head_poly):
    """FX: head lamp (warm white) + tail lamp (red) glow quads, 2 tris each, sprite UVs into the 128x64 glow atlas
    (left half white, right half red).  Separate object, hidden by default (Godot: toggle with the lights)."""
    body = bpy.data.objects[P + '_Body']; tree = B.bvh_of([body]); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    def quad(c, s, xdir, u0, aspect=0.5):
        h = tree.ray_cast(to_bl((3.0 * xdir, c[0], c[1])), to_bl((-xdir, 0, 0)) - to_bl((0, 0, 0)), 6.0)[0]
        x = car(h)[0] + 0.02 * xdir
        for sd in (1, -1):
            q = [(x, sd * (c[0] - s), c[1] - s * aspect), (x, sd * (c[0] + s), c[1] - s * aspect), (x, sd * (c[0] + s), c[1] + s * aspect), (x, sd * (c[0] - s), c[1] + s * aspect)]
            uv = [(u0, 0), (u0 + 0.5, 0), (u0 + 0.5, 1), (u0, 1)]
            vs = [bm.verts.new(to_bl(p)) for p in q]; f = bm.faces.new(vs)
            for lp, t in zip(f.loops, uv): lp[uvl].uv = t
            f.normal_update()
            if car(f.normal)[0] * xdir < 0: f.normal_flip()
    O = np.array(head_poly); quad(O.mean(0), 0.5 * np.ptp(O, 0).max(), 1, 0.0)
    tl = [np.array(p) for p in D['rear_poly']['TAIL_R']]; tl = max([p for p in tl if np.mean(p[:, 0]) > 0], key=len)
    quad(tl.mean(0), 0.5 * np.ptp(tl, 0).max(), -1, 0.5)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    o = B.obj_from_bm(P + '_FX_LampGlow', bm, [M['glow']]); o.hide_render = True; return o
# ------------------------------------------------------------------ UVs
ATLAS = dict(wheel=(0.0, 0.5, 0.5, 1.0), tread=(0.5, 0.0, 1.0, 1.0), head=(0.0, 0.0, 0.5, 0.25))   # u0, v0, u1, v1 (Blender UV, v up)
def wheel_uvs(ob, side):
    """outer cap -> painted disc (sidewall + 15-spoke rim, lettering mirrored per side so it reads on both sides),
    tread -> tread strip, inner cap -> dark corner of the disc tile."""
    me = ob.data; uvl = me.uv_layers.new(name='UVMap'); r = G.TIRE_R
    u0, v0, u1, v1 = ATLAS['wheel']; cu, cv, R = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.984
    t0, s0, t1, s1 = ATLAS['tread']
    for p in me.polygons:
        n = p.normal; c = p.center
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if abs(n.x) > 0.9 and n.x * side > 0:                            # outer face (axle = local X)
                uvl.data[li].uv = (cu + R * (co.y / r) * side, cv + R * co.z / r)
            elif abs(n.x) > 0.9:
                uvl.data[li].uv = (u0 + 0.01, v0 + 0.01)
            else:
                a = math.atan2(co.z, co.y) % (2 * math.pi); ac = math.atan2(c.z, c.y) % (2 * math.pi)
                if abs(a - ac) > math.pi: a += 2 * math.pi if a < ac else -2 * math.pi
                uvl.data[li].uv = (t0 + (t1 - t0) * (0.5 + 0.5 * co.x * side / (G.TIRE_W / 2)) * 0.98 + 0.01, s0 + (s1 - s0) * (a / (2 * math.pi)))
def lamp_uvs(body):
    """headlamp lens (pocket floor, clay_lampcap): planar along x into the atlas head tile; the right lamp uses |y| so
    it mirrors the same art (mirror-image lamps).  Writes detail/tex/lamp_uv.json for the lamp painter."""
    me = body.data; uvl = me.uv_layers.active; li_ = SLOTS.index('clay_lampcap')
    pts = np.array([car(body.matrix_world @ me.vertices[me.loops[l].vertex_index].co) for p in me.polygons if p.material_index == li_ for l in p.loop_indices])
    head = [np.array(q) for q in D['front_poly']['HEADLAMP_F'] if np.mean(np.array(q)[:, 0]) > 0]; head = max(head, key=len)
    yz = np.r_[np.c_[np.abs(pts[:, 1]), pts[:, 2]], np.c_[np.abs(head[:, 0]), head[:, 1]]]   # tile spans the whole lamp outline
    lo, hi = yz.min(0), yz.max(0); mid = (lo + hi) / 2
    u0, v0, u1, v1 = ATLAS['head']; tw, th = (u1 - u0), (v1 - v0)
    sc = min(tw / (hi - lo)[0], th / (hi - lo)[1]) * 0.94
    def uv(y, z): return (u0 + tw / 2 + (abs(y) - mid[0]) * sc * (-1), v0 + th / 2 + (z - mid[1]) * sc)   # outboard -> left of the tile
    for p in me.polygons:
        if p.material_index != li_: continue
        for l in p.loop_indices:
            c = car(body.matrix_world @ me.vertices[me.loops[l].vertex_index].co); uvl.data[l].uv = uv(c[1], c[2])
    px = [((uv(y, z)[0]) * 256, (1 - uv(y, z)[1]) * 256) for y, z in head[::4]]
    json.dump(dict(head=dict(tile=[0, 192, 128, 256], outline_px=px, mid=mid.tolist(), scale_px_per_m=sc * 256)), open(os.path.join(OUT, 'tex', 'lamp_uv.json'), 'w'))
def body_uvs(body):
    for o in bpy.context.selected_objects: o.select_set(False)
    body.select_set(True); bpy.context.view_layer.objects.active = body
    lamp = SLOTS.index('clay_lampcap'); me = body.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    lampv = {v for p in me.polygons if p.material_index == lamp for v in p.vertices}
    for p in me.polygons: p.select = p.material_index != lamp
    for v in me.vertices: v.select = v.index not in lampv
    for e in me.edges: e.select = not (e.vertices[0] in lampv or e.vertices[1] in lampv)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=0.006, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # pack into the lower 3/4 is not needed: lamp lens UVs live in the parts atlas (other image)
# ------------------------------------------------------------------ texture: AO bake + texel maps -> painter
def texture_body(body):
    for o in bpy.context.selected_objects: o.select_set(False)
    body.select_set(True); bpy.context.view_layer.objects.active = body
    lamp = SLOTS.index('clay_lampcap')
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
    if sc.world is None: sc.world = bpy.data.worlds.new('BakeWorld')
    sc.world.light_settings.distance = 0.30
    ao_img = bpy.data.images.new('GRC_AO', TS, TS, alpha=False); dummy = bpy.data.images.new('GRC_AO_dummy', 8, 8, alpha=False); tmp = []
    for i_, sl in enumerate(body.material_slots):
        nt_ = sl.material.node_tree; n_ = nt_.nodes.new('ShaderNodeTexImage'); n_.image = dummy if i_ == lamp else ao_img
        nt_.nodes.active = n_; tmp.append((nt_, n_))
    sc.render.bake.margin = 8; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='AO', use_clear=True)
    ao_png = os.path.join(OUT, 'tex', 'body_ao.png'); ao_img.filepath_raw = ao_png; ao_img.file_format = 'PNG'; ao_img.save()
    for nt_, n_ in tmp: nt_.nodes.remove(n_)
    bpy.data.images.remove(ao_img); bpy.data.images.remove(dummy)
    me = body.data; me.calc_loop_triangles(); uvd = me.uv_layers.active.data; mw = body.matrix_world
    pos = np.zeros((TS, TS, 3), np.float32); nrm = np.zeros((TS, TS, 3), np.float32); fnr = np.zeros((TS, TS, 3), np.float32); mask = np.full((TS, TS), -1, np.int16)
    cn = me.corner_normals; R3 = mw.to_3x3()
    for lt in me.loop_triangles:
        if lt.material_index == lamp: continue
        uv = np.array([uvd[l].uv[:] for l in lt.loops]) * TS - 0.5
        Pv = np.array([car(mw @ me.vertices[v].co) for v in lt.vertices]); Nv = np.array([car(R3 @ cn[l].vector) for l in lt.loops])
        fn = car(R3 @ lt.normal)
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, TS - 1), min(y1, TS - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        (ax, ay), (bx, by), (cx_, cy_) = uv
        den = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
        if abs(den) < 1e-12: continue
        l0 = ((by - cy_) * (gx - cx_) + (cx_ - bx) * (gy - cy_)) / den; l1 = ((cy_ - ay) * (gx - cx_) + (ax - cx_) * (gy - cy_)) / den; l2 = 1 - l0 - l1
        ins = (l0 >= -.02) & (l1 >= -.02) & (l2 >= -.02)
        if not ins.any(): continue
        Lb = np.stack([l0[ins], l1[ins], l2[ins]], 1); ry, rx = gy[ins], gx[ins]
        pos[ry, rx] = Lb @ Pv; nn = Lb @ Nv; nrm[ry, rx] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
        fnr[ry, rx] = fn; mask[ry, rx] = lt.material_index
    npz = os.path.join(OUT, 'tex', 'body_texels.npz'); np.savez_compressed(npz, pos=pos, nrm=nrm, fnr=fnr, mask=mask, slots=np.array(SLOTS))
    body_png = os.path.join(OUT, 'tex', 'gr_corolla_body.png'); run(os.path.join(HERE, 'tex', 'make_body_gr.py'), npz, body_png, ao_png)
    return body_png
# ------------------------------------------------------------------ main
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mk = B.mat
    M = dict(paint=mk('clay', (0.66, 0.66, 0.66), 0.55), glass=mk('clay_glass', (0.16, 0.17, 0.19), 0.3),
             under=mk('under', (0.02, 0.02, 0.02), 1.0), lamp=mk('clay_lampcap', (0.75, 0.77, 0.80), 0.2), trim=mk('clay_trim', (0.08, 0.08, 0.085), 0.8),
             pocket=mk('clay_pocket', (0.05, 0.05, 0.055), 0.9), pfloor=mk('clay_pocketfloor', (0.10, 0.10, 0.11), 0.9), chrome=mk('clay_chrome', (0.55, 0.56, 0.58), 0.3),
             wheel=mk('clay_wheel', (0.12, 0.12, 0.12), 0.8), rim=mk('clay_rim', (0.30, 0.30, 0.31), 0.6), glow=mk('clay_glow', (1.0, 0.95, 0.85), 1.0))
    for k, v in (('clay_pocket', 'pocket'), ('clay_pocketfloor', 'pfloor'), ('clay_chrome', 'chrome'), ('clay_lampcap', 'lamp')): M[k] = M[v]
    for k in ('clay', 'clay_glass', 'under', 'clay_trim'): M[k] = bpy.data.materials[k]
    root = B.empty(P + '-vehicle', (0, 0, 0), size=0.5, kind='ARROWS')
    body, X = B.build_body(M)
    me = body.data                                       # extend the loft's slots to the detail slot order
    for k in SLOTS[len(me.materials):]: me.materials.append(M[k])
    src = loft_normal_source(body)
    tree = B.bvh_of([body]); specs = []
    def L(polys, k=0): return [np.array(p) for p in polys if np.mean(np.array(p)[:, k]) > 0]
    fp, rp, sp, tp = D['front_poly'], D['rear_poly'], D['side_poly'], D['top_poly']
    head = max(L(fp['HEADLAMP_F']), key=len)
    for nm, poly, view, dep, n, mode in (
            ('headlamp', head, 'front', 0.030, 8, 'fourier'),
            ('grille', max(fp['GRILLE_F'], key=len), 'front', 0.050, 8, 'corners'),
            ('side_intake', max(L(fp['SIDE_INTAKE_F']), key=len), 'front', 0.040, 5, 'corners'),
            ('hood_vent', max(L(tp['HOOD_VENT_T'], 1), key=len), 'top', 0.020, 4, 'corners'),
            ('fender_vent', B.hull2d(np.vstack(sp['FENDER_VENT_S'])), 'side', 0.016, 4, 'corners'),
            ('rear_diffuser', diffuser_outline(rp), 'rear', 0.040, 6, 'corners')):
        specs += pocket(nm, poly, view, dep, n, tree, mode, mirror=(nm not in ('grille', 'rear_diffuser')))
    cutter = cutter_object(specs, M); n_pre, n_post = B.cut(body, cutter)
    apply_loft_normals(body, src)
    body.parent = root; tree = B.bvh_of([body])
    wing, nw = build_wing(M); fin, fin_box = B.build_fin(M)
    parts = [wing, fin, build_mirror(P + '_Mirror_L', 1, M), build_mirror(P + '_Mirror_R', -1, M), B.build_floor(M)] + build_exhaust(M, tree)
    for nm, xc, sd, fr in (('FL', G.AXF, 1, True), ('FR', G.AXF, -1, True), ('RL', G.AXR, 1, False), ('RR', G.AXR, -1, False)):
        parts.append(B.build_liner(P + '_Liner_' + nm, xc, sd, fr, M))
    for o in parts: o.parent = root
    glow = glow_quads(M, head); glow.parent = root
    rig = dict(body=body, hub={}, steer={}, hub_rest={}, susp={})
    for nm, xc, yc in (('FL', G.AXF, G.TRACK_F / 2), ('FR', G.AXF, -G.TRACK_F / 2), ('RL', G.AXR, G.TRACK_R / 2), ('RR', G.AXR, -G.TRACK_R / 2)):
        loc = to_bl((xc, yc, G.HUB_Z)); hb = B.empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F': st = B.empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        sd = 1 if yc > 0 else -1; sp_ = B.empty(f'Susp_{nm}', loc, root, 0.15, 'PLAIN_AXES'); rig['susp'][nm] = sp_
        w = B.build_wheel(P + '_Wheel_' + nm, M, par, sd); wheel_uvs(w, sd); B.build_susp(P + '_Susp_' + nm, M, sp_, sd, nm[0] == 'F')
    bpy.context.view_layer.update()
    lines = []; per = {}
    for ob in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
        n = B.tri_count(ob); per[ob.name] = n; lines.append(f'{ob.name:18s} {n:5d}')
    T, TO = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or '_Susp_' in ob.name or '_FX_' in ob.name: continue
        me = ob.data; mw = ob.matrix_world
        for t in me.loop_triangles: T.append([list(car(mw @ me.vertices[i].co)) for i in t.vertices]); TO.append(ob.name)
    np.save(os.path.join(OUT, 'bp', 'tris_carframe.npy'), np.array(T, np.float32)); np.save(os.path.join(OUT, 'bp', 'tris_object.npy'), np.array(TO))
    # ---- mono body: join (body keeps its custom loft normals), origin -> COM estimate
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    off = to_bl((B.COM_X, 0, B.COM_Z)); body.data.transform(Matrix.Translation(-off)); body.location = off; bpy.context.view_layer.update()
    rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
    mono = B.tri_count(body)
    wheels = sum(B.tri_count(o) for o in bpy.data.objects if '_Wheel_' in o.name); susp = sum(B.tri_count(o) for o in bpy.data.objects if '_Susp_' in o.name)
    fx = B.tri_count(glow); tot = mono + wheels + susp + fx
    lines += ['', f'MONO {P}_Body {mono}  (loft + pockets {per[P + "_Body"]} [loft before pockets {n_pre}], wing {per[P + "_Wing"]}, fin {per[P + "_Fin"]}, mirrors {per[P + "_Mirror_L"] + per[P + "_Mirror_R"]}, '
              f'exhaust {sum(v for k, v in per.items() if "_Exhaust_" in k)}, liners {sum(v for k, v in per.items() if "_Liner_" in k)}, floor {per[P + "_Under"]})',
              f'wheels (4 x 10-sided) {wheels}', f'suspension (4 x strut + arm) {susp}', f'FX head + tail lamp glow quads ({P}_FX_LampGlow, hidden by default) {fx}',
              f'TOTAL rendered {tot}  (cap {CAP}: {"OK" if tot <= CAP else "OVER"})', f'stations {len(X)}, half-section points {G.NP}',
              f'shading QC (loft quads): {json.dumps(B.QC)}', f'pockets: {json.dumps(POCKETS)}']
    open(os.path.join(OUT, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    rep = B.clearance(rig); json.dump(rep, open(os.path.join(OUT, 'bp', 'clearance.json'), 'w'), indent=1); B.set_pose(rig)
    json.dump(dict(COM=[B.COM_X, B.COM_Z], bump_front=B.BUMP_F, bump_rear=B.BUMP_R, droop=B.DROOP, lock=B.LOCK, tyre_r=G.TIRE_R, tyre_w=G.TIRE_W,
                   track=G.TRACK_F, wheel_x=[G.AXF, G.AXR], liner_front=B.liner_spec(True), liner_rear=B.liner_spec(False), fin=fin_box, wing_ring_points=nw),
              open(os.path.join(OUT, 'bp', 'rig_meta.json'), 'w'), indent=1)
    if '--geo-only' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'gr_corolla_geo.blend'), compress=True)
        import render_gr; importlib.reload(render_gr); render_gr.render_all(OUT, rig, B.set_pose, dict(BUMP=B.BUMP_F, DROOP=B.DROOP, LOCK=B.LOCK, ROLL=B.ROLL)); return
    # ---- UVs, AO, paint
    ui, ci, R3 = SLOTS.index('under'), SLOTS.index('clay'), body.matrix_world.to_3x3()
    ncap = 0
    for p in body.data.polygons:                      # loft end caps above the sill line carry the painted plate/bumper, not 'under'
        if p.material_index == ui and abs(car(R3 @ p.normal)[0]) > 0.8 and car(body.matrix_world @ p.center)[2] > 0.26: p.material_index = ci; ncap += 1
    print('end-cap faces -> body paint:', ncap)
    body_uvs(body); lamp_uvs(body)
    body_png = texture_body(body)
    parts_png = os.path.join(OUT, 'tex', 'gr_corolla_parts.png'); glow_png = os.path.join(OUT, 'tex', 'gr_corolla_glow.png')
    run(os.path.join(HERE, 'tex', 'make_parts_gr.py'), parts_png, os.path.join(OUT, 'tex', 'lamp_uv.json'), glow_png)
    env_png = os.path.join(OUT, 'tex', 'gr_corolla_env.png'); run(os.path.join(HERE, 'tex', 'make_env.py'), env_png)
    PM.set_env(bpy.data.images.load(env_png))
    bimg = bpy.data.images.load(body_png); pimg = bpy.data.images.load(parts_png); gimg = bpy.data.images.load(glow_png)
    paint = PM.fake_mat('GRC_Paint_Body', img=bimg, ambient=0.50, key=0.58, spec=0.42, shin=55, env=0.30, env_tint=(0.85, 0.90, 1.0), interp='Closest')
    glass = PM.fake_mat('GRC_Glass', rgb=(0.010, 0.014, 0.022), ambient=1.0, key=0.0, spec=0.6, shin=90, env=0.45, env_tint=(0.55, 0.70, 1.0))
    und = PM.fake_mat('GRC_Under', rgb=(0.006, 0.006, 0.007), ambient=1.0, key=0.0, spec=0.0, env=0.0)
    whl = PM.fake_mat('GRC_Wheel', img=pimg, ambient=0.55, key=0.55, spec=0.25, shin=30, env=0.15, interp='Closest')
    lampm = PM.fake_mat('GRC_Lamp', img=pimg, ambient=0.66, key=0.30, spec=0.30, shin=110, env=0.20, env_tint=(0.75, 0.82, 1.0), interp='Closest')
    glowm = bpy.data.materials.new('GRC_FX_Glow'); glowm.use_nodes = True
    gnt = glowm.node_tree; gpb = gnt.nodes['Principled BSDF']; gtx = gnt.nodes.new('ShaderNodeTexImage'); gtx.image = gimg
    gpb.inputs['Base Color'].default_value = (0, 0, 0, 1); gnt.links.new(gtx.outputs['Color'], gpb.inputs['Emission Color'])
    gpb.inputs['Emission Strength'].default_value = 1.5; gnt.links.new(gtx.outputs['Alpha'], gpb.inputs['Alpha'])
    glowm.surface_render_method = 'BLENDED'; glowm.use_backface_culling = True
    glow.hide_render = True
    TEXM = {'clay': paint, 'clay_glass': glass, 'under': und, 'clay_trim': paint, 'clay_pocket': paint, 'clay_pocketfloor': paint, 'clay_chrome': paint,
            'clay_lampcap': lampm, 'clay_wheel': whl, 'clay_rim': whl, 'clay_glow': glowm}
    CLAY = {o.name: [sl.material for sl in o.material_slots] for o in bpy.data.objects if o.type == 'MESH'}
    def apply(textured):
        for o in bpy.data.objects:
            if o.type != 'MESH': continue
            for sl, m0 in zip(o.material_slots, CLAY[o.name]): sl.material = TEXM[m0.name] if textured else m0
    apply(True)
    # merge duplicate material slots per object (glTF primitives): wheel / rim -> one slot
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        names = [sl.material.name for sl in o.material_slots]; uniq = list(dict.fromkeys(names))
        if len(uniq) == len(names): continue
        remap = [uniq.index(n) for n in names]
        idx = [remap[p.material_index] for p in o.data.polygons]          # materials.clear() resets the face indices
        mats = [bpy.data.materials[n] for n in uniq]; o.data.materials.clear()
        for m in mats: o.data.materials.append(m)
        for p, i in zip(o.data.polygons, idx): p.material_index = i
    bpy.context.preferences.filepaths.save_version = 0
    for im in (bimg, pimg, gimg): im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'gr_corolla_detail.blend'), compress=True)
    PM.use_principled(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'gr_corolla_detail.glb'), export_format='GLB', use_visible=True)
    PM.use_principled(False)
    if '--render' in sys.argv:
        import render_gr, render_detail; importlib.reload(render_detail)
        render_detail.render_textured(OUT, rig, B.set_pose)
if __name__ == '__main__': main()
