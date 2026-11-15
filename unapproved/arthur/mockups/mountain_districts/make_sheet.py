#!/usr/bin/env python3
"""3x3 mountain-districts sheet: rows touge / wangan / street, cols entry lane OUT / MID / IN, CAT (chasing) view, Cel A soft.
  python3 make_sheet.py        -> mountain_districts_sheet.png (v1)
  python3 make_sheet.py v2     -> mountain_districts_sheet_v2.png + mountain_districts_v1_v2_mid.png (pass 2)
  python3 make_sheet.py v3     -> mountain_districts_sheet_v3.png + mountain_districts_v2_v3_mid.png (pass 3)"""
import os, sys
ARG = sys.argv[1] if len(sys.argv) > 1 else ''
V3 = ARG == 'v3'
V2 = ARG == 'v2'
SUF = '_' + ARG if ARG else ''
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(H, 'godot', 'fonts', 'NimbusSansNarrow-Bold.otf')
def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except OSError: return ImageFont.load_default()
ROWS3 = [('touge', 'TOUGE', '6.0 m', '11.5-12.5 %'), ('wangan', 'WANGAN  mountain skyline', '7.5 m', '9-10 %'),
         ('street', 'STREET  hillside city', '5.8 m', '11-13 %')]
ROWS = [('touge', 'TOUGE', '6.0 m', ('8.5-9.5 %' if V2 else '8.5 % climb\n(unchanged)')),
        ('wangan', 'WANGAN  mountain skyline', '7.5 m', '6-8 %'),
        ('street', ('STREET  hillside city' if V2 else 'STREET  hillside onsen town'), '5.8 m', '8-10 %')]
if V3: ROWS = ROWS3
COLS = [('out', 'OUT  (A / POW)'), ('mid', 'MID  (S / HAN)'), ('in', 'IN  (D / EN)')]
W, Hh, G, LW, top = 640, 480, 10, 250, 52
sh = Image.new('RGB', (LW + 3 * W + 2 * G, top + 3 * Hh + 2 * G + 44), (11, 23, 43)); d = ImageDraw.Draw(sh)
for j, (_, lab) in enumerate(COLS):
    d.text((LW + j * (W + G) + 10, 10), lab, font=font(32), fill=(220, 228, 240))
for i, (k, name, w, g) in enumerate(ROWS):
    y = top + i * (Hh + G)
    d.multiline_text((12, y + 12), '\n'.join(name.split('  ')), font=font(30), fill=(220, 228, 240), spacing=6)
    d.multiline_text((12, y + 110), 'road %s\ngrade %s' % (w, g), font=font(26), fill=(240, 200, 148), spacing=8)
    for j, (c, _) in enumerate(COLS):
        im = Image.open(os.path.join(H, '%s_%s_cat%s.png' % (k, c, SUF))).convert('RGB').resize((W, Hh), Image.LANCZOS)
        sh.paste(im, (LW + j * (W + G), y))
d.text((12, top + 3 * Hh + 2 * G + 10), 'Cat and mouse, CAT (chasing) view per entry lane, rival 11 m ahead in the same line. Cel A soft, Godot 4.6.3 GL Compatibility: 3D 640x480 RGB555 + Bayer, HUD 1280x960.',
       font=font(22), fill=(150, 165, 190))
sh.save(os.path.join(H, 'mountain_districts_sheet%s.png' % SUF)); print('sheet written')
if V2:   # v1 vs v2, MID lane, one row per district
    W2, H2 = 800, 600
    st = Image.new('RGB', (LW + 2 * W2 + G, top + 3 * H2 + 2 * G + 44), (11, 23, 43)); d = ImageDraw.Draw(st)
    for j, lab in enumerate(['v1  (commit e906682)', 'v2  (pass 2: perspective, hillside city)']):
        d.text((LW + j * (W2 + G) + 10, 10), lab, font=font(32), fill=(220, 228, 240))
    for i, (k, name, w, g) in enumerate(ROWS):
        y = top + i * (H2 + G)
        d.multiline_text((12, y + 12), '\n'.join(name.split('  ')), font=font(30), fill=(220, 228, 240), spacing=6)
        g2 = 'v1 8.5 %\nv2 8.5-9.5 %' if k == 'touge' else g
        d.multiline_text((12, y + 110), 'MID lane\nroad %s\ngrade %s' % (w, g2), font=font(26), fill=(240, 200, 148), spacing=8)
        for j, f in enumerate(['%s_mid_cat.png' % k, '%s_mid_cat_v2.png' % k]):
            st.paste(Image.open(os.path.join(H, f)).convert('RGB').resize((W2, H2), Image.LANCZOS), (LW + j * (W2 + G), y))
    d.text((12, top + 3 * H2 + 2 * G + 10), 'v2 chase: same B.5b family, 2.45 m up (was 3.1), 47 deg lens (was 56.7), aimed 34 m up the road (was 22 m).', font=font(22), fill=(150, 165, 190))
    st.save(os.path.join(H, 'mountain_districts_v1_v2_mid.png')); print('strip written')
if V3:   # v2 vs v3, MID lane, one row per district
    W2, H2 = 800, 600; G2 = {'touge': ('8.5-9.5 %', '11.5-12.5 %'), 'wangan': ('6-8 %', '9-10 %'), 'street': ('8-10 %', '11-13 %')}
    st = Image.new('RGB', (LW + 2 * W2 + G, top + 3 * H2 + 2 * G + 44), (11, 23, 43)); d = ImageDraw.Draw(st)
    for j, lab in enumerate(['v2  (commit 669d864)', 'v3  (pass 3: steeper, Wangan cut)']):
        d.text((LW + j * (W2 + G) + 10, 10), lab, font=font(32), fill=(220, 228, 240))
    for i, (k, name, w, g) in enumerate(ROWS):
        y = top + i * (H2 + G)
        d.multiline_text((12, y + 12), '\n'.join(name.split('  ')), font=font(30), fill=(220, 228, 240), spacing=6)
        d.multiline_text((12, y + 110), 'MID lane\nroad %s\ngrade\nv2 %s\nv3 %s' % (w, G2[k][0], G2[k][1]), font=font(26), fill=(240, 200, 148), spacing=8)
        for j, f in enumerate(['%s_mid_cat_v2.png' % k, '%s_mid_cat_v3.png' % k]):
            st.paste(Image.open(os.path.join(H, f)).convert('RGB').resize((W2, H2), Image.LANCZOS), (LW + j * (W2 + G), y))
    d.text((12, top + 3 * H2 + 2 * G + 10), 'v3 chase: same pose and lens as v2; pitch follows half the climb, so the grade reads against plumb walls and the horizon.', font=font(22), fill=(150, 165, 190))
    st.save(os.path.join(H, 'mountain_districts_v2_v3_mid.png')); print('strip written')
