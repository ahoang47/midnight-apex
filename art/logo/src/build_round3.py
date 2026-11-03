#!/usr/bin/env python3
"""Midnight Apex logo, round 3: W2 one-line layout + S1 extruded APEX, pure black & white,
chicane M, H1 flares on the left. Reuses round-2 glyphs/helpers. Run: python3 build_round3.py"""
import os, sys
sys.path.insert(0, "/workspace/logo/round2")
import build_round2 as R
from build_round2 import Doc, word, mitre, extrude, slashes, kana, kana_width, shear_poly, K
from shapely.ops import unary_union
from shapely import affinity
from PIL import Image, ImageDraw, ImageFont
import cairosvg

OUT = os.path.dirname(os.path.abspath(__file__))
W_, B_ = "#ffffff", "#000000"
for name, ink, dark in (("wob", W_, B_), ("bow", B_, W_)):
    R.PALS[name] = dict(R.PALS["mono"]); R.PALS[name].update(
        bg1=dark, bg2=dark, ink=ink, dark=dark, gap=dark, neon=ink, extr=ink, chrome=ink, kr=ink, kw=dark, red=ink, hl=ink, sh=dark)

def combo(mode, mid="outline", ext=(14, 12), flare=260, nflare=8, kana_on=True, blade=True):
    d = Doc(mode); P = d.P
    base = 214
    w1 = word("MIDNIGHT", 0, 200, 140, k=K, mkind="chicane", s=22 if mid == "outline" else 24, mkerb=False)
    xa = w1["body"].bounds[2] + 34
    w2 = word("APEX", xa - 10, base, 178, k=K, akw=dict(tailL=30, tailR=30))
    b1, b2 = w1["body"], w2["body"]
    ex = extrude(b2, *ext) if ext else None
    a_all = unary_union([b2, ex]) if ext else b2
    # blade behind everything (white, cut out around the letters by black keylines)
    if blade:
        bl = shear_poly([(xa + 10, 150), (xa + w2["adv"] + 190, 130), (xa + w2["adv"] + 180, 150), (xa + 30, 164)], base=200)
        d.path(bl, P["ink"])
    # MIDNIGHT
    if mid == "outline":
        d.path(mitre(b1, 9), P["dark"])                     # cut the blade
        d.path(mitre(b1, 7).difference(mitre(b1, 2.5)), P["ink"])
        d.path(mitre(b1, 2.5), P["dark"])
        d.path(b1.difference(mitre(b1, -4.5)), P["ink"])
    else:
        d.path(mitre(b1, 6), P["dark"])
        d.path(b1, P["ink"])
    for n, g in w1["extras"]:     # chicane kerb: alternating stripes on the floor
        if n == "kerb_r": d.path(g, P["ink"], track=False)
        if n == "kerb_w": d.path(g, P["dark"], track=False)
    # APEX, S1 treatment in B&W: outer keyline, black ring, solid extrusion, black gap, solid face
    d.path(mitre(a_all, 12), P["ink"])
    d.path(mitre(a_all, 7), P["dark"])
    if ext:
        d.path(ex, P["ink"])
        # hard inner edge on the extrusion so it reads as depth, not a blob
    d.path(mitre(b2, 3.2), P["dark"], track=False)
    R.letters(d, w2, P["ink"])
    # H1 flares on the left
    if flare:
        top = b1.bounds[1]
        slashes(d, b1.bounds[0] - 16, top + 8, 200, nflare, flare, P["ink"], seed=5)
    if kana_on:
        kana(d, xa + 40 + (ext[0] if ext else 0) * 0.3, base + 44 + (ext[1] if ext else 0), 26, P["ink"], track=0.1)
    return d

VARIANTS = [
    ("v1", "V1  Outline MIDNIGHT + extruded APEX, blade, long flares, katakana",
     dict(mid="outline", ext=(14, 12), flare=260, kana_on=True, blade=True)),
    ("v2", "V2  Solid MIDNIGHT, medium extrude, blade, short flares, no katakana",
     dict(mid="solid", ext=(9, 8), flare=150, nflare=6, kana_on=False, blade=True)),
    ("v3", "V3  Solid MIDNIGHT, heavy extrude, no blade, long flares, katakana",
     dict(mid="solid", ext=(20, 17), flare=300, nflare=9, kana_on=True, blade=False)),
]

def build():
    rows = []
    for vid, label, kw in VARIANTS:
        od = os.path.join(OUT, f"variant_{vid}"); os.makedirs(od, exist_ok=True); files = {}
        for mode in ("wob", "bow"):
            s = combo(mode, **kw).svg(pad=36)
            p = os.path.join(od, f"{vid}_{'white_on_black' if mode == 'wob' else 'black_on_white'}")
            open(p + ".svg", "w").write(s)
            cairosvg.svg2png(bytestring=s.encode(), write_to=p + ".png")
            cairosvg.svg2png(bytestring=s.encode(), write_to=p + "_64px.png", output_height=64)
            files[mode] = p
        rows.append((vid, label, files))
    sheet(rows)

def sheet(rows):
    F = "/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-Bold.ttf"
    f1 = ImageFont.truetype(F, 52); f2 = ImageFont.truetype(F, 32); f3 = ImageFont.truetype(F, 24)
    W = 2800; pad = 30; blocks = []
    for vid, label, files in rows:
        a = Image.open(files["wob"] + ".png").convert("RGB"); b = Image.open(files["bow"] + ".png").convert("RGB")
        r = 1340 / a.width; a = a.resize((1340, int(a.height * r)), Image.LANCZOS); b = b.resize((1340, int(b.height * r)), Image.LANCZOS)
        a64 = Image.open(files["wob"] + "_64px.png").convert("RGB"); b64 = Image.open(files["bow"] + "_64px.png").convert("RGB")
        a64x = a64.resize((a64.width * 2, 128), Image.NEAREST)
        bh = 52 + a.height + 20 + 128 + 50
        blk = Image.new("RGB", (W, bh), "#808080"); dr = ImageDraw.Draw(blk)
        dr.text((pad, 8), label, font=f2, fill="#000000")
        blk.paste(a, (pad, 52)); blk.paste(b, (pad + 1380, 52))
        y = 52 + a.height + 20
        blk.paste(a64, (pad, y)); blk.paste(b64, (pad + a64.width + 20, y))
        dr.text((pad, y + 70), "actual 64px (white-on-black / black-on-white)", font=f3, fill="#000000")
        blk.paste(a64x, (pad + 1380, y)); dr.text((pad + 1380 + a64x.width + 16, y + 50), "64px x2 nearest", font=f3, fill="#000000")
        blocks.append(blk)
    H = 100 + sum(b.height + 12 for b in blocks)
    sh = Image.new("RGB", (W, H), "#5a5a5a"); dr = ImageDraw.Draw(sh)
    dr.text((pad, 22), "MIDNIGHT APEX - round 3: W2 line + S1 APEX, black & white, chicane M, H1 flares", font=f1, fill="#ffffff")
    y = 100
    for b in blocks: sh.paste(b, (0, y)); y += b.height + 12
    sh.save(os.path.join(OUT, "logo_round3_sheet.png"))
    sh.resize((1400, int(H * 1400 / W)), Image.LANCZOS).save(os.path.join(OUT, "logo_round3_sheet.jpg"), quality=90)

if __name__ == "__main__":
    build()
