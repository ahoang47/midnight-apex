#!/usr/bin/env python3
"""Paint the district prop textures (night values baked in, unlit in Godot).
Bases come from the downloaded CC0 packs (/workspace/district_scenes/assets = converted copies of
/workspace/asset_packs): Kenney Retro Urban Kit rock/windows/wall, 3D Retro Shacks concrete,
Urban Stacked jersey-barrier concrete. Everything else (signs, vending fronts, shop windows) is
painted here. No real brands: all sign text is made-up generic words."""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'godot', 'art', 'env')
A = '/workspace/district_scenes/assets'
os.makedirs(OUT, exist_ok=True)
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
if not os.path.exists(CJK):
    CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
R = random.Random(7)

def load(p, size=None):
    im = Image.open(os.path.join(A, p)).convert('RGB')
    return im.resize(size, Image.BILINEAR) if size else im

def tint(im, mul, add=(0, 0, 0)):
    px = im.load(); w, h = im.size
    out = Image.new('RGB', im.size); po = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            po[x, y] = tuple(max(0, min(255, int(c * m + a))) for c, m, a in zip((r, g, b), mul, add))
    return out

def save(im, n):
    im.save(os.path.join(OUT, n + '.png')); print('tex', n, im.size)

def font(sz):
    return ImageFont.truetype(CJK, sz)

# --- Touge -------------------------------------------------------------------------------------
rock = load('kenney/Textures/rock.png', (128, 128))
save(tint(rock, (0.42, 0.47, 0.50), (4, 8, 14)), 'touge_cutrock')
# shotcrete lower band + rock above (cut slope face, v=0 bottom .. 1 top in Blender UVs)
cut = Image.new('RGB', (128, 256))
cut.paste(tint(rock, (0.40, 0.45, 0.48), (4, 8, 14)), (0, 0))
cut.paste(tint(rock, (0.36, 0.42, 0.42), (6, 10, 12)), (0, 128))
conc = tint(load('shacks/concrete_barricade_Concrete Barricade Texture.png', (128, 64)), (0.36, 0.39, 0.44), (4, 6, 12))
cut.paste(conc, (0, 192))
d = ImageDraw.Draw(cut)
for i in range(0, 128, 16):  # weep holes in the shotcrete
    d.rectangle([i + 6, 216, i + 9, 219], fill=(14, 16, 22))
for i in range(90):  # moss specks on the rock
    x, y = R.randrange(128), R.randrange(190)
    d.point((x, y), fill=(34, 52, 36))
save(cut, 'touge_cutslope')
grass = load('kenney/Textures/grass.png', (64, 64))
save(tint(grass, (0.34, 0.40, 0.42), (2, 6, 10)), 'touge_grasslip')
# gravel shoulder strip (across u 0..1, along v)
gv = Image.new('RGB', (32, 64), (38, 40, 44)); d = ImageDraw.Draw(gv)
for i in range(260):
    c = R.randrange(26, 62); d.point((R.randrange(32), R.randrange(64)), fill=(c, c + 2, c + 6))
save(gv, 'touge_gravel')
# galvanised W-beam guardrail: v rows = top crease ... bottom; posts darker
rl = Image.new('RGB', (32, 64)); d = ImageDraw.Draw(rl)
bands = [(150, 156, 162), (184, 190, 194), (120, 126, 132), (96, 102, 110), (140, 146, 152), (168, 174, 178), (110, 116, 124)]
for i, c in enumerate(bands):
    d.rectangle([0, i * 6, 31, i * 6 + 5], fill=tuple(int(v * 0.62) for v in c))
d.rectangle([0, 42, 31, 63], fill=(70, 74, 80))   # post
d.line([0, 48, 31, 48], fill=(54, 58, 64))
for x in range(4, 32, 8): d.rectangle([x, 12, x + 1, 14], fill=(46, 50, 56))  # bolts
save(rl, 'touge_guardrail')
# reflector delineator (emissive, tiny)
save(Image.new('RGB', (8, 8), (232, 196, 120)), 'emit_reflector')

