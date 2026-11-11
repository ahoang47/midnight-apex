#!/bin/sh
# Rebuild the playback mockups. Needs ../line_select_cam/tex (run ../line_select_cam/run.sh or its make_tex.py first),
# /workspace/asset_packs, the midnight-apex clone (cars), /workspace/mockups/tones/work and Blender 4.2.3.
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
$B -b -t 4 -P build_clash.py    # raw/raw_{entry,apex,exit}_{a,b}.png + glow passes + anchors
python3 post_clash.py           # out/a1..a3, out/b1..b3 (1280x960) + out/line_clash_comparison_sheet.png
