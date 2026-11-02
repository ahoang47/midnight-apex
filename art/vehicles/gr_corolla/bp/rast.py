"""Rasterize SVG layers at SC px per SVG unit -> bp/raster_<layer>.png (ink=255)."""
from layers import render
import cv2, numpy as np
SC = 6
for name, ids in (('outline', ['_x32_D_x24_AG-OUTLINE']), ('transport', ['_x32_D_x24_AG-TRANSPORT']),
                  ('details', ['_x32_D_x24_AG-DETAILS']), ('diagram', ['_x32_D_x24_AG-DIAGRAM']), ('dims', ['N-DIMENSIONS'])):
    render(f'raster_{name}.png', SC, ids, colour=False)
    a = cv2.imread(f'raster_{name}.png', cv2.IMREAD_UNCHANGED)
    ink = (a[..., 3] > 100) & (a[..., :3].mean(-1) < 128) if a.shape[-1] == 4 else a.mean(-1) < 128
    cv2.imwrite(f'raster_{name}.png', (ink * 255).astype(np.uint8)); print(name, a.shape, ink.sum())
