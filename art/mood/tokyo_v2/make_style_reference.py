"""Tokyo v2 style-reference sheet (REBUILT 2026-10-31 after data loss): palette swatches + six captioned crops.
Palette values transcribed from the surviving original sheet (renders/tokyo_v2_original_800/style_reference_800.jpg)."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(os.path.dirname(HERE), "renders", "tokyo_v2") if os.path.basename(HERE) == "tokyo" else os.path.join(HERE, "renders")
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; Rg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PAL = [("CAR", [("#C70D0F", "body paint"), ("#2C0406", "panel line"), ("#1E1E20", "soft top"), ("#FFF2CC", "head glow"), ("#FF1F14", "tail glow")]),
       ("LIGHT", [("#FF9947", "sodium"), ("#9597AD", "road amb"), ("#ADADC8", "vtx amb"), ("#FFD28C", "warm window"), ("#B4E1FF", "cool window"), ("#161C2A", "dark window")]),
       ("SKY/FOG", [("#060614", "zenith"), ("#42284A", "horizon"), ("#784246", "city glow"), ("#30263F", "fog"), ("#120E1C", "skyline")]),
       ("WALLS", [(h, "") for h in ['#C4B8A0', '#8E8A84', '#96523C', '#D6D2C8', '#6E7C88', '#A8A074', '#604032', '#5A826E', '#E2D4B4', '#80788C', '#B8B0AA', '#464850']]),
       ("NEON", [(h, "") for h in ['#FF3C8C', '#3CC8FF', '#FFAA28', '#78FF78', '#C85AFF', '#FF4632']]),
       ("SIGNAGE", [("#6E3CAA", "konbini"), ("#FAC828", "konbini"), ("#285ADC", "drug"), ("#14783C", "parking"), ("#DC283C", "cleaning"), ("#F05014", "cone")])]
CROPS = [("hero_front34", (380, 380, 1000, 760), "CAR: fake env-map shine + Blinn spec, emissive lamps + glow\nsprites, blob shadow, hard jaggies (no AA), 2x nearest upscale"),
         ("establishing", (420, 520, 1040, 896), "ROAD: dry matte asphalt; sodium pools PAINTED into the\ntexture (stepped bands); no wetness / reflections"),
         ("hero_front34", (0, 60, 620, 440), "SIGNS: unlit full-bright neon + additive glow billboards;\nmade-up names only; flat-ribbon wires"),
         ("establishing", (0, 420, 620, 800), "PROPS/SHOPS: pre-lit storefront + cut-out cards;\nsidewalk lit by vertex colour"),
         ("rear34", (640, 60, 1260, 440), "DEPTH: painted sky + skyline cards; linear fog\n(14-105 m) colour-matched to the sky"),
         ("establishing", (900, 60, 1280, 440), "FACADES: pre-lit night textures x vertex light;\nlit/dark windows, AC units, shutters")]
W = 1600; sheet = Image.new('RGB', (W, 1240), (16, 14, 24)); d = ImageDraw.Draw(sheet)
d.text((20, 14), "S2000 / TOKYO v2  -  STYLE REFERENCE  (vibe check, rebuilt 2026-10-31)  -  see art_direction.md Part B", font=ImageFont.truetype(B, 22), fill=(240, 240, 240))
y = 60; fs = ImageFont.truetype(Rg, 12); fl = ImageFont.truetype(B, 14)
for label, sw in PAL:
    d.text((20, y + 12), label, font=fl, fill=(220, 220, 220))
    for i, (h, n) in enumerate(sw):
        x = 140 + i * 96; d.rectangle([x, y, x + 84, y + 30], fill=h)
        d.text((x, y + 32), h, font=fs, fill=(200, 200, 200)); d.text((x, y + 46), n, font=fs, fill=(160, 160, 170))
    y += 70
ims = {n: Image.open(os.path.join(RD, f"tokyo_v2_{n}.png")) for n in ("hero_front34", "rear34", "establishing")}
cw, ch = 500, 300
for k, (n, box, cap) in enumerate(CROPS):
    cx = 20 + (k % 3) * (cw + 30); cy = y + 10 + (k // 3) * (ch + 60)
    sheet.paste(ims[n].crop(box).resize((cw, ch), Image.NEAREST), (cx, cy))
    d.multiline_text((cx, cy + ch + 4), cap, font=fs, fill=(220, 220, 220))
sheet = sheet.crop((0, 0, W, y + 10 + 2 * (ch + 60)))
sheet.save(os.path.join(RD, "style_reference.png"))
sheet.resize((800, int(800 * sheet.height / W)), Image.LANCZOS).save(os.path.join(RD, "style_reference_800.jpg"), quality=90)
print("style reference", sheet.size)
