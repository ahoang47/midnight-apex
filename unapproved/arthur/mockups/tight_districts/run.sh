#!/usr/bin/env bash
# Tight districts (Arthur, unapproved mockup): one Cel A soft CAT frame per district + the 1x3 sheet.
#   ./run.sh                 textures + Blender props + import + render touge / wangan / street + sheet
#   SKIP_ASSETS=1 ./run.sh   renders + sheet only        ONLY="wangan" ./run.sh   one district
# The Godot project here is self-contained (a dereferenced copy of experiments/cel_shaded/godot as staged on the box,
# plus the changes marked `# TIGHT:` in scripts/district_preview.gd), so there is nothing to stage.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
GODOT="${GODOT:-/workspace/tools/godot}"
BLENDER="${BLENDER:-/workspace/tools/blender-4.2.3-linux-x64/blender}"
if [[ -z "${SKIP_ASSETS:-}" ]]; then
  python3 "$ROOT/tex_src/make_tex.py"
  "$BLENDER" -b -P "$ROOT/blender/build_tight.py" 2>&1 | grep -E "EXPORT|STATS|Error" || true
fi
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
sed -i 's/detect_3d\/compress_to=1/detect_3d\/compress_to=0/' "$ROOT"/godot/art/*.import "$ROOT"/godot/art/env/*.import
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
for d in ${ONLY:-touge wangan street}; do
  DISTRICT="$d" xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 2>&1 | grep -E "DISTRICT_OK|wrote|ERROR|SCRIPT ERROR|Parse|error" || true
done
python3 "$ROOT/make_sheet.py"
