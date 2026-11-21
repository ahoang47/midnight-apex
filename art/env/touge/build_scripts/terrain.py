"""Touge course terrain builder (Arthur). Builds one continuous heightfield-style terrain around Gordon's exported road,
split into sections / lot / gallery pieces. Output: terrain_out.npz + terrain_meta.json, consumed by blender_build.py."""
import json, numpy as np, triangle as tr
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Polygon, MultiLineString, Point
from shapely.ops import unary_union
from roadload import load

d, S, L, R, LOT = load()
H = d['header']; W = 3.75
smp = {round(x['s'], 3): x for x in d['samples']}
C = (L + R) / 2.0
N3 = (R - L) / (2 * W)                      # 3D lateral vector per metre (+d = right)
NH = N3[:, [0, 2]] / np.linalg.norm(N3[:, [0, 2]], axis=1, keepdims=True)
C2 = C[:, [0, 2]]
NS = len(S)
TO = H['turnout']; LOT0, LOT1 = TO['s0'], TO['s1']
# lot inside width (left, d<0) from the samples (1 m)
def left_w(s):
    if s < LOT0 - 1 or s > LOT1 + 1: return W
    a = int(np.floor(s)); b = a + 1
    la = smp.get(float(a), {'left_width': W})['left_width']; lb = smp.get(float(b), {'left_width': W})['left_width']
    return la + (lb - la) * (s - a)
# drop side from the rail reference (4 m)
rails = d['reference']['rails']
rail_s = np.array([r['s'] for r in rails]); rail_side = np.array([1.0 if r['side'] == 'R' else -1.0 for r in rails])
def drop_at(s): return rail_side[np.argmin(np.abs(rail_s - (s - 2.0)) + (rail_s > s + 0.01) * 0.0)]
DROP = np.array([rail_side[np.clip(np.searchsorted(rail_s, s, side='right') - 1, 0, len(rail_s) - 1)] for s in S])
# exact drop runs from course.gd (course.drop_runs printed from Gordon's worktree build; the rail reference is 1-3 m late)
DROP_RUNS = [(-1e9, -1.0), (63.0, 1.0), (253.0, -1.0), (463.0, 1.0), (647.0, -1.0), (729.0, 1.0), (799.0, -1.0), (975.0, 1.0)]
def drop_s(s):
    side = DROP_RUNS[0][1]
    for a, sd in DROP_RUNS:
        if s >= a: side = sd
    return side
LAT_HALF = 2.0   # lattice modules are 4 m, put on a side by their centre's drop side: the cut (P_IN) runs 2 m past each flip
def is_out(s, side):
    return drop_s(s) == side and drop_s(s - LAT_HALF) == side and drop_s(s + LAT_HALF) == side

T = {'reach': 100.0, 'out_slope': 0.888, 'in_slope': 0.35}
P_OUT = np.array([[0, -0.01], [0.08, 0.0], [0.55, 0.0], [9.0, -7.5], [100.0, -7.5 - 0.888 * 91]])
P_IN = np.array([[0, -0.01], [0.08, 0.02], [0.7, 0.02], [8.7, 7.6], [18.0, 10.0], [100.0, 10.0 + 0.35 * 82]])
def prof(p, e): return np.interp(e, p[:, 0], p[:, 1])

kd = cKDTree(C2)
G_PROT = 3.5     # gallery wall line: no higher terrain within this of a road edge
G_IN = 8.8       # inside (lattice) side under / beside an overhead road: the whole lattice module (W+0.7 .. W+8.7, top 7.6) stands on its own
                 # cut, the wall starts behind its top cap (Austin pt364u: no lattice buried in a gallery wall)
def gthr(o, legs):
    if o['zone'] == 'in' and o.get('along', 0.0) < 1e-6 and any(q is not o and q['yroad'] > o['yroad'] + 10.0 and q['e'] < 12.0 for q in legs): return G_IN
    return G_PROT
TAU = 3.0

def frame(i, t):
    """interpolated frame between rows i, i+1 at t"""
    j = min(i + 1, NS - 1)
    c = C[i] * (1 - t) + C[j] * t; n3 = N3[i] * (1 - t) + N3[j] * t
    nh = NH[i] * (1 - t) + NH[j] * t; nh /= np.linalg.norm(nh)
    return c, n3, nh

