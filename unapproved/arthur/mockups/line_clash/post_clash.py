"""Post for build_clash.py: bloom (blend50 .22, 0) + sat 1.05 -> native 640x480 HUD (1-bit text, PS1 50/50 panels)
-> RGB555 + 4x4 Bayer -> 2x nearest. Option A = line vs line panel; Option B = clash beat cards. UNAPPROVED PROPOSAL.
python3 post_clash.py"""
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
BEATS = {'ATK': 'NEU', 'NEU': 'DEF', 'DEF': 'ATK'}
PHASES = ['ENTRY', 'APEX', 'EXIT']; YOU = ['NEU', 'DEF', 'ATK']; RIV = ['ATK', 'ATK', 'DEF']   # sample lines
def result(a, b): return 'TIE' if a == b else ('WIN' if BEATS[a] == b else 'LOSS')
RES = [result(a, b) for a, b in zip(YOU, RIV)]          # -> LOSS, WIN, LOSS
def cut(x, y, x1, y1, c=5): return [(x, y), (x1 - c, y), (x1, y + c), (x1, y1), (x + c, y1), (x, y1 - c)]
def scene(name):
    base = np.asarray(Image.open(os.path.join(RAW, f'raw_{name}.png')).convert('RGB')).astype(np.float32)
    g = np.asarray(Image.open(os.path.join(RAW, f'glow_{name}.png')).convert('RGBA')).astype(np.float32)
    lit = Image.fromarray((g[..., :3] * g[..., 3:] / 255).astype(np.uint8))
    f = np.clip(base + T['bloom'][0] * np.asarray(lit.filter(ImageFilter.GaussianBlur(3))).astype(np.float32)
                + T['bloom'][1] * np.asarray(lit.filter(ImageFilter.GaussianBlur(9))).astype(np.float32), 0, 255)
    lum = (f * np.array([.299, .587, .114])).sum(-1, keepdims=True); return np.clip(lum + (f - lum) * T['sat'], 0, 255)
class HUD:
    def __init__(s):
        s.semi = Image.new('RGBA', (640, 480)); s.sd = ImageDraw.Draw(s.semi)
        s.solid = Image.new('RGBA', (640, 480)); s.d = ImageDraw.Draw(s.solid); s.d.fontmode = '1'
    def txt(s, x, y, t, size=12, col=WHITE, anchor='lt', sh=True, it=False):
        if sh: s.d.text((x + 1, y + 1), t, font=font(size, it), fill=INK + (255,), anchor=anchor)
        s.d.text((x, y), t, font=font(size, it), fill=col + (255,), anchor=anchor)
    def panel(s, x, y, x1, y1, col=EDGE, c=5):
        p = cut(x, y, x1, y1, c); s.sd.polygon(p, fill=PANEL + (255,)); s.d.line(p + [p[0]], fill=col + (255,), width=1)
    def chip(s, x, y, st, w=49, dim=False):
        c = tuple(int(v * .6) for v in COL[st]) if dim else COL[st]
        p = [(x + 4, y), (x + w, y), (x + w - 4, y + 14), (x, y + 14)]; s.d.polygon(p, fill=c + (255,)); s.d.line(p + [p[0]], fill=INK + (255,))
        s.txt(x + w / 2, y + 7, st, 11, INK if st == 'NEU' else (255, 255, 255), 'mm', sh=False)
    def res(s, cx, y, r, dim=False):
        w = 49; x = cx - w // 2; p = [(x + 4, y), (x + w, y), (x + w - 4, y + 14), (x, y + 14)]
        if r == 'WIN': s.d.polygon(p, fill=(AMBER if not dim else AMBER_D) + (255,)); s.txt(cx, y + 7, 'WIN', 11, INK, 'mm', sh=False)
        elif r == 'LOSS': s.d.polygon(p, fill=(40, 44, 60, 255)); s.d.line(p + [p[0]], fill=EDGE_L + (255,)); s.txt(cx, y + 7, 'LOSS', 11, WHITE if not dim else DIM, 'mm', sh=False)
        else: s.d.polygon(p, fill=EDGE + (255,)); s.txt(cx, y + 7, 'TIE', 11, WHITE, 'mm', sh=False)
    def corner_plate(s, k):
        s.panel(476, 12, 628, 96); s.txt(534, 18, 'HAIRPIN R', 16); s.txt(534, 40, 'PLAY', 9, DIM); s.txt(560, 38, PHASES[k], 13, AMBER)
        d = s.d; d.line([(492, 88), (492, 46)], fill=SOD + (255,), width=3); d.arc((491, 32, 521, 60), 180, 360, fill=SOD + (255,), width=3)
        d.line([(520, 46), (520, 80)], fill=SOD + (255,), width=3); d.polygon([(514, 78), (526, 78), (520, 88)], fill=SOD + (255,))
        for i, (sx, sy) in enumerate([(492, 70), (506, 33), (520, 64)]):
            dia = [(sx, sy - 5), (sx + 5, sy), (sx, sy + 5), (sx - 5, sy)]
            d.polygon(dia, fill=(AMBER if i == k else (WHITE if i < k else (40, 46, 64))) + (255,)); d.line(dia + [dia[0]], fill=INK + (255,))
        s.txt(534, 74, 'PLAYBACK', 9, DIM)
    def finish(s, b, name):
        sa = np.asarray(s.semi).astype(np.float32); al = sa[..., 3:] / 255 * .5; b = b * (1 - al) + sa[..., :3] * al
        so = np.asarray(s.solid); b = np.where(so[..., 3:] > 127, so[..., :3], b)
        q = Image.fromarray(rgb555(np.clip(b, 0, 255))); q.save(os.path.join(RAW, f'native_{name}.png'))
        q.resize((1280, 960), Image.NEAREST).save(os.path.join(OUT, f'{name}.png')); return q

