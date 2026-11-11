"""Post for build_ow.py (overworld free roam): glow-only bloom -> late-90s console HUD drawn at native 640x480 (no AA)
-> RGB555 + 4x4 Bayer -> 2x nearest (1280x960).  Same HUD kit as lane_chain/v5/post_v5.py.  python3 post_ow.py"""
import os, sys, json, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'raw'); SHOT = 'overworld'
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def rgb555(a):
    h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
FN = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'; FI = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-BoldOblique.otf'
if not os.path.exists(FN): FN = FI = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
def font(sz, it=False): return ImageFont.truetype(FI if it else FN, sz)
RED, GRN, YEL = (232, 40, 44), (44, 184, 74), (240, 200, 40)
AMBER, AMBER_D = (255, 176, 40), (150, 80, 14)
EDGE, EDGE_D, INK = (210, 230, 255), (70, 90, 150), (8, 8, 14)
PANEL = (10, 14, 36); SUB = (150, 165, 200)

sys.path.insert(0, os.path.join(HERE, '..')); from tones import TONES
TONE = os.environ.get('TONE', 'sodium'); T = TONES[TONE]; OUTDIR = os.path.abspath(os.path.join(HERE, '..', '..'))
base = np.asarray(Image.open(os.path.join(RAW, f'raw_{SHOT}_{TONE}.png')).convert('RGB')).astype(np.float32)
g = Image.open(os.path.join(RAW, f'glow_{SHOT}_{TONE}.png')).convert('RGBA'); ga = np.asarray(g).astype(np.float32)
lit = Image.fromarray((ga[..., :3] * ga[..., 3:] / 255).astype(np.uint8))
b1 = np.asarray(lit.filter(ImageFilter.GaussianBlur(3))).astype(np.float32); b2 = np.asarray(lit.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)
frame = np.clip(base + T['bloom'][0] * b1 + T['bloom'][1] * b2, 0, 255)
if T['sat'] != 1.0:     # scene-level saturation, before the HUD and before quantise (dither stays clean)
    lum = (frame * np.array([.299, .587, .114])).sum(-1, keepdims=True); frame = np.clip(lum + (frame - lum) * T['sat'], 0, 255)
A = json.load(open(os.path.join(RAW, f'anchors_{SHOT}.json')))

H, W = 480, 640
semi = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(semi)
solid = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(solid); d.fontmode = '1'
def text(xy, s, f, fill, shadow=True, anchor='la'):
    if shadow: d.text((xy[0] + 1, xy[1] + 1), s, font=f, fill=INK + (255,), anchor=anchor)
    d.text(xy, s, font=f, fill=fill + (255,), anchor=anchor)
def outline(pts, col): d.line(pts + [pts[0]], fill=col + (255,), width=1)
def cut_panel(x0, y0, x1, y1, c=8):
    return [(x0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1), (x0 + c, y1), (x0, y1 - c)]
def panel(x0, y0, x1, y1, c=8, double=False):
    p = cut_panel(x0, y0, x1, y1, c); ds.polygon(p, fill=PANEL + (255,)); outline(p, EDGE)
    if double: outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, c - 1), EDGE_D)

# 1) district + clock plate, top-left (district name is a placeholder; city is fictional)
DISTRICT, CLOCK = 'HARBOR FLATS', '02:14'
x0, y0 = 12, 26
panel(x0, y0, x0 + 150, y0 + 30, 7)
tab = [(x0, y0 - 14), (x0 + 104, y0 - 14), (x0 + 114, y0), (x0, y0)]
d.polygon(tab, fill=AMBER + (255,)); outline(tab, INK); text((x0 + 7, y0 - 13), DISTRICT, font(12, True), INK, shadow=False)
text((x0 + 8, y0 + 3), CLOCK, font(24, True), (255, 255, 255))
text((x0 + 8 + int(d.textlength(CLOCK, font=font(24, True))) + 4, y0 + 14), 'AM', font(11, True), SUB)

# 2) money, top-right: wallet + the garage debt (rep is lore only per 07-economy, so no rep number)
x1, y0 = 628, 12
panel(x1 - 140, y0, x1, y0 + 42, 7)
text((x1 - 132, y0 + 5), 'CASH', font(10, True), SUB); text((x1 - 10, y0 + 2), '3,250', font(16, True), (255, 255, 255), anchor='ra')
d.line([(x1 - 132, y0 + 22), (x1 - 8, y0 + 22)], fill=EDGE_D + (255,))
text((x1 - 132, y0 + 26), 'OWED TO GARAGE', font(10, True), SUB); text((x1 - 10, y0 + 25), '38,000', font(12, True), (230, 120, 110), anchor='ra')

# 3) minimap, bottom-left: rotated so camera-forward is up, player arrow in the middle, meet icon
MX0, MY0, MX1, MY1 = 12, 340, 140, 468; MC = ((MX0 + MX1) / 2, (MY0 + MY1) / 2); SCL = 0.95   # px per metre
yaw = math.radians(A['cam_yaw']); px_, py_ = A['player_xy']
def mp(x, y):
    dx, dy = x - px_, y - py_
    rx = dx * math.cos(yaw) - dy * math.sin(yaw); ry = dx * math.sin(yaw) + dy * math.cos(yaw)   # rotate so camera fwd -> up
    return (MC[0] + rx * SCL, MC[1] - ry * SCL)
