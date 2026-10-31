"""Extract S2000 silhouette curves from the blueprint crops -> bp/curves.json (metres, model axes: +x fwd, +z up)."""
import numpy as np, json
from PIL import Image
import os as _os; _B = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))) + '/'
R = _B + 'ref/'
def load(n): return np.asarray(Image.open(R + f'bp_{n}.png').convert('RGB')).astype(int)
out = {}

# ---------------- side (left side, nose to the left)
a = load('side_left'); H, W, _ = a.shape; mn = a.min(2); mx = a.max(2)
white = mn > 235; line = mx < 60; grey = (mn >= 60) & (mn <= 235)
cols = np.where((mx > 40).any(0))[0]; c0, c1 = cols.min(), cols.max()
L = 4.14; s = L / (c1 - c0 + 1); GROUND = 209.5
X = lambda c: 2.07 - (c - c0) * s
Z = lambda r: (GROUND - r) * s
top_sil, belt, bottom = [], [], []
def medf(v, k=9):
    v = np.asarray(v, float); h = k // 2
    return np.array([np.median(v[max(0, i - h):i + h + 1]) for i in range(len(v))])
bt_rows, bb_rows, xs = [], [], []
for c in range(c0, c1 + 1):
    col_any = mx[:, c] > 40
    rs = np.where(col_any)[0]; r_top = rs.min(); top_sil.append((X(c), Z(r_top)))
    r = r_top
    if Z(r_top) > 0.95:   # cabin: skip glass / soft top / frame down to the first white body pixel
        while r < H and not white[r, c]: r += 1
        # skip a small white island (door mirror) sitting on grey glass
        if r < H and grey[r + 3:r + 30, c].sum() > 8:
            r2 = r + 3
            while r2 < H and not (white[r2, c] and white[r2:r2 + 15, c].mean() > .8): r2 += 1
            r = r2
    bt = r
    rr = bt; last_w = bt
    while rr < H:
        if white[rr, c]: last_w = rr
        if grey[rr:rr + 6, c].all() and Z(rr) < 0.75: break
        if not col_any[rr:].any(): break
        rr += 1
    xs.append(X(c)); bt_rows.append(bt); bb_rows.append(last_w + 1)
bt_rows = medf(bt_rows, 11); bb_rows = medf(bb_rows, 9)
belt = [(x, Z(r)) for x, r in zip(xs, bt_rows)]; bottom = [(x, Z(r)) for x, r in zip(xs, bb_rows)]
out['side_top_silhouette'] = top_sil; out['side_body_top'] = belt; out['side_body_bottom'] = bottom
# wheel centres from tyre contact patches
bot = np.array([np.where(mx[:, c] > 40)[0].max() for c in range(c0, c1 + 1)])
cc = np.where(bot >= bot.max() - 1)[0] + c0
groups = np.split(cc, np.where(np.diff(cc) > 3)[0] + 1)
out['wheel_x'] = [X(g.mean()) for g in groups]
out['side_scale_m_per_px'] = s

# ---------------- top (rear at top, nose at bottom)
a = load('top'); H, W, _ = a.shape; mx = a.max(2)
rows = np.where((mx > 40).any(1))[0]; r0, r1 = rows.min(), rows.max()
st = L / (r1 - r0 + 1)
cx = None
plan = []
for r in range(r0, r1 + 1):
    cs = np.where(mx[r] > 40)[0]
    plan.append([-2.07 + (r - r0) * st, cs.min(), cs.max()])
plan = np.array(plan, float)
cx = np.median((plan[:, 1] + plan[:, 2]) / 2)
hw = np.maximum(cx - plan[:, 1], plan[:, 2] - cx) * st
# remove mirrors: clamp outliers above a running lower envelope
hw_f = hw.copy()
for i in range(len(hw)):
    lo, hi = max(0, i - 40), min(len(hw), i + 40)
    hw_f[i] = min(hw[i], np.percentile(hw[lo:hi], 60) + 0.01)
out['top_halfwidth'] = list(zip(plan[:, 0].tolist(), hw_f.tolist()))
out['top_scale_m_per_px'] = st

# ---------------- front / rear outlines: half-width per height (envelope), scaled by side scale
for name in ('front', 'rear'):
    a = load(name); H, W, _ = a.shape; mx = a.max(2); mn = a.min(2)
    rows = np.where((mx > 40).any(1))[0]; rb = rows.max() + 0.5
    cols = np.where((mx > 40).any(0))[0]; ccx = (cols.min() + cols.max()) / 2
    sc = s
    prof = []
    for r in range(rows.min(), rows.max() + 1):
        cs = np.where(mx[r] > 40)[0]
        prof.append(((rb - r) * sc, (ccx - cs.min()) * sc, (cs.max() - ccx) * sc))
    out[name + '_outline'] = prof
json.dump(out, open(_B + 'bp/curves.json', 'w'))
print('side scale', s, 'top scale', st, 'wheels', out['wheel_x'])
print('max half width (top, no mirrors)', hw_f.max(), 'height (side)', max(z for _, z in top_sil))
for nm in ('front', 'rear'):
    p = out[nm + '_outline']; print(nm, 'height', p[0][0], 'max hw', max(max(q[1], q[2]) for q in p))