# --- Street ------------------------------------------------------------------------------------
kw = load('kenney/Textures/windows.png', (64, 64))
kwall = load('kenney/Textures/wall.png', (64, 64))
kgar = load('kenney/Textures/wall_garage.png', (64, 64))
kconc = load('kenney/Textures/concrete.png', (64, 64))
WIN_LIT = [(206, 176, 126), (150, 196, 186), (196, 204, 196)]

def facade(seed, wall_mul, floors=3, shop='glass'):
    rr = random.Random(seed)
    im = Image.new('RGB', (256, 256))
    wall = tint(kconc if seed % 2 else kwall, wall_mul, (6, 8, 14)).resize((64, 64))
    for x in range(0, 256, 64):
        for y in range(0, 256, 64): im.paste(wall, (x, y))
    d = ImageDraw.Draw(im)
    # upper floors: v 0..170 (top of texture = roof)
    fh = 170 // floors
    for f in range(floors):
        y0 = 8 + f * fh
        for wx in range(0, 3):
            x0 = 18 + wx * 78
            lit = rr.random() < 0.38
            win = tint(kw, (0.30, 0.34, 0.40), (4, 6, 12)).resize((50, fh - 20))
            if lit:
                c = rr.choice(WIN_LIT)
                win = Image.blend(win, Image.new('RGB', win.size, c), 0.55)
            im.paste(win, (x0, y0 + 6))
            d.rectangle([x0 - 2, y0 + fh - 12, x0 + 52, y0 + fh - 10], fill=(34, 36, 44))  # sill
        # AC unit beside a window
        if rr.random() < 0.7:
            ax = 18 + rr.randrange(3) * 78 + 52
            d.rectangle([ax + 2, y0 + fh - 26, ax + 22, y0 + fh - 12], fill=(88, 92, 98))
            d.ellipse([ax + 6, y0 + fh - 24, ax + 16, y0 + fh - 14], outline=(52, 56, 62))
    # sign band 170..190
    d.rectangle([0, 170, 255, 192], fill=(20, 28, 44))
    d.rectangle([0, 170, 255, 171], fill=(60, 70, 86))
    words = ['クリーニング', '喫茶', '酒店', 'たばこ', '理容', '定食', '薬局', '書店', '電器', '洋品店', 'コイン', '弁当']
    w = rr.choice(words)
    col = rr.choice([(226, 214, 186), (150, 206, 196), (220, 220, 214)])
    f = font(18)
    tw = d.textlength(w, font=f)
    d.text(((256 - tw) / 2, 170), w, font=f, fill=col)
    # ground floor 192..256
    if shop == 'glass':
        g = Image.new("RGB", (236, 58), (82, 108, 106)); gd = ImageDraw.Draw(g)
        for sy in range(8, 58, 14):
            gd.rectangle([0, sy, 235, sy + 3], fill=(70, 86, 88))
            for sx in range(4, 230, 9):
                c = rr.choice([(150, 70, 60), (70, 110, 150), (190, 170, 110), (90, 140, 90), (180, 180, 170)])
                gd.rectangle([sx, sy - 6, sx + 5, sy - 1], fill=tuple(int(v * 0.75) for v in c))
        for mx in range(0, 236, 59): gd.rectangle([mx, 0, mx + 2, 57], fill=(40, 46, 54))
        im.paste(g, (10, 196))
    else:
        sh = tint(kgar, (0.34, 0.36, 0.40), (6, 8, 12)).resize((236, 58))
        im.paste(sh, (10, 196))
        d.rectangle([10, 196, 245, 253], outline=(30, 32, 38))
        for sy in range(198, 254, 4): d.line([10, sy, 245, sy], fill=(44, 48, 54))
    return im

for i, (mul, shop) in enumerate([((0.34, 0.36, 0.42), 'glass'), ((0.30, 0.33, 0.40), 'shutter'), ((0.38, 0.38, 0.40), 'glass'), ((0.28, 0.31, 0.38), 'shutter')]):
    save(facade(11 + i, mul, 3 if i % 2 == 0 else 2, shop), 'street_shop_%d' % i)
