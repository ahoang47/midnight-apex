"""Detail-pass sheets: blueprint compare (blueprint view | textured ortho render | IoU overlay, gate scores) and
photo-vs-render (surface character only; photo framing is approximate).  python3 bp/detail_sheets.py TAG"""
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
TAG = sys.argv[1] if len(sys.argv) > 1 else 'detail'
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18); f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
iou = json.load(open('bp/iou_bpframe.json')); gate = dict(side=.95, top=.95, front=.92, rear=.92)
z = np.load('bp/bp_classes.npz'); full = Image.open('ref/brz_blueprint.jpg').convert('RGB')
def crop(v):
    X0, Y0 = int(z[f'{v}_X0']), int(z[f'{v}_Y0']); h, w = z[f'{v}_M'].shape; return full.crop((X0, Y0, X0 + w, Y0 + h))
def fit(im, W, H):
    im = im.copy(); im.thumbnail((W, H), Image.LANCZOS); c = Image.new('RGB', (W, H), (255, 255, 255)); c.paste(im, ((W - im.width) // 2, (H - im.height) // 2)); return c
def autocrop(im, thr=40):
    a = np.asarray(im.convert('RGB')).astype(int); brd = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    b = np.median(brd, 0); m = np.abs(a - b).sum(-1) > thr
    ys, xs = np.where(m); return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)) if len(xs) else im
SCALE = json.load(open('bp/curves.json'))['scale_m_per_px']
ORTHO = {'side': 4.75, 'front': 2.25, 'rear': 2.25}       # render_brz_detail.py ortho scales over 1280 px
def same_scale(bp_im, r_im, v, W, H):
    """bring the render to the blueprint's metres-per-pixel, then fit both with one common factor"""
    k = (ORTHO[v] / 1280) / SCALE; r_im = r_im.resize((max(1, round(r_im.width * k)), max(1, round(r_im.height * k))), Image.LANCZOS)
    f = min(W / max(bp_im.width, r_im.width), H / max(bp_im.height, r_im.height))
    rs = lambda im: im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
    return fit(rs(bp_im), W, H), fit(rs(r_im), W, H)
rend = {'side': f'renders/brz_side_{TAG}.png', 'front': f'renders/brz_front_{TAG}.png', 'rear': f'tex/build/rear_{TAG}.png', 'top': None}
CW, CH = 420, 230; rows = ('side', 'top', 'front', 'rear')
sheet = Image.new('RGB', (CW * 3 + 40, 60 + CH * 4 + 30 * 4), (255, 255, 255)); d = ImageDraw.Draw(sheet)
d.text((20, 15), f'BRZ detail pass - blueprint compare (gate = blueprint-frame IoU, car meshes only)', font=F, fill=(0, 0, 0))
for i, v in enumerate(rows):
    y = 60 + i * (CH + 30); ok = iou[v] >= gate[v]
    d.text((20, y - 2), f'{v}: IoU {iou[v]:.4f}  (gate {gate[v]:.2f}) {"PASS" if ok else "FAIL"}', font=f2, fill=(0, 120, 0) if ok else (200, 0, 0))
    if rend[v]:
        a_, b_ = same_scale(autocrop(crop(v)), autocrop(Image.open(rend[v]).convert('RGB')), v, CW - 10, CH - 20)
        sheet.paste(a_, (10, y + 18)); sheet.paste(b_, (10 + CW, y + 18))
    else:
        sheet.paste(fit(crop(v), CW - 10, CH - 20), (10, y + 18))
        d.text((CW + 40, y + 100), '(top: see IoU overlay)', font=f2, fill=(90, 90, 90))
    ov = Image.open(f'renders/clay_raw/bpiou_{v}.png').convert('RGB'); sheet.paste(fit(ov, CW - 10, CH - 20), (10 + 2 * CW, y + 18))
d.text((20, sheet.height - 26), 'cols: blueprint | textured model (ortho, same metres/px) | overlay grey=both, orange=blueprint only, blue=model only', font=f2, fill=(60, 60, 60))
sheet.save(f'renders/brz_bp_compare_{TAG}_800.jpg', quality=90)
# photo vs render
import os
P = [(v, p) for v, p in (('front34', 'ref/brz_photo_front34.jpg'), ('rear34', 'ref/brz_photo_rear34.jpg'), ('side', 'ref/brz_photo_side.jpg'))
     if os.path.exists(p)]          # the repo copy ships without the dealer front34 photo (licensing unclear)
W, H = 560, 380; sh = Image.new('RGB', (W * 2 + 30, 50 + len(P) * (H + 10)), (255, 255, 255)); d = ImageDraw.Draw(sh)
d.text((15, 12), 'BRZ detail pass - photo vs render (surface character only; photo is a different car colour/angle at front34)', font=f2, fill=(0, 0, 0))
for i, (v, p) in enumerate(P):
    y = 50 + i * (H + 10)
    sh.paste(fit(Image.open(p).convert('RGB'), W, H), (10, y)); sh.paste(fit(Image.open(f'renders/brz_{v}_{TAG}.png').convert('RGB'), W, H), (W + 20, y))
sh.save(f'renders/brz_photo_vs_render_{TAG}_800.jpg', quality=90)
print('sheets done')
