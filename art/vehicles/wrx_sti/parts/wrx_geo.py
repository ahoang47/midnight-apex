"""WRX (GD sedan, 2001-02) low-poly clay body: numpy only, no bpy.  Car frame x fwd (0 = mid-wheelbase), y left, z up.
Every line is a traced blueprint curve (parts/wrx_bp.py).  Two lofts, like the BRZ pass 4 / S2000:
  LOWER  stations along x; half-section = 11 points, sides at height z follow the front/rear-view outline envelope
         ENV(z) scaled to the station's plan half-width W(x); bottom ZB(x) (side silhouette, sills), top ZTB(x) =
         hood / fender line (side paint top, scoop + mirror are dark so excluded), beltline under the cabin, deck
         (side silhouette, the lip spoiler removed) behind it.  Wheel arches = circle fits to the arch paint edge.
  CABIN  greenhouse stations between the windshield base (x .93) and the rear-glass base (x -1.575); half-section =
         7 points: base on the belt, glass bottom, mid glass, glass top (side DLO per column), roof edge, crown, centre
         at the side silhouette top.  Widths = ENV(z) x plan taper k(x)."""
import numpy as np
import wrx_bp as B

AXF, AXR = B.AXF, B.AXR
WB = AXF - AXR
TIRE_OD, TIRE_W, RIM_D = 0.634, 0.225, 0.432          # STI 225/45R17 (WRX blueprint wheel reads ~.63 OD)
TRACK_F, TRACK_R = 1.485, 1.475                       # sheet: 1485/1490 front, 1475/1480 rear (smaller value)
HUB_Z = TIRE_OD / 2
XWS, XRG = 0.93, -1.575                              # windshield base (top view glass .924) / rear glass base (side 1.06)
NP = 11
W_CLAMP = 0.872     # top view reads .90 at the fender / hip flares, front & rear views .87 (sheet W 1730): front/rear win
def _pi(pts, x): p = np.array(pts, float); return np.interp(x, p[:, 0], p[:, 1])
# ---- traced key lines (numbers in keyline_table.md) ----
HOOD = [(0.93, .958), (1.0, .955), (1.15, .945), (1.3, .925), (1.5, .905)]          # side paint top, scoop excluded
BELT = [(-1.575, 1.060), (-1.25, 1.030), (-0.95, 1.000), (-0.6, .990), (-0.3, .975), (0.0, .956), (0.45, .947), (0.93, .958)]
DECK = [(-2.060, 1.025), (-2.0, 1.035), (-1.85, 1.060), (-1.70, 1.070), (-1.575, 1.060)]  # under the lip spoiler
def _ztb_raw(x):
    if x >= 1.5: return float(B.SIL_TOP(x))
    hood = float(np.polyval(B.F['hood_poly'], x))                                    # quadratic fit to the side paint top
    if x >= XWS: return hood if x < 1.45 else float(np.interp(x, [1.45, 1.5], [np.polyval(B.F['hood_poly'], 1.45), B.SIL_TOP(1.5)]))
    if x >= XRG: return float(_pi(BELT, x))
    if x >= -2.06: return float(_pi(DECK, x))
    if x >= -2.09: return float(np.interp(x, [-2.09, -2.06], [0.70, 1.02]))
    return float(min(B.SIL_TOP(x), 0.70))
