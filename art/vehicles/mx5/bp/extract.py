"""Mazda MX-5 (ND, soft top) blueprint extraction from the Dimensions.com VECTOR drawing (bp/mx5_dimensions.svg, 1000x625 units).
Line classes come straight from the Illustrator layers (see bp/line_classes.md):
  2D$AG-OUTLINE   (4 closed paths)  SIL   body silhouette per view (side, plan, front, rear) incl. tyres, mirrors, wing
  2D$AG-TRANSPORT (311 paths)       body/DLO/lamp/trim/wheel lines -> regions, classified below by seed points
  2D$AG-DETAILS   (41 paths)        lamp internals + surface creases (flare crease, character lines): texture only
  2D$AG-DIAGRAM   (ground lines)    z = 0 per view
  N-DIMENSIONS    (dimension text / arrows): ignored except as a scale cross-check
Scale: S = 3.915 m (published ND length) / side-silhouette length (SVG units).  Frames (car: x fwd, y left, z up, metres):
  side  nose RIGHT (car's right side drawn), x = (u - u_mid_wheels) * S, z = (237.54 - v) * S
  top   nose RIGHT, image top = car LEFT (+y), same u as the side view (nose/tail columns agree to 0.06 units)
  front car's left on the image RIGHT, rear car's left on the image LEFT, ground 237.54 / 483.475
Writes bp/curves.json, bp/regions.npz (region masks in car frame) and renders/raw/line_classes.png."""
import xml.etree.ElementTree as ET, json, numpy as np, cv2
from svgpathtools import parse_path
from scipy import ndimage as ndi
NS = '{http://www.w3.org/2000/svg}'
ROOT = ET.parse('mx5_dimensions.svg').getroot()
def layer(i): return [g for g in ROOT.iter(NS + 'g') if g.get('id') == i][0]
# ------------------------------------------------------------------ silhouettes (vector, exact)
polys = []
for e in layer('_x32_D_x24_AG-OUTLINE').iter(NS + 'path'):
    p = parse_path(e.get('d')); pts = []
    for seg in p:
        n = max(4, int(seg.length() * 4))
        pts += [seg.point(t) for t in np.linspace(0, 1, n, endpoint=False)]
    polys.append(np.array([(c.real, c.imag) for c in pts]))
def which(P):
    x0, y0 = P.min(0)
    return ('side' if y0 < 280 else 'top') if x0 < 600 else ('front' if y0 < 280 else 'rear')
SV = {which(P): P for P in polys}
GZ = {'side': 237.54, 'top': None, 'front': 237.54, 'rear': 483.475}
Ls = SV['side'][:, 0].max() - SV['side'][:, 0].min(); S = 3.915 / Ls
# wheels: circle fits to the silhouette's tyre arcs (outline points within 0.20 m of the ground)
sp = SV['side']; zz = (GZ['side'] - sp[:, 1]) * S
W = []
for uc in (183.0, 508.0):                                     # tyre arcs below the sill (wheel u from the region table)
    p = sp[(zz < 0.24) & (np.abs(sp[:, 0] - uc) < 40)]; A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]; c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    W.append((c[0], c[1], np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)))
W.sort(key=lambda w: -w[0])                                   # [front (nose right = larger u), rear]
UM = 0.5 * (W[0][0] + W[1][0])
def side_xz(u, v): return (np.asarray(u) - UM) * S, (GZ['side'] - np.asarray(v)) * S
tp = SV['top']; VC = 0.5 * (tp[:, 1].min() + tp[:, 1].max())
def top_xy(u, v): return (np.asarray(u) - UM) * S, (VC - np.asarray(v)) * S
UC = {}
for k in ('front', 'rear'):
    P = SV[k]; UC[k] = 0.5 * (P[:, 0].min() + P[:, 0].max())
def fr_yz(k, u, v):
    sg = 1 if k == 'front' else -1                              # front: image right = car left (+y)
    return sg * (np.asarray(u) - UC[k]) * S, (GZ[k] - np.asarray(v)) * S
def to_car(k, P):
    if k == 'side': return np.c_[side_xz(P[:, 0], P[:, 1])]
    if k == 'top': return np.c_[top_xy(P[:, 0], P[:, 1])]
    return np.c_[fr_yz(k, P[:, 0], P[:, 1])]
out = dict(source='Dimensions.com "Mazda MX-5 Miata - Soft Top" SVG (vector)', S_m_per_unit=S, wheel_x=[float((w[0] - UM) * S) for w in W],
           wheel_z=[float((GZ['side'] - w[1]) * S) for w in W], tyre_r=[float(w[2] * S) for w in W])
