#!/usr/bin/env bash
# Approved 16 m two-row touge turnout parking-lot kit (Arthur).
# LotArt frame (Godot Y-up): origin = road edge at the entrance, +X into lot, +Y up, +Z along travel.
#   ./run.sh                         textures + 16 m / 2-row kit + Cel A-soft renders + sheet
#   SKIP_TEX=1 ./run.sh
#   ONLY=w11 ./run.sh                optional 11 m one-row comparison (writes glb/w11/, not the default)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../.." && pwd)"
BLENDER="${BLENDER:-/workspace/tools/blender-4.2.3-linux-x64/blender}"
export POCKET_M="${POCKET_M:-62}"
export TAPER_M="${TAPER_M:-14}"
export STALL_W="${STALL_W:-2.5}"
export STALL_D="${STALL_D:-5.0}"
export STALL_ANGLE="${STALL_ANGLE:-70}"
export N_LAMPS="${N_LAMPS:-2}"
export CURB_H="${CURB_H:-0.15}"
if [[ -z "${SKIP_TEX:-}" ]]; then
  python3 "$ROOT/tex_src/make_tex.py"
fi
for c in touge_cedar_a.png touge_cedar_b.png; do
  if [[ ! -f "$ROOT/tex/$c" ]]; then
    src="$REPO/assets/tex/kit/$c"
    [[ -f "$src" ]] && cp "$src" "$ROOT/tex/$c"
  fi
done
# lattice module, already vendored in lib/; fallbacks are read-only
if [[ ! -f "$ROOT/lib/mtn_lattice_slope_g.glb" ]]; then
  mkdir -p "$ROOT/lib"
  for src in \
    "$REPO/unapproved/arthur/mockups/mountain_districts/godot/assets/env/mtn_lattice_slope_g.glb" \
    /workspace/gordon-touge/assets/env/mtn_lattice_slope_g.glb
  do
    if [[ -f "$src" ]]; then
      cp "$src" "$ROOT/lib/"
      break
    fi
  done
fi

run_one() {
  local tag="$1" width="$2" rows="$3"
  echo "======== $tag  pocket_w=${width}  rows=${rows} ========"
  POCKET_W="$width" ROWS="$rows" OUT_TAG="$tag" \
    "$BLENDER" -b -P "$ROOT/blender/export_slots.py"
}

ONLY="${ONLY:-w16}"
if [[ "$ONLY" == "w11" || "$ONLY" == "both" ]]; then
  run_one w11 "${POCKET_W_11:-11}" "${ROWS_11:-1}"
fi
if [[ "$ONLY" == "w16" || "$ONLY" == "both" ]]; then
  run_one w16 "${POCKET_W_16:-16}" "${ROWS_16:-2}"
fi

python3 "$ROOT/post.py"
python3 "$ROOT/make_sheet.py"
if [[ -f "$ROOT/renders/w11_race_cam_640.png" && -f "$ROOT/renders/w16_race_cam_640.png" ]]; then
  python3 "$ROOT/make_compare_sheet.py"
fi
echo "OK  renders in $ROOT/renders  glbs in $ROOT/glb"
