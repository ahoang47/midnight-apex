"""Delivery sheets (800 px jpgs) into renders/:
  mx5_clay_front34_800.jpg, mx5_clay_rear34_800.jpg   clay 3/4 views (Workbench, out/renders/raw)
  mx5_bp_overlay_800.jpg   side/top/front/rear: clay silhouette (blue fill, red edge) over the SVG line drawing
                                   (OUTLINE black, TRANSPORT magenta, DETAILS light), IoU per view in the labels
  mx5_line_classes_800.jpg region / line classification sheet from extract.py
  mx5_clearance_800.jpg     9-pose clearance close-ups + table
Run from bp/ after the build, iou.py and render_only.py."""
import xml.etree.ElementTree as ET, json, numpy as np, cv2
from svgpathtools import parse_path
R, OUT = '../out/renders/raw', '../renders'
NS = '{http://www.w3.org/2000/svg}'; ROOT = ET.parse('mx5_dimensions.svg').getroot(); SC = 6
d = json.load(open('curves.json')); S = d['S_m_per_unit']; iou = json.load(open('../out/bp/iou.json'))
# ---- frames, exactly as extract.py
polys = []
for e in [g for g in ROOT.iter(NS + 'g') if g.get('id') == '_x32_D_x24_AG-OUTLINE'][0].iter(NS + 'path'):
    p = parse_path(e.get('d')); pts = []
    for seg in p: pts += [seg.point(t) for t in np.linspace(0, 1, max(4, int(seg.length() * 4)), endpoint=False)]
    polys.append(np.array([(c.real, c.imag) for c in pts]))
def which(P):
    x0, y0 = P.min(0); return ('side' if y0 < 280 else 'top') if x0 < 600 else ('front' if y0 < 280 else 'rear')
SV = {which(P): P for P in polys}; GZ = {'side': 237.54, 'front': 237.54, 'rear': 483.475}
xs_min = np.array(d['sil']['side'])[:, 0].min(); UM = SV['side'][:, 0].min() - xs_min / S                  # u at x = 0
VC = 0.5 * (SV['top'][:, 1].min() + SV['top'][:, 1].max()); UC = {k: 0.5 * (SV[k][:, 0].min() + SV[k][:, 0].max()) for k in ('front', 'rear')}
def car_to_svg(view, A, B):
    if view == 'side': return A / S + UM, GZ['side'] - B / S
    if view == 'top': return A / S + UM, VC - B / S
    sg = 1 if view == 'front' else -1; return UC[view] + sg * A / S, GZ[view] - B / S
