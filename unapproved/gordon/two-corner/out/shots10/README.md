# shots10: re-pin to f0efecf and three timing QTEs per turn (UNAPPROVED)

Austin approved this at 2026-11-11 10:56 PM PT ("Yes."). The ask was to move the two-corner test onto Barry's latest sim and build the three QTEs.

- **Sim pin:** `f0efecfbc18b495a0ba9df3bf956d8e89acc3477`. Build id: `8063046172` (`godot/spec/build.json`).
- **Run:** `spec/inputs/shots10_qte.json` (seed 3, windowed 1280x960, scripted).
  - Corner 1 QTE: Entry 0.92, Apex **unplayed** (cursor ran past the far edge, scored 0), Exit 0.55.
  - Corner 2 QTE: 0.6 / 0.9 / 0.75.
  - Result matches the sim: max_abs_diff 0.0.
- **Flow per turn:**
  1. Plan the Line (unpaused, with countdown).
  2. LINE LOCKED.
  3. Entry QTE at the Entry chase, Apex QTE at the Apex stop, Exit QTE at the Exit stop, all over the scrolling road.
  4. Camera returns to Entry and playback runs.
  5. Result panel, then "Press Enter to continue" countdown.
- **Zone:** `qte_zone_width(r=1.05, qte_window_mod=0)` = 1.0, times QTE_ZONE_BASE_MS = **800 ms**. The same zone is used for all three phases.
  - Score: max(0, 1 - |e| / 400 ms).
  - Unplayed scores 0 (PHASE_QTE_UNPLAYED).
  - The turn's player_qte is mean_phase_qte of the three.

## Files
- `turn1_three_qtes_apex_unplayed.gif`: 640 px, 10 fps, local copy only. The repo has a 400 px, 5 fps copy at `repo/...`.
- `full_run_2turn.gif`: local only.
- `qte_panel_three_phases_1to1.png`: the QTE panel at 1:1, in sweep and score states for each phase.
- `parity.txt`: full `tools/run_parity.sh` output. Every check passes at 0.0.

## Placeholders (for Arthur; none of these are in his frames)
- QTE sweep timing: lead_ms 700, tail_ms 200, ready_s 0.5, result_hold_s 0.6, key SPACE (`display.json` `qte_sweep`).
- QTE panel layout: title, phase chips with scores, sweep bar (L_SEG_OFF track, L_AMBER zone, ink centre tick, white cursor), "HIT x.xx" / "UNPLAYED 0" text and the "zone N ms" label. It uses B.2a palette names only.
- Plate words "QTE" / "TIMING".
- Cars are hidden at the Apex/Exit QTE stops, and the mirror is on at Entry.
- An early press (before the zone) scores 0 but counts as played.

## Conflicts
- **B.5c (`art_direction.md`, rewritten in 31b2299):** "UI composited after the upscale, drawn sharp at 1280x960". Arthur says Austin may have moved UI text to smooth full-res. This build keeps Austin's 10:22 PM choice to me: pixel-hard text on the 2x grid, unchanged as instructed. Austin needs to decide.
- **godot-build-guide §7.1/7.2:** one continuous QTE per corner, TIMING/MASH by turn type x stance, presses x10. This build uses three timing QTEs scored with the sim's s formula. The guide also still refers to a 1-10 score.
- **B.5b:** "camera returns to Entry and playback runs". The QTEs now sit between the lock and the return.
- **Retired:** the PROVISIONAL W=1 hook, because clash_progress at f0efecf has no knot window.
- **Old tokens:** TC1 (builds up to 4322b31, sim 212eaab) replays on that build only. TC2 records sim + build.
