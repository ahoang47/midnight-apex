#!/usr/bin/env python3
"""Midnight Apex logo concepts, round 2 (hard-edged / 1999 Japanese racing-game energy).
Latin letters are hand-built polygons (glyphs.py): mitres and chamfers only, no round caps or joins.
Katakana subtext from Dela Gothic One (OFL). Run: python3 build_round2.py"""
import os, sys, io, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyphs import *
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from shapely import affinity
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import cairosvg
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
KANA = "ミッドナイト・エイペックス"
KFONT = TTFont("/usr/share/fonts/truetype/sand-box/google/Dela Gothic One/DelaGothicOne-Regular.ttf")
K = 0.30   # forward italic (about 17 degrees)

PALS = {
 "color": dict(bg1="#0c0f2e", bg2="#03040b", chrome="url(#chrome)", steel="url(#steel)", ink="#f4f7ff", dark="#05060f",
               neon="#20e3ff", neon2="#ff2d8a", extr="#2a1160", extr_edge="#6b3fd6", kr="#e3172b", kw="#f4f7ff",
               amber="#ffb03a", red="#e3172b", hl="#ffffff", sh="#0b0e2a", plate="#10142f", gap="#05060f"),
 "mono":  dict(bg1="#000000", bg2="#000000", chrome="#ffffff", steel="#ffffff", ink="#ffffff", dark="#000000",
               neon="#ffffff", neon2="#ffffff", extr="#ffffff", extr_edge="#ffffff", kr="#ffffff", kw="#000000",
               amber="#ffffff", red="#ffffff", hl="#ffffff", sh="#000000", plate="#000000", gap="#000000"),
}

# ------------------------------------------------------------------ svg helpers
def gp(g):
    if g is None or g.is_empty: return ""
    polys = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
    return " ".join("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in r.coords) + " Z"
                    for p in polys for r in [p.exterior] + list(p.interiors))

class Doc:
    def __init__(self, mode):
        self.mode = mode; self.P = PALS[mode]; self.els = []; self.defs = []; self.geoms = []
    def path(self, g, fill, track=True):
        if g is None or g.is_empty or fill in (None, "none"): return
        self.els.append(f'<path d="{gp(g)}" fill="{fill}" fill-rule="evenodd"/>')
        if track: self.geoms.append(g)
    def raw(self, s, bounds=None):
        self.els.append(s)
        if bounds: self.geoms.append(box(*bounds))
    def grad(self, gid, y0, y1, stops, x0=0, x1=0):
        st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
        self.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}">{st}</linearGradient>')
    def svg(self, pad=40, minw=0):
        b = unary_union([g.envelope for g in self.geoms]).bounds
        x0, y0, x1, y1 = b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad
        w, h = x1 - x0, y1 - y0
        bg = (f'<linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{self.P["bg1"]}"/>'
              f'<stop offset="1" stop-color="{self.P["bg2"]}"/></linearGradient>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}">'
                f'<defs>{bg}{"".join(self.defs)}</defs><rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#bgg)"/>'
                + "".join(self.els) + "</svg>")

def chrome_grad(d, gid, y0, y1):
    if d.mode == "mono": return
    # icy sky -> hard horizon -> sodium-lamp ground (1999 chrome, night version)
    d.grad(gid, y0, y1, [(0, "#ffffff"), (0.22, "#e6eeff"), (0.44, "#93a8dc"), (0.50, "#1d2456"), (0.515, "#3b2461"),
                         (0.60, "#b0487e"), (0.78, "#ffb46a"), (1, "#fff1d6")])

def steel_grad(d, gid, y0, y1):
    if d.mode == "mono": return
    d.grad(gid, y0, y1, [(0, "#dfe7f7"), (0.48, "#7d8cb3"), (0.52, "#3a4570"), (1, "#a7b5d8")])

def mitre(g, w):
    return g.buffer(w, join_style="mitre", mitre_limit=5.0)

def extrude(g, dx, dy, n=14):
    return unary_union([affinity.translate(g, dx * i / n, dy * i / n) for i in range(1, n + 1)])

def bevel(d, g, w=2.2, hl=None, sh=None):
    """hard-edged fake bevel: lit top-left edge, dark bottom-right edge (no blur)"""
    if d.mode == "mono": return
    d.path(g.difference(affinity.translate(g, w, w)), hl or d.P["hl"], track=False)
    d.path(g.difference(affinity.translate(g, -w, -w)), sh or "#1a1440", track=False)