# pass 2: hood -> belt -> deck is ONE faired line (gaussian 4 cm between the bumper drops), so the shoulder never kinks
_ZG = np.round(np.arange(B.X_TAIL, B.X_NOSE + 1e-9, 0.005), 4); _ZR = np.array([_ztb_raw(x) for x in _ZG])
_ZS = B.ndi.gaussian_filter1d(_ZR, 8); _zw = np.clip(np.minimum((_ZG + 2.04) / 0.04, (1.46 - _ZG) / 0.04), 0, 1)
_ZT = _zw * _ZS + (1 - _zw) * _ZR
def ZTB(x): return float(np.interp(x, _ZG, _ZT))
def ZB(x): return float(B.ZB_FAIR(x))
def _ss(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def crown_of(x):
    """hood / deck crown height, ramped (not stepped) at the windshield and rear-glass bases."""
    return 0.004 + 0.024 * _ss((x - XWS + 0.10) / 0.25) + 0.014 * _ss((XRG + 0.05 - x) / 0.2)
def soft_min(a, b, k=0.012): return 0.5 * (a + b - np.sqrt((a - b) ** 2 + k * k))   # C1 (smooth) clamp, no kink where W crosses the clamp
def GT(x):
    """greenhouse top = side silhouette top (roof nub at x -.15..-.3 clipped to the roof line)."""
    if x > 0.86: return float(np.interp(x, [0.86, XWS], [B.SIL_TOP(0.86), ZTB(XWS) + 0.012]))
    return float(min(B.SIL_TOP(x), 1.468))
K_PTS = [(XRG, .80), (-1.35, .87), (-1.1, .95), (-0.95, 1.0), (0.45, 1.0), (0.75, .93), (XWS, .86)]   # plan taper (top view)
def K(x): p = np.array(K_PTS); return float(np.interp(x, p[:, 0], p[:, 1]))
def arch_z(x):
    z = -1.0
    for A in (B.ARCH_F, B.ARCH_R):
        d = abs(x - A['xc'])
        if d < A['r'] and A['x0'] <= x <= A['x1']: z = max(z, A['zc'] + np.sqrt(A['r'] ** 2 - d * d))
    return z

T_SIDE = [0, .08, .25, .45, .65, .82, .93, 1.0]
NOSE_X0, TAIL_X0 = 1.78, -1.84
def lower_section(x):
    zb, zt = ZB(x), ZTB(x)
    crown = min(crown_of(x), 0.25 * (zt - zb))
    zsh = zt - crown; wn = soft_min(float(B.W(x)), W_CLAMP) / B.WMAX
    pts = []
    for i, t in enumerate(T_SIDE):
        z = zb + (zsh - zb) * t; y = wn * float(B.ENV(z, x))
        if i == 0: y *= 0.93
        pts.append([y, z])
    # pass 2 nose / tail rounding: plan half-width W(x) is kept at the widest point of the section (top-view
    # silhouette unchanged); above / below it the corner is pulled in progressively towards the nose / tail tip,
    # so the face reads as a rounded bumper instead of a box.  Front / rear views are set by the full-width stations.
    nose = x > 0; tr = _ss((x - NOSE_X0) / (B.X_NOSE - NOSE_X0)) if nose else _ss((TAIL_X0 - x) / (TAIL_X0 - B.X_TAIL))
    ku, kl = (0.26, 0.14) if nose else (0.10, 0.0)   # tail: light upper rounding only (lamps sit there; lower kept so the tail cap stays convex)
    if tr > 0:
        ys = [p[0] for p in pts]; iw = int(np.argmax(ys)); zw = pts[iw][1]
        for i, p in enumerate(pts):
            if i > iw: h = (p[1] - zw) / max(zsh - zw, 1e-3); p[0] *= 1 - ku * tr * h * h
            elif i < iw: h = (zw - p[1]) / max(zw - zb, 1e-3); p[0] *= 1 - kl * tr * h * h
    ysh = pts[-1][0]
    pts += [[0.62 * ysh, zt - 0.35 * crown], [0.30 * ysh, zt - 0.08 * crown], [0.0, zt]]
    sec = np.array(pts)
    az = arch_z(x)
    if az > 0:
        ymax = sec[:6, 0].max(); off = [0.0, 0.010, 0.025, 0.045, 0.07]
        for i in range(5):
            if sec[i, 1] < az + off[i]: sec[i, 1] = az + off[i]; sec[i, 0] = ymax - (0.006 if i == 0 else 0)
        for i in range(1, NP): sec[i, 1] = max(sec[i, 1], sec[i - 1, 1] + 0.004)
    return sec

def _dlo_lines():
    """pass 2 side DLO lines: door glass = the quadratic fits from bp/fair.py (top line fitted on the door-glass
    interiors only, so the rear-door sash corner no longer drags the roof-rail line down = the thick band above the
    rear door in pass 1); windshield-wrap and rear-glass-wrap bands traced; pillars bridged; 3 cm gaussian."""
    R = B.F['glass_regions']; xs = np.round(np.arange(XRG - 0.02, XWS + 0.02, 0.005), 4)
    top = np.full(len(xs), np.nan); bot = np.full(len(xs), np.nan)
    d0, d1 = R['rear_door']['x'][0], R['front_door']['x'][1]
    m = (xs >= d0) & (xs <= d1); top[m] = np.polyval(B.F['dlo_top_poly'], xs[m]); bot[m] = np.polyval(B.F['dlo_bot_poly'], xs[m])
    for k in ('ws', 'rear_glass'):
        bd = B.F[k + '_band']; bx = np.array(bd['x']); mm = (xs >= bx.min()) & (xs <= bx.max())
        top[mm] = np.interp(xs[mm], bx, bd['top']); bot[mm] = np.interp(xs[mm], bx, bd['bot'])
    ok = ~np.isnan(top); top = np.interp(xs, xs[ok], top[ok]); bot = np.interp(xs, xs[ok], bot[ok])
    return xs, B.ndi.gaussian_filter1d(bot, 6), B.ndi.gaussian_filter1d(top, 6)
_DX, _DB, _DT = _dlo_lines()
def dlo(x): return float(np.interp(x, _DX, _DB)), float(np.interp(x, _DX, _DT))
def cabin_section(x):
    zb = ZTB(x) - 0.004; zt = GT(x); k = K(x)
    g0, g1 = dlo(x)
    g0 = max(g0, zb + 0.008); g1 = min(g1, zt - 0.03)
    if g1 < g0 + 0.01: g0 = zb + 0.35 * (zt - zb); g1 = zb + 0.7 * (zt - zb)
    zr = g1 + 0.65 * (zt - g1)                          # roof rail: a fixed share of the glass-top -> crown height
    hz = [zb, g0, 0.5 * (g0 + g1), g1, zr]
    ys = [k * float(B.ENV(z, x)) for z in hz]
    ys[4] = ys[3] - 0.55 * max(0.0, ys[3] - k * float(B.ENV(min(zt - 0.012, B.ROOF_Z - 0.012), x)))
    ys[0] = min(ys[0], lower_section(x)[NP - 4, 0] - 0.004) if x < XWS else ys[0]
    for i in range(1, 5): ys[i] = min(ys[i], ys[i - 1] - 0.002)
    pts = list(zip(ys, hz)) + [(0.5 * ys[4], zt - 0.007), (0.0, zt)]
    return np.array(pts)

def _even(anchors, h):
    """evenly spaced stations between consecutive anchors (spacing <= h, equal within each span)."""
    a = sorted(set(round(v, 4) for v in anchors)); out = []
    for p, q in zip(a[:-1], a[1:]):
        n = max(1, int(np.ceil((q - p) / h - 1e-6))); out += list(np.linspace(p, q, n + 1)[:-1])
    return out + [a[-1]]
H_MID, H_END = 0.10, 0.055
def stations():
    """pass 2: ONE section topology (11 pts) at every station; along the flanks the stations are evenly spaced
    (<= 8.5 cm, equal inside each span between the arch edges / windshield / rear-glass anchors); the overhangs
    keep the denser face stations (lamps, bumper steps) but on an even 4.5 cm base."""
    mid = [-1.90, 1.90, XWS, XRG] + [v for A in (B.ARCH_F, B.ARCH_R) for v in (A['x0'] - 0.01, A['x0'] + 0.006, A['x1'] - 0.006, A['x1'] + 0.01)]
    s = set(np.round(_even(mid, H_MID), 4))
    s |= set(np.round(_even([1.90, B.X_NOSE - 0.004], H_END), 4)) | set(np.round(_even([B.X_TAIL + 0.004, -1.90], H_END), 4))
    s |= {-2.06, -2.075, -2.09}                                   # deck / bumper step under the spoiler
    for a, b_ in ((1.92, B.X_NOSE), (B.X_TAIL, -1.92)):            # face stations at fixed plan half-widths (nose / tail)
        xs = np.linspace(a, b_, 400); ws = np.array([soft_min(float(B.W(x)), W_CLAMP) for x in xs])
        for wl in (0.2, 0.34, 0.46, 0.56, 0.64, 0.71, 0.77, 0.82):
            j = np.argmin(np.abs(ws - wl)); s.add(round(float(xs[j]), 4))
    s = sorted([x for x in s if B.X_TAIL + 0.004 <= x <= B.X_NOSE - 0.004], reverse=True)
    out = []
    for x in s:
        if not out or out[-1] - x > (0.008 if abs(x) > 1.92 else 0.012): out.append(x)
    out = [x for x in out if B.X_TAIL + 0.010 < x < B.X_NOSE - 0.010]       # no 2 mm sliver next to the end stations
    return np.array([B.X_NOSE - 0.002] + out + [B.X_TAIL + 0.002])

CAB_ANCHORS = [XWS, 0.449, 0.295, -0.283, -0.318, -1.010, -1.073, XRG]   # pillar / glass-region edges (side view)
def cabin_stations():
    """cabin: its own even stations (<= 9 cm) between the pillar edges, so the glass boundaries are exact."""
    return np.array(sorted(set(np.round(_even(CAB_ANCHORS, 0.11), 4)), reverse=True))
