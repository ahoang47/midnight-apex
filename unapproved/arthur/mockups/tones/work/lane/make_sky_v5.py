"""v4 hand-built textures (no pack has them): night sky gradient whose bottom band == fog colour, and a stepped
sodium light-pool decal. Everything else comes from the asset packs or the Tokyo v2 vibe-check textures.
python3 make_sky_v4.py <tex_dir>"""
import sys, os, numpy as np
from PIL import Image
OUT = sys.argv[1]
FOG = np.array([0x26, 0x1F, 0x38], np.float32)     # fog colour, also the sky's horizon
ZEN = np.array([0x05, 0x05, 0x10], np.float32)
GLOWC = np.array([0x5A, 0x34, 0x40], np.float32)   # faint city glow just above the horizon
W, H = 512, 256
t = np.linspace(0, 1, H)[:, None]                  # 0 = top, 1 = horizon (bottom of the card)
col = ZEN[None] * (1 - t ** 1.8) + FOG[None] * t ** 1.8
g = np.clip((t - .72) / .2, 0, 1) * np.clip((1 - t) / .08, 0, 1)
col = col * (1 - .45 * g) + GLOWC[None] * .45 * g
col[-6:] = FOG                                     # exact fog band at the bottom
a = np.repeat(col[:, None, :], W, 1)
rng = np.random.default_rng(5)
for _ in range(70):
    x, y = rng.integers(0, W), rng.integers(0, int(H * .5)); a[y, x] = (110, 105, 130)
B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - .5
tt = np.tile(B, (H // 4, W // 4))[..., None]
q = (np.clip(np.floor(a / 8 + tt + .5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
Image.fromarray(q).save(os.path.join(OUT, 'sky_v4.png'))
# stepped (banded) sodium pool decal, alpha = strength, 4 hard bands like a painted PS2 light pool
S = 128; yy, xx = np.mgrid[0:S, 0:S]; r = np.sqrt((xx - S / 2 + .5) ** 2 + (yy - S / 2 + .5) ** 2) / (S / 2)
lv = np.floor(np.clip(1 - r, 0, 1) ** 1.1 * 4) / 4
rgba = np.dstack([np.full((S, S), 255), np.full((S, S), 150), np.full((S, S), 70), lv * 255]).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'pool_v4.png'))
print('sky/pool ->', OUT)
