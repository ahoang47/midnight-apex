"""MX-5 (ND, soft top): fair (low-pass + smoothing spline) every traced curve before it drives geometry (same recipe as
gr_corolla/bp/fair.py: bridge -> median + gaussian -> smoothing cubic spline, sampled every 5 mm).  Output
bp/fair_curves.json (read inside Blender by parts/mx5_geo.py, numpy only) + renders/raw/fair_curves.png.
Curves (car frame, metres; x fwd from mid-wheelbase, nose x +1.913, tail x -2.003):
  ZB    body bottom: side silhouette bottom, arches bridged, sill = one quadratic between the arches
  ZT    body top: side silhouette top (front fender peaks -> windshield -> soft top -> deck/trunk); nothing bridged
  ZBELT shoulder / belt: hood-fender line (HOOD_S bottom, nose) -> fender top -3 cm -> cowl -> DLO bottom (door glass)
        -> soft-top base (SOFTTOP_S bottom) -> deck/trunk shut line (DECK_S bottom, tail)
  Z5    upper edge height: DLO top (glass top, cabin) -> A-pillar (between DLO and the windshield) / a share of
        (ZT - ZBELT) on the hood, the soft-top quarter and the trunk
  W     plan half-width (top view, mirrors bridged)
  Y5    plan half-width of the upper surface edge: hood edge (HOOD_T) / windshield edge (WS_T) / side-glass top
        (SIDE_GLASS_T inner edge) / soft-top edge (ROOF_T) / trunk edge (TRUNK_T)
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
def colstat(cls, f, src='side', k=1):
    a = col(cls, src); xs = np.unique(np.round(a[:, 0], 3))
    return xs, np.array([f(a[np.abs(a[:, 0] - q) < 0.003, k]) for q in xs])
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
# ---- ZT (the roadster's whole top line is body: fender peaks, screen, soft top, deck)
zt = sc[:, 2].copy(); raw['ZT'] = (x, zt.copy())
zt = lowpass(zt, 2, 5)
out['ZT'] = np.interp(grid, x, zt).tolist(); zt_g = np.array(out['ZT'])
# ---- ZBELT
gx, gbot = colstat('DLO_GLASS', np.min); gx2, gtop = colstat('DLO_GLASS', np.max, k=2)
stx, stb = colstat('SOFTTOP_S', np.min)
dkx, dkb = colstat('DECK_S', np.min)
hsx, hsb = colstat('HOOD_S', np.min)
cab = (gx > -0.66) & (gx < -0.18)
cb = np.polyfit(gx[cab], ndi.median_filter(gbot[cab], 15), 2)              # DLO bottom (door belt) over the door glass
XG0, XG1 = float(gx.min()), float(gx.max())                                  # DLO glass x range
st_k = (stx < -0.80) & (stx > -1.24)                                         # soft-top base behind the glass
hk = (hsx > 1.20) & (hsx < 1.70)
fz = lambda q: float(np.interp(q, grid, zt_g))
bx = np.r_[dkx[::6], stx[st_k][::6], np.linspace(-0.66, -0.18, 20), 0.20, 0.32, 0.45, 0.70, 0.95, hsx[hk][::6]]
bz = np.r_[dkb[::6] - 0.006, stb[st_k][::6] - 0.004, np.polyval(cb, np.linspace(-0.66, -0.18, 20)),
           np.polyval(cb, 0.20) + 0.004, 0.872, fz(0.45) - 0.022, fz(0.70) - 0.030, fz(0.95) - 0.030, lowpass(hsb[hk], 6, 9)[::6]]
o = np.argsort(bx); bx, bz = bx[o], bz[o]
belt = spl(bx, bz, 0.004)(grid)
belt = np.minimum(belt, zt_g - 0.012)
for e in (grid > hsx[hk].max(), grid < dkx.min()):                           # nose / tail tips: follow the top 2.5 cm down
    belt[e] = np.minimum(belt[e], zt_g[e] - 0.025)
out['ZBELT'] = belt.tolist(); raw['BELT'] = (np.r_[gx, stx, dkx, hsx], np.r_[gbot, stb, dkb, hsb])
# ---- Z5: DLO top over the door glass, A-pillar (midline of the pillar strip) ahead of it, else a share of (ZT - ZBELT)
apx, aplo = colstat('A_PILLAR_S', np.min); _, aphi = colstat('A_PILLAR_S', np.max, k=2)
ct = (gx2 > -0.66) & (gx2 < -0.18)
ax_ = (apx > -0.10) & (apx < 0.30)
zx = np.r_[gx2[ct], apx[ax_]]; zv = np.r_[gtop[ct], 0.5 * (aplo[ax_] + aphi[ax_])]
o = np.argsort(zx); zx, zv = zx[o], zv[o]
z5c = spl(zx, lowpass(zv, 3, 9), 0.006)(np.clip(grid, -0.66, 0.30))
share = 0.55; z5d = belt + share * (zt_g - belt)
w = np.clip(np.minimum((grid - (-0.66)) / 0.10, (0.36 - grid) / 0.10), 0, 1); w = w * w * (3 - 2 * w)
z5 = w * np.minimum(z5c, zt_g - 0.02) + (1 - w) * z5d
out['Z5'] = ndi.gaussian_filter1d(z5, 4).tolist(); raw['Z5'] = (zx, zv)
# ---- W (plan half-width, mirrors bridged)
xt = tc[:, 0]; hw = 0.5 * (tc[:, 2] - tc[:, 1]); raw['W'] = (xt, hw.copy())
hw = bridge(xt, hw, [(-0.10, 0.13)])
hw = lowpass(hw, 2, 5)
k_ = (xt > X_TAIL + .01) & (xt < X_NOSE - .01); s_ = spl(xt[k_], hw[k_], 0.002)
Wf = s_(grid)
for e in (grid > X_NOSE - 0.06, grid < X_TAIL + 0.06): Wf[e] = np.interp(grid[e], xt, hw)
out['W'] = np.maximum(Wf, 0.02).tolist()
# ---- Y5 (plan, left half)
TL = d['top_left']
def edge(k, hi=True, lo_x=-9, hi_x=9):
    a = np.array(TL[k]); a = a[(a[:, 0] > lo_x) & (a[:, 0] < hi_x)]
    xs = np.unique(np.round(a[:, 0], 3)); v = np.array([(a[np.abs(a[:, 0] - q) < 0.003, 2].max() if hi else a[np.abs(a[:, 0] - q) < 0.003, 1].min()) for q in xs])
    return xs, v
sgx, sgin = edge('SIDE_GLASS_T', hi=False, lo_x=-0.68, hi_x=-0.20)       # glass top (inner edge in plan)
wsx, wso = edge('WS_T', lo_x=0.02, hi_x=0.34)                            # windshield outer edge
hdx, hdo = edge('HOOD_T', lo_x=0.62, hi_x=1.62)                          # hood edge
rfx, rfo = edge('ROOF_T', lo_x=-1.24, hi_x=-0.70)                        # soft-top edge behind the glass
tkx, tko = edge('TRUNK_T', lo_x=-1.85, hi_x=-1.42)                       # trunk lid edge
yx = np.r_[tkx[::4], -1.33, rfx[::4], sgx[::4], wsx[::4], 0.42, 0.52, hdx[::4]]
yv = np.r_[tko[::4], 0.56, rfo[::4], sgin[::4], wso[::4], 0.68, 0.70, hdo[::4]]
o = np.argsort(yx); yx, yv = yx[o], yv[o]
y5 = spl(yx, lowpass(yv, 3, 5), 0.008)(grid)
y5[grid > 1.62] = np.interp(grid[grid > 1.62], [1.62, X_NOSE], [float(np.interp(1.62, hdx, hdo)), 0.05])
y5[grid < -1.85] = np.interp(grid[grid < -1.85], [X_TAIL, -1.85], [0.05, float(np.interp(-1.85, tkx, tko))])
out['Y5'] = np.clip(y5, 0.03, None).tolist(); raw['Y5'] = (yx, yv)
out['x_glass'] = [XG0, XG1]; out['x_softtop'] = [float(stx.min()), float(stx.max())]
out['x_ws'] = [float(wsx.min()), 0.40]
# ---- front / rear envelopes
for k in ('front', 'rear'):
    r = np.array([q for q in d[k + '_rows'] if q[1] is not None], float); z = r[:, 0]; h = 0.5 * (r[:, 2] - r[:, 1])
    h = bridge(z, h, [(0.79, 0.97)]); keep = z < z.max() - 0.004
    z, h = z[keep], h[keep]; raw[k] = (z, h.copy())
    h = ndi.gaussian_filter1d(ndi.median_filter(h, 5, mode='nearest'), 3, mode='nearest')
    out[k + '_env'] = dict(z=z.tolist(), hw=h.tolist())
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
plot(raw['ZT'][0], raw['ZT'][1], grid, out['ZT'], (40, 540, 1520, 180), (200, 80, 0), 'body top ZT(x): grey raw, blue fair')
plot(np.r_[raw['BELT'][0], raw['Z5'][0]], np.r_[raw['BELT'][1], raw['Z5'][1]], np.r_[grid, grid[::-1]], np.r_[out['ZBELT'], out['Z5'][::-1]], (40, 780, 1520, 160), (150, 0, 150), 'belt ZBELT + upper edge Z5: grey traced, purple fair')
plot(raw['Y5'][0], raw['Y5'][1], grid, out['Y5'], (40, 1000, 1520, 160), (0, 120, 200), 'Y5 plan edge of the upper surface (trunk / soft top / glass top / windshield / hood)')
cv2.imwrite('../renders/raw/fair_curves.png', img)
print('arches', json.dumps(arch)); print('X', X_NOSE, X_TAIL, 'glass', XG0, XG1, 'softtop', out['x_softtop'])
