#!/usr/bin/env bash
# Cel A study (approved 2026-11-19): stage on top of the staged districts project, render touge / street / wangan
# in Godot 4.6.3 (each writes <district>_cel.png and <district>_cel_clean.png), then make cel_compare_sheet.png.
#   ./run.sh      ONLY="touge" ./run.sh     CEL_NOINK=1 ./run.sh (ramp only, for checking)
# Needs ../../../unapproved/arthur/mockups/districts/godot staged first (its own run.sh / stage.py).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
GODOT="${GODOT:-/workspace/tools/godot}"
python3 "$ROOT/../../../unapproved/arthur/mockups/districts/stage.py" >/dev/null
python3 "$ROOT/stage.py"
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
for d in ${ONLY:-touge street wangan}; do
  DISTRICT="$d" xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 2>&1 | grep -E "DISTRICT_OK|wrote|ERROR|SCRIPT ERROR|Parse|error" || true
done
python3 "$ROOT/make_sheet.py"
