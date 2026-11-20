#!/usr/bin/env bash
# TOUGE 10-turn race (Gordon, unapproved). The game now lives in the repo root (res:// = repo root); this script only drives it.
#   ./run.sh play       import + play (F6 timer off, F9 dump, F10 load)
#   ./run.sh checks     headless parity (mx5 / brz vs s2000), auto-fill check, then the scripted race with CLIP_CHECK / HEAT_CHECK
#                       and the game-result parity under $OUT (default /tmp/touge)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"; GODOT="${GODOT:-/workspace/tools/godot}"; OUT="${OUT:-/tmp/touge}"
X() { xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$REPO" --rendering-driver opengl3 "$@"; }
MODE="${1:-play}"; shift || true
"$GODOT" --headless --path "$REPO" --import >/dev/null 2>&1 || true
case "$MODE" in
  play) X "$@" ;;
  checks)
    python3 "$REPO/tools/touge_race/parity_touge.py" 300 --player-car mx5 --opp-car s2000
    python3 "$REPO/tools/touge_race/parity_touge.py" 100 --player-car brz --opp-car s2000
    "$GODOT" --headless --path "$REPO" -s tools/touge_race/autofill_check.gd | grep AUTOFILL_CHECK
    mkdir -p "$OUT"
    X -- --script-inputs res://spec/touge_playtest.json --shots "$OUT" > "$OUT/run.log" 2>&1
    grep -E "CLIP_CHECK|HEAT_CHECK" "$OUT/run.log"
    python3 "$REPO/tools/touge_race/parity_touge.py" --game-result "$OUT/touge_result.json" ;;
esac
