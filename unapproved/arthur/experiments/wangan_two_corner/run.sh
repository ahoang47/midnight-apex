#!/usr/bin/env bash
# Wangan two-corner playtest (Arthur, unapproved experiment). The Godot project here is a full copy (Gordon's two-corner
# + the Cel A soft port + the Wangan changes marked `# WANGAN:`), so there is nothing to stage.
#   ./run.sh assets     repaint the textures (tex_src/make_tex.py) and rebuild the Blender kit (blender/build_wangan.py)
#   ./run.sh play       play it (F7 cel on/off, F8 Cel A soft / original Cel A)
#   ./run.sh playtest   scripted full race (spec/wangan_pass.json) at a fixed 30 fps: key shots cel on + off, per-frame
#                       dumps (on / off / ink mask) for the video and the motion checks, under $OUT (default /tmp/wtc)
#   ./run.sh perf       the same scripted race in real time, cel off / on twice each, prints CEL_PERF lines
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; GODOT="${GODOT:-/workspace/tools/godot}"; OUT="${OUT:-/tmp/wtc}"
BLENDER="${BLENDER:-/workspace/tools/blender-4.2.3-linux-x64/blender}"
IN="--script-inputs res://spec/${INPUTS:-wangan_pass}.json"
X() { xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 "$@"; }
MODE="${1:-play}"; shift || true
case "$MODE" in
  assets)
    python3 "$ROOT/tex_src/make_tex.py"
    "$BLENDER" -b -P "$ROOT/blender/build_wangan.py" | grep -E "EXPORT|STATS"
    "$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
    sed -i 's/detect_3d\/compress_to=1/detect_3d\/compress_to=0/' "$ROOT"/godot/art/env/*.import ;;
  play) "$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true; X "$@" ;;
  playtest)
    "$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
    mkdir -p "$OUT"/{gif_on,gif_off,gif_ink}
    X --fixed-fps 30 -- $IN --cel 1 --shots "$OUT/on" > "$OUT/on.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 0 --shots "$OUT/off" > "$OUT/off.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 1 --gif "$OUT/gif_on" --gif-dt 0.0333333 > "$OUT/gif_on.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 0 --gif "$OUT/gif_off" --gif-dt 0.0333333 > "$OUT/gif_off.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 1 --ink-debug --gif "$OUT/gif_ink" --gif-dt 0.0333333 > "$OUT/gif_ink.log" 2>&1
    grep -hiE "error" "$OUT"/*.log || echo "no errors in the Godot logs"
    ffmpeg -y -loglevel error -framerate 30 -i "$OUT/gif_on/f%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow /workspace/wangan_two_corner_run.mp4
    ffmpeg -y -loglevel error -framerate 30 -i "$OUT/gif_on/f%05d.png" -vf scale=960:720:flags=neighbor -c:v libx264 -pix_fmt yuv420p -crf 31 -preset slow -tune grain "$ROOT/wangan_two_corner_run.mp4"
    OUT="$OUT" python3 "$ROOT/playtest/checks.py"
    OUT="$OUT" python3 "$ROOT/make_sheet.py" ;;
  perf) "$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
    for c in 0 1 0 1; do X -- $IN --cel $c --perf 2>&1 | grep -E "CEL_PERF|ERROR"; done ;;
esac
