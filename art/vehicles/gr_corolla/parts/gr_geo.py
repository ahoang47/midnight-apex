"""GR Corolla lean sections + stations (numpy only; runs inside Blender).  Car frame x fwd (0 = mid-wheelbase), y left,
z up, metres.  Every number comes from bp/fair_curves.json (the faired Dimensions.com vector blueprint).
ONE loft nose -> tail (hatchback: no separate cabin loft), 9-point half section:
  0 rocker bottom  1 rocker crease  2 lower door  3 widest (flare / door)      -> width = ENV(z) x W(x)/EMAX
  4 shoulder: belt line (DLO bottom) on the cabin, hood-fender shut line on the nose, hatch-glass bottom at the tail
  5 upper edge: side-glass top (cabin) / A-pillar (windshield) / hood edge / hatch edge   -> plan width Y5(x), height Z5(x)
  6 roof rail / hood shoulder   7 crown   8 centre = side-silhouette top ZT(x)
Arches: circle fits to the traced arch lines; the lower rows are lifted over them (lip wall + interior stations)."""
import json, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(HERE, 'bp', 'fair_curves.json'))); D = json.load(open(os.path.join(HERE, 'bp', 'curves.json')))
G_ = np.array(F['grid'])
def _f(k): y = np.array(F[k]); return lambda x: float(np.interp(x, G_, y))
ZB, ZT, ZBELT, Z5, W, Y5 = (_f(k) for k in ('ZB', 'ZT', 'ZBELT', 'Z5', 'W', 'Y5'))
X_NOSE, X_TAIL = F['x_nose'], F['x_tail']
AXF, AXR = F['wheel_x'][0], F['wheel_x'][1]
TIRE_R = round(F['tyre_r'], 4); TIRE_OD = 2 * TIRE_R; HUB_Z = TIRE_R
TIRE_W = 0.235                          # 235/40R18; the front/rear-view tyre faces read .218 between strokes (+ 1 stroke = .237)
TRACK_F = TRACK_R = 2 * 0.785           # tyre centre y .785 in the front and rear views (tyre faces y .676-.894, both views)
ARCH_F, ARCH_R = F['arch_f'], F['arch_r']
def _env(k): e = F[k + '_env']; return np.array(e['z']), np.array(e['hw'])
FZ, FHW = _env('front'); RZ, RHW = _env('rear')
def ENV(z, x):
    t = np.clip((x + 1.6) / 3.2, 0, 1); z = max(z, 0.30)
    return float(t * np.interp(z, FZ, FHW) + (1 - t) * np.interp(z, RZ, RHW))
