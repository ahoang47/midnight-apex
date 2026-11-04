"""MX-5 ND (copy of gr_corolla/bp/vectors.py; emblem test widened to the ND's smaller oval).
Blueprint features as VECTORS for the body painter (A.3.2: panel lines are drawn as vector polylines, never traced
from a raster).  Writes bp/feature_vectors.json:
  [view]['lines']    TRANSPORT-layer paths/lines (body, shut, DLO, lamp, trim lines), car frame, per view
  [view]['details']  DETAILS-layer paths (creases, lamp internals): painted faint
  [view]['polys'][CLASS]  region outlines (classified regions of extract.py, contour -> Douglas-Peucker), car frame
Tyre / wheel paths (inside the fitted tyre circles in the side view, TYRE_F / TYRE_R in front / rear) are dropped."""
import json, numpy as np, cv2
import xml.etree.ElementTree as ET
from frames import layer, NS, path_pts, which, to_car, D, S
SC = 6
def elems(lid):
    out = []
    for e in layer(lid).iter():
        t = e.tag.split('}')[1]
        if t == 'path': P = path_pts(e.get('d'), 6)
        elif t == 'line': P = np.array([[float(e.get('x1')), float(e.get('y1'))], [float(e.get('x2')), float(e.get('y2'))]])
        elif t in ('polyline', 'polygon'):
            q = np.array(e.get('points').replace(',', ' ').split(), float).reshape(-1, 2); P = np.vstack([q, q[:1]]) if t == 'polygon' else q
        else: continue
        if len(P) >= 2: out.append(P)
    return out
R = np.load('regions.npz')
def inside_tyre(view, C):
    if view == 'side':
        for xw, zw, rw in zip(D['wheel_x'], D['wheel_z'], D['tyre_r']):
            if np.mean(np.hypot(C[:, 0] - xw, C[:, 1] - zw) < rw * 0.995) > 0.5: return True
    return False
def reg_frac(view, P, cls):
    m = R[cls]; u = np.clip(np.round(P[:, 0] * SC).astype(int), 0, m.shape[1] - 1); v = np.clip(np.round(P[:, 1] * SC).astype(int), 0, m.shape[0] - 1)
    return m[v, u].mean()
out = {v: dict(lines=[], details=[], polys={}) for v in ('side', 'top', 'front', 'rear')}
DROPPED = []
for lid, key in (('_x32_D_x24_AG-TRANSPORT', 'lines'), ('_x32_D_x24_AG-DETAILS', 'details')):
    for P in elems(lid):
        v = which(P); C = to_car(v, P)
        if inside_tyre(v, C): continue
        c_, wh = C.mean(0), np.ptp(C, 0)
        if v in ('front', 'rear') and abs(c_[0]) < 0.05 and 0.08 < wh[0] < 0.20 and 0.04 < wh[1] < 0.12 and 0.50 < c_[1] < 0.95 and np.linalg.norm(C[0] - C[-1]) < 0.01:
            DROPPED.append(dict(view=v, centre=np.round(c_, 3).tolist(), size=np.round(wh, 3).tolist())); continue   # real maker emblem: never painted
        if v == 'front' and reg_frac(v, P, 'TYRE_F') > 0.5: continue
        if v == 'rear' and reg_frac(v, P, 'TYRE_R') > 0.5: continue
        out[v][key].append(np.round(C, 5).tolist())
VIEW = {k: ('side' if k.endswith('_S') or k in ('DLO_GLASS',) else 'top' if k.endswith('_T') else 'front' if k.endswith('_F') else 'rear') for k in R.files}
for cls in R.files:
    m = R[cls].astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); ps = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) < 150: continue
        c = cv2.approxPolyDP(c, 0.6, True)[:, 0, :] / SC                    # 0.1 SVG unit = 0.8 mm tolerance
        ps.append(np.round(to_car(VIEW[cls], c), 5).tolist())
    out[VIEW[cls]]['polys'][cls] = ps
out['dropped_emblems'] = DROPPED
json.dump(out, open('feature_vectors.json', 'w'))
print('dropped (maker emblem outlines):', DROPPED)
print({v: (len(o['lines']), len(o['details']), {k: len(p) for k, p in o['polys'].items()}) for v, o in out.items() if v != 'dropped_emblems'})
