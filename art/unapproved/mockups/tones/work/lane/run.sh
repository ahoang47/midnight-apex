#!/bin/sh
# Rebuild both v5 mockups. Needs /workspace/asset_packs and the midnight-apex clone (tex/ is already populated).
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
python3 /workspace/midnight-apex/art/mood/tokyo_v2/make_tex_v2.py tex; python3 make_sky_v5.py tex
$B -b -P build_v5.py -- entry; $B -b -P build_v5.py -- apex
python3 post_v5.py entry; python3 post_v5.py apex
