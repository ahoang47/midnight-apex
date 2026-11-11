#!/bin/bash
set -euo pipefail
export MAMBA_ROOT_PREFIX=/workspace/tools/mamba-root
eval "$(/workspace/tools/mamba/bin/micromamba shell hook -s bash)"
micromamba activate crt
source "$HOME/.cargo/env"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
HERE=/workspace/mockups/race_state_study/resolution_test
for name in 03_close_behind_center 04_far_behind_outside 04_far_behind_center 04_far_behind_inside 02_ahead_room_center; do
 for w in 640 960; do
  librashader-cli render -r opengl3 -p "$HERE/crt_easymode_restrained.slangp" -i "$HERE/native/${name}_${w}_native.png" -o "$HERE/display/${name}_${w}_crt.png" -d 1920x1440 -f 3 >"$HERE/logs/${name}_${w}_crt.log" 2>&1
  echo "CRT_DONE ${name} ${w}"
 done
done
librashader-cli --version > "$HERE/logs/librashader_version.txt"
