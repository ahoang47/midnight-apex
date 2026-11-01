"""Lean-build sheets (run after build_wrx_lean.py --render, WRX_OUT=lean bp/bpcompare.py, WRX_OUT=lean deliver.py):
  lean/renders/wrx_lean_orthos_800.jpg        textured PSX orthos + blueprint silhouette (own frame) + IoU per view
  lean/renders/wrx_lean_front34_800.jpg / rear34   textured, PSX reference frame (640x448, RGB555 + Bayer, nearest)
  lean/renders/wrx_lean_front34_ref.png / rear34   same at 2x nearest (1280x896) = the review frame
  lean/renders/wrx_lean_vs_old_800.jpg        pass-2 clay (4,926 tris) | lean clay | lean textured, side + front 3/4
  lean/renders/wrx_lean_texture_800.jpg       the 1024^2 body texture + 256^2 wheel atlas"""
import cv2, numpy as np, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tex'))
from PIL import Image
from quant import rgb555_bayer
L = 'lean'; R = f'{L}/renders/clay_raw'; O = f'{L}/renders'
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']; Z = np.load('bp/bp_classes.npz')
iou = json.load(open(f'{L}/bp/iou_bpframe.json')); cl = json.load(open(f'{L}/bp/clearance.json'))
tri = open(f'{L}/tri_count.txt').read(); TOT = int([l for l in tri.splitlines() if l.startswith('TOTAL')][0].split()[2])
OLD = int([l for l in open('tri_count.txt').read().splitlines() if l.startswith('TOTAL as exported')][0].split('=')[1].split()[0])
def lab(i, t, org=(8, 22), s=0.55, col=(0, 0, 0)):
    (w, h), b = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, s, 1); x, y = org
    cv2.rectangle(i, (x - 2, y - h - 3), (x + w + 2, y + b), (255, 255, 255), -1); cv2.putText(i, t, org, cv2.FONT_HERSHEY_SIMPLEX, s, col, 1, cv2.LINE_AA)
def fitw(i, W, interp=cv2.INTER_AREA): return cv2.resize(i, (W, int(round(i.shape[0] * W / i.shape[1]))), interpolation=interp)
def fith(i, H, interp=cv2.INTER_AREA): return cv2.resize(i, (int(round(i.shape[1] * H / i.shape[0])), H), interpolation=interp)
def save(img, name): cv2.imwrite(f'{O}/{name}', img, [cv2.IMWRITE_JPEG_QUALITY, 92]); print('wrote', name, img.shape)
def psx(path):
    q = np.asarray(rgb555_bayer(Image.open(path).convert('RGB')))[..., ::-1].copy(); return q
def bp_in_render(view):
    M = Z[f'{view}_M']; X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    v_, u_ = np.mgrid[0:1000, 0:1000].astype(float)
    if view == 'side':
        x = (500 - u_) * 0.005; z = 0.65 + (500 - v_) * 0.005; c = float(Z['side_CM']) - X0 - x / S; r = float(Z['side_ZF']) - Y0 - z / S
    elif view == 'top':
        x = (500 - u_) * 0.005; y = (v_ - 500) * 0.005; c = float(Z['top_CM']) - X0 - x / S; r = float(Z['top_CR']) + y / S
    else:
        sg = 1 if view == 'front' else -1; y = sg * (u_ - 500) * 0.005; z = 0.65 + (500 - v_) * 0.005
        c = float(Z[f'{view}_CC']) + sg * y / S; r = float(Z[f'{view}_ZF']) - Y0 - z / S
    ri, ci = np.round(r).astype(int), np.round(c).astype(int); ok = (ri >= 0) & (ri < M.shape[0]) & (ci >= 0) & (ci < M.shape[1])
    out = np.zeros((1000, 1000), np.uint8); out[ok] = M[ri[ok], ci[ok]]; return out