out['sil'] = {k: to_car(k, P).tolist() for k, P in SV.items()}
# cross-checks against the published figures (mm)
fp, rp = to_car('front', SV['front']), to_car('rear', SV['rear'])
chk = dict(length=Ls * S * 1000, wheelbase=(W[0][0] - W[1][0]) * S * 1000,
           height_side=float(to_car('side', sp)[:, 1].max() * 1000), height_front=float(fp[:, 1].max() * 1000),
           width_mirrors_front=float(np.ptp(fp[:, 0]) * 1000), plan_length=float(np.ptp(SV['top'][:, 0]) * S * 1000))
# ------------------------------------------------------------------ TRANSPORT regions (classified by seed points)
SC = 6
T = cv2.imread('raster_transport.png', 0) > 0; O = cv2.imread('raster_outline.png', 0) > 0
LAB = ndi.label(~(T | O))[0]
SEEDS = {   # class: [(view, u, v)]  (SVG units; picked on bp/work_reg_*.png from regions_map.py, checked on renders/raw/line_classes.png)
 'DLO_GLASS':  [('side', 291.0, 99.0)],
 'A_PILLAR_S': [('side', 347.0, 93.0)],
 'SOFTTOP_S':  [('side', 235.0, 88.0)],
 'WS_S':       [('side', 370.0, 98.0)],
 'MIRROR_S':   [('side', 346.0, 114.0), ('side', 355.0, 126.0)],
 'HOOD_S':     [('side', 559.0, 138.0)],
 'DECK_S':     [('side', 121.0, 113.0)],
 'HEADLAMP_S': [('side', 574.0, 152.0)],
 'TAIL_S':     [('side', 98.0, 136.0), ('side', 82.0, 123.0), ('side', 84.0, 135.0)],
 'DOOR_S':     [('side', 326.0, 159.0)],
 'SIDE_GLASS_T': [('top', 293.0, 340.0), ('top', 293.0, 524.0)],
 'SHOULDER_T': [('top', 310.0, 320.0), ('top', 310.0, 544.0)],
 'ROOF_T':     [('top', 250.0, 432.0), ('top', 184.0, 432.0)],
 'WS_T':       [('top', 372.0, 432.0)],
 'HOOD_T':     [('top', 502.0, 432.0)],
 'TRUNK_T':    [('top', 116.0, 432.0)],
 'MIRROR_T':   [('top', 348.0, 308.0), ('top', 348.0, 556.0)],
 'HEADLAMP_T': [('top', 573.0, 345.0), ('top', 573.0, 520.0)],
 'WS_F':       [('front', 801.0, 95.0)],
 'HOOD_F':     [('front', 801.0, 132.0)],
 'MIRROR_F':   [('front', 680.0, 114.0), ('front', 922.0, 114.0)],
 'HEADLAMP_F': [('front', 715.0, 152.0), ('front', 887.0, 152.0)],
 'GRILLE_F':   [('front', 801.0, 172.0), ('front', 748.0, 173.0), ('front', 854.0, 173.0)] + [('front', u, v) for v in (184.0, 191.0) for u in (747.0, 765.0, 783.0, 801.0, 819.0, 837.0, 855.0)] + [('front', u, 199.0) for u in (753.0, 767.0, 784.0, 801.0, 818.0, 834.0, 848.5)],
 'SIDE_INTAKE_F': [('front', 707.0, 190.0), ('front', 895.0, 190.0)],
 'LIP_F':      [('front', 802.0, 211.0)],
 'TYRE_F':     [('front', 694.0, 222.0), ('front', 908.0, 222.0)],
 'REAR_GLASS_R': [('rear', 801.0, 339.0)],
 'ROOF_R':     [('rear', 801.0, 322.0)],
 'DECK_R':     [('rear', 801.0, 359.0)],
 'TAIL_R':     [('rear', 718.0, 384.0), ('rear', 739.0, 382.0), ('rear', 863.0, 382.0), ('rear', 884.0, 384.0)],
 'MIRROR_R':   [('rear', 680.0, 360.0), ('rear', 923.0, 360.0)],
 'PLATE_R':    [('rear', 801.0, 427.0)],
 'REFLECTOR_R': [('rear', 713.0, 437.0), ('rear', 889.0, 437.0)],
 'DIFFUSER_R': [('rear', 783.0, 444.0), ('rear', 776.0, 452.0), ('rear', 862.0, 446.0), ('rear', 868.0, 453.0)],
 'EXHAUST_R':  [('rear', 845.7, 450.2)],   # inner pipe only is a clean region; the outer pipe is offset from it in the build,
 'TYRE_R':     [('rear', 694.0, 464.0), ('rear', 908.0, 464.0)],
}
REG = {}
for cl, seeds in SEEDS.items():
    m = np.zeros_like(T)
    for _, u, v in seeds:
        l = LAB[int(round(v * SC)), int(round(u * SC))]
        if l == 0:                                             # thin strip: centroid on the stroke -> nearest free pixel
            yy, xx = np.mgrid[-12:13, -12:13]; o = np.argsort((yy ** 2 + xx ** 2).ravel())
            for q in o:
                l = LAB[int(round(v * SC)) + yy.ravel()[q], int(round(u * SC)) + xx.ravel()[q]]
                if l: break
        m |= LAB == l
    REG[cl] = ndi.binary_closing(m, np.ones((5, 5)))           # close over the 2.5-unit stroke between sibling regions