EMAX = 0.5 * (FHW[(FZ > .3) & (FZ < .9)].max() + RHW[(RZ > .3) & (RZ < .9)].max())
def _ss(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
T_LOW = [0.0, 0.09, 0.40, 0.68]
NP = 9
NOSE_X0, TAIL_X0 = 1.95, -1.93
XWS, XHDR, XROOF = 1.10, 0.30, F['x_roof_end']      # windshield base (cowl), header, roof end (side view)
def arch_z(x, sag=0.0):
    z = -1.0
    for A in (ARCH_F, ARCH_R):
        d = abs(x - A['xc'])
        if d < A['r']: z = max(z, A['zc'] + np.sqrt(A['r'] ** 2 - d * d) + sag)
    return z
ARCH_SAG = 0.012                        # chords between sparse arch stations would sag into the tyre path
def section(x):
    zb, zt, z4, w = ZB(x), ZT(x), ZBELT(x), W(x) / EMAX
    z4 = min(z4, zt - 0.02); z4 = max(z4, zb + 0.10)
    pts = []
    for i, t in enumerate(T_LOW + [1.0]):
        z = zb + (z4 - zb) * t; y = w * ENV(z, x)
        if i == 0: y *= 0.94
        pts.append([y, z])
    # nose / tail rounding (plan width kept at the widest row, corners above / below pulled in towards the tip)
    tr = _ss((x - NOSE_X0) / (X_NOSE - NOSE_X0)) if x > 0 else _ss((TAIL_X0 - x) / (TAIL_X0 - X_TAIL))
    if tr > 0:
        ku, kl = (0.16, 0.10) if x > 0 else (0.10, 0.05)
        iw = int(np.argmax([p[0] for p in pts])); zw = pts[iw][1]
        for i, p in enumerate(pts):
            if i > iw: h = (p[1] - zw) / max(z4 - zw, 1e-3); p[0] *= 1 - ku * tr * h * h
            elif i < iw: h = (zw - p[1]) / max(zw - zb, 1e-3); p[0] *= 1 - kl * tr * h * h
    y4 = pts[4][0]
    z5 = min(max(Z5(x), z4 + 0.006), zt - 0.012); y5 = min(Y5(x), y4 - 0.008)
    y5 = max(y5, 0.25 * y4)
    z6 = z5 + 0.80 * (zt - z5); y6 = 0.80 * y5
    z7 = zt - 0.25 * (zt - z6); y7 = 0.45 * y6
    pts += [[y5, z5], [y6, z6], [y7, z7], [0.0, zt]]
    sec = np.array(pts)
    az = arch_z(x, ARCH_SAG)
    if az > 0:
        ymax = sec[:4, 0].max(); off = [0.0, 0.010, 0.028, 0.050]
        for i in range(4):
            if sec[i, 1] < az + off[i]: sec[i, 1] = az + off[i]; sec[i, 0] = ymax - (0.006 if i == 0 else 0.0)
        for i in range(1, NP): sec[i, 1] = max(sec[i, 1], sec[i - 1, 1] + 0.004)
    return sec
def _even(anchors, h):
    a = sorted(set(round(v, 4) for v in anchors)); out = []
    for p, q in zip(a[:-1], a[1:]):
        n = max(1, int(np.ceil((q - p) / h - 1e-6))); out += list(np.linspace(p, q, n + 1)[:-1])
    return out + [a[-1]]
H_FLANK, H_ARCH, H_END = 0.30, 0.18, 0.10
def stations():
    s = set()
    for A in (ARCH_F, ARCH_R):
        x0, x1 = A['xc'] - A['r'], A['xc'] + A['r']
        s |= {round(x0 - 0.012, 4), round(x1 + 0.012, 4)}
        s |= set(np.round(_even([x0 + 0.006, x1 - 0.006], H_ARCH), 4))
    af0, ar1 = ARCH_F['xc'] - ARCH_F['r'] - 0.012, ARCH_R['xc'] + ARCH_R['r'] + 0.012
    s |= set(np.round(_even([ar1, XHDR, af0], H_FLANK), 4))                          # doors: straight, faired, sparse
    s |= set(np.round(_even([ARCH_F['xc'] + ARCH_F['r'] + 0.012, X_NOSE - 0.004], H_END), 4))
    s |= set(np.round(_even([X_TAIL + 0.004, -1.93, ARCH_R['xc'] - ARCH_R['r'] - 0.012], H_END), 4))
    s |= {round(XROOF, 4), -1.86, -2.06}                    # roof end, hatch bottom, tail / nose face
    s = sorted([x for x in s if X_TAIL + 0.010 < x < X_NOSE - 0.010], reverse=True)
    out = []
    for x in s:
        if not out or out[-1] - x > 0.016: out.append(x)
    return np.array([X_NOSE - 0.002] + out + [X_TAIL + 0.002])
if __name__ == '__main__':
    X = stations(); print(len(X), 'stations, loft tris ~', 2 * (len(X) - 1) * (2 * NP - 2)); print(np.round(X, 3))
    for x in (2.0, 1.3, 0.8, 0.0, -1.0, -1.6, -2.0): print(x, np.round(section(x), 3).tolist())