def legs_at(p, rad=130.0):
    idx = kd.query_ball_point(p, rad)
    if not idx: return []
    idx = np.array(sorted(idx))
    dist = np.linalg.norm(C2[idx] - p, axis=1)
    mins = []
    for k in range(len(idx)):
        i = idx[k]
        lft = dist[k - 1] if k > 0 and idx[k - 1] == i - 1 else np.inf
        rgt = dist[k + 1] if k + 1 < len(idx) and idx[k + 1] == i + 1 else np.inf
        if dist[k] <= lft and dist[k] <= rgt: mins.append((dist[k], i))
    mins.sort()
    out = []
    for dd, i in mins:
        # refine: bilinear inverse on the row quads around i (rows are exact road rows; between rows c and n are linear)
        best = None
        for a in (i - 2, i - 1, i, i + 1):
            if a < 0 or a + 1 >= NS: continue
            c0, c1 = C2[a], C2[a + 1]; n0, n1 = NH[a], NH[a + 1]
            q0 = p - c0; dc = c1 - c0; dn = n1 - n0
            # f(t) = cross(q0 - dc t, n0 + dn t) = 0
            A2 = -(dc[0] * dn[1] - dc[1] * dn[0])
            A1 = (q0[0] * dn[1] - q0[1] * dn[0]) - (dc[0] * n0[1] - dc[1] * n0[0])
            A0 = q0[0] * n0[1] - q0[1] * n0[0]
            ts = np.roots([A2, A1, A0]) if abs(A2) > 1e-12 else ([-A0 / A1] if abs(A1) > 1e-12 else [])
            for t in ts:
                if abs(np.imag(t)) > 1e-9: continue
                t = float(np.real(t))
                lo = -1e-6 if a > 0 else -1e9; hi = 1 + 1e-6 if a + 1 < NS - 1 else 1e9
                if t < lo or t > hi: continue
                cc = c0 + dc * t; nn = n0 + dn * t
                dd_ = float(np.dot(p - cc, nn) / np.dot(nn, nn))
                if best is None or abs(dd_) < abs(best[0]): best = (dd_, a, t)
        if best is None: continue
        dl, a, t = best
        along = 0.0
        if t < 0: along = -t * 2.0; t_c = 0.0
        elif t > 1: along = (t - 1) * 2.0; t_c = 1.0
        else: t_c = t
        if along > 0: dl = float(np.dot(p - (C2[a] + (C2[a+1]-C2[a]) * t_c), NH[a] * (1 - t_c) + NH[a+1] * t_c))
        t = t_c
        s = S[a] + 2.0 * t
        if any(abs(s - o['s']) < 14.0 for o in out): continue
        c = C[a] * (1 - t) + C[a + 1] * t; n3 = N3[a] * (1 - t) + N3[a + 1] * t
        nh = NH[a] * (1 - t) + NH[a + 1] * t
        dq = abs(dl)
        side = 1.0 if dl >= 0 else -1.0
        ws = left_w(s) if side < 0 else W
        e = abs(dl) - ws
        if along > 0.0: e = max(e, along)
        out.append({'along': along, 's': s, 'd': dl, 'e': e, 'side': side, 'ws': ws, 'c': c, 'n3': n3, 'nh': nh, 'foot': c[[0, 2]], 'dist': dq})
    for o in out:
        c, n3 = o['c'], o['n3']; dl = o['d']
        if o['e'] < -0.002:
            if abs(dl) <= W: o['h'] = c[1] + n3[1] * dl - 0.15; o['zone'] = 'road'
            else: o['h'] = c[1] + n3[1] * dl - 0.06; o['zone'] = 'lotfloor'
        else:
            yedge = c[1] + n3[1] * o['side'] * min(o['ws'], W)   # lot floor is graded, not banked
            out_side = is_out(o['s'], o['side'])
            o['out'] = out_side
            o['h'] = yedge + prof(P_OUT if out_side else P_IN, max(o['e'], 0.0)); o['yedge'] = yedge
            o['zone'] = 'out' if out_side else 'in'
        o['yroad'] = c[1]
    return out

