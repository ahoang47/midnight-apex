#!/usr/bin/env python3
"""Compare sheet + playtest evidence for the Cel A two-corner port. Inputs: frames/cel_on, frames/cel_off (this folder) and,
for the motion/mirror/HUD checks, a playtest frame dump (GIF_ON / GIF_OFF / GIF_INK dirs, default /tmp/ctc/gif_*)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(H, 'godot', 'fonts', 'NimbusSansNarrow-Bold.otf')
def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except OSError: return ImageFont.load_default()
BG = (11, 23, 43); TX = (220, 228, 240)
def img(p): return Image.open(p).convert('RGB')
rows = ['c1_01_entry_select', 'c1_02_apex_stop', 'c1_06_playback', 'c2_06_playback', 'finish']
W, Hh, top, lab = 640, 480, 44, 150
sh = Image.new('RGB', (lab + 2 * W, top + len(rows) * Hh), BG); d = ImageDraw.Draw(sh)
d.text((lab, 8), 'CEL OFF (Gordon, as built)', font=font(26), fill=TX); d.text((lab + W, 8), 'CEL A ON (same game frame)', font=font(26), fill=TX)
for i, r in enumerate(rows):
    y = top + i * Hh
    d.text((10, y + 10), r.replace('_', ' '), font=font(20), fill=TX)
    sh.paste(img(f'{H}/frames/cel_off/{r}.png').resize((W, Hh), Image.LANCZOS), (lab, y))
    sh.paste(img(f'{H}/frames/cel_on/{r}.png').resize((W, Hh), Image.LANCZOS), (lab + W, y))
sh.save(f'{H}/cel_two_corner_compare_sheet.png')
G = {k: os.environ.get('GIF_' + k.upper(), f'/tmp/ctc/gif_{k}') for k in ('on', 'off', 'ink')}
if not os.path.isdir(G['on']): raise SystemExit('compare sheet only (no frame dump for the playtest checks)')
fr = lambda k, f: img(f"{G[k]}/f{f:05d}.png")
# mirror check: rear-view inset, off / on, x3 nearest (frame 60, Entry straight)
box = (440, 24, 840, 168); out = Image.new('RGB', ((box[2] - box[0]) * 3, (box[3] - box[1]) * 6 + 40), BG); d = ImageDraw.Draw(out)
for j, k in enumerate(('off', 'on')):
    out.paste(fr(k, 60).crop(box).resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3), Image.NEAREST), (0, 40 + j * (box[3] - box[1]) * 3))
d.text((8, 8), 'REAR VIEW x3: top cel off, bottom cel A (ink from the rear-view G-buffer, flipped with the colour)', font=font(24), fill=TX)
out.save(f'{H}/playtest/mirror_check.png')
# HUD check: green = pixel identical cel on vs off, red = differs (frame 60)
a = np.asarray(fr('on', 60)).astype(int); b = np.asarray(fr('off', 60)).astype(int)
same = (a == b).all(2); vis = np.zeros_like(a); vis[..., 1] = same * 140; vis[..., 0] = (~same) * 255
Image.fromarray(vis.astype(np.uint8)).save(f'{H}/playtest/hud_check.png')
# motion strip: 6 consecutive 30 fps frames, Entry straight scroll, mid-distance rail + cedars, x2 nearest, off over on
def strip(f0, box, n=6, z=2):
    w, h = box[2] - box[0], box[3] - box[1]
    o = Image.new('RGB', (w * z * n, h * z * 2 + 40), BG); dd = ImageDraw.Draw(o)
    dd.text((8, 8), f'frames {f0}-{f0 + n - 1} (30 fps), top cel off, bottom cel A', font=font(24), fill=TX)
    for j, k in enumerate(('off', 'on')):
        for i in range(n): o.paste(fr(k, f0 + i).crop(box).resize((w * z, h * z), Image.NEAREST), (i * w * z, 40 + j * h * z))
    return o
strip(100, (0, 380, 260, 620)).save(f'{H}/playtest/motion_entry_rail.png')
strip(1300, (300, 300, 620, 560), n=4).save(f'{H}/playtest/motion_c2_car_road.png')
print('sheets written')
