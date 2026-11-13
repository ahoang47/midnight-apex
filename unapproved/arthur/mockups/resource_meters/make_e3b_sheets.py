#!/usr/bin/env python3
"""Icon sheet and E3B state-model contact sheet (concept only, not in the sim)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = (8, 10, 16)
PANEL = (10, 14, 36)
AMBER = (255, 184, 56)
DIM = (140, 159, 180)
EDGE = (71, 94, 127)
WHITE = (220, 230, 242)
INK = (8, 10, 16)


def font(sz):
    for p in [
        ROOT / "godot/fonts/NimbusSans-Bold.otf",
        Path("/workspace/midnight-apex/unapproved/arthur/mockups/line_preview/godot/fonts/NimbusSans-Bold.otf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]:
        if p.exists():
            return ImageFont.truetype(str(p), sz)
    return ImageFont.load_default()


def label_bar(draw, box, text, f, fill=AMBER):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill=(18, 22, 36), outline=EDGE)
    draw.text((x0 + 10, y0 + 6), text, font=f, fill=fill)


def icons_sheet():
    # In-band (as drawn in 640-space, shown also at 2x nearest = HUD pixels)
    # plus 64 and 128 review sizes, on the dark panel colour.
    cells = [
        ("POW  coolant  (unchanged)", "icon_pow_coolant_20.png", "icon_pow_coolant_64_panel.png", "icon_pow_coolant_128_panel.png"),
        ("EN  brake rotor + caliper  (no wheel)", "icon_en_brake_20.png", "icon_en_brake_64_panel.png", "icon_en_brake_128_panel.png"),
        ("HAN  vertical coilover", "icon_han_shock_22.png", "icon_han_shock_64_panel.png", "icon_han_shock_128_panel.png"),
    ]
    missing = [c[i] for c in cells for i in (1, 2, 3) if not (ROOT / c[i]).exists()]
    if missing:
        print("icons_sheet skip, missing", missing)
        return
    pad = 16
    label_h = 36
    # Column widths: in-band 24, 2x 48, 64, 128
    col_w = [80, 96, 96, 160]
    headers = ["IN-BAND", "HUD 2x", "64 px", "128 px"]
    row_h = 128 + label_h
    name_w = 360
    W = pad * 2 + name_w + sum(col_w) + pad * 4
    H = pad * 2 + 40 + 3 * (row_h + pad)
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    f = font(18)
    f2 = font(14)
    d.text((pad, pad), "E3B HUD ICONS  concept only, not in the sim", font=f, fill=AMBER)
    x = pad + name_w
    for w, h in zip(col_w, headers):
        d.text((x, pad + 22), h, font=f2, fill=DIM)
        x += w + pad
    y = pad + 40
    for title, p20, p64, p128 in cells:
        d.rectangle([pad, y, pad + name_w - 8, y + row_h], fill=(18, 22, 36), outline=EDGE)
        d.text((pad + 12, y + 16), title, font=f, fill=WHITE)
        im20 = Image.open(ROOT / p20).convert("RGB")
        im64 = Image.open(ROOT / p64).convert("RGB")
        im128 = Image.open(ROOT / p128).convert("RGB")
        im40 = im20.resize((im20.size[0] * 2, im20.size[1] * 2), Image.NEAREST)
        icons = [im20, im40, im64, im128]
        x = pad + name_w
        for w, im in zip(col_w, icons):
            # panel well
            well = Image.new("RGB", (w - 4, row_h - 8), PANEL)
            wd = ImageDraw.Draw(well)
            wd.rectangle([0, 0, well.size[0] - 1, well.size[1] - 1], outline=EDGE)
            ix = (well.size[0] - im.size[0]) // 2
            iy = (well.size[1] - im.size[1]) // 2
            well.paste(im, (ix, iy))
            sheet.paste(well, (x, y + 4))
            x += w + pad
        y += row_h + pad
    out = ROOT / "icons_e3_sheet.png"
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)


def states_sheet():
    frames = [
        ("e3b_state_cool.png", "COOL  low fill, under LIMIT, stat colour"),
        ("e3b_state_mid.png", "MID  normal fill, still under LIMIT"),
        ("e3b_state_overrun.png", "OVERRUN  past LIMIT, orange fill, orange POW chip as the penalty badge"),
        ("e3b_state_locked.png", "LOCKED  full bar, padlock, POW chip struck / unavailable"),
        ("e3b_state_cooling.png", "LOCKED, COOLING  hatch fill, still locked until RELEASE"),
        ("e3b_state_unlocked.png", "UNLOCKED  just under RELEASE, POW selectable again"),
    ]
    missing = [n for n, _ in frames if not (ROOT / n).exists()]
    if missing:
        print("states_sheet skip, missing", missing)
        return
    # Crop the bottom HUD band (640-space y=408..479 → 1280-space 816..958).
    # One column, full 1280 width, so the meters, marks and plan chips stay readable.
    crops = []
    for name, label in frames:
        im = Image.open(ROOT / name).convert("RGB")
        crop = im.crop((0, 800, 1280, 960))
        crops.append((crop, label))
    tw, th = 1280, 160
    gap = 10
    label_h = 36
    W = tw + gap * 2
    H = 48 + len(crops) * (th + label_h + gap) + gap
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    f = font(20)
    f2 = font(16)
    d.text((gap, 10), "E3B  POW heat bar through the state model", font=f, fill=AMBER)
    d.text((gap, 30), "LIMIT = amber cap at ~80%     RELEASE = blue triangle at ~55%     concept only, numbers not approved", font=f2, fill=DIM)
    for i, (im, label) in enumerate(crops):
        x = gap
        y = 48 + gap + i * (th + label_h + gap)
        sheet.paste(im if im.size == (tw, th) else im.resize((tw, th), Image.NEAREST), (x, y))
        bar = Image.new("RGB", (tw, label_h), (18, 22, 36))
        bd = ImageDraw.Draw(bar)
        bd.rectangle([0, 0, tw - 1, label_h - 1], outline=EDGE)
        bd.text((10, 6), label, font=f, fill=AMBER)
        sheet.paste(bar, (x, y + th))
    out = ROOT / "e3b_states.png"
    sheet.save(out, optimize=True)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    icons_sheet()
    states_sheet()
