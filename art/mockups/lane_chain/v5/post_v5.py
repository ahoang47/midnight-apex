"""Post for build_v5.py (v5: line planned on the rear chase view, replay shows the locked plan): glow-only bloom -> 1999-style HUD drawn at native 640x480 (no AA) -> RGB555 + 4x4 Bayer
-> 2x nearest (1280x960).  python3 post_v5.py entry|apex"""
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
def chip(x1, y, label, col, dim=False, w=None, pending=False):
    """stat tag: small slanted chip, right-aligned at x1."""
    f = font(11); tw = int(d.textlength(label, font=f)); w = w or tw + 12; x0 = x1 - w
    pts = [(x0 + 4, y), (x1, y), (x1 - 4, y + 13), (x0, y + 13)]
    if pending:   # planned but not played yet: solid chip at half brightness (never confused with 'none drawn')
        d.polygon(pts, fill=tuple(int(c * .5) for c in col) + (255,)); outline(pts, INK)
        text((x0 + w / 2, y + 7), label, f, (200, 205, 215), shadow=False, anchor='mm'); return
    if dim:
        outline(pts, tuple(int(c * .55) for c in col)); text((x0 + w / 2, y + 7), label, f, tuple(int(c * .7) for c in col), shadow=False, anchor='mm')
    else:
        d.polygon(pts, fill=col + (255,)); outline(pts, INK)
        text((x0 + w / 2, y + 7), label, f, INK if col == YEL else (255, 255, 255), shadow=False, anchor='mm')

def check(x, y, col=GRN):      # small hard-edged tick mark (no font glyph needed)
    d.line([(x, y + 3), (x + 2, y + 5), (x + 6, y)], fill=col + (255,), width=2)
def lock_x(x, y, r, col):
    d.line([(x - r, y - r), (x + r, y + r)], fill=col + (255,), width=2); d.line([(x - r, y + r), (x + r, y - r)], fill=col + (255,), width=2)
DIMY = tuple(int(c * .7) for c in YEL); DIMT = (88, 92, 110)
def crumb(x, y, steps, cur):
    """ENTRY OUT [tick] > APEX > EXIT ; current phase in an amber slab, done = tick, pending = dim."""
    f = font(11, True)
    for i, (lab, state) in enumerate(steps):
        w = int(d.textlength(lab, font=f))
        if state == 'cur':
            d.polygon([(x - 3, y - 1), (x + w + 5, y - 1), (x + w + 2, y + 12), (x - 6, y + 12)], fill=AMBER + (255,)); text((x, y), lab, f, INK, shadow=False); x += w + 6
        elif state == 'done': text((x, y), lab, f, EDGE); check(x + w + 3, y + 3); x += w + 12
        else: text((x, y), lab, f, (110, 122, 155)); x += w
        if i < len(steps) - 1: text((x + 4, y), '>', f, (110, 122, 155)); x += 15
CALLS = [('Late brake, dive inside', 'POW', RED, False), ('Hold the inside, cover', 'EN', GRN, False), ('Trail-brake, late apex', 'HAN \u00b7 none drawn', YEL, True)]
EXIT_CALL = ('Short-shift, track out', 'EN', GRN)   # placeholder exit call until Nathaniel writes them

