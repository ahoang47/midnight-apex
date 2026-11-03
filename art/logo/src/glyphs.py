"""Midnight Apex round 2: hand-built angular letterforms (no fonts for Latin).
Units: cap height 100, y up, baseline 0. Every corner is a miter or a chamfer; nothing is round."""
import math
from shapely.geometry import Polygon, LineString, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

MJ = dict(join_style="mitre", mitre_limit=6.0)
H = 100.0

def cbox(x0, y0, x1, y1, tl=0, tr=0, br=0, bl=0):
    """box with chamfered corners (straight 45deg cuts)"""
    pts = []
    pts += [(x0, y0 + bl), (x0, y1 - tl)] if True else []
    pts = [(x0 + bl, y0), (x1 - br, y0), (x1, y0 + br), (x1, y1 - tr), (x1 - tr, y1),
           (x0 + tl, y1), (x0, y1 - tl), (x0, y0 + bl)]
    return Polygon(pts)

def stroke(pts, w, cap="flat"):
    return LineString(pts).buffer(w / 2, cap_style=cap, **MJ)

def clipbox(g, x0, y0, x1, y1):
    return g.intersection(box(x0, y0, x1, y1))

class Glyph:
    def __init__(self, body, adv, extras=None):
        self.body = body; self.adv = adv; self.extras = extras or {}

# ---- standard letters --------------------------------------------------------
def g_I(s, t, c):
    return Glyph(box(0, 0, s, H), s)

def g_E(s, t, c, W=60):
    b = unary_union([box(0, 0, s, H), box(0, H - t, W, H), box(0, 50 - t / 2, W - 8, 50 + t / 2), box(0, 0, W, t)])
    return Glyph(b.intersection(cbox(0, 0, W, H, tl=c, bl=c * 0.6)), W)

def g_T(s, t, c, W=68):
    b = unary_union([box(0, H - t, W, H), box(W / 2 - s / 2, 0, W / 2 + s / 2, H)])
    return Glyph(b.intersection(cbox(0, 0, W, H, tl=c * 0.6, tr=0)), W)

def g_H(s, t, c, W=70):
    b = unary_union([box(0, 0, s, H), box(W - s, 0, W, H), box(0, 50 - t / 2, W, 50 + t / 2)])
    return Glyph(b.intersection(cbox(0, 0, W, H, tl=c * 0.6, br=c * 0.6)), W)

def g_N(s, t, c, W=72):
    d = Polygon([(0, H), (s + 6, H), (W, 0), (W - s - 6, 0)])
    b = unary_union([box(0, 0, s, H), box(W - s, 0, W, H), d]).intersection(box(0, 0, W, H))
    return Glyph(b.intersection(cbox(0, 0, W, H, tl=c * 0.6, br=c * 0.6)), W)

def g_D(s, t, c, W=72):
    o = cbox(0, 0, W, H, tl=c * 0.4, tr=c * 2.0, br=c * 2.0, bl=c * 0.4)
    i = cbox(s, t, W - s, H - t, tr=c * 1.3, br=c * 1.3)
    return Glyph(o.difference(i), W)

def g_G(s, t, c, W=72):
    o = cbox(0, 0, W, H, tl=c * 1.6, tr=c * 0.8, br=c * 1.6, bl=c * 0.8)
    i = cbox(s, t, W - s, H - t, tl=c * 0.9, br=c * 0.9)
    ring = o.difference(i).difference(box(W - s - 1, 50, W + 1, H - t))
    bar = box(W * 0.46, 50 - t, W, 50)
    return Glyph(unary_union([ring, bar]).intersection(o), W)

def g_P(s, t, c, W=68):
    top = 40
    o = cbox(0, top - t, W, H, tl=c * 0.5, tr=c * 1.6, br=c * 1.0)
    i = cbox(s, top, W - s, H - t, tr=c * 0.9, br=c * 0.4)
    b = unary_union([o.difference(i), box(0, 0, s, H)])
    return Glyph(b.intersection(cbox(0, 0, W, H, tl=c * 0.5, bl=0)), W)

