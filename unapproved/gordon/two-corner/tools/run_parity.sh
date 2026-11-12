#!/usr/bin/env bash
# Parity: sim (pinned Python) vs Godot headless, plus dump/load round-trip, the in-game restart test and the Plan the Line key test.
# Godot only since 2026-11-11 (Austin: Three.js dropped; its files stay in threejs/ untouched).
# Sim pin 50928ed (53267c5 POW/EN/HAN rename + c3ffc41 QTE rounding). Per-phase QTE inputs [entry, apex, exit] go into
# both engines, each phase score rounded with floor(x*1000+0.5)/1000; the mean is not re-rounded. qte_fn_test.py checks
# raw_qte_score bit-for-bit and allows a 1-ULP tolerance on unrounded erf / expected_hit_quality / qte_zone_width.
# CI's qte-v1 step is strict (50928ed, no continue-on-error).
set -u
cd "$(dirname "$0")/.."
G=${GODOT:-/workspace/tools/godot}
mkdir -p out
rc=0
python3 tools/stamp_build.py
if [ "${SKIP_QTE_FN_TEST:-0}" != "1" ]; then
  echo -n "== "; python3 tools/qte_fn_test.py || rc=1
fi
for f in seed20261113_idx seed20261114_idx seed42_timeout seed21273_overtake fuzz300; do
  python3 tools/sim_parity.py spec/inputs/$f.json --out out/sim_$f.json >/dev/null
  $G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/$f.json --out ../out/godot_$f.json >/dev/null 2>&1
  echo "== $f  Godot vs sim"; python3 tools/compare.py out/sim_$f.json out/godot_$f.json | tail -1 || rc=1
done
echo "== dump after corner 1 result, load in a fresh process, finish"
for f in seed20261113_idx seed20261114_idx seed42_timeout; do
  $G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/$f.json --dump-after 0 --dump-to ../out/godot_state.tc2 >/dev/null 2>&1
  $G --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/$f.json --load ../out/godot_state.tc2 --out ../out/godot_resumed.json >/dev/null 2>&1
  echo -n "godot_resumed $f: "; python3 tools/compare.py out/sim_$f.json out/godot_resumed.json | tail -1 || rc=1
done
echo "== restart test (game loop)"; bash tools/run_restart_test.sh || rc=1
echo -n "== Plan the Line key test: "
rm -f out/key_test_inputs.json out/key_test_godot.json
timeout 600 xvfb-run -a -s "-screen 0 1280x960x24" $G --path godot --rendering-driver opengl3 -- --no-menu --plan-key-test 2>&1 | grep -E "PLAN KEY|seed [0-9]+:" || rc=1
python3 tools/sim_parity.py out/key_test_inputs.json --out out/sim_key_test.json >/dev/null || rc=1
echo -n "key test Godot vs sim (same picks + SPACE-press QTE scores): "; python3 tools/compare.py out/sim_key_test.json out/key_test_godot.json | tail -1 || rc=1
echo "token:"; head -c 160 out/godot_state.tc2; echo " ..."
exit $rc