def option_a(k):
    """Both full lines face up from the start of playback (frame-4 LINE LOCKED panel + rival row). Only the current phase is
    highlighted; results fill in as each phase plays."""
    h = HUD(); b = scene(PHASES[k].lower() + '_a')
    x0, y0, x1, y1 = 120, 12, 466, 100; h.panel(x0, y0, x1, y1, EDGE_L, 8)
    tab = [(x0, y0 - 0), (x0 + 0, y0)]
    h.txt(x0 + 8, y0 + 6, 'LINE LOCKED', 12, AMBER, it=True)
    cols = [241, 331, 421]
    for i, cx in enumerate(cols):
        cur = i == k
        if cur:
            p = cut(cx - 42, y0 + 3, cx + 42, y1 - 3, 5); h.d.line(p + [p[0]], fill=AMBER + (255,), width=1)
            h.d.polygon([(cx - 30, y0 + 9), (cx - 25, y0 + 13), (cx - 30, y0 + 17)], fill=AMBER + (255,))
        h.txt(cx, y0 + 13, PHASES[i], 11, AMBER if cur else (WHITE if i < k else DIM), 'mm')
    rows = [('YOU', YOU, 30), ('RIVAL', RIV, 50)]
    for lab, line, dy in rows:
        h.txt(x0 + 8, y0 + dy + 1, lab, 11, WHITE if lab == 'YOU' else DIM)
        for i, cx in enumerate(cols): h.chip(cx - 24, y0 + dy, line[i])
        for i in range(2): h.txt(cols[i] + 45, y0 + dy + 7, '>', 10, DIMMER, 'mm')
    h.txt(x0 + 8, y0 + 71, 'RESULT', 11, DIM)
    for i, cx in enumerate(cols):
        if i <= k: h.res(cx, y0 + 70, RES[i])
        else: h.txt(cx, y0 + 77, '- -', 11, DIMMER, 'mm')
    h.d.line([(x0 + 6, y0 + 25), (x1 - 8, y0 + 25)], fill=EDGE + (255,))
    h.corner_plate(k)
    return h.finish(b, f'a{k + 1}_{PHASES[k].lower()}_line_vs_line')

