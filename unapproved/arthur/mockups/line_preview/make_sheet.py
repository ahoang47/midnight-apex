#!/usr/bin/env python3
"""Labelled contact sheet of the five line-preview frames. Frames are already 1280x960
(B.5c: 3D dithered then 2x, HUD sharp on top). The sheet is judged at full size; a final
2x nearest upscale is applied to the assembled sheet for review, matching the road-test sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FRAMES = [
    ("1_entry_out_atk.png", "1  ENTRY OUT  hover ATK"),
    ("2_apex_def.png", "2  ENTRY locked OUT/ATK   APEX hover DEF"),
    ("3_apex_atk.png", "3  ENTRY locked OUT/ATK   APEX hover ATK"),
    ("4_exit_atk.png", "4  ENTRY IN/DEF   APEX NEU   EXIT hover ATK"),
    ("5_locked.png", "5  ALL THREE LOCKED"),
]
OUT = ROOT / "line_preview_sheet.png"
LABEL_H = 36
GAP = 8
BG = (8, 10, 16)
INK = (8, 8, 12)
WHITE = (220, 230, 242)
AMBER = (255, 184, 56)

def font(sz):
    for p in [
        ROOT / "godot/fonts/NimbusSans-Bold.otf",
        Path("/workspace/midnight-apex/unapproved/arthur/mockups/psx_road_test/godot/fonts/NimbusSans-Bold.otf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]:
        if p.exists():
            return ImageFont.truetype(str(p), sz)
    return ImageFont.load_default()

def main():
    tiles = []
    for name, label in FRAMES:
        im = Image.open(ROOT / name).convert("RGB")
        tiles.append((im, label))
    tw, th = tiles[0][0].size
    # 3 on the top row, 2 on the bottom, centred
    cols, rows = 3, 2
    W = cols * tw + (cols + 1) * GAP
    H = rows * (th + LABEL_H) + (rows + 1) * GAP
    sheet = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(sheet)
    f = font(22)
    # Bayer-ish label bar only, frames pasted 1:1 (already quantised)
    positions = [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1),
    ]
    # centre the last row
    for i, ((im, label), (c, r)) in enumerate(zip(tiles, positions)):
        if r == 1:
            x = (W - 2 * tw - 3 * GAP) // 2 + c * (tw + GAP) + GAP
        else:
            x = GAP + c * (tw + GAP)
        y = GAP + r * (th + LABEL_H + GAP)
        sheet.paste(im, (x, y))
        bar = Image.new("RGB", (tw, LABEL_H), (18, 22, 36))
        bd = ImageDraw.Draw(bar)
        bd.rectangle([0, 0, tw - 1, LABEL_H - 1], outline=(71, 94, 127))
        bd.text((10, 8), label, font=f, fill=AMBER)
        sheet.paste(bar, (x, y + th))
    # one 2x nearest of the whole sheet (review at full size)
    sheet = sheet.resize((sheet.size[0] * 2, sheet.size[1] * 2), Image.NEAREST)
    sheet.save(OUT, optimize=True)
    print("wrote", OUT, sheet.size)

if __name__ == "__main__":
    main()
