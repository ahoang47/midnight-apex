"""Post for scene_mx5_tokyo.py: the post_duo.py recipe (neon-only bloom -> RGB555 + 4x4 Bayer -> 2x nearest, 1280x896)
+ _800.jpg previews.  python3 post_mx5_tokyo.py [raw_dir] [out_dir]"""
import os, sys, numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
RD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'renders', 'raw'); OD = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'renders')
V2DIR = os.path.dirname(os.environ.get('TOKYO_V2', os.path.normpath(os.path.join(HERE, '..', 'tokyo_v2', 'scene_v2.py'))))
sys.path.insert(0, V2DIR); from post_v2 import rgb555           # the Tokyo v2 quantiser, unchanged
for name in ("mx5_hero_front34", "mx5_rear34", "mx5_establishing"):
    base = np.asarray(Image.open(os.path.join(RD, f"raw_{name}.png")).convert('RGB')).astype(np.float32)
    n = np.asarray(Image.open(os.path.join(RD, f"neon_{name}.png")).convert('RGBA')).astype(np.float32)
    lit = n[..., :3] * (n[..., 3:] / 255)
    b1 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
    b2 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
    q = rgb555(np.clip(base + 0.45 * b1 + 0.35 * b2, 0, 255))
    im = Image.fromarray(q).resize((q.shape[1] * 2, q.shape[0] * 2), Image.NEAREST)
    p = os.path.join(OD, f"mx5_tokyo_{name[4:]}.png"); im.save(p); im.resize((800, 560), Image.LANCZOS).save(p.replace('.png', '_800.jpg'), quality=90)
    print('wrote', p)
