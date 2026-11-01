"""BRZ lean sheets (run after build_brz_lean.py --render and the lean IoU:
  BRZ_TRIS=lean/bp/tris_carframe.npy BRZ_IOU=lean/bp/iou_bpframe.json BRZ_OD=lean/renders/raw python3 bp/bpcompare_lean.py)
  lean/renders/brz_lean_orthos_800.jpg     textured PSX orthos + blueprint silhouette edge (yellow) + IoU
  lean/renders/brz_lean_front34_800.jpg / rear34 (+ _ref.png = 1280x896 review frame, RGB555 + Bayer, nearest x2)
  lean/renders/brz_lean_raking_side_800.jpg   Cycles grazing light on grey clay (flank fairness)
  lean/renders/brz_lean_vs_old_800.jpg     approved pass-4 clay | lean clay | lean textured (side + front 3/4)
  lean/renders/brz_lean_texture_800.jpg    1024^2 baked body texture + 256^2 parts/wheel atlas"""
import sys, os, json, cv2, numpy as np
_CAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(_CAR), 'lean_common')); from deliver_kit import *
os.chdir(_CAR); R = 'lean/renders/raw'; O = 'lean/renders'
iou = json.load(open('lean/bp/iou_bpframe.json')); cl = json.load(open('lean/bp/clearance.json'))
tri = open('lean/tri_count.txt').read(); TOT = int([l for l in tri.splitlines() if l.startswith('TOTAL')][0].split()[2])
GATE = dict(side=.95, top=.95, front=.92, rear=.92)
Z = np.load('bp/bp_classes.npz'); S = json.load(open('bp/curves.json'))['scale_m_per_px']
def bp_in_render(view, flip=False):
    M = Z[f'{view}_M']; X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    v_, u_ = np.mgrid[0:1000, 0:1000].astype(float)
    if view == 'side':
        x = (500 - u_) * 0.005; z = 0.65 + (500 - v_) * 0.005; c = float(Z['side_CM']) - X0 - x / S; r = float(Z['side_ZF']) - Y0 - z / S
    elif view == 'top':
        x = (500 - u_) * 0.005; y = (v_ - 500) * 0.005 * (-1 if flip else 1); c = float(Z['top_CM']) - X0 - x / S; r = float(Z['top_CR']) - y / S
    else:
        sg = 1 if view == 'front' else -1; y = sg * (u_ - 500) * 0.005; z = 0.65 + (500 - v_) * 0.005
        c = float(Z[f'{view}_CC']) + sg * y / S; r = float(Z[f'{view}_ZF']) - Y0 - z / S
    ri, ci = np.round(r).astype(int), np.round(c).astype(int); ok = (ri >= 0) & (ri < M.shape[0]) & (ci >= 0) & (ci < M.shape[1])
    out = np.zeros((1000, 1000), np.uint8); out[ok] = M[ri[ok], ci[ok]]; return out
def ortho(view):
    sil = cv2.imread(f'{R}/sil_{view}.png', 0) > 127
    cands = [bp_in_render(view, f) for f in (False, True)] + [bp_in_render(view)[:, ::-1].copy()]
    sc = [((c > 0) & sil).sum() / max(((c > 0) | sil).sum(), 1) for c in cands]; bp = cands[int(np.argmax(sc))]
    print(view, 'render-frame mask agreement', [round(s, 3) for s in sc])
    im = psx(f'{R}/tex_{view}.png')
    e = cv2.morphologyEx(bp, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; im[e] = (0, 220, 255)
    ys, xs = np.nonzero((bp > 0) | sil); m = 20
    return im[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]
sd, tp, fr, rr = (ortho(k) for k in ('side', 'top', 'front', 'rear'))
sd = fitw(sd, 800); tp = fitw(tp, 800)
h = max(fr.shape[0], rr.shape[0]); pad = lambda i: cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
fr2 = fitw(np.hstack([pad(fr), np.full((h, 30, 3), 255, np.uint8), pad(rr)]), 800)
for im, k in ((sd, 'side'), (tp, 'top')): lab(im, f'{k} IoU {iou[k]:.3f} (gate {GATE[k]:.2f})', s=0.45)
lab(fr2, f'front IoU {iou["front"]:.3f} (gate .92)', s=0.45); lab(fr2, f'rear IoU {iou["rear"]:.3f} (gate .92)', (412, 22), s=0.45)
foot = np.full((44, 800, 3), 255, np.uint8)
cv2.putText(foot, f'BRZ LEAN: {TOT} tris total (cap 2,000). Yellow = blueprint silhouette edge; IoU in the blueprint frame (bpcompare).', (8, 17), 0, 0.40, (0, 0, 0), 1, cv2.LINE_AA)
cv2.putText(foot, f'gate {"PASS" if all(iou[k] >= GATE[k] for k in GATE) else "FAIL"}   clearance: {"all clear" if cl["all_clear"] else "INTERFERENCE"}, tightest {cl["tightest"]["gap_m"]*1000:.1f} mm', (8, 36), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
save(vcat([sd, tp, fr2, foot]), f'{O}/brz_lean_orthos_800.jpg')
for k in ('front34', 'rear34'):
    ref_frame(f'{R}/tex_{k}.png', f'{O}/brz_lean_{k}_ref.png', f'{O}/brz_lean_{k}_800.jpg', f'BRZ LEAN {TOT} tris - {k} - baked 1024 body tex + 256 atlas, fake shine, RGB555+Bayer')
rk = fitw(crop_bg(cv2.imread(f'{R}/clay_raking_side.png')), 800); lab(rk, 'BRZ lean clay - raking light along the flank (Cycles sun, 7 deg)', s=0.45)
save(rk, f'{O}/brz_lean_raking_side_800.jpg')
OLD = int(os.environ.get('BRZ_OLD_TRIS', '0'))
r1 = [fith(crop_bg(cv2.imread(f'{R}/old_clay_side.png')), 150), fith(crop_bg(cv2.imread(f'{R}/clay_side.png')), 150),
      fith(crop_bg(psx(f'{R}/tex_side.png'), 6), 150, cv2.INTER_NEAREST)]
r2 = [fith(crop_bg(cv2.imread(f'{R}/old_clay_front34.png')), 260), fith(crop_bg(cv2.imread(f'{R}/clay_front34.png')), 260),
      fith(crop_bg(cv2.resize(psx(f'{R}/tex_front34.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)), 260, cv2.INTER_NEAREST)]
sheet = fitw(vcat([hcat(r1), hcat(r2)]), 800)
cw = 800 // 3
for i, t in enumerate((f'approved pass 4: {OLD} tris', f'lean clay: {TOT} tris', f'lean textured: {TOT} tris')): lab(sheet, t, (8 + i * cw, 20), 0.45)
save(sheet, f'{O}/brz_lean_vs_old_800.jpg')
bt = cv2.imread('lean/tex/brz_body.png'); at = cv2.imread('lean/tex/brz_wheel_atlas.png')
tx = fitw(hcat([fith(bt, 560, cv2.INTER_NEAREST), vcat([cv2.resize(at, (240, 240), interpolation=cv2.INTER_NEAREST), np.full((312, 240, 3), 255, np.uint8)])]), 800, cv2.INTER_NEAREST)
lab(tx, 'body 1024^2 (baked from the approved pass-4 vector-painted build + AO, RGB555+Bayer) | atlas 256^2 (made-up marks)', s=0.38)
save(tx, f'{O}/brz_lean_texture_800.jpg')
