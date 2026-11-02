"""Fair (low-pass + smoothing spline) every traced curve before it drives geometry (same recipe as wrx/bp/fair.py:
bridge -> median + gaussian -> smoothing cubic spline, sampled every 5 mm).  Output bp/fair_curves.json (read inside
Blender by parts/gr_geo.py, which has numpy only) + renders/raw/fair_curves.png (raw grey vs fair colour).
Curves (car frame, metres):
  ZB    body bottom: side silhouette bottom, arches bridged, sill = one quadratic between the arches
  ZT    body top: side silhouette top; shark-fin antenna bridged; under the roof wing = roof end -> hatch-glass top
  ZBELT shoulder / belt: hood-fender shut line (nose) -> DLO bottom (cabin) -> hatch-glass bottom (tail)
  Z5    DLO top (cabin) / blended to a fixed share of (ZT - ZBELT) on the hood and hatch
  W     plan half-width (top view, mirrors bridged)
  Y5    plan half-width of the upper surface edge: hood edge (HOOD_T) / A-pillar (WS_T) / glass top (SIDE_GLASS_T
        inner edge) / C-pillar + hatch (ramped)
  YR    plan half-width of the roof edge (ROOF_T), used for the roof-rail row
  front_env / rear_env: centre-connected half-width per height (mirrors bridged), front / rear views"""
import json, numpy as np, cv2
from scipy import ndimage as ndi
from scipy.interpolate import UnivariateSpline
d = json.load(open('curves.json'))
A = lambda k, src=None: np.array((src or d)[k], float)
XW = d['wheel_x']; R_T = 0.5 * sum(d['tyre_r'])
sc = A('side_cols'); tc = A('top_cols')
X_NOSE, X_TAIL = float(sc[:, 0].max()), float(sc[:, 0].min())
grid = np.round(np.arange(X_TAIL, X_NOSE + 1e-9, 0.005), 4)
def lowpass(y, s, med=7): return ndi.gaussian_filter1d(ndi.median_filter(y, med, mode='nearest'), s, mode='nearest')
def bridge(x, y, zones):
    y = y.copy()
    for a, b in zones:
        m = (x > a) & (x < b); ok = ~m; y[m] = np.interp(x[m], x[ok], y[ok])
    return y
def spl(x, y, rms): return UnivariateSpline(x, y, k=3, s=len(x) * rms ** 2)
def col(cls, src='side'):
    a = A(cls, d[src]); return a[np.argsort(a[:, 0])]
out = dict(grid=grid.tolist(), x_nose=X_NOSE, x_tail=X_TAIL, wheel_x=XW, tyre_r=R_T); raw = {}
# ---- arches: circle fit to the arch-line profile (rays from the hub; tyre hits removed)
arch = []
for (xw, zw, rt, prof) in zip(XW, d['wheel_z'], d['tyre_r'], d['arch_profile']):
    p = np.array(prof); p = p[(p[:, 1] > rt * 1.03 + 0.006) & (p[:, 0] > -5) & (p[:, 0] < 185)]
    P = np.c_[xw + p[:, 1] * np.cos(np.radians(p[:, 0])), zw + p[:, 1] * np.sin(np.radians(p[:, 0]))]
    M_ = np.c_[2 * P, np.ones(len(P))]; c = np.linalg.lstsq(M_, (P ** 2).sum(1), rcond=None)[0]
    r = float(np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)); arch.append(dict(xc=float(c[0]), zc=float(c[1]), r=r, n=len(P),
        rms_mm=float(1000 * np.sqrt(np.mean((np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]) - r) ** 2)))))
out['arch_f'], out['arch_r'] = arch
# ---- ZB
x, zb = sc[:, 0], sc[:, 1]; raw['ZB'] = (x, zb.copy())
zones = [(a['xc'] - a['r'] - 0.03, a['xc'] + a['r'] + 0.03) for a in arch]
zb = bridge(x, zb, zones)
mid = (x > zones[1][1]) & (x < zones[0][0]); c = np.polyfit(x[mid], ndi.median_filter(zb[mid], 21), 2); zb[mid] = np.polyval(c, x[mid])
zb = lowpass(zb, 3)
out['ZB'] = np.interp(grid, x, zb).tolist()
# ---- ZT (antenna bridged; wing replaced by the hatch line under it)
zt = sc[:, 2].copy(); raw['ZT'] = (x, zt.copy())
hg = col('HATCH_GLASS_S'); hx = np.unique(np.round(hg[:, 0], 3)); htop = np.array([hg[np.abs(hg[:, 0] - q) < 0.003, 2].max() for q in hx])
x_roof_end = -1.30
zt = bridge(x, zt, [(-1.36, -1.08)])                                   # shark-fin antenna (x -1.33..-1.12) -> roof line
z_roof_end = float(np.interp(x_roof_end, x, zt))
hatch_top = lowpass(htop, 4, 5) + 0.010                                 # hatch skin over the glass (stroke + seal)
m = (x > -1.86) & (x < x_roof_end)
# hatch top under the wing: glass top where traced (x <= -1.49), then a straight run up to the roof end
hk_ = (hx <= -1.49) & (hx >= -1.85); ch = np.polyfit(np.r_[hx[hk_], x_roof_end], np.r_[hatch_top[hk_], z_roof_end], 1,
                                                   w=np.r_[np.ones(hk_.sum()), 8.0])          # the hatch glass is straight in side view