def ortho(view):
    im = psx(f'{R}/tex_{view}.png'); bp = bp_in_render(view)
    e = cv2.morphologyEx(bp, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; im[e] = (0, 220, 255)
    ys, xs = np.nonzero(bp | (cv2.imread(f'{R}/sil_{view}.png', 0) > 127)); m = 20
    return im[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]
g = iou['gate']; f = iou['sti_mono']; n = iou['no_aero']
def tag(v): return f'{v}  IoU aero-masked (gate) {g[v]:.3f} | full STI {f[v]:.3f} | no aero parts {n[v]:.3f}  (min {iou["gate_thresholds"][v]:.2f})'
sd, tp, fr, rr = (ortho(k) for k in ('side', 'top', 'front', 'rear'))
sd = fitw(sd, 800); tp = fitw(tp, 800)
h = max(fr.shape[0], rr.shape[0]); pad = lambda i: cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
fr2 = fitw(np.hstack([pad(fr), np.full((h, 30, 3), 255, np.uint8), pad(rr)]), 800)
lab(sd, tag('side'), s=0.42); lab(tp, tag('top'), s=0.42)
lab(fr2, f'front {g["front"]:.3f} / {f["front"]:.3f} / {n["front"]:.3f}', s=0.42); lab(fr2, f'rear {g["rear"]:.3f} / {f["rear"]:.3f} / {n["rear"]:.3f}', (412, 22), s=0.42)
foot = np.full((44, 800, 3), 255, np.uint8)
cv2.putText(foot, f'WRX STI LEAN: {TOT} tris total (cap 2,000). Yellow = blueprint silhouette, own frame, no fitting. Texture PSX-quantised.', (8, 17), 0, 0.40, (0, 0, 0), 1, cv2.LINE_AA)
cv2.putText(foot, f'gate (aero region masked in blueprint AND model): {"PASS" if iou["gate_pass"] else "FAIL"}', (8, 36), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
save(np.vstack([sd, tp, fr2, foot]), 'wrx_lean_orthos_800.jpg')
for k in ('front34', 'rear34'):
    q = psx(f'{R}/tex_{k}.png'); ref = cv2.resize(q, (q.shape[1] * 2, q.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'{O}/wrx_lean_{k}_ref.png', ref)
    im = fitw(ref, 800); lab(im, f'WRX STI LEAN {TOT} tris - {k} - painted 1024 body tex + 256 wheel atlas, fake shine, RGB555+Bayer', s=0.42)
    save(im, f'wrx_lean_{k}_800.jpg')
# lean vs old: rows side / front34; cols pass-2 clay, lean clay, lean textured
def row(old, new, tex, H=230):
    a = fith(cv2.imread(old), H); b = fith(cv2.imread(new), H); c = fith(cv2.resize(psx(tex), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST), H)
    return [a, b, c]
def crop_side(p):
    im = cv2.imread(p); g_ = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); bg = np.median(g_[0]); ys, xs = np.nonzero(np.abs(g_.astype(int) - bg) > 10)
    return im[ys.min() - 10:ys.max() + 10, xs.min() - 10:xs.max() + 10]
tmp = '/tmp/_lean_cmp'; os.makedirs(tmp, exist_ok=True)
for nm, p in (('o', 'renders/clay_raw/clay_side.png'), ('n', f'{R}/clay_side.png'), ('t', f'{R}/tex_side.png')):
    cv2.imwrite(f'{tmp}/{nm}.png', crop_side(p))
r1 = [fith(cv2.imread(f'{tmp}/o.png'), 180), fith(cv2.imread(f'{tmp}/n.png'), 180), fith(cv2.resize(psx(f'{tmp}/t.png'), None, fx=1, fy=1), 180, cv2.INTER_NEAREST)]
r2 = [fith(cv2.imread('renders/clay_raw/clay_front34.png')[60:-60, 40:-40], 300), fith(cv2.imread(f'{R}/clay_front34.png')[60:-60, 40:-40], 300),
      fith(cv2.resize(psx(f'{R}/tex_front34.png'), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)[40:-40, 20:-20], 300, cv2.INTER_NEAREST)]
def hcat(ims):
    return np.hstack(sum([[i, np.full((i.shape[0], 8, 3), 255, np.uint8)] for i in ims], [])[:-1])
top = hcat(r1); bot = hcat(r2); Wd = max(top.shape[1], bot.shape[1])
top = fitw(top, Wd); bot = fitw(bot, Wd); sheet = fitw(np.vstack([top, np.full((8, Wd, 3), 255, np.uint8), bot]), 800)
cw = 800 // 3
for i, t in enumerate((f'pass-2 clay: {OLD} tris', f'lean clay: {TOT} tris', f'lean textured: {TOT} tris')): lab(sheet, t, (8 + i * cw, 20), 0.45)
save(sheet, 'wrx_lean_vs_old_800.jpg')
bt = cv2.imread(f'{L}/tex/wrx_body.png'); wt = cv2.imread(f'{L}/tex/wrx_wheel.png')
tx = np.hstack([fith(bt, 560, cv2.INTER_NEAREST), np.full((560, 8, 3), 255, np.uint8), cv2.resize(wt, (224, 224), interpolation=cv2.INTER_NEAREST).repeat(1, 0).__array__() if False else np.vstack([cv2.resize(wt, (224, 224), interpolation=cv2.INTER_NEAREST), np.full((336, 224, 3), 255, np.uint8)])])
tx = fitw(tx, 800, cv2.INTER_NEAREST); lab(tx, 'body 1024^2 (vector-painted lamps / grille / trim / panel lines, baked AO, RGB555+Bayer) | wheel atlas 256^2', s=0.40)
save(tx, 'wrx_lean_texture_800.jpg')
