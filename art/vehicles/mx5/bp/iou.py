"""IoU gate: blueprint silhouettes (exact vector OUTLINE paths, bp/curves.json 'sil') vs the clay triangle soup
(out/bp/tris_carframe.npy, rest pose, everything rendered except struts and FX), both rasterised in the car frame at
2 mm / px.  No bbox fitting: blueprint frame = wheel centres (x), ground (z), centre line (y).
Gate: side >= .95, top >= .95, front >= .92, rear >= .92.  Writes out/bp/iou.json and out/renders/raw/iou_<view>.png
(grey = both, orange = blueprint only, red = clay only)."""
import numpy as np, cv2, json, os
OUT = '../' + os.environ.get('MX5_OUT', 'out')
RES = 0.002
d = json.load(open('curves.json'))
T = np.load(f'{OUT}/bp/tris_carframe.npy').reshape(-1, 3, 3)
AX = {'side': (0, 2), 'top': (0, 1), 'front': (1, 2), 'rear': (1, 2)}
GATE = dict(side=.95, top=.95, front=.92, rear=.92)
def grid(view):
    P = np.array(d['sil'][view]); a, b = AX[view]
    lo = np.minimum(P.min(0), np.r_[T[..., a].min(), T[..., b].min()]) - 0.05; hi = np.maximum(P.max(0), np.r_[T[..., a].max(), T[..., b].max()]) + 0.05
    return lo, np.ceil((hi - lo) / RES).astype(int)
res = {}; os.makedirs(f'{OUT}/renders/raw', exist_ok=True)
for view in ('side', 'top', 'front', 'rear'):
    lo, n = grid(view); a, b = AX[view]
    def px(Q): return np.round(np.c_[(Q[:, 0] - lo[0]) / RES, (n[1] - 1) - (Q[:, 1] - lo[1]) / RES] * 16).astype(np.int32)
    Bm = np.zeros((n[1], n[0]), np.uint8); cv2.fillPoly(Bm, [px(np.array(d['sil'][view]))], 1, shift=4)
    Cm = np.zeros_like(Bm)
    for t in T: cv2.fillPoly(Cm, [px(t[:, [a, b]])], 1, shift=4)
    Bm, Cm = Bm > 0, Cm > 0
    res[view] = round(float((Bm & Cm).sum() / (Bm | Cm).sum()), 4)
    ov = np.full(Bm.shape + (3,), 255, np.uint8); ov[Bm & Cm] = (190, 190, 190); ov[Bm & ~Cm] = (0, 140, 255); ov[Cm & ~Bm] = (0, 0, 230)
    if view == 'rear': ov = ov[:, ::-1]                       # drawn as seen from behind (car left on the image left)
    if view in ('side', 'top'): pass
    cv2.imwrite(f'{OUT}/renders/raw/iou_{view}.png', ov)
res['gate_thresholds'] = GATE; res['gate_pass'] = all(res[v] >= g for v, g in GATE.items())
json.dump(res, open(f'{OUT}/bp/iou.json', 'w'), indent=1); print(json.dumps(res))
