#!/usr/bin/env bash
# Screenshots + frame sequences, Godot only (since 2026-11-11), single look (640x480, RGB555 + Bayer).
# Usage: tools/two_corner/run_shots.sh <input-name> [outroot]
set -eu; cd "$(dirname "$0")/../.."   # repo root = the Godot project
O=.out/two_corner
IN=${1:-seed20261113_idx}; OUT=${2:-$O/shots5}
xvfb-run -a -s "-screen 0 1280x960x24" /workspace/tools/godot --path . --rendering-driver opengl3 -- --script-inputs res://spec/$IN.json --shots $PWD/$OUT/godot_$IN >/dev/null 2>&1
python3 tools/two_corner/sim_parity.py spec/$IN.json --out $O/sim_$IN.json >/dev/null
python3 tools/two_corner/compare.py $O/sim_$IN.json $OUT/godot_$IN/result_640.json | tail -1
