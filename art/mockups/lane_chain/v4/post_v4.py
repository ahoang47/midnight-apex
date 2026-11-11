"""Post for build_v4.py: glow-only bloom -> 1999-style HUD drawn at native 640x480 (no AA) -> RGB555 + 4x4 Bayer
-> 2x nearest (1280x960).  python3 post_v4.py entry|apex"""
import os, sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'raw')
SHOT = sys.argv[1] if len(sys.argv) > 1 else 'entry'
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def rgb555(a):     # same quantiser as art/mood/tokyo_v2/post_v2.py
    h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
FN = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'; FI = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-BoldOblique.otf'
if not os.path.exists(FN): FN = FI = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
def font(sz, it=False): return ImageFont.truetype(FI if it else FN, sz)
RED, GRN, YEL = (232, 40, 44), (44, 184, 74), (240, 200, 40)
AMBER, AMBER_D = (255, 176, 40), (150, 80, 14)
EDGE, EDGE_D, INK = (210, 230, 255), (70, 90, 150), (8, 8, 14)
PANEL = (10, 14, 36)

base = np.asarray(Image.open(os.path.join(RAW, f'raw_{SHOT}.png')).convert('RGB')).astype(np.float32)
g = Image.open(os.path.join(RAW, f'glow_{SHOT}.png')).convert('RGBA'); ga = np.asarray(g).astype(np.float32)
lit = Image.fromarray((ga[..., :3] * ga[..., 3:] / 255).astype(np.uint8))
b1 = np.asarray(lit.filter(ImageFilter.GaussianBlur(3))).astype(np.float32); b2 = np.asarray(lit.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)
frame = np.clip(base + .35 * b1 + .25 * b2, 0, 255)
A = json.load(open(os.path.join(RAW, f'anchors_{SHOT}.json')))

# --- HUD layers: 'semi' = PS1-style 50/50 semi-transparent polys, 'solid' = opaque polys + 1-bit text
H, W = 480, 640
semi = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(semi)
solid = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(solid); d.fontmode = '1'
def text(xy, s, f, fill, shadow=True, anchor='la'):
    if shadow: d.text((xy[0] + 1, xy[1] + 1), s, font=f, fill=INK + (255,), anchor=anchor)
    d.text(xy, s, font=f, fill=fill + (255,), anchor=anchor)
def outline(pts, col):
    d.line(pts + [pts[0]], fill=col + (255,), width=1)
def cut_panel(x0, y0, x1, y1, c=8):
    """angular panel: top-right and bottom-left corners cut at 45 deg (hard-edged, like the logo)."""
    return [(x0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1), (x0 + c, y1), (x0, y1 - c)]
def chip(x1, y, label, col, dim=False, w=None):
    """stat tag: small slanted chip, right-aligned at x1."""
    f = font(11); tw = int(d.textlength(label, font=f)); w = w or tw + 12; x0 = x1 - w
    pts = [(x0 + 4, y), (x1, y), (x1 - 4, y + 13), (x0, y + 13)]
    if dim:
        outline(pts, tuple(int(c * .55) for c in col)); text((x0 + w / 2, y + 7), label, f, tuple(int(c * .7) for c in col), shadow=False, anchor='mm')
    else:
        d.polygon(pts, fill=col + (255,)); outline(pts, INK)
        text((x0 + w / 2, y + 7), label, f, INK if col == YEL else (255, 255, 255), shadow=False, anchor='mm')

