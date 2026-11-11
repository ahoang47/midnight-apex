#!/bin/sh
# Render every tone for both scenes. Tone presets live in tones.py. Usage: ./run_tones.sh [tone ...]
set -e; cd "$(dirname "$0")"; B=/workspace/tools/blender-4.2.3-linux-x64/blender
python3 make_tone_tex.py lane/tex; python3 make_tone_tex.py ow/tex
TONES=${*:-"sodium mercury txr rain dawn"}
for t in $TONES; do
  TONE=$t $B -b -P lane/build_v5.py -- entry > /tmp/tone_lane_$t.log 2>&1 && TONE=$t python3 lane/post_v5.py entry
  TONE=$t $B -b -P ow/build_ow.py > /tmp/tone_ow_$t.log 2>&1 && TONE=$t python3 ow/post_ow.py
done
python3 sheet.py
