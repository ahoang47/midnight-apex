"""S2000 256x256 'PS2' atlas (same UV layout as the 128 atlas, twice the detail). Run with system python (PIL).
Tiles are drawn upright in PIL; PIL row 0 = v 1."""
import math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = 256; SS = 4   # supersample then downsample (smooth, slightly soft, like a 256px PS2 texture)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FBO = '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'
FC = '/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf'
OUT = sys.argv[1] if len(sys.argv) > 1 else __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))), 's2000_atlas.png')
A = Image.new('RGB', (S * SS, S * SS), (12, 12, 12))
def box(u0, v0, u1, v1): return (round(u0 * S * SS), round((1 - v1) * S * SS), round(u1 * S * SS), round((1 - v0) * S * SS))
def tile(rect):
    b = box(*rect); return Image.new('RGB', (b[2] - b[0], b[3] - b[1]), (0, 0, 0)), b
def F(px, path=FB): return ImageFont.truetype(path, px)
def grad(im, top, bot):
    d = ImageDraw.Draw(im); w, h = im.size
    for y in range(h):
        t = y / max(h - 1, 1); d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))

# ---- headlight (0,.5,.5,1): left = inner tip, right = big outer end, top = upper edge
im, b = tile((0, .5, .5, 1)); w, h = im.size; d = ImageDraw.Draw(im)
grad(im, (190, 196, 204), (120, 126, 136))                       # clear cover over chrome bowl
d.rectangle([w * .05, h * .12, w * .97, h * .86], fill=(70, 74, 82))
for x in range(int(w * .06), int(w * .96), 10): d.line([(x, h * .14), (x + 18, h * .84)], fill=(84, 88, 98), width=3)   # reflector facets
for cx, rx, ry in ((.72, .15, .30), (.42, .11, .24)):         # projector + low beam
    cx *= w; rx *= w; ry *= h; cy = h * .48
    d.ellipse([cx - rx * 1.25, cy - ry * 1.25, cx + rx * 1.25, cy + ry * 1.25], fill=(28, 28, 32))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(205, 212, 222))
    d.ellipse([cx - rx * .62, cy - ry * .62, cx + rx * .62, cy + ry * .62], fill=(240, 244, 250))
    d.ellipse([cx - rx * .3, cy - ry * .3, cx + rx * .3, cy + ry * .3], fill=(255, 255, 250))
d.rectangle([w * .80, h * .80, w * .97, h * .97], fill=(255, 140, 20))   # amber corner (UV_AMBER samples here)
d.line([(w * .06, h * .1), (w * .96, h * .1)], fill=(235, 238, 242), width=8)  # cover highlight along the top
d.rectangle([0, 0, w - 1, h - 1], outline=(18, 18, 20), width=8)
A.paste(im, b)
# amber turn signal sample area UV_AMBER (.41,.51,.48,.56)
ImageDraw.Draw(A).rectangle(box(.405, .505, .485, .565), fill=(255, 140, 20))

