"""Overworld v1 textures.
- houses_lit.png: night variant of the URBAN pack's houses.png atlas (pack texture, recoloured): glass pixels become
  lamp-lit warm glass, frames darken. Picked per face by the 'Lit' vertex attribute in build_ow.py.
- meet_ring.png (hand-built): stepped amber ground ring with four chevrons for the meet marker decal.
python3 make_tex_ow.py tex"""
import sys, os, numpy as np
from PIL import Image
OUT = sys.argv[1]
SRC = '/workspace/asset_packs/psx-style-urban-stacked-pack/x/URBAN/textures/houses.png'
WIN = [(130, 130, 188, 248, 'blue'), (400, 130, 460, 248, 'blue'), (190, 130, 242, 195, 'dark'), (693, 95, 766, 188, 'dark')]
a = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32); lit = a * 0.35
for x0, y0, x1, y1, k in WIN:
    r = a[y0:y1, x0:x1]; lum = r.mean(-1, keepdims=True)
    glass = (r[..., 2] > r[..., 0] + 25) if k == 'blue' else (lum[..., 0] < 80)
    warm = np.array([255, 210, 140], np.float32) * (0.78 + 0.35 * (lum / 255))
    blk = lit[y0:y1, x0:x1]; blk[glass] = np.clip(warm, 0, 255)[glass]; lit[y0:y1, x0:x1] = blk
B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - .5
def q555(x):
    h, w = x.shape[:2]; t = np.tile(B, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(x / 8 + t + .5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
Image.fromarray(q555(lit)).save(os.path.join(OUT, 'houses_lit.png'))
# meet ring: 4 hard bands, chevrons pointing inward, alpha = strength (additive decal)
S = 256; yy, xx = np.mgrid[0:S, 0:S]; cx = S / 2 - .5; r = np.hypot(xx - cx, yy - cx) / (S / 2); ang = np.arctan2(yy - cx, xx - cx)
al = np.zeros((S, S), np.float32)
al[(r > .80) & (r < .92)] = 1.0; al[(r > .70) & (r < .76)] = .55
for k in range(4):
    a0 = k * np.pi / 2; d = np.abs(((ang - a0 + np.pi) % (2 * np.pi)) - np.pi)
    al[(r > .46) & (r < .64) & (d < (r - .44) * .9)] = .8
al[r < .12] = .35
rgba = np.dstack([np.full((S, S), 255), np.full((S, S), 170), np.full((S, S), 40), al * 255]).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'meet_ring.png'))
print('ok')
# Kenney retro-urban-kit windows.png -> windows_lit.png (pack texture, recoloured glass)
K = '/workspace/asset_packs/retro-urban-kit/x/Models/GLB format/Textures/windows.png'
w = np.asarray(Image.open(K).convert('RGB')).astype(np.float32); lum = w.mean(-1, keepdims=True)
glass = ((w[..., 2] > w[..., 0] + 12) | (w[..., 1] > w[..., 0] + 12)) | (lum[..., 0] > 150)
lw = w * 0.35; warm = np.clip(np.array([255, 205, 130], np.float32) * (0.7 + 0.45 * lum / 255), 0, 255)
lw[glass] = warm[glass]
Image.fromarray(q555(lw)).save(os.path.join(OUT, 'windows_lit.png')); print('windows_lit ok')
# meet-lot asphalt: the Kenney asphalt.png brightened x1.55 so the lot lamps' pools read on it
a = np.asarray(Image.open(K.replace('windows.png', 'asphalt.png')).convert('RGB')).astype(np.float32)
Image.fromarray(np.clip(a * 1.55, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'asphalt_lot.png')); print('asphalt_lot ok')
