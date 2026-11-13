#!/usr/bin/env python3
"""Contact sheet of the unapproved resource-meter concept frames."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
LABEL_H = 40
GAP = 8
BG = (8, 10, 16)
AMBER = (255, 184, 56)
DIM = (140, 159, 180)

# Filled in after the frames are judged; default assumes B is the hero for the
# state rows. make_sheet reads HERO from the environment if set (A, B or C).
HERO = Path(ROOT / "HERO").read_text().strip().upper() if (ROOT / "HERO").exists() else "B"
TAG = HERO.lower()

VARIANTS = [
    ("a_full.png", "A  VERTICAL BARS  icons + thermometer pips  — all full"),
    ("b_full.png", "B  HORIZONTAL BARS  LINE LOCK-style pips beside icons  — all full"),
    ("c_full.png", "C  COMBINED PLATE  segmented ring + short pip track  — all full"),
]
STATES = [
    (f"{TAG}_drain.png", f"{HERO}  AFTER A POW PICK  fuel drains (ghost pips)  brakes/susp full"),
    (f"{TAG}_low.png", f"{HERO}  LOW  fuel + brakes in the warning colour  FUEL LOW badge"),
    (f"{TAG}_empty.png", f"{HERO}  EMPTY  fuel gone (slash + EMPTY)  brakes low  susp mid"),
    (f"{TAG}_susp_spent.png", f"{HERO}  AFTER A HAN PICK  suspension spent  fuel still empty"),
    (f"{TAG}_susp_refill.png", f"{HERO}  NEXT TURN  suspension recovers  fuel/brakes do not"),
]


def font(sz):
    for p in [
        ROOT / "godot/fonts/NimbusSans-Bold.otf",
        Path("/workspace/midnight-apex/unapproved/arthur/mockups/line_preview/godot/fonts/NimbusSans-Bold.otf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]:
        if p.exists():
            return ImageFont.truetype(str(p), sz)
    return ImageFont.load_default()


def build(rows, out_name):
    tiles_rows = []
    for row in rows:
        tiles = []
        for name, label in row:
            path = ROOT / name
            if not path.exists():
                print("skip missing", path)
                return None
            tiles.append((Image.open(path).convert("RGB"), label))
        tiles_rows.append(tiles)
    tw, th = tiles_rows[0][0][0].size
    cols = max(len(r) for r in tiles_rows)
    W = cols * tw + (cols + 1) * GAP
    H = len(tiles_rows) * (th + LABEL_H) + (len(tiles_rows) + 1) * GAP
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
    out = ROOT / out_name
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)
    return out


D_FRAMES = [
    ("d_full.png", "D  BOTTOM LEFT  one wide plate  continuous trough bars  — all full"),
    ("d_drain.png", "D  AFTER A POW PICK  fuel drains as a freeform fill  ghost in the trough"),
    ("d_low.png", "D  LOW  fuel + brakes in the warning colour  FUEL LOW badge"),
    ("d_empty.png", "D  EMPTY  fuel gone (slash + EMPTY)  brakes low  susp mid"),
    ("d_susp_spent.png", "D  AFTER A HAN PICK  suspension spent  fuel still empty"),
    ("d_susp_refill.png", "D  NEXT TURN  suspension recovers  fuel/brakes do not"),
]

E_FRAMES = [
    ("e_full.png", "E1  BOTTOM BAND  flat HUD  HEAT/BRAKES/SUSP + LINE LOCK + PLAN  — all full"),
    ("e_drain.png", "E1  AFTER A POW PICK  HEAT headroom drains  ghost in the trough"),
    ("e_low.png", "E1  OVERHEAT  heat + brakes warning  hot tint + OVERHEAT tag"),
    ("e_empty.png", "E1  LIMP  heat empty (dark trough, no slash)  LIMP tag"),
    ("e_susp_spent.png", "E1  AFTER A HAN PICK  suspension spent  heat still limp"),
    ("e_susp_refill.png", "E1  NEXT TURN  suspension recovers  heat stays limp"),
]

COMPARE = [
    ("d_full.png", "D  BEFORE  grainy plates  meters bottom-left  LINE LOCK and PLAN on the play area"),
    ("e_full.png", "E1  AFTER  one flat bottom band  play area clear  floating turn sign"),
    ("e2_full.png", "E2  AFTER  bottom band + slim top strip for LINE LOCK and the corner name"),
]


def main():
    # Row 1: three style variants at full. Rows 2–3: state strip for the hero variant.
    if Path(ROOT / "a_full.png").exists():
        rows = [VARIANTS, STATES[:3], STATES[3:]]
        build(rows, "resource_meters_sheet.png")
    # Variant D gets its own sheet (bottom-left continuous bars).
    if Path(ROOT / "d_full.png").exists():
        build([D_FRAMES[:3], D_FRAMES[3:]], "resource_meters_d_sheet.png")
    if Path(ROOT / "e_full.png").exists():
        build([E_FRAMES[:3], E_FRAMES[3:]], "resource_meters_e_sheet.png")
    if Path(ROOT / "e_full.png").exists() and Path(ROOT / "d_full.png").exists():
        row = [c for c in COMPARE if Path(ROOT / c[0]).exists()]
        build([row], "resource_meters_d_vs_e.png")


if __name__ == "__main__":
    main()
