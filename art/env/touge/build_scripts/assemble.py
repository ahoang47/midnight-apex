"""Assemble the authored Touge env pieces (Godot space) -> build_data.npz + build_meta.json for blender_build.py"""
import numpy as np, pickle, json, trimesh
from terrain import *
OUT = '/workspace/touge_env_work/'
z = np.load(OUT + 'tri_kept.npz'); TV, TF, Hs = z['TV'], z['TF'], z['Hs']
ownc = pickle.load(open(OUT + 'ownc.pkl', 'rb'))
V3 = np.c_[TV[:, 0], Hs, TV[:, 1]]
# ---------- sections ----------
TURNS = H['turns']
def turn_of(s):
    for t in TURNS:
        if s < t['s1'] or t['id'] == 10: return t['id']
    return 10
SEC = {t['id']: 'touge_t%02d' % t['id'] for t in TURNS}
SEC_RANGE = {t['id']: [(-96.0 if t['id'] == 1 else t['s0']), (1104.0 if t['id'] == 10 else t['s1'])] for t in TURNS}
GAL = [('touge_gallery_a', 904.0, 975.0), ('touge_gallery_b', 975.0, 997.0), ('touge_gallery_c', 1068.0, 1104.0)]
DECKS = [('touge_gallery_c', 319.0, 399.0), ('touge_gallery_b', 439.0, 467.0), ('touge_gallery_a', 467.0, 546.0)]
# per-vertex legs (for per-corner UVs relative to the triangle's leg)
VL = [legs_at(p) for p in TV]
def rel(vi, s_ref):
    best = None
    for o in VL[vi]:
        if abs(o['s'] - s_ref) < 25 and (best is None or abs(o['s'] - s_ref) < abs(best['s'] - s_ref)): best = o
    return best
objs = {}   # name -> {'P':[], 'UV':[], 'M':[], 'COL':[]}
def obj(n):
    if n not in objs: objs[n] = {'P': [], 'UV': [], 'M': [], 'COL': []}
    return objs[n]
def add_tri(n, ps, uvs, mat, cols=None, want=None):
    ps = [np.asarray(q, float) for q in ps]
    if want is not None:
        nn = np.cross(ps[1] - ps[0], ps[2] - ps[0])
        if np.dot(nn, want) < 0: ps = [ps[0], ps[2], ps[1]]; uvs = [uvs[0], uvs[2], uvs[1]]; cols = None if cols is None else [cols[0], cols[2], cols[1]]
    o = obj(n); o['P'].extend(ps); o['UV'].extend(uvs); o['M'].append(mat); o['COL'].extend(cols if cols is not None else [(1, 1, 1, 1)] * 3)
