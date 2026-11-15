#!/usr/bin/env python3
"""Mountain-district textures (Arthur, unapproved mockup, Austin 2026-11-15: every district becomes a mountain pass, each keeping
its identity). Starts from the tight_districts recipe (the two road strips + the curve mirror, unchanged) and adds the
mountain kit: retaining walls, house walls / roofs / windows, stone steps, the toll-road sign, and the valley light field.
Tight-district textures (Arthur, unapproved mockup, Austin 2026-11-15: cat-and-mouse only, roads "a little tight").
Hand-painted night values (everything is unlit in Godot), quantised RGB555 + 4x4 Bayer and saved lossless, the same
recipe as ../../../experiments/wangan_two_corner/tex_src/make_tex.py.
  python3 tex_src/make_tex.py  ->  godot/art/wangan_tight_road.png, godot/art/street_tight_road.png, godot/art/env/street_curvemirror.png
Road strips: x = across the asphalt (u 0..1 = -half .. +half), y = metres along (one lamp period per tile)."""
import os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.normpath(os.path.join(HERE, '..', 'godot', 'art'))
R = random.Random(7)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def quant555(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32); h, w = a.shape[:2]
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = np.clip(np.floor(a[..., :3] / 8 + t + 0.5), 0, 31) * 8.2258
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')
def save(im, path):
    quant555(im).save(path); print('tex', os.path.relpath(path, ART), im.size)