AX = {'side': (0, 2), 'top': (0, 1), 'front': (1, 2), 'rear': (1, 2)}
T = np.load('../out/bp/tris_carframe.npy').reshape(-1, 3, 3)
lay = {k: cv2.imread(f'raster_{k}.png', 0) > 0 for k in ('outline', 'transport', 'details')}
H, W = lay['outline'].shape
panels = {}
for v in ('side', 'top', 'front', 'rear'):
    a, b = AX[v]; m = np.zeros((H, W), np.uint8)
    for t in T:
        u, w = car_to_svg(v, t[:, a], t[:, b]); cv2.fillPoly(m, [np.round(np.c_[u, w] * SC * 16).astype(np.int32)], 1, shift=4)
    P = SV[v]; x0, y0 = (P.min(0) * SC - 40).astype(int); x1, y1 = (P.max(0) * SC + 40).astype(int)
    sl = (slice(max(y0, 0), y1), slice(max(x0, 0), x1))
    im = np.full((y1 - max(y0, 0), x1 - max(x0, 0), 3), 255, np.uint8); mm = m[sl] > 0
    im[mm] = (235, 205, 170)                                                     # clay silhouette fill (light blue)
    im[lay['details'][sl]] = (215, 170, 235); im[lay['transport'][sl]] = (200, 60, 230); im[lay['outline'][sl]] = (20, 20, 20)
    edge = cv2.morphologyEx(mm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    im[edge] = (0, 0, 230)
    panels[v] = im
def fitw(a, w): return cv2.resize(a, (w, round(a.shape[0] * w / a.shape[1])), interpolation=cv2.INTER_AREA)
def lab(im, t, s=0.5): cv2.putText(im, t, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, s, (30, 30, 30), 1, cv2.LINE_AA); return im
Wd = 1600
side = lab(fitw(panels['side'], Wd), f"SIDE (car right, nose right)  IoU {iou['side']:.3f}  gate .95", 0.7)
top = lab(fitw(panels['top'], Wd), f"TOP (nose right, car left up)  IoU {iou['top']:.3f}  gate .95", 0.7)
fr = lab(fitw(panels['front'], Wd // 2 - 10), f"FRONT  IoU {iou['front']:.3f}  gate .92", 0.7)
re = lab(fitw(panels['rear'], Wd // 2 - 10), f"REAR  IoU {iou['rear']:.3f}  gate .92", 0.7)
h = max(fr.shape[0], re.shape[0]); row = np.full((h, Wd, 3), 255, np.uint8); row[:fr.shape[0], :fr.shape[1]] = fr; row[:re.shape[0], Wd - re.shape[1]:] = re
head = np.full((60, Wd, 3), 255, np.uint8)
cv2.putText(head, 'MX-5 (ND) clay vs Dimensions.com SVG: black = OUTLINE, magenta = TRANSPORT lines, pink = DETAILS, blue = clay silhouette, red = clay edge', (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30, 30, 30), 1, cv2.LINE_AA)
sheet = np.vstack([head, side, top, row])
cv2.imwrite(f'{OUT}/mx5_bp_overlay_full.png', sheet)
def save800(im, name): cv2.imwrite(f'{OUT}/{name}', fitw(im, 800), [cv2.IMWRITE_JPEG_QUALITY, 92])
save800(sheet, 'mx5_bp_overlay_800.jpg')
save800(cv2.imread(f'{R}/clay_front34.png'), 'mx5_clay_front34_800.jpg')
save800(cv2.imread(f'{R}/clay_rear34.png'), 'mx5_clay_rear34_800.jpg')
save800(cv2.imread('../renders/raw/line_classes.png'), 'mx5_line_classes_800.jpg')
# ---- clearance sheet
C = json.load(open('../out/bp/clearance.json'))
ims = [cv2.imread(f'{R}/{n}.png') for n in ('clr_lockL_bump_34', 'clr_lockR_bump_34', 'clr_static_34', 'clr_lockL_bump_top_xray')]
g = np.vstack([np.hstack([fitw(ims[0], 800), fitw(ims[1], 800)]), np.hstack([fitw(ims[2], 800), fitw(ims[3], 800)])])
tab = np.full((300, 1600, 3), 255, np.uint8); y = 30
sp = C['spec']; cv2.putText(tab, f"9-pose clearance (tyre BVH vs body+liners): bump F {sp['bump_front']*1000:.0f} mm / R {sp['bump_rear']*1000:.0f} mm, droop {sp['droop']*1000:.0f} mm, lock +-{sp['lock_deg']:.0f} deg   ALL CLEAR: {C['all_clear']}   tightest {C['tightest']['gap_m']*1000:.1f} mm ({C['tightest']['corner']}, {C['tightest']['pose']})", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
for r in C['poses']:
    y += 28; s = '   '.join(f"{k} {c.get('min_gap_m', 0)*1000:5.1f} mm" + (f" OVERLAP {c['overlaps']}" if c['overlaps'] else '') for k, c in r['corners'].items())
    cv2.putText(tab, f"{r['pose']:<22s} {s}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1, cv2.LINE_AA)
save800(np.vstack([g, tab]), 'mx5_clearance_800.jpg')
print('ok', sheet.shape)