def letters(d, w, fill, kerb=True, extras_mono_gap=True):
    d.path(w["body"], fill)
    if kerb:
        for n, g in w["extras"]:
            if n == "kerb_r": d.path(g, d.P["kr"], track=False)
            if n == "kerb_w": d.path(g, d.P["kw"], track=False)

def kana(d, x, base, size, fill, k=K, track=0.06, text=KANA):
    f = KFONT; gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    s = size / (upm * 0.88); out = []; xx = x; bp = BoundsPen(gs); minx = miny = 1e9; maxx = maxy = -1e9
    for ch in text:
        gn = cmap[ord(ch)]; pen = SVGPathPen(gs)
        tf = (s, 0, s * k, -s, xx, base)
        gs[gn].draw(TransformPen(pen, tf))
        bpn = BoundsPen(gs); gs[gn].draw(TransformPen(bpn, tf))
        if bpn.bounds:
            minx, miny = min(minx, bpn.bounds[0]), min(miny, bpn.bounds[1]); maxx, maxy = max(maxx, bpn.bounds[2]), max(maxy, bpn.bounds[3])
        out.append(pen.getCommands())
        xx += gs[gn].width * s + track * size
    d.raw(f'<path d="{" ".join(out)}" fill="{fill}"/>', (minx, miny, maxx, maxy))
    return xx - x - track * size

def kana_width(size, track=0.06, text=KANA):
    f = KFONT; gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    s = size / (upm * 0.88)
    return sum(gs[cmap[ord(c)]].width * s + track * size for c in text) - track * size

def slashes(d, xr, ytop, ybot, n, L0, fill, k=K, seed=3, left=True):
    """speed slashes: thin sheared wedges, needle-sharp at the trailing end"""
    import random; r = random.Random(seed); gs = []
    hgt = (ybot - ytop) / (n * 1.6)
    for i in range(n):
        y = ytop + i * (ybot - ytop) / n
        L = L0 * (0.45 + 0.55 * r.random()); h = hgt * (0.5 + r.random() * 0.7)
        xo = xr - (ybot - y) * k  # follow the italic
        if left:
            gs.append(Polygon([(xo - L, y + h), (xo + h * k, y), (xo, y + h)]))
        else:
            gs.append(Polygon([(xo, y + h), (xo + h * k, y), (xo + L, y)]))
    g = unary_union(gs); d.path(g, fill); return g

def star(cx, cy, r, w):
    """4-point glint, all straight edges"""
    return Polygon([(cx, cy - r), (cx + w, cy - w), (cx + r * 0.62, cy), (cx + w, cy + w), (cx, cy + r * 0.62),
                    (cx - w, cy + w), (cx - r * 0.62, cy), (cx - w, cy - w)])

def shear_poly(pts, k=K, base=0):
    return Polygon([(x + k * (base - y), y) for x, y in pts])

# ------------------------------------------------------------------ concepts
def c_w1(mode, mk="chicane"):
    """W1 Lagoon Chrome: one-line chrome wordmark, purple block extrude, cyan neon keyline, slashes, kana."""
    d = Doc(mode); P = d.P
    w = word("MIDNIGHT APEX", 0, 200, 150, k=K, mkind=mk)
    b = w["body"]; y0, y1 = b.bounds[1], b.bounds[3]
    chrome_grad(d, "chrome", y0, 200)
    ex = extrude(b, 11, 11)
    d.path(mitre(unary_union([b, ex]), 9), P["neon"])
    d.path(mitre(unary_union([b, ex]), 5), P["dark"])
    d.path(ex, P["extr"]); 
    if mode == "mono": d.path(mitre(b, 2.5), P["gap"], track=False)
    letters(d, w, P["chrome"]); bevel(d, b)
    slashes(d, b.bounds[0] - 14, y0 + 10, 200, 6, 230, P["neon"])
    kw = kana_width(30)
    x = b.bounds[2] - kw - 20
    d.path(shear_poly([(x - 260, 248), (x - 20, 248), (x - 20, 252), (x - 260, 252)], base=250), P["red"])
    kana(d, x, 262, 30, P["ink"])
    return d