def option_b(k):
    """Clash beat: playback holds, the two cards slam in from opposite sides, the winner breaks the loser's card."""
    h = HUD(); b = scene(PHASES[k].lower() + '_b'); d = h.d
    you, riv, r = YOU[k], RIV[k], RES[k]
    # hold: flat 50/50 letterbox bars
    h.sd.rectangle((0, 0, 639, 34), fill=(4, 6, 14, 255)); h.sd.rectangle((0, 446, 639, 479), fill=(4, 6, 14, 255))
    d.line([(0, 34), (639, 34)], fill=EDGE + (255,)); d.line([(0, 446), (639, 446)], fill=EDGE + (255,))
    h.txt(320, 17, f'{PHASES[k]}  CLASH', 18, WHITE, 'mm', it=True)
    win_txt = 'YOU WIN' if r == 'WIN' else ('RIVAL WINS' if r == 'LOSS' else 'TIE')
    h.txt(624, 17, win_txt, 16, AMBER if r == 'WIN' else EDGE_L, 'rm', it=True)
    h.txt(16, 17, 'YOU', 13, WHITE, 'lm'); h.txt(52, 17, 'vs', 11, DIM, 'lm'); h.txt(68, 17, 'RIVAL', 13, DIM, 'lm')
    # bottom bar: phase track with results so far
    x = 170
    for i in range(3):
        cur = i == k; h.txt(x, 463, PHASES[i], 12, AMBER if cur else (WHITE if i < k else DIMMER), 'lm')
        w = int(d.textlength(PHASES[i], font=font(12)))
        if i <= k: h.res(x + w + 32, 456, RES[i])
        else: h.txt(x + w + 32, 463, '- -', 11, DIMMER, 'mm')
        x += w + 80
        if i < 2: h.txt(x - 14, 463, '>', 11, DIMMER, 'mm')
    # cards: 92 x 120 skewed slabs meeting at screen centre, speed bars trailing to their own screen edge
    CY0, CY1, SK = 44, 156, 14
    def card_pts(xc, flip):
        l, rr = xc - 46, xc + 46
        return [(l + SK, CY0), (rr + SK, CY0), (rr - SK, CY1), (l - SK, CY1)] if not flip else [(l - SK, CY0), (rr - SK, CY0), (rr + SK, CY1), (l + SK, CY1)]
    def bars(side, st):
        for j, (yy, ln) in enumerate(((CY0 + 14, 170), (CY0 + 52, 230), (CY0 + 92, 150))):
            if side == 'L': h.sd.polygon([(0, yy), (ln, yy), (ln - 8, yy + 10), (0, yy + 10)], fill=COL[st] + (255,))
            else: h.sd.polygon([(640 - ln + 8, yy), (640, yy), (640, yy + 10), (640 - ln, yy + 10)], fill=COL[st] + (255,))
    def face(pts, st, who, dim=False):
        c = tuple(int(v * .55) for v in COL[st]) if dim else COL[st]
        d.polygon([(a + 3, bb + 4) for a, bb in pts], fill=INK + (255,)); d.polygon(pts, fill=c + (255,)); d.line(pts + [pts[0]], fill=INK + (255,), width=2)
        inner = [(pts[0][0] + 5, pts[0][1] + 5), (pts[1][0] - 5, pts[1][1] + 5), (pts[2][0] - 5, pts[2][1] - 5), (pts[3][0] + 5, pts[3][1] - 5)]
        d.line(inner + [inner[0]], fill=(INK if st == 'NEU' else (255, 255, 255)) + (255,), width=1)
        cx = sum(p[0] for p in pts) / 4; tc = INK if st == 'NEU' else (255, 255, 255)
        h.txt(cx, CY0 + 16, PHASES[k], 10, tc, 'mm', sh=False); h.txt(cx, (CY0 + CY1) // 2 + 2, st, 34, tc, 'mm', sh=False, it=True)
        h.txt(cx, CY1 - 14, who, 11, tc, 'mm', sh=False)
    PX, RX = 278, 362           # overlap ~8 px at the centre line
    bars('L', you); bars('R', riv)
    if r == 'TIE':
        face(card_pts(PX - 6, False), you, 'YOU'); face(card_pts(RX + 6, True), riv, 'RIVAL')
    else:
        win_left = r == 'WIN'
        lpts = card_pts(RX + 10 if win_left else PX - 10, not win_left)
        lst, lwho = (riv, 'RIVAL') if win_left else (you, 'YOU')
        # loser: split along a jagged diagonal into two hard-edged halves pushed apart, plus three angular chips
        cxL = sum(p[0] for p in lpts) / 4; dirn = 1 if win_left else -1
        crack = [(cxL - 10 * dirn, CY0), (cxL + 6 * dirn, CY0 + 34), (cxL - 6 * dirn, CY0 + 58), (cxL + 12 * dirn, CY0 + 86), (cxL - 2 * dirn, CY1)]
        img = Image.new('RGBA', (640, 480)); di = ImageDraw.Draw(img); di.fontmode = '1'
        # draw the whole loser card on its own layer, then cut it into two halves with the crack polygon
        sub = HUD(); sub.d = di; sub.sd = di
        def face_on(dd):
            c = tuple(int(v * .55) for v in COL[lst])
            dd.polygon(lpts, fill=c + (255,)); dd.line(lpts + [lpts[0]], fill=INK + (255,), width=2)
            tc = (200, 200, 190)
            for t_, yy, sz in ((PHASES[k], CY0 + 16, 10), (lst, (CY0 + CY1) // 2 + 2, 34), (lwho, CY1 - 14, 11)):
                dd.text((cxL, yy), t_, font=font(sz, sz == 34), fill=tc + (255,), anchor='mm')
        face_on(di)
        far = 400 * dirn
        maskA = Image.new('L', (640, 480)); ImageDraw.Draw(maskA).polygon(crack + [(cxL + far, CY1), (cxL + far, CY0)], fill=255)
        maskB = Image.new('L', (640, 480)); ImageDraw.Draw(maskB).polygon(crack + [(cxL - far, CY1), (cxL - far, CY0)], fill=255)
        outer = Image.new('RGBA', (640, 480)); inner = Image.new('RGBA', (640, 480))
        outer.paste(img, (0, 0), maskA); inner.paste(img, (0, 0), maskB)
        outer = outer.rotate(-9 * dirn, center=(cxL, CY0 + 30), resample=Image.NEAREST, translate=(30 * dirn, -8))
        inner = inner.rotate(4 * dirn, center=(cxL, CY1 - 20), resample=Image.NEAREST, translate=(-2 * dirn, 0))
        for lay in (inner, outer):
            sh_ = Image.new('RGBA', (640, 480)); sh_.paste(Image.new('RGBA', (640, 480), INK + (255,)), (3, 4), lay)
            h.solid.alpha_composite(sh_); h.solid.alpha_composite(lay)
        for (ax, ay, sz) in ((cxL + 34 * dirn, CY0 + 20, 7), (cxL + 50 * dirn, CY0 + 70, 5), (cxL + 26 * dirn, CY1 + 8, 6)):
            tri = [(ax, ay - sz), (ax + sz * dirn, ay + sz // 2), (ax - sz * dirn // 2, ay + sz)]
            d.polygon(tri, fill=tuple(int(v * .55) for v in COL[lst]) + (255,)); d.line(tri + [tri[0]], fill=INK + (255,))
        # flat hard-edged impact star at the contact point, then the intact winner on top
        ix = 320 + 4 * dirn; iy = (CY0 + CY1) // 2
        star = []
        for j in range(12):
            a = j / 12 * 6.283; rr = (40 if j % 2 == 0 else 15) + (8 if j % 4 == 0 else 0)
            star.append((ix + rr * np.cos(a) * .8, iy + rr * np.sin(a)))
        d.polygon(star, fill=(250, 240, 210, 255)); d.line(star + [star[0]], fill=INK + (255,), width=1)
        wpts = card_pts(PX + 8 if win_left else RX - 8, not win_left)
        face(wpts, you if win_left else riv, 'YOU' if win_left else 'RIVAL')
    return h.finish(b, f'b{k + 1}_{PHASES[k].lower()}_clash')

A = [option_a(k) for k in range(3)]; Bf = [option_b(k) for k in range(3)]
# comparison sheet: A row on top, B row below, native frames then 2x nearest
W, H = 1960, 1104; sh = Image.new('RGB', (W, H), (5, 10, 19)); d = ImageDraw.Draw(sh); d.fontmode = '1'
d.text((12, 8), 'CORNER PLAYBACK', font=font(20, True), fill=WHITE); d.text((200, 12), 'PROPOSAL  /  UNAPPROVED  /  PLAYER  NEU > DEF > ATK   vs   RIVAL  ATK > ATK > DEF', font=font(13), fill=DIM)
slots = []
for r_, (label, frames) in enumerate((('A  LINE VS LINE', A), ('B  CLASH BEATS', Bf))):
    y = 40 + r_ * 534
    tab = [(10, y), (196, y), (208, y + 22), (10, y + 22)]; d.polygon(tab, fill=AMBER); d.rectangle((10, y, 34, y + 22), fill=INK)
    d.text((22, y + 11), label[0], font=font(19, True), fill=AMBER, anchor='mm'); d.text((42, y + 11), label[3:], font=font(15, True), fill=INK, anchor='lm')
    d.line([(212, y + 21), (W - 10, y + 21)], fill=EDGE)
    for i, f in enumerate(frames):
        x = 10 + i * 650; d.text((x + 4, y + 30), f'{i + 1}  {PHASES[i]}', font=font(13, True), fill=AMBER if True else WHITE)
        slots.append((f, (x, y + 48)))
q = Image.fromarray(rgb555(np.asarray(sh).astype(np.float32)))
for f, xy in slots: q.paste(f, xy)
q.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(OUT, 'line_clash_comparison_sheet.png'))
print('post ok', RES)
