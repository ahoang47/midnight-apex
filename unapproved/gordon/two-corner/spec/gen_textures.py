"""Procedural PSX road textures (display only), quantised to RGB555 with 4x4 Bayer at authoring (art_direction A.3.5).
road.png: u across the road (-W..W), v along one ROAD_TEX_TILE_M tile: asphalt, edge lines, dashed lane lines.
verge.png: dark grass/gravel. barrier.png: concrete wall with a dark post seam per tile."""
import json, random
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
disp = json.load(open(ROOT / "spec" / "display.json"))
B = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
def q(img):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            b = B[(x % 4) + (y % 4) * 4] / 16 - 0.5
            px[x, y] = tuple(max(0, min(31, int(c / 255 * 31 + 0.5 + b))) * 255 // 31 for c in px[x, y])
    return img
R = random.Random(3)
lw = disp["lane_width_m"]; W = lw * 1.5 + 1.0; tile = disp["road_scroller"]["road_tex_tile_m"]
w, h = 64, 64
road = Image.new("RGB", (w, h))
for y in range(h):
    for x in range(w):
        g = 62 + R.randint(-10, 10); road.putpixel((x, y), (g, g, g + 6))
def ucol(d): return int((d + W) / (2 * W) * w)
for y in range(h):
    sm = (y + 0.5) / h * tile
    for d in (-W + 0.6, W - 0.6):
        road.putpixel((ucol(d), y), (200, 200, 190))
    if sm < tile * 0.4:  # dash 40% of the tile
        for d in (-lw * 0.5, lw * 0.5):
            for x in (ucol(d), ucol(d) + 1): road.putpixel((x, y), (215, 215, 200))
q(road).save(ROOT / "spec" / "tex" / "road.png")
verge = Image.new("RGB", (32, 32))
for y in range(32):
    for x in range(32):
        g = R.randint(0, 14); verge.putpixel((x, y), (16 + g, 26 + g, 18 + g))
q(verge).save(ROOT / "spec" / "tex" / "verge.png")
bar = Image.new("RGB", (16, 16))
for y in range(16):
    for x in range(16):
        g = 88 + R.randint(-8, 8) - (40 if y < 2 else 0); bar.putpixel((x, y), (g, g - 4, g - 10))
q(bar).save(ROOT / "spec" / "tex" / "barrier.png")
print("ok")