def c_w2(mode, mk="skyline"):
    """W2 Split Neon: MIDNIGHT as hollow neon tube, APEX solid white-hot with a hard red shadow, red speed blade."""
    d = Doc(mode); P = d.P
    w1 = word("MIDNIGHT", 0, 200, 140, k=K, mkind=mk, s=22)
    xa = w1["body"].bounds[2] + 34
    w2 = word("APEX", xa - 10, 214, 178, k=K, akw=dict(tailL=30, tailR=30))
    b1, b2 = w1["body"], w2["body"]
    # blade behind everything
    blade = shear_poly([(-120, 150), (xa + w2["adv"] + 160, 132), (xa + w2["adv"] + 150, 150), (-60, 162)], base=200)
    d.path(blade, P["red"] if mode == "color" else P["ink"])
    if mode == "mono": d.path(mitre(unary_union([b1, b2]), 6).intersection(mitre(blade, 4)), P["gap"], track=False)
    # MIDNIGHT: neon tube (outline only), double line
    d.path(mitre(b1, 7).difference(mitre(b1, 2.5)), P["neon"])
    d.path(mitre(b1, 2.5), P["dark"])
    d.path(b1.difference(mitre(b1, -4.5)), P["neon"])
    if mk == "chicane" or mk == "skyline":
        for n, g in w1["extras"]:
            if n == "kerb_r": d.path(g, P["kr"], track=False)
    # APEX: hard offset shadow + white
    sh = affinity.translate(b2, 9, 7)
    d.path(mitre(unary_union([b2, sh]), 5), P["dark"])
    d.path(sh, P["red"] if mode == "color" else P["ink"])
    if mode == "mono": d.path(mitre(b2, 3), P["gap"], track=False)
    letters(d, w2, P["ink"])
    kana(d, xa + 40, 262, 26, P["neon"], track=0.1)
    return d

def c_s1(mode, mk="chicane"):
    """S1 Night Run stack: tracked MIDNIGHT over huge chrome APEX, kana in a cut-corner red bar."""
    d = Doc(mode); P = d.P
    wa = word("APEX", 0, 330, 230, k=K)
    ba = wa["body"]
    wm = word("MIDNIGHT", 0, 0, 62, k=K, mkind=mk, gap=16)
    # centre MIDNIGHT over APEX (account for italic: shift right by k*height difference)
    off = (ba.bounds[0] + ba.bounds[2]) / 2 - (wm["body"].bounds[0] + wm["body"].bounds[2]) / 2 + 10
    bm = affinity.translate(wm["body"], off, 330 - 230 - 26)
    wm["body"] = bm; wm["extras"] = [(n, affinity.translate(g, off, 330 - 230 - 26)) for n, g in wm["extras"]]
    chrome_grad(d, "chrome", ba.bounds[1], 330)
    ex = extrude(ba, 14, 12)
    d.path(mitre(unary_union([ba, ex]), 12), P["neon"])
    d.path(mitre(unary_union([ba, ex]), 7), P["dark"])
    d.path(ex, P["extr"])
    if mode == "mono": d.path(mitre(ba, 3), P["gap"], track=False)
    letters(d, wa, P["chrome"]); bevel(d, ba, 3)
    d.path(mitre(bm, 6), P["dark"])
    letters(d, wm, P["ink"])
    # kana bar
    x0 = ba.bounds[0] + 40; x1 = ba.bounds[2] + 10
    bar = shear_poly([(x0, 362), (x1, 362), (x1 - 0, 398), (x0 + 0, 398)], base=398)
    bar = bar.difference(Polygon([(x1 - 30, 362), (x1 + 50, 362), (x1 + 50, 380)]))  # cut corner
    d.path(bar, P["red"])
    kw = kana_width(24)
    kana(d, (x0 + x1) / 2 - kw / 2 - 6, 390, 22, P["dark"] if mode == "mono" else P["ink"])
    slashes(d, ba.bounds[0] - 10, ba.bounds[1] + 30, 330, 7, 200, P["neon"])
    return d