def pts_of(cl):
    rr, cc = np.nonzero(REG[cl]); return cc / SC, rr / SC          # SVG units
def per_col(cl, view, step=0.005, left=False):
    u, v = pts_of(cl); P = to_car(view, np.c_[u, v])
    if left: P = P[P[:, 1] > 0]                                   # plan: car-left half only (symmetric car)
    x = np.round(P[:, 0] / step) * step
    ux = np.unique(x); lo = np.array([P[x == q, 1].min() for q in ux]); hi = np.array([P[x == q, 1].max() for q in ux])
    return np.c_[ux, lo, hi].tolist()
def outline_poly(cl, view):
    m = REG[cl].astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    res = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) < 200: continue
        c = c[:, 0, :] / SC; res.append(to_car(view, c).tolist())
    return res
out['side'] = {k: per_col(k, 'side') for k in ('DLO_GLASS', 'A_PILLAR_S', 'SOFTTOP_S', 'WS_S', 'HOOD_S', 'DECK_S', 'HEADLAMP_S', 'TAIL_S', 'DOOR_S')}
out['side_poly'] = {k: outline_poly(k, 'side') for k in ('HEADLAMP_S', 'TAIL_S', 'MIRROR_S', 'DLO_GLASS', 'SOFTTOP_S', 'WS_S')}
out['top_left'] = {k: per_col(k, 'top', left=True) for k in ('SIDE_GLASS_T', 'SHOULDER_T', 'ROOF_T', 'WS_T', 'HOOD_T', 'TRUNK_T')}
out['top'] = {k: per_col(k, 'top') for k in ('SIDE_GLASS_T', 'ROOF_T', 'WS_T', 'HOOD_T', 'TRUNK_T')}
out['top_poly'] = {k: outline_poly(k, 'top') for k in ('MIRROR_T', 'HEADLAMP_T')}
for k, cls in (('front', ('WS_F', 'HOOD_F', 'MIRROR_F', 'HEADLAMP_F', 'GRILLE_F', 'SIDE_INTAKE_F', 'LIP_F', 'TYRE_F')),
               ('rear', ('REAR_GLASS_R', 'ROOF_R', 'DECK_R', 'TAIL_R', 'MIRROR_R', 'PLATE_R', 'REFLECTOR_R', 'DIFFUSER_R', 'EXHAUST_R', 'TYRE_R'))):
    out[k + '_poly'] = {c: outline_poly(c, k) for c in cls}
# per-height silhouette half-width (front / rear), per-x silhouette top / bottom (side), per-x half-width (top)
def raster_poly(P, res=0.002):
    lo = P.min(0) - 0.01; n = np.ceil((P.max(0) + 0.01 - lo) / res).astype(int)
    img = np.zeros((n[1], n[0]), np.uint8); q = ((P - lo) / res * 16).round().astype(np.int32)
    cv2.fillPoly(img, [q], 1, shift=4); return img > 0, lo, res
for k in ('front', 'rear'):
    M, lo, r = raster_poly(np.array(out['sil'][k])); rows = []
    for j in range(M.shape[0]):
        c = np.nonzero(M[j])[0]
        if len(c) == 0: continue
        z = lo[1] + (j + 0.5) * r
        lab, n = ndi.label(M[j]); ctr = int(round(-lo[0] / r)); L = lab[ctr]
        if L == 0: rows.append([z, None, None, (lo[0] + c.min() * r), lo[0] + (c.max() + 1) * r]); continue
        s = np.nonzero(lab == L)[0]; rows.append([z, lo[0] + s.min() * r, lo[0] + (s.max() + 1) * r, lo[0] + c.min() * r, lo[0] + (c.max() + 1) * r])
    out[k + '_rows'] = rows                          # z, centre-connected span (no mirrors / tyres when separate), full span
M, lo, r = raster_poly(np.array(out['sil']['side'])); cols = []
for i in range(M.shape[1]):
    j = np.nonzero(M[:, i])[0]
    if len(j): cols.append([lo[0] + (i + 0.5) * r, lo[1] + j.min() * r, lo[1] + (j.max() + 1) * r])
