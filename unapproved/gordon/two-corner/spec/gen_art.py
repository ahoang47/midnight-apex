#!/usr/bin/env python3
"""Display-only environment + HUD textures for the two-corner test, following design/art/art_direction.md @212eaab.
Recipes are the Tokyo v2 vibe-check recipe (art/mood/tokyo_v2/make_tex_v2.py, Part B [VIBE]) with ALL lettering removed
(no signage text, no names), re-coloured per district with the Part B.3 [PROPOSAL] values (Touge / Urban Street).
assets/env, assets/ui and assets/fonts are empty at the pin, so everything here is a STAND-IN, not a game-ready asset.
Every texture is quantised RGB555 + 4x4 Bayer (A.3.5) and saved lossless PNG.
Strip textures: image x = across the strip (or up a wall), image y = metres along the road (tile = display.json value).
Usage: python3 gen_art.py  -> spec/art/*.png + spec/art/font.json"""
import os, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'art'); os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(HERE, 'display.json'))); DIST = D['districts']; PAL = D['palette']; CAL = PAL['calib']
# B.2a (art_direction.md@55b9063): navy/teal + pale sodium. 'Pre-lit' world textures are multiplied by the B.2a ambient
# (B.1: texture x vertex light), scaled by the display calibration in display.json palette.calib.
R = random.Random(7)
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def quant555(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32); h, w = a.shape[:2]
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    rgb = np.clip(np.floor(a[..., :3] / 8 + t + 0.5), 0, 31) * 8.2258
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3:]]).astype(np.uint8), 'RGBA')
def save(im, name, q=True): (quant555(im) if q else im.convert('RGBA')).save(os.path.join(OUT, name))
def prelit(im, gain=None):
    a = np.asarray(im.convert('RGBA')).astype(np.float32); k = hx(PAL['ambient']) / 255 * PAL['ambient_k'] * (CAL['facade_amb_gain'] if gain is None else gain) * 2
    a[..., :3] *= k; return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