def c_s2(mode, mk="skyline"):
    """S2 Red Banner stack: MIDNIGHT reversed out of a sheared red banner, APEX white with cyan/black keylines and magenta shadow."""
    d = Doc(mode); P = d.P
    wa = word("APEX", 0, 330, 220, k=K)
    ba = wa["body"]
    wm = word("MIDNIGHT", 0, 0, 58, k=K, mkind=mk, gap=10)
    bx = ba.bounds[0] + 10
    by = 330 - 220 - 34
    bm = affinity.translate(wm["body"], bx, by)
    mex = [(n, affinity.translate(g, bx, by)) for n, g in wm["extras"]]
    # banner
    bb = bm.bounds
    ban = shear_poly([(bb[0] - 60, bb[1] - 16), (bb[2] + 40, bb[1] - 16), (bb[2] + 20, by + 14), (bb[0] - 80, by + 14)], base=by + 14)
    ban = ban.difference(Polygon([(bb[2] + 10, bb[1] - 17), (bb[2] + 120, bb[1] - 17), (bb[2] + 120, bb[1] + 22)]))
    d.path(mitre(ban, 5), P["dark"])
    d.path(ban, P["red"])
    if mode == "mono":
        d.path(bm, P["dark"])
    else:
        d.path(affinity.translate(bm, 4, 3), "#5a0010", track=False); d.path(bm, P["ink"])
    sh = affinity.translate(ba, 12, 10)
    d.path(mitre(unary_union([ba, sh]), 13), P["neon"])
    d.path(mitre(unary_union([ba, sh]), 8), P["dark"])
    d.path(sh, P["neon2"])
    if mode == "mono": d.path(mitre(ba, 3.5), P["gap"], track=False)
    letters(d, wa, P["ink"]); bevel(d, ba, 3, hl="#ffffff", sh="#9fb2d9")
    # slashes off the X
    slashes(d, ba.bounds[2] + 4, ba.bounds[1] + 60, 330, 5, 180, P["neon"], left=False, seed=8)
    kw = kana_width(22)
    kana(d, ba.bounds[2] - kw - 40, 386, 22, P["neon"], track=0.1)
    return d

def hexagon(cx, cy, rw, rh, k=K):
    pts = [(cx - rw, cy), (cx - rw * 0.55, cy - rh), (cx + rw * 0.55, cy - rh), (cx + rw, cy), (cx + rw * 0.55, cy + rh), (cx - rw * 0.55, cy + rh)]
    return shear_poly(pts, k=k * 0.6, base=cy)

def c_b1(mode, mk="chicane"):
    """B1 Hex Apex emblem: italic hexagon, chrome rim, the racing-line A with kerb, MIDNIGHT/APEX tab."""
    d = Doc(mode); P = d.P
    hx = hexagon(300, 300, 270, 210)
    steel_grad(d, "steel", 90, 510)
    d.path(mitre(hx, 14), P["neon"])
    d.path(mitre(hx, 9), P["dark"])
    d.path(hx, P["steel"])
    inner = mitre(hx, -12); d.path(inner, P["plate"] if mode == "color" else P["dark"])
    d.path(inner.difference(mitre(inner, -4)), P["neon"] if mode == "color" else P["ink"], track=False)
    # horizon: lower half of the plate a shade lighter, with converging road lines (hard edges)
    if mode == "color":
        d.path(inner.intersection(box(0, 330, 700, 700)), "#181d48", track=False)
    wa = word("A", 0, 0, 228, k=K * 0.8, akw=dict(tailL=26, tailR=26))
    ba = wa["body"]; cx = (ba.bounds[0] + ba.bounds[2]) / 2
    dx, dy = 300 - cx + 4, 384
    if True:  # converging road edges under the A (track running to the apex)
        road = Polygon([(118, 440), (250, 384), (262, 384), (148, 440)])
        road2 = Polygon([(482, 440), (350, 384), (338, 384), (452, 440)])
        dash = unary_union([Polygon([(296 - 3 * f, 392 + 14 * i * f), (304 + 3 * f, 392 + 14 * i * f), (305 + 4 * f, 400 + 14 * i * f), (295 - 4 * f, 400 + 14 * i * f)]) for i, f in ((0, 1), (1, 1.15), (2, 1.3))])
        d.path(unary_union([road, road2]).intersection(inner), P["neon"] if mode == "color" else P["ink"], track=False)
        d.path(dash.intersection(inner), P["amber"], track=False)
    wa["body"] = affinity.translate(ba, dx, dy); wa["extras"] = [(n, affinity.translate(g, dx, dy)) for n, g in wa["extras"]]
    chrome_grad(d, "chrome", wa["body"].bounds[1], wa["body"].bounds[3])
    ex = extrude(wa["body"], 10, 9)
    d.path(mitre(unary_union([wa["body"], ex]), 6), P["dark"], track=False)
    d.path(ex, P["extr"], track=False)
    if mode == "mono": d.path(mitre(wa["body"], 3), P["gap"], track=False)
    letters(d, wa, P["chrome"]); bevel(d, wa["body"], 2.5)
    # name tab across the bottom edge
    wm = word("MIDNIGHT APEX", 0, 0, 34, k=K, mkind=mk, s=26, t=21, gap=8, space=20, akw=dict(tailL=0, tailR=0, kerb=False))
    bm = wm["body"]; tw = bm.bounds[2] - bm.bounds[0]
    tdx = 300 - (bm.bounds[0] + bm.bounds[2]) / 2 + 6; tdy = 488
    tab = shear_poly([(300 - tw / 2 - 40, 446), (300 + tw / 2 + 30, 446), (300 + tw / 2 + 30, 498), (300 - tw / 2 - 40, 498)], base=498)
    tab = tab.difference(Polygon([(300 + tw / 2 + 10, 499), (300 + tw / 2 + 80, 499), (300 + tw / 2 + 80, 470)]))
    d.path(mitre(tab, 6), P["dark"]); d.path(tab, P["red"])
    d.path(affinity.translate(bm, tdx, tdy - 1), P["dark"] if mode == "mono" else P["ink"])
    return d

