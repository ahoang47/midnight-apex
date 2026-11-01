"""WRX LEAN (2,000-tri cap) sections + stations.  Same faired blueprint curves as clay pass 2 (parts/wrx_geo.py:
ZB / ZTB / crown / soft clamp / DLO lines / arch circles), fewer points:
  LOWER  8-point half section: rocker bottom, rocker crease, lower door, upper door, shoulder (belt / fender top),
         hood|deck crown mid, centre.  Arch lift on the lower four.
  CABIN  6-point half section: belt, glass bottom, glass top, roof rail, roof mid, centre.
Stations: spent on silhouette -- arch circles (lip walls + interior), nose / tail profile and plan corners, pillar
edges -- and only every ~30 cm along the flat doors (faired curves, so no ripple)."""
import numpy as np
import wrx_bp as B, wrx_geo as G
XWS, XRG, AXF, AXR = G.XWS, G.XRG, G.AXF, G.AXR
T_SIDE = [0.0, 0.10, 0.42, 0.76, 1.0]
NP = len(T_SIDE) + 2
NOSE_X0, TAIL_X0 = G.NOSE_X0, G.TAIL_X0
def lower_section(x):
    zb, zt = G.ZB(x), G.ZTB(x)
    crown = min(G.crown_of(x), 0.25 * (zt - zb)); zsh = zt - crown
    wn = G.soft_min(float(B.W(x)), G.W_CLAMP) / B.WMAX
    pts = []
    for i, t in enumerate(T_SIDE):
        z = zb + (zsh - zb) * t; y = wn * float(B.ENV(z, x))
        if i == 0: y *= 0.93
        pts.append([y, z])
    nose = x > 0; tr = G._ss((x - NOSE_X0) / (B.X_NOSE - NOSE_X0)) if nose else G._ss((TAIL_X0 - x) / (TAIL_X0 - B.X_TAIL))
    ku, kl = (0.26, 0.14) if nose else (0.10, 0.0)
    if tr > 0:
        iw = int(np.argmax([p[0] for p in pts])); zw = pts[iw][1]
        for i, p in enumerate(pts):
            if i > iw: h = (p[1] - zw) / max(zsh - zw, 1e-3); p[0] *= 1 - ku * tr * h * h
            elif i < iw: h = (zw - p[1]) / max(zw - zb, 1e-3); p[0] *= 1 - kl * tr * h * h
    ysh = pts[-1][0]
    pts += [[0.55 * ysh, zt - 0.30 * crown], [0.0, zt]]
    sec = np.array(pts)
    az = G.arch_z(x)
    if az > 0: az += ARCH_SAG       # lean: chords between the sparser arch stations would sag into the tyre path
    if az > 0:
        ymax = sec[:4, 0].max(); off = [0.0, 0.012, 0.035, 0.06]
        for i in range(4):
            if sec[i, 1] < az + off[i]: sec[i, 1] = az + off[i]; sec[i, 0] = ymax - (0.006 if i == 0 else 0)
        for i in range(1, NP): sec[i, 1] = max(sec[i, 1], sec[i - 1, 1] + 0.004)
    return sec
def cabin_section(x):
    zb = G.ZTB(x) - 0.004; zt = G.GT(x); k = G.K(x)
    g0, g1 = G.dlo(x)
    g0 = max(g0, zb + 0.008); g1 = min(g1, zt - 0.03)
    if g1 < g0 + 0.01: g0 = zb + 0.35 * (zt - zb); g1 = zb + 0.7 * (zt - zb)
    zr = g1 + 0.65 * (zt - g1)
    hz = [zb, g0, g1, zr]
    ys = [k * float(B.ENV(z, x)) for z in hz]
    ys[3] = ys[2] - 0.55 * max(0.0, ys[2] - k * float(B.ENV(min(zt - 0.012, B.ROOF_Z - 0.012), x)))
    if x < XWS: ys[0] = min(ys[0], lower_section(x)[len(T_SIDE) - 1, 0] - 0.004)
    for i in range(1, 4): ys[i] = min(ys[i], ys[i - 1] - 0.002)
    return np.array(list(zip(ys, hz)) + [(0.5 * ys[3], zt - 0.007), (0.0, zt)])
ARCH_SAG = 0.015
H_FLANK, H_ARCH, H_END = 0.60, 0.11, 0.07     # flank 0.30 -> 0.60 (headlamp pocket budget): the doors are straight in plan, no ripple
def stations():
    AF, AR = B.ARCH_F, B.ARCH_R
    s = set()
    # arches: lip walls (outside / inside pairs) + even interior
    for A in (AF, AR):
        s |= {round(A['x0'] - 0.012, 4), round(A['x1'] + 0.012, 4)}
        s |= set(np.round(G._even([A['x0'] + 0.006, A['x1'] - 0.006], H_ARCH), 4))
    # flanks between the arches and the overhangs: coarse, faired
    s |= set(np.round(G._even([AR['x1'] + 0.012, XWS if XWS < AF['x0'] else AF['x0'] - 0.012, AF['x0'] - 0.012], H_FLANK), 4))
    s |= set(np.round(G._even([AF['x1'] + 0.012, 1.90], H_END * 2), 4)) | set(np.round(G._even([-1.90, AR['x0'] - 0.012], H_END * 2), 4))
    # nose / tail profile: even base + stations at fixed plan half-widths (plan corner) + deck / bumper step
    s |= set(np.round(G._even([1.90, B.X_NOSE - 0.004], H_END), 4)) | set(np.round(G._even([B.X_TAIL + 0.004, -1.90], H_END), 4))
    s |= {-2.06, -2.09}
    for a, b_ in ((1.92, B.X_NOSE), (B.X_TAIL, -1.92)):
        xs = np.linspace(a, b_, 400); ws = np.array([G.soft_min(float(B.W(x)), G.W_CLAMP) for x in xs])
        for wl in (0.30, 0.55, 0.72, 0.82):
            j = np.argmin(np.abs(ws - wl)); s.add(round(float(xs[j]), 4))
    s = sorted([x for x in s if B.X_TAIL + 0.010 < x < B.X_NOSE - 0.010], reverse=True)
    out = []
    for x in s:
        if not out or out[-1] - x > (0.012 if abs(x) > 1.92 else 0.010): out.append(x)
    return np.array([B.X_NOSE - 0.002] + out + [B.X_TAIL + 0.002])
CAB_ANCHORS = G.CAB_ANCHORS
def cabin_stations():
    return np.array(sorted(set(np.round(G._even(CAB_ANCHORS, 0.24), 4)), reverse=True))
if __name__ == '__main__':
    X = stations(); C = cabin_stations(); print(len(X), len(C), 'body tris ~', 2 * (len(X) - 1) * (2 * NP - 2), 'cabin ~', 2 * (len(C) - 1) * 10)
    print(np.round(X, 3))
