"""Trace the bugeye headlamp, fog lamp and corner-indicator OUTLINES from the blueprint front view (car-left side,
which the watermark does not cross) at sub-pixel precision: 8x bicubic crop -> lens-white threshold -> largest
component -> contour -> metres -> Fourier low-pass (outline only, no interior raster is copied).  The side view lamp
outline is traced the same way as a cross-check of the fore-aft extent.  Writes bp/lamp_outlines.json and
renders/clay_raw/lamp_trace.png (record)."""
import numpy as np, cv2, json
Z = np.load('bp/bp_classes.npz'); S = json.load(open('bp/curves.json'))['scale_m_per_px']
im = cv2.imread('ref/wrx_blueprint.jpg').astype(np.float32); UP = 8
X0f = int(Z['front_X0']); CC = float(Z['front_CC']); ZF = float(Z['front_ZF'])
CM = float(Z['side_CM']); ZFs = float(Z['side_ZF'])
def crop(view, a0, a1, z0, z1):
    if view == 'front': c0, c1 = CC + a0 / S + X0f, CC + a1 / S + X0f
    else: c0, c1 = CM - a1 / S, CM - a0 / S
    zf = ZF if view == 'front' else ZFs; r0, r1 = zf - z1 / S, zf - z0 / S
    c0, c1, r0, r1 = int(np.floor(c0)), int(np.ceil(c1)), int(np.floor(r0)), int(np.ceil(r1))
    sub = im[r0:r1, c0:c1]; big = cv2.resize(sub, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    def to_m(px, py):
        cc = c0 + (px + 0.5) / UP - 0.5; rr = r0 + (py + 0.5) / UP - 0.5
        a = (cc - X0f - CC) * S if view == 'front' else (CM - cc) * S
        return a, (zf - rr) * S
    return big, to_m
def lens_mask(big, thr):
    """lens + chrome bezel = the low-saturation (non-paint) region brighter than the dark outline stroke"""
    g = big.mean(2); sat = big.max(2) - big.min(2)
    m = ((g > thr) & (sat < 50)).astype(np.uint8)
    ff = np.pad(m, 1); h, w = ff.shape; cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    return m | (1 - ff[1:-1, 1:-1])                          # fill holes (watermark strokes, lens detail)
def outline(view, box, thr, harm, seed=None, n=256, hull=False, ell=False, opn=5):
    big, to_m = crop(view, *box); m = lens_mask(big, thr)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((opn, opn), np.uint8))
    k, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if seed is None: i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    else:
        sx, sy = seed; i = 1 + int(np.argmin([np.hypot(*(np.array(to_m(*c)) - (sx, sy))) + (0 if st[j + 1, 4] > 40 * UP else 9) for j, c in enumerate(cen[1:])]))
    cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0].astype(float)
    if hull: c = cv2.convexHull(c.astype(np.float32))[:, 0].astype(float)
    if ell:                                       # watermark-damaged round lens: ellipse fit to the hull
        (ex, ey), (ea, eb), ang = cv2.fitEllipse(c.astype(np.float32)); t_ = np.linspace(0, 2 * np.pi, 180, endpoint=False)
        ca, sa = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        c = np.c_[ex + ea / 2 * np.cos(t_) * ca - eb / 2 * np.sin(t_) * sa, ey + ea / 2 * np.cos(t_) * sa + eb / 2 * np.sin(t_) * ca]
    a, z = to_m(c[:, 0], c[:, 1]); P = np.c_[a, z]
    # outline grows by half the dark outline stroke (the stroke is the housing edge): dilate by 1 blueprint px / 2
    # arc-length resample + Fourier low-pass
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))]
    t = np.linspace(0, L[-1], n, endpoint=False); Q = np.c_[np.interp(t, L, np.r_[P[:, 0], P[0, 0]]), np.interp(t, L, np.r_[P[:, 1], P[0, 1]])]
    F = np.fft.fft(Q[:, 0] + 1j * Q[:, 1]); F[harm + 1:n - harm] = 0; q = np.fft.ifft(F)
    Q = np.c_[q.real, q.imag]
    if np.cross(Q[1] - Q[0], Q[2] - Q[1]) < 0 if False else (np.sum(Q[:, 0] * np.roll(Q[:, 1], -1) - np.roll(Q[:, 0], -1) * Q[:, 1]) < 0): Q = Q[::-1]   # CCW
    return Q, big, m, (lab == i)
