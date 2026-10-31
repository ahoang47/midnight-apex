"""Painted equirect environment for the fake-shine shader (256x128, RGB555 + Bayer): dusk sky gradient, a bright
horizon band with a few street-light blobs, dark ground.  Neutral/cool so glass stays cool (A: untinted env -> orange glass)."""
import numpy as np, sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
W, H = 256, 128; out = sys.argv[1] if len(sys.argv) > 1 else 'brz_env.png'
v = (np.arange(H)[:, None] + .5) / H; u = (np.arange(W)[None, :] + .5) / W     # v 0 = zenith
el = (0.5 - v) * np.pi                                                          # elevation
sky = np.array([40, 52, 84]) + np.array([150, 160, 175]) * (np.clip(1 - el / 1.2, 0, 1) ** 3)[..., None]
gnd = np.array([22, 23, 26]) + np.array([40, 42, 46]) * (np.clip(1 + el / 0.5, 0, 1) ** 4)[..., None]
img = np.where((el > 0)[..., None], sky, gnd) * np.ones((1, W, 1))
band = np.exp(-((el - 0.03) / 0.035) ** 2)[..., None] * np.array([70, 74, 80]); img = img + band
rng = np.random.default_rng(7)
for k in range(9):                                                              # street-light blobs above the horizon
    cu, ce = rng.uniform(0, 1), rng.uniform(0.08, 0.30)
    d = ((np.minimum(np.abs(u - cu), 1 - np.abs(u - cu)) * 2 * np.pi) ** 2 + (el - ce) ** 2)
    img = img + np.exp(-d / 0.0015)[..., None] * np.array([235, 230, 215])
for k in range(6):                                                              # tall soft-box panels (studio-ish key reflections)
    cu = (k + 0.3) / 6; m = (np.abs(u - cu) < 0.025) & (el > 0.25) & (el < 0.9)
    img[m] = img[m] * 0.4 + np.array([230, 235, 245]) * 0.6
rgb555_bayer(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))).save(out); print('env', out)