if SHOT == 'entry':
    # 1) lane markers above the turn-in point: chosen line = chunky faux-3D chevron, the other two = faint hollow ticks
    CH = 'OUT'
    for k, (x, y, z) in A['lanes'].items():
        x, y = int(round(x)), int(round(y))
        if k == CH:
            w, h, t = 26, 15, 8
            pts = lambda dy: [(x - w // 2, y - h + dy), (x - w // 2 + t, y - h + dy), (x, y - 4 + dy), (x + w // 2 - t, y - h + dy), (x + w // 2, y - h + dy), (x, y + dy)]
            d.polygon(pts(3), fill=AMBER_D + (255,)); d.polygon(pts(0), fill=AMBER + (255,)); outline(pts(3), INK); outline(pts(0), INK)
            d.line([(x - w // 2 + 2, y - h + 1), (x - w // 2 + t - 1, y - h + 1)], fill=(255, 236, 170, 255))
            text((x, y - h - 9), k, font(11), AMBER, anchor='mm')
        else:
            w, h, t = 12, 7, 4
            pts = [(x - w // 2, y - h), (x - w // 2 + t, y - h), (x, y - 3), (x + w // 2 - t, y - h), (x + w // 2, y - h), (x, y)]
            ds.polygon(pts, fill=(150, 170, 210, 255)); text((x, y - h - 8), k, font(10), (120, 135, 170), anchor='mm')
    # 2) corner-warning plate (Initial D / TXR style): right-hander ahead
    px, py = 296, 22
    ds.polygon(cut_panel(px, py, px + 48, py + 34, 7), fill=PANEL + (255,)); outline(cut_panel(px, py, px + 48, py + 34, 7), EDGE)
    arrow = [(px + 12, py + 29), (px + 12, py + 13), (px + 28, py + 13), (px + 28, py + 7), (px + 38, py + 16), (px + 28, py + 25), (px + 28, py + 19), (px + 18, py + 19), (px + 18, py + 29)]
    d.polygon([(a + 1, b + 2) for a, b in arrow], fill=AMBER_D + (255,)); d.polygon(arrow, fill=AMBER + (255,)); outline(arrow, INK)
    text((px + 24, py + 44), 'ENTRY', font(11, True), EDGE, anchor='mm')
    # 3) small entry strip, bottom centre
    x0, y0 = 232, 444
    poly = cut_panel(x0, y0, x0 + 176, y0 + 20, 6); ds.polygon(poly, fill=PANEL + (255,)); outline(poly, EDGE)
    for i, k in enumerate(('OUT', 'MID', 'IN')):
        cx = x0 + 40 + i * 50
        if k == CH:
            d.polygon([(cx - 21, y0 + 4), (cx + 19, y0 + 4), (cx + 17, y0 + 16), (cx - 23, y0 + 16)], fill=AMBER + (255,))
            text((cx - 2, y0 + 10), k, font(12, True), INK, shadow=False, anchor='mm')
        else: text((cx - 2, y0 + 10), k, font(12, True), (120, 135, 170), anchor='mm')
    text((x0 + 9, y0 + 10), '<', font(12), EDGE, anchor='mm'); text((x0 + 169, y0 + 10), '>', font(12), EDGE, anchor='mm')
else:
    # late-90s call menu, bottom-left over the empty road
    x0, y0, x1, y1 = 16, 340, 336, 462
    ds.polygon(cut_panel(x0, y0, x1, y1, 10), fill=PANEL + (255,))
    outline(cut_panel(x0, y0, x1, y1, 10), EDGE); outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 9), EDGE_D)
    # header tab: angular amber slab + breadcrumb
    tab = [(x0, y0 - 16), (x0 + 112, y0 - 16), (x0 + 124, y0), (x0, y0)]
    d.polygon(tab, fill=AMBER + (255,)); outline(tab, INK)
    text((x0 + 8, y0 - 15), 'APEX CALL', font(14, True), INK, shadow=False)
    text((x0 + 134, y0 - 13), 'ENTRY  OUT  >  APEX  >  EXIT', font(11, True), (150, 165, 200))
    rows = [('Late brake, dive inside', 'POW', RED, False), ('Hold the inside, cover', 'EN', GRN, False), ('Trail-brake, late apex', 'HAN \u00b7 none drawn', YEL, True)]
    for i, (lab, tag, col, off) in enumerate(rows):
        ry = y0 + 12 + i * 27
        if i == 0:   # cursor bar: stepped amber gradient (4 hard bands) + solid arrow cursor
            for j, a in enumerate((200, 150, 100, 55)):
                bx0 = x0 + 8 + j * 70; ds.polygon([(bx0, ry - 2), (bx0 + 74, ry - 2), (bx0 + 70, ry + 19), (bx0 - 4, ry + 19)], fill=AMBER + (a,))
            d.polygon([(x0 + 9, ry + 3), (x0 + 17, ry + 8), (x0 + 9, ry + 13)], fill=(255, 255, 255, 255)); outline([(x0 + 9, ry + 3), (x0 + 17, ry + 8), (x0 + 9, ry + 13)], INK)
        text((x0 + 24, ry + 1), lab, font(15), (88, 92, 110) if off else (255, 255, 255), shadow=not off)
        chip(x1 - 10, ry + 3, tag, col, dim=off)
        if i < 2: d.line([(x0 + 22, ry + 22), (x1 - 12, ry + 22)], fill=EDGE_D + (255,))
    text((x0 + 12, y1 - 17), '\u25b2\u25bc CHOOSE      \u25cf COMMIT', font(11), (150, 165, 200))

# PS1 semi-transparency: alpha 255 polys blend 50/50, lower alpha = proportionally less
sa = np.asarray(semi).astype(np.float32); af = sa[..., 3:] / 255 * .5
alpha_bar = (sa[..., 3:] < 254) & (sa[..., 3:] > 0)
af = np.where(alpha_bar, sa[..., 3:] / 255 * .75, af)
frame = frame * (1 - af) + sa[..., :3] * af
so = np.asarray(solid).astype(np.float32); m = so[..., 3:] > 127
frame = np.where(m, so[..., :3], frame)
q = rgb555(np.clip(frame, 0, 255))
out = Image.fromarray(q).resize((1280, 960), Image.NEAREST)
name = {'entry': 'entry_rear.png', 'apex': 'apex_call.png'}[SHOT]
out.save(os.path.join(HERE, name)); Image.fromarray(q).save(os.path.join(RAW, f'native_{name}'))
print('wrote', name)
