"""Phase 4 composites (Godot only): before/after, tones mockups, Plan the Line sheet, build vs Arthur's lane_chain/v5 mockups.

Paths are relative to the two-corner root (this file lives in tools/). Regenerating
composites still needs the full out/shots3 and out/shots4 frame sets, which are not
in the unapproved/gordon/two-corner copy — only the three key composites are kept.
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
O = str(ROOT / 'out'); B = f'{O}/shots3/godot_seed20261113_idx'; A = f'{O}/shots4/godot_seed20261113_idx'; C = f'{O}/shots4/composites'
F = ImageFont.truetype('/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf', 18)
def im(p, w=640, h=480): return Image.open(p).convert('RGB').resize((w, h), Image.NEAREST if w >= 640 else Image.LANCZOS)
def sheet(rows, labels, name, w=640, h=480):
    cols = max(len(r) for r in rows); W = Image.new('RGB', (cols * w, len(rows) * (h + 26)), (12, 12, 18)); d = ImageDraw.Draw(W)
    for ri, r in enumerate(rows):
        for ci, p in enumerate(r):
            if p is None: continue
            W.paste(im(p, w, h), (ci * w, ri * (h + 26) + 26)); d.text((ci * w + 6, ri * (h + 26) + 3), labels[ri][ci], font=F, fill=(230, 230, 240))
    W.save(f'{C}/{name}'); print(name, W.size)
shots = [('seq_select0_2', 'selection corner 1 (Touge)'), ('seq_select1_2', 'selection corner 2 (Street)'), ('seq_corner0_4', 'corner 1 camera'),
         ('seq_corner1_4', 'corner 2 camera'), ('finish', 'finish')]
sheet([[f'{B}/{s}_640.png', f'{A}/{s}_640.png'] for s, _ in shots], [[f'BEFORE (shots3) {l}', f'AFTER (shots4) {l}'] for _, l in shots], 'before_after.png')
T = '/workspace/mockups/tones'
sheet([[f'{T}/entry_blend50.png', f'{A}/seq_select1_2_640.png', f'{A}/seq_select0_2_640.png'],
       [f'{T}/overworld_blend50.png', f'{A}/seq_corner1_4_640.png', f'{A}/seq_corner0_4_640.png']],
      [['tones.py blend50: entry_blend50.png', 'build: Street selection', 'build: Touge selection'],
       ['tones.py blend50: overworld_blend50.png', 'build: Street corner cam', 'build: Touge corner cam']], 'vs_tones_blend50.png')
sheet([[f'{A}/seq_select0_2_640.png', f'{A}/plan_apex0_640.png', f'{A}/plan_exit0_640.png', f'{A}/seq_corner0_4_640.png', f'{A}/result0_640.png'],
       [f'{A}/seq_select1_2_640.png', f'{A}/plan_apex1_640.png', f'{A}/plan_exit1_640.png', f'{A}/seq_corner1_4_640.png', f'{A}/result1_640.png']],
      [['C1 entry phase', 'C1 apex phase', 'C1 exit phase', 'C1 LINE LOCKED (playback)', 'C1 strip with clash results'],
       ['C2 entry phase', 'C2 apex phase', 'C2 exit phase', 'C2 LINE LOCKED (playback)', 'C2 strip with clash results']], 'plan_the_line_sheet.png')
M = '/workspace/mockups/lane_chain/v5'
sheet([[f'{M}/entry_plan.png', f'{A}/plan_apex1_640.png', f'{A}/plan_apex0_640.png'], [f'{M}/apex_replay.png', f'{A}/seq_corner1_4_640.png', f'{A}/seq_corner0_4_640.png']],
      [['Arthur mockup: entry_plan.png', 'build: Street, apex phase', 'build: Touge, apex phase'], ['Arthur mockup: apex_replay.png', 'build: Street playback strip', 'build: Touge playback strip']],
      'vs_lane_chain_v5.png')
# native 2x crops of the HUD blocks
a = Image.open(f'{A}/plan_apex0_640.png').convert('RGB'); m = Image.open(f'{M}/raw/native_entry_plan.png').convert('RGB') if os.path.exists(f'{M}/raw/native_entry_plan.png') else Image.open(f'{M}/entry_plan.png').convert('RGB').resize((640, 480), Image.NEAREST)
W = Image.new('RGB', (1280, 720)); W.paste(m.crop((0, 300, 640, 480)).resize((1280, 360), Image.NEAREST), (0, 0)); W.paste(a.crop((0, 300, 640, 480)).resize((1280, 360), Image.NEAREST), (0, 360)); W.save(f'{C}/hud_crop_plan_vs_mockup.png')
