"""Clipping sweep: terrain vs Gordon's code-placed kit (lattice, cedars, delineators) and the baked lamps / rails."""
import numpy as np, json, sys
import matplotlib.tri as mtri
from terrain import *
z = np.load('/workspace/touge_env_work/tri_kept.npz'); TV, TF, Hs = z['TV'], z['TF'], z['Hs']
tri = mtri.Triangulation(TV[:, 0], TV[:, 1], TF); fnd = tri.get_trifinder()
def th(p):
    k = fnd(p[0], p[1])
    if k < 0: return None
    a, b, c = TV[TF[k]]; M = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]]); u, v = np.linalg.solve(M, p - a)
    f = TF[k]; return Hs[f[0]] * (1 - u - v) + Hs[f[1]] * u + Hs[f[2]] * v
def at(s, d):
    i = int(np.clip(np.searchsorted(S, s) - 1, 0, NS - 2)); t = (s - S[i]) / (S[i + 1] - S[i])
    c, n3, nh = frame(i, t); return c[[0, 2]] + nh * d, c[1] + n3[1] * d
LAT = np.array([[0.7, 0.02], [5.74, 7.23], [8.7, 7.6]])
res = {'lattice_poke': [], 'cedar_in_float': [], 'cedar_in_buried': [], 'deline': [], 'lamp': [], 'rail': []}
for s in np.arange(-60.0, 1075.0, 1.0):
    ins = -drop_s(s)
    if left_w(s) > W + 0.05 and ins < 0: continue        # lot: Gordon's lot scene owns that side
    for e in (0.7, 2.0, 3.5, 5.0, 5.74, 7.0, 8.0, 8.7):
        p, _ = at(s, ins * (W + e)); t = th(p)
        if t is None: continue
        y = at(s, ins * (W + 0.7))[1]   # the module is rigid: origin at elev(s, W + 0.7), not rolled to the bank
        lh = y + np.interp(e, LAT[:, 0], LAT[:, 1])
        if t > lh + 0.05: res['lattice_poke'].append((float(s), e, round(float(t - lh), 2)))
    for e in (9.5, 12.5, 15.5):
        p, y = at(s, ins * (W + e)); t = th(p)
        if t is None: continue
        b = y + 7.6
        if t < b - 1.0: res['cedar_in_float'].append((float(s), e, round(float(t - b), 2)))
        if t > b + 4.0: res['cedar_in_buried'].append((float(s), e, round(float(t - b), 2)))
    for sd, e in ((ins, 0.5), (-ins, 0.62)):
        p, y = at(s, sd * (W + e)); t = th(p)
        if t is not None and abs(t - y) > 0.12: res['deline'].append((float(s), sd, round(float(t - y), 2)))
REF = d['reference']
for lp in REF['lamps']:
    if lp['kind'] != 'road': continue
    p = np.array(lp['pos']); t = th(p[[0, 2]])
    if t is None or abs(t - p[1]) > 0.1: res['lamp'].append((lp['s'], None if t is None else round(float(t - p[1]), 2)))
for rl in REF['rails']:
    if not rl['visible']: continue
    p = np.array(rl['pos']); t = th(p[[0, 2]])
    if t is None or abs(t - p[1]) > 0.1: res['rail'].append((rl['s'], None if t is None else round(float(t - p[1]), 2)))
def runs(lst):
    out = []
    for q in lst:
        if out and q[0] - out[-1][1] <= 2.0: out[-1][1] = q[0]; out[-1][2] = max(out[-1][2], abs(q[-1]) if q[-1] is not None else 99)
        else: out.append([q[0], q[0], abs(q[-1]) if q[-1] is not None else 99])
    return out
for k, v in res.items(): print(k, len(v), [(a, b, round(c, 2)) for a, b, c in runs(v)][:40])
json.dump(res, open('/workspace/touge_env_work/props_check.json', 'w'))