FLIPS = [r[0] for r in DROP_RUNS[1:]]
stats = {}
for k, f in enumerate(TF):
    oc = ownc[k]; s0 = oc['s']; side = oc['side']
    P = V3[f]
    if oc['zone'] == 'ring':   # backdrop ring: planar UVs (U = x / 8 m, V = z m), one material
        add_tri('touge_backdrop', [P[0], P[2], P[1]], [(P[0][0] / 8.0, P[0][2]), (P[2][0] / 8.0, P[2][2]), (P[1][0] / 8.0, P[1][2])], 'touge_hill')
        stats['touge_backdrop'] = stats.get('touge_backdrop', 0) + 1; continue
    nrm = np.cross(P[1] - P[0], P[2] - P[0]); nl = np.linalg.norm(nrm)
    ny = abs(nrm[1]) / nl if nl > 1e-9 else 1.0
    # target object
    target = SEC[turn_of(s0)]
    lot = (turn_of(s0) == 5 and side < 0 and LOT0 - 2 <= s0 <= LOT1 + 2 and oc['e'] < 30.0 and (oc['zone'] in ('lotfloor', 'in')))
    if lot: target = 'touge_lot'
    # gallery wall: steep face on the lower road's wall line
    cen = P.mean(0)[[0, 2]]
    gwall = None
    if ny < 0.5:
        for o in legs_at(cen):
            for gn, ga, gb in GAL:
                if ga <= o['s'] <= gb and (3.0 < o['e'] < 4.2 or 8.5 < o['e'] < 9.6) and o['zone'] != 'road':
                    gwall = gn; break
            if gwall: break
    zone = oc['zone']; e = oc['e']
    if gwall:
        target = gwall; mat = 'touge_concrete'
    elif zone == 'lotfloor': mat = 'asphalt'
    elif zone == 'road' or e < 0.08 or (zone == 'in' and e < 0.7): mat = 'touge_gravel'
    elif ny < 0.45: mat = 'touge_cutrock'
    elif (zone == 'in' and drop_s(s0) == side) or (min(abs(s0 - f_) for f_ in FLIPS) < 3.0 and ny < 0.75 and e < 9.5): mat = 'touge_concrete'   # wing wall at a drop flip: the cut runs 2 m past it (a lattice module there may sit either side), faced as a concrete retaining-wall end
    elif zone == 'in' and e < 8.7: mat = 'touge_cutface'
    else: mat = 'touge_hill'
    uvs = []
    for vi in f:
        r = rel(vi, s0) or oc
        sv = r['s']; ev = max(r['e'], 0.0) if r['zone'] != 'road' else r['e']
        y = V3[vi][1]
        if mat == 'touge_cutface': u = (ev - 0.7) / 8.0
        elif mat in ('touge_cutrock', 'touge_concrete'): u = (y - r['yroad']) / 8.0
        elif mat == 'asphalt': u = (abs(r['d']) - W) / 8.0
        else: u = ev / 8.0
        uvs.append((u, sv))
    # keep each triangle's V span sane (a corner that re-projected far along s takes the centroid's s)
    vs = [q[1] for q in uvs]
    if max(vs) - min(vs) > 12.0: uvs = [(q[0], s0) for q in uvs]
    add_tri(target, [P[0], P[2], P[1]], [uvs[0], uvs[2], uvs[1]], mat)   # triangle() is CCW in (x, z) = facing -Y: flip all
    stats[target] = stats.get(target, 0) + 1
print('terrain tris per object', stats)
# ---------- decks (soffit + fascia + lip where the road edge has no ground) ----------
gaps = json.load(open(OUT + 'gaps.json'))
def gap_near(s, sd, m=4.0): return any(g[1] == sd and abs(g[0] - s) <= m for g in gaps)
DEPTH = 1.2; LIP = 1.6   # lip carries the rail (W+0.45), delineators (W+0.5 / 0.62) and lamp posts (W+1.2)
for gn, a, b in DECKS:
    rows = [i for i in range(NS) if a <= S[i] <= b]
    def yd(i, dd): return C[i] + N3[i] * dd
    for i0, i1 in zip(rows[:-1], rows[1:]):
        s = S[i0]
        dl = W + (LIP if gap_near(s, -1) else 0.0); dr = W + (LIP if gap_near(s, 1) else 0.0)
        A0 = yd(i0, -dl) - [0, DEPTH, 0]; B0 = yd(i0, dr) - [0, DEPTH, 0]; A1 = yd(i1, -dl) - [0, DEPTH, 0]; B1 = yd(i1, dr) - [0, DEPTH, 0]
        uvq = lambda dd, ss: ((dd + 5) / 8.0, ss)
        dn = np.array([0, -1.0, 0])
        add_tri(gn, [A0, A1, B0], [uvq(-dl, S[i0]), uvq(-dl, S[i1]), uvq(dr, S[i0])], 'touge_concrete', want=dn)
        add_tri(gn, [B0, A1, B1], [uvq(dr, S[i0]), uvq(-dl, S[i1]), uvq(dr, S[i1])], 'touge_concrete', want=dn)
        for sd, dd in ((-1, dl), (1, dr)):
            if not gap_near(s, sd): continue
            T0 = yd(i0, sd * dd) - [0, 0.01, 0]; T1 = yd(i1, sd * dd) - [0, 0.01, 0]
            E0 = yd(i0, sd * W) - [0, 0.01, 0]; E1 = yd(i1, sd * W) - [0, 0.01, 0]
            Bt0 = T0 - [0, DEPTH, 0]; Bt1 = T1 - [0, DEPTH, 0]
            # fascia (outer face) U up the face
            ow = N3[i0] * sd; ow[1] = 0
            add_tri(gn, [T0, Bt0, T1], [(DEPTH / 8, S[i0]), (0, S[i0]), (DEPTH / 8, S[i1])], 'touge_concrete', want=ow)
            add_tri(gn, [T1, Bt0, Bt1], [(DEPTH / 8, S[i1]), (0, S[i0]), (0, S[i1])], 'touge_concrete', want=ow)
            # lip (top strip beside the road, carries the rail)
            up = np.array([0, 1.0, 0])
            add_tri(gn, [E0, T0, E1], [(0, S[i0]), (LIP / 8, S[i0]), (0, S[i1])], 'touge_concrete', want=up)
            add_tri(gn, [E1, T0, T1], [(0, S[i1]), (LIP / 8, S[i0]), (LIP / 8, S[i1])], 'touge_concrete', want=up)
