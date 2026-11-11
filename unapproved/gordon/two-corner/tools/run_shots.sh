#!/usr/bin/env bash
# Screenshots + frame sequences, Godot only (since 2026-11-11), single look (640x480, RGB555 + Bayer).
# Usage: tools/run_shots.sh <input-name> [outroot]
set -eu; cd "$(dirname "$0")/.."
IN=${1:-seed20261113_idx}; OUT=${2:-out/shots4}
xvfb-run -a -s "-screen 0 1280x960x24" /workspace/tools/godot --path godot --rendering-driver opengl3 -- --script-inputs res://spec/$IN.json --shots $PWD/$OUT/godot_$IN >/dev/null 2>&1
python3 tools/sim_parity.py spec/inputs/$IN.json --out out/sim_$IN.json >/dev/null
python3 tools/compare.py out/sim_$IN.json $OUT/godot_$IN/result_640.json | tail -1
