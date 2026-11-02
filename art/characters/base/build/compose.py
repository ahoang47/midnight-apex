"""Assemble /tmp/cb renders into renders/*.png|jpg"""
import os, json
from PIL import Image, ImageDraw
SRC = "/tmp/cb"; OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "renders"); os.makedirs(OUT, exist_ok=True)
tris = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tris.json")))
SEX = {"m": "MALE", "f": "FEMALE"}
def label(d, xy, t): d.rectangle([xy[0] - 2, xy[1] - 2, xy[0] + 7 * len(t) + 4, xy[1] + 13], fill=(20, 20, 24)); d.text(xy, t, fill=(255, 220, 150))
def save2(img, name):
    img.save(os.path.join(OUT, name + ".png")); r = 800 / img.width
    img.convert("RGB").resize((800, int(img.height * r)), Image.LANCZOS).save(os.path.join(OUT, name + "_800.jpg"), quality=90)
for s in ("m", "f"):
    for shape in ("standard", "slim", "bulky"):
        im = Image.new("RGB", (1920, 670), (30, 30, 34)); d = ImageDraw.Draw(im)
        for i, v in enumerate(("front", "side", "back")):
            im.paste(Image.open(f"{SRC}/turn_{s}_{shape}_{v}.png").convert("RGB"), (i * 640, 30)); label(d, (i * 640 + 8, 8), v.upper())
        label(d, (1380, 8), f"{SEX[s]} {shape.upper()} - tee outfit + Hair_A {tris[s]['_combos']['Hair_A+outfit_tee']} tris")
        save2(im, f"turnaround_{'male' if s == 'm' else 'female'}_{shape}")
    o_t, o_a = ("outfit_tee", "outfit_hoodie") if s == "m" else ("outfit_tee", "outfit_jacket")
    im = Image.new("RGB", (960, 1300), (30, 30, 34)); d = ImageDraw.Draw(im)
    for i, h in enumerate(("Hair_A", "Hair_B")):
        for j, (o, k) in enumerate(((o_t, "tee"), (o_a, "alt"))):
            im.paste(Image.open(f"{SRC}/swap_{s}_{h}_{k}.png").convert("RGB"), (j * 480, 20 + i * 640))
            label(d, (j * 480 + 8, 24 + i * 640), f"{h} + {o}.png  ({tris[s]['_combos'][h + '+' + o]} tris)")
    label(d, (8, 2), f"{SEX[s]} swap sheet: 2 outfits (texture swap on one body mesh) x 2 hair pieces")
    im.convert("RGB").save(os.path.join(OUT, f"swap_sheet_{'male' if s == 'm' else 'female'}.jpg"), quality=90)
# builds lineup: one row, same ortho scale
im = Image.new("RGB", (560 * 6, 670), (30, 30, 34)); d = ImageDraw.Draw(im)
for i, (s, k) in enumerate([(s, k) for s in ("m", "f") for k in ("slim", "standard", "bulky")]):
    im.paste(Image.open(f"{SRC}/build_{s}_{k}.png").convert("RGB"), (i * 560, 30)); label(d, (i * 560 + 8, 8), f"{SEX[s]} {k.upper()}")
im.convert("RGB").resize((2520, 502), Image.LANCZOS).save(os.path.join(OUT, "builds_lineup.jpg"), quality=90)
# before / after (old standard front vs new)
BEF = os.environ.get("BEFORE_DIR", "")   # old renders (not in the repo)
if os.path.exists(f"{BEF}/turn_m_standard_front.png"):
    im = Image.new("RGB", (640 * 4, 670), (30, 30, 34)); d = ImageDraw.Draw(im)
    for i, (src, t) in enumerate(((f"{BEF}/turn_m_standard_front.png", "MALE before (layered clothes)"), (f"{SRC}/turn_m_standard_front.png", "MALE after (painted, tune-up)"),
                                  (f"{BEF}/turn_f_standard_front.png", "FEMALE before"), (f"{SRC}/turn_f_standard_front.png", "FEMALE after"))):
        im.paste(Image.open(src).convert("RGB"), (i * 640, 30)); label(d, (i * 640 + 8, 8), t)
    im.save(os.path.join(OUT, "tuneup_before_after.jpg"), quality=90)