def c_b2(mode, mk="skyline"):
    """B2 Night Plate: cut-corner race plate, MA monogram (skyline M + racing-line A), kerb stripe, kana."""
    d = Doc(mode); P = d.P
    pl = shear_poly([(0, 0), (720, 0), (720, 340), (0, 340)], k=K * 0.5, base=340)
    pl = pl.difference(Polygon([(-200, -1), (60, -1), (-200, 160)])).difference(Polygon([(1000, 341), (640, 341), (1000, 120)]))
    pl = pl.intersection(shear_poly([(0, 0), (720, 0), (720, 340), (0, 340)], k=K * 0.5, base=340))
    pl = Polygon([(x, y) for x, y in pl.exterior.coords])
    # recompute clean chamfered plate
    pts = [(70, 0), (720, 0), (720, 250), (630, 340), (0, 340), (0, 90)]
    pl = shear_poly(pts, k=K * 0.5, base=340)
    steel_grad(d, "steel", 0, 340)
    d.path(mitre(pl, 13), P["neon"]); d.path(mitre(pl, 8), P["dark"]); d.path(pl, P["steel"])
    inner = mitre(pl, -11); d.path(inner, P["plate"] if mode == "color" else P["dark"])
    # kerb stripe along the bottom of the plate
    kb = inner.intersection(box(-100, 284, 900, 304))
    segs = [kb.intersection(shear_poly([(i * 34, 284), (i * 34 + 34, 284), (i * 34 + 34, 304), (i * 34, 304)], k=0.9, base=304)) for i in range(-2, 26)]
    d.path(unary_union(segs[0::2]), P["kr"], track=False); d.path(unary_union(segs[1::2]), P["kw"], track=False)
    w = word("MA", 0, 0, 200, k=K, mkind=mk, gap=-4, akw=dict(tailL=30, tailR=40))
    b = w["body"]; cx = (b.bounds[0] + b.bounds[2]) / 2
    dx, dy = 360 - cx + 60, 252
    w["body"] = affinity.translate(b, dx, dy); w["extras"] = [(n, affinity.translate(g, dx, dy)) for n, g in w["extras"]]
    chrome_grad(d, "chrome", w["body"].bounds[1], 252)
    ex = extrude(w["body"], 9, 8)
    d.path(mitre(unary_union([w["body"], ex]), 5), P["dark"], track=False)
    d.path(ex, P["extr"], track=False)
    if mode == "mono": d.path(mitre(w["body"], 2.5), P["gap"], track=False)
    letters(d, w, P["chrome"]); bevel(d, w["body"], 2.5)
    kw = kana_width(19, track=0.12)
    kana(d, 360 - kw / 2 + 4, 330, 19, P["neon"], track=0.12)
    return d