def g_X(s, t, c, W=78):
    sw = s * 1.12
    a = Polygon([(0, 0), (sw, 0), (W, H), (W - sw, H)])
    b = Polygon([(W - sw, 0), (W, 0), (sw, H), (0, H)])
    return Glyph(unary_union([a, b]), W)

# ---- M variants --------------------------------------------------------------
def g_M(s, t, c, W=96, kind="plain"):
    """M = full box minus a top notch minus a lower counter (all straight cuts)."""
    ex = {}
    full = cbox(0, 0, W, H, bl=c * 0.5, br=c * 0.5)
    if kind == "chicane":
        fy = 56                       # top of the chicane floor
        notch = Polygon([(s + 3, H + 1), (W - s - 3, H + 1), (W * 0.62, fy), (W * 0.38, fy)])
        cnt = Polygon([(s, -1), (W - s, -1), (W - s, H - 40), (W * 0.62 - 10, fy - t), (W * 0.38 + 10, fy - t), (s, H - 40)])
        b = full.difference(notch).difference(cnt)
        # red/white kerb laid on top of the chicane floor
        band = notch.intersection(box(0, fy, W, fy + 7))
        n = 5; x0, x1 = W * 0.38 - 4, W * 0.62 + 4; ws = (x1 - x0) / n
        segs = [band.intersection(Polygon([(x0 + i * ws, fy - 1), (x0 + (i + 1) * ws, fy - 1), (x0 + (i + 1) * ws + 3, fy + 9), (x0 + i * ws + 3, fy + 9)])) for i in range(n)]
        ex["kerb_r"] = unary_union(segs[0::2]); ex["kerb_w"] = unary_union(segs[1::2])
        ex["kerb_band"] = band
    else:
        vy = 40
        notch = Polygon([(s + 3, H + 1), (W - s - 3, H + 1), (W / 2, vy)])
        cnt = Polygon([(s, -1), (W - s, -1), (W - s, H - 42), (W / 2, vy - 30), (s, H - 42)])
        b = full.difference(notch).difference(cnt)
        if kind == "skyline":
            # stair-step the notch + counter edges into rooftops, spire on the left tower, mast on the right
            cols = []; n = 7; cw = (W - 2 * s) / n
            body = box(s, 0, W - s, H).intersection(b)
            stepped = []
            for k in range(n):
                xa, xb = s + k * cw, s + (k + 1) * cw
                seg = body.intersection(box(xa + cw / 2 - .01, -5, xa + cw / 2 + .01, H + 5))
                if seg.is_empty: continue
                y0, y1 = seg.bounds[1], seg.bounds[3]
                y0 = math.floor(y0 / 5) * 5; y1 = math.ceil(y1 / 5) * 5
                stepped.append(box(xa - .05, y0, xb + .05, min(y1, H)))
            b = unary_union([box(0, 0, s, H), box(W - s, 0, W, H)] + stepped)
            b = unary_union([b, box(s * 0.2, H, s * 0.8, H + 7), Polygon([(s * 0.34, H + 7), (s * 0.66, H + 7), (s * 0.5, H + 24)]),
                             box(W - s * 0.75, H, W - s * 0.2, H + 5), box(W - s * 0.5 - 1, H + 5, W - s * 0.5 + 1, H + 13)])
            wins = [box(s * 0.5 - 2.6, y, s * 0.5 + 2.6, y + 7) for y in (78, 64, 50, 36, 22)]
            wins += [box(W - s * 0.5 - 2.6, y, W - s * 0.5 + 2.6, y + 7) for y in (82, 68, 54, 26)]
            b = b.difference(unary_union(wins))
    return Glyph(b, W, ex)

