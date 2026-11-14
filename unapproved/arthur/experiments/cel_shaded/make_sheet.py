#!/usr/bin/env python3
"""cel_compare_sheet.png: per district (rows) the current frame, cel + PSX dither (A) and clean cel (B), each
1280x960 frame box-halved to 640x480, labelled. Originals are read from ../../mockups/districts (not modified)."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, '..', '..', 'mockups', 'districts')
F = os.path.join(ORIG, 'godot', 'fonts', 'ArchivoBlack-Regular.ttf')
F2 = os.path.join(ORIG, 'godot', 'fonts', 'NimbusSans-Bold.otf')
ROWS = [('touge', 'TOUGE'), ('street', 'STREET'), ('wangan', 'WANGAN')]
COLS = [(lambda k: os.path.join(ORIG, k + '.png'), 'CURRENT', 'unlit PSX look, RGB555 + Bayer'),
        (lambda k: os.path.join(HERE, k + '_cel.png'), 'CEL  A', '3-band ramp + ink + flatten, RGB555 + Bayer kept'),
        (lambda k: os.path.join(HERE, k + '_cel_clean.png'), 'CEL  B', 'same cel pass, no dither')]
W, H, PAD, TOP = 640, 480, 12, 58
sheet = Image.new('RGB', (PAD + len(COLS) * (W + PAD), len(ROWS) * (TOP + H) + PAD), (11, 23, 43))
d = ImageDraw.Draw(sheet)
f1 = ImageFont.truetype(F, 22); f2 = ImageFont.truetype(F2, 15)
for r, (k, name) in enumerate(ROWS):
    for c, (path, cname, sub) in enumerate(COLS):
        im = Image.open(path(k)).convert('RGB').resize((W, H), Image.BOX)
        x = PAD + c * (W + PAD); y = r * (TOP + H)
        sheet.paste(im, (x, y + TOP))
        d.rectangle([x - 1, y + TOP - 1, x + W, y + TOP + H], outline=(110, 127, 151))
        d.text((x, y + 8), name + '  -  ' + cname, font=f1, fill=(240, 200, 40))
        d.text((x, y + 36), sub, font=f2, fill=(210, 216, 226))
sheet.save(os.path.join(HERE, 'cel_compare_sheet.png')); print('sheet', sheet.size)
