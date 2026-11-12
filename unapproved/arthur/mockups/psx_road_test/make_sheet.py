"""Labelled side-by-side sheet of the road test frames.
Native frames are pasted 1:1; chrome is drawn at native size with 1-bit text,
quantised once, then the whole sheet gets one 2x nearest upscale (B.5c).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5

def rgb555(a):
    h, w = a.shape[:2]
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)

FN = '/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def font(n):
    return ImageFont.truetype(FN, n)

WHITE = (220, 230, 242)
DIM = (140, 159, 180)
AMBER = (255, 184, 56)
INK = (8, 10, 16)
BG = (5, 10, 19)
EDGE = (71, 94, 127)

frames = [
    ("BEFORE (Blender, old road)", "before.png"),
    ("AFTER SMOOTH (Godot, pack road)", "after_smooth.png"),
    ("AFTER NEAREST (Godot, pack road)", "after_nearest.png"),
    ("AFTER SMOOTH + SHARP UI", "after_smooth_sharpui.png"),
    ("AFTER NEAREST + SHARP UI", "after_nearest_sharpui.png"),
]
ims = []
for title, name in frames:
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        raise SystemExit("missing " + p)
    ims.append((title, Image.open(p).convert("RGB")))

# Two rows: 3 on top (before / smooth / nearest), 2 on bottom (sharpui). Tiles are 640x480.
PAD, TAB, TITLE_H = 10, 22, 36
COLS = 3
W = PAD + COLS * (640 + PAD)
H = TITLE_H + 2 * (TAB + 480 + PAD)
sh = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(sh)
d.fontmode = "1"
d.text((PAD, 8), "PSX ROAD TEST  /  PACK ASPHALT  /  UNAPPROVED", font=font(20), fill=WHITE)
d.text((PAD + 420, 12), "3D 640x480  RGB555+Bayer  2x nearest   UI classic at 640 or sharp at 1280", font=font(12), fill=DIM)

slots = []
positions = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]
for (title, im), (c, r) in zip(ims, positions):
    x = PAD + c * (640 + PAD)
    y = TITLE_H + r * (TAB + 480 + PAD)
    tab = [(x, y), (x + 280, y), (x + 292, y + TAB), (x, y + TAB)]
    d.polygon(tab, fill=AMBER)
    d.text((x + 8, y + 4), title, font=font(13), fill=INK)
    d.line([(x + 296, y + TAB - 1), (x + 640, y + TAB - 1)], fill=EDGE)
    # Frames are already 1280x960; paste a 640x480 nearest-down copy? B.5c: paste native 1:1.
    # The deliverable frames are 1280x960. For a readable sheet, use 640-wide tiles only if we
    # also ship full-size. Task wants a labelled side-by-side sheet judged from full-size frames.
    slots.append((im, (x, y + TAB)))

# Rebuild the sheet at full frame size (1280x960 tiles) so nothing is downscaled.
PAD, TAB, TITLE_H = 12, 28, 44
TW, TH = 1280, 960
W = PAD + COLS * (TW + PAD)
H = TITLE_H + 2 * (TAB + TH + PAD)
sh = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(sh)
d.fontmode = "1"
d.text((PAD, 10), "PSX ROAD TEST  /  PACK ASPHALT  /  UNAPPROVED", font=font(28), fill=WHITE)
d.text((PAD + 620, 16), "3D 640x480, no AA, RGB555 + Bayer, 2x nearest. Classic HUD dithered at 640. Sharp UI drawn after the upscale at 1280x960.", font=font(16), fill=DIM)
slots = []
for (title, im), (c, r) in zip(ims, positions):
    x = PAD + c * (TW + PAD)
    y = TITLE_H + r * (TAB + TH + PAD)
    tab = [(x, y), (x + 520, y), (x + 536, y + TAB), (x, y + TAB)]
    d.polygon(tab, fill=AMBER)
    d.text((x + 12, y + 4), title, font=font(20), fill=INK)
    d.line([(x + 540, y + TAB - 1), (x + TW, y + TAB - 1)], fill=EDGE)
    slots.append((im, (x, y + TAB)))

q = Image.fromarray(rgb555(np.asarray(sh).astype(np.float32)))
for im, xy in slots:
    q.paste(im, xy)
out = os.path.join(HERE, "road_test_sheet.png")
q.resize((q.width * 2, q.height * 2), Image.NEAREST).save(out)
print("wrote", out, q.width * 2, q.height * 2)