def c_h1(mode, mk="chicane"):
    """H1 Chrome Hero: full stacked chrome, double keyline, heavy extrude, glint on the apex, horizon rule, kana plate."""
    d = Doc(mode); P = d.P
    wm = word("MIDNIGHT", 0, 0, 120, k=K, mkind=mk, gap=9)
    wa = word("APEX", 0, 0, 280, k=K, akw=dict(tailL=40, tailR=40))
    bm0, ba0 = wm["body"], wa["body"]
    # right-align MIDNIGHT's right edge with the A's apex column for a tight interlock
    ax = (ba0.bounds[0] + ba0.bounds[2]) / 2
    mdx = ba0.bounds[0] + 30 - bm0.bounds[0] - 110
    def mv(wd, dx, dy):
        wd["body"] = affinity.translate(wd["body"], dx, dy); wd["extras"] = [(n, affinity.translate(g, dx, dy)) for n, g in wd["extras"]]
        if wd.get("apex"): wd["apex"] = (wd["apex"][0] + dx, wd["apex"][1] + dy)
    mv(wm, mdx, 150); mv(wa, 0, 470)
    bm, ba = wm["body"], wa["body"]
    chrome_grad(d, "chrome", ba.bounds[1], 470)
    if mode == "color":
        d.grad("chrome2", bm.bounds[1], 150, [(0, "#ffffff"), (0.45, "#b8c6ea"), (0.5, "#2a2f66"), (0.56, "#7a4a9a"), (1, "#ffd9a8")])
    exa = extrude(ba, 18, 16); exm = extrude(bm, 9, 8)
    allg = unary_union([ba, exa, bm, exm])
    d.path(mitre(allg, 20), P["dark"])
    d.path(mitre(allg, 15), P["neon"])
    d.path(mitre(allg, 9), P["dark"])
    d.path(exa, P["extr"]); d.path(exm, P["extr"])
    if mode == "color":
        d.path(exa.difference(affinity.translate(exa, -3, -3)), "#120530", track=False)
    if mode == "mono": d.path(mitre(ba, 3.5), P["gap"], track=False); d.path(mitre(bm, 2.5), P["gap"], track=False)
    letters(d, wa, P["chrome"]); bevel(d, ba, 3.5)
    letters(d, wm, "url(#chrome2)" if mode == "color" else P["ink"]); bevel(d, bm, 2)
    # glint on the apex of the A
    ap = wa["apex"]
    if ap:
        d.path(star(ap[0] + 3, ap[1] + 4, 58, 5), P["hl"], track=False)
        d.path(star(ap[0] + 3, ap[1] + 4, 22, 3), P["neon"] if mode == 'color' else P['dark'], track=False)
    # horizon rule + kana
    yb = 470 + 46
    x0 = ba.bounds[0] - 60; x1 = ba.bounds[2] + 40
    rule = shear_poly([(x0, yb), (x1, yb - 6), (x1, yb), (x0 + 40, yb + 4)], base=yb)
    d.path(rule, P["neon"])
    kw = kana_width(30, track=0.08)
    kpl = shear_poly([(x1 - kw - 70, yb + 12), (x1 - 10, yb + 12), (x1 - 30, yb + 52), (x1 - kw - 90, yb + 52)], base=yb + 52)
    d.path(kpl, P["red"])
    kana(d, x1 - kw - 54, yb + 46, 30, P["dark"] if mode == "mono" else P["ink"], track=0.08)
    slashes(d, ba.bounds[0] - 20, ba.bounds[1] + 70, 470, 8, 260, P["neon"], seed=5)
    return d

CONCEPTS = [
    ("w1", "W1  Lagoon Chrome - one-line chrome wordmark", c_w1, "chicane", "skyline"),
    ("w2", "W2  Split Neon - hollow neon MIDNIGHT + white-hot APEX", c_w2, "skyline", "chicane"),
    ("s1", "S1  Night Run - stacked, chrome APEX, kana bar", c_s1, "chicane", "skyline"),
    ("s2", "S2  Red Banner - stacked, banner MIDNIGHT", c_s2, "skyline", "chicane"),
    ("b1", "B1  Hex Apex - hexagon emblem", c_b1, "chicane", "skyline"),
    ("b2", "B2  Night Plate - cut-corner plate, MA monogram", c_b2, "skyline", "chicane"),
    ("h1", "H1  Chrome Hero - full chrome key art lockup", c_h1, "chicane", "skyline"),
]

