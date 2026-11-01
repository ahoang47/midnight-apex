"""Blueprint curves for the WRX build (all from bp/curves.json written by bp/extract.py; no photos).
Every function is a smoothed version of a traced blueprint line in the car frame (x fwd, y left, z up, metres)."""
import json, os, numpy as np

class ndi:   # numpy stand-ins (Blender's Python has no scipy)
    @staticmethod
    def median_filter(a, k, mode='nearest'):
        a = np.asarray(a, float); h = k // 2; p = np.pad(a, h, mode='edge')
        return np.array([np.median(p[i:i + k]) for i in range(len(a))])
    @staticmethod
    def gaussian_filter1d(a, s, mode='nearest'):
        a = np.asarray(a, float); r = max(1, int(3 * s)); t = np.arange(-r, r + 1); w = np.exp(-0.5 * (t / s) ** 2); w /= w.sum()
        return np.convolve(np.pad(a, r, mode='edge'), w, 'valid')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(HERE, 'bp', 'curves.json')))
S = D['scale_m_per_px']
def _arr(k): return np.array(D[k], float)
def _fn(pts, med=5, gauss=1.0):
    p = np.array(sorted(pts, key=lambda t: t[0]), float)
    y = ndi.gaussian_filter1d(ndi.median_filter(p[:, 1], med, mode='nearest'), gauss, mode='nearest') if len(p) > 3 else p[:, 1]
    return lambda x: np.interp(x, p[:, 0], y)
WHEEL_X = sorted(D['side_wheel_x'], reverse=True)          # [front, rear] from the contact patches
AXF, AXR = float(WHEEL_X[0]), float(WHEEL_X[1])
X_NOSE = float(_arr('top_halfwidth')[:, 0].max()); X_TAIL = float(_arr('side_sil_top')[:, 0].min())
# pass 2: the curves that drive the loft are the FAIRED ones (bp/fair.py: bridged, low-passed, smoothing-spline refit)
F = json.load(open(os.path.join(HERE, 'bp', 'fair_curves.json'))); _G = np.array(F['grid'])
def _fair(k): y = np.array(F[k]); return lambda x: np.interp(x, _G, y)
SIL_TOP = _fair('SIL_TOP')                                     # side silhouette top (roof nub bridged)
SIL_BOT = _fn(D['side_sil_bot'], 5, 0.8)                       # raw (tyres included) -- only for the STI lip / checks
ZB_FAIR = _fair('ZB')                                          # body bottom: arches bridged, sill = one quadratic
BLUE_TOP = _fn(D['side_blue_top'], 7, 1.0)
W = _fair('W')                                                 # plan half-width (mirror zone bridged, spline-faired)
# arches: circle fits to the lowest paint per column around each wheel (bp/extract.py side_blue_bot)
def _arch(xc):
    bb = _arr('side_blue_bot'); m = (np.abs(bb[:, 0] - xc) < 0.42) & (bb[:, 1] > 0.32); p = bb[m]
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]; c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    return dict(xc=float(c[0]), zc=float(c[1]), r=float(np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)), x0=float(p[:, 0].min()), x1=float(p[:, 0].max()))
ARCH_F, ARCH_R = _arch(AXF), _arch(AXR)
# front / rear view outline envelopes: half-width per height, mirror rows (z .92-1.08) replaced by the line between
def _outline(k):
    e = F[k + '_env']; return np.array(e['z']), np.array(e['hw'])     # faired in bp/fair.py (mirror rows bridged)
FZ, FHW = _outline('front'); RZ, RHW = _outline('rear')
def ENV(z, x):
    """section envelope half-width at height z (front view at the nose, rear view at the tail, blended linearly between x +-1.6)."""
    t = np.clip((x + 1.6) / 3.2, 0, 1); z = np.maximum(z, 0.30)   # below .30 the views show tyres / the centre lip only
    return t * np.interp(z, FZ, FHW) + (1 - t) * np.interp(z, RZ, RHW)
WMAX = 0.5 * (FHW[(FZ > 0.3) & (FZ < 0.9)].max() + RHW[(RZ > 0.3) & (RZ < 0.9)].max())
ROOF_Z = float(min(FZ.max(), RZ.max()))
# side glass (DLO) per column, regions, windshield / rear glass
GLC = _arr('side_glass_cols')        # (x, ztop, zbot)
REG = D['side_glass_regions']
def regions():
    out = {}
    for g in REG:
        x0, x1 = g['x']; z0, z1 = g['z']
        if z0 > 1.40: continue                                 # roof nub
        c = 0.5 * (x0 + x1)
        k = 'ws' if c > 0.5 else ('front_door' if c > -0.3 else ('rear_door' if c > -1.05 else 'rear_glass'))
        out[k] = dict(x=(x0, x1), z=(z0, z1))
    return out
GLASS = regions()