def noise(w, h, s, amp, seed):
    rng = np.random.default_rng(seed); n = rng.random((h // s + 2, w // s + 2))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
    return (n - 0.5) * amp

# ── road: u across [-W, W] (W = 1.5 lanes + 1 m), v along one lamp period; STEPPED pools painted in (B.1) ──
def road(dk, cfg):
    W_m = D['lane_width_m'] * 1.5 + 1.0; tile = cfg['lamp_period_m']
    PXU, PXV = 16, 12; W, H = int(2 * W_m * PXU), int(tile * PXV)
    base = np.full((H, W, 3), cfg['asphalt'], np.float32)
    base += noise(W, H, 3, 26, 1)[..., None] + noise(W, H, 40, 14, 2)[..., None]
    rng = np.random.default_rng(3)
    for _ in range(int(tile * 0.6)):
        y, x = rng.integers(0, H), rng.integers(0, W); base[y:y + rng.integers(6, 40), x:x + rng.integers(8, 50)] += rng.uniform(-10, 8)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(int(tile * 0.4)):
        x, y = R.randrange(W), R.randrange(H); pts = [(x, y)]
        for _ in range(R.randrange(3, 8)): x += R.randint(-10, 10); y += R.randint(-8, 8); pts.append((x, y))
        d.line(pts, fill=(22, 22, 26), width=1)
    cl = W // 2; dash = int(4 * PXV)
    for v in range(0, H, dash * 2): d.rectangle([cl - 2, v, cl + 2, v + dash], fill=(168, 168, 164))   # centre dashes
    edge = tuple(int(c) for c in hx(cfg['edge_line']))
    e0 = int(0.4 * PXU); d.rectangle([e0, 0, e0 + 2, H], fill=edge); d.rectangle([W - e0 - 3, 0, W - e0 - 1, H], fill=edge)
    a = np.asarray(im).astype(np.float32) / 255
    # B.2a lighting, structured like the blend50 mockup (tones/work/lane/build_v5.py:219-228, 268-275):
    #   texture x (ambient x amb_k + 3-step vertex pools r 13 m x lamp_k x lane_ground_lamp) + additive 3-step pool decal (13 m square)
    amb = hx(PAL['ambient']) / 255 * PAL['ambient_k'] * CAL['road_amb_gain']
    light = np.tile(amb, (H, W, 1)); add = np.zeros((H, W, 3), np.float32)
    vv, uu = np.mgrid[0:H, 0:W]; sod = hx(cfg['lamp_colour']) / 255; n = PAL['pool_steps']
    for lamp in cfg['lamps']:                      # [s within tile, side]
        for rep in (-1, 0, 1):                     # wrap so pools tile seamlessly
            cv = (lamp[0] + rep * tile) * PXV; cu = (W_m + lamp[1] * (W_m - 0.8)) * PXU
            dv = (vv - cv) / PXV; du = (uu - cu) / PXU; dd = np.sqrt(dv ** 2 + du ** 2)
            lv = np.floor(np.clip(1 - np.sqrt(dd ** 2 + 6.35 ** 2) / 13.0, 0, 1) * PAL['vertex_steps']) / PAL['vertex_steps']   # 3D distance to a head 6.35 m up (build_v5.py:115,225)
            light += lv[..., None] * sod * PAL['lamp_k'] * PAL['lane_ground_lamp'] * CAL['road_vertex_lamp_gain']
            r = dd / 6.5; dec = np.floor(np.clip(1 - r, 0, 1) ** 1.1 * n) / n      # make_tone_tex.py:25-26 (round decal)
            add += dec[..., None] * sod * PAL['pool_k'] * PAL['lane_pool_mul'] * CAL['road_decal_gain']
    return Image.fromarray((np.clip(a * light + add, 0, 1) * 255).astype(np.uint8))

def verge(cfg):      # flat shoulder strip, 30 m wide, tile 6 m
    W, H = 240, 48; a = np.tile(hx(cfg['verge']), (H, W, 1)) + noise(W, H, 2, 18, 5)[..., None] + noise(W, H, 12, 14, 6)[..., None]
    return prelit(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 1.0)

def guardrail():     # W-beam on posts, 1.0 m high wall strip, tile 4 m; x = height (0 bottom), y = along; alpha cut-out
    PX = 32; W, H = 32, 4 * PX
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in (0, 2 * PX):
        d.rectangle([0, y, int(0.62 * PX), y + 3], fill=(92, 98, 100, 255))                      # post (x = up)
    beam = [(int(0.42 * PX), (150, 158, 160)), (int(0.50 * PX), (186, 192, 192)), (int(0.58 * PX), (120, 126, 128))]
    for i, (x, c) in enumerate(beam): d.rectangle([x, 0, x + 2, H], fill=c + (255,))
    for y in range(0, H, 2 * PX): d.rectangle([int(0.42 * PX), y + PX - 1, int(0.60 * PX), y + PX + 1], fill=(70, 74, 76, 255))  # splice
    return prelit(im)

def cedar(seed):     # cut-out card, 128x256 (2:1); layered dark cone, cold green (B.3 "cedar cards")
    rs = random.Random(seed); W, H = 128, 256
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60, 200, 68, H], fill=(38, 30, 26, 255))
    for k in range(9):
        y = 12 + k * 22; hw = 10 + k * 6
        c = (int(28 + rs.randint(0, 10)), int(44 + rs.randint(0, 12)), int(40 + rs.randint(0, 10)), 255)
        d.polygon([(64, y - 4), (64 + hw, y + 30), (64 - hw, y + 30)], fill=c)
        d.line([(64 - hw + 4, y + 29), (64 + hw - 4, y + 29)], fill=(20, 30, 28, 255), width=2)
    return prelit(im, 1.0)

def sidewalk():      # 4.5 m wide strip (x across), tile 4 m (y along)
    W, H = 72, 64; im = Image.new('RGB', (W, H), (120, 116, 118)); d = ImageDraw.Draw(im)
    for y in range(0, H, 16):
        for x in range(0, W, 16):
            c = 104 + R.randint(-10, 10); d.rectangle([x + 1, y + 1, x + 14, y + 14], fill=(c, c - 4, c + 2))
    d.rectangle([0, 0, 3, H], fill=(150, 146, 140))
    return prelit(im)                                                            # sidewalk lit by vertex colour (B.1), B.2a ambient

