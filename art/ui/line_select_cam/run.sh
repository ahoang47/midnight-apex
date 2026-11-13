#!/bin/sh
# Rebuild the line-select camera mockup. Needs /workspace/asset_packs (street light), the midnight-apex clone (cars),
# /workspace/mockups/tones/work (blend50 preset + lane/tex pool, glow, sky, env, blob textures) and Blender 4.2.3.
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
# The repo copy of race_state_study/ was removed 2026-11-13 (git history). This cp is for a box working copy under /workspace/mockups/.
mkdir -p tex raw; cp ../race_state_study/entry_matrix/asphalt.png ../race_state_study/entry_matrix/hairpin_sign.png tex/
python3 make_tex.py
$B -b -t 4 -P build_lsc.py      # renders raw/raw_{chase,mirror,apex,exit}.png + glow passes + anchors
python3 post_lsc.py             # out/1..4 frames (1280x960) + out/line_select_cam_contact_sheet.png
