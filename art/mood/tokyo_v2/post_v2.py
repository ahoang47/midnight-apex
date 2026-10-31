"""Tokyo v2 post (REBUILT 2026-10-31 after data loss): neon-only bloom -> RGB555 + 4x4 Bayer -> 2x nearest (1280x896).
Also writes _800.jpg previews and a contact sheet. Usage: python3 post_v2.py"""
import os, numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(os.path.dirname(HERE), "renders", "tokyo_v2") if os.path.basename(HERE) == "tokyo" else os.path.join(HERE, "renders")
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def rgb555(a):
    h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
def post(name):
    base = np.asarray(Image.open(os.path.join(RD, f"raw_{name}.png")).convert('RGB')).astype(np.float32)
    neon = Image.open(os.path.join(RD, f"neon_{name}.png")).convert('RGBA'); n = np.asarray(neon).astype(np.float32)
    lit = n[..., :3] * (n[..., 3:] / 255)                                  # neon + glow sprites only, occlusion kept
    b1 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
    b2 = np.asarray(Image.fromarray(lit.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
    out = base + 0.45 * b1 + 0.35 * b2
    q = rgb555(np.clip(out, 0, 255))
    im = Image.fromarray(q).resize((q.shape[1] * 2, q.shape[0] * 2), Image.NEAREST)
    p = os.path.join(RD, f"tokyo_v2_{name}.png"); im.save(p)
    im.resize((800, 560), Image.LANCZOS).save(p.replace('.png', '_800.jpg'), quality=90)
    return im
if __name__ == '__main__':
    names = ["hero_front34", "rear34", "establishing"]; ims = [post(n) for n in names]
    W, H = 640, 448; sheet = Image.new('RGB', (W * 3 + 40, H + 60), (14, 12, 22)); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    for i, (n, im) in enumerate(zip(names, ims)):
        sheet.paste(im.resize((W, H), Image.NEAREST), (10 + i * (W + 10), 40)); d.text((10 + i * (W + 10), 10), n, font=f, fill=(230, 230, 230))
    sheet.save(os.path.join(RD, "tokyo_v2_contact.png")); sheet.resize((800, int(800 * sheet.height / sheet.width)), Image.LANCZOS).save(os.path.join(RD, "tokyo_v2_contact_800.jpg"), quality=90)
    print("post done", os.listdir(RD))
