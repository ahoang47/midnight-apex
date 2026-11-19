# shots7 legibility composites: before/after at 1920x1080 (2.25x non-integer -> 2x integer), crops at true screen pixels.
import sys
from PIL import Image, ImageDraw, ImageFont
R = sys.argv[1] if len(sys.argv) > 1 else 'out/shots7'
FN = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
f = ImageFont.truetype(FN, 22)
def crop(state, shot, nat):  # nat = box in 640x480 coords; map to the screen canvas of that run
    im = Image.open(f'{R}/{state}_live/1920x1080/{shot}.png').convert('RGB')
    ox, oy, sc = (240, 0, 2.25) if state == 'before' else (320, 60, 2.0)
    x0, y0, x1, y1 = nat
    c = im.crop((round(ox + x0 * sc), round(oy + y0 * sc), round(ox + x1 * sc), round(oy + y1 * sc)))
    return c.resize((c.width * 2, c.height * 2), Image.NEAREST)   # 2x again so the reader sees screen pixels
rows = [('1_plan_entry', (404, 312, 632, 472), 'Plan the Line'), (('5_playback', '6_playback_b'), (118, 8, 636, 104), 'B.5a line vs line + corner plate'),
        ('1_plan_entry', (8, 6, 200, 64), 'Line-lock timer + debug HUD')]
tiles = []
for shot, box, name in rows:
    sb, sa = shot if isinstance(shot, tuple) else (shot, shot)   # swiftshader runs at different speeds: pick the frame where the panel is up
    b, a = crop('before', sb, box), crop('after', sa, box)
    W = b.width + a.width + 30; H = max(b.height, a.height) + 40
    t = Image.new('RGB', (W, H), (5, 10, 19)); d = ImageDraw.Draw(t)
    d.text((6, 6), f'{name}  BEFORE 2.25x nearest (pixels 2/3 wide)', font=f, fill=(255, 176, 40))
    d.text((b.width + 30, 6), 'AFTER 2x integer', font=f, fill=(44, 184, 74))
    t.paste(b, (0, 36)); t.paste(a, (b.width + 30, 36)); tiles.append(t)
W = max(t.width for t in tiles); H = sum(t.height + 10 for t in tiles)
out = Image.new('RGB', (W, H), (5, 10, 19)); y = 0
for t in tiles: out.paste(t, (0, y)); y += t.height + 10
out.save(f'{R}/composite_before_after_1920x1080.png'); print(out.size)
# full-window side by side (as the browser shows it)
b = Image.open(f'{R}/before_live/1920x1080/2_plan_apex.png').convert('RGB'); a = Image.open(f'{R}/after_live/1920x1080/2_plan_apex.png').convert('RGB')
s = Image.new('RGB', (3860, 1080)); s.paste(b, (0, 0)); s.paste(a, (1940, 0)); s.save(f'{R}/composite_fullwindow_1920x1080.png')
# native 640x480 (2x nearest) Godot vs Arthur's approved frames: the HUD text matches his 1-bit NimbusSansNarrow renders
G = f'{R}/before_native/godot_seed20261113_idx'; A = '/workspace/midnight-apex/art/ui'
pairs = [(f'{G}/plan_apex0_640.png', f'{A}/line_select_cam/2_apex_pick.png'), (f'{G}/result0_640.png', f'{A}/line_vs_line/a2_apex_line_vs_line.png')]
s = Image.new('RGB', (2580, 2 * 1000), (5, 10, 19)); d = ImageDraw.Draw(s)
for i, (g, a) in enumerate(pairs):
    y = i * 1000; d.text((6, y + 6), 'GODOT (native 640x480, 2x nearest)', font=f, fill=(255, 176, 40)); d.text((1306, y + 6), "ARTHUR'S APPROVED FRAME (same font, sizes, 1-bit)", font=f, fill=(255, 176, 40))
    s.paste(Image.open(g).convert('RGB').resize((1280, 960), Image.NEAREST), (0, y + 36)); s.paste(Image.open(a).convert('RGB').resize((1280, 960), Image.NEAREST), (1300, y + 36))
s.save(f'{R}/composite_native_godot_vs_arthur.png')
