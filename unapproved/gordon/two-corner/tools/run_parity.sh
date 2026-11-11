#!/usr/bin/env bash
# Parity: sim (pinned Python) vs Godot headless, plus dump/load round-trip, the in-game restart test and the Plan the Line key test.
# Godot only since 2026-11-11 (Austin: Three.js dropped; its files stay in threejs/ untouched).
set -u
cd "$(dirname "$0")/.."
G=${GODOT:-/workspace/tools/godot}
mkdir -p out
rc=0
for f in seed20261113_idx seed20261114_idx seed42_timeout seed21273_overtake fuzz300; do
  python3 tools/sim_parity.py spec/inputs/$f.json --out out/sim_$f.json >/dev/null
  $G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/$f.json --out ../out/godot_$f.json >/dev/null 2>&1
  echo "== $f  Godot vs sim"; python3 tools/compare.py out/sim_$f.json out/godot_$f.json | tail -1 || rc=1
done
echo "== dump after corner 1 result, load in a fresh process, finish"
$G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/seed20261113_idx.json --dump-after 0 --dump-to ../out/godot_state.tc1 >/dev/null 2>&1
$G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/seed20261113_idx.json --load ../out/godot_state.tc1 --out ../out/godot_resumed.json >/dev/null 2>&1
echo -n "godot_resumed: "; python3 tools/compare.py out/sim_seed20261113_idx.json out/godot_resumed.json | tail -1 || rc=1
echo "== restart test (game loop)"; bash tools/run_restart_test.sh || rc=1
echo -n "== Plan the Line key test: "
timeout 300 xvfb-run -a -s "-screen 0 1280x960x24" $G --path godot --rendering-driver opengl3 -- --no-menu --plan-key-test 2>&1 | grep -E "PLAN KEY|seed [0-9]+:" || rc=1
echo "token:"; head -c 160 out/godot_state.tc1; echo " ..."
exit $rc
