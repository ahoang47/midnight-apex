"""BRZ 256x256 parts atlas (PIL, 4x supersampled), quantised RGB555 + 4x4 Bayer by tex/quant.py.
Tiles: wheel + tyre (10 twin-spoke, fictional sidewall lettering, no brakes/calipers), headlight lens (wedge, tall at the
outer end), taillight lens (swept boomerang), hex grille mesh, fictional plate, made-up emblem and wordmark, amber
marker, exhaust tip.  No real brands.  PIL row 0 = v 1.  Usage: python3 tex/make_atlas.py out.png"""
import math, sys, os
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import rgb555_bayer
S = 256; SS = 4
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FC = '/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf'
FI = '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'brz_atlas.png'
UV = dict(WHEEL=(0, .5, .5, 1), HEAD=(.5, .75, 1, 1), TAIL=(.5, .5, 1, .75), GRILLE=(0, .25, .5, .5),
          PLATE=(.5, .25, .875, .4375), WORD=(.5, .4375, .875, .5), EMBLEM=(.875, .4375, 1, .5),
          AMBER=(.875, .25, 1, .3125), EXH=(.875, .3125, 1, .4375), TREAD=(0, 0, .5, .25))
A = Image.new('RGB', (S * SS, S * SS), (10, 10, 12))
def box(u0, v0, u1, v1): return (round(u0 * S * SS), round((1 - v1) * S * SS), round(u1 * S * SS), round((1 - v0) * S * SS))
def tile(k):
    b = box(*UV[k]); return Image.new('RGB', (b[2] - b[0], b[3] - b[1]), (0, 0, 0)), b
F = lambda px, p=FB: ImageFont.truetype(p, int(px))
def grad(im, top, bot, horiz=False):
    d = ImageDraw.Draw(im); w, h = im.size; n = w if horiz else h
    for i in range(n):
        t = i / max(n - 1, 1); c = tuple(int(a + (b - a) * t) for a, b in zip(top, bot))
        d.line([(i, 0), (i, h)] if horiz else [(0, i), (w, i)], fill=c)

# ---- wheel + tyre (0,.5,.5,1): tile spans the tyre OD; rim = 18/25.0 of it
im, b = tile('WHEEL'); w, h = im.size; d = ImageDraw.Draw(im); c = w / 2
Rt = w * .5; Rr = Rt * 0.72
d.ellipse([c - Rt, c - Rt, c + Rt, c + Rt], fill=(24, 24, 26))
d.ellipse([c - Rt * .96, c - Rt * .96, c + Rt * .96, c + Rt * .96], outline=(34, 34, 37), width=6)
d.ellipse([c - Rr * 1.07, c - Rr * 1.07, c + Rr * 1.07, c + Rr * 1.07], outline=(14, 14, 15), width=10)
f = F(w * .05)
for word, a0 in (("VORTA  APEX-R", -62), ("215/40 R18  89Y", 118)):      # fictional tyre brand
    for k, ch in enumerate(word):
        a = math.radians(a0 + k * 6.0); rr = (Rt * .965 + Rr * 1.07) / 2
        ci = Image.new('RGBA', (int(w * .08), int(w * .08)), (0, 0, 0, 0)); ImageDraw.Draw(ci).text((w * .015, 0), ch, font=f, fill=(118, 118, 122, 255))
        ci = ci.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        im.paste(ci, (int(c + rr * math.cos(a) - ci.width / 2), int(c + rr * math.sin(a) - ci.height / 2)), ci)
d.ellipse([c - Rr * 1.04, c - Rr * 1.04, c + Rr * 1.04, c + Rr * 1.04], fill=(150, 152, 158))     # rim lip
d.ellipse([c - Rr * .96, c - Rr * .96, c + Rr * .96, c + Rr * .96], fill=(18, 18, 20))            # dark barrel (no brakes)
d.ellipse([c - Rr * .80, c - Rr * .80, c + Rr * .80, c + Rr * .80], fill=(30, 30, 33))
for k in range(10):                                                   # 10 twin spokes (5 pairs x 2? -> 10 pairs)
    a = math.radians(-90 + k * 36)
    for off in (-0.085, 0.085):
        ai, ao = a + off * 0.55, a + off
        p = [(c + Rr * .30 * math.cos(ai - .05), c + Rr * .30 * math.sin(ai - .05)), (c + Rr * .30 * math.cos(ai + .05), c + Rr * .30 * math.sin(ai + .05)),
             (c + Rr * .97 * math.cos(ao + .035), c + Rr * .97 * math.sin(ao + .035)), (c + Rr * .97 * math.cos(ao - .035), c + Rr * .97 * math.sin(ao - .035))]
        d.polygon(p, fill=(92, 94, 100), outline=(48, 49, 53))
        p2 = [p[0], p[1], ((p[1][0] + p[2][0]) / 2, (p[1][1] + p[2][1]) / 2), ((p[0][0] + p[3][0]) / 2, (p[0][1] + p[3][1]) / 2)]
        d.polygon(p2, fill=(118, 120, 126))                          # machined highlight on the inner half