# UV templates (artists paint a new outfit over these)
REG = {"torso": "TORSO (tee / jacket + jeans top)", "neck": "NECK", "arm_L": "ARM L", "arm_R": "ARM R", "hand_L": "HAND L", "hand_R": "HAND R",
       "thumb_L": "THUMB L", "thumb_R": "THUMB R", "leg_L": "LEG L (jeans)", "leg_R": "LEG R (jeans)", "shoe_L": "SHOE L", "shoe_R": "SHOE R", "addon": "ADD-ON (hood / collar)"}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import spec
for s in ("m", "f"):
    uv = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"uv_{s}.json")))
    S = 1024; base = Image.open(os.path.join(spec.TEXDIR, s, "outfit_tee.png")).convert("RGB").resize((S, S), Image.NEAREST)
    im = Image.blend(base, Image.new("RGB", (S, S), (40, 40, 44)), 0.55); d = ImageDraw.Draw(im)
    for k, r in spec.ATLAS.items():
        d.rectangle([r[0] * S, (1 - r[3]) * S, r[2] * S - 1, (1 - r[1]) * S - 1], outline=(255, 200, 80), width=2)
        label(d, (r[0] * S + 6, (1 - r[3]) * S + 6), REG[k])
    for f in uv:
        pts = [(u * S, (1 - v) * S) for u, v in f["uv"]]; d.polygon(pts, outline=(120, 230, 255))
    label(d, (8, S - 20), f"{'MALE' if s == 'm' else 'FEMALE'} outfit atlas UV template - 256 px texture (shown x4). Paint inside the yellow regions; front of each part = centre column.")
    im.save(os.path.join(OUT, f"uv_template_{s}.png"))
# deform check
cap = {"1_tpose": "rest T-pose", "2_std": "test pose: A-arms, knee bend, head turn", "3_bulky_alt": "BULKY + alt hair/top",
       "4_slim_back": "SLIM back view", "5_bulky_armpit": "BULKY armpit/hip close-up"}
im = Image.new("RGB", (480 * 5, 1300), (30, 30, 34)); d = ImageDraw.Draw(im)
for r, s in enumerate(("m", "f")):
    for c, k in enumerate(cap):
        im.paste(Image.open(f"{SRC}/def_{s}_{k}.png").convert("RGB"), (c * 480, 20 + r * 640)); label(d, (c * 480 + 8, 24 + r * 640), f"{SEX[s]}: {cap[k]}")
label(d, (8, 2), "Deformation check - action 'deform_test' frame 40 (same skeleton, same action for every body)")
im.convert("RGB").save(os.path.join(OUT, "deform_check.jpg"), quality=90)
# lineup with height marks (ortho: zc .95, scale 2.8, 1000 px)
im = Image.open(f"{SRC}/lineup.png").convert("RGB"); d = ImageDraw.Draw(im)
py = lambda z: 500 - (z - 0.95) / 2.8 * 1000
for z, t in ((tris["m"]["_height_body_hairA"], "male %.2f m" % tris["m"]["_height_body_hairA"]), (tris["f"]["_height_body_hairA"], "female %.2f m" % tris["f"]["_height_body_hairA"]), (0.0, "0 m")):
    y = py(z); d.line([(0, y), (1000, y)], fill=(255, 220, 150)); label(d, (8, y - 16), t)
label(d, (8, 8), "Lineup, same scale (ortho), A-pose frame 20")
im.save(os.path.join(OUT, "lineup_mf.jpg"), quality=90)
print(sorted(os.listdir(OUT)))
