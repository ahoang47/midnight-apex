#!/usr/bin/env bash
# Cel A port of Gordon's two-corner test (unapproved experiment). Stages the project, then:
#   ./run.sh play       play it (F7 toggles cel on/off; ./run.sh play -- --cel 0 starts with it off)
#   ./run.sh playtest   scripted full race (spec/shots9_pass.json, seed 3) at a fixed 30 fps: key shots cel on + off,
#                       per-frame dumps (on / off / ink mask) for the video and the motion checks, under $OUT (default /tmp/ctc)
#   ./run.sh perf       the same scripted race in real time, cel off / on twice each, prints CEL_PERF lines
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; GODOT="${GODOT:-/workspace/tools/godot}"; OUT="${OUT:-/tmp/ctc}"
python3 "$ROOT/stage.py"
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
X() { xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 "$@"; }
IN="--script-inputs res://spec/shots9_pass.json"
MODE="${1:-play}"; shift || true
case "$MODE" in
  play) X "$@" ;;
  playtest)
    mkdir -p "$OUT"/{gif_on,gif_off,gif_ink}
    X --fixed-fps 30 -- $IN --cel 1 --shots "$OUT/on3" > "$OUT/on3.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 0 --shots "$OUT/off1" > "$OUT/off1.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 1 --gif "$OUT/gif_on" --gif-dt 0.0333333 > "$OUT/gif_on.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 0 --gif "$OUT/gif_off" --gif-dt 0.0333333 > "$OUT/gif_off.log" 2>&1
    X --fixed-fps 30 -- $IN --cel 1 --ink-debug --gif "$OUT/gif_ink" --gif-dt 0.0333333 > "$OUT/gif_ink.log" 2>&1
    grep -hiE "error" "$OUT"/*.log || echo "no errors in the Godot logs"
    ffmpeg -y -loglevel error -framerate 30 -i "$OUT/gif_on/f%05d.png" -c:v libx264 -pix_fmt yuv420p -crf 30 -preset slow -tune grain "$ROOT/cel_two_corner_run.mp4"
    (cd "$OUT" && python3 "$ROOT/playtest/ink_pops.py" && python3 "$ROOT/playtest/temporal_diff.py")
    GIF_ON="$OUT/gif_on" GIF_OFF="$OUT/gif_off" GIF_INK="$OUT/gif_ink" python3 "$ROOT/make_sheet.py" ;;
  perf) for c in 0 1 0 1; do X -- $IN --cel $c --perf 2>&1 | grep -E "CEL_PERF|ERROR"; done ;;
esac
