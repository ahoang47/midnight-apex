"""Painted textures for the authored Touge terrain (Cel A soft: flat painted values, soft mottling, baked AO / crest gradient
across U where U spans a face). All quantised to RGB555 with a 4x4 Bayer at authoring time."""
import numpy as np
from PIL import Image
OUT = '/workspace/touge_env_build/assets/tex/kit/env/'
rng = np.random.default_rng(7)
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5
def noise(h, w, scale, seed):
    r = np.random.default_rng(seed).standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    k = np.exp(-(f * scale) ** 2)
    n = np.real(np.fft.ifft2(np.fft.fft2(r) * k)); n = (n - n.mean()) / (n.std() + 1e-9)
    return n
def q555(a):
    h, w = a.shape[:2]
    b = np.tile(B4, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    v = np.clip(a / 255.0 * 31.0 + b, 0, 31); v = np.floor(v + 0.5) / 31.0 * 255.0
    return np.clip(v, 0, 255).astype(np.uint8)
def save(a, n, alpha=None):
    rgb = q555(a)
    if alpha is not None: Image.fromarray(np.dstack([rgb, alpha.astype(np.uint8)]), 'RGBA').save(OUT + n)
    else: Image.fromarray(rgb, 'RGB').save(OUT + n)
# touge_hill: hillside / verge ground (palette of touge_verge.png, mean 37 62 59), soft scrub mottling
h = w = 128
base = np.array([36, 60, 56], float)
n1 = noise(h, w, 18, 1); n2 = noise(h, w, 5, 2); n3 = noise(h, w, 40, 3)
a = base[None, None, :] * (1 + 0.10 * n1[..., None] + 0.05 * n2[..., None])
a += np.array([4, 6, -2])[None, None, :] * np.clip(n3, 0, None)[..., None]      # drier olive patches
save(a, 'touge_hill.png')
# touge_cutface: the inside cut slope behind the lattice. U (x) base -> crest; V (y) tiles. AO at the toe, moss mid, grass lip on top.
h, w = 256, 128
x = np.linspace(0, 1, w)[None, :]
rock = np.array([54, 61, 67], float); moss = np.array([40, 56, 50], float); grass = np.array([34, 58, 52], float)
n1 = noise(h, w, 10, 4); n2 = noise(h, w, 30, 5)
mix_m = np.clip((n2 + 0.3) * 0.6, 0, 1)[..., None] * 0.6
col = rock[None, None] * (1 - mix_m) + moss[None, None] * mix_m
lip = np.clip((x - 0.86) / 0.08, 0, 1)[..., None]
col = col * (1 - lip) + grass[None, None] * lip
ao = (0.62 + 0.38 * np.clip(x / 0.35, 0, 1) ** 0.7)[..., None]                     # toe AO (baked)
col = col * ao * (1 + 0.08 * n1[..., None])
save(col, 'touge_cutface.png')
# touge_concrete: gallery walls, pilasters, deck soffit. Board-formed concrete, soft stains, faint lift lines every 2 m (U = m/8)
h = w = 128
base = np.array([66, 72, 80], float)
n1 = noise(h, w, 12, 6); n2 = noise(h, w, 50, 7)
col = base[None, None] * (1 + 0.06 * n1[..., None] + 0.05 * n2[..., None])
streak = noise(h, w * 4, 3, 8)[:, ::4]
col *= (1 - 0.06 * np.clip(streak, 0, None))[..., None]
for xl in range(0, w, 32): col[:, xl:xl + 1] *= 0.80                              # lift joints (across U, i.e. every 2 m up the wall)
save(col, 'touge_concrete.png')
# line_chevron: white chevron pointing +V (code tints), soft 2-3 px alpha edge, flat value (no gloss gradient)
h = w = 64
yy, xx = np.mgrid[0:h, 0:w].astype(float) + 0.5
u = (xx / w - 0.5) * 2; v = 1 - yy / h            # v = 0 tail .. 1 tip (texture top = +Z tip)
# chevron: band between two V lines  v = 0.86 - 0.62|u|  (outer) and v = 0.50 - 0.62|u| (inner), clipped to |u| < 0.92
outer = 0.88 - 0.70 * np.abs(u); inner = outer - 0.34
dist = np.minimum(outer - v, v - inner) * h * 0.55
dist = np.minimum(dist, (0.92 - np.abs(u)) * w * 0.5)
alpha = np.clip(dist / 2.5 + 0.5, 0, 1) * 255
rgb = np.full((h, w, 3), 236.0)
save(rgb, 'line_chevron.png', alpha)
print('ok')