def combine0(p, legs):
    if not legs: return None, None
    # within G_PROT of any road edge (or on it): the LOWEST of those legs owns the point (a road's verge / gallery floor is
    # never covered by another leg's higher terrain; an overhead road there is a deck)
    prot = [o for o in legs if o['e'] < gthr(o, legs)]
    if prot:
        o = min(prot, key=lambda o: o['h']); return o['h'], o
    cand = list(legs)
    # rule 1: terrain of leg i may not reach across a road k that it stands above (k between p and i)
    keep = []
    for i in cand:
        b = i['foot'] - p; lb = np.linalg.norm(b) + 1e-9; bad = False
        for k in cand:
            if k is i: continue
            a = k['foot'] - p; la = np.linalg.norm(a) + 1e-9
            if la < lb and np.dot(a, b) / (la * lb) > 0.5 and i['h'] > k['yroad'] - 8.0: bad = True; break
        if not bad: keep.append(i)
    cand = keep or cand
    emin = min(o['e'] for o in cand)
    o0 = min(cand, key=lambda o: o['e'])
    ws = []; hs = []
    for o in cand:
        dh = abs(o['h'] - o0['h'])
        if dh > 8.0: continue
        w = np.exp(-(o['e'] - emin) / TAU) * np.exp(-dh / 4.0)
        ws.append(w); hs.append(o['h'])
    hv = float(np.dot(ws, hs) / np.sum(ws))
    return hv, o0

# ---- turn-4 underpass canyon (Austin pt364u): the run-out's cut under turn 4 is a stepped cut (7 m faces, 1.4 m benches)
# instead of one 30-45 m sheer face. h = max(base, min(T(e), upper terrain)) blended in where a much higher leg is near.
CAN_S0 = 1036.0
CAN_FACE, CAN_BENCH, CAN_RISE = 0.6, 1.4, 7.0
def can_steps(side):
    e0, h0 = (16.0, 9.46) if side == 'in' else (1.6, -0.1)   # inside: lattice (to 8.7) + the cedar band (9.5-15.5 at 7.6) stay on P_IN
    pts = [(0.0, h0 if side == 'out' else 0.0)] if side == 'out' else []
    pts.append((e0, h0)); e, h = e0, h0
    for k in range(9):
        e += CAN_FACE; h += CAN_RISE; pts.append((e, h))
        e += CAN_BENCH; h += 0.3; pts.append((e, h))
    return pts
CAN_T = {z: np.array(can_steps(z)) for z in ('in', 'out')}
CAN_ROWS = {z: [float(q[0]) for q in can_steps(z)[1:]] for z in ('in', 'out')}
def can_T(zone, e, s):
    t = CAN_T[zone]
    h = np.interp(e, t[:, 0], t[:, 1], left=-1e3)
    k = np.searchsorted(t[:, 0], e)   # per-step jitter along s so the benches read as rock ledges, not a staircase
    return h + 0.9 * np.sin(s * 0.21 + 1.7 * k) * min(1.0, max(0.0, (e - t[1, 0]) / CAN_FACE))
def combine(p, legs):
    h, o = combine0(p, legs)
    if h is None: return h, o
    for L in legs:
        if not (CAN_S0 <= L['s'] <= 1104.0) or L.get('along', 0.0) > 1e-6 or L['e'] < 0.0 or L['zone'] == 'road': continue
        ups = [q for q in legs if q is not L and q['yroad'] > L['yroad'] + 15.0 and q['e'] < 25.0]
        if not ups: continue
        U = min(ups, key=lambda q: q['e'])
        w = min(1.0, max(0.0, (25.0 - U['e']) / 8.0)) * min(1.0, max(0.0, (L['s'] - CAN_S0) / 8.0))
        if w <= 0.0: continue
        ht = max(L['h'], min(L['yedge'] + can_T(L['zone'], L['e'], L['s']), U['h']))
        h2 = h * (1.0 - w) + ht * w
        return h2, (L if w > 0.5 and ht < U['h'] - 0.01 else o)
    return h, o

def eval_pts(P):
    Hs = np.zeros(len(P)); own = []
    for k, p in enumerate(P):
        lg = legs_at(p); h, o = combine(p, lg)
        Hs[k] = h if h is not None else -200; own.append(o)
    return Hs, own