out['side_cols'] = cols                              # x, z bottom, z top
M, lo, r = raster_poly(np.array(out['sil']['top'])); cols = []
for i in range(M.shape[1]):
    j = np.nonzero(M[:, i])[0]
    if len(j): cols.append([lo[0] + (i + 0.5) * r, lo[1] + j.min() * r, lo[1] + (j.max() + 1) * r])
out['top_cols'] = cols                               # x, y min, y max (mirrors included)
# arch opening: march out from each hub along rays, first TRANSPORT ink beyond the tyre (tyre circle + 4 %)
arch = []
for (u0, v0, r0) in W:
    prof = []
    for a in np.radians(np.arange(-12, 193, 4)):
        d = np.array([np.cos(a), -np.sin(a)]); hit = None
        for t in np.arange(r0 * 1.03, r0 * 1.6, 0.1):
            u, v = u0 + d[0] * t, v0 + d[1] * t
            if T[int(round(v * SC)), int(round(u * SC))] or O[int(round(v * SC)), int(round(u * SC))]:
                hit = t; break
        if hit is not None: prof.append([float(np.degrees(a)), float(hit * S)])
    arch.append(prof)
out['arch_profile'] = arch                            # [deg from +x (fwd), radius m] per wheel (front, rear)
out['checks_mm'] = {k: round(float(v), 1) for k, v in chk.items()}
json.dump(out, open('curves.json', 'w'))
np.savez_compressed('regions.npz', **{k: v for k, v in REG.items()})
print(json.dumps(out['checks_mm']), 'S mm/unit', round(S * 1000, 4), 'wheels x', np.round(out['wheel_x'], 4), 'z', np.round(out['wheel_z'], 4), 'r', np.round(out['tyre_r'], 4))
# ------------------------------------------------------------------ line-class sheet
COL = {'DLO': (230, 160, 0), 'LAMP': (0, 60, 230), 'AERO': (200, 0, 200), 'TRIM': (60, 160, 60), 'GLASS': (230, 200, 0)}
GROUP = {'DLO_GLASS': 'DLO', 'A_PILLAR_S': 'TRIM', 'SIDE_GLASS_T': 'DLO', 'WS_S': 'GLASS', 'WS_T': 'GLASS', 'WS_F': 'GLASS', 'REAR_GLASS_R': 'GLASS',
         'HEADLAMP_S': 'LAMP', 'TAIL_S': 'LAMP', 'HEADLAMP_F': 'LAMP', 'TAIL_R': 'LAMP', 'HEADLAMP_T': 'LAMP',
         'SOFTTOP_S': 'AERO', 'ROOF_T': 'AERO', 'ROOF_R': 'AERO', 'GRILLE_F': 'AERO', 'SIDE_INTAKE_F': 'AERO',
         'LIP_F': 'AERO', 'DIFFUSER_R': 'AERO', 'EXHAUST_R': 'AERO', 'MIRROR_S': 'TRIM', 'MIRROR_T': 'TRIM', 'MIRROR_F': 'TRIM', 'MIRROR_R': 'TRIM',
         'PLATE_R': 'TRIM', 'REFLECTOR_R': 'LAMP'}   # 'AERO' colour = soft top + intakes/diffuser
img = np.full(T.shape + (3,), 255, np.uint8)
for cl, g in GROUP.items(): img[REG[cl]] = (np.array(COL[g]) * 0.35 + 255 * 0.65).astype(np.uint8)
Dt = cv2.imread('raster_details.png', 0) > 0; Dm = cv2.imread('raster_dims.png', 0) > 0; Dg = cv2.imread('raster_diagram.png', 0) > 0
img[T] = (40, 40, 40); img[Dt] = (255, 120, 0); img[Dm] = (200, 200, 200); img[Dg] = (0, 170, 0); img[O] = (0, 0, 220)
y = 3550
for i, (t, c) in enumerate([('SIL outline layer', (0, 0, 220)), ('TRANSPORT body/panel lines', (40, 40, 40)), ('DETAILS creases/lamp internals (texture only)', (255, 120, 0)),
                            ('DIMENSIONS (ignored)', (200, 200, 200)), ('ground', (0, 170, 0))] + [(f'region: {g}', tuple(int(q * 0.35 + 255 * 0.65) for q in COL[g])) for g in COL]):
    x = 150 + (i % 5) * 1150; yy = y + (i // 5) * 120
    cv2.rectangle(img, (x, yy - 60), (x + 90, yy + 10), c, -1); cv2.rectangle(img, (x, yy - 60), (x + 90, yy + 10), (0, 0, 0), 3)
    cv2.putText(img, t, (x + 110, yy), 0, 2.0, (0, 0, 0), 4)
cv2.imwrite('../renders/raw/line_classes.png', img)
