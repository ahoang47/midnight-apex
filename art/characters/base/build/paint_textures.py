"""Paint the placeholder textures (PSX painted style, nearest filtered, RGB555 + 4x4 Bayer).
python3 paint_textures.py  ->  ../textures/*.png"""
import os, math, numpy as np
from PIL import Image, ImageDraw
import spec
OUT = spec.TEXDIR
rng = np.random.default_rng(3)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

class Tex:
    def __init__(self, size, base="#808080"):
        self.S = size; self.a = np.ones((size, size, 3)) * hexc(base)
    def px(self, u, v): return u * self.S, (1 - v) * self.S
    def rect(self, r, col, noise=0.0, grad=None):
        u0, v0, u1, v1 = r; S = self.S
        x0, x1 = int(round(u0 * S)), int(round(u1 * S)); y0, y1 = int(round((1 - v1) * S)), int(round((1 - v0) * S))
        blk = np.ones((y1 - y0, x1 - x0, 3)) * hexc(col)
        if noise: blk *= (1 + rng.normal(0, noise, (y1 - y0, x1 - x0, 1)))
        if grad:  # (top factor, bottom factor) vertical shading
            g = np.linspace(grad[0], grad[1], y1 - y0)[:, None, None]; blk *= g
        self.a[y0:y1, x0:x1] = blk
    def shade_u(self, r, fn):
        """multiply columns by fn(u) inside rect (fake light wrap: front lit, sides/back darker)"""
        u0, v0, u1, v1 = r; S = self.S
        x0, x1 = int(u0 * S), int(u1 * S); y0, y1 = int((1 - v1) * S), int((1 - v0) * S)
        for x in range(x0, x1):
            uu = (x + .5 - x0) / max(1, x1 - x0)
            self.a[y0:y1, x] *= fn(uu)
    def save(self, name, draw_fn=None, down=None):
        img = Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8))
        if draw_fn: draw_fn(ImageDraw.Draw(img), self)
        if down: img = img.resize((down, down), Image.BOX)
        a = np.asarray(img).astype(float)
        H, W = a.shape[:2]
        b = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
        q = np.floor(a / 255.0 * 31 + b) / 31 * 255   # RGB555 + ordered dither
        os.makedirs(OUTD, exist_ok=True); Image.fromarray(np.clip(q, 0, 255).astype(np.uint8)).save(os.path.join(OUTD, name))
        print("wrote", name, img.size)

def vat(lf, coord, key=2):
    vs, _, _ = spec.ring_vs(lf); cs = [r[key] for r in lf["rings"]]
    if cs[0] > cs[-1]: cs = cs[::-1]; vs = vs[::-1]
    return float(np.interp(coord, cs, vs))

def wrap(uu):  # front (u=.5) brightest
    return 0.80 + 0.22 * math.cos((uu - 0.5) * 2 * math.pi) * 0.5 + 0.11


def R(d, box, **kw):   # rectangle with sorted corners
    x0, y0, x1, y1 = box; d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], **kw)

PAL = {
 "m": dict(SKIN="#D2A27E", TEE="#66788E", TEE_D=(84, 98, 116), ALT="#2F5753", JE="#28344F", HAIR_A=("#211A16", "#3A2E26"),
           HAIR_B=("#3B2A1E", "#6A4E36"), STRIPE=(60, 84, 120)),
 "f": dict(SKIN="#DDB08E", TEE="#8A8698", TEE_D=(110, 106, 124), ALT="#A8843C", JE="#34507A", HAIR_A=("#2B1E18", "#4E3A2C"),
           HAIR_B=("#5A3A22", "#8A6240"), STRIPE=(48, 120, 116)),
}

