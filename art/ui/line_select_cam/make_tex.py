"""Hand-painted-style PSX textures for the Touge hairpin (cedar card, guardrail beam, chevron board, slope, ridge).
Small, nearest-sampled, quantised to 5 bits/channel with 4x4 Bayer like every other mockup texture.  python3 make_tex.py"""
import os, random, numpy as np
from PIL import Image, ImageDraw
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex'); R = random.Random(7)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def q5(im):
    a = np.asarray(im).astype(np.float32); h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = (np.clip(np.floor(a[..., :3] / 8 + t + .5), 0, 31) * 8.2258).clip(0, 255)
    if a.shape[2] == 4: rgb = np.concatenate([rgb, np.where(a[..., 3:] > 127, 255, 0)], -1)
    return Image.fromarray(rgb.astype(np.uint8))
def noise(d, w, h, cols, n):
    for _ in range(n):
        x, y = R.randrange(w), R.randrange(h); d.point((x, y), fill=R.choice(cols))

# cedar card: stacked drooping tiers, dark blue-green, ragged edge, thin trunk (64x192)
W, H = 64, 192; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle((30, 150, 33, 191), fill=(74, 52, 40, 255)); d.line((31, 150, 31, 191), fill=(98, 72, 52, 255))
tiers = 9
for i in range(tiers):
    top = 4 + i * 17; hw = 6 + i * 3.1; bot = top + 26
    pts = [(32, top)]
    for k in range(7):
        t = (k + 1) / 7; x = 32 + hw * t + R.uniform(-1.5, 1.5); pts.append((x, top + (bot - top) * t ** .7 + R.uniform(-2, 2)))
    for k in range(7):
        t = 1 - k / 7; x = 32 - hw * t + R.uniform(-1.5, 1.5); pts.append((x, top + (bot - top) * t ** .7 + R.uniform(-2, 2)))
    d.polygon(pts, fill=(34, 70, 58, 255))
    for k in range(int(hw * 2)):   # lighter needle clumps on the upper face of each tier, darker underside
        x = 32 + R.uniform(-hw, hw) * .9; y = top + 6 + abs(x - 32) / max(hw, 1) * 14 + R.uniform(-3, 3)
        for dx, c in ((0, (58, 104, 82, 255)), (1, (48, 92, 72, 255))):
            if 0 <= x + dx < W and 0 <= y < H and im.getpixel((int(x + dx), int(y)))[3]: d.point((x + dx, y), fill=c)
    d.line([(32 - hw * .9, bot - 3), (32 + hw * .9, bot - 3)], fill=(20, 44, 38, 255))
q5(im).save(os.path.join(T, 'cedar.png'))

# guardrail W-beam (64 x 16): galvanised grey, darker crease, rust/grime streaks, reflector dot every 2 m (u = 4 m)
im = Image.new('RGB', (64, 16), (176, 182, 186)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, 63, 2), fill=(206, 212, 214)); d.rectangle((0, 7, 63, 8), fill=(110, 116, 122)); d.rectangle((0, 13, 63, 15), fill=(140, 146, 150))
for x in range(0, 64, 3):
    if R.random() < .45: d.line((x, 9, x + R.randint(-1, 1), 15), fill=(132, 120, 108))
for x in (14, 46): d.rectangle((x, 6, x + 2, 9), fill=(240, 208, 120))
q5(im).save(os.path.join(T, 'guardrail.png'))

# chevron board (32 x 32): yellow ground, black right-pointing chevrons (hairpin turns right)
im = Image.new('RGB', (32, 32), (236, 196, 40)); d = ImageDraw.Draw(im)
for x0 in (3, 15):
    d.polygon([(x0, 4), (x0 + 6, 4), (x0 + 14, 16), (x0 + 6, 28), (x0, 28), (x0 + 8, 16)], fill=(16, 16, 18))
d.rectangle((0, 0, 31, 31), outline=(20, 20, 20))
q5(im).save(os.path.join(T, 'chevron.png'))

# slope (64 x 64): mossy cut bank, grass + rock + dark soil
im = Image.new('RGB', (64, 64), (70, 84, 58)); d = ImageDraw.Draw(im)
noise(d, 64, 64, [(56, 70, 48), (88, 100, 70), (62, 66, 58), (96, 92, 80)], 1500)
for _ in range(14):
    x, y = R.randrange(64), R.randrange(64); r = R.randint(2, 5); d.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=(104, 104, 98))
q5(im).save(os.path.join(T, 'slope.png'))

# concrete gutter / post colour (16 x 16)
im = Image.new('RGB', (16, 16), (150, 150, 146)); d = ImageDraw.Draw(im); noise(d, 16, 16, [(132, 132, 128), (168, 168, 162)], 90)
q5(im).save(os.path.join(T, 'concrete.png'))

# distant ridge silhouettes (512 x 96 RGBA): two cutout layers, colours sit just off the blend50 fog (#0B172B)
for name, col, base, amp, seed in (('ridge_far.png', (16, 30, 50), 52, 26, 3), ('ridge_near.png', (9, 18, 30), 34, 30, 5)):
    rr = random.Random(seed); im = Image.new('RGBA', (512, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    h = [base + amp * np.sin(x / 512 * 6.283 * 2 + seed) * .5 + amp * .5 * np.sin(x / 512 * 6.283 * 5 + seed * 2) for x in range(512)]
    for x in range(512):
        y = 96 - int(h[x]); d.line((x, y, x, 95), fill=col + (255,))
        if rr.random() < .22:      # cedar spikes on the skyline
            sh = rr.randint(3, 8); d.polygon([(x - 2, y + 1), (x, y - sh), (x + 2, y + 1)], fill=col + (255,))
    q5(im).save(os.path.join(T, name))
print('tex ok')