def noise(w, h, s, amp, seed):
    rng = np.random.default_rng(seed); n = rng.random((h // s + 2, w // s + 2))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (n - 0.5) * amp
SOD = hx('#F0C894') / 255
AMB = hx('#5575A0') / 255 * 0.8 * 1.7
PXU, PXV = 16, 12

def light(im, W_m, tile, lamps, head_h, reach, dec_r):
    """bake the sodium pools of the lamp heads (s, d) into the painted asphalt: stepped vertex pool + stepped decal"""
    a = np.asarray(im).astype(np.float32) / 255; H, W = a.shape[:2]
    L = np.tile(AMB, (H, W, 1)); add = np.zeros((H, W, 3), np.float32); vv, uu = np.mgrid[0:H, 0:W]
    for s_l, d_l in lamps:
        for rep in (-1, 0, 1):
            dd = np.sqrt(((vv - (s_l + rep * tile) * PXV) / PXV) ** 2 + ((uu - (W_m + d_l) * PXU) / PXU) ** 2)
            lv = np.clip(1 - np.sqrt(dd ** 2 + head_h ** 2) / reach, 0, 1)
            L += (np.floor(lv * 3 * 2.2) / 3 / 2.2)[..., None] * SOD * 0.85 * 0.55 * 2.6
            add += (np.floor(np.clip(1 - dd / dec_r, 0, 1) ** 1.1 * 3) / 3)[..., None] * SOD * 0.09 * 1.8 * 2.2
    return Image.fromarray((np.clip(a * L + add, 0, 1) * 255).astype(np.uint8))

# ── Wangan tight: 7.5 m between the parapet feet = 2 x 3.5 m lanes + 0.25 m marginal strips. Edge lines at +-3.5,
#    dashed white centre divider (6 m on / 6 m off), an expansion joint at s 40. Lamps every 48 m staggered, heads 11.6 m up
#    and just over the centre line (the arm of wangan_lamp reaches 4.5 m in from the parapet top).
def wangan_road():
    W_m, tile = 3.75, 48.0; W, H = int(2 * W_m * PXU), int(tile * PXV)
    base = np.full((H, W, 3), (46, 46, 54), np.float32) + noise(W, H, 3, 20, 1)[..., None] + noise(W, H, 40, 12, 2)[..., None]
    rng = np.random.default_rng(3)
    for _ in range(10):
        y, x = rng.integers(0, H), rng.integers(0, W); base[y:y + rng.integers(10, 50), x:x + rng.integers(12, 40)] += rng.uniform(-7, 5)
    # wheel tracks: slightly polished bands in each lane (the only wear on a fast road)
    for c in (-1.75, 1.75):
        for o in (-0.8, 0.8):
            x0 = int((W_m + c + o - 0.3) * PXU); base[:, x0:x0 + int(0.6 * PXU)] += 4
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    X = lambda m: int(round(W / 2 + m * PXU)); edge = (189, 189, 168)
    d.rectangle([0, 0, X(-3.6) - 1, H], fill=(112, 112, 110)); d.rectangle([X(3.6), 0, W, H], fill=(112, 112, 110))   # marginal strip at the wall foot
    for sgn in (-1, 1): d.rectangle([X(sgn * 3.5 - 0.08), 0, X(sgn * 3.5 + 0.08) - 1, H], fill=edge)
    for v in np.arange(0, tile, 12.0): d.rectangle([X(-0.07), int(v * PXV), X(0.07), int((v + 6.0) * PXV) - 1], fill=edge)
    for v in np.arange(3.0, tile, 12.0):   # drain slots in the marginal strip
        for sgn in (-1, 1): xa = X(sgn * 3.66); d.rectangle([xa - 1, int(v * PXV), xa + 1, int(v * PXV) + 5], fill=(40, 40, 44))
    jy = int(40.0 * PXV)
    d.rectangle([0, jy - 2, W, jy + 2], fill=(38, 40, 46)); d.line([0, jy - 3, W, jy - 3], fill=(92, 96, 104)); d.line([0, jy + 3, W, jy + 3], fill=(80, 84, 92))
    return light(im, W_m, tile, [(0.0, -0.5), (24.0, 0.5)], 11.6, 19.0, 8.0)

# ── Street tight: 5.8 m kerb to kerb, no centre line (a two-way back street), solid white 路側帯 lines 0.55 m in from
#    each kerb, patched asphalt, a utility cover. Pole lamps 5.2 m up every 24 m, left at s 0 / right at s 12, heads 1.35 m
#    out from the poles (poles at +-3.3 on the pavement) -> pools at d -+1.95.
def street_road():
    W_m, tile = 2.9, 24.0; W, H = int(2 * W_m * PXU), int(tile * PXV)
    base = np.full((H, W, 3), (42, 42, 50), np.float32) + noise(W, H, 3, 22, 4)[..., None] + noise(W, H, 30, 14, 5)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    X = lambda m: int(round(W / 2 + m * PXU))
    # utility trench patch (older, darker asphalt, tar-sealed edges) along the left third + one transverse patch
    d.rectangle([X(-1.6), int(2 * PXV), X(-0.9), int(17 * PXV)], fill=(36, 36, 43))
    d.rectangle([X(-1.6), int(2 * PXV), X(-0.9), int(17 * PXV)], outline=(28, 28, 33))
    d.rectangle([X(-2.4), int(19.5 * PXV), X(1.2), int(20.6 * PXV)], fill=(50, 50, 57), outline=(30, 30, 35))
    cx, cy = X(0.6), int(8.0 * PXV)   # round utility cover, 0.6 m
    d.ellipse([cx - 5, cy - 4, cx + 5, cy + 4], fill=(56, 56, 60), outline=(30, 30, 34))
    for k in (-2, 0, 2): d.line([cx - 4, cy + k, cx + 4, cy + k], fill=(44, 44, 48))
    for _ in range(8):
        x, y = R.randrange(W), R.randrange(H); pts = [(x, y)]
        for _ in range(R.randrange(3, 6)): x += R.randint(-8, 8); y += R.randint(-6, 6); pts.append((x, y))
        d.line(pts, fill=(28, 28, 33), width=1)
    gut = (70, 70, 72)
    d.rectangle([0, 0, X(-2.6) - 1, H], fill=gut); d.rectangle([X(2.6), 0, W, H], fill=gut)   # concrete gutter at the kerb
    for v in np.arange(1.5, tile, 6.0):   # gutter grates
        for sgn in (-1, 1):
            xa = X(sgn * 2.75)
            for k in range(4): d.line([xa - 2, int(v * PXV) + 2 * k, xa + 2, int(v * PXV) + 2 * k], fill=(30, 30, 34))
    for sgn in (-1, 1): d.rectangle([X(sgn * 2.35 - 0.07), 0, X(sgn * 2.35 + 0.07) - 1, H], fill=(178, 178, 166))
    return light(im, W_m, tile, [(0.0, -1.95), (12.0, 1.95)], 5.2, 9.5, 4.2)

# ── curve mirror (カーブミラー): orange-painted head ring + dark convex face with a painted cool sheen (never reflective)
def curvemirror():
    S = 64; im = Image.new('RGB', (S, S), (16, 22, 34)); d = ImageDraw.Draw(im)
    d.ellipse([2, 2, S - 3, S - 3], fill=(150, 72, 30))            # orange rim
    d.ellipse([8, 8, S - 9, S - 9], fill=(24, 34, 52))             # face
    d.ellipse([14, 12, 40, 30], fill=(44, 60, 86))                  # painted sheen, upper left
    d.ellipse([18, 15, 30, 22], fill=(70, 92, 120))
    d.rectangle([0, 0, 7, 7], fill=(150, 72, 30))                   # u 0..0.12: orange pole paint swatch
    d.rectangle([56, 0, 63, 7], fill=(36, 38, 44))                  # back of the head
    return im

save(wangan_road(), os.path.join(ART, 'wangan_tight_road.png'))
save(street_road(), os.path.join(ART, 'street_tight_road.png'))
save(curvemirror(), os.path.join(ART, 'env', 'street_curvemirror.png'))

ENV = os.path.join(ART, 'env')
def tex_noise(w, h, base, amp, seed, s1=2, s2=12):
    a = np.full((h, w, 3), base, np.float32) + noise(w, h, s1, amp, seed)[..., None] + noise(w, h, s2, amp * 0.6, seed + 1)[..., None]
    return a

# ── retaining wall, cast concrete: u = 4 m along, v = 3 m up (v 0 = top). Board-mark lines, a row of weep holes, rust/
#    water streaks under them, the foot darker where the drainage channel runs.
def retain_concrete():
    W, H = 64, 48; a = tex_noise(W, H, (66, 70, 78), 10, 21)
    for y in range(4, H, 6): a[y, :] -= 6                        # board marks
    a[:, 31:33] -= 14                                            # 2 m panel joint
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 2], fill=(86, 90, 98))                 # coping
    for x in (12, 44):
        d.ellipse([x - 2, 30, x + 2, 34], fill=(20, 22, 28))     # weep hole + a soft stain below it
        for k in range(10): d.point((x + (k % 2), 35 + k), fill=(52, 54, 58))
    d.rectangle([0, H - 4, W, H], fill=(44, 46, 52))
    return im

