"""MX-5 detail-pass sheets (copy of gr_corolla/bp/deliver_detail.py; run from bp/ after `build_mx5_detail.py --render` and `MX5_OUT=detail python3 iou.py`):
  detail/renders/mx5_detail_front34_800.jpg / rear34   textured, PSX reference frame (640x448 -> RGB555 + Bayer)
  detail/renders/mx5_detail_front34_ref.png / rear34   same at 2x nearest (1280x896) = the review frame
  detail/renders/mx5_detail_lit_800.jpg                lamps on (glow FX visible), front 3/4 + rear 3/4
  detail/renders/mx5_detail_orthos_800.jpg             textured PSX orthos + blueprint OUTLINE silhouette edge
                                                               (yellow, own frame, no fitting) + IoU per view
  detail/renders/mx5_detail_texture_800.jpg            1024^2 body texture | 256^2 parts atlas | 128x64 glow
  detail/renders/mx5_detail_vs_clay_800.jpg            signed-off clay | detail clay | detail textured
  detail/renders/mx5_detail_clearance_800.jpg          9-pose clearance close-ups + table
  detail/renders/mx5_detail_closeups_800.jpg           wheel lettering / headlamp + grille / ring tail lamps / headlamp 3/4"""
import sys, os, json, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
VEH = next(p for p in (os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')), '/workspace/midnight-apex/art/vehicles') if os.path.isdir(os.path.join(p, 'lean_common')) and os.path.isdir(os.path.join(p, 'wrx_sti')))
sys.path.insert(0, os.path.join(VEH, 'lean_common'))
from deliver_kit import psx, lab, fitw, fith, save, hcat, vcat, crop_bg, ref_frame
import frames as F
from PIL import Image
D = os.path.join(HERE, '..', 'detail'); R = f'{D}/renders/tex_raw'; RC = f'{D}/renders/raw'; O = f'{D}/renders'
iou = json.load(open(f'{D}/bp/iou.json')); C = json.load(open(f'{D}/bp/clearance.json'))
txt = open(f'{D}/tri_count.txt').read(); import re
TOT = int(re.search(r'TOTAL\D*(\d+)', txt).group(1))
CLAY = int(re.search(r'TOTAL\D*(\d+)', open(os.path.join(HERE, '..', 'out', 'tri_count.txt')).read()).group(1))
NAME = 'MX-5 ND DETAIL'
# ---------------------------------------------------------------- 3/4 reference frames + lit pair
for k in ('front34', 'rear34'):
    ref_frame(f'{R}/tex_{k}.png', f'{O}/mx5_detail_{k}_ref.png', f'{O}/mx5_detail_{k}_800.jpg',
              f'{NAME} {TOT} tris - {k} - 1024 body + 256 parts atlas, fake shine, RGB555+Bayer, 2x nearest')
lit = hcat([cv2.resize(psx(f'{R}/lit_{k}.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST) for k in ('front34', 'rear34')])
lit = fitw(lit, 800, cv2.INTER_AREA); lab(lit, f'{NAME} - lamps on: emissive lamp art + {"MX5_FX_LampGlow"} sprites (hidden by default)', s=0.40)
save(lit, f'{O}/mx5_detail_lit_800.jpg')
# ---------------------------------------------------------------- orthos + blueprint silhouette (own frame)
AX = {'side': (0, 2), 'top': (0, 1), 'front': (1, 2), 'rear': (1, 2)}
def bp_mask(view, flip):
    P = F.to_car(view, F.SV[view]); A, Bv = P[:, 0], P[:, 1]
    if view == 'top': u = 500 + flip[0] * A / 0.005; v = 500 + flip[1] * Bv / 0.005
    else: u = 500 + flip[0] * A / 0.005; v = 500 - (Bv - 0.70) / 0.005
    m = np.zeros((1000, 1000), np.uint8); cv2.fillPoly(m, [np.round(np.c_[u, v] * 16).astype(np.int32)], 1, shift=4); return m
def ortho(view):
    raw = cv2.imread(f'{R}/tex_{view}.png'); g = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(int)
    car = np.abs(g - np.median(g[0])) > 6
    best = max(((s0, s1) for s0 in (1, -1) for s1 in ((1, -1) if view == 'top' else (1,))),
               key=lambda f: (bp_mask(view, f) & car).sum())                    # orientation only (sign), no scale/offset fitting
    m = bp_mask(view, best); im = psx(f'{R}/tex_{view}.png')
    e = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; im[e] = (0, 220, 255)
    ys, xs = np.nonzero(m | car); k = 20
    return im[max(ys.min() - k, 0):ys.max() + k, max(xs.min() - k, 0):xs.max() + k]
def tag(v): return f'{v.upper()}  IoU {iou[v]:.3f}  (gate {iou["gate_thresholds"][v]:.2f})'
sd, tp, fr, rr = (ortho(k) for k in ('side', 'top', 'front', 'rear'))
sd = fitw(sd, 800); tp = fitw(tp, 800); fr2 = fitw(hcat([fr, rr], 30), 800)
lab(sd, tag('side'), s=0.45); lab(tp, tag('top'), s=0.45); lab(fr2, tag('front'), s=0.45); lab(fr2, tag('rear'), (412, 22), s=0.45)
foot = np.full((44, 800, 3), 255, np.uint8)
cv2.putText(foot, f'{NAME}: {TOT} tris total (cap 2,000). Yellow = blueprint OUTLINE silhouette, own frame, no fitting.', (8, 17), 0, 0.40, (0, 0, 0), 1, cv2.LINE_AA)
cv2.putText(foot, f'IoU gate (side/top >= .95, front/rear >= .92): {"PASS" if iou["gate_pass"] else "FAIL"}   texture PSX-quantised', (8, 36), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
save(vcat([sd, tp, fr2, foot]), f'{O}/mx5_detail_orthos_800.jpg')
# ---------------------------------------------------------------- textures
bt = cv2.imread(f'{D}/tex/mx5_body.png'); pt = cv2.imread(f'{D}/tex/mx5_parts.png')
gl = cv2.imread(f'{D}/tex/mx5_glow.png', cv2.IMREAD_UNCHANGED)
if gl is not None and gl.shape[2] == 4: a = gl[..., 3:4] / 255.0; gl = (gl[..., :3] * a + 40 * (1 - a)).astype(np.uint8)
side_col = vcat([cv2.resize(pt, (256, 256), interpolation=cv2.INTER_NEAREST)] + ([cv2.resize(gl, (256, 128), interpolation=cv2.INTER_NEAREST)] if gl is not None else []))
tx = fitw(hcat([cv2.resize(bt, (560, 560), interpolation=cv2.INTER_NEAREST), side_col]), 800, cv2.INTER_NEAREST)
lab(tx, 'body 1024^2 (vector panel lines, painted lamps/grille/vents/badges, baked AO, RGB555+Bayer) | parts 256^2 | glow 128x64', s=0.38)
save(tx, f'{O}/mx5_detail_texture_800.jpg')
# ---------------------------------------------------------------- signed-off clay vs detail clay vs textured
OC = os.path.join(HERE, '..', 'out', 'renders', 'raw')
r1 = [fith(crop_bg(cv2.imread(f'{OC}/clay_front34.png')), 300), fith(crop_bg(cv2.imread(f'{RC}/clay_front34.png')), 300),
      fith(crop_bg(cv2.resize(psx(f'{R}/tex_front34.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)), 300, cv2.INTER_AREA)]
r2 = [fith(crop_bg(cv2.imread(f'{OC}/clay_rear34.png')), 300), fith(crop_bg(cv2.imread(f'{RC}/clay_rear34.png')), 300),
      fith(crop_bg(cv2.resize(psx(f'{R}/tex_rear34.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)), 300, cv2.INTER_AREA)]
sheet = fitw(vcat([hcat(r1), hcat(r2)]), 800); cw = 800 // 3
for i, t in enumerate((f'signed-off clay: {CLAY} tris', f'detail clay: {TOT} tris', f'detail textured: {TOT} tris')): lab(sheet, t, (8 + i * cw, 20), 0.42)
save(sheet, f'{O}/mx5_detail_vs_clay_800.jpg')
# ---------------------------------------------------------------- clearance
ims = [cv2.imread(f'{RC}/{n}.png') for n in ('clr_lockL_bump_34', 'clr_lockR_bump_34', 'clr_static_34', 'clr_lockL_bump_top_xray')]
g = vcat([hcat([fitw(ims[0], 800), fitw(ims[1], 800)], 0), hcat([fitw(ims[2], 800), fitw(ims[3], 800)], 0)], 0)
tab = np.full((300, 1600, 3), 255, np.uint8); y = 30; sp = C['spec']
cv2.putText(tab, f"9-pose clearance (tyre BVH vs body+liners): bump F {sp['bump_front']*1000:.0f} mm / R {sp['bump_rear']*1000:.0f} mm, droop {sp['droop']*1000:.0f} mm, lock +-{sp['lock_deg']:.0f} deg   ALL CLEAR: {C['all_clear']}   tightest {C['tightest']['gap_m']*1000:.1f} mm ({C['tightest']['corner']}, {C['tightest']['pose']})", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
for r in C['poses']:
    y += 28; s = '   '.join(f"{k} {c.get('min_gap_m', 0)*1000:5.1f} mm" + (f" OVERLAP {c['overlaps']}" if c['overlaps'] else '') for k, c in r['corners'].items())
    cv2.putText(tab, f"{r['pose']:<22s} {s}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1, cv2.LINE_AA)
save(fitw(vcat([g, tab], 0), 800), f'{O}/mx5_detail_clearance_800.jpg')
# ---------------------------------------------------------------- close-ups (PSX, nearest): headlamp / grille / diffuser / wheel
fo = psx(f'{R}/tex_front.png'); ro = psx(f'{R}/tex_rear.png'); f34 = psx(f'{R}/tex_front34.png'); wl = psx(f'{R}/tex_wheel_lockL.png')
def box(im, view, y0, y1, z0, z1):                      # crop an ortho by car coords (front/rear views: u = 500 +- y/.005)
    u = sorted([500 + y0 / 0.005, 500 + y1 / 0.005]); v = sorted([500 - (z0 - 0.7) / 0.005, 500 - (z1 - 0.7) / 0.005])
    return im[int(v[0]):int(v[1]), int(u[0]):int(u[1])]
def z(i, H=260): return fith(i, H, cv2.INTER_NEAREST)
so = psx(f'{R}/tex_side.png'); c1 = z(so[495:665, 175:365]); c2 = z(box(fo, 'front', -0.80, 0.80, 0.20, 0.72))
c3 = z(box(ro, 'rear', -0.85, 0.85, 0.18, 0.88)); c4 = z(f34[200:300, 140:300])
top_ = hcat([c1, c2]); bot_ = hcat([c3, c4]); sheet = fitw(vcat([fitw(top_, 1200), fitw(bot_, 1200)]), 800, cv2.INTER_AREA)
lab(sheet, 'wheel: made-up tyre lettering, 10-spoke | headlamp: pocket molding + painted projector ring; grille: planar pocket + slats', s=0.40)
lab(sheet, 'rear: painted ring tail lamps, black diffuser band, flat plate | 3/4: headlamp molding + lamp art', (8, sheet.shape[0] - 12), s=0.40)
save(sheet, f'{O}/mx5_detail_closeups_800.jpg')