# ---------- kit pieces ----------
def box(x0, x1, y0, y1, z0, z1, col, bottom=False):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    if not bottom: q = [qq for qq in q if qq != (0, 1, 5, 4)]
    tris = []
    ctr = v.mean(0)
    for a_, b_, c_, d_ in q:
        for t in ((v[a_], v[b_], v[c_]), (v[a_], v[c_], v[d_])):
            nn = np.cross(t[1] - t[0], t[2] - t[0])
            if np.dot(nn, np.mean(t, 0) - ctr) < 0: t = (t[0], t[2], t[1])
            tris.append(t)
    return [(t, col) for t in tris]
POST = (0.16, 0.16, 0.18, 1.0); HEAD = (0.941, 0.784, 0.580, 1.0); ARM = (0.20, 0.20, 0.22, 1.0)
lamp = []
lamp += box(-0.09, 0.09, 0.0, 6.5, -0.09, 0.09, POST)               # post
lamp += box(-0.16, 0.16, 0.0, 0.5, -0.16, 0.16, POST)               # base collar
lamp += box(-1.45, 0.0, 6.38, 6.5, -0.05, 0.05, ARM)                # arm
lamp += box(-1.75, -1.05, 6.24, 6.42, -0.16, 0.16, ARM)             # head housing
lamp += [t for t in box(-1.70, -1.10, 6.22, 6.24, -0.12, 0.12, HEAD, bottom=True)]   # lens (full-bright, luma >= 0.5)
LAMP_T = [t for t, c in lamp]; LAMP_C = [c for t, c in lamp]
# gallery bay: pilaster (unit height) + cap block; local +X away from the road (into the wall), protrudes toward the road (-X)
bay = box(-0.45, 0.05, 0.0, 1.0, -0.35, 0.35, None)
BAY_T = [t for t, c in bay]
# rail: the approved touge_guardrail.glb module (4 m, +X away from the road)
gr = trimesh.load('/workspace/touge_env_godot/assets/env/touge_guardrail.glb')
RAIL = []
for nm in gr.graph.nodes_geometry:
    tf, gk = gr.graph[nm]; g = gr.geometry[gk]
    vv = trimesh.transform_points(g.vertices, tf); uv = g.visual.uv.copy(); uv[:, 1] = 1 - uv[:, 1]
    for fa in g.faces: RAIL.append((vv[fa], uv[fa], g.visual.material.name))
