"""Stock S2000 soft top fabric texture (512x512, PS2 style).
UV layout (set by build_softtop): u = along the car (0 = windshield header, 1 = rear edge on the deck; u = (0.03 - x) / 1.40),
v = across (0.5 = centre line, 0.2 / 0.8 = roof-edge seams, 0 / 1 = bottom of the quarter panels at the body shoulder)."""
import numpy as np, sys
from PIL import Image, ImageDraw
dst = sys.argv[1]; S = 512
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:S, 0:S]
# canvas weave: 2px over/under with fibre noise and soft mottling
weave = np.where(((xx // 2) + (yy // 2)) % 2 == 0, 1.0, -1.0) * np.where((xx + yy) % 2 == 0, 1.0, 0.6)
low = np.asarray(Image.fromarray((rng.random((16, 16)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)) / 255.0
v = 30 + 3.2 * weave + rng.normal(0, 1.6, (S, S)) + 4 * (low - .5)
V = 1 - (yy + .5) / S          # uv v of each pixel row (PIL row 0 = v 1)
U = (xx + .5) / S
roof = (V > .2) & (V < .8)
v = v * np.where(roof, 1.0, 0.86)                       # sides a touch darker than the top-lit roof
v *= 1 - 0.10 * np.clip(1 - np.abs(V - .5) / .3, 0, 1) * 0   # (flat roof, no fake crown)
img = np.stack([v, v, v * 1.06], -1)
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
px = lambda u, vv: (u * S, (1 - vv) * S)
def u_of(x): return (0.03 - x) / 1.40
# bow ridges (painted): lit crest + shadow just behind it, across the roof only
for xb in (-0.39, -0.70, -0.82):
    u = u_of(xb) * S
    d.rectangle([u - 3, .2 * S + 2, u + 1, .8 * S - 2], fill=(42, 42, 45))
    d.rectangle([u + 2, .2 * S + 2, u + 6, .8 * S - 2], fill=(19, 19, 20))
# B-pillar seam continuing down the quarter panels
uB = u_of(-0.70) * S
for a, b in ((0, .2), (.8, 1)):
    d.line([(uB + 2, (1 - b) * S), (uB + 2, (1 - a) * S)], fill=(14, 14, 15), width=2)
# roof-edge seams: groove + twin stitch rows
for vv in (.2, .8):
    r = (1 - vv) * S
    d.line([(0, r), (S, r)], fill=(12, 12, 13), width=3)
    for off in (-5, 5):
        for k in range(0, S, 6): d.line([(k, r + off), (k + 3, r + off)], fill=(52, 52, 55), width=1)
# rear window surround stitching (window ~x -0.90..-1.31, half-width .45/.49 m -> v .5 +/- ~.21/.23)
def win_poly(grow):
    u0, u1 = u_of(-0.875 + grow) , u_of(-1.335 - grow)
    hf, hr = .21 + grow * .3 / .64, .23 + grow * .3 / .64
    return [px(u0, .5 - hf), px(u0, .5 + hf), px(u1, .5 + hr), px(u1, .5 - hr)]
d.polygon(win_poly(.018), outline=(12, 12, 13), width=3)
pts = win_poly(.03)
for i in range(4):
    (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 4]; L = int(np.hypot(x1 - x0, y1 - y0) / 6)
    for k in range(L):
        t0, t1 = k / L, (k + .5) / L
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=(52, 52, 55), width=1)
# bound edges: header strip and the rear edge where the top meets the deck
d.rectangle([0, 0, 7, S], fill=(18, 18, 19)); d.line([(9, 0), (9, S)], fill=(50, 50, 53), width=1)
d.rectangle([S - 8, 0, S, S], fill=(14, 14, 15)); d.line([(S - 10, 0), (S - 10, S)], fill=(50, 50, 53), width=1)
# soft fold shading at the quarter-panel bottoms (fabric pulls tight to the shoulder)
a = np.asarray(im).astype(np.float32)
a *= (1 - 0.25 * np.clip((0.07 - np.minimum(V, 1 - V)) / 0.07, 0, 1))[..., None]
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst); print('softtop texture', dst)
