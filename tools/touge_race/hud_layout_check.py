#!/usr/bin/env python3
"""HUD layout check at every window size Austin asked for (pt137u pic 3): runs hud_layout_check.gd under xvfb per size,
prints one HUD_LAYOUT_CHECK line each and a summary; exit 1 if any size fails. Stills: <out>/hud_<W>x<H>.png.
usage: python3 tools/touge_race/hud_layout_check.py [--out DIR] [--godot PATH] [--jobs N]"""
import argparse, os, subprocess, sys, concurrent.futures as cf
SIZES = ["1024x768", "1280x720", "1920x1080", "2560x1440", "1366x768", "2560x1080", "800x600"]
ap = argparse.ArgumentParser(); ap.add_argument("--out", default="/tmp/hud_check"); ap.add_argument("--godot", default="/workspace/tools/godot")
ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--sizes", default=",".join(SIZES)); a = ap.parse_args()
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs(a.out, exist_ok=True)
def run(sz):
    cmd = ["xvfb-run", "-a", "-s", f"-screen 0 {sz}x24", a.godot, "--path", root, "--rendering-driver", "opengl3", "--resolution", sz,
           "-s", "res://tools/touge_race/hud_layout_check.gd", "--", "--win", sz, "--out", a.out, "--no-menu", "--seed", "366035919"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    lines = [l for l in p.stdout.splitlines() if l.startswith(("HUD_LAYOUT_CHECK", "HUD_ISSUE", "HUD_WINDOW"))]
    if not any(l.startswith("HUD_LAYOUT_CHECK") for l in lines): lines.append(f"HUD_LAYOUT_CHECK {sz} ERROR (no result) rc={p.returncode} " + p.stderr[-400:].replace("\n", " "))
    return sz, lines
ok = True
with cf.ThreadPoolExecutor(a.jobs) as ex:
    for sz, lines in ex.map(run, a.sizes.split(",")):
        for l in lines: print(l)
        ok = ok and any(l.startswith("HUD_LAYOUT_CHECK") and l.endswith("PASS") for l in lines)
print("HUD_LAYOUT_CHECK ALL", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
