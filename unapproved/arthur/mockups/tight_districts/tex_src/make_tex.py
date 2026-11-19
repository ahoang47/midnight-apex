#!/usr/bin/env python3
"""Tight-district textures (Arthur, unapproved mockup, Austin 2026-11-15: cat-and-mouse only, roads "a little tight").
Hand-painted night values (everything is unlit in Godot), quantised RGB555 + 4x4 Bayer and saved lossless, the same
recipe as ../../../experiments/wangan_two_corner/tex_src/make_tex.py.
  python3 tex_src/make_tex.py  ->  godot/art/wangan_tight_road.png, godot/art/street_tight_road.png, godot/art/env/street_curvemirror.png
Road strips: x = across the asphalt (u 0..1 = -half .. +half), y = metres along (one lamp period per tile)."""
import os, random
import numpy as np
from PIL import Image, ImageDraw
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