# ---- taillight (.5,.5,1,1): top half = lens housing (left = inner end, right = wraps to the side); bottom = lamp tiles
im, b = tile((.5, .75, 1, 1)); w, h = im.size; d = ImageDraw.Draw(im)
grad(im, (190, 22, 22), (105, 6, 8))
for x in range(0, w, 14): d.line([(x, 0), (x, h)], fill=(150, 12, 14), width=4)     # fine lens optics
d.rectangle([0, h * .18, w, h * .26], fill=(235, 120, 110))                          # glossy streak
d.rectangle([0, 0, w - 1, h - 1], outline=(50, 2, 2), width=10)
A.paste(im, b)
for rect, kind in (((.5, .5, .75, .75), 0), ((.75, .5, 1, .75), 1)):
    im, b = tile(rect); w, h = im.size; d = ImageDraw.Draw(im); c = w / 2; R = w * .47
    d.rectangle([0, 0, w, h], fill=(110, 8, 8))
    d.ellipse([c - R, c - R, c + R, c + R], fill=(55, 0, 0))
    d.ellipse([c - R * .9, c - R * .9, c + R * .9, c + R * .9], fill=(235, 30, 26))
    if kind == 0:   # outer: brake/tail with an inner ring
        d.ellipse([c - R * .62, c - R * .62, c + R * .62, c + R * .62], fill=(120, 4, 4))
        d.ellipse([c - R * .52, c - R * .52, c + R * .52, c + R * .52], fill=(250, 60, 50))
        d.ellipse([c - R * .22, c - R * .22, c + R * .22, c + R * .22], fill=(255, 170, 150))
    else:           # inner: turn/reverse split by a bar
        d.rectangle([c - R * .9, c - R * .07, c + R * .9, c + R * .07], fill=(60, 0, 0))
        d.chord([c - R * .8, c - R * .8, c + R * .8, c + R * .8], 180, 360, fill=(250, 70, 60))
        d.chord([c - R * .8, c - R * .8, c + R * .8, c + R * .8], 0, 180, fill=(235, 225, 225))   # clear reverse lens
        d.rectangle([c - R * .9, c - R * .07, c + R * .9, c + R * .07], fill=(60, 0, 0))
    for k in range(10):   # fresnel rings
        rr = R * (.2 + .07 * k); d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(255, 120, 110) if k % 2 else (170, 10, 10), width=2)
    d.arc([c - R * .8, c - R * .8, c + R * .8, c + R * .8], 200, 250, fill=(255, 230, 230), width=10)   # highlight
    A.paste(im, b)

