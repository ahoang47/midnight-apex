#!/bin/sh
# Rebuild both v4 mockups. Needs /workspace/asset_packs and the midnight-apex clone.
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
python3 /workspace/midnight-apex/art/mood/tokyo_v2/make_tex_v2.py tex   # glow/blob/throw/env/skyline textures (Tokyo v2)
python3 make_sky_v4.py tex                                               # sky gradient + stepped pool decal (hand-built)
$B -b -P build_v4.py -- entry; $B -b -P build_v4.py -- apex
python3 post_v4.py entry; python3 post_v4.py apex
