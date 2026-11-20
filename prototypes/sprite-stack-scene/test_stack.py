"""Headless checks for the sprite-stack look test.

Run from the repo root or from this folder:

    python3 prototypes/sprite-stack-scene/test_stack.py

Needs Pillow (already used to build the sheets) and node on PATH.
The page check needs Google Chrome.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))

from stack_math import draw_stack, iround, opaque_bbox, turn_from_velocity  # noqa: E402


def check(name, cond):
    if not cond:
        raise SystemExit("FAIL " + name)
    print("PASS", name)


def test_guide_invariants():
    sw, sh, count = 6, 8, 4
    sheet = np.zeros((sh, count * sw, 4), np.uint8)
    for z in range(count):
        sheet[:, z * sw : (z + 1) * sw] = (40 + z * 40, 10, 10, 255)

    def pasted(spacing):
        out_h = sh + (count - 1) * spacing
        out = np.zeros((out_h, sw, 4), np.uint8)
        for z in range(count):
            sl = sheet[:, z * sw : (z + 1) * sw]
            y0 = (count - 1 - z) * spacing
            for y in range(sh):
                for x in range(sw):
                    if sl[y, x, 3] >= 128:
                        out[y0 + y, x] = sl[y, x]
        return out

    dest = np.zeros((sh + (count - 1), sw, 4), np.uint8)
    draw_stack(sheet, count, sw, sh, (sw // 2, (count - 1) + sh // 2), 0.0, 1.0, 1.0, dest)
    check("straight paste matches hand stack", np.array_equal(dest, pasted(1)))

    box = opaque_bbox(dest)
    check("squash 1 turn 0 width", box[2] - box[0] + 1 == sw)
    check("squash 1 turn 0 height", box[3] - box[1] + 1 == sh + count - 1)

    flat = np.zeros((sh, sw, 4), np.uint8)
    draw_stack(sheet, count, sw, sh, (sw // 2, sh // 2), 0.0, 1.0, 0.0, flat)
    check("spacing 0 keeps the top slice", np.array_equal(flat, sheet[:, (count - 1) * sw : count * sw]))

    squashed = draw_stack(sheet, count, sw, sh, (40, 40), 0.0, 0.75, 1.0)
    tall = draw_stack(sheet, count, sw, sh, (40, 40), 0.0, 1.0, 1.0)
    wide = draw_stack(sheet, count, sw, sh, (40, 40), math.pi / 2, 1.0, 1.0)
    spaced = draw_stack(sheet, count, sw, sh, (40, 60), 0.0, 1.0, 2.0)
    sb = opaque_bbox(squashed)
    tb = opaque_bbox(tall)
    wb = opaque_bbox(wide)
    sp = opaque_bbox(spaced)
    check("squash 0.75 is shorter", (sb[3] - sb[1]) < (tb[3] - tb[1]))
    check("spacing 2 is taller", (sp[3] - sp[1]) > (tb[3] - tb[1]))
    turned_w = wb[2] - wb[0] + 1
    check("turn 90 width is the slice height", abs(turned_w - sh) <= 2)


def test_nose_follows_heading():
    sw, sh = 9, 11
    sheet = np.zeros((sh, sw, 4), np.uint8)
    sheet[sh - 2, sw // 2] = (220, 20, 20, 255)
    sheet[1, sw // 2] = (20, 40, 220, 255)
    dest = np.zeros((81, 81, 4), np.uint8)
    # Moving up the screen (negative y). The sheet faces down, so it must spin 180.
    turn = turn_from_velocity(0.0, -1.0)
    check("upward turn is a half turn", abs(abs(turn) - math.pi) < 1e-6)
    draw_stack(sheet, 1, sw, sh, (40, 40), turn, 1.0, 1.0, dest)
    red = np.argwhere((dest[:, :, 0] > 180) & (dest[:, :, 2] < 40))
    check("nose is drawn", len(red) == 1)
    check("nose points up the screen", int(red[0, 0]) < 40)

    dest2 = np.zeros((81, 81, 4), np.uint8)
    turn_r = turn_from_velocity(1.0, 0.0)
    draw_stack(sheet, 1, sw, sh, (40, 40), turn_r, 1.0, 1.0, dest2)
    red = np.argwhere((dest2[:, :, 0] > 180) & (dest2[:, :, 2] < 40))
    check("nose points right", int(red[0, 1]) > 40 and abs(int(red[0, 0]) - 40) <= 1)
    _ = iround


def test_sheets():
    manifest = json.loads((HERE / "slices" / "manifest.json").read_text())
    check("internal resolution", manifest["internal"] == [640, 480])
    check("default squash", manifest["squash"] == 0.75)
    objs = manifest["objects"]
    for car in ("kite", "daybreak", "hatchet", "chalk"):
        check(car + " present", car in objs and objs[car]["role"] == "car")
    peaks = []
    for obj in objs.values():
        im = Image.open(HERE / "slices" / obj["file"]).convert("RGBA")
        check(obj["id"] + " sheet width", im.size[0] == obj["w"] * obj["slices"])
        check(obj["id"] + " sheet height", im.size[1] == obj["h"])
        check(obj["id"] + " pivot is the slice center", obj["pivot_x"] == obj["w"] // 2 and obj["pivot_y"] == obj["h"] // 2)
        arr = np.asarray(im)
        opaque = int((arr[:, :, 3] >= 128).sum())
        check(obj["id"] + " has pixels", opaque > 20)
        ground = arr[:, : obj["w"], 3]
        top = arr[:, (obj["slices"] - 1) * obj["w"] :, 3]
        check(obj["id"] + " ground slice", int((ground >= 128).sum()) > 0)
        check(obj["id"] + " top slice", int((top >= 128).sum()) > 0)
        if obj["role"] == "car":
            peaks.append(obj["peak_luma"])
            # Front of the sheet is +y, so the lower rows of a mid slice should be occupied.
            mid = arr[:, (obj["slices"] // 2) * obj["w"] : (obj["slices"] // 2 + 1) * obj["w"], 3]
            check(obj["id"] + " mid slice", int((mid >= 128).sum()) > 30)
    hut = objs["hut"]["peak_luma"]
    check("stand is dimmer than every car", hut < min(peaks))


def test_js_syntax():
    subprocess.check_call(["node", "--check", str(HERE / "main.js")])
    print("PASS main.js syntax")


def test_page_loads():
    url = "file://" + str(HERE / "index.html") + "?t=0.4"
    proc = subprocess.run(
        [
            "/opt/google/chrome/chrome",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--user-data-dir=/tmp/chrome-stack-test",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=8000",
            "--timeout=20000",
            "--dump-dom",
            url,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    html = proc.stdout + proc.stderr
    if "ready" not in html:
        tail = html[-1500:]
        raise SystemExit("FAIL page load\n" + tail)
    if "error:" in html.split("id=\"status\"", 1)[-1][:200]:
        raise SystemExit("FAIL page status\n" + html[-800:])
    print("PASS page loads")


def main():
    test_guide_invariants()
    test_nose_follows_heading()
    test_sheets()
    test_js_syntax()
    test_page_loads()
    print("ALL PASS")


if __name__ == "__main__":
    main()
