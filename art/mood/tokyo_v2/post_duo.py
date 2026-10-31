"""Tokyo v2 DUO post: identical recipe to post_v2.py (neon-only bloom -> RGB555 + 4x4 Bayer -> 2x nearest, 1280x896)
plus _800.jpg previews and a 2x2 contact sheet.  Usage: python3 post_duo.py [TAG]"""
import os, sys, numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from post_v2 import rgb555
RD = os.path.join(os.path.dirname(HERE), "renders", "tokyo_duo") if os.path.basename(HERE) == "tokyo" else os.path.join(HERE, "renders", "duo")
TAG = sys.argv[1] if len(sys.argv) > 1 else ""
NAMES = ["duo_hero_front34", "duo_rear34", "duo_side_by_side", "duo_establishing"]
def post(name):
    base = np.asarray(Image.open(os.path.join(RD, f"raw_{name}.png")).convert('RGB')).astype(np.float32)
    n = np.asarray(Image.open(os.path.join(RD, f"neon_{name}.png")).convert('RGBA')).astype(np.float32)
    lit = n[..., :3] * (n[..., 3:] / 255)
    b1 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
    b2 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
    q = rgb555(np.clip(base + 0.45 * b1 + 0.35 * b2, 0, 255))
    im = Image.fromarray(q).resize((q.shape[1] * 2, q.shape[0] * 2), Image.NEAREST)
    p = os.path.join(RD, f"{name}{TAG}.png"); im.save(p)
    im.resize((800, 560), Image.LANCZOS).save(p.replace('.png', '_800.jpg'), quality=90)
    return im
if __name__ == '__main__':
    ims = [post(n) for n in NAMES]
    W, H = 640, 448; sheet = Image.new('RGB', (W * 2 + 30, (H + 40) * 2 + 10), (14, 12, 22)); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    for i, (n, im) in enumerate(zip(NAMES, ims)):
        x = 10 + (i % 2) * (W + 10); y = 10 + (i // 2) * (H + 40)
        d.text((x, y), n, font=f, fill=(230, 230, 230)); sheet.paste(im.resize((W, H), Image.NEAREST), (x, y + 30))
    sp = os.path.join(RD, f"duo_contact{TAG}.png"); sheet.save(sp)
    sheet.resize((800, int(800 * sheet.height / sheet.width)), Image.LANCZOS).save(sp.replace('.png', '_800.jpg'), quality=90)
    print("post done")
