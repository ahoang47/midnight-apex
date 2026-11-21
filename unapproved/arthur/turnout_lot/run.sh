#!/usr/bin/env bash
# Touge turnout parking-lot kit (Arthur, unapproved).
# LotArt frame (Godot Y-up): origin = road edge at the entrance, +X into lot, +Y up, +Z along travel.
#   ./run.sh                              textures + 11 m (1-row) + 16 m (2-row) + renders + sheet
#   SKIP_TEX=1 ./run.sh
#   ONLY=w11 ./run.sh                     just the 11 m kit
#   POCKET_M=80 TAPER_M=16 POCKET_W=11 ROWS=1 N_LAMPS=2 ./run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
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
    src="/workspace/arthur-turnout/assets/tex/kit/$c"
    [[ -f "$src" ]] && cp "$src" "$ROOT/tex/$c"
  fi
done
# lattice module (read from Gordon's tree, never write there)
if [[ ! -f "$ROOT/lib/mtn_lattice_slope_g.glb" && -f /workspace/gordon-touge/assets/env/mtn_lattice_slope_g.glb ]]; then
  mkdir -p "$ROOT/lib"
  cp /workspace/gordon-touge/assets/env/mtn_lattice_slope_g.glb "$ROOT/lib/"
fi

run_one() {
  local tag="$1" width="$2" rows="$3"
  echo "======== $tag  pocket_w=${width}  rows=${rows} ========"
  POCKET_W="$width" ROWS="$rows" OUT_TAG="$tag" \
    "$BLENDER" -b -P "$ROOT/blender/export_slots.py"
}

ONLY="${ONLY:-both}"
if [[ "$ONLY" == "w11" || "$ONLY" == "both" ]]; then
  run_one w11 "${POCKET_W_11:-11}" "${ROWS_11:-1}"
fi
if [[ "$ONLY" == "w16" || "$ONLY" == "both" ]]; then
  run_one w16 "${POCKET_W_16:-16}" "${ROWS_16:-2}"
fi

python3 "$ROOT/post.py"
python3 "$ROOT/make_compare_sheet.py"
echo "OK  renders in $ROOT/renders  glbs in $ROOT/glb/w11 and $ROOT/glb/w16"
