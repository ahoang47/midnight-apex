# shots9: HUD text pixel-hard on a 2x grid (1280x960). Before = shots8 smooth window-resolution HUD (85d505d), after = shots9.
# Usage: python3 tools/shots9_composite.py  (reads out/shots8/after_live and out/shots9/after_live)
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
R = 'out/shots9'
SRC = {'before': 'out/shots8/after_live', 'after': 'out/shots9/after_live'}
f = ImageFont.truetype('/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf', 26)
def load(state, size, shot):
    im = Image.open(f'{SRC[state]}/{size}/{shot}.png').convert('RGB'); a = np.asarray(im).sum(2)
    ys, xs = np.where(a > 0); x0, y0 = xs.min(), ys.min(); sc = (ys.max() - y0 + 1) / 480.0   # game canvas inside the black bars
    return im, x0, y0, sc
def crop(state, size, shot, box, k=1):
    im, ox, oy, sc = load(state, size, shot); x0, y0, x1, y1 = box
    c = im.crop((round(ox + x0 * sc), round(oy + y0 * sc), round(ox + x1 * sc), round(oy + y1 * sc)))
    return c.resize((c.width * k, c.height * k), Image.NEAREST)
def pair(tiles_title, b, a, la, lb):
    W = b.width + a.width + 30; H = max(b.height, a.height) + 44
    t = Image.new('RGB', (W, H), (5, 10, 19)); d = ImageDraw.Draw(t)
    d.text((6, 6), la, font=f, fill=(255, 176, 40)); d.text((b.width + 30, 6), lb, font=f, fill=(44, 184, 74))
    t.paste(b, (0, 40)); t.paste(a, (b.width + 30, 40)); return t
def stack(tiles, path):
    W = max(t.width for t in tiles); H = sum(t.height + 12 for t in tiles); o = Image.new('RGB', (W, H), (5, 10, 19)); y = 0
    for t in tiles: o.paste(t, (0, y)); y += t.height + 12
    o.save(path); print(path, o.size)
# 1) 1920x1080 before/after, full window
b = Image.open(f"{SRC['before']}/1920x1080/2_plan_apex.png").convert('RGB'); a = Image.open(f"{SRC['after']}/1920x1080/2_plan_apex.png").convert('RGB')
stack([pair('', b, a, 'BEFORE (85d505d): smooth HUD at window resolution', 'AFTER: pixel-hard HUD on 1280x960 grid')], f'{R}/composite_before_after_1920x1080_full.png')
# 2) 1920x1080 text areas at 2x zoom (screen pixels doubled)
rows = [('2_plan_apex', (404, 312, 632, 472), 'Plan the Line'), ('6_playback_b', (118, 8, 636, 104), 'B.5a line vs line + corner plate'),
        ('4_line_locked', (8, 6, 420, 160), 'Timer, debug HUD, LINE LOCKED'), ('7_result', (180, 395, 460, 472), 'Timing bar + gap meter')]
stack([pair('', crop('before', '1920x1080', s, bx, 2), crop('after', '1920x1080', s, bx, 2), f'{n}: BEFORE (2x zoom)', 'AFTER (2x zoom)') for s, bx, n in rows],
      f'{R}/composite_before_after_1920x1080_zoom2x.png')
# 3) after, Plan panel + B.5a panel at every window size (true screen pixels)
for s, bx, n in rows[:2]:
    stack([pair('', crop('before', sz, s, bx), crop('after', sz, s, bx), f'{sz} BEFORE', f'{sz} AFTER') for sz in ['1366x768', '1280x960', '1920x1080', '2560x1440']],
          f'{R}/composite_sizes_{s}.png')
