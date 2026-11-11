"""Per-tone hand-built textures: sky gradient (bottom band == fog), stepped lamp-pool decal, lamp glow sprite.
Built the same way as lane_chain/v5/make_sky_v5.py. python3 make_tone_tex.py <tex_dir>"""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from tones import TONES
OUT = sys.argv[1]
B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - .5
def q555(a):
    h, w = a.shape[:2]; tt = np.tile(B, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + tt + .5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
def h3(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
glow_src = np.asarray(Image.open(os.path.join(OUT, 'glow_sodium.png')).convert('RGBA')).astype(np.float32)
for name, T in TONES.items():
    FOG, ZEN = h3(T['fog']), h3(T['zen']); W, H = 512, 256
    t = np.linspace(0, 1, H)[:, None]
    col = ZEN[None] * (1 - t ** 1.8) + FOG[None] * t ** 1.8
    if T['cityglow']:
        g = np.clip((t - .72) / .2, 0, 1) * np.clip((1 - t) / .08, 0, 1); col = col * (1 - .45 * g) + h3(T['cityglow'])[None] * .45 * g
    col[-6:] = FOG
    a = np.repeat(col[:, None, :], W, 1); rng = np.random.default_rng(5)
    if T['stars']:
        for _ in range(70):
            x, y = rng.integers(0, W), rng.integers(0, int(H * .5)); a[y, x] = T['stars']
    Image.fromarray(q555(a)).save(os.path.join(OUT, f'sky_{name}.png'))
    S = 128; yy, xx = np.mgrid[0:S, 0:S]; r = np.sqrt((xx - S / 2 + .5) ** 2 + (yy - S / 2 + .5) ** 2) / (S / 2)
    n = T['pool_tex_steps']; lv = np.floor(np.clip(1 - r, 0, 1) ** 1.1 * n) / n
    for li, lc in enumerate(T['lamps']):
        c = h3(lc) if name != 'sodium' else np.array([255, 150, 70], np.float32)
        rgba = np.dstack([np.full((S, S), c[0]), np.full((S, S), c[1]), np.full((S, S), c[2]), lv * 255]).astype(np.uint8)
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'pool_{name}_{li}.png'))
        if T['glow_tex'] is None: gl = glow_src.copy()
        else:
            tint = h3(lc) if T['glow_tex'] == 'per-lamp' else h3(T['glow_tex'])
            al = glow_src[..., 3:] / 255
            core = (al > .8).astype(np.float32)                       # small white-hot core, hard edged
            rgb = tint[None, None] * .8 * (1 - core) + np.array([255, 245, 235.]) * core
            al = np.floor(al * 3) / 3                                 # 3 hard alpha bands, no soft halo
            gl = np.dstack([np.clip(np.broadcast_to(rgb, glow_src[..., :3].shape), 0, 255), al * 255])
        Image.fromarray(gl.astype(np.uint8), 'RGBA').save(os.path.join(OUT, f'glow_{name}_{li}.png'))
print('tone tex ->', OUT)
