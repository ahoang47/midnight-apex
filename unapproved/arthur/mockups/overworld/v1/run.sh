#!/bin/sh
# Rebuild the overworld mockup. Needs /workspace/asset_packs and the midnight-apex clone (cars); tex/ is already populated
# (copied from lane_chain/v5/tex, plus houses_lit / windows_lit / meet_ring from make_tex_ow.py).
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
python3 make_tex_ow.py tex
$B -b -P build_ow.py
python3 post_ow.py