# ---- the A: an out-in-out racing line ---------------------------------------
def g_A(s, t, c, W=118, kerb=True, tailL=30, tailR=30, apex_y=88, line=False):
    """The A is the line through a hairpin, drawn with straight segments:
    wide entry (tail runs in flat from the far left) -> hard turn-in kink at the foot -> pointed apex
    (kerb clipped on the inside of the peak) -> hard kink -> wide exit (tail runs out flat to the right)."""
    sw = s * 1.02
    P = [(8, -12), (W * 0.5, apex_y), (W - 8, -12)]
    body = clipbox(stroke(P, sw), -10, 0, W + 10, H + 40)
    hull = Polygon([(P[0][0], -12), P[1], (P[2][0], -12)]).buffer(sw / 2, **MJ)
    bar = box(0, 24, W, 24 + t * 0.9).intersection(hull)
    fl = body.intersection(box(-50, 0, W + 50, 0.5)).bounds  # foot extents
    parts = [body, bar]
    th = t * 0.95
    if tailL:   # entry: a flat run-in wedge, sharp point at the far end, mitred into the leg
        parts.append(Polygon([(-tailL, 0), (fl[0] + sw * 0.9, 0), (fl[0] + sw * 0.9 + th * 0.0, th), (fl[0] + th * 0.25, th)]))
    if tailR:   # exit: same, mirrored, can be stretched into an underline
        parts.append(Polygon([(fl[2] - sw * 0.9, 0), (W + tailR, 0), (fl[2] - th * 0.25, th), (fl[2] - sw * 0.9, th)]))
    b = unary_union(parts).intersection(box(-tailL - 1, 0, W + tailR + 1, H + 40))
    ex = {}
    holes = [Polygon(r) for poly in (b.geoms if hasattr(b, "geoms") else [b]) for r in poly.interiors]
    if holes and kerb:
        cnt = max(holes, key=lambda p: p.area)
        top = cnt.bounds[3]
        band = cnt.difference(cnt.buffer(-kerb_w(s), **MJ)).intersection(box(-50, top - 34, W + 50, top + 5))
        st = 5.6
        rs = [box(-50, top - (k + 1) * st, W + 50, top - k * st) for k in range(8)]
        ex["kerb_r"] = unary_union([band.intersection(r) for i, r in enumerate(rs) if i % 2 == 0])
        ex["kerb_w"] = unary_union([band.intersection(r) for i, r in enumerate(rs) if i % 2 == 1])
    ex["apex_pt"] = (W * 0.5, b.bounds[3])
    return Glyph(b, W, ex)

def kerb_w(s):
    return s * 0.30

LETTERS = dict(I=g_I, E=g_E, T=g_T, H=g_H, N=g_N, D=g_D, G=g_G, P=g_P, X=g_X)

def word(text, x0, base, size, k=0.28, s=24, t=19, c=12, gap=7, mkind="chicane", akw=None, space=26, mkerb=None):
    """lay out a word -> dict(body=union, extras=[(name, geom)], adv, apex)"""
    S = size / H
    x = 0.0; bodies = []; extras = []; apex = None; glyphs = []
    prev = None; chars = []
    akw_kern = (akw or {}).get("kern", 16)
    akw = {k_: v for k_, v in (akw or {}).items() if k_ != "kern"}
    for ch in text:
        if ch == " ":
            x += space; prev = ch; continue
        if ch == "M": g = g_M(s, t, c, kind=mkind)
        elif ch == "A":
            g = g_A(s, t, c, **(akw or {}))
            x += max(0, (akw or {}).get("tailL", 30) - (space if prev == " " else 0) - 2)
        else: g = LETTERS[ch](s, t, c)
        tf = [S, S * k, 0, -S, x0 + S * x, base]
        bodies.append(affinity.affine_transform(g.body, tf))
        for kname, gg in g.extras.items():
            if kname == "apex_pt":
                px, py = gg; apex = (x0 + S * (x + px + k * py), base - S * py)
            elif ch == "M" and not (mkerb if mkerb is not None else size >= 100):
                continue
            elif kname != "counter":
                extras.append((kname, affinity.affine_transform(gg, tf)))
        x += g.adv + gap - (akw_kern if ch == "A" else 0)
        chars.append(ch)
        prev = ch
    # the A's run-off tails slide under their neighbours with a hard keyline gap (interlock, no collision)
    for i, ch in enumerate(chars):
        if ch == "A":
            nb = [bodies[j] for j in (i - 1, i + 1) if 0 <= j < len(bodies)]
            if nb:
                bodies[i] = bodies[i].difference(unary_union(nb).buffer(4.5 * S, join_style="mitre", mitre_limit=5))
    return dict(body=unary_union(bodies), extras=extras, adv=S * (x - gap), apex=apex, S=S)
