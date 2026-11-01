"""Pass 2: fair (smooth) every traced curve before it drives geometry.  Pass 1 fed raw per-column traces straight into
the loft, so 1-px tracing noise (5.7 mm), mirror bleed in the top view and the sill bridge under the arches turned into
station-to-station width / height jumps = the vertical ripple on the doors.  Here every curve is
  1. cleaned (mirror / scoop / wheel zones removed and bridged),  2. low-passed (median + gaussian, stronger along the
  flanks than at the nose / tail), 3. refitted with a smoothing cubic spline (C2), then sampled every 5 mm.
Writes bp/fair_curves.json (read by parts/wrx_bp.py inside Blender, which has no scipy).  Also writes
renders/clay_raw/fair_curves.png (raw vs fair) for the record."""
import json, numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import UnivariateSpline
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']
def arr(k): return np.array(d[k], float)
def srt(p): return p[np.argsort(p[:, 0])]
WX = sorted(d['side_wheel_x'], reverse=True)
def arch(xc):
    bb = arr('side_blue_bot'); m = (np.abs(bb[:, 0] - xc) < 0.42) & (bb[:, 1] > 0.32); p = bb[m]
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]; c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    return dict(xc=float(c[0]), zc=float(c[1]), r=float(np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)), x0=float(p[:, 0].min()), x1=float(p[:, 0].max()))
AF, AR = arch(WX[0]), arch(WX[1])
def lowpass(x, y, sig_mid, sig_end, x_end=1.75, med=9):
    """median + gaussian with sigma (in samples) blended from sig_mid on the flanks to sig_end at the ends."""
    ym = ndi.median_filter(y, med, mode='nearest')
    a = ndi.gaussian_filter1d(ym, sig_mid, mode='nearest'); b = ndi.gaussian_filter1d(ym, sig_end, mode='nearest')
    t = np.clip((np.abs(x) - x_end) / 0.2, 0, 1); t = t * t * (3 - 2 * t)
    return (1 - t) * a + t * b
def spline(x, y, rms):
    sp = UnivariateSpline(x, y, k=3, s=len(x) * rms ** 2); return sp
def bridge(x, y, zones):
    y = y.copy()
    for a, b in zones:
        m = (x > a) & (x < b); ok = ~m
        y[m] = np.interp(x[m], x[ok], y[ok])
    return y
X_NOSE = float(arr('top_halfwidth')[:, 0].max()); X_TAIL = float(arr('side_sil_top')[:, 0].min())
grid = np.round(np.arange(X_TAIL, X_NOSE + 1e-9, 0.005), 4)
out = {'grid': grid.tolist(), 'arch_f': AF, 'arch_r': AR, 'x_nose': X_NOSE, 'x_tail': X_TAIL, 'wheel_x': WX}
raw = {}
# ---- plan half-width (top view, both sides averaged; mirror zones x .40-.95 bridged on both sides)
hw = srt(arr('top_halfwidth_raw')); x = hw[:, 0]; y = 0.5 * (hw[:, 1] + hw[:, 2])
y = bridge(x, y, [(0.38, 0.97)])
raw['W'] = (x, y.copy())
y = lowpass(x, y, 30, 1.5)
m = (x > X_TAIL + 0.004) & (x < X_NOSE - 0.004)
spW = spline(x[m], y[m], 0.003)
W = spW(grid)
for e in (grid > X_NOSE - 0.04, grid < X_TAIL + 0.04):          # spline ends overshoot on the steep nose / tail closes:
    W[e] = np.interp(grid[e], x, y)                              # use the low-passed trace there (C0 join, 4 cm in)
W = np.maximum(W, 0.03)
out['W'] = W.tolist()
# ---- side silhouette top (nose, roof, tail) and bottom
st = srt(arr('side_sil_top')); raw['SIL_TOP'] = (st[:, 0], st[:, 1])
t = lowpass(st[:, 0], st[:, 1], 5, 1.0)
t = bridge(st[:, 0], t, [(-0.36, -0.08)])                         # roof nub
out['SIL_TOP'] = np.interp(grid, st[:, 0], t).tolist()
sb = srt(arr('side_sil_bot')); raw['SIL_BOT'] = (sb[:, 0], sb[:, 1])
xb, yb = sb[:, 0], sb[:, 1].copy()
yb = bridge(xb, yb, [(AF['x0'] - 0.03, AF['x1'] + 0.03), (AR['x0'] - 0.03, AR['x1'] + 0.03)])
mid = (xb > AR['x1'] + 0.03) & (xb < AF['x0'] - 0.03)               # sill: one straight-ish line (quadratic)
c = np.polyfit(xb[mid], ndi.median_filter(yb[mid], 15), 2)
yb[mid] = np.polyval(c, xb[mid])
yb = lowpass(xb, yb, 8, 2.0, x_end=1.65)
out['ZB'] = np.interp(grid, xb, yb).tolist()
# ---- hood line (side paint top; scoop + mirror are dark so not in it): quadratic over x .93-1.55, blended into the nose
bt = srt(arr('side_blue_top')); raw['BLUE_TOP'] = (bt[:, 0], bt[:, 1])
mh = (bt[:, 0] > 0.93) & (bt[:, 0] < 1.55)
ch = np.polyfit(bt[mh, 0], bt[mh, 1], 2)
out['hood_poly'] = ch.tolist()
# ---- side DLO: door-glass bottom / top as quadratics over the door glass interiors; windshield / rear-glass wrap bands
reg = {}
for g in d['side_glass_regions']:
    if g['z'][0] > 1.40: continue
    cx = 0.5 * sum(g['x']); k = 'ws' if cx > 0.5 else ('front_door' if cx > -0.3 else ('rear_door' if cx > -1.05 else 'rear_glass'))
    reg[k] = g
