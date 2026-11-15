# Progress checkpoint (Barry draft, 2026-11-13)
- sweep_main.json: live engine, 15 stand-in tracks, N=300/track/style, r 0.94..1.24 step 0.01, 10/20/30 turns.
- drift_T3.json/.txt: current live constants, Touge hard cell = T3_Usui_Esses (worst Touge track). drift_T1.*: hard = T1_Akina.
- fit_ladder.json: ladder fit with provisional boss r street 1.043 / wangan 1.040 / touge 1.069 (T3 hard). Criteria 1-8 pass.
- Finale F2 r* 1.040 -> cap rounds to L76, arrival r 1.0366 (60/60 28.5). r* 1.041-1.043 -> L77.
- confirm30 sweep (N=1500, 30-turn, r 1.034..1.072) running -> sweep_confirm30.json, for boss/finale cells.
- Remaining: boss pick from confirm, arc fit, RESULTS.md, proposed_constants.json.
- DONE 17:5x: RESULTS.md + proposed_constants.json written (default = fit_ladder_v3 + finale 1.070/1.041/1.044/1.070). fit_ladder.json/v2 are superseded provisional fits.
## Round 2 (Austin pick 18:53: bosses on hardest track per district)
- point_confirm_hardest.json: W3 1.044-1.055, T3 1.073-1.077 (N=3000).
- Picks: Wangan boss 1.055 on W3 (39.7/90.7); F2 1.058 (cap L79, W3 grid N1500 41.7/92.5); F1/F4 1.075 (T3 34.7/94.7, caps L64/L115).
- econ_patch HARD_WANGAN env adds W3 30-turn hard cell; oracle ORACLE_POINTS env merges point checks.
- aero stage1 running -> aero_best_splits_live.json; then STAGE=2 -> aero_live.json
- hardest.json/.txt: fit_ladder_hardest + finale 1.075/1.058/1.044/1.075, caps L64/79/94/115, arc pass. aero stage2 running (N=2000).
- round2 DONE 19:3x: RESULTS.md (round2), proposed_constants.json (hardest). Round1 -> RESULTS_round1.md