mm = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dm = ImageDraw.Draw(mm)
for r in A['roads']:
    pts = [mp(*p) for p in r]
    dm.line(pts, fill=(62, 72, 110, 255), width=9, joint='curve')
for r in A['roads']:
    dm.line([mp(*p) for p in r], fill=(150, 165, 205, 255), width=5, joint='curve')
mx, my = mp(*A['meet_xy'])
dm.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=AMBER_D + (255,)); dm.ellipse([mx - 4, my - 4, mx + 4, my + 4], fill=AMBER + (255,)); dm.rectangle([mx - 1, my - 1, mx + 1, my + 1], fill=INK + (255,))
clip = Image.new('L', (W, H), 0); ImageDraw.Draw(clip).polygon(cut_panel(MX0 + 2, MY0 + 2, MX1 - 2, MY1 - 2, 9), fill=255)
panel(MX0, MY0, MX1, MY1, 10, double=True)
mm.putalpha(Image.fromarray(np.minimum(np.asarray(mm)[..., 3], np.asarray(clip))))
solid.alpha_composite(mm); d = ImageDraw.Draw(solid); d.fontmode = '1'
# player arrow (heading = player_hdg in world, shown in map space)
hd = math.radians(A.get('player_hdg', 0.0)); hx_, hy_ = math.cos(hd), math.sin(hd)
ax = hx_ * math.cos(yaw) - hy_ * math.sin(yaw); ay = -(hx_ * math.sin(yaw) + hy_ * math.cos(yaw)); nx, ny = -ay, ax
c = MC; tip = (c[0] + ax * 8, c[1] + ay * 8); l = (c[0] - ax * 5 + nx * 5, c[1] - ay * 5 + ny * 5); r = (c[0] - ax * 5 - nx * 5, c[1] - ay * 5 - ny * 5); bk = (c[0] - ax * 2, c[1] - ay * 2)
d.polygon([tip, l, bk, r], fill=AMBER + (255,)); outline([tip, l, bk, r], INK)
# north tick on the rim
ncx, ncy = MC[0] - math.sin(yaw) * 54, MC[1] - math.cos(yaw) * 54
d.polygon([(ncx - 6, ncy - 6), (ncx + 6, ncy - 6), (ncx + 6, ncy + 6), (ncx - 6, ncy + 6)], fill=PANEL + (255,)); outline([(ncx - 6, ncy - 6), (ncx + 6, ncy - 6), (ncx + 6, ncy + 6), (ncx - 6, ncy + 6)], EDGE_D)
text((ncx, ncy), 'N', font(10, True), EDGE, shadow=False, anchor='mm')

# 4) meet prompt by the pin: who is there, and what you can do
pxs, pys = A['pin'][:2]; qx, qy = int(pxs + 22), int(pys - 30)
pw, ph = 118, 54
ds.polygon(cut_panel(qx, qy, qx + pw, qy + ph, 7), fill=PANEL + (255,)); outline(cut_panel(qx, qy, qx + pw, qy + ph, 7), EDGE)
d.line([(int(pxs) + 6, int(pys) - 2), (qx, qy + 16)], fill=EDGE + (255,), width=1)
tab = [(qx, qy - 13), (qx + 72, qy - 13), (qx + 81, qy), (qx, qy)]
d.polygon(tab, fill=AMBER + (255,)); outline(tab, INK); text((qx + 6, qy - 12), 'WRX STI', font(11, True), INK, shadow=False)
text((qx + pw - 8, qy - 11), 'parked', font(10, True), SUB, anchor='ra')
sel = [(qx + 4, qy + 6), (qx + pw - 6, qy + 6), (qx + pw - 9, qy + 23), (qx + 1, qy + 23)]
ds.polygon(sel, fill=AMBER + (200,))
text((qx + 9, qy + 7), '\u25cf CHALLENGE', font(13, True), (255, 255, 255))
text((qx + 9, qy + 28), '\u25cf TALK', font(13, True), (190, 200, 225))
text((qx + pw - 8, qy + 41), '1-on-1', font(9, True), SUB, anchor='ra')

sa = np.asarray(semi).astype(np.float32); af = sa[..., 3:] / 255 * .5
alpha_bar = (sa[..., 3:] < 254) & (sa[..., 3:] > 0)
af = np.where(alpha_bar, sa[..., 3:] / 255 * .75, af)
frame = frame * (1 - af) + sa[..., :3] * af
so = np.asarray(solid).astype(np.float32); m = so[..., 3:] > 127
frame = np.where(m, so[..., :3], frame)
q = rgb555(np.clip(frame, 0, 255))
Image.fromarray(q).resize((1280, 960), Image.NEAREST).save(os.path.join(OUTDIR, f'overworld_{TONE}.png')); Image.fromarray(q).save(os.path.join(RAW, f'native_overworld_{TONE}.png'))
print('wrote overworld.png', A['player'], A['pin'], A['rival'])
