"""GR Corolla (2022) blueprint extraction from the Dimensions.com VECTOR drawing (bp/gr_dimensions.svg, 1000x675 units).
Line classes come straight from the Illustrator layers (see bp/line_classes.md):
  2D$AG-OUTLINE   (4 closed paths)  SIL   body silhouette per view (side, plan, front, rear) incl. tyres, mirrors, wing
  2D$AG-TRANSPORT (311 paths)       body/DLO/lamp/trim/wheel lines -> regions, classified below by seed points
  2D$AG-DETAILS   (41 paths)        lamp internals + surface creases (flare crease, character lines): texture only
  2D$AG-DIAGRAM   (ground lines)    z = 0 per view
  N-DIMENSIONS    (dimension text / arrows): ignored except as a scale cross-check
Scale: S = 4.406 m / side-silhouette length (SVG units).  Frames (car: x fwd, y left, z up, metres):
  side  nose RIGHT (car's right side drawn), x = (u - u_mid_wheels) * S, z = (259.76 - v) * S
  top   nose RIGHT, image top = car LEFT (+y), same u as the side view (nose/tail columns agree to 0.06 units)
  front car's left on the image RIGHT, rear car's left on the image LEFT, ground 259.76 / 541.198
Writes bp/curves.json, bp/regions.npz (region masks in car frame) and renders/raw/line_classes.png."""
import xml.etree.ElementTree as ET, json, numpy as np, cv2
from svgpathtools import parse_path
from scipy import ndimage as ndi
NS = '{http://www.w3.org/2000/svg}'
ROOT = ET.parse('gr_dimensions.svg').getroot()
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
    return ('side' if y0 < 300 else 'top') if x0 < 600 else ('front' if y0 < 300 else 'rear')