WALLS = ['#C4B8A0', '#8E8A84', '#96523C', '#D6D2C8', '#6E7C88', '#A8A074', '#604032', '#5A826E', '#E2D4B4', '#80788C', '#B8B0AA', '#464850']
def facade(seed, wall, w_m=8, h_m=24, px=16):
    """Pre-lit night facade (B.1), NO lettering. Returns image with x along, y down (top row = roof)."""
    rs = random.Random(seed); W, H = w_m * px, h_m * px
    a = np.tile(hx(wall) * hx(PAL['ambient']) / 255 * PAL['ambient_k'] * CAL['facade_amb_gain'] * 2, (H, W, 1)) + noise(W, H, 3, 8, seed)[..., None]   # wall x B.2a ambient
    if seed % 3 == 2:
        for y in range(0, H, 3): a[y, :] *= 0.82
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    fh = 3.6 * px; floors = int((H - fh) // (3.2 * px)); cols = max(1, int(w_m // 2.6))
    for f in range(floors):
        y0 = H - fh - (f + 1) * 3.2 * px + 11
        for c in range(cols):
            x0 = c * W / cols + 5; x1 = (c + 1) * W / cols - 5; r = rs.random()
            col = hx('#161C2A') if r < .5 else hx('#FFD28C' if r < .8 else '#B4E1FF') * rs.uniform(.45, .7)
            d.rectangle([x0, y0, x1, y0 + 29], fill=tuple(int(v) for v in col), outline=(20, 20, 24))
            if r >= .5 and rs.random() < .4:
                for yy in range(int(y0) + 2, int(y0) + 29, 3): d.line([x0, yy, x1, yy], fill=tuple(int(v * .7) for v in col))
            if rs.random() < .25: d.rectangle([x1 - 15, y0 + 31, x1 - 1, y0 + 41], fill=(130, 130, 126), outline=(60, 60, 60))
    gy = H - fh; d.rectangle([0, gy, W, gy + 5], fill=(30, 30, 34))
    gk = rs.choice(['shutter', 'shop', 'shop', 'dark'])
    if gk == 'shutter':
        d.rectangle([6, gy + 8, W - 6, H - 1], fill=(92, 80, 74))
        for yy in range(int(gy) + 9, H, 3): d.line([6, yy, W - 6, yy], fill=(66, 58, 54))
    elif gk == 'shop':                      # lit shop, toned down so it never out-shines the car (B.1)
        lc = hx(rs.choice(['#FFD28C', '#B4E1FF'])) * .5
        d.rectangle([6, gy + 20, W - 6, H - 3], fill=tuple(int(v) for v in lc), outline=(30, 30, 30), width=2)
        for k in range(rs.randint(2, 4)): yy = gy + 30 + k * 12; d.rectangle([10, yy, W - 10, yy + 2], fill=tuple(int(v * .6) for v in lc))
        d.rectangle([6, gy + 6, W - 6, gy + 19], fill=(20, 20, 26))     # blank fascia: no shop names (flag)
    else:
        d.rectangle([6, gy + 8, W - 6, H - 1], fill=(26, 26, 32))
    return im
def facade_strip(n=6):
    ims = [facade(100 + i, WALLS[(i * 5) % 12]) for i in range(n)]
    row = Image.new('RGB', (sum(i.width for i in ims), ims[0].height)); x = 0
    for i in ims: row.paste(i, (x, 0)); x += i.width
    return row.transpose(Image.Transpose.ROTATE_270)    # -> x = up (0 = ground), y = along

def neon_blank(col, w=24, h=96):    # unlit full-bright neon tube panel, NO lettering (doc B.1 wants made-up names; none canon -> blank)
    im = Image.new('RGB', (w, h), (20, 16, 24)); d = ImageDraw.Draw(im); c = tuple(int(v) for v in hx(col))
    d.rectangle([2, 2, w - 3, h - 3], outline=c, width=2)
    for y in range(10, h - 10, 14): d.line([7, y, w - 8, y], fill=c, width=2)
    return Image.blend(im.filter(ImageFilter.GaussianBlur(1.5)), im, 0.7)

def cutout(kind):
    W, H = 64, 64; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 'cone':
        d.polygon([(32, 5), (44, 56), (20, 56)], fill=(240, 80, 20, 255)); d.rectangle([14, 55, 50, 61], fill=(240, 80, 20, 255))
        d.polygon([(28, 22), (36, 22), (38, 31), (26, 31)], fill=(235, 235, 235, 255))
    elif kind == 'bike':
        for cx in (15, 49): d.ellipse([cx - 12, 30, cx + 12, 54], outline=(30, 30, 30, 255), width=2)
        d.line([(15, 42), (30, 26), (49, 42), (32, 42), (15, 42)], fill=(214, 210, 200, 255), width=3)
    elif kind == 'plant':
        d.rectangle([22, 45, 42, 62], fill=(40, 80, 160, 255))
        for _ in range(30): x, y = R.randint(14, 50), R.randint(15, 46); d.ellipse([x - 5, y - 4, x + 5, y + 4], fill=(40 + R.randint(0, 30), 100 + R.randint(0, 40), 50, 255))
    elif kind == 'vending':   # pre-lit (B.1): not ambient-multiplied
        d.rectangle([12, 2, 52, 62], fill=(180, 184, 190, 255)); d.rectangle([15, 5, 49, 32], fill=(200, 208, 212, 255))
        for r in range(3):
            for c in range(5): d.rectangle([17 + c * 6, 7 + r * 8, 21 + c * 6, 13 + r * 8], fill=(60 + R.randint(0, 150), 80 + R.randint(0, 120), 120 + R.randint(0, 100), 255))
        d.rectangle([15, 36, 49, 42], fill=(40, 40, 40, 255)); d.rectangle([18, 48, 46, 56], fill=(30, 30, 30, 255))
        return im
    return prelit(im, 1.0)

def sky(cfg, W=2048):   # sky cylinder strip (row 0 = top, horizon at the middle row = camera height); recipe: tones/work/make_tone_tex.py:14-23
    H = 128; hz = H // 2; a = np.tile(hx(cfg['fog']), (H, 1))
    t = (np.arange(hz) / hz)[:, None]; z, h = hx(cfg['sky_zenith']), hx(cfg['sky_horizon'])
    a[:hz] = z[None] * (1 - t ** 1.8) + h[None] * t ** 1.8                      # zen -> fog, t^1.8; no city-glow band (B.2a)
    a[hz - 3:hz] = hx(cfg['fog'])                                                # bottom band == fog
    a = np.repeat(a[:, None, :], W, 1); rng = np.random.default_rng(5)
    for _ in range(70 * W // 512):                                               # stars (90,100,150) in the upper half
        a[rng.integers(0, int(hz * .8)), rng.integers(0, W)] = PAL['stars']
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def skyline(seed, W=512, H=96):      # painted skyline card (B.1), x around, y up (row 0 top)
    rs = random.Random(seed); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 0
    while x < W:
        bw, bh = rs.randint(18, 50), rs.randint(24, H - 4); d.rectangle([x, H - bh, x + bw, H], fill=(18, 14, 28, 255))
        for yy in range(H - bh + 3, H, 4):
            for xx in range(x + 2, x + bw - 2, 4):
                if rs.random() < .25: d.rectangle([xx, yy, xx + 1, yy + 1], fill=tuple(int(v) for v in hx(rs.choice(['#FFD28C', '#B4E1FF', '#FFFFFF']))) + (255,))
        x += bw + rs.randint(-4, 4)
    return im
def ridge(seed, W=512, H=64):        # Touge: far ridge silhouette, a shade darker than fog (doc silent on Touge skyline: plain)
    rs = random.Random(seed); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(0, H)]; y = H * .5
    for x in range(0, W + 16, 16): y = min(H - 6, max(8, y + rs.randint(-6, 6))); pts.append((x, y))
    pts.append((W, H)); d.polygon(pts, fill=(30, 36, 40, 255)); return im   # PLACEHOLDER colour: a shade darker than the Touge fog
def glow(col, size=64):
    yy, xx = np.mgrid[0:size, 0:size]; r = np.sqrt((xx - size / 2 + .5) ** 2 + (yy - size / 2 + .5) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2; c = hx(col)
    return Image.fromarray(np.dstack([np.tile(c, (size, size, 1)), a * 255]).astype(np.uint8), 'RGBA')
def lamp_glow(col, size=64):   # make_tone_tex.py:31-38 glow_tex='per-lamp': hard white-hot core, lamp tint x .8, 3 hard alpha bands
    yy, xx = np.mgrid[0:size, 0:size]; r = np.sqrt((xx - size / 2 + .5) ** 2 + (yy - size / 2 + .5) ** 2) / (size / 2)
    al = np.clip(1 - r, 0, 1) ** 2.2; core = (al > .8).astype(np.float32)[..., None]
    rgb = hx(col)[None, None] * .8 * (1 - core) + np.array([255, 245, 235.])[None, None] * core
    al = np.floor(al * 3) / 3
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), 'RGBA')
def blob_shadow():
    W, H = 64, 128; yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2); a = np.clip(1 - r, 0, 1) ** .7 * 220
    return Image.fromarray(np.dstack([np.zeros((H, W, 3)), a]).astype(np.uint8), 'RGBA')