out = {}; rec = []
JOBS = (('head', 'front', (0.42, 0.80, 0.54, 0.86), 120, 6, (0.60, 0.70), {}),
        ('indicator', 'front', (0.71, 0.84, 0.58, 0.78), 150, 4, (0.77, 0.67), {}),
        ('head_side', 'side', (1.80, 2.08, 0.54, 0.84), 150, 5, (1.95, 0.69), dict(opn=15, ell=True)),
        ('marker_side', 'side', (1.70, 1.90, 0.58, 0.76), 150, 4, (1.81, 0.67), {}))
for key, view, box, thr, harm, seed, kw in JOBS:
    Q, big, m, sel = outline(view, box, thr, harm, seed, **kw)
    out[key] = np.round(Q, 5).tolist()
    r = big.astype(np.uint8).copy(); r[sel] = (r[sel] * 0.6 + np.array([0, 160, 0]) * 0.4).astype(np.uint8)
    _, to_m_ = crop(view, *box); X_, Y_ = np.meshgrid(np.arange(r.shape[1]), np.arange(r.shape[0])); A_, Zm_ = to_m_(X_, Y_)
    cs_ = [np.argmin(np.abs(A_[0] - a)) for a in Q[:, 0]]; rs_ = [np.argmin(np.abs(Zm_[:, 0] - z)) for z in Q[:, 1]]
    cv2.polylines(r, [np.c_[cs_, rs_].astype(np.int32)], True, (0, 0, 255), 2, cv2.LINE_AA)
    rec.append((key, r))
    print(key, 'extent', Q.min(0).round(3), Q.max(0).round(3), 'area cm2', round(0.5 * abs(np.sum(Q[:, 0] * np.roll(Q[:, 1], -1) - np.roll(Q[:, 0], -1) * Q[:, 1])) * 1e4, 1))
# fog lens: the watermark crosses both fog lenses in the sheet, so its outline is an ellipse fitted to the blueprint
# lamp-class contour (bp_classes front_LL), grown by one blueprint pixel for the bezel stroke
L_ = Z['front_LL'].astype(np.uint8); cs, _ = cv2.findContours(L_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
best = None
for c in cs:
    if len(c) < 5: continue
    (ex, ey), (ea, eb), ang = cv2.fitEllipse(c.astype(np.float32)); y_ = (ex - CC) * S; z_ = (ZF - int(Z['front_Y0']) - ey) * S
    if abs(y_ - 0.627) < 0.05 and abs(z_ - 0.437) < 0.05: best = (y_, z_, (ea / 2 + 1) * S, (eb / 2 + 1) * S, ang)
y_, z_, ra, rb, ang = best; t_ = np.linspace(0, 2 * np.pi, 128, endpoint=False); ca, sa = np.cos(np.radians(ang)), np.sin(np.radians(ang))
out['fog'] = np.round(np.c_[y_ + ra * np.cos(t_) * ca - rb * np.sin(t_) * sa, z_ - (ra * np.cos(t_) * sa + rb * np.sin(t_) * ca)], 5).tolist()
out['fog'] = out['fog'][::-1] if np.sum(np.array(out['fog'])[:, 0] * np.roll(np.array(out['fog'])[:, 1], -1) - np.roll(np.array(out['fog'])[:, 0], -1) * np.array(out['fog'])[:, 1]) < 0 else out['fog']
F_ = np.array(out['fog']); print('fog extent', F_.min(0).round(3), F_.max(0).round(3))
json.dump(out, open('bp/lamp_outlines.json', 'w'))
H = max(r.shape[0] for _, r in rec); cv2.imwrite('renders/clay_raw/lamp_trace.png', np.hstack([cv2.copyMakeBorder(r, 0, H - r.shape[0], 0, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for _, r in rec]))