zt[m] = np.polyval(ch, x[m]); out['hatch_line'] = ch.tolist()
zt = lowpass(zt, 2, 5)
mh = (x > -1.86) & (x < -1.20); zt[mh] = ndi.gaussian_filter1d(zt, 10, mode='nearest')[mh]   # hatch run: one faired line
out['ZT'] = np.interp(grid, x, zt).tolist(); out['x_roof_end'] = x_roof_end
# ---- ZBELT
dg = np.vstack([col('DLO_GLASS'), col('DLO_PILLAR')]); dx = np.unique(np.round(dg[:, 0], 3))
dbot = np.array([dg[np.abs(dg[:, 0] - q) < 0.003, 1].min() for q in dx]); dtop = np.array([dg[np.abs(dg[:, 0] - q) < 0.003, 2].max() for q in dx])
cab = (dx > -1.12) & (dx < 0.47)
cb = np.polyfit(dx[cab], ndi.median_filter(dbot[cab], 15), 2)            # DLO bottom (belt) over the door glass
hs = col('HOOD_S'); hsx = np.unique(np.round(hs[:, 0], 3)); hsb = np.array([hs[np.abs(hs[:, 0] - q) < 0.003, 1].min() for q in hsx])
hk = (hsx > 1.32) & (hsx < 2.08); hb = lowpass(hsb[hk], 6, 9); hbx = hsx[hk]
hgb = np.array([hg[np.abs(hg[:, 0] - q) < 0.003, 1].min() for q in hx]); hk2 = hx < -1.66
# belt anchor list: hood shut line (nose) <- blend <- cabin quadratic -> C-pillar -> hatch-glass bottom
bx = np.r_[hx[hk2][::8], -1.40, np.linspace(-1.12, 0.47, 30), 0.80, hbx[::6]]
bz = np.r_[hgb[hk2][::8] - 0.010, np.polyval(cb, -1.12) + 0.004, np.polyval(cb, np.linspace(-1.12, 0.47, 30)), np.polyval(cb, 0.80) - 0.004, hb[::6]]
o = np.argsort(bx); bx, bz = bx[o], bz[o]
belt = spl(bx, bz, 0.004)(grid)
zt_g = np.array(out['ZT'])
belt = np.minimum(belt, zt_g - 0.012)
for e in (grid > hbx.max(), grid < hx[hk2].min()):                      # nose / tail tips: follow the top 2.5..6 cm down
    belt[e] = np.minimum(belt[e], zt_g[e] - 0.025)
out['ZBELT'] = belt.tolist(); raw['BELT'] = (dx, dbot)
# ---- Z5: DLO top (side glass top / A-pillar) over the cabin, else a share of (ZT - ZBELT)
ct = (dx > -1.08) & (dx < 1.06)
ct &= ~((dx > 0.36) & (dx < 0.56))                                     # mirror sail / A-pillar notch bridged
dtop_f = spl(dx[ct], lowpass(dtop[ct], 3, 9), 0.006)(np.clip(grid, -1.08, 1.06)); z5c = dtop_f
share = 0.62; z5d = belt + share * (zt_g - belt)
w = np.clip(np.minimum((grid - (-1.08)) / 0.12, (1.06 - grid) / 0.12), 0, 1); w = w * w * (3 - 2 * w)
z5 = w * np.minimum(z5c, zt_g - 0.02) + (1 - w) * z5d
out['Z5'] = ndi.gaussian_filter1d(z5, 6).tolist(); raw['Z5'] = (dx, dtop)
# ---- W (plan half-width, mirrors bridged)
xt = tc[:, 0]; hw = 0.5 * (tc[:, 2] - tc[:, 1]); raw['W'] = (xt, hw.copy())
hw = bridge(xt, hw, [(0.47, 0.76)])
hw = lowpass(hw, 2, 5)
s_ = spl(xt[(xt > X_TAIL + .01) & (xt < X_NOSE - .01)], hw[(xt > X_TAIL + .01) & (xt < X_NOSE - .01)], 0.002)
Wf = s_(grid)
for e in (grid > X_NOSE - 0.06, grid < X_TAIL + 0.06): Wf[e] = np.interp(grid[e], xt, hw)
out['W'] = np.maximum(Wf, 0.02).tolist()
# ---- Y5 / YR (plan, left half)
TL = d['top_left']
def edge(k, hi=True, lo_x=-9, hi_x=9):
    a = np.array(TL[k]); a = a[(a[:, 0] > lo_x) & (a[:, 0] < hi_x)]; return a[:, 0], (a[:, 2] if hi else a[:, 1])
