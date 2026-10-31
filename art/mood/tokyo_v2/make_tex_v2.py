"""Tokyo v2 vibe-check textures (REBUILT 2026-10-31 after data loss; original script was lost).
Painted, pre-lit night textures for an unlit PSX/PS2-style street. All light is painted in.
Usage: python3 make_tex_v2.py [outdir]"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")
os.makedirs(OUT, exist_ok=True)
R = random.Random(7)
CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
if not os.path.exists(CJK): CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(sz, cjk=True): return ImageFont.truetype(CJK if cjk else LAT, sz, index=0) if cjk else ImageFont.truetype(LAT, sz)
def hx(h, a=255): h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
PAL = dict(sodium='#FF9947', road_amb='#9597AD', warm_win='#FFD28C', cool_win='#B4E1FF', dark_win='#161C2A',
           zenith='#060614', horizon='#42284A', city_glow='#784246', fog='#30263F', skyline='#120E1C')
WALLS = ['#C4B8A0', '#8E8A84', '#96523C', '#D6D2C8', '#6E7C88', '#A8A074', '#604032', '#5A826E', '#E2D4B4', '#80788C', '#B8B0AA', '#464850']
NEON = ['#FF3C8C', '#3CC8FF', '#FFAA28', '#78FF78', '#C85AFF', '#FF4632']

def quant555(im):
    """RGB555 with 4x4 Bayer ordered dither (rule A.3.5)."""
    a = np.asarray(im.convert('RGBA')).astype(np.float32)
    b = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
    h, w = a.shape[:2]; t = np.tile(b, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = np.clip(np.floor(a[..., :3] / 8 + t + 0.5), 0, 31) * 8.2258
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')
def save(im, name, q=True):
    (quant555(im) if q else im).save(os.path.join(OUT, name))

def noise(w, h, s, amp, seed):
    rng = np.random.default_rng(seed); n = rng.random((h // s + 2, w // s + 2))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (n - 0.5) * amp

# ---------------------------------------------------------------- road: 9 m x 220 m strip, 64 px/m across, 16 px/m along
def road(lamps_x, length=220.0, x0=-110.0):
    W, H = 288, int(length * 12)          # u across (9 m -> 288 px = 32 px/m), v along (12 px/m)
    base = np.full((H, W, 3), (46, 46, 54), np.float32)
    base += noise(W, H, 3, 26, 1)[..., None] + noise(W, H, 40, 14, 2)[..., None]
    rng = np.random.default_rng(3)
    for _ in range(140):                   # patches / repairs
        y, x = rng.integers(0, H), rng.integers(0, W); hh, ww = rng.integers(8, 60), rng.integers(10, 80)
        base[y:y + hh, x:x + ww] += rng.uniform(-10, 8)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(90):                    # cracks / tar seams
        x, y = R.randrange(W), R.randrange(H); pts = [(x, y)]
        for _ in range(R.randrange(3, 8)): x += R.randint(-14, 14); y += R.randint(-10, 10); pts.append((x, y))
        d.line(pts, fill=(22, 22, 26), width=1)
    cl = W // 2                            # centre dashes + edge lines
    for v in range(0, H, 96): d.rectangle([cl - 4, v, cl + 4, v + 48], fill=(168, 168, 164))
    d.rectangle([10, 0, 15, H], fill=(196, 170, 70)); d.rectangle([W - 16, 0, W - 11, H], fill=(196, 170, 70))
    for k in range(6):                     # crosswalk near the end
        v = int((70 - x0) * 12) + k * 0
    cw = int((60 - x0) * 12)
    for u in range(24, W - 24, 28): d.rectangle([u, cw, u + 16, cw + 40], fill=(190, 190, 186))
    for mx in (-30, 12, 47):              # manholes / painted markings
        v = int((mx - x0) * 12); d.ellipse([cl + 40, v, cl + 76, v + 36], fill=(34, 34, 38), outline=(60, 60, 66))
    a = np.asarray(im).astype(np.float32) / 255
    # painted lighting: road ambient tint + STEPPED sodium pools under each lamp (lamps at u=edge)
    amb = np.array(ImageColorArr(PAL['road_amb'])) / 255 * 0.85
    light = np.tile(amb, (H, W, 1))
    vv, uu = np.mgrid[0:H, 0:W]
    sod = np.array(ImageColorArr(PAL['sodium'])) / 255
    for lx, side in lamps_x:
        cv = (lx - x0) * 12; cu = 30 if side < 0 else W - 30
        dd = np.sqrt(((vv - cv) / 12) ** 2 + ((uu - cu) / 32) ** 2)   # metres
        lvl = np.clip(1 - dd / 9.0, 0, 1); lvl = np.floor(lvl * 4) / 4      # 4 hard bands
        light += lvl[..., None] * sod * 1.1
    out = np.clip(a * light * 1.25, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))
def ImageColorArr(h): return hx(h)[:3]

def sidewalk():
    W, H = 128, 512
    im = Image.new('RGB', (W, H), (120, 116, 118)); d = ImageDraw.Draw(im)
    for y in range(0, H, 32):
        for x in range(0, W, 32):
            c = 110 + R.randint(-12, 12); d.rectangle([x + 1, y + 1, x + 30, y + 30], fill=(c, c - 4, c + 2))
    d.rectangle([0, 0, 5, H], fill=(150, 146, 140))             # curb edge
    d.rectangle([W - 8, 0, W - 4, H], fill=(196, 170, 70))       # yellow line near shops
    return im

def facade(seed, wall, w_m, h_m, kind):
    """Pre-lit night facade, 32 px/m."""
    rs = random.Random(seed); W, H = int(w_m * 32), int(h_m * 32)
    base = np.array(hx(wall)[:3], np.float32) * 0.62
    a = np.tile(base, (H, W, 1)) + noise(W, H, 4, 16, seed)[..., None]
    if kind == 'brick':
        for y in range(0, H, 6): a[y, :] *= 0.8
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    fh = 3.6 * 32; floors = int((H - fh) // (3.2 * 32))
    cols = max(1, int(w_m // 2.6))
    for f in range(floors):
        y0 = H - fh - (f + 1) * 3.2 * 32 + 22
        for c in range(cols):
            x0 = c * W / cols + 10; x1 = (c + 1) * W / cols - 10
            r = rs.random(); col = hx(PAL['dark_win'])[:3] if r < .5 else hx(PAL['warm_win'] if r < .8 else PAL['cool_win'])[:3]
            if r >= .5: col = tuple(int(v * rs.uniform(.65, 1)) for v in col)
            d.rectangle([x0, y0, x1, y0 + 58], fill=col, outline=(20, 20, 24))
            if r >= .5 and rs.random() < .4:   # blinds / curtains
                for yy in range(int(y0) + 4, int(y0) + 58, 6): d.line([x0, yy, x1, yy], fill=tuple(int(v * .7) for v in col))
            if rs.random() < .25:              # AC unit
                d.rectangle([x1 - 30, y0 + 62, x1 - 2, y0 + 82], fill=(150, 150, 146), outline=(60, 60, 60))
    # ground floor: shutter / shopfront / lit shop
    gy = H - fh
    d.rectangle([0, gy, W, gy + 10], fill=(30, 30, 34))
    gk = rs.choice(['shutter', 'shop', 'shop', 'dark'])
    if gk == 'shutter':
        d.rectangle([12, gy + 16, W - 12, H - 2], fill=(150, 130, 118))
        for yy in range(int(gy) + 18, H, 5): d.line([12, yy, W - 12, yy], fill=(110, 94, 86))
        if rs.random() < .5: d.text((40, H - 70), rs.choice(['GCYC', 'R0KU', 'MSK']), font=F(34, False), fill=(200, 70, 140))
    elif gk == 'shop':
        lc = hx(rs.choice([PAL['warm_win'], PAL['cool_win']]))[:3]; lc = tuple(int(v * .78) for v in lc)
        d.rectangle([12, gy + 40, W - 12, H - 6], fill=lc, outline=(30, 30, 30), width=4)
        for k in range(rs.randint(2, 4)):      # shelves / counters
            yy = gy + 60 + k * 24; d.rectangle([20, yy, W - 20, yy + 4], fill=tuple(int(v * .6) for v in lc))
        nc = hx(rs.choice(NEON))[:3]; d.rectangle([12, gy + 12, W - 12, gy + 38], fill=(20, 20, 26))
        d.text((24, gy + 12), rs.choice(['歯科', '珈琲', 'クリーニング', '駐車場', '薬局', 'らーめん']), font=F(22), fill=nc)
    else:
        d.rectangle([12, gy + 16, W - 12, H - 2], fill=(26, 26, 32))
    return im

def neon_sign(text, col, vertical=True, bg='#141018'):
    sz = 64; n = len(text)
    W, H = (sz + 24, n * (sz + 6) + 24) if vertical else (n * (sz - 6) + 40, sz + 28)
    im = Image.new('RGB', (W, H), hx(bg)[:3]); d = ImageDraw.Draw(im)
    c = hx(col)[:3]; d.rectangle([3, 3, W - 4, H - 4], outline=c, width=3)
    if vertical:
        for i, ch in enumerate(text): d.text((12, 10 + i * (sz + 6)), ch, font=F(sz), fill=c)
    else:
        d.text((18, 6), text, font=F(sz), fill=c)
    glow = im.filter(ImageFilter.GaussianBlur(3))
    return Image.blend(glow, im, 0.75)

def lightbox(text, bgc, fg=(20, 20, 20), vertical=True):
    sz = 56; n = len(text)
    W, H = (sz + 20, n * (sz + 4) + 20) if vertical else (n * sz + 30, sz + 24)
    im = Image.new('RGB', (W, H), hx(bgc)[:3]); d = ImageDraw.Draw(im)
    if vertical:
        for i, ch in enumerate(text): d.text((10, 8 + i * (sz + 4)), ch, font=F(sz), fill=fg)
    else: d.text((14, 4), text, font=F(sz), fill=fg)
    return im

def konbini():
    W, H = 640, 160                       # 20 m x 5 m storefront at 32 px/m
    im = Image.new('RGB', (W, H), (205, 205, 200)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 34], fill=hx('#6E3CAA')[:3]); d.rectangle([0, 34, W, 42], fill=hx('#FAC828')[:3])
    d.text((14, -2), 'よるマート', font=F(30), fill=(245, 245, 245)); d.text((W - 170, 2), 'YORU MART 24h', font=F(20, False), fill=(250, 230, 120))
    # glass + shelves, toned down so it never out-shines the car
    d.rectangle([8, 48, W - 8, H - 18], fill=(176, 182, 172))
    for x in range(8, W - 8, 120): d.line([x, 48, x, H - 18], fill=(70, 70, 70), width=3)
    for row in range(4):
        y = 56 + row * 22
        for x in range(14, W - 14, 9):
            if R.random() < .85: d.rectangle([x, y, x + 6, y + 14], fill=hx(R.choice(NEON + ['#FAC828', '#285ADC']))[:3])
        d.rectangle([10, y + 15, W - 10, y + 18], fill=(120, 120, 116))
    d.rectangle([W - 120, 52, W - 60, 110], fill=hx('#DC283C')[:3]); d.text((W - 116, 60), '新発売', font=F(16), fill=(255, 255, 255))
    d.rectangle([0, H - 18, W, H], fill=(60, 60, 64))
    return im

def vending():
    W, H = 64, 112
    im = Image.new('RGB', (W, H), (210, 214, 220)); d = ImageDraw.Draw(im)
    d.rectangle([4, 6, W - 5, 60], fill=(228, 236, 240))
    for r in range(3):
        for c in range(5): d.rectangle([7 + c * 11, 9 + r * 17, 14 + c * 11, 22 + r * 17], fill=hx(R.choice(NEON + ['#285ADC', '#FAC828']))[:3])
    d.rectangle([4, 64, W - 5, 76], fill=(40, 40, 40)); d.rectangle([10, 90, W - 10, 104], fill=(30, 30, 30))
    return im

def cutout(kind):
    W, H = 128, 128; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 'bike':
        c = hx(R.choice(['#DC283C', '#285ADC', '#D6D2C8']))
        for cx in (30, 98): d.ellipse([cx - 24, 60, cx + 24, 108], outline=(30, 30, 30, 255), width=4)
        d.line([(30, 84), (60, 52), (98, 84), (64, 84), (30, 84)], fill=c, width=5); d.line([(60, 52), (56, 40)], fill=c, width=4)
        d.line([(92, 62), (90, 40), (104, 38)], fill=(40, 40, 40, 255), width=4)
    elif kind == 'cone':
        d.polygon([(64, 10), (88, 112), (40, 112)], fill=hx('#F05014')); d.rectangle([28, 110, 100, 122], fill=hx('#F05014'))
        d.polygon([(56, 44), (72, 44), (76, 62), (52, 62)], fill=(235, 235, 235, 255))
    elif kind == 'barrier':
        d.rectangle([4, 20, 124, 50], fill=(240, 210, 30, 255))
        for x in range(-30, 130, 24): d.polygon([(x, 50), (x + 12, 50), (x + 42, 20), (x + 30, 20)], fill=(20, 20, 20, 255))
        d.rectangle([4, 20, 10, 124], fill=(220, 220, 220, 255)); d.rectangle([118, 20, 124, 124], fill=(220, 220, 220, 255))
        d.rectangle([30, 62, 98, 90], fill=(240, 240, 240, 255)); d.text((36, 60), '工事中', font=F(20), fill=(200, 20, 20, 255))
    elif kind == 'plant':
        d.rectangle([44, 90, 84, 124], fill=(40, 80, 160, 255))
        for _ in range(40): x, y = R.randint(28, 100), R.randint(30, 92); d.ellipse([x - 9, y - 7, x + 9, y + 7], fill=(40 + R.randint(0, 40), 110 + R.randint(0, 50), 50, 255))
    elif kind == 'board':
        d.polygon([(30, 124), (44, 20), (84, 20), (98, 124)], fill=(30, 30, 30, 255)); d.rectangle([46, 28, 82, 100], fill=(20, 30, 24, 255))
        for k in range(5): d.line([50, 36 + k * 12, 78, 36 + k * 12], fill=(230, 230, 230, 255), width=2)
    return im

def sky():
    W, H = 1024, 256
    a = np.zeros((H, W, 3), np.float32); t = np.linspace(0, 1, H)[:, None]
    z, hz, cg = [np.array(hx(PAL[k])[:3], np.float32) for k in ('zenith', 'horizon', 'city_glow')]
    a[:] = (z * (1 - t ** 1.6) + hz * t ** 1.6)[:, None, :] if False else (z[None] * (1 - t ** 1.6) + hz[None] * t ** 1.6)[:, None, :]
    a[int(H * .82):] = a[int(H * .82):] * .6 + cg * .4
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(60): x, y = R.randrange(W), R.randrange(int(H * .5)); d.point((x, y), fill=(120, 110, 140))
    return im

def skyline(seed, W=1024, H=256):
    rs = random.Random(seed); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 0
    while x < W:
        bw, bh = rs.randint(40, 120), rs.randint(60, H - 10); col = hx(PAL['skyline'])
        d.rectangle([x, H - bh, x + bw, H], fill=col)
        for yy in range(H - bh + 6, H, 8):
            for xx in range(x + 4, x + bw - 4, 7):
                if rs.random() < .28: d.rectangle([xx, yy, xx + 3, yy + 3], fill=hx(rs.choice([PAL['warm_win'], PAL['cool_win'], '#FFFFFF']), 255))
        if rs.random() < .2: d.rectangle([x + bw // 2, H - bh - 8, x + bw // 2 + 2, H - bh], fill=(255, 40, 40, 255))
        x += bw + rs.randint(-10, 10)
    return im

def glow(col, size=64, hard=False):
    yy, xx = np.mgrid[0:size, 0:size]; r = np.sqrt((xx - size / 2 + .5) ** 2 + (yy - size / 2 + .5) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    if hard: a = np.floor(a * 5) / 5
    c = np.array(hx(col)[:3], np.float32)
    return Image.fromarray(np.dstack([np.tile(c, (size, size, 1)), a * 255]).astype(np.uint8), 'RGBA')

def blob_shadow():
    W, H = 128, 64; yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.clip(1 - r, 0, 1) ** .7 * 220
    return Image.fromarray(np.dstack([np.zeros((H, W, 3)), a]).astype(np.uint8), 'RGBA')

def headlight_throw():
    W, H = 128, 256; yy, xx = np.mgrid[0:H, 0:W]
    fan = np.clip(1 - np.abs(xx - W / 2) / (W / 2 * (0.25 + .75 * yy / H)), 0, 1) * np.clip(1 - yy / H, 0, 1) ** 1.2
    a = np.floor(fan * 4) / 4 * 150
    c = np.array(hx('#FFF2CC')[:3]); return Image.fromarray(np.dstack([np.tile(c, (H, W, 1)), a]).astype(np.uint8), 'RGBA')

def env_map():
    """Painted equirect for the car's fake shine: dark sky top, sodium/neon band, dark street below."""
    W, H = 512, 256; a = np.zeros((H, W, 3), np.float32); t = np.linspace(0, 1, H)[:, None]
    top = np.array([30, 24, 54], np.float32); hor = np.array([150, 110, 120], np.float32); bot = np.array([26, 24, 28], np.float32)
    up = (top[None] * (1 - t / .5) + hor[None] * (t / .5)); dn = hor[None] * (1 - (t - .5) / .5) + bot[None] * ((t - .5) / .5)
    a[:] = np.where(t < .5, up, dn)[:, None, :]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(40):
        x = R.randrange(W); y = R.randint(70, 124); col = hx(R.choice(NEON + [PAL['sodium']] * 3))[:3]
        d.rectangle([x, y, x + R.randint(3, 12), y + R.randint(4, 30)], fill=col)
    for x in range(0, W, 64): d.ellipse([x + 20, 96, x + 34, 104], fill=(255, 200, 140))
    return im.filter(ImageFilter.GaussianBlur(1.5))

