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
