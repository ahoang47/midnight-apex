#!/usr/bin/env python3
"""Labelled contact sheets of the line-preview frames. Frames are already 1280x960
(B.5c: 3D dithered then 2x, HUD sharp on top). The sheet is judged at full size; a final
2x nearest upscale is applied to the assembled sheet for review, matching the road-test sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OVERVIEW = [
    ("1_entry_out_pow.png", "1  ENTRY OUT  hover POW"),
    ("2_apex_en.png", "2  ENTRY locked OUT/POW   APEX hover EN"),
    ("3_apex_pow.png", "3  ENTRY locked OUT/POW   APEX hover POW"),
    ("4_exit_pow.png", "4  ENTRY OUT/POW   APEX EN   EXIT hover POW"),
    ("5_locked.png", "5  ALL THREE LOCKED  OUT/POW  EN  POW"),
]
CAMSTOPS = [
    ("1_entry_out_pow_camstop.png", "1  ENTRY chase cam  OUT hover POW"),
    ("2_apex_en_camstop.png", "2  APEX stop  ENTRY OUT/POW  hover EN"),
    ("4_exit_pow_camstop.png", "4  EXIT stop  ENTRY OUT/POW  APEX EN  hover POW"),
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


VARIANTS_ENTRY = [
    ("a_entry_out_pow.png", "A  ENTRY stop  OUT hover POW  — implied Apex EN + Exit POW (dimmer)"),
]
VARIANTS_APEX = [
    ("b_apex_pow.png", "B  APEX  Entry locked OUT/POW  hover POW  — Exit POW dimmer"),
    ("b_apex_han.png", "B  APEX  Entry locked OUT/POW  hover HAN  — Exit POW dimmer"),
    ("b_apex_en.png", "B  APEX  Entry locked OUT/POW  hover EN  — Exit POW dimmer"),
]
VARIANTS_EXIT = [
    ("c_exit_pow.png", "C  EXIT  Entry OUT/POW  Apex EN locked  hover POW"),
    ("c_exit_han.png", "C  EXIT  Entry OUT/POW  Apex EN locked  hover HAN"),
    ("c_exit_en.png", "C  EXIT  Entry OUT/POW  Apex EN locked  hover EN"),
]


def build_variants_sheet():
    """Row 1: Entry A (centred). Row 2: Apex POW / HAN / EN. Row 3: Exit POW / HAN / EN."""
    rows = [VARIANTS_ENTRY, VARIANTS_APEX, VARIANTS_EXIT]
    tiles_rows = []
    for row in rows:
        tiles = []
        for name, label in row:
            path = ROOT / name
            if not path.exists():
                print("skip missing variants sheet, need", path)
                return None
            tiles.append((Image.open(path).convert("RGB"), label))
        tiles_rows.append(tiles)
    tw, th = tiles_rows[1][0][0].size
    cols = 3
    W = cols * tw + (cols + 1) * GAP
    H = 3 * (th + LABEL_H) + 4 * GAP
    sheet = Image.new("RGB", (W, H), BG)
    f = font(20)
    for r, tiles in enumerate(tiles_rows):
        n = len(tiles)
        for c, (im, label) in enumerate(tiles):
            if n < cols:
                x = (W - n * tw - (n + 1) * GAP) // 2 + c * (tw + GAP) + GAP
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
    out = ROOT / "line_preview_stance_variants.png"
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)
    return out


def main():
    build(OVERVIEW, "line_preview_sheet.png", 3, center_last_row=True)
    build(CAMSTOPS, "line_preview_camstops_sheet.png", 3, center_last_row=False)
    build_variants_sheet()


if __name__ == "__main__":
    main()