def rotYXZ(r):
    x, y, zz = r
    Rx = np.array([[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]])
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    Rz = np.array([[np.cos(zz), -np.sin(zz), 0], [np.sin(zz), np.cos(zz), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz
REF = d['reference']
markers = {}   # object -> list of (name, pos)
nl = 0
import matplotlib.tri as _mtri
_tri = _mtri.Triangulation(TV[:, 0], TV[:, 1], TF); _fnd = _tri.get_trifinder()
def ground_at(p):
    k = _fnd(p[0], p[1])
    if k < 0: return None
    a_, b_, c_ = TV[TF[k]]; M = np.array([[b_[0] - a_[0], c_[0] - a_[0]], [b_[1] - a_[1], c_[1] - a_[1]]]); u, v = np.linalg.solve(M, p - a_)
    f = TF[k]; return Hs[f[0]] * (1 - u - v) + Hs[f[1]] * u + Hs[f[2]] * v
def in_deck(s): return any(a_ <= s <= b_ for _, a_, b_ in DECKS)
lamp_fix = []
for lp in REF['lamps']:
    if lp['kind'] != 'road': continue
    Rm = rotYXZ(lp['rotation_rad']); p0 = np.array(lp['pos'])
    tgt = SEC[turn_of(lp['s'])]
    sd = 1.0 if lp['d'] > 0 else -1.0
    g = ground_at(p0[[0, 2]])
    if in_deck(lp['s']) and gap_near(lp['s'], sd): g = p0[1] - 0.01          # stands on the deck lip
    gl = 0.0 if g is None else float(g - p0[1])                             # ground in lamp-local y (lamps are only yawed)
    gl = min(gl, 0.0); lamp_fix.append((lp['s'], round(gl, 2)))
    body = box(-0.09, 0.09, gl - 0.25, 6.5, -0.09, 0.09, POST) + box(-0.16, 0.16, gl - 0.25, gl + 0.5, -0.16, 0.16, POST) + lamp[20:]
    for t, c in body:
        add_tri(tgt, [Rm @ q + p0 for q in t], [(0, 0)] * 3, 'lamp_post', [c] * 3)
    markers.setdefault(tgt, []).append(('lamp_head_%03d' % nl, (Rm @ np.array(lp['arm_local']) + p0).tolist(), lp['s'])); nl += 1
nr = 0
for rl in REF['rails']:
    if not rl['visible']: continue
    Rm = rotYXZ(rl['rotation_rad']); p0 = np.array(rl['pos'])
    tgt = SEC[turn_of(rl['s'])]
    for vv, uv, mn in RAIL:
        add_tri(tgt, [Rm @ q + p0 for q in vv], [tuple(x) for x in uv], mn)
    nr += 1
print('lamps', nl, 'rails', nr, 'lamp ground offsets', lamp_fix)
# gallery bays along each wall line, 8 m apart
for gn, ga, gb in GAL:
    sv = ga + 4.0
    while sv < gb:
        i = int(np.argmin(abs(S - sv)))
        best = None
        for side, (eb, et) in [(sd, pr) for sd in (-1.0, 1.0) for pr in ((3.45, 3.6), (8.75, 8.9))]:
            pb = C2[i] + NH[i] * side * (W + eb); pt_ = C2[i] + NH[i] * side * (W + et)
            hb, ob = combine(pb, legs_at(pb)); ht, ot = combine(pt_, legs_at(pt_))
            if ht - hb > 6.0 and ob is not None and abs(ob['s'] - S[i]) < 5: best = (side, hb, ht, pb)
        if best:
            side, hb, ht, pb = best
            yaw = np.arctan2(NH[i][0] * side, NH[i][1] * side)   # local +X -> away from the road
            # local +X = side * NH ; rotation about Y mapping (1,0,0) -> (nx, 0, nz): angle = atan2(-nz, nx)
            nx, nz = NH[i][0] * side, NH[i][1] * side
            ang = np.arctan2(-nz, nx)
            Rm = rotYXZ([0, ang, 0]); hgt = (ht - hb) - 0.05
            p0 = np.array([pb[0], hb - 0.3, pb[1]])
            for t in BAY_T:
                add_tri(gn, [Rm @ (np.array(q) * [1, hgt + 0.3, 1]) + p0 for q in t], [((q[1] * (hgt + 0.3)) / 8.0, q[2] + q[0]) for q in t], 'touge_concrete')
        sv += 8.0
# ---------- write ----------
data = {}; meta = {'objects': {}, 'markers': markers, 'sections': {SEC[k]: v for k, v in SEC_RANGE.items()},
                    'galleries': GAL, 'decks': DECKS, 'lot': [LOT0, LOT1]}
for n, o in objs.items():
    data[n + '__P'] = np.array(o['P'], np.float32).reshape(-1, 3)
    data[n + '__UV'] = np.array(o['UV'], np.float32).reshape(-1, 2)
    data[n + '__C'] = np.array(o['COL'], np.float32).reshape(-1, 4)
    mats = sorted(set(o['M'])); data[n + '__M'] = np.array([mats.index(m) for m in o['M']], np.int32)
    meta['objects'][n] = {'mats': mats, 'tris': len(o['M'])}
# kit pieces as their own objects
data['lamp_post__P'] = np.array(LAMP_T, np.float32).reshape(-1, 3); data['lamp_post__UV'] = np.zeros((len(LAMP_T) * 3, 2), np.float32)
data['lamp_post__C'] = np.repeat(np.array(LAMP_C, np.float32), 3, axis=0); data['lamp_post__M'] = np.zeros(len(LAMP_T), np.int32)
meta['kit'] = {'lamp_post': {'mats': ['lamp_post'], 'tris': len(LAMP_T)}}
data['rail_seg__P'] = np.array([v for v, u, m in RAIL], np.float32).reshape(-1, 3); data['rail_seg__UV'] = np.array([u for v, u, m in RAIL], np.float32).reshape(-1, 2)
rm = sorted(set(m for v, u, m in RAIL)); data['rail_seg__M'] = np.array([rm.index(m) for v, u, m in RAIL], np.int32); data['rail_seg__C'] = np.ones((len(RAIL) * 3, 4), np.float32)
meta['kit']['rail_seg'] = {'mats': rm, 'tris': len(RAIL)}
data['gallery_bay__P'] = np.array(BAY_T, np.float32).reshape(-1, 3); data['gallery_bay__UV'] = np.array([((q[1]) / 8.0, q[2] + q[0]) for t in BAY_T for q in t], np.float32)
data['gallery_bay__M'] = np.zeros(len(BAY_T), np.int32); data['gallery_bay__C'] = np.ones((len(BAY_T) * 3, 4), np.float32)
meta['kit']['gallery_bay'] = {'mats': ['touge_concrete'], 'tris': len(BAY_T)}
# chevron: flat quad 1.0 long (+Z = pointing) x 0.9 wide, on the ground plane
cq = [np.array([-0.45, 0, -0.5]), np.array([0.45, 0, -0.5]), np.array([0.45, 0, 0.5]), np.array([-0.45, 0, 0.5])]
cu = [(0, 1), (1, 1), (1, 0), (0, 0)]
data['line_chevron__P'] = np.array([cq[0], cq[2], cq[1], cq[0], cq[3], cq[2]], np.float32)
data['line_chevron__UV'] = np.array([cu[0], cu[2], cu[1], cu[0], cu[3], cu[2]], np.float32)
data['line_chevron__M'] = np.zeros(2, np.int32); data['line_chevron__C'] = np.ones((6, 4), np.float32)
meta['kit']['line_chevron'] = {'mats': ['line_chevron'], 'tris': 2}
np.savez(OUT + 'build_data.npz', **data)
json.dump(meta, open(OUT + 'build_meta.json', 'w'), indent=1, default=float)
for n, m in meta['objects'].items(): print(n, m)
