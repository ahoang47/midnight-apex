#!/usr/bin/env python3
"""1x3 comparison: touge_cat (6.0 m, reference) | wangan_tight_cat (7.5 m) | street_tight_cat (5.8 m), Cel A soft."""
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(H, 'godot', 'fonts', 'NimbusSansNarrow-Bold.otf')
def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except OSError: return ImageFont.load_default()
COLS = [('touge_cat.png', 'TOUGE  6.0 m  (unchanged, reference)'), ('wangan_tight_cat.png', 'WANGAN  7.5 m  (was 11.9 m, 3 lanes)'),
        ('street_tight_cat.png', 'STREET  5.8 m  (was 8.4 m)')]
W, Hh, top = 960, 720, 56
sh = Image.new('RGB', (3 * W + 2 * 12, top + Hh + 40), (11, 23, 43)); d = ImageDraw.Draw(sh)
for i, (f, lab) in enumerate(COLS):
    x = i * (W + 12)
    d.text((x + 10, 12), lab, font=font(34), fill=(220, 228, 240))
    sh.paste(Image.open(os.path.join(H, f)).convert('RGB').resize((W, Hh), Image.LANCZOS), (x, top))
d.text((10, top + Hh + 8), 'Cat and mouse, CAT (chasing) view, Cel A soft, Godot 4.6.3 GL Compatibility: 3D 640x480 RGB555 + Bayer, HUD 1280x960. Rival 11 m ahead in the player line.',
       font=font(24), fill=(150, 165, 190))
sh.save(os.path.join(H, 'tight_districts_sheet.png')); print('sheet written')