# ── stone retaining wall (谷積み, diagonal-laid stones): u = 4 m along, v = 4.5 m up
def stonewall():
    W, H = 64, 72; im = Image.new('RGB', (W, H), (34, 36, 42)); d = ImageDraw.Draw(im); rr = random.Random(5)
    for row in range(-2, 14):
        for col in range(-1, 6):
            cx = col * 13 + (row % 2) * 6.5; cy = row * 6
            pts = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
            v = rr.randint(58, 78); d.polygon([(x + rr.uniform(-0.6, 0.6), y + rr.uniform(-0.6, 0.6)) for x, y in pts], fill=(v, v + 2, v + 6), outline=(30, 32, 38))
    for _ in range(14):   # moss in the joints, kept dark and few
        x, y = rr.randrange(W), rr.randrange(H); d.point((x, y), fill=(40, 58, 44))
    d.rectangle([0, 0, W, 2], fill=(80, 82, 88))
    return im

# ── house wall (vertical boards over a plaster base), roof tiles, lit window
def house_wall():
    W, H = 64, 64; a = tex_noise(W, H, (58, 54, 52), 8, 31)
    for x in range(0, W, 4): a[:40, x] -= 10                     # board joints, upper part
    a[40:, :] = tex_noise(W, 24, (74, 76, 80), 6, 33)            # plaster base
    a[39:41, :] = (40, 38, 38)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def roof():
    W, H = 64, 64; a = tex_noise(W, H, (38, 42, 52), 6, 41)
    for y in range(0, H, 5): a[y:y + 1, :] -= 12                 # tile courses
    for y in range(0, H, 5):
        for x in range((y // 5 % 2) * 3, W, 6): a[y:y + 5, x] -= 5
    a[:, :2] = (60, 64, 72)                                      # ridge / verge tiles
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def house_window():
    im = Image.new('RGB', (16, 16), (30, 26, 24)); d = ImageDraw.Draw(im)
    d.rectangle([1, 1, 14, 14], fill=(176, 158, 120))            # cream window light (paper screen), dimmer than the car
    d.line([8, 1, 8, 14], fill=(120, 100, 76)); d.line([1, 8, 14, 8], fill=(120, 100, 76))
    return im

# ── stone steps: u across (1.4 m), v along the flight
def steps():
    W, H = 32, 64; a = tex_noise(W, H, (70, 70, 74), 10, 51)
    for y in range(0, H, 5): a[y:y + 1, :] = (36, 36, 40)        # tread nosings
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ── toll-road sign (green, white letters, generic words): スカイライン / SKYLINE  料金所 2km / TOLL
def toll_sign():
    W, H = 200, 60; im = Image.new('RGB', (W, H), (22, 74, 52)); d = ImageDraw.Draw(im)
    d.rectangle([1, 1, W - 2, H - 2], outline=(200, 206, 200))
    try: f1, f2 = ImageFont.truetype(CJK, 17), ImageFont.truetype(CJK, 11)
    except OSError: f1 = f2 = ImageFont.load_default()
    d.text((8, 4), 'スカイライン', font=f1, fill=(226, 230, 224)); d.text((8, 28), 'SKYLINE', font=f2, fill=(226, 230, 224))
    d.text((124, 4), '料金所', font=f1, fill=(226, 230, 224)); d.text((124, 28), '2km  TOLL', font=f2, fill=(226, 230, 224))
    d.line([116, 6, 116, H - 7], fill=(200, 206, 200))
    d.text((8, 44), '湾岸方面 ↓', font=f2, fill=(186, 192, 186))
    return im

# ── valley light field: palette strip (u picks the colour: cream / teal / sodium / red aviation / white) and the
#    ground under it (land / water two-tone, a hair lighter than the fog so the coast reads)
def light_palette():
    im = Image.new('RGB', (10, 2)); d = ImageDraw.Draw(im)
    for i, c in enumerate([(232, 214, 168), (150, 210, 214), (240, 200, 148), (220, 60, 50), (236, 236, 228)]):
        d.rectangle([i * 2, 0, i * 2 + 1, 1], fill=c)
    return im
def valley_ground(water):
    W = 64; a = np.full((W, W, 3), (12, 22, 40) if water else (9, 17, 31), np.float32) + noise(W, W, 8, 4, 61)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

for fn, n in [(retain_concrete, 'mtn_retain_concrete'), (stonewall, 'mtn_stonewall'), (house_wall, 'mtn_house_wall'), (roof, 'mtn_roof'),
              (house_window, 'emit_house_window'), (steps, 'mtn_steps'), (toll_sign, 'mtn_sign_toll')]:
    save(fn(), os.path.join(ENV, n + '.png'))
light_palette().save(os.path.join(ENV, 'emit_valley_lights.png')); print('tex env/emit_valley_lights.png (palette, unquantised)')
save(valley_ground(True), os.path.join(ENV, 'valley_water.png')); save(valley_ground(False), os.path.join(ENV, 'valley_land.png'))

# ════ PASS 2 (Austin 2026-11-15: "the side assets should be decreasing in height, to achieve perspective"; street "doesn't
#      feel like city in the mountains"). Lattice-framed cut slopes (法枠), delineators, the hillside-city block kit.
# ── 法枠 lattice cut slope: the cast beams (light concrete) and the cell infill (grass for touge, shotcrete for Wangan)
def lattice_beam():
    a = tex_noise(32, 32, (88, 92, 98), 8, 71); a[:, :2] -= 10; a[:, -2:] -= 14
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def lattice_fill(grass):
    a = tex_noise(32, 32, (34, 46, 38) if grass else (54, 58, 64), 12 if grass else 8, 73 if grass else 75, 1, 6)
    if grass:
        rr = random.Random(9)
        for _ in range(40): x, y = rr.randrange(32), rr.randrange(32); a[y:y + 2, x] += (10, 16, 8)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# ── delineator post: white post, orange-amber reflector (catches the headlights: Emit_, dimmer than the car lamps)
def delineator():
    im = Image.new('RGB', (8, 32), (168, 170, 172)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 7, 5], fill=(208, 150, 70)); d.rectangle([0, 28, 7, 31], fill=(90, 92, 96))
    return im
# ── hillside-city blocks (熱海 / 北野 / 尾道): facade tile in three tints, flat roof, the window atlas (32 cells, about a
#    third lit, all below the car's brightness), ground-floor atlas (4 x: lit entrance, shutter, small shop, hotel lobby),
#    sign atlas (6 generic boards: ホテル 旅館 ♨ スナック 喫茶 民宿), the footbridge rail (alpha) and fascia
def block_wall(base, seed):
    W, H = 64, 64; a = tex_noise(W, H, base, 6, seed)
    for y in range(0, H, 4): a[y, :] -= 5
    for x in range(0, W, 8): a[:, x] -= 4
    a[:, 0:2] -= 10                                              # column line at the module edge
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def flat_roof():
    a = tex_noise(32, 32, (40, 42, 48), 6, 81); a[:2, :] = (70, 72, 78)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def windows_atlas():
    W, H = 256, 16; im = Image.new('RGB', (W, H), (34, 36, 42)); d = ImageDraw.Draw(im); rr = random.Random(13)
    for c in range(32):
        x = c * 8; r = rr.random()
        if r < 0.22: g = (176, 158, 120)                         # cream room light
        elif r < 0.32: g = (150, 116, 78)                        # warm curtain
        elif r < 0.36: g = (96, 124, 136)                        # TV-blue, rare
        else: g = (22, 28, 40) if rr.random() < 0.6 else (28, 34, 46)
        d.rectangle([x + 1, 2, x + 6, 12], fill=g)
        if g[0] > 100 and rr.random() < 0.5: d.rectangle([x + 1, 2, x + 6, 5], fill=tuple(int(v * 0.7) for v in g))   # blind half down
        d.line([x, 13, x + 7, 13], fill=(70, 72, 78)); d.line([x, 15, x + 7, 15], fill=(58, 60, 66))   # balcony rail
        for k in range(x, x + 8, 2): d.point((k, 14), fill=(62, 64, 70))
    return im
def ground_atlas():
    W, H = 256, 32; im = Image.new('RGB', (W, H), (30, 30, 34)); d = ImageDraw.Draw(im)
    # 0 lit glass entrance with a noren curtain
    d.rectangle([4, 6, 60, 31], fill=(132, 118, 92)); d.rectangle([4, 6, 60, 13], fill=(74, 40, 44))
    for x in range(10, 60, 10): d.line([x, 13, x, 31], fill=(60, 54, 46))
    # 1 closed shutter
    d.rectangle([66, 4, 126, 31], fill=(64, 66, 72))
    for y in range(6, 31, 2): d.line([66, y, 126, y], fill=(50, 52, 58))
    # 2 small shop window, goods silhouettes
    d.rectangle([132, 8, 188, 31], fill=(118, 112, 96)); d.rectangle([132, 4, 188, 7], fill=(58, 60, 70))
    for x in range(136, 186, 7): d.rectangle([x, 22, x + 4, 31], fill=(70, 64, 56))
    # 3 hotel lobby, warm, revolving-door frame
    d.rectangle([196, 4, 252, 31], fill=(150, 128, 92))
    for x in range(204, 252, 12): d.line([x, 4, x, 31], fill=(84, 72, 56))
    d.rectangle([196, 4, 252, 6], fill=(96, 84, 66))
    return im
def sign_atlas():
    W, H = 192, 96; im = Image.new('RGB', (W, H), (20, 20, 24)); d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype(CJK, 20)
    except OSError: f = ImageFont.load_default()
    boards = [('ホテル', (92, 30, 34), (226, 214, 180)), ('旅館', (28, 36, 60), (220, 222, 224)), ('♨', (200, 186, 150), (120, 40, 40)),
              ('スナック', (70, 30, 62), (220, 200, 210)), ('喫茶', (40, 58, 46), (226, 220, 196)), ('民宿', (180, 166, 132), (40, 36, 34))]
    for i, (t, bg, fg) in enumerate(boards):
        x = i * 32; d.rectangle([x + 1, 1, x + 30, 94], fill=bg, outline=(70, 70, 74))
        chars = list(t) if t != '♨' else ['♨', '湯']
        sp = min(22, 84 // len(chars)); fz = f if len(chars) < 4 else ImageFont.truetype(CJK, 18)
        for k, ch in enumerate(chars): d.text((x + 6 if len(chars) < 4 else x + 7, 5 + k * sp), ch, font=fz, fill=fg)
    return im
def rail_alpha():
    im = Image.new('RGBA', (64, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 1], fill=(120, 124, 130, 255)); d.rectangle([0, 14, 63, 15], fill=(96, 98, 104, 255))
    for x in range(0, 64, 4): d.rectangle([x, 0, x, 15], fill=(104, 108, 114, 255))
    return im
def bridge_fascia():
    a = tex_noise(64, 16, (78, 80, 86), 6, 91); a[:2, :] = (96, 98, 104); a[-2:, :] = (44, 46, 52)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
for fn, n in [(lattice_beam, 'mtn_lattice_beam'), (lambda: lattice_fill(True), 'mtn_lattice_fill_g'), (lambda: lattice_fill(False), 'mtn_lattice_fill_c'),
              (delineator, 'emit_delineator'), (lambda: block_wall((86, 82, 74), 101), 'mtn_block_wall_a'), (lambda: block_wall((70, 74, 80), 103), 'mtn_block_wall_b'),
              (lambda: block_wall((80, 66, 58), 105), 'mtn_block_wall_c'), (flat_roof, 'mtn_roof_flat'), (windows_atlas, 'emit_mtn_windows'),
              (ground_atlas, 'emit_mtn_ground'), (sign_atlas, 'emit_mtn_signs'), (rail_alpha, 'mtn_rail'), (bridge_fascia, 'mtn_bridge_fascia')]:
    save(fn(), os.path.join(ENV, n + '.png'))
# ── pass 3 (Austin 2026-11-15: the Wangan lattice "feels too similar to the touge"; near Street windows read flat) ──────────
# sound wall: u = 4 m module, v = 2 m up (v 0 = top). Grey-green steel louvre panels: horizontal ribs every 2 px, a darker
# frame, a translucent (lighter) strip near the top as on 首都高 / 有料道路 noise barriers.
def soundwall():
    W, H = 64, 32; a = tex_noise(W, H, (70, 80, 78), 4, 121)
    for y in range(5, H - 2):                                           # louvre slats: 3 px lit face, 1 px dark shadow line
        a[y, :] += (10 if (y - 5) % 4 == 0 else (-26 if (y - 5) % 4 == 3 else 0))
    a[:4, :] = tex_noise(W, 4, (96, 110, 118), 4, 122)                  # translucent top strip
    a[4, :] = (36, 40, 42); a[-2:, :] = (36, 40, 42)                    # rails
    a[:, 0:2] = (44, 48, 50)                                            # the joint on the H-post only (one per 4 m)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# shotcrete with rock netting: u = 2 m, v = 2 m. Grey sprayed concrete, darker weep/water stains, a diamond wire net over it
# (thin dark lines, 0.5 m mesh) and a few anchor plates.
def shotcrete_net():
    W, H = 32, 32; a = tex_noise(W, H, (60, 62, 66), 10, 131, 1, 5)
    rr = random.Random(31)
    for _ in range(3):
        x = rr.randrange(W); a[:, x:x + 2] -= (8, 8, 6)
    for y in range(H):
        for x in range(W):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0: a[y, x] = a[y, x] * 0.72 + np.array((30, 32, 30)) * 0.28
    for (x, y) in ((4, 4), (20, 20)): a[y:y + 2, x:x + 2] = (92, 92, 90)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# windows v3: 32 cells of 16 x 24 px (each 1.6 m x 1.35 m strip) so the near blocks keep detail: aluminium frame + mullion,
# curtains or blinds, interior gradient and furniture silhouettes in the lit ones, an AC unit or laundry on some balconies.
def windows_atlas_v3():
    W, H = 512, 24; im = Image.new('RGB', (W, H), (34, 36, 42)); d = ImageDraw.Draw(im); rr = random.Random(17)
    for c in range(32):
        x = c * 16; r = rr.random()
        if r < 0.24: g = (178, 160, 122)
        elif r < 0.34: g = (152, 118, 80)
        elif r < 0.38: g = (96, 124, 136)
        else: g = (22, 28, 40) if rr.random() < 0.6 else (30, 36, 48)
        lit = g[0] > 90
        d.rectangle([x + 1, 2, x + 14, 17], fill=(58, 60, 66))                 # frame
        for yy in range(3, 17):                                              # glass, lit ones brighter at the top (ceiling light)
            k = 1.0 - (yy - 3) * (0.025 if lit else 0.01)
            d.line([x + 2, yy, x + 13, yy], fill=tuple(int(v * k) for v in g))
        if lit:
            if rr.random() < 0.6:                                            # curtains drawn to the sides
                cc = tuple(int(v * 0.62) for v in g); d.rectangle([x + 2, 3, x + 4, 16], fill=cc); d.rectangle([x + 11, 3, x + 13, 16], fill=cc)
            if rr.random() < 0.5:                                            # furniture / person silhouette
                fx = x + 5 + rr.randrange(4); d.rectangle([fx, 11, fx + 2, 16], fill=tuple(int(v * 0.45) for v in g))
            if rr.random() < 0.3: d.rectangle([x + 2, 3, x + 13, 6], fill=tuple(int(v * 0.7) for v in g))   # blind
        d.line([x + 7, 2, x + 8, 17], fill=(58, 60, 66))                    # mullion (sliding sash)
        d.line([x + 1, 2, x + 14, 2], fill=(84, 86, 92))
        d.rectangle([x, 18, x + 15, 18], fill=(76, 78, 84)); d.rectangle([x, 23, x + 15, 23], fill=(58, 60, 66))   # balcony rail
        for k in range(x, x + 16, 2): d.line([k, 19, k, 22], fill=(62, 64, 70))
        q = rr.random()
        if q < 0.3: d.rectangle([x + 2, 19, x + 6, 22], fill=(118, 120, 122))                     # AC unit
        elif q < 0.45: d.rectangle([x + 4, 15, x + 12, 19], fill=(96, 92, 84) if lit else (52, 54, 60))  # laundry
    return im
for fn, n in [(soundwall, 'mtn_soundwall'), (shotcrete_net, 'mtn_shotcrete_net'), (windows_atlas_v3, 'emit_mtn_windows_v3')]:
    save(fn(), os.path.join(ENV, n + '.png'))