def render(svg, path_png, width=None, height=None):
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path_png, output_width=width, output_height=height)

def build():
    rows = []
    for cid, label, fn, mk, alt in CONCEPTS:
        od = os.path.join(OUT, f"concept_{cid}"); os.makedirs(od, exist_ok=True)
        files = {}
        for tag, mode, m in (("color", "color", mk), ("mono", "mono", mk), ("color_alt_m", "color", alt)):
            s = fn(mode, m).svg()
            p = os.path.join(od, f"{cid}_{tag}")
            open(p + ".svg", "w").write(s)
            render(s, p + ".png")
            files[tag] = p + ".png"
        s = fn("color", mk).svg()
        render(s, os.path.join(od, f"{cid}_64px.png"), height=64)
        files["64"] = os.path.join(od, f"{cid}_64px.png")
        sm = fn("mono", mk).svg()
        render(sm, os.path.join(od, f"{cid}_mono_64px.png"), height=64)
        files["m64"] = os.path.join(od, f"{cid}_mono_64px.png")
        rows.append((cid, label, mk, alt, files))
    sheet(rows)

def sheet(rows):
    W = 2800; pad = 30
    F = "/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-Bold.ttf"
    f1 = ImageFont.truetype(F, 52); f2 = ImageFont.truetype(F, 30); f3 = ImageFont.truetype(F, 24)
    blocks = []
    for cid, label, mk, alt, files in rows:
        col = Image.open(files["color"]).convert("RGB"); mono = Image.open(files["mono"]).convert("RGB")
        altm = Image.open(files["color_alt_m"]).convert("RGB")
        s64 = Image.open(files["64"]).convert("RGB"); m64 = Image.open(files["m64"]).convert("RGB")
        hmax = 380
        def fit(im, maxw, maxh):
            r = min(maxw / im.width, maxh / im.height); return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        col = fit(col, 1000, hmax); mono = fit(mono, 760, hmax * 0.8); altm = fit(altm, 560, hmax * 0.6)
        s64x3 = s64.resize((s64.width * 3, s64.height * 3), Image.NEAREST)
        if s64x3.width > 600: s64x3 = fit(s64x3, 600, 192)
        bh = max(col.height, mono.height, altm.height + 70 + s64.height + 10 + m64.height) + 70
        blk = Image.new("RGB", (W, bh), "#15171f"); dr = ImageDraw.Draw(blk)
        dr.text((pad, 8), label, font=f2, fill="#ffffff")
        dr.text((pad + 1120, 8), f"M: {mk}   |   alt M: {alt}  ->", font=f3, fill="#9aa3b8")
        y = 52; blk.paste(col, (pad, y)); blk.paste(mono, (pad + 1040, y))
        xr = pad + 1040 + mono.width + 40
        blk.paste(altm, (xr, y)); dr.text((xr, y + altm.height + 4), "alt M", font=f3, fill="#9aa3b8")
        yy = y + altm.height + 40
        blk.paste(s64, (xr, yy)); blk.paste(m64, (xr + s64.width + 16, yy))
        dr.text((xr, yy + 66), "actual 64px (colour / mono)", font=f3, fill="#9aa3b8")
        blocks.append(blk)
    H = 110 + sum(b.height + 14 for b in blocks)
    sh = Image.new("RGB", (W, H), "#0c0d12"); dr = ImageDraw.Draw(sh)
    dr.text((pad, 24), "MIDNIGHT APEX - logo concepts, round 2 (hard-edged)", font=f1, fill="#ffffff")
    dr.text((pad + 1400, 44), "each row: colour  |  mono  |  alt-M colour  +  actual 64px checks", font=f3, fill="#9aa3b8")
    y = 110
    for b in blocks:
        sh.paste(b, (0, y)); y += b.height + 14
    sh.save(os.path.join(OUT, "logo_round2_sheet.png"))
    r = 1400 / W
    sh.resize((1400, int(H * r)), Image.LANCZOS).save(os.path.join(OUT, "logo_round2_sheet.jpg"), quality=90)

if __name__ == "__main__":
    build()