if __name__ == '__main__':
    import json
    lamps = json.load(open(os.path.join(OUT, 'lamps.json'))) if os.path.exists(os.path.join(OUT, 'lamps.json')) else \
        [[x, s] for x in range(-100, 101, 16) for s in (-1, 1)]
    save(road(lamps), 'road.png'); save(sidewalk(), 'sidewalk.png')
    for i in range(12):
        kind = 'brick' if i % 3 == 2 else 'plain'
        save(facade(100 + i, WALLS[i], 8, 24, kind), f'facade_{i:02d}.png')
    signs = [('ホテル夜桜', '#FF3C8C'), ('カラオケ', '#C85AFF'), ('焼肉', '#FF4632'), ('居酒屋ほたる', '#3CC8FF'),
             ('BAR月', '#FFAA28'), ('らーめん', '#78FF78'), ('カラオケ', '#3CC8FF'), ('焼肉', '#FFAA28')]
    for i, (t, c) in enumerate(signs): save(neon_sign(t, c), f'neon_{i:02d}.png')
    boxes = [('番', '#285ADC', (255, 255, 255)), ('電', '#E8E8E8', (20, 20, 20)), ('歯科', '#E8E8E8', (30, 60, 160)),
             ('ラーメン', '#FAC828', (20, 20, 20)), ('生ビール', '#E8E8E8', (200, 30, 30)), ('屋', '#E8F8F0', (30, 140, 90))]
    for i, (t, b, f) in enumerate(boxes): save(lightbox(t, b, f), f'box_{i:02d}.png')
    save(lightbox('ドラッグ', '#285ADC', (255, 255, 255), vertical=False), 'box_drug.png')
    save(konbini(), 'konbini.png'); save(vending(), 'vending.png')
    for k in ('bike', 'cone', 'barrier', 'plant', 'board'): save(cutout(k), f'cut_{k}.png')
    save(sky(), 'sky.png'); save(skyline(1), 'skyline_a.png'); save(skyline(2), 'skyline_b.png')
    save(glow('#FFB060'), 'glow_sodium.png', q=False); save(glow('#FFF2CC'), 'glow_head.png', q=False)
    save(glow('#FF1F14'), 'glow_tail.png', q=False); save(glow('#FFFFFF'), 'glow_white.png', q=False)
    save(blob_shadow(), 'blob_shadow.png', q=False); save(headlight_throw(), 'headlight_throw.png', q=False)
    save(env_map(), 'env_street.png')
    print('textures ->', OUT, len(os.listdir(OUT)))
