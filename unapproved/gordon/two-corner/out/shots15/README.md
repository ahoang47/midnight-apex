# shots15 — HUD plate grain, bevel, heavier type, and stat-under-position chips

Austin (12:55 PM PT, 2026-11-12): "I like his HUD look." Later the same day: every row uses IN/MID/OUT + stat, then "The stat should be framed under the position text" (Arthur 769f073). Grain/bevel/fonts are ported from Arthur's `hud_panel.gd` / `plan_panel.gd`. UI is drawn pixel-hard on the 1280×960 HUD layer, after the 640×480 dither pass. Grain is only on HUD plates, never on the 3D or the road.

- `entry_*_1280.png`, `apex_*_1280.png`, `exit_*_1280.png` — selection, hover on each stance, seed 20261114. Unframed OUT / MID / IN over a small framed POW / HAN / EN stat box.
- `exit_qte_1280.png` — Exit QTE during playback.
- `result_1280.png` — RESULT after the first corner (QTEs unplayed in this harness).
- `compare_arthur_vs_gordon.png` — Arthur 769f073 / fb38d45 left, this build right, at half scale (nearest).
