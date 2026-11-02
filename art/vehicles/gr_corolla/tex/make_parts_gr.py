"""GR Corolla parts atlas, 256x256 (A.3.3), painted, RGB555 + Bayer:
  [0..128 x 0..128]    wheel face disc: 235/40R18 sidewall with made-up "VORTA" lettering + gunmetal 15-spoke rim
                        (the wheel mesh is a 10-sided cylinder; rim, spokes and lettering exist only here)
  [128..256 x 0..256]  tread strip (circumferential grooves + sipes), tiles vertically
  [0..128 x 192..256]  headlamp lens art (pocket floor UVs, parts/lamp_uvs in build_gr_detail.py): dark housing,
                        LED DRL strip along the upper edge, two LED projector modules, amber corner, lens glint
Also writes the 128x64 RGBA glow sprite atlas (left: warm head glow, right: red tail glow).
python3 tex/make_parts_gr.py atlas.png lamp_uv.json glow.png"""
import numpy as np, sys, os, json, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
out, uvj, glow = sys.argv[1:4]
S = 256; SS = 4; VMAX = 232.0
img = np.zeros((S * SS, S * SS, 3), np.float32) + (20, 20, 22)
yy, xx = np.mgrid[0:S * SS, 0:S * SS].astype(np.float32) / SS + 0.5 / SS        # atlas px coords
# ---------------------------------------------------------------- wheel disc (centre 64,64, R 63 = tyre OD)
cx, cy, R = 64.0, 64.0, 63.0
r = np.hypot(xx - cx, yy - cy) / R; a = np.arctan2(yy - cy, xx - cx)
RIM = 0.712                                                                    # 18" rim / 321 mm tyre radius
tile = (xx < 128) & (yy < 128)
tyre = tile & (r <= 1.0) & (r > RIM)
img[tyre] = (24, 24, 26)
img[tile & (r > 0.97) & (r <= 1.0)] = (16, 16, 17)                              # shoulder
img[tile & (r > RIM) & (r < RIM + 0.03)] = (34, 34, 36)                         # bead seat
rim = tile & (r <= RIM)
GUN = np.array([74, 77, 84]); GUN_D = np.array([40, 42, 47])
img[rim & (r > RIM - 0.05)] = (96, 99, 106)                                     # rim lip
face = rim & (r <= RIM - 0.05)
img[face] = (14, 14, 16)                                                        # dark barrel behind the spokes (no brake geometry)
sp = (np.abs(((a / (2 * np.pi) * 15) % 1) - 0.5) < 0.16) & (r > 0.16) & (r <= RIM - 0.05)
lit = 0.80 + 0.20 * np.cos(a + 2.2)
img[face & sp] = (GUN * lit[..., None])[face & sp]
edge = (np.abs(((a / (2 * np.pi) * 15) % 1) - 0.5) < 0.16) & (np.abs(((a / (2 * np.pi) * 15) % 1) - 0.5) > 0.11)
img[face & sp & edge] = (GUN_D * lit[..., None])[face & sp & edge]
hub = tile & (r <= 0.20); img[hub] = (64, 66, 72); img[tile & (r <= 0.09)] = (30, 31, 34)
for k in range(5):                                                              # lug nuts
    q = 2 * np.pi * k / 5; img[tile & (np.hypot(xx - cx - 0.135 * R * np.cos(q), yy - cy - 0.135 * R * np.sin(q)) < 0.028 * R)] = (120, 122, 128)
img[tile & (r > 1.0)] = (20, 20, 22)
# made-up sidewall lettering (upper and lower arc), drawn at 4x, light grey, unbranded
lt = Image.new('L', (S * SS, S * SS), 0); dr = ImageDraw.Draw(lt)
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 9 * SS)
except Exception: font = ImageFont.load_default()
def arc_text(txt, ang0, rr, upper=True):
    n = len(txt); step = 0.115
    for i, ch in enumerate(txt):
        q = ang0 + (i - (n - 1) / 2) * step * (1 if upper else -1)
        px_, py_ = cx + rr * R * np.cos(q), cy + rr * R * np.sin(q)
        g = Image.new('L', (14 * SS, 14 * SS), 0); ImageDraw.Draw(g).text((7 * SS, 7 * SS), ch, fill=255, font=font, anchor='mm')
        rot = -np.degrees(q) - 90 if upper else -np.degrees(q) + 90
        g = g.rotate(rot, resample=Image.BICUBIC)
        lt.paste(255, (int(px_ * SS - 7 * SS), int(py_ * SS - 7 * SS)), g)
