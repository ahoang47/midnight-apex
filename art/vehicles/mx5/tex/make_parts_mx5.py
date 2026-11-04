"""MX-5 (ND) parts atlas, 256x256 (A.3.3), painted, RGB555 + Bayer:
  [0..128 x 0..128]    wheel face disc: 205/45R17 sidewall with made-up "SOLANA" lettering + gunmetal 10-spoke rim (ND 17" design read)
                        (the wheel mesh is a 10-sided cylinder; rim, spokes and lettering exist only here)
  [128..256 x 0..256]  tread strip (circumferential grooves + sipes), tiles vertically
  [0..128 x 192..256]  headlamp lens art (pocket floor UVs, parts/lamp_uvs in build_gr_detail.py): dark housing,
                        one round LED projector with a lit ring (outboard), LED line along the upper edge, lens glint
Also writes the 128x64 RGBA glow sprite atlas (left: warm head glow, right: red tail glow).
python3 tex/make_parts_mx5.py atlas.png lamp_uv.json glow.png"""
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
RIM = 0.701                                                                    # 17" rim / 308 mm tyre radius
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
lit = 0.80 + 0.20 * np.cos(a + 2.2)
fs = ((a / (2 * np.pi) * 5) % 1) - 0.5; spread = 0.115 * np.clip((r - 0.16) / (RIM - 0.21), 0, 1)       # 5 twin-spoke V pairs (10 spokes)
dv = np.abs(np.abs(fs) - spread); sp = (dv < 0.048) & (r > 0.16) & (r <= RIM - 0.05)
img[face & sp] = (GUN * lit[..., None])[face & sp]
edge = sp & (dv > 0.032) & (fs > 0)                                             # one shaded flank per spoke
img[face & edge] = (GUN_D * lit[..., None])[face & edge]
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
arc_text('SOLANA', -np.pi / 2, 0.855, True)                                     # top arc reads left-to-right
arc_text('205/45R17', np.pi / 2, 0.855, False)                                 # bottom arc reads left-to-right
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
# ND LED headlamp (public photos, A.1.3): slim smoked housing, ONE big round projector toward the outboard end with a
# lit LED ring around it, a thin LED line along the upper edge running inboard, no amber (that sits in the bumper)
J = json.load(open(uvj))['head']; O = np.asarray(J['outline_px'], np.float32)
m = np.zeros((S * SS, S * SS), np.uint8); cv2.fillPoly(m, [np.round(O * SS * 16).astype(np.int32)], 1, cv2.LINE_8, shift=4)
x0, y0, x1, y1 = J['tile']; T_ = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
img[T_] = (24, 25, 30)                                                          # housing (also beyond the traced lens)
M = m > 0
d = cv2.distanceTransform(m, cv2.DIST_L2, 5) / SS
img[M] = (36, 39, 48)                                                           # smoked inner housing
img[M & (d < 1.3)] = (66, 70, 80)                                               # bezel edge
ox0, oy0 = O.min(0); ox1, oy1 = O.max(0); Wl, Hl = ox1 - ox0, oy1 - oy0
sc_, mid = J['scale_px_per_m'], J['mid']
def to_px(y, z): return 64.0 - (abs(y) - mid[0]) * sc_, 224.0 - (z - mid[1]) * sc_     # car (|y|, z) -> atlas px (lamp_uvs mapping)
pcx, pcy = to_px(0.613, 0.606); pr = 0.040 * sc_                                 # projector: the blueprint's round DETAILS circle (y .579-.647, z .572-.640)
q = np.hypot(xx - pcx, yy - pcy) / pr
img[M & (q <= 1.25)] = (52, 56, 66)                                             # reflector bowl
img[M & (q <= 1.00) & (q > 0.80)] = (226, 230, 236)                             # LED ring
img[M & (q <= 0.80)] = (92, 100, 118); img[M & (q <= 0.55)] = (170, 178, 194); img[M & (q <= 0.22)] = (226, 230, 238)   # lens
img[M & (q > 0.80) & (q <= 0.86)] = (40, 42, 48)
top_edge = {}
for c in np.arange(int(ox0), int(ox1)) + 0.5:
    col_ = M[:, int(c * SS)]
    if col_.any(): top_edge[c] = np.min(np.where(col_)[0]) / SS
for c, t in top_edge.items():                                                   # LED line hugging the upper edge, inboard of the projector
    if c < pcx + pr * 1.1: continue
    img[M & (np.abs(xx - c) <= 0.5) & (yy > t + 1.0) & (yy < t + 2.4)] = (214, 220, 228)
gl = M & (np.abs((xx - ox0) / Wl - (yy - oy0) / Hl * 0.35 - 0.62) < 0.010); img[gl] = img[gl] * 0.6 + np.array([200, 208, 224]) * 0.4   # lens glint
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