def paint(sex):
    global OUTD
    OUTD = os.path.join(OUT, sex)
    p = PAL[sex]; LOFTS = {l["name"]: l for l in spec.lofts(sex)}
    SKIN, TEE, JE = p["SKIN"], p["TEE"], p["JE"]
    for o in spec.OUTFITS[sex]: atlas(sex, p, LOFTS, alt=(o != "outfit_tee"), name=o + ".png")
    # ---------------- Head (generic placeholder face) ----------------
    lf = LOFTS["head"]
    t = Tex(256, SKIN)
    t.rect(lf["rect"], SKIN, 0.02, grad=(1.0, 0.86))
    t.shade_u(lf["rect"], wrap)
    t.rect((0, .92, 1, 1), "#2A211C", 0.08)           # crown painted as hair (hidden under hair pieces)
    t.rect(spec.EARS["rect"], "#C49272", 0.02)
    def head_draw(d, t):
        per = lambda z: 2 * math.pi * math.sqrt((.086 ** 2 + .1 ** 2) / 2)
        du = lambda m: m / per(0)
        ve, vb, vn, vm = vat(lf, 1.703), vat(lf, 1.728), vat(lf, 1.672), vat(lf, 1.638)
        for s in (-1, 1):
            cx, cy = t.px(.5 + s * du(.031), ve)
            R(d, [cx - 5, cy - 3, cx + 5, cy + 3], fill=(236, 232, 224))       # sclera
            R(d, [cx - 2, cy - 3, cx + 2, cy + 3], fill=(70, 52, 40))          # iris (brown)
            R(d, [cx - 1, cy - 2, cx + 1, cy + 1], fill=(18, 14, 12))          # pupil
            d.line([(cx - 6, cy - 4), (cx + 6, cy - 4)], fill=(30, 22, 18), width=2)  # lash line
            if sex == "f":
                d.line([(cx + s * 6, cy - 4), (cx + s * 8, cy - 6)], fill=(30, 22, 18), width=2)   # lash flick
                R(d, [cx - 5, cy - 6, cx + 5, cy - 5], fill=(190, 150, 140))                     # soft lid colour
            d.point([(cx + s * -1, cy - 2)], fill=(255, 255, 255))                    # catch-light
            bx, by = t.px(.5 + s * du(.033), vb)
            d.line([(bx - 7, by + (1 if s < 0 else 0)), (bx + 7, by + (0 if s < 0 else 1))], fill=(52, 38, 30), width=(3 if sex == "m" else 2))  # brows
        nx, ny = t.px(.5, vn)
        d.line([(nx - 1, ny - 10), (nx - 2, ny)], fill=(176, 128, 100))   # nose side shadow
        d.line([(nx - 4, ny + 1), (nx + 4, ny + 1)], fill=(150, 104, 82)) # nostril line
        mx, my = t.px(.5, vm)
        if sex == "f":
            R(d, [mx - 6, my - 2, mx + 6, my + 2], fill=(176, 92, 92)); d.line([(mx - 6, my), (mx + 6, my)], fill=(120, 58, 58))   # lips
        else:
            d.line([(mx - 7, my), (mx + 7, my)], fill=(120, 62, 58), width=2)   # mouth
        d.line([(mx - 5, my + 3), (mx + 5, my + 3)], fill=(196, 140, 112))  # lower lip light
        for s in (-1, 1):
            cx, cy = t.px(.5 + s * du(.05), (ve + vm) / 2)
            d.ellipse([cx - 5, cy - 3, cx + 5, cy + 3], fill=(214, 150, 122))  # soft cheek
        # ear inner shading
        u0, v0, u1, v1 = spec.EARS["rect"]
        x0, y0 = t.px(u0 + .03, v1 - .02); x1, y1 = t.px(u1 - .03, v0 + .02)
        d.ellipse([x0, y0, x1, y1], outline=(150, 104, 82), width=2)
        # hairline fringe hint
        for i in range(0, 256, 3):
            x, y = i, t.px(0, .92)[1]
            d.line([(x, y), (x, y + (i * 7) % 5 + 1)], fill=(42, 33, 28))
    t.save("head.png", head_draw, down=128)

    # ---------------- Hair ----------------
    def hair(name, base, hi, out):
        t = Tex(128, base)
        t.rect((0, 0, 1, 1), base, 0.06, grad=(1.15, 0.75))
        for i in range(70):   # strands
            x = rng.integers(0, 128); y0 = rng.integers(0, 90); ln = rng.integers(10, 38)
            c = hexc(hi) * rng.uniform(.8, 1.1)
            t.a[y0:y0 + ln, x] = c
        t.shade_u((0, 0, 1, 1), lambda uu: 0.85 + 0.15 * math.cos((uu - .5) * 2 * math.pi))
        t.save(out)
    hair("hair_a", *p["HAIR_A"], "hair_a.png")
    hair("hair_b", *p["HAIR_B"], "hair_b.png")


