#!/usr/bin/env python3
"""districts_sheet.png: touge / street / wangan side by side (each 1280x960 frame box-halved to 640x480), labelled."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'godot', 'fonts', 'ArchivoBlack-Regular.ttf')
F2 = os.path.join(HERE, 'godot', 'fonts', 'NimbusSans-Bold.otf')
ROWS = [('touge', 'TOUGE', 'road 6.0 m, 2 narrow lanes, no lane lines'),
        ('street', 'STREET', 'road 8.4 m, 2 lanes + kerbs, lane lines'),
        ('wangan', 'WANGAN', 'road 11.9 m (E3B road as is), 3 lanes, lane lines')]
W, H, PAD, TOP = 640, 480, 12, 58
sheet = Image.new('RGB', (PAD + len(ROWS) * (W + PAD), TOP + H + PAD), (11, 23, 43))
d = ImageDraw.Draw(sheet)
f1 = ImageFont.truetype(F, 22); f2 = ImageFont.truetype(F2, 15)
for i, (k, name, sub) in enumerate(ROWS):
    im = Image.open(os.path.join(HERE, k + '.png')).convert('RGB').resize((W, H), Image.BOX)
    x = PAD + i * (W + PAD)
    sheet.paste(im, (x, TOP))
    d.rectangle([x - 1, TOP - 1, x + W, TOP + H], outline=(110, 127, 151))
    d.text((x, 8), name, font=f1, fill=(240, 200, 40))
    d.text((x, 36), sub, font=f2, fill=(210, 216, 226))
sheet.save(os.path.join(HERE, 'districts_sheet.png')); print('sheet', sheet.size)

# consistency_sheet.png: touge mouse / touge cat / street / wangan, 2x2, same HUD, chevrons, palette and camera family
CELLS = [('touge_mouse', 'TOUGE - MOUSE (leading)', 'rival 6.5 m behind: beams on road + car, rear view, gap bar'),
         ('touge_cat', 'TOUGE - CAT (chasing)', 'rival 11 m ahead in the chevrons, taillights'),
         ('street', 'STREET', 'standard Entry chase'),
         ('wangan', 'WANGAN', 'standard Entry chase')]
cs = Image.new('RGB', (PAD + 2 * (W + PAD), 2 * (TOP + H) + PAD), (11, 23, 43))
d = ImageDraw.Draw(cs)
for i, (k, name, sub) in enumerate(CELLS):
    im = Image.open(os.path.join(HERE, k + '.png')).convert('RGB').resize((W, H), Image.BOX)
    x = PAD + (i % 2) * (W + PAD); y = (i // 2) * (TOP + H)
    cs.paste(im, (x, y + TOP))
    d.rectangle([x - 1, y + TOP - 1, x + W, y + TOP + H], outline=(110, 127, 151))
    d.text((x, y + 8), name, font=f1, fill=(240, 200, 40))
    d.text((x, y + 36), sub, font=f2, fill=(210, 216, 226))
cs.save(os.path.join(HERE, 'consistency_sheet.png')); print('consistency', cs.size)

# mouse_options_sheet.png: 3 mouse-view options (columns) x 2 gaps (rows: ~10 m, ~24 m)
OPTS = [('mouse_bigmirror', 'A  BIG MIRROR', 'standard chase cam, rear view 2x'),
        ('mouse_lookback', 'B  LOOK BACK', 'reverse cam at the tail, AHEAD inset'),
        ('mouse_highcam', 'C  HIGH CAM', 'higher, steeper chase, both cars on screen')]
GAPS = [('', 'gap ~10 m (+0.40 s)'), ('_far', 'gap ~24 m (+0.96 s)')]
ms = Image.new('RGB', (PAD + 3 * (W + PAD), 2 * (TOP + H) + PAD), (11, 23, 43))
d = ImageDraw.Draw(ms)
for r, (suf, gl) in enumerate(GAPS):
    for c, (k, name, sub) in enumerate(OPTS):
        im = Image.open(os.path.join(HERE, k + suf + '.png')).convert('RGB').resize((W, H), Image.BOX)
        x = PAD + c * (W + PAD); y = r * (TOP + H)
        ms.paste(im, (x, y + TOP))
        d.rectangle([x - 1, y + TOP - 1, x + W, y + TOP + H], outline=(110, 127, 151))
        d.text((x, y + 8), name, font=f1, fill=(240, 200, 40))
        d.text((x, y + 36), sub + '  |  ' + gl, font=f2, fill=(210, 216, 226))
ms.save(os.path.join(HERE, 'mouse_options_sheet.png')); print('mouse options', ms.size)
