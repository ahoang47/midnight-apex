#!/usr/bin/env bash
# District looks (unapproved): paint textures, build the Blender prop kit, stage the Godot project on top of the
# E3B resource-meter project, render touge / street / wangan with the E3B HUD, then make the sheet.
#   ./run.sh            everything        SKIP_ASSETS=1 ./run.sh   Godot renders + sheet only
#   ONLY="touge" ./run.sh                 one district
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
GODOT="${GODOT:-/workspace/tools/godot}"
BLENDER="${BLENDER:-/workspace/tools/blender-4.2.3-linux-x64/blender}"
if [[ -z "${SKIP_ASSETS:-}" ]]; then
  python3 "$ROOT/tex_src/make_tex.py"
  "$BLENDER" -b -P "$ROOT/blender/build_assets.py" 2>&1 | grep -E "EXPORT|STATS|Error" || true
fi
# resource_meters/godot must already be staged (resource_meters/run.sh links it from line_preview)
python3 "$ROOT/stage.py"
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
for d in ${ONLY:-touge street wangan}; do
  DISTRICT="$d" xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 2>&1 | grep -E "DISTRICT_OK|wrote|ERROR|SCRIPT ERROR|Parse" || true
done
python3 "$ROOT/make_sheet.py"