d.ellipse([c - Rr * .34, c - Rr * .34, c + Rr * .34, c + Rr * .34], fill=(84, 86, 92), outline=(44, 45, 49), width=5)
for k in range(5):
    a = math.radians(-90 + k * 72); x, y = c + Rr * .21 * math.cos(a), c + Rr * .21 * math.sin(a)
    d.ellipse([x - w * .02, y - w * .02, x + w * .02, y + w * .02], fill=(36, 36, 40))
d.ellipse([c - w * .05, c - w * .05, c + w * .05, c + w * .05], fill=(26, 26, 30))
d.regular_polygon((c, c, w * .03), 6, fill=(150, 152, 158))           # made-up hex centre cap
A.paste(im, b)
# ---- tyre tread (0,0,.5,.25): dark rubber with grooves (wrapped around the tread)
im, b = tile('TREAD'); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(26, 26, 28))
for yy in (.2, .42, .58, .8): d.rectangle([0, h * yy - 6, w, h * yy + 6], fill=(12, 12, 13))
for x in range(0, w, 24): d.line([(x, 0), (x + 10, h * .2)], fill=(15, 15, 16), width=5); d.line([(x, h), (x + 10, h * .8)], fill=(15, 15, 16), width=5)
A.paste(im, b)

# ---- headlight (.5,.75,1,1): u 0 = inner tip (near the badge) -> 1 = tall outer end; v 0 = bottom
im, b = tile('HEAD'); w, h = im.size; d = ImageDraw.Draw(im)
grad(im, (78, 82, 92), (30, 32, 38))                                  # smoked housing behind the cover
for x in range(0, w, 12): d.line([(x, h * .2), (x + 14, h * .95)], fill=(46, 49, 56), width=3)
cx, cy, r = w * .70, h * .54, h * .30                                 # main projector (outer)
d.ellipse([cx - r * 1.3, cy - r * 1.3, cx + r * 1.3, cy + r * 1.3], fill=(16, 16, 20))
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 204, 216)); d.ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55], fill=(250, 252, 255))
cx2, r2 = w * .43, h * .20                                            # second projector
d.ellipse([cx2 - r2 * 1.3, cy - r2 * 1.3, cx2 + r2 * 1.3, cy + r2 * 1.3], fill=(16, 16, 20))
d.ellipse([cx2 - r2, cy - r2, cx2 + r2, cy + r2], fill=(186, 194, 206)); d.ellipse([cx2 - r2 * .5, cy - r2 * .5, cx2 + r2 * .5, cy + r2 * .5], fill=(245, 248, 255))
# L-shaped LED DRL: along the lower edge from the inner tip, turning up the tall outer end
d.line([(w * .04, h * .80), (w * .86, h * .88), (w * .95, h * .82), (w * .97, h * .16)], fill=(245, 250, 255), width=int(h * .085), joint='curve')
d.rectangle([w * .06, h * .90, w * .30, h * .99], fill=(230, 130, 30))   # amber strip under the inner end
d.line([(0, h * .06), (w, h * .02)], fill=(225, 230, 238), width=6)    # cover highlight
d.rectangle([0, 0, w - 1, h - 1], outline=(10, 10, 12), width=6)
A.paste(im, b)
# ---- taillight (.5,.5,1,.75): u 0 = pointed inner end on the rear face -> 1 = front tip on the flank; v 0 = bottom
im, b = tile('TAIL'); w, h = im.size; d = ImageDraw.Draw(im)
grad(im, (64, 6, 10), (28, 2, 4))                                     # smoked red lens
for x in range(0, w, 10): d.line([(x, 0), (x, h)], fill=(52, 4, 8), width=3)
# swept boomerang light bar: runs along the top from the inner end, kinks down at the corner (u ~.62), sweeps forward
pts = [(w * .05, h * .55), (w * .30, h * .30), (w * .60, h * .26), (w * .66, h * .55), (w * .96, h * .40)]
d.line(pts, fill=(255, 40, 34), width=int(h * .16), joint='curve')
d.line(pts, fill=(255, 150, 130), width=int(h * .05), joint='curve')
for k in range(7):                                                    # vertical fins inside the boomerang
    x = w * (.10 + .07 * k); d.line([(x, h * .45), (x, h * .85)], fill=(150, 10, 14), width=5)