gc = srt(arr('side_glass_cols'))
def cols(k, shrink=0.05):
    r = reg[k]; m = (gc[:, 0] > r['x'][0] + shrink) & (gc[:, 0] < r['x'][1] - shrink) & (gc[:, 1] < 1.40); return gc[m]
doors = np.vstack([cols('front_door'), cols('rear_door', 0.0)])
rd = cols('rear_door', 0.0); rd = rd[rd[:, 0] > -0.80]                # drop the sash-triangle corner (top slants down)
dt = np.vstack([cols('front_door'), rd])
ct = np.polyfit(dt[:, 0], ndi.median_filter(dt[:, 1], 9), 2)            # DLO top (roof-rail line)
fd, rdb = cols('front_door'), cols('rear_door')
out['dlo_top_poly'] = ct.tolist()
out['glass_bot_front'] = float(np.median(fd[:, 2])); out['glass_bot_rear'] = float(np.median(rdb[:, 2]))
cb = np.polyfit(np.r_[fd[:, 0], rdb[:, 0]], np.r_[fd[:, 2], rdb[:, 2]], 1)
out['dlo_bot_poly'] = cb.tolist()
for k in ('ws', 'rear_glass'):
    g = cols(k, 0.03); out[f'{k}_band'] = dict(x=g[:, 0].tolist(), top=ndi.gaussian_filter1d(g[:, 1], 4).tolist(), bot=ndi.gaussian_filter1d(g[:, 2], 4).tolist())
out['glass_regions'] = {k: dict(x=v['x'], z=v['z']) for k, v in reg.items()}
# ---- front / rear outline envelopes (half-width per height): mirror rows bridged, low-passed in z
for k in ('front', 'rear'):
    p = srt(arr(k + '_outline_raw')); z = p[:, 0]; h = 0.5 * (p[:, 1] + p[:, 2])
    h = bridge(z, h, [(0.92, 1.08)]); keep = z < z.max() - 0.012; z, h = z[keep], h[keep]
    raw[k] = (z, h.copy())
    h = ndi.gaussian_filter1d(ndi.median_filter(h, 5, mode='nearest'), 2.0, mode='nearest')
    out[k + '_env'] = dict(z=z.tolist(), hw=h.tolist())
json.dump(out, open('bp/fair_curves.json', 'w'))
# ---- record plot
import cv2
img = np.full((900, 1600, 3), 255, np.uint8)
def plot(xr, yr, xf, yf, box, col, title, ys=600):
    x0, y0, w, h = box; lo, hi = min(yr.min(), np.min(yf)), max(yr.max(), np.max(yf))
    X = lambda v: (x0 + (v - xr.min()) / (xr.max() - xr.min()) * w).astype(int); Y = lambda v: (y0 + h - (v - lo) / (hi - lo + 1e-9) * h).astype(int)
    for a, b in zip(X(xr), Y(yr)): cv2.circle(img, (int(a), int(b)), 1, (170, 170, 170), -1)
    cv2.polylines(img, [np.c_[X(np.asarray(xf)), Y(np.asarray(yf))].astype(np.int32)], False, col, 2, cv2.LINE_AA)
    cv2.putText(img, title, (x0, y0 - 6), 0, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
plot(raw['W'][0], raw['W'][1], grid, W, (40, 40, 1520, 240), (0, 0, 220), 'plan half-width W(x): grey raw trace (mirror zone bridged), red fair')
plot(raw['SIL_BOT'][0], raw['SIL_BOT'][1], grid, out['ZB'], (40, 340, 1520, 220), (0, 140, 0), 'body bottom ZB(x): grey raw silhouette bottom (tyres included), green fair (arches bridged, sill quadratic)')
plot(raw['SIL_TOP'][0], raw['SIL_TOP'][1], grid, out['SIL_TOP'], (40, 640, 1520, 220), (200, 80, 0), 'side silhouette top: grey raw, blue fair (roof nub bridged)')
cv2.imwrite('renders/clay_raw/fair_curves.png', img)
print('fair curves ok; W mid-flank residual rms (mm):', round(1000 * float(np.sqrt(np.mean((spW(x[np.abs(x) < 1.6]) - raw['W'][1][np.abs(x) < 1.6]) ** 2))), 2))