# ---- grille (0,0,.5,.30): honeycomb-ish black mesh
im, b = tile((0, 0, .5, .30)); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(8, 8, 9))
cw, ch = 26, 18
for j in range(-1, h // ch + 2):
    for i in range(-1, w // cw + 2):
        x = i * cw + (cw / 2 if j % 2 else 0); y = j * ch
        d.polygon([(x, y + ch * .5), (x + cw * .25, y), (x + cw * .75, y), (x + cw, y + ch * .5), (x + cw * .75, y + ch), (x + cw * .25, y + ch)],
                  outline=(48, 48, 52), fill=(14, 14, 16))
d.line([(w / 2, 0), (w / 2, h)], fill=(30, 30, 33), width=10)
A.paste(im, b)
# ---- 'S2000' rear emblem (0,.31,.25,.365): chrome letters on Formula Red
im, b = tile((0, .31, .25, .365)); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(200, 13, 15))
f = F(int(h * .95), FBO); tw = d.textlength("S2000", font=f)
d.text(((w - tw) / 2 + 3, h * .05 + 3), "S2000", font=f, fill=(60, 0, 0))
d.text(((w - tw) / 2, h * .05), "S2000", font=f, fill=(222, 226, 232))
A.paste(im, b)
# ---- 'H' badge (0.004,.379,.121,.496): chrome H in a rounded frame on black
im, b = tile((0.004, .379, .121, .496)); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(200, 13, 15))
d.rounded_rectangle([w * .06, h * .1, w * .94, h * .9], radius=w * .12, fill=(30, 30, 34), outline=(225, 228, 234), width=max(4, w // 14))
for x0 in (.28, .62): d.rectangle([w * x0, h * .26, w * (x0 + .12), h * .74], fill=(225, 228, 234))
d.rectangle([w * .28, h * .45, w * .74, h * .55], fill=(225, 228, 234))
A.paste(im, b)
# ---- licence plate (.13,.375,.49,.495)
im, b = tile((.13, .375, .49, .495)); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(238, 238, 232)); d.rectangle([4, 4, w - 5, h - 5], outline=(40, 70, 40), width=10)
f = F(int(h * .30)); d.text((w * .08, h * .08), "Honda", font=f, fill=(40, 90, 40))
f2 = F(int(h * .52), FC); t = "S 20-00"; tw = d.textlength(t, font=f2); d.text(((w - tw) / 2, h * .38), t, font=f2, fill=(30, 80, 30))
A.paste(im, b)

# ---- wheel (.5,0,1,.5): 16" AP1 seven split-spoke rim + tyre sidewall
im, b = tile((.5, 0, 1, .5)); w, h = im.size; d = ImageDraw.Draw(im); c = w / 2
d.rectangle([0, 0, w, h], fill=(16, 16, 17))
Rt, Rr = w * .5, w * .5 * 21 / 32 * 1.0
d.ellipse([c - Rt, c - Rt, c + Rt, c + Rt], fill=(26, 26, 27))
d.ellipse([c - Rt * .97, c - Rt * .97, c + Rt * .97, c + Rt * .97], outline=(36, 36, 38), width=6)
# sidewall lettering
f = F(int(w * .045))
for word, a0 in (("POTENZA  S-02", -60), ("205/55R16  87W", 120)):
    for k, ch_ in enumerate(word):
        a = math.radians(a0 + k * 6.2); rr = (Rt + Rr) / 2 + w * .005
        ci = Image.new('RGBA', (int(w * .07), int(w * .07)), (0, 0, 0, 0)); ImageDraw.Draw(ci).text((w * .012, 0), ch_, font=f, fill=(92, 92, 96, 255))
        ci = ci.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        im.paste(ci, (int(c + rr * math.cos(a) - ci.width / 2), int(c + rr * math.sin(a) - ci.height / 2)), ci)
d.ellipse([c - Rr * 1.04, c - Rr * 1.04, c + Rr * 1.04, c + Rr * 1.04], fill=(200, 202, 206))     # rim lip
d.ellipse([c - Rr * .93, c - Rr * .93, c + Rr * .93, c + Rr * .93], fill=(22, 22, 24))            # dark barrel behind spokes
# painted brake hint behind the spokes (no geometry): dull disc with a darker hat, plus a caliper silhouette
d.ellipse([c - Rr * .80, c - Rr * .80, c + Rr * .80, c + Rr * .80], fill=(58, 58, 62))
d.ellipse([c - Rr * .78, c - Rr * .78, c + Rr * .78, c + Rr * .78], outline=(80, 80, 84), width=5)
d.ellipse([c - Rr * .45, c - Rr * .45, c + Rr * .45, c + Rr * .45], fill=(34, 34, 37))
for k in range(18):
    a_ = math.radians(k * 20); rr = Rr * (.58 + .1 * (k % 2))
    d.ellipse([c + rr * math.cos(a_) - 4, c + rr * math.sin(a_) - 4, c + rr * math.cos(a_) + 4, c + rr * math.sin(a_) + 4], fill=(38, 38, 41))
d.pieslice([c - Rr * .90, c - Rr * .90, c + Rr * .90, c + Rr * .90], -150, -95, fill=(30, 30, 33))   # caliper (rear-top)
d.pieslice([c - Rr * .55, c - Rr * .55, c + Rr * .55, c + Rr * .55], -150, -95, fill=(58, 58, 62))
for k in range(7):
    a = math.radians(-90 + k * 360 / 7)
    for off in (-1, 0, 1):   # each spoke splits into three fingers toward the rim
        ai = a + off * 0.035; ao = a + off * 0.13
        p = [(c + Rr * .30 * math.cos(ai - .07), c + Rr * .30 * math.sin(ai - .07)), (c + Rr * .30 * math.cos(ai + .07), c + Rr * .30 * math.sin(ai + .07)),
             (c + Rr * .95 * math.cos(ao + .045), c + Rr * .95 * math.sin(ao + .045)), (c + Rr * .95 * math.cos(ao - .045), c + Rr * .95 * math.sin(ao - .045))]
        d.polygon(p, fill=(196, 199, 205), outline=(120, 122, 128))
d.ellipse([c - Rr * .36, c - Rr * .36, c + Rr * .36, c + Rr * .36], fill=(190, 193, 199), outline=(110, 112, 118), width=4)
for k in range(5):
    a = math.radians(-90 + k * 72); x, y = c + Rr * .22 * math.cos(a), c + Rr * .22 * math.sin(a)
    d.ellipse([x - w * .022, y - w * .022, x + w * .022, y + w * .022], fill=(70, 70, 74))
d.ellipse([c - w * .045, c - w * .045, c + w * .045, c + w * .045], fill=(30, 30, 34))
fH = F(int(w * .05)); d.text((c - w * .017, c - w * .03), "H", font=fH, fill=(210, 210, 215))
A.paste(im, b)

A = A.resize((S, S), Image.LANCZOS)
A.save(OUT); print("atlas", OUT)