arc_text('VORTA', -np.pi / 2, 0.855, True)                                     # top arc reads left-to-right
arc_text('235/40R18', np.pi / 2, 0.855, False)                                 # bottom arc reads left-to-right
L = np.asarray(lt, np.float32) / 255.0
img = img * (1 - L[..., None] * 0.85) + np.array([150, 150, 156]) * (L[..., None] * 0.85)
# inner-cap corner (UV 0.01, 0.51 -> px ~2.5, 125) stays dark
# ---------------------------------------------------------------- tread strip (u across the width, v around)
tr = (xx >= 128)
img[tr] = (26, 26, 28)
u = (xx - 128) / 128.0
groove = tr & ((np.abs(u - 0.30) < 0.035) | (np.abs(u - 0.52) < 0.035) | (np.abs(u - 0.74) < 0.035))
img[groove] = (12, 12, 13)
sipe = tr & ((yy % 16) < 2.0) & ~groove & (u > 0.12) & (u < 0.88); img[sipe] = (18, 18, 19)
img[tr & ((u < 0.06) | (u > 0.94))] = (22, 22, 24)
# ---------------------------------------------------------------- headlamp lens (tile 0..128 x 192..256)
J = json.load(open(uvj))['head']; O = np.asarray(J['outline_px'], np.float32)
m = np.zeros((S * SS, S * SS), np.uint8); cv2.fillPoly(m, [np.round(O * SS * 16).astype(np.int32)], 1, cv2.LINE_8, shift=4)
x0, y0, x1, y1 = J['tile']; T_ = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
img[T_] = (30, 32, 37)                                                          # housing (also beyond the traced lens)
M = m > 0
d = cv2.distanceTransform(m, cv2.DIST_L2, 5) / SS
img[M] = (44, 48, 58)                                                           # inner housing (dark blue-grey)
ox0, oy0 = O.min(0); ox1, oy1 = O.max(0); Wl, Hl = ox1 - ox0, oy1 - oy0
# outline: u decreases outboard (lamp_uvs), so outboard = small x
img[M & (d < 1.4)] = (70, 74, 84)                                               # chrome bezel edge
top_edge = np.array([np.min(np.where(M[:, int(c * SS)])[0]) / SS if M[:, int(c * SS)].any() else np.nan for c in np.arange(int(ox0), int(ox1)) + 0.5])
for i, c in enumerate(np.arange(int(ox0), int(ox1)) + 0.5):                    # LED DRL strip hugging the upper edge
    if np.isnan(top_edge[i]): continue
    sel = M & (np.abs(xx - c) <= 0.5) & (yy > top_edge[i] + 1.2) & (yy < top_edge[i] + 3.0)
    img[sel] = (224, 228, 232)
for k, (fxp, fyp, rr) in enumerate(((0.62, 0.60, 0.17), (0.80, 0.58, 0.15))):   # two LED projector modules (inboard half)
    pcx, pcy = ox0 + fxp * Wl, oy0 + fyp * Hl; rr_ = rr * Hl * 1.3
    q = np.hypot(xx - pcx, yy - pcy) / rr_
    img[M & (q <= 1.0)] = (62, 68, 80); img[M & (q <= 0.78)] = (150, 158, 172); img[M & (q <= 0.40)] = (214, 218, 226)
    img[M & (q > 0.92) & (q <= 1.0)] = (28, 30, 34)
amb = M & (xx < ox0 + 0.16 * Wl) & (yy > oy0 + 0.45 * Hl); img[amb] = (178, 120, 40)   # amber corner (outboard, low)
gl = M & (np.abs((xx - ox0) / Wl - (yy - oy0) / Hl * 0.35 - 0.30) < 0.012); img[gl] = img[gl] * 0.6 + np.array([210, 216, 228]) * 0.4
img = np.minimum(img, VMAX)
small = cv2.resize(img, (S, S), interpolation=cv2.INTER_AREA)
rgb555_bayer(Image.fromarray(np.clip(small, 0, 255).astype(np.uint8))).save(out); print('parts atlas', out)
# ---------------------------------------------------------------- glow sprite atlas 128x64 RGBA
gy, gx = np.mgrid[0:64, 0:128].astype(np.float32) + 0.5
G = np.zeros((64, 128, 4), np.float32)
for k, c in ((0, (255, 240, 214)), (1, (255, 40, 30))):
    rr = np.hypot((gx - (32 + 64 * k)) / 32, (gy - 32) / 32); al = np.clip(1 - rr, 0, 1) ** 2.2 * (0.80 if k == 0 else 0.70)
    sel = (gx >= 64 * k) & (gx < 64 * (k + 1)); G[sel, :3] = c; G[sel, 3] = (al * 255)[sel]
Image.fromarray(G.clip(0, 255).astype(np.uint8), 'RGBA').save(glow); print('glow', glow)
