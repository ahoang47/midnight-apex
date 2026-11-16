#!/usr/bin/env bash
# Mountain districts (Arthur, unapproved mockup): 9 Cel A soft CAT frames (touge / wangan / street x entry OUT / MID / IN)
# + the sheets. Pass 4 (default): wangan_*_cat_v4, wangan_bridge_*_cat_v4, street_alley_*_cat_v4, mountain_districts_sheet_v4.png;
# MTN_V=3 / 2 / 1 ./run.sh rebuild the v3 / v2 / v1 frames + sheets exactly. ONLY="wangan:bridge" ./run.sh: one section.
#   ./run.sh                 textures + Blender props + import + render touge / wangan / street (3 lanes each) + sheet
#   SKIP_ASSETS=1 ./run.sh   renders + sheet only        ONLY="wangan" ./run.sh   one district
# The Godot project here is self-contained (a dereferenced copy of experiments/cel_shaded/godot as staged on the box,
# plus the changes marked `# TIGHT:` and `# MOUNTAIN:` in scripts/district_preview.gd), so there is nothing to stage.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
GODOT="${GODOT:-/workspace/tools/godot}"
BLENDER="${BLENDER:-/workspace/tools/blender-4.2.3-linux-x64/blender}"
if [[ -z "${SKIP_ASSETS:-}" ]]; then
  python3 "$ROOT/tex_src/make_tex.py"
  "$BLENDER" -b -P "$ROOT/blender/build_mountain.py" 2>&1 | grep -E "EXPORT|STATS|Error" || true
fi
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
sed -i 's/detect_3d\/compress_to=1/detect_3d\/compress_to=0/' "$ROOT"/godot/art/*.import "$ROOT"/godot/art/env/*.import "$ROOT"/godot/assets/env/*.import
"$GODOT" --headless --path "$ROOT/godot" --import --quit >/dev/null 2>&1 || true
# FRAME=wangan_mid_cat.png renders one frame only. timeout: a GDScript parse error leaves Godot open instead of quitting
# pass 4 (default) renders only what changed: wangan skyline, wangan:bridge, street:alley (touge / street main reuse v3)
if [[ "${MTN_V:-4}" == "4" ]]; then DEF="wangan wangan:bridge street:alley"; else DEF="touge wangan street"; fi
for x in ${ONLY:-$DEF}; do
  d="${x%%:*}"; s=""; [[ "$x" == *:* ]] && s="${x##*:}"
  SECTION="$s" DISTRICT="$d" timeout 900 xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$ROOT/godot" --rendering-driver opengl3 2>&1 | grep -E "DISTRICT_OK|wrote|ERROR|SCRIPT ERROR|Parse|error" || true
done
case "${MTN_V:-4}" in 1) python3 "$ROOT/make_sheet.py" ;; 2) python3 "$ROOT/make_sheet.py" v2 ;; 3) python3 "$ROOT/make_sheet.py" v3 ;; *) python3 "$ROOT/make_sheet.py" v4 ;; esac
