"""Post for build_lsc.py (B.5c-checked: see b5c_composite): glow-only bloom (blend50 .22, 0) + sat 1.05 -> late-90s angular HUD drawn at native 640x480
(1-bit text, PS1 50/50 semi-transparent panels) -> RGB555 + 4x4 Bayer -> 2x nearest. Writes the 4 frames and a contact sheet.
Selector adapted from race_state_study/entry_matrix (PLAYER LINE LOCK). UNAPPROVED PROPOSAL.  python3 post_lsc.py"""
import os, sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'raw'); OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, '/workspace/mockups/tones/work'); from tones import TONES
T = TONES['blend50']
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def rgb555(a):
    h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
FN = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'; FI = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-BoldOblique.otf'
def font(n, it=False): return ImageFont.truetype(FI if it else FN, n)
WHITE = (220, 230, 242); DIM = (140, 159, 180); DIMMER = (96, 108, 132); EDGE = (71, 94, 127); EDGE_L = (150, 172, 205)
AMBER = (255, 184, 56); AMBER_D = (150, 90, 20); PANEL = (10, 14, 36); INK = (8, 10, 16); SOD = (240, 200, 148)
COL = {'ATK': (232, 40, 44), 'DEF': (44, 184, 74), 'NEU': (240, 200, 40)}
PICKS = [('ENTRY', 'MID', 'NEU'), ('APEX', 'IN', 'DEF'), ('EXIT', 'OUT', 'ATK')]   # sample picks for the mockup only
def cut(x, y, x1, y1, c=5): return [(x, y), (x1 - c, y), (x1, y + c), (x1, y1), (x + c, y1), (x, y1 - c)]


# ---- B.5c (art_direction, 2026-11-11): every layer drawn and composited at native 640x480 with no AA and no smoothing.
# Overlay layers must have binary alpha (PIL polygons/lines/arcs are aliased; text uses fontmode '1'); any rotation is NEAREST.
# Composite = 50/50 PS1 semi layer, then hard 1-bit solid layer; RGB555 + 4x4 Bayer ONCE; then ONE 2x nearest upscale.
# Layers are dumped to raw/layers_<name>.npz for verify_b5c.py. (Bloom on the 3D glow pass is the approved B.2a post, not an overlay.)
def b5c_composite(b, semi, solid, name, raw_dir, out_dir):
    assert semi.size == solid.size == (640, 480) and b.shape == (480, 640, 3), 'B.5c: native 640x480 only'
    sa = np.asarray(semi).astype(np.float32); so = np.asarray(solid)
    for lab, a in (('semi', sa[..., 3]), ('solid', so[..., 3])):
        bad = set(np.unique(a).astype(int).tolist()) - {0, 255}
        assert not bad, f'B.5c: soft alpha {sorted(bad)[:8]} in {lab} layer of {name}'
    al = (sa[..., 3:] > 0) * .5
    under = b * (1 - al) + sa[..., :3] * al
    m = so[..., 3:] == 255
    comp = np.clip(np.where(m, so[..., :3].astype(np.float32), under), 0, 255)
    q = Image.fromarray(rgb555(comp))
    np.savez_compressed(os.path.join(raw_dir, f'layers_{name}.npz'), solid=so, semi_a=sa[..., 3].astype(np.uint8), under=np.clip(under, 0, 255).astype(np.float32), comp=comp.astype(np.float32))
    q.save(os.path.join(raw_dir, f'native_{name}.png')); q.resize((1280, 960), Image.NEAREST).save(os.path.join(out_dir, f'{name}.png'))
    return q

def scene(shot):
    base = np.asarray(Image.open(os.path.join(RAW, f'raw_{shot}.png')).convert('RGB')).astype(np.float32)
    g = np.asarray(Image.open(os.path.join(RAW, f'glow_{shot}.png')).convert('RGBA')).astype(np.float32)
    lit = Image.fromarray((g[..., :3] * g[..., 3:] / 255).astype(np.uint8))
    b1 = np.asarray(lit.filter(ImageFilter.GaussianBlur(3))).astype(np.float32); b2 = np.asarray(lit.filter(ImageFilter.GaussianBlur(9))).astype(np.float32)
    f = np.clip(base + T['bloom'][0] * b1 + T['bloom'][1] * b2, 0, 255)
    lum = (f * np.array([.299, .587, .114])).sum(-1, keepdims=True); return np.clip(lum + (f - lum) * T['sat'], 0, 255)

