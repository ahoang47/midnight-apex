#!/usr/bin/env bash
# VOID check (Austin pt137u pic 5): render every race camera stop (plan E/A/X, the 3 QTE camera types at each QTE, RESULT,
# turnout + 6 lot views) over all 10 turns of a scripted race with the clear colour set to magenta, then ray-test every
# below-horizon magenta pixel against the approved roadside (tools/touge_race/void_check.py). PASS = 0 void pixels and the
# terrain reach covers fog_far + the furthest camera, plus WALL_CHECK (no frame filled by a flat surface) and
# DROP_SIDE_CHECK (drop side downhill, cut side uphill) and TERRAIN_CHECK (no terrain over the road / lot, pt155u). ~40 min on llvmpipe.
# usage: tools/touge_race/void_sweep.sh [OUT_DIR] [INPUTS_JSON]   (inputs need "void_sweep": true; default seed 366 race)
set -u
cd "$(dirname "$0")/../.."
O=${1:-.out/void_sweep}; IN=${2:-}
G=${GODOT:-/workspace/tools/godot}
if [ -z "$IN" ]; then
  IN=$O/void_inputs.json; mkdir -p $O
  python3 - "$IN" <<'PY'
import json, sys
d = json.load(open("spec/touge_playtest.json")); d["void_sweep"] = True; d["shot_turns"] = []; d["cam_turns"] = []
json.dump(d, open(sys.argv[1], "w"))
PY
fi
# geometry first (seconds): the cut / lattice side is uphill and the drop / guardrail side downhill wherever the ground is known
timeout 300 $G --headless --path . -s tools/touge_race/drop_side_check.gd 2>&1 | grep -E "^DROP_SIDE"; D=${PIPESTATUS[0]}
rm -rf $O/void_raw; mkdir -p $O; O=$(realpath $O); IN=$(realpath $IN)
# no terrain over any drivable surface (road + lot, every leg, up to road_clear_m): pt155u, main.gd --terrain-check
timeout 900 xvfb-run -a -s "-screen 0 1280x960x24" $G --path . --rendering-driver opengl3 -- --script-inputs $IN --terrain-check 2>&1 | grep -E "^TERRAIN"; TC=${PIPESTATUS[0]}
timeout 4000 xvfb-run -a -s "-screen 0 1280x960x24" $G --path . --rendering-driver opengl3 -- --script-inputs $IN --shots $O --void-no-shots > $O/void_sweep.log 2>&1
grep -E "VOID_SWEEP_DONE" $O/void_sweep.log || { echo "VOID_CHECK sweep did not finish (see $O/void_sweep.log)"; exit 1; }
python3 tools/touge_race/void_check.py $O --masks $O/masks
V=$?
python3 tools/touge_race/wall_check.py $O; W=$?
[ $V -eq 0 ] && [ $W -eq 0 ] && [ $D -eq 0 ] && [ $TC -eq 0 ]