if __name__ == '__main__':
    import sys, time
    t0 = time.time()
    # ---------- constraint rows ----------
    E_ROWS = [-0.6, 0.0, 0.08, 0.55, 0.75, 0.7, 3.45, 3.55, 8.7, 8.75, 8.85, 9.0, 18.0, 32.0]
    lines = []
    KEPT = {}
    for side in (-1.0, 1.0):
        for e, ck in [(x, None) for x in E_ROWS] + [(x, 'in') for x in CAN_ROWS['in'] if x != 8.85] + [(x, 'out') for x in CAN_ROWS['out']]:
            pts = []; meta = []
            for i in range(NS):
                s = S[i]; ws = left_w(s) if side < 0 else W
                if ck is not None and (s < CAN_S0 - 2.0 or (ck == 'out') != is_out(s, side)): pts.append(None); continue
                if ck is not None: pass
                elif False: pass
                if ck is None and e in (0.55, 0.75) and not is_out(s, side): pts.append(None); continue
                if ck is None and e in (0.7, 8.7, 8.75, 8.85) and is_out(s, side): pts.append(None); continue
                if ck is None and e == 9.0 and not is_out(s, side): pts.append(None); continue
                p = C2[i] + NH[i] * side * (ws + e)
                pts.append(p)
            # ownership filter
            P = np.array([q for q in pts if q is not None])
            idx = [k for k, q in enumerate(pts) if q is not None]
            _, own = eval_pts(P)
            ok = {}
            Hrow, _ = eval_pts(P)
            for k, o, hh in zip(idx, own, Hrow):
                ok[k] = o is not None and abs(o['s'] - S[k]) < 5.0 and o['side'] == side
                if e in (3.55, 8.85) and o is not None and not ok[k]:
                    # wall top: the gallery line where another leg's higher terrain starts
                    i0 = k; ws = left_w(S[i0]) if side < 0 else W
                    ok[k] = hh > C[i0][1] + 1.0
            if ck is None: KEPT[(side, e)] = {k: (pts[k], hh) for k, hh in zip(idx, Hrow) if ok.get(k, False)}
            run = []
            for k in range(NS):
                if ok.get(k, False): run.append(pts[k])
                else:
                    if len(run) >= 2: lines.append(LineString(run))
                    run = []
            if len(run) >= 2: lines.append(LineString(run))
    # gallery / step walls: intermediate rows between the wall foot (3.45) and the wall top (3.55), heights interpolated, so a
    # 20-35 m wall is split into bands (per-vertex lamp light on one tall triangle saw-tooths) with no T-junctions
    NWALL = 8; WALLV = {}
    for side, (eb, et) in [(sd, pr) for sd in (-1.0, 1.0) for pr in ((3.45, 3.55), (8.75, 8.85))]:
        bot = KEPT[(side, eb)]; top = KEPT[(side, et)]
        cols = [k for k in range(NS) if k in bot and k in top and top[k][1] - bot[k][1] > 3.0]
        runs = []
        for k in cols:
            if runs and k == runs[-1][-1] + 1: runs[-1].append(k)
            else: runs.append([k])
        for j in range(1, NWALL + 1):
            f = j / (NWALL + 1.0); e = eb + 0.1 * f
            for r in runs:
                if len(r) < 2: continue
                pl = []
                for k in r:
                    ws = left_w(S[k]) if side < 0 else W
                    p = C2[k] + NH[k] * side * (ws + e); pl.append(p)
                    WALLV[(round(p[0], 3), round(p[1], 3))] = bot[k][1] + (top[k][1] - bot[k][1]) * f
                lines.append(LineString(pl))
    print('rows', len(lines), 'wall verts', len(WALLV), time.time() - t0)
    # ---------- domain ----------
    cl = LineString(C2)
    dom = cl.buffer(T['reach'], resolution=6).simplify(2.0)
    lines.append(LineString(np.array(dom.exterior.coords)))
    for it in dom.interiors: lines.append(LineString(np.array(it.coords)))
    net = unary_union(lines)
    segs_ = list(net.geoms) if hasattr(net, 'geoms') else [net]
    vid = {}; V = []; SEG = []
    def vi(q):
        k = (round(q[0], 3), round(q[1], 3))
        if k not in vid: vid[k] = len(V); V.append(q)
        return vid[k]
    for ls in segs_:
        cs = np.array(ls.coords)
        for a, b in zip(cs[:-1], cs[1:]):
            ia, ib = vi(a), vi(b)
            if ia != ib: SEG.append((ia, ib))
    V = np.array(V); SEG = np.array(SEG)
    print('pslg', len(V), len(SEG), time.time() - t0)
    holes = [list(np.array(it.representative_point().coords)[0]) for it in []]
    A = {'vertices': V, 'segments': SEG}
    out = tr.triangulate(A, 'pYa40')   # Y: no Steiner points on the 100 m boundary, the backdrop ring shares it vertex for vertex
    TV = out['vertices']; TF = out['triangles']
    print('tri', len(TV), len(TF), time.time() - t0)
    Hs, own = eval_pts(TV)
    nw = 0
    for vi, p in enumerate(TV):
        key = (round(p[0], 3), round(p[1], 3))
        if key in WALLV: Hs[vi] = WALLV[key]; nw += 1
    print('heights', time.time() - t0, 'wall verts set', nw)
    # ---------- backdrop rings (Austin pt364u: no hard terrain edge at 100 m even with fog off) ----------
    # ring 1: 100 -> 700 m (falloff into a valley / up the hill, then a ridge line); ring 2: 700 -> 2600 m (far ranges, past the
    # 2000 m overview far plane). Each ring shares its inner boundary vertex for vertex (Triangle -Y), so there is no seam.
    ymin, ymax = C[:, 1].min(), C[:, 1].max(); ctr = C2.mean(0)
    def ridge(p):
        a = np.arctan2(p[1] - ctr[1], p[0] - ctr[0])
        return ymax + 45.0 + 30.0 * np.sin(3 * a + 0.7) + 18.0 * np.sin(7 * a + 2.1) + 9.0 * np.sin(13 * a)
    def far_range(p):
        a = np.arctan2(p[1] - ctr[1], p[0] - ctr[0])
        return ymax + 170.0 + 70.0 * np.sin(4 * a + 1.3) + 35.0 * np.sin(9 * a + 0.4) + 15.0 * np.sin(17 * a + 2.0)
    NIN = len(TF); own = list(own)
    inner = dom; BP_all = TV.copy(); BH_all = Hs.copy()
    for RING, AREA, SIMP in ((700.0, 2500.0, 8.0), (2600.0, 60000.0, 40.0)):
        dom_out = cl.buffer(RING, resolution=4).simplify(SIMP)
        bkey = {(round(p[0], 3), round(p[1], 3)): k for k, p in enumerate(TV)}
        rV = []; rS = []; rmap = []
        def add_ring(coords, isin):
            cs = np.array(coords)[:-1]; n0 = len(rV)
            for q in cs:
                k = bkey.get((round(q[0], 3), round(q[1], 3)), -1) if isin else -1
                if isin and k < 0: raise SystemExit('ring vertex not on the inner boundary %s' % q)
                rV.append(q); rmap.append(k)
            for j in range(len(cs)): rS.append((n0 + j, n0 + (j + 1) % len(cs)))
        add_ring(inner.exterior.coords, True)
        for it in inner.interiors: add_ring(it.coords, True)
        add_ring(dom_out.exterior.coords, False)
        rout = tr.triangulate({'vertices': np.array(rV), 'segments': np.array(rS), 'holes': [list(C2[NS // 2])]}, 'pYqa%g' % AREA)
        RV = rout['vertices']; RF = rout['triangles']
        bidx = np.array([k for k in rmap if k >= 0]); BP = TV[bidx]; BH = Hs[bidx]; bkd = cKDTree(BP)
        gmap = []; newV = []; newH = []
        for j, p in enumerate(RV):
            if j < len(rmap) and rmap[j] >= 0: gmap.append(int(rmap[j])); continue
            if RING < 1000.0:
                dd_, ii = bkd.query(p, k=12); w = 1.0 / np.maximum(dd_, 1.0) ** 2
                hb = float(np.dot(w, BH[ii]) / w.sum()); dist = float(dd_[0])
                yr = C[kd.query(p)[1]][1]
                near = max(hb + (-0.6 if hb < yr else 0.35) * dist, ymin - 120.0)
                t = min(1.0, max(0.0, (dist - 150.0) / 450.0)); t = t * t * (3 - 2 * t)
                hv = near * (1 - t) + ridge(p) * t
            else:
                dist = float(cl.distance(Point(p[0], p[1])))
                t = min(1.0, max(0.0, (dist - 700.0) / 1100.0)); t = t * t * (3 - 2 * t)
                hv = ridge(p) * (1 - t) + far_range(p) * t
            gmap.append(len(TV) + len(newV)); newV.append(p); newH.append(hv)
        gmap = np.array(gmap)
        print('ring', RING, len(newV), 'verts', len(RF), 'tris')
        TV = np.vstack([TV, np.array(newV)]); Hs = np.concatenate([Hs, np.array(newH)])
        TF = np.vstack([TF, gmap[RF]]); own += [None] * len(newV)
        inner = dom_out
    np.savez('/workspace/touge_env_work/tri_raw.npz', TV=TV, TF=TF, Hs=Hs, NIN=NIN)
    import pickle
    pickle.dump([None if o is None else {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in o.items()} for o in own], open('/workspace/touge_env_work/own.pkl', 'wb'))
