"""Phase 5 composites (Godot only; paths relative to the two-corner root, needs the full out/shots4 + out/shots5 frame sets): build frames next to Arthur's approved B.5b (art/ui/line_select_cam) and B.5a (art/ui/line_vs_line)
reference frames, before/after vs Phase 4, and full-corner GIFs.  python3 tools/phase5_composites.py [midnight-apex clone]"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = sys.argv[1] if len(sys.argv) > 1 else '/workspace/midnight-apex'
O = os.path.join(ROOT, 'out'); A = f'{O}/shots5/godot_seed20261113_idx'; B4 = f'{O}/shots4/godot_seed20261113_idx'; C = f'{O}/shots5/composites'; os.makedirs(C, exist_ok=True)
LSC = f'{REPO}/art/ui/line_select_cam'; LVL = f'{REPO}/art/ui/line_vs_line'
F = ImageFont.truetype('/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf', 18)
def im(p, w=640, h=480): return Image.open(p).convert('RGB').resize((w, h), Image.NEAREST)
def sheet(rows, labels, name, w=640, h=480):
    cols = max(len(r) for r in rows); W = Image.new('RGB', (cols * w, len(rows) * (h + 26)), (12, 12, 18)); d = ImageDraw.Draw(W)
    for ri, r in enumerate(rows):
        for ci, p in enumerate(r):
            W.paste(im(p, w, h), (ci * w, ri * (h + 26) + 26)); d.text((ci * w + 6, ri * (h + 26) + 3), labels[ri][ci], font=F, fill=(230, 230, 240))
    W.save(f'{C}/{name}', optimize=True); print(name, W.size, os.path.getsize(f'{C}/{name}') // 1024, 'KB')
sheet([[f'{LSC}/1_entry_pick.png', f'{A}/seq_select0_2_640.png', f'{A}/seq_select1_2_640.png'],
       [f'{LSC}/2_apex_pick.png', f'{A}/plan_apex0_640.png', f'{A}/plan_apex1_640.png'],
       [f'{LSC}/3_exit_pick.png', f'{A}/plan_exit0_640.png', f'{A}/plan_exit1_640.png'],
       [f'{LSC}/4_line_locked.png', f'{A}/seq_lock0_2_640.png', f'{A}/seq_lock1_2_640.png']],
      [['Arthur B.5b 1_entry_pick', 'Godot C1 Touge HP L: Entry stop (chase, rival in lane)', 'Godot C2 Street N90 R: Entry stop'],
       ['Arthur B.5b 2_apex_pick', 'Godot C1: Apex stop (no cars)', 'Godot C2: Apex stop'],
       ['Arthur B.5b 3_exit_pick', 'Godot C1: Exit stop (no cars)', 'Godot C2: Exit stop'],
       ['Arthur B.5b 4_line_locked', 'Godot C1: back at Entry, LINE LOCKED', 'Godot C2: LINE LOCKED']], 'vs_line_select_cam.png')
sheet([[f'{LVL}/a1_entry_line_vs_line.png', f'{A}/seq_corner0_1_640.png', f'{A}/seq_corner1_1_640.png'],
       [f'{LVL}/a2_apex_line_vs_line.png', f'{A}/seq_corner0_4_640.png', f'{A}/seq_corner1_4_640.png'],
       [f'{LVL}/a3_exit_line_vs_line.png', f'{A}/seq_corner0_6_640.png', f'{A}/seq_corner1_6_640.png']],
      [['Arthur B.5a a1 entry', 'Godot C1 playback: ENTRY', 'Godot C2 playback: ENTRY'],
       ['Arthur B.5a a2 apex', 'Godot C1 playback: APEX', 'Godot C2 playback: APEX'],
       ['Arthur B.5a a3 exit', 'Godot C1 playback: EXIT', 'Godot C2 playback: EXIT']], 'vs_line_vs_line.png')
sheet([[f'{B4}/seq_select0_2_640.png', f'{A}/seq_select0_2_640.png'], [f'{B4}/plan_apex0_640.png', f'{A}/plan_apex0_640.png'],
       [f'{B4}/seq_corner0_4_640.png', f'{A}/seq_corner0_4_640.png'], [f'{B4}/result0_640.png', f'{A}/result0_640.png'], [f'{B4}/finish_640.png', f'{A}/finish_640.png']],
      [['PHASE 4 selection C1', 'PHASE 5 Entry stop C1'], ['PHASE 4 apex phase (still on the straight)', 'PHASE 5 Apex stop C1'],
       ['PHASE 4 playback strip', 'PHASE 5 B.5a LINE LOCKED panel'], ['PHASE 4 result', 'PHASE 5 result'], ['PHASE 4 finish', 'PHASE 5 finish']], 'before_after_phase4.png')
# full-corner GIFs: select (Entry stop) -> Apex stop -> Exit stop -> lock -> back to Entry -> playback -> result
for ci, tag in ((0, 'corner1_touge_HP'), (1, 'corner2_street_N90')):
    seq = [(f'seq_select{ci}_{i}', 250) for i in range(6)] + [(f'seq_move{ci}_0_{m}', 200) for m in range(3)] + [(f'plan_apex{ci}', 900)] \
        + [(f'seq_move{ci}_1_{m}', 200) for m in range(3)] + [(f'plan_exit{ci}', 900), (f'lock{ci}', 200)] + [(f'seq_lock{ci}_{m}', 350) for m in range(3)] \
        + [(f'seq_corner{ci}_{i}', 450) for i in range(8)] + [(f'result{ci}', 1800)]
    fr = [Image.open(f'{A}/{n}_640.png').convert('RGB') for n, _ in seq if os.path.exists(f'{A}/{n}_640.png')]
    du = [t for n, t in seq if os.path.exists(f'{A}/{n}_640.png')]
    out = f'{O}/shots5/{tag}_full.gif'
    fr[0].save(out, save_all=True, append_images=fr[1:], duration=du, loop=0, optimize=True); print(out, len(fr), 'frames', os.path.getsize(out) // 1024, 'KB')
