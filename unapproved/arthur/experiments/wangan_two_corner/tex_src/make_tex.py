#!/usr/bin/env python3
"""Wangan two-corner textures (Arthur, unapproved experiment). Small hand-painted night textures, values baked in
(everything is unlit in Godot), quantised RGB555 + 4x4 Bayer like Gordon's gen_art.py and saved lossless.
  python3 tex_src/make_tex.py   -> godot/art/env/*.png
Strip textures: x = across the strip (or up a wall), y = metres along the road. Palette: TXR navy fog #0B172B,
pale sodium #F0C894 only, cream / Mercury-teal window lights. No brands: sign words are generic route words.
The road recipe is Gordon's spec/gen_art.py road() (two-corner, B.5b lined road), re-run with the Wangan lamp layout
(staggered 24 m, heads over the lanes) plus a painted expansion joint per 48 m tile."""
import os, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'godot', 'art', 'env')); os.makedirs(OUT, exist_ok=True)
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
R = random.Random(11)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def quant555(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32); h, w = a.shape[:2]
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = np.clip(np.floor(a[..., :3] / 8 + t + 0.5), 0, 31) * 8.2258
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')
def save(im, n, q=True):
    (quant555(im) if q else im.convert('RGBA')).save(os.path.join(OUT, n + '.png')); print('tex', n, im.size)
