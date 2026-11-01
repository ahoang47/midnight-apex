"""Lean S2000 parts/wheel atlas (256^2): the approved atlas with every real brand painted out (art rule 7: names,
plates and badges are made up).  emblem 'H' -> made-up Midnight Apex chevron; plate 'Honda S 20-00' -> 'APEX / MA 2002';
boot badge 'S2000' -> 'RS-20'; wheel centre cap 'H' -> plain cap; tyre lettering 'POTENZA S-02' -> 'KAIDO K-2' (size
marking 205/55R16 kept).  python3 tex/debrand_atlas.py <in.png> <out.png>"""
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); a = np.asarray(im).copy()
def font(px):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        try: return ImageFont.truetype(p, px)
        except Exception: pass
    return ImageFont.load_default()
im = Image.fromarray(a); d = ImageDraw.Draw(im)
# emblem tile (x 0-31, y 128-159): keep the red frame, new black badge with a white double chevron
d.rectangle((3, 131, 28, 156), fill=(20, 20, 22)); d.rectangle((4, 132, 27, 155), outline=(205, 205, 210))
for dy in (0, 7):
    d.line([(8, 150 - dy), (15.5, 140 - dy), (23, 150 - dy)], fill=(235, 235, 240), width=3)
# plate (x 33-125, y 129-160)
d.rectangle((33, 129, 125, 160), fill=(36, 70, 40)); d.rectangle((35, 131, 123, 158), fill=(232, 236, 226))
d.text((41, 131), 'APEX', fill=(36, 70, 40), font=font(8))
d.text((50, 139), 'MA 2002', fill=(30, 60, 34), font=font(15))
# boot badge (x 0-64, y 162-176)
d.rectangle((0, 162, 64, 176), fill=(200, 16, 20)); d.text((12, 162), 'RS-20', fill=(240, 240, 240), font=font(12))
# wheel tile: centre (192,192); cap logo -> plain cap; tyre ring text -> made-up brand
cx, cy = 192, 192; A = np.asarray(im).astype(float)
yy, xx = np.mgrid[0:256, 0:256]; r = np.hypot(xx - cx, yy - cy); th = np.degrees(np.arctan2(yy - cy, xx - cx))
ring = (r > 47) & (r < 61.5) & (xx >= 128) & (yy >= 128)
base = np.median(A[ring], axis=0)
sel = ring & (th > -95) & (th < 40)                     # POTENZA ... S-02 arc (image upper right .. right)
A[sel] = base
A[(r < 6.5) & (xx >= 128) & (yy >= 128)] = A[cy, cx + 9]  # centre cap: plain
im = Image.fromarray(A.astype(np.uint8)); d = ImageDraw.Draw(im)
text = 'KAIDO  K-2'; f = font(7); n = len(text); a0 = -80.0
for i, ch in enumerate(text):
    ang = a0 + i * 10.5
    t = Image.new('L', (12, 12), 0); ImageDraw.Draw(t).text((3, 1), ch, fill=255, font=f)
    t = t.rotate(-(ang + 90), resample=Image.BICUBIC)
    px = cx + 54.5 * math.cos(math.radians(ang)) - 6; py = cy + 54.5 * math.sin(math.radians(ang)) - 6
    col = Image.new('RGB', (12, 12), (150, 150, 155)); im.paste(col, (int(round(px)), int(round(py))), t)
im.save(dst); print('wrote', dst)