# side wall (plain)
save(tint(kwall, (0.24, 0.27, 0.33), (4, 6, 12)).resize((64, 64)), 'street_sidewall')
# vertical signs (emissive boards, kept dimmer than the car)
VS = [('スナック', (22, 30, 48), (226, 210, 170)), ('ホテル', (16, 44, 48), (170, 220, 210)), ('麻雀', (60, 26, 30), (230, 220, 200)), ('ラーメン', (226, 214, 186), (40, 30, 30))]
for i, (w, bg, fg) in enumerate(VS):
    im = Image.new('RGB', (32, 128), bg); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 31, 127], outline=tuple(min(255, int(c * 0.6 + 30)) for c in fg))
    f = font(22)
    n = len(w); step = 120 / max(n, 1)
    for k, ch in enumerate(w):
        tw = d.textlength(ch, font=f)
        d.text(((32 - tw) / 2, 2 + k * step + (step - 26) / 2), ch, font=f, fill=fg)
    save(im, 'emit_sign_v%d' % i)
# vending machine front (emissive) + body
vm = Image.new('RGB', (64, 128), (176, 186, 190)); d = ImageDraw.Draw(vm)
d.rectangle([4, 6, 59, 70], fill=(206, 214, 214))
for row in range(3):
    for k in range(6):
        c = R.choice([(170, 50, 46), (40, 90, 160), (200, 170, 60), (60, 130, 80), (220, 220, 220), (120, 70, 40)])
        x = 7 + k * 9; y = 10 + row * 21
        d.rectangle([x, y, x + 5, y + 13], fill=c)
        d.rectangle([x + 1, y + 15, x + 4, y + 16], fill=(40, 40, 40))
d.rectangle([4, 74, 59, 84], fill=(40, 44, 52))
for k in range(6): d.rectangle([8 + k * 8, 77, 12 + k * 8, 80], fill=(120, 200, 190))
d.rectangle([8, 92, 30, 104], fill=(26, 28, 34)); d.rectangle([40, 92, 56, 100], fill=(60, 64, 70))
d.rectangle([4, 110, 59, 122], fill=(24, 26, 30))
save(vm, 'emit_vending_front')
save(Image.new('RGB', (16, 16), (64, 70, 78)), 'vending_body')
# concrete utility pole + misc
cp = tint(load('shacks/concrete_barricade_Concrete Barricade Texture.png', (64, 64)), (0.42, 0.44, 0.48), (4, 6, 10))
save(cp, 'street_pole_concrete')
save(Image.new('RGB', (16, 16), (50, 54, 60)), 'street_metal')
# sidewalk paving + curb
sw = tint(load('kenney/Textures/tiles.png', (64, 64)), (0.30, 0.32, 0.36), (6, 8, 12))
save(sw, 'street_paving')
cb = Image.new('RGB', (16, 16), (92, 94, 98)); save(cb, 'street_curb')

# --- Wangan ------------------------------------------------------------------------------------
jb = Image.open(os.path.join(A, 'urban/Jersey_barrier_concrete_barriers.png')).convert('RGB').crop((0, 0, 128, 52))
jb = tint(jb.resize((128, 64)), (0.40, 0.43, 0.48), (4, 6, 12))
save(jb, 'wangan_barrier')
pc = tint(load('shacks/concrete_barricade_Concrete Barricade Texture.png', (128, 128)), (0.32, 0.35, 0.41), (4, 6, 12))
save(pc, 'wangan_concrete')
save(Image.new('RGB', (16, 16), (78, 84, 92)), 'wangan_galv')
save(Image.new('RGB', (16, 8), (240, 200, 148)), 'emit_sodium')   # every lamp head = #F0C894
# distant tower facades: dark blocks with sparse lit windows (cream + mercury teal), no neon
for i in range(3):
    rr = random.Random(40 + i)
    im = Image.new('RGB', (64, 256), (12, 18, 30)); d = ImageDraw.Draw(im)
    for y in range(4, 256, 8):
        for x in range(3, 64, 6):
            p = rr.random()
            if p < 0.20:
                c = rr.choice([(196, 170, 124), (120, 176, 170), (170, 180, 180)])
            elif p < 0.5:
                c = (22, 30, 44)
            else:
                continue
            d.rectangle([x, y, x + 3, y + 4], fill=c)
    if i == 0:  # red aviation light on top
        d.rectangle([28, 0, 35, 3], fill=(200, 60, 50))
    save(im, 'emit_tower_%d' % i)
