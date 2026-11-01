"""WRX STI wheel atlas, 256x256 (parts atlas budget), painted: u 0-.5 = wheel face disc (tyre sidewall + gold 10-spoke
rim, made-up sidewall marks), u .5-1 = tread strip.  The wheel mesh is a 10-sided cylinder; the rim exists only here.
RGB555 + Bayer.  python3 tex/make_wheel_wrx.py out.png"""
import numpy as np, sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
S = 256; out = sys.argv[1]
img = np.zeros((S, S, 3), np.float32)
# disc in the left half: centre (64, 64) of a 128 tile, radius 63 = tyre OD (.317 m)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) + 0.5
def disc(cx, cy, R):
    dx, dy = xx - cx, yy - cy; r = np.hypot(dx, dy) / R; a = np.arctan2(dy, dx); return r, a
for cy in (64, 192):                               # two copies (top: outer face, bottom: same) -> forgiving UVs
    r, a = disc(64, cy, 63.0)
    tyre = (r <= 1.0) & (r > 0.68)
    sh = 0.75 + 0.25 * np.clip((1 - r) / 0.32, 0, 1)
    col = np.zeros((S, S, 3), np.float32) + np.array([22, 22, 24]) * sh[..., None]
    marks = tyre & (r > 0.80) & (r < 0.88) & (np.abs(((a / (2 * np.pi) * 24) % 1) - 0.5) < 0.18) & (np.sin(a) > 0.3)
    col[marks] = (70, 70, 74)                       # made-up sidewall lettering blocks
    lip = (r <= 0.68) & (r > 0.62); col[lip] = (205, 175, 90)
    rim = r <= 0.62
    spoke = np.abs(((a / (2 * np.pi) * 10) % 1) - 0.5) < 0.17
    face = np.array([190, 155, 60]) * (0.85 + 0.15 * np.cos(a - 0.8))[..., None]
    col[rim & spoke] = face[rim & spoke]
    col[rim & ~spoke & (r > 0.22)] = (28, 24, 18)  # spoke gaps (dark, brake shadow; no caliper geometry)
    col[(r <= 0.22) & (r > 0.12)] = (175, 145, 55); col[r <= 0.12] = (60, 55, 40)
    m = r <= 1.0; img[m] = col[m]
    img[(r > 1.0) & (xx < 128) & (np.abs(yy - cy) < 64)] = (20, 20, 22)
# tread strip (right half): dark rubber with blocks
t = xx >= 128
blk = ((np.floor((xx - 128) / 8) + np.floor(yy / 16)) % 2 == 0)
img[t] = (24, 24, 26); img[t & blk & ((xx - 128) % 32 > 3) & ((xx - 128) % 32 < 29)] = (34, 34, 37)
rgb555_bayer(Image.fromarray(img.clip(0, 255).astype(np.uint8))).save(out); print('wheel atlas', out)
