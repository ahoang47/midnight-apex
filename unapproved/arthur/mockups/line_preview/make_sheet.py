#!/usr/bin/env python3
"""Labelled contact sheets of the line-preview frames. Frames are already 1280x960
(B.5c: 3D dithered then 2x, HUD sharp on top). The sheet is judged at full size; a final
2x nearest upscale is applied to the assembled sheet for review, matching the road-test sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OVERVIEW = [
    ("1_entry_out_atk.png", "1  ENTRY OUT  hover ATK"),
    ("2_apex_def.png", "2  ENTRY locked OUT/ATK   APEX hover DEF"),
    ("3_apex_atk.png", "3  ENTRY locked OUT/ATK   APEX hover ATK"),
    ("4_exit_atk.png", "4  ENTRY IN/DEF   APEX NEU   EXIT hover ATK"),
    ("5_locked.png", "5  ALL THREE LOCKED"),
]
CAMSTOPS = [
    ("1_entry_out_atk_camstop.png", "1  ENTRY chase cam  OUT hover ATK"),
    ("2_apex_def_camstop.png", "2  APEX stop  ENTRY OUT/ATK  hover DEF"),
    ("4_exit_atk_camstop.png", "4  EXIT stop  IN/DEF  NEU  hover ATK"),
]
LABEL_H = 36
GAP = 8
BG = (8, 10, 16)
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


def build(frames, out_name, cols, center_last_row=False):
    tiles = []
    for name, label in frames:
        path = ROOT / name
        if not path.exists():
            print("skip missing", path)
            return None
        tiles.append((Image.open(path).convert("RGB"), label))
    tw, th = tiles[0][0].size
    rows = (len(tiles) + cols - 1) // cols
    W = cols * tw + (cols + 1) * GAP
    H = rows * (th + LABEL_H) + (rows + 1) * GAP
    sheet = Image.new("RGB", (W, H), BG)
    f = font(22)
    last_row = rows - 1
    last_row_n = len(tiles) - last_row * cols
    for i, (im, label) in enumerate(tiles):
        r, c = divmod(i, cols)
        if center_last_row and r == last_row and last_row_n < cols:
            x = (W - last_row_n * tw - (last_row_n + 1) * GAP) // 2 + c * (tw + GAP) + GAP
        else:
            x = GAP + c * (tw + GAP)
        y = GAP + r * (th + LABEL_H + GAP)
        sheet.paste(im, (x, y))
        bar = Image.new("RGB", (tw, LABEL_H), (18, 22, 36))
        bd = ImageDraw.Draw(bar)
        bd.rectangle([0, 0, tw - 1, LABEL_H - 1], outline=(71, 94, 127))
        bd.text((10, 8), label, font=f, fill=AMBER)
        sheet.paste(bar, (x, y + th))
    sheet = sheet.resize((sheet.size[0] * 2, sheet.size[1] * 2), Image.NEAREST)
    out = ROOT / out_name
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)
    return out


def main():
    build(OVERVIEW, "line_preview_sheet.png", 3, center_last_row=True)
    build(CAMSTOPS, "line_preview_camstops_sheet.png", 3, center_last_row=False)


if __name__ == "__main__":
    main()
