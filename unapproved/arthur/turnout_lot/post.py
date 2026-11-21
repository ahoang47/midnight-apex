#!/usr/bin/env python3
"""Cel A soft post: linear fog, 1px prop ink, soft sodium bloom, RGB555 + Bayer.
Surfaces, decals and pools get no ink. 640x480, no AA, integer nearest upscale for the sheet.
"""
import os, glob
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'renders', 'raw')
OUT = os.path.join(HERE, 'renders')
os.makedirs(OUT, exist_ok=True)

FOG = np.array([0x0B, 0x17, 0x2B], np.float32)
INK = np.array([0x04, 0x08, 0x10], np.float32)
SOD = np.array([0xF0, 0xC8, 0x94], np.float32)
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)

# mist 0-1 = 0-120 m; fog 14-105 m (B.3 / Tokyo v2)
FOG_START, FOG_END, DEPTH_MAX = 14.0, 105.0, 120.0

def rgb555(a):
    h, w = a.shape[:2]
    t = (B4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4] + 0.5) / 16.0 - 0.5
    q = np.floor(a / 255.0 * 31.0 + 0.5 + t[..., None])
    return np.clip(q, 0, 31) * (255.0 / 31.0)

def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode)).astype(np.float32)

def depth_m(path):
    # 16-bit PNG, 0-1 = 0-120 m. Blender writes this override pass vertically flipped
    # relative to the beauty / mask PNGs (the mask is not flipped).
    im = Image.open(path)
    a = np.asarray(im)
    if a.ndim == 3:
        a = a[..., 0]
    if a.dtype == np.uint16:
        z = a.astype(np.float32) / 65535.0 * DEPTH_MAX
    else:
        z = a.astype(np.float32) / 255.0 * DEPTH_MAX
    return np.flipud(z)

def fog_amt(z):
    return np.clip((z - FOG_START) / (FOG_END - FOG_START), 0, 1)

def ink_mask(mask):
    """Props (red) get ink. Cards (cyan) get a lighter ink. Decals/surfaces/pools do not.
    Mask colours are Standard-view (sRGB) encodings of the linear KIND_COLOR values, so
    0.15 linear lands around 90-110, not 38."""
    r, g, b = mask[..., 0], mask[..., 1], mask[..., 2]
    prop = (r > 180) & (g < 140) & (b < 140)
    card = (r < 140) & (g > 180) & (b > 180)
    return prop, card

def near_ink(depth, mask_prop, fog):
    """1 px ink on the prop/card side of a silhouette (against a non-prop neighbour).
    Depth-jump edges on the ground are ignored: at a 47° grazing chase cam they fire on
    every road pixel and scribble. Lines fade into fog."""
    h, w = mask_prop.shape
    p = np.pad(mask_prop, 1, mode='edge')
    sil = np.zeros((h, w), np.bool_)
    sil |= p[1:-1, 1:-1] & ~p[1:-1, 2:]
    sil |= p[1:-1, 1:-1] & ~p[1:-1, 0:-2]
    sil |= p[1:-1, 1:-1] & ~p[2:, 1:-1]
    sil |= p[1:-1, 1:-1] & ~p[0:-2, 1:-1]
    strength = (1.0 - np.clip(fog, 0, 1)) * sil.astype(np.float32)
    return strength

def bloom(rgb, mask, emit_mask):
    # soft sodium bloom, 0.22 strength, 0 threshold on emit + glow pixels, slight colour bias
    lit = rgb * emit_mask[..., None]
    # also pick up already-bright sodium pixels
    warm = np.clip((rgb[..., 0] * 0.5 + rgb[..., 1] * 0.4 - rgb[..., 2] * 0.2 - 80) / 80, 0, 1)
    lit = np.maximum(lit, rgb * (warm * 0.5)[..., None])
    im = Image.fromarray(np.clip(lit, 0, 255).astype(np.uint8))
    b1 = np.asarray(im.filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32)
    b2 = np.asarray(im.filter(ImageFilter.GaussianBlur(4.5))).astype(np.float32)
    return 0.14 * b1 + 0.08 * b2  # ~0.22 combined

def emit_from_mask(mask):
    r, g, b = mask[..., 0], mask[..., 1], mask[..., 2]
    emit = (r > 180) & (g > 180) & (b < 140)    # yellow = emit
    pool = (r > 180) & (g < 160) & (b > 180)    # magenta = pool
    return emit | pool

def process(name):
    beauty = os.path.join(RAW, name + '_beauty.png')
    mask_p = os.path.join(RAW, name + '_mask.png')
    depth_p = os.path.join(RAW, name + '_depth.png')
    if not (os.path.exists(beauty) and os.path.exists(mask_p) and os.path.exists(depth_p)):
        print('skip (missing raw)', name)
        return None
    rgb = load(beauty)
    mask = load(mask_p)
    # masks may be a few px off if filter leaked; they should be 640x480
    if mask.shape[:2] != rgb.shape[:2]:
        mask = np.asarray(Image.fromarray(mask.astype(np.uint8)).resize((rgb.shape[1], rgb.shape[0]), Image.NEAREST)).astype(np.float32)
    z = depth_m(depth_p)
    if z.shape != rgb.shape[:2]:
        z = np.asarray(Image.fromarray((np.clip(z / DEPTH_MAX, 0, 1) * 65535).astype(np.uint16), 'I;16').resize((rgb.shape[1], rgb.shape[0]), Image.NEAREST), np.float32) / 65535.0 * DEPTH_MAX
    # world-background pixels have z ~ 0; treat as a sky gradient (zenith at the top, fog at the horizon)
    sky = z < 0.6
    h = z.shape[0]
    yy = np.linspace(1, 0, h)[:, None]  # 1 at top
    sky_col = FOG * (1 - yy * yy) + np.array([0x01, 0x04, 0x08], np.float32) * (yy * yy)
    sky_col = np.broadcast_to(sky_col[:, None, :], (h, z.shape[1], 3))
    z_fix = np.where(sky, FOG_END, z)
    fog = fog_amt(z_fix)
    prop, card = ink_mask(mask)
    ink_s = near_ink(z, prop, fog)  # cards are alpha cut-outs; inking the quad draws a box
    emit = emit_from_mask(mask)
    blo = bloom(rgb, mask, emit)
    out = rgb + blo
    # ink on top of beauty+bloom, before fog, then fade with fog
    out = out * (1.0 - ink_s)[..., None] + INK * ink_s[..., None]
    out = out * (1.0 - fog)[..., None] + FOG * fog[..., None]
    if sky.any():
        out = np.where(sky[..., None], sky_col, out)
    out = np.clip(out, 0, 255)
    q = rgb555(out)
    im = Image.fromarray(np.round(q).astype(np.uint8), 'RGB')
    dest = os.path.join(OUT, name + '_640.png')
    im.save(dest)
    print('post', dest)
    return dest

def main():
    names = []
    for fn in sorted(os.listdir(RAW)):
        if fn.endswith('_beauty.png'):
            names.append(fn[:-len('_beauty.png')])
    if not names:
        names = ['race_cam', 'overhead', 'close_island', 'close_stalls', 'close_lamp', 'close_entry']
    for n in names:
        process(n)

if __name__ == '__main__':
    main()
