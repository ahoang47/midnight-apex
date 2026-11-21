import numpy as np, pickle, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from terrain import *
z = np.load('/workspace/touge_env_work/tri_raw.npz'); TV, TF, Hs = z['TV'], z['TF'], z['Hs']
cen = TV[TF].mean(1)
Hc, ownc = eval_pts(cen)
keep = np.ones(len(TF), bool)
OWNV = pickle.load(open('/workspace/touge_env_work/own.pkl', 'rb'))
def deep(vi):
    q = OWNV[vi]; return q is not None and ((q['zone'] == 'road' and q['e'] < -0.3) or (q['zone'] != 'road' and (3.0 < q['e'] < 3.6 or 8.7 < q['e'] < 8.9)))
NIN = int(z['NIN']) if 'NIN' in z else len(TF)
from shapely.prepared import prep
from shapely.geometry import Point as _Pt
DOM = prep(LineString(C2).buffer(T['reach'], resolution=6).simplify(2.0))
for k, o in enumerate(ownc):
    if k >= NIN: ownc[k] = {'zone': 'ring', 's': 0.0, 'side': 1.0, 'e': 999.0}; continue   # backdrop ring: always kept
    if o is None or not DOM.contains(_Pt(cen[k][0], cen[k][1])): keep[k] = False; continue   # outside the 100 m domain: the ring has it
    if o['zone'] == 'road' and o['e'] < -0.6:
        # under an overhead road: keep it as fill (at that road's y - 0.15, hidden by the road) when a lower road's wall
        # stands below/beside it, so the gallery / canyon wall runs up into the deck with no jagged hole line
        lg = legs_at(cen[k])
        if all(deep(v) for v in TF[k]) and any(q is not o and q['yroad'] < o['yroad'] - 3.0 and G_PROT <= q['e'] < 20.0 for q in lg): continue
        keep[k] = False
TFk = TF[keep]
print('kept', keep.sum(), 'of', len(TF))
np.savez('/workspace/touge_env_work/tri_kept.npz', TV=TV, TF=TFk, Hs=Hs, keep=keep)
pickle.dump([ownc[k] for k in np.where(keep)[0]], open('/workspace/touge_env_work/ownc.pkl', 'wb'))
# ---- check: terrain over road ----
tri = mtri.Triangulation(TV[:, 0], TV[:, 1], TFk)
fnd = tri.get_trifinder()
bad = []; gap = []
for i in range(NS - 1):
    for t in (0.0, 0.5):
        c, n3, nh = frame(i, t); s = S[i] + 2 * t
        for dd in np.linspace(-W + 0.05, W - 0.05, 9):
            p = c[[0, 2]] + nh * dd; yr = c[1] + n3[1] * dd
            k = fnd(p[0], p[1])
            if k < 0: continue
            a, b, cc = TV[TFk[k]]
            # barycentric
            M = np.array([[b[0] - a[0], cc[0] - a[0]], [b[1] - a[1], cc[1] - a[1]]])
            u, v = np.linalg.solve(M, p - a)
            ht = Hs[TFk[k][0]] * (1 - u - v) + Hs[TFk[k][1]] * u + Hs[TFk[k][2]] * v
            if ht > yr - 0.005 and ht < yr + 8.0: bad.append((s, dd, ht - yr))
        for sd in (-1, 1):   # edge coverage just outside the road
            ws = left_w(s) if sd < 0 else W
            if ws > W + 0.01: continue
            E0 = C[i] + N3[i] * sd * W; E1 = C[i + 1] + N3[i + 1] * sd * W; Em = E0 * (1 - t) + E1 * t
            p = Em[[0, 2]] + nh * sd * 0.03; ye = Em[1]
            k = fnd(p[0], p[1])
            if k < 0: gap.append((s, sd, 'none')); continue
            a, b, cc = TV[TFk[k]]
            M = np.array([[b[0] - a[0], cc[0] - a[0]], [b[1] - a[1], cc[1] - a[1]]]); u, v = np.linalg.solve(M, p - a)
            ht = Hs[TFk[k][0]] * (1 - u - v) + Hs[TFk[k][1]] * u + Hs[TFk[k][2]] * v
            if abs(ht - ye) > 0.06: gap.append((s, sd, round(ht - ye, 2)))
print('OVER_ROAD', len(bad), bad[:20])
print('EDGE_GAP', len(gap))
import itertools
for sd in (-1,1):
    ss=sorted(set(g[0] for g in gap if g[1]==sd))
    grp=[]
    for s in ss:
        if grp and s-grp[-1][1]<=3: grp[-1][1]=s
        else: grp.append([s,s])
    print('  side',sd,grp)
json.dump([[float(g[0]),g[1]] for g in gap], open('/workspace/touge_env_work/gaps.json','w'))
fig, ax = plt.subplots(figsize=(16, 10))
ax.tripcolor(tri, Hs, shading='gouraud', cmap='terrain')
ax.triplot(tri, lw=0.1, color='k')
ax.plot(C2[:, 0], C2[:, 1], 'r-', lw=0.5)
ax.set_aspect('equal'); plt.savefig('/workspace/touge_env_work/terrain_plan.png', dpi=110)