SV = {which(P): P for P in polys}
GZ = {'side': 259.76, 'top': None, 'front': 259.76, 'rear': 541.198}
Ls = SV['side'][:, 0].max() - SV['side'][:, 0].min(); S = 4.406 / Ls
# wheels: circle fits to the silhouette's tyre arcs (outline points within 0.20 m of the ground)
sp = SV['side']; zz = (GZ['side'] - sp[:, 1]) * S
W = []
for uc in (161.0, 505.0):                                     # tyre arcs below the sill (wheel u from the region table)
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
out = dict(source='Dimensions.com "Toyota GR Corolla Dimensions" SVG (vector)', S_m_per_unit=S, wheel_x=[float((w[0] - UM) * S) for w in W],
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
SEEDS = {   # class: [(view, u, v)]  (SVG units; region table from bp/regions.py, checked on renders/raw/line_classes.png)
 'DLO_GLASS':  [('side', 202.8, 110.4), ('side', 252.4, 108.4), ('side', 351.3, 113.6), ('side', 436.7, 112.0)],
 'DLO_PILLAR': [('side', 289.4, 110.1), ('side', 299.8, 111.8)],
 'ROOF_RAIL':  [('side', 263.3, 77.0)],
 'HATCH_GLASS_S': [('side', 112.4, 112.8), ('side', 131.9, 106.0)],
 'WING_S':     [('side', 140.6, 90.6)],
 'MIRROR_S':   [('side', 411.0, 128.6), ('side', 411.4, 137.7), ('side', 427.1, 127.6)],
 'HOOD_S':     [('side', 548.2, 151.1)],
 'HEADLAMP_S': [('side', 580.3, 171.0)],
 'TAIL_S':     [('side', 108.4, 144.1)],
 'SKIRT_S':    [('side', 328.7, 234.1)],
 'FENDER_VENT_S': [('side', 455.5, 173.6), ('side', 463.7, 172.6)],
 'SIDE_GLASS_T': [('top', 253.2, 382.6), ('top', 289.9, 381.8), ('top', 300.1, 381.3), ('top', 353.4, 380.0), ('top', 425.6, 374.3),
                  ('top', 253.2, 563.7), ('top', 289.9, 564.6), ('top', 300.1, 565.1), ('top', 353.4, 566.4), ('top', 425.6, 572.1)],
 'ROOF_T':     [('top', 270.1, 473.2)],
 'WS_T':       [('top', 435.6, 473.2), ('top', 447.4, 473.2)],
 'HOOD_T':     [('top', 547.6, 473.2)],
 'HOOD_VENT_T': [('top', 547.0, 435.4), ('top', 547.0, 511.0)],
 'WING_T':     [('top', 127.5, 473.2), ('top', 149.3, 473.2)],
 'MIRROR_T':   [('top', 412.6, 351.6), ('top', 412.6, 594.7)],
 'WS_F':       [('front', 810.6, 111.7), ('front', 810.6, 114.4)],
 'HOOD_F':     [('front', 810.6, 152.6)],
 'MIRROR_F':   [('front', 690.0, 129.2), ('front', 931.2, 129.2), ('front', 693.9, 139.9), ('front', 927.3, 139.9)],
 'HEADLAMP_F': [('front', 733.5, 174.1), ('front', 887.7, 174.2)],
 'GRILLE_F':   [('front', 755.0, 210.0), ('front', 810.6, 208.2)],
 'SIDE_INTAKE_F': [('front', 707.8, 216.2), ('front', 913.4, 216.2)],
 'LIP_F':      [('front', 810.6, 233.1)],
 'TYRE_F':     [('front', 708.9, 249.3), ('front', 912.3, 249.3)],
 'REAR_GLASS_R': [('rear', 810.6, 385.6), ('rear', 810.6, 390.8)],
 'WING_R':     [('rear', 810.6, 363.3)],
 'TAIL_R':     [('rear', 719.2, 427.7), ('rear', 902.0, 427.7), ('rear', 745.9, 423.4), ('rear', 875.3, 423.4)],
 'MIRROR_R':   [('rear', 689.9, 413.4), ('rear', 931.3, 413.4)],
 'DIFFUSER_R': [('rear', 738.6, 489.6), ('rear', 882.6, 489.6), ('rear', 810.6, 516.7)],
 'EXHAUST_R':  [('rear', 765.4, 501.2), ('rear', 855.7, 501.2), ('rear', 810.6, 507.8)],
 'TYRE_R':     [('rear', 708.7, 524.9), ('rear', 912.5, 524.9)],
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
out['side'] = {k: per_col(k, 'side') for k in ('DLO_GLASS', 'DLO_PILLAR', 'ROOF_RAIL', 'HATCH_GLASS_S', 'WING_S', 'HOOD_S', 'HEADLAMP_S', 'TAIL_S', 'SKIRT_S')}
out['side_poly'] = {k: outline_poly(k, 'side') for k in ('HEADLAMP_S', 'FENDER_VENT_S', 'TAIL_S', 'WING_S', 'HATCH_GLASS_S', 'MIRROR_S')}
out['top_left'] = {k: per_col(k, 'top', left=True) for k in ('SIDE_GLASS_T', 'ROOF_T', 'WS_T', 'HOOD_T', 'WING_T')}
out['top'] = {k: per_col(k, 'top') for k in ('SIDE_GLASS_T', 'ROOF_T', 'WS_T', 'HOOD_T', 'WING_T')}
out['top_poly'] = {k: outline_poly(k, 'top') for k in ('HOOD_VENT_T', 'MIRROR_T', 'WING_T')}
for k, cls in (('front', ('WS_F', 'HOOD_F', 'MIRROR_F', 'HEADLAMP_F', 'GRILLE_F', 'SIDE_INTAKE_F', 'LIP_F', 'TYRE_F')),
               ('rear', ('REAR_GLASS_R', 'WING_R', 'TAIL_R', 'MIRROR_R', 'DIFFUSER_R', 'EXHAUST_R', 'TYRE_R'))):
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
GROUP = {'DLO_GLASS': 'DLO', 'DLO_PILLAR': 'DLO', 'HATCH_GLASS_S': 'GLASS', 'SIDE_GLASS_T': 'DLO', 'WS_T': 'GLASS', 'WS_F': 'GLASS', 'REAR_GLASS_R': 'GLASS',
         'HEADLAMP_S': 'LAMP', 'TAIL_S': 'LAMP', 'HEADLAMP_F': 'LAMP', 'TAIL_R': 'LAMP',
         'WING_S': 'AERO', 'WING_T': 'AERO', 'WING_R': 'AERO', 'HOOD_VENT_T': 'AERO', 'FENDER_VENT_S': 'AERO', 'GRILLE_F': 'AERO', 'SIDE_INTAKE_F': 'AERO',
         'LIP_F': 'AERO', 'DIFFUSER_R': 'AERO', 'EXHAUST_R': 'AERO', 'MIRROR_S': 'TRIM', 'MIRROR_T': 'TRIM', 'MIRROR_F': 'TRIM', 'MIRROR_R': 'TRIM', 'SKIRT_S': 'TRIM'}
img = np.full(T.shape + (3,), 255, np.uint8)
for cl, g in GROUP.items(): img[REG[cl]] = (np.array(COL[g]) * 0.35 + 255 * 0.65).astype(np.uint8)
Dt = cv2.imread('raster_details.png', 0) > 0; Dm = cv2.imread('raster_dims.png', 0) > 0; Dg = cv2.imread('raster_diagram.png', 0) > 0
img[T] = (40, 40, 40); img[Dt] = (255, 120, 0); img[Dm] = (200, 200, 200); img[Dg] = (0, 170, 0); img[O] = (0, 0, 220)
y = 3800
for i, (t, c) in enumerate([('SIL outline layer', (0, 0, 220)), ('TRANSPORT body/panel lines', (40, 40, 40)), ('DETAILS creases/lamp internals (texture only)', (255, 120, 0)),
                            ('DIMENSIONS (ignored)', (200, 200, 200)), ('ground', (0, 170, 0))] + [(f'region: {g}', tuple(int(q * 0.35 + 255 * 0.65) for q in COL[g])) for g in COL]):
    x = 150 + (i % 5) * 1150; yy = y + (i // 5) * 120
    cv2.rectangle(img, (x, yy - 60), (x + 90, yy + 10), c, -1); cv2.rectangle(img, (x, yy - 60), (x + 90, yy + 10), (0, 0, 0), 3)
    cv2.putText(img, t, (x + 110, yy), 0, 2.0, (0, 0, 0), 4)
cv2.imwrite('../renders/raw/line_classes.png', img)