def dk(col, f): c = hexc(col) if isinstance(col, str) else np.array(col, float); return tuple(int(v) for v in c * f)

def atlas(sex, p, LOFTS, alt, name):
    """One 256 px outfit atlas for the whole body mesh (+ the outfit add-on). Clothes are painted on, PS1 style."""
    SKIN, TEE, JE = p["SKIN"], (p["ALT"] if alt else p["TEE"]), p["JE"]
    TD = dk(TEE, .78); TD2 = dk(TEE, .88); TD3 = dk(TEE, .64)
    t = Tex(256, SKIN)
    tl = LOFTS["torso"]; TR = tl["rect"]
    hem = .90 if alt else spec.HEM_Z
    vh = vat(tl, hem)
    t.rect((TR[0], vh, TR[2], TR[3]), TEE, 0.05, grad=(1.0, 0.84))
    t.rect((TR[0], TR[1], TR[2], vh), JE, 0.07)
    t.shade_u(TR, wrap)
    for sd in ("L", "R"):
        al = LOFTS["arm_" + sd]; r = al["rect"]; sg = 1 if sd == "L" else -1
        t.rect(r, SKIN, 0.025); 
        vs = vat(al, sg * (.755 if alt else spec.SLEEVE_X), 0)
        lo, hi = sorted((r[1], vs)) if True else None
        t.rect((r[0], r[1], r[2], vs), TEE, 0.05)
        t.shade_u(r, wrap)
        t.rect(LOFTS["hand_" + sd]["rect"], SKIN, 0.025); t.shade_u(LOFTS["hand_" + sd]["rect"], wrap)
        t.rect(LOFTS["thumb_" + sd]["rect"], SKIN, 0.02)
        ll = LOFTS["leg_" + sd]; t.rect(ll["rect"], JE, 0.07, grad=(1.0, 0.85)); t.shade_u(ll["rect"], wrap)
        t.rect(LOFTS["shoe_" + sd]["rect"], "#D8D6CE", 0.03)
    t.rect(LOFTS["neck"]["rect"], SKIN, 0.025); t.shade_u(LOFTS["neck"]["rect"], wrap)
    t.rect(spec.ATLAS["addon"], dk(TEE, .86) and "#%02x%02x%02x" % dk(TEE, .86), 0.06, grad=(1.1, 0.7))
    # denim twill on denim only
    yy, xx = np.mgrid[0:256, 0:256]; tw = (1 + 0.04 * ((xx + yy) % 3 == 0))[:, :, None]
    for rr in [ (TR[0], TR[1], TR[2], vh), LOFTS["leg_L"]["rect"], LOFTS["leg_R"]["rect"]]:
        x0, x1 = int(rr[0] * 256), int(rr[2] * 256); y0, y1 = int((1 - rr[3]) * 256), int((1 - rr[1]) * 256)
        t.a[y0:y1, x0:x1] *= tw[y0:y1, x0:x1]
    def draw(d, t):
        W0, W1 = t.px(TR[0], 0)[0], t.px(TR[2], 0)[0]
        TU = lambda f: TR[0] + (TR[2] - TR[0]) * f
        _, ytop = t.px(0, TR[3])
        # ---- jeans part of the torso
        _, yw0 = t.px(0, vat(tl, .955 if not alt else .90)); _, yw1 = t.px(0, vat(tl, .925))
        if not alt:
            R(d, [W0, yw0, W1, yw1], fill=dk(JE, .78))                                             # waistband
            for f in (.12, .3, .34, .66, .7, .88): x, _ = t.px(TU(f), 0); R(d, [x, yw0, x + 1, yw1 + 2], fill=dk(JE, 1.15))   # loops
        x, y0 = t.px(TU(.5), vat(tl, .925)); _, y1 = t.px(TU(.5), vat(tl, .86)); d.line([(x, y0), (x, y1)], fill=dk(JE, 1.3))   # fly
        # ---- top
        if alt:
            _, y0 = t.px(0, vat(tl, .945)); _, y1 = t.px(0, vat(tl, .90)); R(d, [W0, y0, W1, y1], fill=TD)       # rib hem
            if sex == "f":   # zip jacket: centre zip + slash pockets
                x, y0 = t.px(TU(.5), TR[3]); _, y1 = t.px(TU(.5), vat(tl, .90)); d.line([(x, y0), (x, y1)], fill=(60, 60, 64), width=2)
                for s_ in (-1, 1):
                    xa, ya = t.px(TU(.5 + s_ * .07), vat(tl, 1.07)); xb, yb = t.px(TU(.5 + s_ * .1), vat(tl, .98)); d.line([(xa, ya), (xb, yb)], fill=TD3, width=2)
            else:            # hoodie: kangaroo pocket + drawstrings
                xa, ya = t.px(TU(.5 - .085), vat(tl, 1.14)); xb, yb = t.px(TU(.5 + .085), vat(tl, .975))
                d.polygon([(xa + 6, ya), (xb - 6, ya), (xb, yb), (xa, yb)], fill=TD2, outline=TD3)
                for s_ in (-1, 1):
                    x, y = t.px(TU(.5 + s_ * .022), vat(tl, 1.50)); _, y2 = t.px(0, vat(tl, 1.32))
                    d.line([(x, y), (x, y2)], fill=(200, 200, 190)); R(d, [x - 1, y2, x + 1, y2 + 3], fill=(150, 150, 140))
        else:
            _, yc = t.px(0, vat(tl, 1.512)); R(d, [W0, ytop, W1, yc], fill=p["TEE_D"])               # collar rib
            _, yh = t.px(0, vat(tl, .962)); d.line([(W0, yh), (W1, yh)], fill=p["TEE_D"])            # hem stitch
            for k in range(3):
                x, y = t.px(TU(.5 + (k - 1) * .06), vat(tl, 1.06)); d.line([(x - 6, y), (x + 6, y + 3)], fill=p["TEE_D"])
        for f in (.25, .75):                                                                           # side seams
            x, y0 = t.px(TU(f), TR[3]); _, y1 = t.px(TU(f), TR[1]); d.line([(x, y0), (x, y1)], fill=TD if True else None)
        # ---- arms
        for sd in ("L", "R"):
            al = LOFTS["arm_" + sd]; u0, v0, u1, v1 = al["rect"]; sg = 1 if sd == "L" else -1
            if alt:
                x0, y0 = t.px(u0, vat(al, sg * .755, 0)); x1, y1 = t.px(u1, vat(al, sg * .715, 0)); R(d, [x0, y0, x1, y1], fill=TD)   # cuff
                for k in range(3):
                    x, yy_ = t.px(u0 + (u1 - u0) * (.3 + .2 * k), vat(al, sg * .45, 0)); d.line([(x - 4, yy_), (x + 4, yy_ + 2)], fill=TD2)
            else:
                x0, y0 = t.px(u0, vat(al, sg * spec.SLEEVE_X, 0)); x1, y1 = t.px(u1, vat(al, sg * .285, 0)); R(d, [x0, y0, x1, y1], fill=p["TEE_D"])  # sleeve hem
            # hands: finger grooves + knuckles
            hl = LOFTS["hand_" + sd]; u0, v0, u1, v1 = hl["rect"]
            vk = vat(hl, sg * .855, 0)
            for fu in (.38, .5, .62):
                for off in (0.0, 0.5):
                    uu = u0 + (u1 - u0) * ((fu + off) % 1.0); x, y0 = t.px(uu, vk); _, y1 = t.px(uu, v1 - .01)
                    d.line([(x, y0), (x, y1)], fill=(150, 104, 82))
            x0, yk = t.px(u0, vk); x1, _ = t.px(u1, vk); d.line([(x0, yk), (x1, yk)], fill=(176, 126, 98))
            # legs
            ll = LOFTS["leg_" + sd]; u0, v0, u1, v1 = ll["rect"]; outer = .75 if sd == "L" else .25
            for uu, c in ((outer, dk(JE, 1.4)), (1 - outer, dk(JE, 1.1))):
                x, y0 = t.px(u0 + (u1 - u0) * uu, v1); _, y1 = t.px(0, v0); d.line([(x, y0), (x, y1)], fill=c)
            kx, ky = t.px(u0 + (u1 - u0) * .5, vat(ll, .47)); d.ellipse([kx - 9, ky - 10, kx + 9, ky + 10], fill=dk(JE, 1.12))   # knee fade
            x0, yh = t.px(u0, vat(ll, .16)); x1, yb = t.px(u1, vat(ll, .115)); R(d, [x0, yh, x1, yb], fill=dk(JE, 1.2))            # hem roll
            _, ys = t.px(0, vat(ll, .10)); R(d, [x0, ys, x1, t.px(0, v0)[1]], fill=(60, 62, 68))                                 # shoe collar
            # shoes
            m = LOFTS["shoe_" + sd]; u0, v0, u1, v1 = m["rect"]; Wd = u1 - u0; U = lambda f: u0 + Wd * f
            for f0, f1 in ((0, .2), (.8, 1)):
                x0, y0 = t.px(U(f0), v1); x1, y1 = t.px(U(f1), v0); R(d, [x0, y0, x1, y1], fill=(120, 122, 126))   # sole band
            for f in (.22, .78):
                x0, y0 = t.px(U(f), v1); x1, y1 = t.px(U(f) + .006, v0); R(d, [x0, y0, x1, y1], fill=(236, 236, 230))
            for f in (.33, .67):
                x0, y0 = t.px(U(f) - .012, vat(m, .0, 1)); x1, y1 = t.px(U(f) + .012, vat(m, -.09, 1)); R(d, [x0, y0, x1, y1], fill=p["STRIPE"])
            xl, yl0 = t.px(U(.5), vat(m, .05, 1)); _, yl1 = t.px(U(.5), vat(m, -.07, 1))
            R(d, [xl - 4, yl0, xl + 4, yl1], fill=(196, 194, 186))
            for k in range(4):
                yy_ = yl0 + (yl1 - yl0) * (k + .5) / 4; d.line([(xl - 4, yy_), (xl + 4, yy_)], fill=(70, 70, 76))
            x0, y0 = t.px(U(.3), vat(m, -.12, 1)); x1, _ = t.px(U(.7), v1); R(d, [x0, t.px(0, v1)[1], x1, y0], fill=(200, 198, 190))
            x0, y0 = t.px(U(.25), vat(m, .085, 1)); x1, y1 = t.px(U(.75), vat(m, .06, 1)); R(d, [x0, y0, x1, y1], fill=(70, 72, 78))      # heel opening
        # neck: collar shadow
        nl = LOFTS["neck"]; u0, v0, u1, v1 = nl["rect"]; x0, y0 = t.px(u0, vat(nl, 1.535)); x1, y1 = t.px(u1, v0)
        R(d, [x0, y0, x1, y1], fill=dk(SKIN, .82))
    t.save(name, draw)


for sx in ("m", "f"): paint(sx)
