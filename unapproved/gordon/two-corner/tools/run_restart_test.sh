#!/usr/bin/env bash
# Restart test (Austin 2026-11-10): in the Godot game loop, run a race, then restart through each finish option
# (1 RESTART SAME SEED, 2 NEW RACE, 3 MAIN MENU -> type seed -> START RACE) and check EVERY race against the pinned sim.
# The game also asserts that the restarted state equals a cold start (fresh RaceCore: seed, rng draws, line, hand, totals).
# Godot only since 2026-11-11. Needs xvfb. Usage: tools/run_restart_test.sh [outroot=out/restart_test]
set -u; cd "$(dirname "$0")/.."
G=${GODOT:-/workspace/tools/godot}
OUT=${1:-out/restart_test}; rc=0; rm -rf $OUT/godot
python3 tools/sim_parity.py spec/inputs/restart_test.json --out out/sim_restart_test.json >/dev/null
timeout 600 xvfb-run -a -s "-screen 0 1280x960x24" "$G" --path godot --rendering-driver opengl3 -- \
  --script-inputs res://spec/restart_test.json --shots $PWD/$OUT/godot >/dev/null 2>&1 || rc=1
echo -n "restart Godot vs sim: "; python3 tools/compare.py out/sim_restart_test.json $OUT/godot/result_640.json | tail -1 || rc=1
exit $rc
