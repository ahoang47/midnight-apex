#!/usr/bin/env python3
"""Frames + sheets for the Wangan two-corner playtest. Reads the key shots of ./run.sh playtest ($OUT/on, $OUT/off) and writes
frames/<name>.png (cel A soft, full 1280x960), frames/cel_off/<name>.png, the contact sheet (cel on, 3x3) and the
cel off / on compare sheet."""
import os, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.environ.get('OUT', '/tmp/wtc')
FONT = os.path.join(H, 'godot', 'fonts', 'NimbusSansNarrow-Bold.otf')
def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except OSError: return ImageFont.load_default()
BG = (11, 23, 43); TX = (220, 228, 240)
SHOTS = [('c1_sw_entry_select', 'seq_select0_0'), ('c1_sw_apex_stop', 'plan_apex0'), ('c1_sw_exit_stop', 'plan_exit0'),
         ('c1_sw_playback_apex', 'seq_corner0_3'), ('c2_ir_entry_select', 'seq_select1_0'), ('c2_ir_apex_stop', 'plan_apex1'),
         ('c2_ir_exit_stop', 'plan_exit1'), ('c2_ir_playback_apex', 'seq_corner1_3'), ('finish', 'finish')]
os.makedirs(f'{H}/frames/cel_off', exist_ok=True)
for nm, src in SHOTS:
    shutil.copy(f'{OUT}/on/{src}_640.png', f'{H}/frames/{nm}.png'); shutil.copy(f'{OUT}/off/{src}_640.png', f'{H}/frames/cel_off/{nm}.png')
img = lambda p: Image.open(p).convert('RGB')
W, Hh, top = 640, 480, 44
cs = Image.new('RGB', (3 * W, top + 3 * (Hh + 30)), BG); d = ImageDraw.Draw(cs)
d.text((10, 8), 'WANGAN TWO-CORNER PLAYTEST  Cel A soft  seed 3  (SW sweeper L, IR increasing radius R)', font=font(28), fill=TX)
for i, (nm, _) in enumerate(SHOTS):
    x, y = (i % 3) * W, top + (i // 3) * (Hh + 30)
    d.text((x + 8, y + 2), nm.replace('_', ' '), font=font(22), fill=TX)
    cs.paste(img(f'{H}/frames/{nm}.png').resize((W, Hh), Image.LANCZOS), (x, y + 28))
cs.save(f'{H}/wangan_two_corner_contact_sheet.png')
lab = 230; sh = Image.new('RGB', (lab + 2 * W, top + len(SHOTS) * Hh), BG); d = ImageDraw.Draw(sh)
d.text((lab, 8), 'CEL OFF (Gordon renderer, same frame)', font=font(26), fill=TX); d.text((lab + W, 8), 'CEL A SOFT', font=font(26), fill=TX)
for i, (nm, _) in enumerate(SHOTS):
    y = top + i * Hh; d.text((10, y + 10), nm.replace('_', ' '), font=font(22), fill=TX)
    sh.paste(img(f'{H}/frames/cel_off/{nm}.png').resize((W, Hh), Image.LANCZOS), (lab, y)); sh.paste(img(f'{H}/frames/{nm}.png').resize((W, Hh), Image.LANCZOS), (lab + W, y))
sh.save(f'{H}/wangan_two_corner_compare_sheet.png')
if os.path.exists(f'{H}/playtest/mirror_check.png'): shutil.copy(f'{H}/playtest/mirror_check.png', f'{H}/frames/mirror_check.png')
print('sheets written')