gx, gin = edge('SIDE_GLASS_T', hi=False); wsx, wso = edge('WS_T', lo_x=0.40, hi_x=1.06); hdx, hdo = edge('HOOD_T', lo_x=1.30, hi_x=2.12)
rfx, rfo = edge('ROOF_T', lo_x=-1.30, hi_x=0.26)
# windshield outer edge and the glass top meet at the A-pillar; glass-top rows ahead of x .40 are the A-pillar sail
gk = (gx > -0.85) & (gx < 0.30); wk = wsx > 0.46
yx = np.r_[-1.95, -1.80, -1.62, -1.45, -1.30, gx[gk], wsx[wk], hdx]
yv = np.r_[0.50, 0.58, 0.62, 0.62, 0.60, gin[gk], wso[wk], hdo]
o = np.argsort(yx); yx, yv = yx[o], yv[o]
y5 = spl(yx, lowpass(yv, 3, 5), 0.006)(grid)
y5[grid > 2.12] = np.interp(grid[grid > 2.12], [2.12, X_NOSE], [float(np.interp(2.12, hdx, hdo)), 0.05])
out['Y5'] = np.clip(y5, 0.03, None).tolist(); raw['Y5'] = (yx, yv)
yr = np.interp(grid, rfx, lowpass(rfo, 3, 5)); out['YR'] = yr.tolist()
out['glass_top_inner'] = dict(x=gx.tolist(), y=gin.tolist())
# ---- front / rear envelopes
for k in ('front', 'rear'):
    r = np.array([q for q in d[k + '_rows'] if q[1] is not None], float); z = r[:, 0]; h = 0.5 * (r[:, 2] - r[:, 1])
    h = bridge(z, h, [(0.84, 1.10)]); keep = z < z.max() - 0.004
    z, h = z[keep], h[keep]; raw[k] = (z, h.copy())
    h = ndi.gaussian_filter1d(ndi.median_filter(h, 5, mode='nearest'), 3, mode='nearest')
    out[k + '_env'] = dict(z=z.tolist(), hw=h.tolist())
    # crown: silhouette top height vs half-width (greenhouse top contour), for the roof-crown rows
    P = np.array(d['sil'][k]); P = P[P[:, 1] > 1.2]; yy = np.abs(P[:, 0]); o = np.argsort(yy)
    out[k + '_crown'] = dict(y=yy[o].tolist(), z=P[o, 1].tolist())
json.dump(out, open('fair_curves.json', 'w'))
# ---- record plot
img = np.full((1200, 1600, 3), 255, np.uint8)
def plot(xr, yr_, xf, yf, box, col_, title):
    x0, y0, w_, h_ = box; xs = np.r_[xr, xf]; lo, hi = min(np.min(yr_), np.min(yf)), max(np.max(yr_), np.max(yf))
    X = lambda v: (x0 + (np.asarray(v) - xs.min()) / (xs.max() - xs.min()) * w_).astype(int); Y = lambda v: (y0 + h_ - (np.asarray(v) - lo) / (hi - lo + 1e-9) * h_).astype(int)
    for a, b in zip(X(xr), Y(yr_)): cv2.circle(img, (int(a), int(b)), 1, (170, 170, 170), -1)
    cv2.polylines(img, [np.c_[X(xf), Y(yf)].astype(np.int32)], False, col_, 2, cv2.LINE_AA); cv2.putText(img, title, (x0, y0 - 6), 0, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
plot(raw['W'][0], raw['W'][1], grid, out['W'], (40, 40, 1520, 200), (0, 0, 220), 'plan half-width W(x): grey raw (mirrors), red fair')
plot(raw['ZB'][0], raw['ZB'][1], grid, out['ZB'], (40, 300, 1520, 180), (0, 140, 0), 'body bottom ZB(x): grey raw silhouette bottom (tyres), green fair')
plot(raw['ZT'][0], raw['ZT'][1], grid, out['ZT'], (40, 540, 1520, 180), (200, 80, 0), 'body top ZT(x): grey raw (antenna, wing), blue fair (hatch under the wing)')
plot(np.r_[raw['BELT'][0], raw['Z5'][0]], np.r_[raw['BELT'][1], raw['Z5'][1]], np.r_[grid, grid[::-1]], np.r_[out['ZBELT'], out['Z5'][::-1]], (40, 780, 1520, 160), (150, 0, 150), 'belt ZBELT + DLO top Z5: grey traced DLO, purple fair')
plot(raw['Y5'][0], raw['Y5'][1], grid, out['Y5'], (40, 1000, 1520, 160), (0, 120, 200), 'Y5 plan edge of the upper surface (hood / A-pillar / glass top / hatch)')
cv2.imwrite('../renders/raw/fair_curves.png', img)
print('arches', json.dumps(arch)); print('X', X_NOSE, X_TAIL, 'roof end z', z_roof_end)