d.rectangle([w * .14, h * .66, w * .30, h * .84], fill=(205, 200, 200))  # clear reverse segment
d.line([(0, h * .08), (w, h * .12)], fill=(150, 70, 70), width=5)     # cover highlight
d.rectangle([0, 0, w - 1, h - 1], outline=(14, 2, 3), width=6)
A.paste(im, b)
# ---- hex grille mesh (0,.25,.5,.5)
im, b = tile('GRILLE'); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(6, 6, 7)); cw, ch = 28, 22
for j in range(-1, h // ch + 2):
    for i in range(-1, w // cw + 2):
        x = i * cw + (cw / 2 if j % 2 else 0); y = j * ch
        d.polygon([(x, y + ch * .5), (x + cw * .25, y), (x + cw * .75, y), (x + cw, y + ch * .5), (x + cw * .75, y + ch), (x + cw * .25, y + ch)],
                  outline=(88, 90, 98), fill=(12, 12, 14))
        d.line([(x + cw * .25, y + 2), (x + cw * .75, y + 2)], fill=(84, 86, 92), width=2)   # top-lit hex edges
A.paste(im, b)
# ---- plate (.5,.25,.875,.4375): fictional Midnight Apex plate, 2:1
im, b = tile('PLATE'); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(236, 236, 230)); d.rectangle([6, 6, w - 7, h - 7], outline=(30, 40, 70), width=8)
t = "MIDNIGHT APEX"; f = F(h * .17); d.text(((w - d.textlength(t, font=f)) / 2, h * .08), t, font=f, fill=(30, 40, 90))
t = "KS 27-04"; f = F(h * .46, FC); d.text(((w - d.textlength(t, font=f)) / 2, h * .34), t, font=f, fill=(20, 26, 60))
A.paste(im, b)
# ---- wordmark (.5,.4375,.875,.5): made-up model name, chrome on body blue
im, b = tile('WORD'); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(22, 52, 128))
t = "KESTREL"; f = F(h * .9, FI); tw = d.textlength(t, font=f)
d.text(((w - tw) / 2 + 3, 3), t, font=f, fill=(8, 18, 50)); d.text(((w - tw) / 2, 0), t, font=f, fill=(222, 226, 234))
A.paste(im, b)
# ---- emblem (.875,.4375,1,.5): made-up mark, a chrome chevron in a dark oval (no real logo)
im, b = tile('EMBLEM'); w, h = im.size; d = ImageDraw.Draw(im)
d.rectangle([0, 0, w, h], fill=(22, 52, 128))
d.ellipse([w * .04, h * .06, w * .96, h * .94], fill=(20, 22, 30), outline=(220, 224, 232), width=max(4, h // 10))
d.polygon([(w * .22, h * .64), (w * .5, h * .28), (w * .78, h * .64), (w * .66, h * .64), (w * .5, h * .44), (w * .34, h * .64)], fill=(225, 228, 236))
A.paste(im, b)
# ---- amber marker, exhaust tip
im, b = tile('AMBER'); ImageDraw.Draw(im).rectangle([0, 0, *im.size], fill=(250, 140, 24)); A.paste(im, b)
im, b = tile('EXH'); w, h = im.size; d = ImageDraw.Draw(im); c = w / 2
d.rectangle([0, 0, w, h], fill=(20, 20, 22)); d.ellipse([2, 2, w - 3, h - 3], fill=(170, 172, 178)); d.ellipse([w * .14, h * .14, w * .86, h * .86], fill=(10, 10, 10))
A.paste(im, b)
A = A.resize((S, S), Image.LANCZOS)
rgb555_bayer(A).save(OUT); print('atlas', OUT)