def headlight_throw():   # x across, y forward (row 0 = at the bumper); stepped, reduced strength (A.4.4)
    W, H = 64, 128; yy, xx = np.mgrid[0:H, 0:W]
    fan = np.clip(1 - np.abs(xx - W / 2) / (W / 2 * (0.25 + .75 * yy / H)), 0, 1) * np.clip(1 - yy / H, 0, 1) ** 1.2
    a = np.floor(fan * 4) / 4 * 150; c = hx('#FFF2CC')
    return Image.fromarray(np.dstack([np.tile(c, (H, W, 1)), a]).astype(np.uint8), 'RGBA')

# ── HUD stand-ins (B.5: bitmap-style font, 9-slice panels at native res); assets/fonts + assets/ui are empty ──
def bitmap_font():
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 8)
    cw, ch = 6, 9; chars = [chr(c) for c in range(32, 127)]; cols = 16; rows = math.ceil(len(chars) / cols)
    im = Image.new('L', (cols * cw, rows * ch), 0); d = ImageDraw.Draw(im)
    for i, c in enumerate(chars): d.text(((i % cols) * cw, (i // cols) * ch - 1), c, font=f, fill=255)
    a = (np.asarray(im) > 110).astype(np.uint8) * 255            # hard 1-bit glyphs: no anti-aliasing
    Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA').save(os.path.join(OUT, 'font_6x9.png'))
    json.dump({'cell': [cw, ch], 'cols': cols, 'first': 32, 'count': len(chars)}, open(os.path.join(OUT, 'font.json'), 'w'))
def panel9():           # 12x12, 4 px corners: dark navy fill (#060614 zenith), 1 px #9597AD frame, hard corners
    im = Image.new('RGBA', (12, 12), (10, 14, 36, 128)); d = ImageDraw.Draw(im)   # lane_chain/v5/post_v5.py:16-17,149-153: navy 50/50, EDGE frame
    d.rectangle([0, 0, 11, 11], outline=(210, 230, 255, 255)); d.rectangle([1, 1, 10, 10], outline=(70, 90, 150, 255))
    d.point([(0, 0), (11, 0), (0, 11), (11, 11)], fill=(0, 0, 0, 0))
    im.save(os.path.join(OUT, 'panel9.png'))
def logo(w=384):        # approved V3 wordmark (art/logo/final, Austin 2026-11-02), downsampled to native res, hard 1-bit alpha
    src = Image.open(os.path.join(HERE, '..', '_pin', 'art', 'logo', 'final', 'v3_white_on_black.png')).convert('L')
    h = round(src.height * w / src.width); a = (np.asarray(src.resize((w, h), Image.LANCZOS)) > 128).astype(np.uint8) * 255
    Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA').save(os.path.join(OUT, 'logo_v3.png'))

if __name__ == '__main__':
    for dk, cfg in DIST.items():
        save(road(dk, cfg), f'{dk}_road.png'); save(verge(cfg), f'{dk}_verge.png'); save(sky(cfg), f'{dk}_sky.png')
    save(guardrail(), 'touge_rail.png'); save(cedar(1), 'touge_cedar_a.png'); save(cedar(2), 'touge_cedar_b.png'); save(ridge(3), 'touge_ridge.png')
    save(sidewalk(), 'street_walk.png'); save(facade_strip(), 'street_facade.png'); save(skyline(1), 'street_skyline.png')
    for i, c in enumerate(DIST['street']['neon']): save(neon_blank(c), f'street_neon_{i}.png')
    for k in ('cone', 'bike', 'plant', 'vending'): save(cutout(k), f'street_cut_{k}.png')
    save(lamp_glow(PAL['lamp']), 'glow_lamp.png', q=False); save(glow('#FFF2CC'), 'glow_head.png', q=False)
    save(glow('#FF1F14'), 'glow_tail.png', q=False); save(glow('#FFFFFF'), 'glow_white.png', q=False)
    save(blob_shadow(), 'blob_shadow.png', q=False); save(headlight_throw(), 'headlight_throw.png', q=False)
    bitmap_font(); panel9(); logo()
    print('art ->', OUT, sorted(os.listdir(OUT)))