def frame(n):
    """n = 1 entry pick, 2 apex pick, 3 exit pick, 4 line locked (back at the entry chase camera)."""
    shot = {1: 'chase', 2: 'apex', 3: 'exit', 4: 'chase'}[n]; active = {1: 0, 2: 1, 3: 2, 4: None}[n]
    b = scene(shot); A = json.load(open(os.path.join(RAW, f'anchors_{shot}.json')))
    semi = Image.new('RGBA', (640, 480)); sd = ImageDraw.Draw(semi)
    solid = Image.new('RGBA', (640, 480)); d = ImageDraw.Draw(solid); d.fontmode = '1'
    def txt(x, y, t, size=12, col=WHITE, anchor='lt', sh=True, it=False):
        if sh: d.text((x + 1, y + 1), t, font=font(size, it), fill=INK + (255,), anchor=anchor)
        d.text((x, y), t, font=font(size, it), fill=col + (255,), anchor=anchor)
    def panel(x, y, x1, y1, col=EDGE, c=5):
        p = cut(x, y, x1, y1, c); sd.polygon(p, fill=PANEL + (255,)); d.line(p + [p[0]], fill=col + (255,), width=1)
    def chip(x, y, st, label=None, w=49):
        p = [(x + 4, y), (x + w, y), (x + w - 4, y + 14), (x, y + 14)]; d.polygon(p, fill=COL[st] + (255,)); d.line(p + [p[0]], fill=INK + (255,))
        txt(x + w / 2, y + 7, label or st, 11, INK if st == 'NEU' else (255, 255, 255), 'mm', sh=False)
    def tick(x, y, col=(44, 184, 74)): d.line([(x, y + 3), (x + 2, y + 5), (x + 6, y)], fill=col + (255,), width=2)

    # rear-view mirror only on the chase camera (frames 1 and 4), exactly where entry_matrix put it
    if shot == 'chase':
        m = np.flip(scene_mirror(), axis=1); b[16:80, 224:416] = m
        d.rectangle((221, 13, 418, 82), outline=(110, 127, 151, 255)); d.rectangle((222, 14, 417, 81), outline=(15, 20, 30, 255)); txt(291, 84, 'REAR VIEW', 9, DIM)

    # top-left: line-lock timer (sample values)
    panel(14, 12, 192, 57)
    if n < 4:
        secs = {1: '04.8s', 2: '03.1s', 3: '01.6s'}[n]; lit_n = {1: 10, 2: 6, 3: 3}[n]
        txt(23, 18, 'LINE LOCK', 12); txt(183, 18, secs, 19, AMBER, 'rt')
        for j in range(17): d.polygon([(24 + j * 9, 43), (30 + j * 9, 43), (28 + j * 9, 50), (22 + j * 9, 50)], fill=(AMBER if j < lit_n else (68, 52, 40)) + (255,))
    else:
        txt(23, 18, 'LINE LOCK', 12); txt(183, 18, 'SET', 19, WHITE, 'rt')
        for j in range(17): d.polygon([(24 + j * 9, 43), (30 + j * 9, 43), (28 + j * 9, 50), (22 + j * 9, 50)], fill=EDGE_L + (255,))

    # top-right: corner plate with the hairpin map and the three camera stops (E / A / X)
    panel(476, 12, 628, 96)
    txt(534, 18, 'HAIRPIN R', 16)
    stop_name = {1: 'ENTRY', 2: 'APEX', 3: 'EXIT', 4: 'ENTRY'}[n]
    txt(534, 40, 'VIEW', 9, DIM); txt(560, 38, stop_name, 13, AMBER)
    d.line([(492, 88), (492, 46)], fill=SOD + (255,), width=3); d.arc((492 - 1, 32, 520 + 1, 60), 180, 360, fill=SOD + (255,), width=3)
    d.line([(520, 46), (520, 80)], fill=SOD + (255,), width=3); d.polygon([(514, 78), (526, 78), (520, 88)], fill=SOD + (255,))
    stops = [(492, 70), (506, 33), (520, 64)]
    for i, (sx, sy) in enumerate(stops):
        cur = (i == active) or (n == 4 and i == 0); done = (active is not None and i < active) or (n == 4 and i > 0)
        dia = [(sx, sy - 5), (sx + 5, sy), (sx, sy + 5), (sx - 5, sy)]
        d.polygon(dia, fill=(AMBER if cur else (WHITE if done else (40, 46, 64))) + (255,)); d.line(dia + [dia[0]], fill=INK + (255,))
    txt(534, 58, 'E', 10, AMBER if n in (1, 4) else WHITE); txt(548, 58, 'A', 10, AMBER if n == 2 else (WHITE if n > 2 else DIMMER)); txt(562, 58, 'X', 10, AMBER if n == 3 else (WHITE if n == 4 else DIMMER))
    txt(534, 74, 'CAMERA STOP', 9, DIM)

    # right: PLAYER LINE LOCK selector (entry_matrix layout, one active slot that moves Entry -> Apex -> Exit)
    used = {k: 0 for k in COL}
    for i, (_, _, st) in enumerate(PICKS):
        if (active is not None and i < active) or n == 4: used[st] += 1
    y = 154; slots = []
    for i, (ph, lane, st) in enumerate(PICKS):
        h = 60 if i == active else 31; slots.append((i, ph, lane, st, y, h)); y += h + 8
    y_end = y - 8
    panel(414, 107, 628, y_end + 24, AMBER if n == 4 else EDGE)
    txt(422, 114, 'PLAYER LINE LOCK', 15)
    txt(422, 133, 'HAND', 10, DIM)
    for k, st in enumerate(('ATK', 'DEF', 'NEU')): chip(473 + k * 50, 131, st, f'{st} x{2 - used[st]}')
    for i, ph, lane, st, y, h in slots:
        if i == active:
            panel(420, y, 622, y + h, AMBER)
            d.polygon([(425, y + 9), (431, y + 14), (425, y + 19)], fill=AMBER + (255,)); txt(438, y + 5, ph, 12, AMBER)
            txt(615, y + 6, 'CONFIRM', 9, AMBER, 'rt')
            d.polygon([(475, y + 21), (613, y + 21), (609, y + 39), (471, y + 39)], fill=AMBER + (255,)); txt(543, y + 30, f'< {lane} / {st} >', 15, INK, 'mm', sh=False)
            txt(428, y + 44, 'D-PAD LANE', 10); d.ellipse((538, y + 45, 543, y + 50), fill=WHITE + (255,)); txt(549, y + 44, 'SET', 10)
        else:
            filled = n == 4 or (active is not None and i < active)
            panel(420, y, 622, y + h, EDGE_L if filled else EDGE)
            txt(428, y + 9, ph, 12, WHITE if filled else DIM)
            if filled:
                txt(492, y + 7, lane, 15, WHITE); chip(530, y + 8, st); tick(606, y + 11)
            else:
                txt(510, y + 7, '- - -', 15, DIMMER); txt(614, y + 11, 'NOT SET', 9, DIMMER, 'rt')
    nset = 3 if n == 4 else active
    txt(422, y_end + 8, '[L1] / [R1] PHASE' if n < 4 else '[X] REDO', 10, DIM); txt(619, y_end + 8, f'{nset}/3 SET', 10, AMBER if n == 4 else DIM, 'rt')

    # frames 2 and 3: lane marks at this camera stop (picked lane = amber chevron, others = faint ticks)
    if n in (2, 3):
        pick = PICKS[active][1]
        for k, (x, yy, z) in A['lanes'].items():
            x, yy = int(round(x)), int(round(yy))
            if k == pick:
                w, hh, t = 26, 15, 8
                pts = lambda dy: [(x - w // 2, yy - hh + dy), (x - w // 2 + t, yy - hh + dy), (x, yy - 4 + dy), (x + w // 2 - t, yy - hh + dy), (x + w // 2, yy - hh + dy), (x, yy + dy)]
                d.polygon(pts(3), fill=AMBER_D + (255,)); d.polygon(pts(0), fill=AMBER + (255,)); d.line(pts(0) + [pts(0)[0]], fill=INK + (255,))
                txt(x, yy - hh - 9, k, 12, AMBER, 'mm')
            else:
                w, hh, t = 12, 7, 4
                pts = [(x - w // 2, yy - hh), (x - w // 2 + t, yy - hh), (x, yy - 3), (x + w // 2 - t, yy - hh), (x + w // 2, yy - hh), (x, yy)]
                sd.polygon(pts, fill=(150, 170, 210, 255)); txt(x, yy - hh - 8, k, 10, (150, 165, 200), 'mm')

    # frame 4: LINE LOCKED banner, about to hand over to playback
    if n == 4:
        x0, y0, x1, y1 = 176, 112, 404, 150
        sd.polygon(cut(x0 - 6, y0 - 4, x1 + 6, y1 + 22, 9), fill=PANEL + (255,))
        slab = [(x0 + 10, y0), (x1, y0), (x1 - 10, y1), (x0, y1)]
        d.polygon([(a + 2, c + 3) for a, c in slab], fill=AMBER_D + (255,)); d.polygon(slab, fill=AMBER + (255,)); d.line(slab + [slab[0]], fill=INK + (255,))
        d.line([(x0 + 12, y0 + 3), (x1 - 4, y0 + 3)], fill=(255, 236, 170, 255))
        txt((x0 + x1) // 2, (y0 + y1) // 2 + 1, 'LINE LOCKED', 26, INK, 'mm', sh=False, it=True)
        for k, (ph, lane, st) in enumerate(PICKS):
            cx = x0 + 22 + k * 70; chip(cx, y1 + 5, st)
            if k < 2: txt(cx + 57, y1 + 5, '>', 12, DIM)

    name = {1: '1_entry_pick', 2: '2_apex_pick', 3: '3_exit_pick', 4: '4_line_locked'}[n]
    return b5c_composite(b, semi, solid, name, RAW, OUT), name
def scene_mirror():
    m = np.asarray(Image.open(os.path.join(RAW, 'raw_mirror.png')).convert('RGB')).astype(np.float32)
    lum = (m * np.array([.299, .587, .114])).sum(-1, keepdims=True); return np.clip(lum + (m - lum) * T['sat'], 0, 255)

frames = [frame(n) for n in (1, 2, 3, 4)]
# contact sheet: native frames on a 2x2 grid with game-style number tabs, then 2x nearest
W, H = 1310, 1072; sh = Image.new('RGB', (W, H), (5, 10, 19)); d = ImageDraw.Draw(sh); d.fontmode = '1'
d.text((12, 8), 'LINE SELECT CAMERA', font=font(20, True), fill=WHITE); d.text((200, 12), 'PROPOSAL  /  UNAPPROVED  /  TOUGE HAIRPIN R', font=font(13), fill=DIM)
slots = []
titles = ['ENTRY PICK', 'APEX PICK', 'EXIT PICK', 'LINE LOCKED']
for i, (q, name) in enumerate(frames):
    x = 10 + (i % 2) * 650; y = 40 + (i // 2) * 516
    tab = [(x, y), (x + 150, y), (x + 162, y + 22), (x, y + 22)]
    d.polygon(tab, fill=AMBER); d.rectangle((x, y, x + 24, y + 22), fill=INK)
    d.text((x + 12, y + 11), str(i + 1), font=font(19, True), fill=AMBER, anchor='mm'); d.text((x + 32, y + 11), titles[i], font=font(15, True), fill=INK, anchor='lm')
    d.line([(x + 166, y + 21), (x + 640, y + 21)], fill=EDGE)
    slots.append((q, (x, y + 24)))
q = Image.fromarray(rgb555(np.asarray(sh).astype(np.float32)))      # quantise the sheet chrome (1-bit text, hard polys), then paste
for f_, xy in slots: q.paste(f_, xy)                                 # the already-quantised native frames 1:1 (no resampling)
q.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(OUT, 'line_select_cam_contact_sheet.png'))   # full size: same 2x as the frames
json.dump({name: [xy[0] * 2, xy[1] * 2] for (f_, xy), (_, name) in zip(slots, frames)}, open(os.path.join(RAW, 'sheet_layout.json'), 'w'))
print('post ok')
