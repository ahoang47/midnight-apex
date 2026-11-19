#!/usr/bin/env python3
"""Before/after + mood-reference composites for the art pass. usage: art_composites.py <before_root> <after_root> <pin_worktree> <outdir>"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
before, after, pin, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
CW, CH = 480, 360
FRAMES = [('seq_select0_2', 'selection, corner 1 (Touge HP)'), ('seq_corner0_4', 'corner cam, hairpin'), ('seq_select1_5', 'selection, corner 2 (Street N90)'),
          ('seq_corner1_4', 'corner cam, 90-degree'), ('finish', 'finish')]
def cell(p):
    if not os.path.exists(p): im = Image.new('RGB', (CW, CH), (40, 0, 40)); ImageDraw.Draw(im).text((10, 10), 'missing', font=F, fill=(255, 255, 255)); return im
    return Image.open(p).convert('RGB').resize((CW, CH), Image.LANCZOS)
def sheet(rows, cols, title, name):
    W = 10 + len(cols) * (CW + 10); H = 40 + len(rows) * (CH + 34)
    S = Image.new('RGB', (W, H), (14, 12, 22)); d = ImageDraw.Draw(S); d.text((10, 10), title, font=F, fill=(235, 235, 235))
    for r, (label, paths) in enumerate(rows):
        y = 40 + r * (CH + 34)
        for c, p in enumerate(paths):
            x = 10 + c * (CW + 10); S.paste(cell(p), (x, y + 20)); d.text((x, y + 2), f'{cols[c]}  |  {label}' if c == 0 else cols[c], font=F, fill=(200, 200, 210))
    S.save(os.path.join(out, name)); return os.path.join(out, name)
made = []
for eng in ('threejs', 'godot'):
    b = os.path.join(before, f'{eng}_seed20261113_idx'); a = os.path.join(after, f'{eng}_seed20261113_idx')
    rows = [(lab, [os.path.join(b, f'{f}_low.png'), os.path.join(b, f'{f}_crt.png'), os.path.join(a, f'{f}_640.png')]) for f, lab in FRAMES]
    made.append(sheet(rows, ['BEFORE low 320x240', 'BEFORE crt 640x480', 'AFTER 640x480 RGB555'], f'{eng}: before vs after art pass (seed 20261113)', f'before_after_{eng}.png'))
mood = os.path.join(pin, 'art/mood')
refs = [os.path.join(mood, 'tokyo_v2/renders/original_800/tokyo_v2_2_rear34_800.jpg'), os.path.join(mood, 'tokyo_mx5/renders/mx5_tokyo_rear34_800.jpg'),
        os.path.join(mood, 'tokyo_v2/renders/original_800/tokyo_v2_3_establishing_800.jpg')]
for eng in ('threejs', 'godot'):
    a = os.path.join(after, f'{eng}_seed20261113_idx')
    rows = [('Street (B.3: Tokyo v2 palette as start)', [refs[0], refs[1], os.path.join(a, 'seq_select1_5_640.png'), os.path.join(a, 'seq_corner1_4_640.png')]),
            ('Touge (B.3 text only; no mood render exists)', [refs[2], os.path.join(mood, 'tokyo_v2/renders/style_reference.png'), os.path.join(a, 'seq_select0_2_640.png'), os.path.join(a, 'seq_corner0_4_640.png')])]
    made.append(sheet(rows, ['MOOD tokyo_v2', 'MOOD tokyo_mx5 / style ref', f'AFTER {eng}', f'AFTER {eng}'], f'{eng}: after vs art/mood references (vibe check, non-binding)', f'mood_vs_{eng}.png'))
# engine vs engine
a1 = os.path.join(after, 'threejs_seed20261113_idx'); a2 = os.path.join(after, 'godot_seed20261113_idx')
made.append(sheet([(lab, [os.path.join(a1, f'{f}_640.png'), os.path.join(a2, f'{f}_640.png')]) for f, lab in FRAMES], ['Three.js', 'Godot'], 'after: Three.js vs Godot (seed 20261113)', 'engines_after.png'))
for m in made: print(m)