def noise(w, h, s, amp, seed):
    rng = np.random.default_rng(seed); n = rng.random((h // s + 2, w // s + 2))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (n - 0.5) * amp
SOD = hx('#F0C894') / 255
AMB = hx('#5575A0') / 255 * 0.8 * 1.7          # display.json palette ambient x ambient_k x calib.road_amb_gain (as gen_art.py)

# ── road: 11.9 m (half 5.95 = 1.5 lanes + 1 m), 3 x 3.3 m lanes, one 48 m tile, 16 px/m across, 12 px/m along ──
def road():
    W_m, tile = 5.95, 48.0; PXU, PXV = 16, 12; W, H = int(2 * W_m * PXU), int(tile * PXV)
    base = np.full((H, W, 3), (46, 46, 54), np.float32)
    base += noise(W, H, 3, 22, 1)[..., None] + noise(W, H, 40, 12, 2)[..., None]
    rng = np.random.default_rng(3)
    for _ in range(int(tile * 0.4)):   # a few resurfacing patches, kept faint (big flat surface: no busy noise)
        y, x = rng.integers(0, H), rng.integers(0, W); base[y:y + rng.integers(10, 50), x:x + rng.integers(12, 60)] += rng.uniform(-7, 5)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    cx = W / 2; X = lambda m: int(round(cx + m * PXU))
    for _ in range(10):   # sparse sealed cracks
        x, y = R.randrange(W), R.randrange(H); pts = [(x, y)]
        for _ in range(R.randrange(3, 7)): x += R.randint(-9, 9); y += R.randint(-7, 7); pts.append((x, y))
        d.line(pts, fill=(28, 28, 33), width=1)
    sh = (150, 150, 146); edge = (189, 189, 168)
    d.rectangle([0, 0, X(-4.95) - 1, H], fill=sh); d.rectangle([X(4.95), 0, W, H], fill=sh)    # concrete shoulders beyond the 9.9 m of lanes
    for sgn in (-1, 1):
        e = sgn * 4.80; d.rectangle([X(e - 0.08), 0, X(e + 0.08) - 1, H], fill=edge)            # solid edge lines
        l = sgn * 1.65
        for v in np.arange(0, tile, 12.0):                                                       # expressway dashes 6 m on / 6 m off
            d.rectangle([X(l - 0.06), int(v * PXV), X(l + 0.06), int((v + 6.0) * PXV) - 1], fill=edge)
    # shoulder grime toward the parapet + a drain slot every 12 m
    for sgn in (-1, 1):
        x0, x1 = (0, X(-5.6)) if sgn < 0 else (X(5.6), W)
        d.rectangle([x0, 0, x1, H], fill=(118, 118, 116))
        for v in np.arange(3.0, tile, 12.0):
            xa = X(sgn * 5.75); d.rectangle([min(xa, xa - 2 * sgn), int(v * PXV), max(xa, xa - 2 * sgn), int(v * PXV) + 5], fill=(40, 40, 44))
    # expansion joint at s = 40 m: steel finger plate (dark band, two bright steel edges) across the full deck
    jy = int(40.0 * PXV)
    d.rectangle([0, jy - 2, W, jy + 2], fill=(34, 36, 42)); d.line([0, jy - 3, W, jy - 3], fill=(96, 100, 108)); d.line([0, jy + 3, W, jy + 3], fill=(84, 88, 96))
    for x in range(0, W, 6): d.line([x, jy - 2, x, jy + 2], fill=(58, 60, 66))
    a = np.asarray(im).astype(np.float32) / 255
    light = np.tile(AMB, (H, W, 1)); add = np.zeros((H, W, 3), np.float32)
    vv, uu = np.mgrid[0:H, 0:W]
    for s_l, d_l in ((0.0, 1.7), (24.0, -1.7)):       # lamp heads (wangan_lamp arm) over the lanes, staggered every 24 m
        for rep in (-1, 0, 1):
            cv = (s_l + rep * tile) * PXV; cu = (W_m + d_l) * PXU
            dd = np.sqrt(((vv - cv) / PXV) ** 2 + ((uu - cu) / PXU) ** 2)
            lv = np.clip(1 - np.sqrt(dd ** 2 + 11.6 ** 2) / 19.0, 0, 1)                 # vertex pool from a head 11.6 m up
            light += (np.floor(lv * 3 * 2.2) / 3 / 2.2)[..., None] * SOD * 0.85 * 0.55 * 2.6
            dec = np.floor(np.clip(1 - dd / 8.0, 0, 1) ** 1.1 * 3) / 3                  # stepped decal, 8 m (taller head = wider pool)
            add += dec[..., None] * SOD * 0.09 * 1.8 * 2.2
    return Image.fromarray((np.clip(a * light + add, 0, 1) * 255).astype(np.uint8))
save(road(), 'wangan_road')

# ── parapet: cast concrete, u = around the profile (0 = road-side foot .. 1 = back foot), v = 4 m along ──
def parapet():
    W, H = 64, 64
    a = np.zeros((H, W, 3), np.float32)
    prof = np.linspace(0, 1, W)
    # road face: lit by the sodium pools (warm-neutral grey); top lighter; back face (toward the bay) darker navy
    col = np.where(prof[:, None] < 0.55, np.array([96, 102, 112]), np.where(prof[:, None] < 0.68, np.array([124, 128, 134]), np.array([46, 54, 70])))
    a[:] = col[None]
    a[:, :6] = (62, 64, 72)                       # kerb foot, dirty
    a += noise(W, H, 4, 10, 21)[..., None]
    for x in range(10, 34, 1):                    # rain streaks down the road face (vertical in u, faint)
        if R.random() < 0.18: a[:, x] -= R.uniform(4, 10)
    a[:2] = (40, 42, 48); a[-1:] = (40, 42, 48)   # 4 m contraction joint at the module ends
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(parapet(), 'wangan_parapet')

# ── deck fascia + underside: x = down the fascia (0 top .. 1 bottom), y = 6 m along ──
def fascia():
    W, H = 32, 64
    a = np.tile(np.array([52, 58, 72], np.float32), (H, W, 1)) + noise(W, H, 4, 8, 31)[..., None]
    a[:, :3] = (70, 74, 84)                       # cornice lip
    for y in range(0, H, 16): a[y:y + 1, 4:] -= 10   # formwork seams
    rr = random.Random(9)
    for _ in range(5):                            # a few faint drip streaks under the cornice (kept calm: big surface)
        y0 = rr.randrange(H); a[y0:y0 + 2, 3:3 + rr.randrange(6, 20)] -= 5
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(fascia(), 'wangan_fascia')
def underside():
    W, H = 32, 32
    a = np.tile(np.array([22, 28, 42], np.float32), (H, W, 1)) + noise(W, H, 4, 6, 41)[..., None]
    a[::16] -= 6
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(underside(), 'wangan_underside')

# ── pier concrete (columns + cap beam), lit only by spill from the deck: dark navy, lighter top ──
def pier():
    W, H = 32, 64
    a = np.zeros((H, W, 3), np.float32)
    t = np.linspace(0, 1, H)[:, None]             # v 0 = top
    a[:] = (np.array([60, 66, 80]) * (1 - t) + np.array([20, 28, 44]) * t)[:, None, :].reshape(H, 1, 3)
    a += noise(W, H, 4, 6, 51)[..., None]
    a[:, ::16] -= 5
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(pier(), 'wangan_pier')

# ── bay water: big soft surface, near-black navy, a few long horizontal ripple glints (no mirror floor) ──
def water():
    W, H = 128, 128
    a = np.tile(np.array([9, 17, 32], np.float32), (H, W, 1)) + noise(W, H, 16, 5, 61)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rr = random.Random(5)
    for _ in range(26):
        x, y, l = rr.randrange(W), rr.randrange(H), rr.randrange(6, 18)
        d.line([x, y, x + l, y], fill=(20, 32, 52))
    return im
save(water(), 'wangan_water')

# ── sodium reflection streak on the water (additive decal, x across, y along the view): soft stepped column ──
def streak():
    W, H = 32, 128
    yy, xx = np.mgrid[0:H, 0:W]
    rr = np.random.default_rng(4)
    wob = np.repeat(rr.normal(0, 2.2, (H // 4 + 1, 1)), 4, 0)[:H]   # each ripple row shifts sideways a little
    r = np.abs(xx - W / 2 + 0.5 - wob) / (W / 2)
    a = np.clip(1 - r * 1.4, 0, 1) * np.sin(np.clip(yy / H, 0, 1) * np.pi) ** 0.8
    rip = 0.55 + 0.45 * (rr.random((H // 3 + 1, 1)).repeat(3, 0)[:H] > 0.35)   # broken, not dashed
    a = np.floor(a * rip * 3) / 3
    rgb = np.tile(hx('#F0C894'), (H, W, 1)) * a[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
save(streak(), 'wangan_streak', q=False)

# ── wangan sky: Gordon's sky recipe (gen_art.py sky(): zenith #010408 -> fog #0B172B, t^1.8, bottom band = fog), but
#    2048 x 384 so the stars land as single dots on the 250 m cylinder instead of 2.5x tall streaks that read as rain ──
def sky(W=2048, H=384):
    hz = H // 2; a = np.tile(hx('#0B172B'), (H, 1)).astype(np.float32)
    t = (np.arange(hz) / hz)[:, None]; z, h = hx('#010408'), hx('#0B172B')
    a[:hz] = z[None] * (1 - t ** 1.8) + h[None] * t ** 1.8
    a[hz - 6:hz] = hx('#0B172B')
    a = np.repeat(a[:, None, :], W, 1); rng = np.random.default_rng(5)
    for _ in range(60 * W // 512):
        y, x = rng.integers(0, int(hz * .75)), rng.integers(0, W); a[y, x] = (90, 100, 150) if rng.random() < .8 else (130, 140, 180)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(sky(), 'wangan_sky')

# ── overhead sign panels: expressway green, white letters, generic route words only (no brands, no real exits) ──
def sign(lines, w=128, h=48, bg=(22, 74, 52)):
    im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], outline=(176, 190, 182))
    fs = [ImageFont.truetype(CJK, sz) for _, sz in lines]
    hs = [d.textbbox((0, 0), t, font=f)[3] - d.textbbox((0, 0), t, font=f)[1] for (t, _), f in zip(lines, fs)]
    gap = 3; y = (h - sum(hs) - gap * (len(lines) - 1)) / 2
    for (txt, sz), f, th in zip(lines, fs, hs):
        bb = d.textbbox((0, 0), txt, font=f); tw = bb[2] - bb[0]
        d.text(((w - tw) / 2 - bb[0], y - bb[1]), txt, font=f, fill=(206, 214, 208)); y += th + gap
    # night: retroreflective sheeting reads only where the gantry lamp hits; dim the lower half a touch
    a = np.asarray(im).astype(np.float32); a *= np.linspace(1.0, 0.78, h)[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(sign([('湾岸線', 16), ('BAYSHORE RTE', 10), ('東 EAST', 8)]), 'wangan_sign_0')
save(sign([('出口 2km', 16), ('EXIT', 10), ('3', 8)]), 'wangan_sign_1')
save(sign([('速度注意', 12), ('CURVE', 8)], w=64, h=32, bg=(30, 40, 72)), 'wangan_sign_2')     # small blue advisory board

# ── steel (gantry truss, crane, bridge): flat painted values, near side lit by the deck ──
def steel(c0, c1, n):
    W, H = 16, 32; t = np.linspace(0, 1, H)[:, None, None]
    a = np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t
    a = np.tile(a, (1, W, 1)) + noise(W, H, 4, 4, n)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
save(steel((92, 98, 108), (58, 64, 76), 71), 'wangan_steel')                 # gantry, km plates, lit by the road
save(steel((22, 32, 50), (14, 22, 38), 72), 'wangan_silhouette')            # far cranes + bridge: just off the fog
save(Image.new('RGB', (8, 8), (200, 60, 50)), 'emit_aviation')               # red aviation light (cranes, bridge towers)
save(Image.new('RGB', (8, 8), (214, 190, 140)), 'emit_bridge_lamp')         # bridge deck lamps: pale sodium, dimmed by fog
save(Image.new('RGB', (8, 8), (240, 200, 148)), 'emit_sodium')              # every lamp head #F0C894
# km post plate (white on dark green, tiny)
kp = Image.new('RGB', (16, 16), (24, 60, 44)); d = ImageDraw.Draw(kp); d.rectangle([0, 0, 15, 15], outline=(150, 160, 150))
d.text((2, 3), '14', fill=(200, 206, 200)); save(kp, 'wangan_kpost')
