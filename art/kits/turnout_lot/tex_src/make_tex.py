#!/usr/bin/env python3
"""Turnout parking-lot textures. Night navy/teal + pale sodium (B.2a), RGB555 + 4x4 Bayer.
Asphalt and terrain stay smooth (no toon steps). Prop textures get three painted toon bands.
Sodium pools are a soft radial falloff — no rings. Decals are flat paint with alpha (no ink).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'tex'))
os.makedirs(OUT, exist_ok=True)

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5

def hx(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)

FOG = hx('#0B172B')
ZEN = hx('#010408')
AMB = hx('#5575A0')
SOD = hx('#F0C894')
INK = hx('#040810')

def quant555(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32)
    h, w = a.shape[:2]
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = np.clip(np.floor(a[..., :3] / 8.0 + t + 0.5), 0, 31) * (255.0 / 31.0)
    return Image.fromarray(np.dstack([np.clip(np.round(rgb), 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')

def save(im, name):
    p = os.path.join(OUT, name + '.png')
    quant555(im).save(p)
    print('tex', name, im.size)

def noise(w, h, scale, amp, seed):
    rng = np.random.default_rng(seed)
    n = rng.random((h // scale + 2, w // scale + 2))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (n - 0.5) * amp

def arr_to_im(a, alpha=None):
    rgb = np.clip(a, 0, 255).astype(np.uint8)
    if alpha is None:
        return Image.fromarray(rgb, 'RGB').convert('RGBA')
    return Image.fromarray(np.dstack([rgb, np.clip(alpha, 0, 255).astype(np.uint8)]), 'RGBA')

# ── tiling dry-matte lot / road asphalt (smooth, no toon, no rings) ──────────
def asphalt(name, w, h, seed, lift=0.0, seam=True):
    """w,h in pixels. Night dry asphalt with cool ambient fill and subtle patches."""
    base = np.array([28.0, 36.0, 52.0])  # navy-leaning dry matte
    a = np.zeros((h, w, 3), np.float32)
    a += base
    a += noise(w, h, 1, 6, seed)[..., None]
    a += noise(w, h, 4, 8, seed + 1)[..., None]
    a += noise(w, h, 16, 10, seed + 2)[..., None]
    # cooler ambient wash, very soft
    a += AMB * (0.10 + lift)
    # darker oil patches
    rng = np.random.default_rng(seed + 9)
    patch = noise(w, h, 32, 1, seed + 3)
    a += np.clip(patch, -1, 0)[..., None] * np.array([8, 8, 6])
    # faint tar seams along v (tileable)
    if seam:
        yy = np.arange(h)[:, None]
        for k, y0 in enumerate((0, h // 2)):
            d = np.minimum((yy - y0) % h, (y0 - yy) % h)
            line = np.exp(-((d.astype(np.float32) / 1.6) ** 2)) * (4.0 if k == 0 else 2.5)
            a -= line[..., None] * np.array([6, 5, 4])
    a = np.clip(a, 0, 255)
    save(arr_to_im(a), name)

def lot_asphalt():
    # 8 m x 8 m tile at 32 px/m — tiling, no baked pools (pools are a soft decal)
    asphalt('lot_asphalt', 256, 256, seed=11, lift=0.0, seam=True)

def road_asphalt():
    # 7.5 m wide x 8 m along, 32 px/m → 240 x 256. Slightly lighter than the lot so the two read apart.
    asphalt('lot_road', 240, 256, seed=21, lift=0.04, seam=True)

# ── soft sodium pool decal (smooth falloff, never rings) ─────────────────────
def lot_pool():
    # 10 m x 10 m, 32 px/m
    s, ppm = 10.0, 32
    n = int(s * ppm)
    yy, xx = np.mgrid[0:n, 0:n]
    cx = cy = (n - 1) / 2.0
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / ppm
    t = np.clip(r / 4.6, 0, 1)  # visible radius ~4.6 m, fades to 0
    # C2-smooth, no shoulder: (1-t)^2 * (1+2t) would have a flatter crown;
    # use a raised-cosine squared so the derivative is 0 at the edge (no ring after dither).
    fall = np.cos(0.5 * np.pi * t) ** 2
    fall = np.where(t >= 1, 0, fall)
    # slight vertical stretch so a lamp-arm offset still reads oval-soft, not a circle stamp
    alpha = np.clip(fall * 255 * 0.72, 0, 255)
    col = SOD * fall[..., None]  # premultiplied-looking colour; we'll use straight alpha
    rgb = np.broadcast_to(SOD, (n, n, 3)).copy()
    save(arr_to_im(rgb, alpha), 'lot_pool')

def lot_glow():
    # additive lamp-head sprite, 64x64
    n = 64
    yy, xx = np.mgrid[0:n, 0:n]
    cx = cy = (n - 1) / 2.0
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (n * 0.48)
    t = np.clip(r, 0, 1)
    fall = np.cos(0.5 * np.pi * t) ** 2
    fall = np.where(t >= 1, 0, fall)
    core = np.clip(1.0 - r * 2.4, 0, 1) ** 2
    rgb = SOD * (0.55 + 0.45 * core)[..., None] + np.array([255, 250, 230]) * (core * 0.35)[..., None]
    alpha = np.clip((fall * 0.85 + core * 0.4) * 255, 0, 255)
    save(arr_to_im(rgb, alpha), 'lot_glow')

# ── flat paint decals (alpha, no ink) ────────────────────────────────────────
def _paint_rgb(fill, w, h):
    return np.broadcast_to(np.asarray(fill, np.float32), (h, w, 3)).copy()

def lot_decal_stall():
    # 0.20 m x 5.0 m solid white line, hard edges (crisp paint, not a feathered decal).
    ppm, width_m, len_m = 64, 0.20, 5.0
    w, h = int(width_m * ppm), int(len_m * ppm)
    col = np.array([226.0, 224.0, 216.0])
    a = np.full((h, w), 255, np.float32)
    save(arr_to_im(_paint_rgb(col, w, h), a), 'lot_decal_stall')

def lot_decal_solid_white():
    """A tiny solid white tile for geometry paint (stall lines, arrows, edge)."""
    col = np.array([226.0, 224.0, 216.0])
    save(arr_to_im(_paint_rgb(col, 16, 16), np.full((16, 16), 255, np.float32)), 'lot_paint_white')

def lot_decal_solid_chevron():
    """A tiny solid terracotta tile for geometry chevron bands."""
    col = np.array([176.0, 70.0, 42.0])
    save(arr_to_im(_paint_rgb(col, 16, 16), np.full((16, 16), 255, np.float32)), 'lot_paint_chevron')

def lot_decal_edge():
    # 0.15 m x 4.0 m white edge line
    ppm, width_m, len_m = 64, 0.15, 4.0
    w, h = int(width_m * ppm), int(len_m * ppm)
    col = np.array([214.0, 212.0, 204.0])
    a = np.full((h, w), 255, np.float32)
    save(arr_to_im(_paint_rgb(col, w, h), a), 'lot_decal_edge')

def lot_decal_center():
    # 0.15 m x 4.0 m yellow centre line
    ppm, width_m, len_m = 64, 0.15, 4.0
    w, h = int(width_m * ppm), int(len_m * ppm)
    col = np.array([196.0, 158.0, 48.0])  # muted night yellow
    a = np.full((h, w), 255, np.float32)
    save(arr_to_im(_paint_rgb(col, w, h), a), 'lot_decal_center')

def lot_decal_arrow():
    # 0.9 m wide x 2.6 m long, white painted arrow pointing +V
    ppm = 64
    w, h = int(0.9 * ppm), int(2.6 * ppm)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (210, 208, 200, 255)
    # shaft
    x0, x1 = int(w * 0.32), int(w * 0.68)
    y0, y1 = int(h * 0.38), int(h * 0.96)
    d.rectangle([x0, y0, x1, y1], fill=col)
    # head
    tip = (w // 2, int(h * 0.04))
    d.polygon([tip, (int(w * 0.06), int(h * 0.42)), (int(w * 0.94), int(h * 0.42))], fill=col)
    save(im, 'lot_decal_arrow')

def lot_decal_chevron():
    # Solid filled orange-red rumble chevron, pointing +V (direction of travel),
    # like the Hakone photo (a painted band, not an outline).
    # 3.0 m wide (most of the 3.75 m lane) x 2.4 m along.
    ppm = 64
    w, h = int(3.0 * ppm), int(2.4 * ppm)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (176, 70, 42, 255)  # night-muted terracotta, still reads as the photo's orange-red
    cx = w / 2
    # Filled chevron (solid V): tip at the top of the image, wide base at the bottom,
    # thick enough to read as a painted band. PIL y=0 is the top of the file = V=1 in Blender.
    tip_y = int(h * 0.04)
    base_y = int(h * 0.96)
    half = w * 0.48
    thick = int(0.55 * ppm)  # ~0.55 m thick band
    outer = [(cx, tip_y), (cx - half, base_y), (cx + half, base_y)]
    # cut a smaller V out of the base so the chevron is a solid band, not a solid triangle
    # For a FILLED band like the photo, the photo's marks are solid arrow-heads / filled Vs.
    # Use a solid triangle-ish chevron with a slightly concave back so they nest.
    back = int(h * 0.42)
    poly = [
        (cx, tip_y),
        (int(cx - half), base_y),
        (int(cx - half + thick * 1.15), base_y),
        (cx, tip_y + thick),
        (int(cx + half - thick * 1.15), base_y),
        (int(cx + half), base_y),
    ]
    # Actually: solid filled chevron (the whole V-arrow is filled paint), not a hollow ring.
    # A filled arrow-head / chevron bar:
    solid = [
        (cx, tip_y),
        (int(cx - half), base_y),
        (int(cx + half), base_y),
    ]
    d.polygon(solid, fill=col)
    save(im, 'lot_decal_chevron')

# ── prop textures: three hard toon bands, painted, navy shadow ───────────────
def _bands(lit, mid, sh, w, h, kind, seed):
    """kind: 'top' (mostly lit), 'side' (mid with a lit lip), 'post' (vertical gradient)."""
    a = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    xx = np.linspace(0, 1, w)[None, :]
    if kind == 'top':
        # mostly lit, mid in one corner, a single hard highlight stripe
        a += mid
        a = np.where((yy < 0.72)[..., None], lit, a)
        hi = lit * 1.08 + np.array([12, 8, 0])
        a = np.where(((yy > 0.18) & (yy < 0.28) & (xx > 0.1) & (xx < 0.85))[..., None], hi, a)
        a = np.where((yy > 0.90)[..., None], sh, a)
    elif kind == 'side':
        a += mid
        a = np.where((yy < 0.22)[..., None], lit, a)
        a = np.where((yy > 0.78)[..., None], sh, a)
    else:  # post / vertical
        a += mid
        a = np.where((xx < 0.35)[..., None], lit, a)
        a = np.where((xx > 0.78)[..., None], sh, a)
        a = np.where(((xx > 0.12) & (xx < 0.20))[..., None], lit * 1.06 + np.array([10, 7, 0]), a)
    a += noise(w, h, 2, 4, seed)[..., None]
    a += noise(w, h, 8, 5, seed + 1)[..., None]
    return np.clip(a, 0, 255)

def lot_curb():
    # concrete: cool grey with a sodium-warm lit band on the top
    lit = np.array([118.0, 112.0, 104.0]) + SOD * 0.10
    mid = np.array([78.0, 80.0, 86.0])
    sh = np.array([32.0, 38.0, 52.0])
    save(arr_to_im(_bands(lit, mid, sh, 128, 128, 'top', 40)), 'lot_curb')

def lot_wheel_stop():
    lit = np.array([130.0, 122.0, 110.0]) + SOD * 0.08
    mid = np.array([88.0, 86.0, 84.0])
    sh = np.array([36.0, 40.0, 50.0])
    save(arr_to_im(_bands(lit, mid, sh, 64, 64, 'side', 41)), 'lot_wheel_stop')

def lot_guardrail():
    # Pale / white-painted W-beam (the ref is a white rail). Night: still reads white,
    # with a sodium-warm lit band and a navy-leaning crease shadow.
    lit = np.array([198.0, 196.0, 188.0]) + SOD * 0.12
    mid = np.array([152.0, 150.0, 148.0])
    sh = np.array([58.0, 62.0, 74.0])
    save(arr_to_im(_bands(lit, mid, sh, 64, 128, 'side', 42)), 'lot_guardrail')

def lot_metal():
    lit = np.array([90.0, 88.0, 86.0]) + SOD * 0.08
    mid = np.array([58.0, 58.0, 62.0])
    sh = np.array([26.0, 28.0, 38.0])
    save(arr_to_im(_bands(lit, mid, sh, 64, 64, 'post', 43)), 'lot_metal')

def lot_pole():
    # concrete-ish lamp post, slightly warmer than raw metal
    lit = np.array([96.0, 90.0, 80.0]) + SOD * 0.10
    mid = np.array([62.0, 60.0, 58.0])
    sh = np.array([28.0, 30.0, 40.0])
    save(arr_to_im(_bands(lit, mid, sh, 64, 128, 'post', 44)), 'lot_pole')

def emit_sodium():
    # flat head colour, full-bright in engine
    im = Image.new('RGBA', (16, 8), tuple(int(x) for x in SOD) + (255,))
    save(im, 'emit_sodium')

def lot_vending_body():
    lit = np.array([72.0, 78.0, 88.0])
    mid = np.array([48.0, 52.0, 62.0])
    sh = np.array([22.0, 26.0, 38.0])
    save(arr_to_im(_bands(lit, mid, sh, 64, 64, 'post', 45)), 'lot_vending_body')

def emit_vending_front():
    # Small painted front: dark cabinet, two paler drink bands, a faint sodium door glow.
    w, h = 64, 128
    a = np.zeros((h, w, 3), np.float32)
    a += np.array([28.0, 32.0, 42.0])
    a[8:16, 8:56] = np.array([40.0, 48.0, 62.0])          # header plate
    a[20:54, 10:54] = np.array([36.0, 70.0, 86.0])         # cool window
    a[20:54, 10:54] += SOD * 0.12
    a[58:90, 10:54] = np.array([86.0, 44.0, 40.0])         # warm window
    a[96:118, 10:54] = np.array([22.0, 24.0, 30.0])        # tray
    # a couple of can dots
    a[28:36, 18:28] = SOD * 0.55 + np.array([40, 40, 40])
    a[28:36, 34:44] = np.array([180.0, 40.0, 40.0])
    a[66:74, 18:28] = np.array([40.0, 80.0, 160.0])
    a[66:74, 34:44] = np.array([40.0, 140.0, 70.0])
    a += noise(w, h, 2, 3, 46)[..., None]
    save(arr_to_im(np.clip(a, 0, 255)), 'emit_vending_front')

def lot_sign_face():
    # Large, hard-edged parking plate: saturated blue + a blocky white P, no anti-alias.
    w, h = 128, 160
    im = Image.new('RGBA', (w, h), (24, 72, 168, 255))
    d = ImageDraw.Draw(im)
    # white border
    d.rectangle([0, 0, w - 1, h - 1], outline=(230, 228, 220, 255), width=8)
    d.rectangle([8, 8, w - 9, h - 9], outline=(230, 228, 220, 255), width=2)
    # blocky P (pixel-clean, no font AA)
    col = (236, 234, 226, 255)
    # stem
    d.rectangle([28, 28, 48, 132], fill=col)
    # bowl
    d.rectangle([48, 28, 96, 88], fill=col)
    d.rectangle([48, 44, 80, 72], fill=(24, 72, 168, 255))
    save(im, 'lot_sign_face')

def lot_verge():
    # Dark forest floor / grass lip, smooth, no toon. 4 m x 4 m.
    w = h = 128
    base = np.array([18.0, 28.0, 24.0])
    a = np.zeros((h, w, 3), np.float32) + base
    a += noise(w, h, 2, 6, 50)[..., None]
    a += noise(w, h, 8, 8, 51)[..., None]
    # cooler in the cracks
    patch = noise(w, h, 16, 1, 52)
    a += patch[..., None] * np.array([4, 8, 6])
    a += AMB * 0.04
    save(arr_to_im(np.clip(a, 0, 255)), 'lot_verge')

def lot_cut_slope():
    # Inside-of-bend drop: dark earth / rock, smooth.
    w, h = 128, 256
    base = np.array([24.0, 26.0, 28.0])
    a = np.zeros((h, w, 3), np.float32) + base
    a += noise(w, h, 2, 5, 60)[..., None]
    a += noise(w, h, 8, 8, 61)[..., None]
    a += noise(w, h, 32, 7, 62)[..., None]
    yy = np.linspace(0, 1, h)[:, None]
    a += (1 - yy)[..., None] * np.array([4, 8, 6])  # slightly greener toward the top lip
    a += AMB * 0.05
    save(arr_to_im(np.clip(a, 0, 255)), 'lot_cut_slope')

def lot_sky():
    # Vertical gradient, zenith at v=1, fog/horizon at v=0. 32 x 256.
    w, h = 32, 256
    yy = np.linspace(0, 1, h)[:, None, None]
    # smooth ease, no banding before dither
    t = yy * yy * (3 - 2 * yy)
    col = FOG * (1 - t) + ZEN * t
    a = np.broadcast_to(col, (h, w, 3)).copy()
    save(arr_to_im(a), 'lot_sky')

def main():
    lot_asphalt(); road_asphalt()
    lot_pool(); lot_glow()
    lot_decal_stall(); lot_decal_edge(); lot_decal_center()
    lot_decal_arrow(); lot_decal_chevron()
    lot_decal_solid_white(); lot_decal_solid_chevron()
    lot_curb(); lot_wheel_stop(); lot_guardrail()
    lot_metal(); lot_pole(); emit_sodium()
    lot_vending_body(); emit_vending_front(); lot_sign_face()
    lot_verge(); lot_cut_slope(); lot_sky()
    print('wrote textures to', OUT)

if __name__ == '__main__':
    main()
