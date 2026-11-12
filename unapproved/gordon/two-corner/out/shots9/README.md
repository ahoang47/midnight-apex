# shots9 — after-turn countdown, arrow lanes, line-following cars, pass animation, continuous Touge 2-turn track, 2x-grid HUD

Austin playtest 2026-11-11 ~9:58–10:01 PM PT, plus steering 10:22 PM PT ("now the text is really sharp and uncharacteristic of the vibe" → "Draw HUD text pixel-hard on a 2x grid (1280x960)").
Display/flow only. Sim pin 212eaab, scoring and RNG unchanged. `tools/run_parity.sh` PASS, max diff 0.0, key test PASS (`parity.txt`).

Scripted run: `spec/inputs/shots9_pass.json` (seed 3), driven by real Left/Right/Enter steps, auto-continue on.
- Corner 1 (Touge HP L): player SAA vs rival DSA, timing 3. Both exit on lane A (shared). The player passes and takes the open lane. Then it settles.
- Corner 2 (Touge N90 R): player AAS vs rival DDS, timing 3. Both exit on lane S (shared). The rival re-passes.
- `MIN_SEP_OVERLAP 3.300 m`: the smallest lateral gap while the cars are within 4.6 m along the road (no clipping). The Godot result equals the sim (`compare.py` PASS).

Files
- `c1_pass_shared_exit.gif` and `c2_pass_shared_exit.gif`: the pass in each corner (400x300).
- `c1_select_arrows.gif`: Left/Right moving the Entry highlight in on-screen direction.
- `countdown_c1_1280x960.png`: "Press Enter to continue 5" under the B.5a panel, HUD on the 2x grid.
- `composite_before_after_1920x1080_zoom2x.png`: BEFORE = 85d505d smooth HUD (shots8), AFTER = pixel-hard 2x grid. Also `_full.png` and `composite_sizes_*.png` (box only).
- Box only (large): `full_run_2turn.gif` and the clips `c1_*`, `c2_*` at 640/800 px; `gif_frames/` (1280x960, 0.1 s game time); `run/`; `after_live/` (web export at 4 window sizes).

Placeholders (spec/display.json `playback_flow`): continue_s 6.0, lane_ease_s 0.35, blend_before_m 6, blend_after_m 8, pass_u0/u1 0.2/0.9, gap_ease_s 0.12, overlap_full_m 5.5, overlap_clear_m 9.0, min_sep_m 2.6, car_len_m 4.6.
