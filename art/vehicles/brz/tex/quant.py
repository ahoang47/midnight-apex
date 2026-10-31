"""RGB555 quantisation with a 4x4 ordered (Bayer) dither, applied at authoring time (art direction A.3.5)."""
import numpy as np
from PIL import Image
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)
def rgb555_bayer(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32); h, w = a.shape[:2]
    t = (B4[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4] + 0.5) / 16.0 - 0.5     # -0.5..0.5
    q = np.floor(a / 255.0 * 31.0 + 0.5 + t[..., None])
    q = np.clip(q, 0, 31) * 255.0 / 31.0
    return Image.fromarray(np.round(q).astype(np.uint8))