if SHOT == 'entry':
    CH, LOCK = 'OUT', 'MID'
    # 1) lane markers over the turn-in point: chosen = chunky faux-3D chevron, available = faint tick, locked = dark tick crossed out
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
            if k == LOCK:
                d.polygon(pts, fill=(40, 42, 56, 255)); outline(pts, (70, 74, 92)); lock_x(x, y - 4, 4, DIMY)
                text((x, y - h - 8), k, font(10), DIMT, anchor='mm')
            else:
                ds.polygon(pts, fill=(150, 170, 210, 255)); text((x, y - h - 8), k, font(10), (120, 135, 170), anchor='mm')
    # 2) corner-warning plate
    px, py = 296, 22
    ds.polygon(cut_panel(px, py, px + 48, py + 34, 7), fill=PANEL + (255,)); outline(cut_panel(px, py, px + 48, py + 34, 7), EDGE)
    arrow = [(px + 12, py + 29), (px + 12, py + 13), (px + 28, py + 13), (px + 28, py + 7), (px + 38, py + 16), (px + 28, py + 25), (px + 28, py + 19), (px + 18, py + 19), (px + 18, py + 29)]
    d.polygon([(a + 1, b + 2) for a, b in arrow], fill=AMBER_D + (255,)); d.polygon(arrow, fill=AMBER + (255,)); outline(arrow, INK)
    text((px + 24, py + 44), 'TURN-IN 16m', font(11, True), EDGE, anchor='mm')
    # 3) entry strip, bottom-left: OUT selected (ticked), MID locked with its stat tag, IN available
    x0, y0 = 14, 430
    poly = cut_panel(x0, y0, x0 + 188, y0 + 36, 6); ds.polygon(poly, fill=PANEL + (255,)); outline(poly, EDGE)
    text((x0 + 8, y0 + 3), 'ENTRY', font(10, True), (150, 165, 200))
    for i, k in enumerate(('OUT', 'MID', 'IN')):
        cx = x0 + 36 + i * 58; ry = y0 + 19
        if k == CH:
            d.polygon([(cx - 21, ry - 6), (cx + 19, ry - 6), (cx + 17, ry + 6), (cx - 23, ry + 6)], fill=AMBER + (255,))
            text((cx - 4, ry), k, font(12, True), INK, shadow=False, anchor='mm'); check(cx + 8, ry - 3, INK)
        elif k == LOCK:
            text((cx - 2, ry - 2), k, font(12, True), DIMT, shadow=False, anchor='mm')
            f = font(9); lab = 'HAN \u00b7 none drawn'; tw = int(d.textlength(lab, font=f)) + 10
            tp = [(cx - tw // 2 + 3, ry + 4), (cx + tw // 2, ry + 4), (cx + tw // 2 - 3, ry + 14), (cx - tw // 2, ry + 14)]
            outline(tp, tuple(int(c * .55) for c in YEL)); text((cx, ry + 9), lab, f, DIMY, shadow=False, anchor='mm')
        else: text((cx - 2, ry), k, font(12, True), (150, 165, 200), anchor='mm')
    # 4) line-planning menu, lower-right (clear of both cars and the corner): planning APEX while still on the straight
    x0, y0, x1, y1 = 404, 328, 628, 468
    ds.polygon(cut_panel(x0, y0, x1, y1, 9), fill=PANEL + (255,))
    outline(cut_panel(x0, y0, x1, y1, 9), EDGE); outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
    tab = [(x0, y0 - 15), (x0 + 108, y0 - 15), (x0 + 119, y0), (x0, y0)]
    d.polygon(tab, fill=AMBER + (255,)); outline(tab, INK); text((x0 + 7, y0 - 14), 'PLAN THE LINE', font(13, True), INK, shadow=False)
    crumb(x0 + 9, y0 + 6, [('ENTRY OUT', 'done'), ('APEX', 'cur'), ('EXIT', 'todo')], 1)
    d.line([(x0 + 6, y0 + 22), (x1 - 8, y0 + 22)], fill=EDGE_D + (255,))
    for i, (lab, tag, col, off) in enumerate(CALLS):
        ry = y0 + 29 + i * 22
        if i == 0:
            for j, a in enumerate((200, 150, 100, 55)):
                bx0 = x0 + 6 + j * 52; ds.polygon([(bx0, ry - 2), (bx0 + 56, ry - 2), (bx0 + 52, ry + 16), (bx0 - 4, ry + 16)], fill=AMBER + (a,))
            tri = [(x0 + 7, ry + 2), (x0 + 14, ry + 7), (x0 + 7, ry + 12)]; d.polygon(tri, fill=(255, 255, 255, 255)); outline(tri, INK)
        text((x0 + 19, ry), lab, font(13), DIMT if off else (255, 255, 255), shadow=not off)
        chip(x1 - 8, ry + 1, tag, col, dim=off)
    text((x0 + 9, y1 - 16), 'Line locks at turn-in', font(10, True), (150, 165, 200))
    text((x1 - 10, y1 - 16), '\u25cf SET', font(10), (150, 165, 200), anchor='ra')
else:
    # replay: locked-plan strip along the bottom (clear of the cars, which sit in the upper half)
    x0, y0, x1, y1 = 12, 432, 628, 468
    ds.polygon(cut_panel(x0, y0, x1, y1, 8), fill=PANEL + (255,)); outline(cut_panel(x0, y0, x1, y1, 8), EDGE)
    tab = [(x0, y0 - 14), (x0 + 92, y0 - 14), (x0 + 102, y0), (x0, y0)]
    d.polygon(tab, fill=EDGE + (255,)); outline(tab, INK); text((x0 + 7, y0 - 13), 'LINE LOCKED', font(12, True), INK, shadow=False)
    segs = [('ENTRY', 'OUT', None, None, 'done', 126), ('APEX', CALLS[0][0], 'POW', RED, 'cur', 268), ('EXIT', EXIT_CALL[0], EXIT_CALL[1], EXIT_CALL[2], 'todo', 222)]
    x = x0 + 4
    for i, (ph, call, tag, col, st, w) in enumerate(segs):
        cy = y0 + 18
        if st == 'cur':
            band = [(x + 2, y0 + 4), (x + w, y0 + 4), (x + w - 5, y1 - 4), (x - 3, y1 - 4)]
            ds.polygon(band, fill=AMBER + (190,)); outline(band, AMBER)
        tc = INK if st == 'cur' else (EDGE if st == 'done' else (125, 135, 165))
        text((x + 6, y0 + 5), ph, font(10, True), INK if st == 'cur' else (150, 165, 200), shadow=st != 'cur')
        text((x + 6, y0 + 16), call, font(13), (255, 255, 255) if st == 'cur' else ((225, 232, 250) if st == 'done' else (125, 135, 165)), shadow=True)
        if st == 'done': check(x + 6 + int(d.textlength(call, font=font(13))) + 5, y0 + 20)
        if tag: chip(x + w - 8, y0 + 12, tag, col, pending=(st == 'todo'))
        x += w + 2
        if i < 2: d.line([(x - 1, y0 + 6), (x - 5, y1 - 6)], fill=EDGE_D + (255,))
    text((x1 - 10, y0 - 12), 'REPLAY', font(10, True), (150, 165, 200), anchor='ra')

# PS1 semi-transparency: alpha 255 polys blend 50/50, lower alpha = proportionally less
sa = np.asarray(semi).astype(np.float32); af = sa[..., 3:] / 255 * .5
alpha_bar = (sa[..., 3:] < 254) & (sa[..., 3:] > 0)
af = np.where(alpha_bar, sa[..., 3:] / 255 * .75, af)
frame = frame * (1 - af) + sa[..., :3] * af
so = np.asarray(solid).astype(np.float32); m = so[..., 3:] > 127
frame = np.where(m, so[..., :3], frame)
q = rgb555(np.clip(frame, 0, 255))
out = Image.fromarray(q).resize((1280, 960), Image.NEAREST)
name = {'entry': 'entry_plan.png', 'apex': 'apex_replay.png'}[SHOT]
out.save(os.path.join(HERE, name)); Image.fromarray(q).save(os.path.join(RAW, f'native_{name}'))
print('wrote', name)
