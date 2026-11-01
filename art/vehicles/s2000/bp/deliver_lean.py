"""S2000 lean sheets (run after build_s2000_lean.py --render and bp/compare_lean.py with S2K_RD=lean/renders/raw/):
  lean/renders/s2000_lean_orthos_800.jpg     textured PSX orthos in the compare frames + blueprint silhouette (yellow) + IoU
  lean/renders/s2000_lean_front34_800.jpg / rear34 (+ _ref.png = 1280x896 review frame, RGB555 + Bayer, nearest x2)
  lean/renders/s2000_lean_raking_side_800.jpg   Cycles grazing light on grey clay (flank fairness)
  lean/renders/s2000_lean_vs_old_800.jpg     approved build clay | lean clay | lean textured (side + front 3/4)
  lean/renders/s2000_lean_texture_800.jpg    1024^2 baked body texture + 256^2 de-branded parts/wheel atlas"""
import sys, os, json, cv2, numpy as np
_CAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(_CAR), 'lean_common')); from deliver_kit import *
os.chdir(_CAR); R = 'lean/renders/raw'; O = 'lean/renders'
iou = json.load(open(f'{R}/iou.json')); cl = json.load(open('lean/bp/clearance.json'))
tri = open('lean/tri_count.txt').read(); TOT = int([l for l in tri.splitlines() if l.startswith('TOTAL')][0].split()[2])
GATE = dict(side=.95, top=.95, front=.92, rear=.92)
v = {}
for k in ('side', 'top', 'front', 'rear'):
    bm = cv2.imread(f'{R}/bpmask_{k}.png', 0) > 127; sil = cv2.imread(f'{R}/cmp_{k}.png', cv2.IMREAD_UNCHANGED)[..., 3] > 128
    v[k] = overlay(f'{R}/tex_cmp_{k}.png', bm, sil)
    lab(v[k], f'{k} IoU {iou[k]:.3f} (gate {GATE[k]:.2f})', s=0.45)
sd = fitw(v['side'], 800); tp = fitw(np.rot90(v['top']).copy(), 800); fr = fitw(hcat([v['front'], v['rear']], 20), 800)
foot = np.full((44, 800, 3), 255, np.uint8)
cv2.putText(foot, f'S2000 LEAN: {TOT} tris total (cap 2,000). Yellow = blueprint silhouette in the approved compare frames (4 mm/px).', (8, 17), 0, 0.40, (0, 0, 0), 1, cv2.LINE_AA)
cv2.putText(foot, f'gate {"PASS" if all(iou[k] >= GATE[k] for k in GATE) else "FAIL"}   clearance: {"all clear" if cl["all_clear"] else "INTERFERENCE"}, tightest {cl["tightest"]["gap_m"]*1000:.0f} mm', (8, 36), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
save(vcat([sd, tp, fr, foot]), f'{O}/s2000_lean_orthos_800.jpg')
for k in ('front34', 'rear34'):
    ref_frame(f'{R}/tex_{k}.png', f'{O}/s2000_lean_{k}_ref.png', f'{O}/s2000_lean_{k}_800.jpg', f'S2000 LEAN {TOT} tris - {k} - baked 1024 body tex + 256 atlas, fake shine, RGB555+Bayer')
rk = fitw(crop_bg(cv2.imread(f'{R}/clay_raking_side.png')), 800); lab(rk, 'S2000 lean clay - raking light along the flank (Cycles sun, 7 deg)', s=0.45)
save(rk, f'{O}/s2000_lean_raking_side_800.jpg')
OLD = 4354
r1 = [fith(crop_bg(cv2.imread(f'{R}/old_clay_side.png')), 150), fith(crop_bg(cv2.imread(f'{R}/clay_side.png')), 150),
      fith(crop_bg(psx(f'{R}/tex_cmp_side.png'), 6), 150, cv2.INTER_NEAREST)]
r2 = [fith(crop_bg(cv2.imread(f'{R}/old_clay_front34.png')), 260), fith(crop_bg(cv2.imread(f'{R}/clay_front34.png')), 260),
      fith(crop_bg(cv2.resize(psx(f'{R}/tex_front34.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)), 260, cv2.INTER_NEAREST)]
sheet = fitw(vcat([hcat(r1), hcat(r2)]), 800)
cw = 800 // 3
for i, t in enumerate((f'approved build: {OLD} tris', f'lean clay: {TOT} tris', f'lean textured: {TOT} tris')): lab(sheet, t, (8 + i * cw, 20), 0.45)
save(sheet, f'{O}/s2000_lean_vs_old_800.jpg')
bt = cv2.imread('lean/tex/s2000_body.png'); at = cv2.imread('lean/tex/s2000_atlas_lean.png')
tx = fitw(hcat([fith(bt, 560, cv2.INTER_NEAREST), vcat([cv2.resize(at, (240, 240), interpolation=cv2.INTER_NEAREST), np.full((312, 240, 3), 255, np.uint8)])]), 800, cv2.INTER_NEAREST)
lab(tx, 'body 1024^2 (baked from the approved vector-painted build + AO, RGB555+Bayer) | atlas 256^2 (brands removed)', s=0.38)
save(tx, f'{O}/s2000_lean_texture_800.jpg')
