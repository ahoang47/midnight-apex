# shots11: editor scenes + QTEs during playback (UNAPPROVED)

Two changes, both asked for by Austin on 2026-11-12:
1. **Scene refactor** ("I think this is a good chance to work on your workflow for the editor with the two corner scene"). The two-corner test
   is now `main.tscn` plus track, touge_dressing, sky, car (x2), camera_rig and hud scenes. See the README section "Editor workflow".
   No numbers, rules or behaviour changed. With a fixed 1/60 s step, the split build matched the old build pixel for pixel on **73/73 shots and 611/611 GIF frames**.
2. **QTE flow** (Austin: line select is Entry, then a static Apex, then a static Exit; QTEs play during playback, each with a timer; the cars stay at
   that phase with the road scrolling until the timer runs out). The Entry camera and Entry selection screen are unchanged.

- **Run:** `spec/inputs/shots10_qte.json`, the same inputs as shots10 (seed 3; corner 1 QTE 0.92 / unplayed / 0.55, corner 2 0.6 / 0.9 / 0.75), windowed
  1280x960. Result vs the sim: max_abs_diff 0.0.
- **Entry pixel diff** (`entry_pixel_diff.txt`):
  - Corner 1 Entry selection (seq_select0_0..5) vs shots10: 0 differing pixels in all 6 frames.
  - The LINE LOCKED return to Entry is also identical in a fixed-step A/B against the old build.
  - Corner 2 Entry selection has the same camera pose, rig and car positions. Only the road texture phase differs (40 m of scroll), because corner 1's
    playback now includes the QTE holds.
- `side_by_side_shots10_vs_shots11.png`: shots10 | shots11 | diff, for two Entry frames, the now-static Apex stop and the Apex QTE.
- `turn1_full_qte_in_playback.gif` (local, 640 px 10 fps) / `turn1_full_qte_in_playback_400.gif` (repo copy, 400 px 5 fps): all of turn 1, from Entry
  select through the Apex and Exit stops, LINE LOCKED, playback with the Entry / Apex (unplayed) / Exit QTE holds, and the result with its continue countdown.
- `editor_track_tscn.png`: the Godot editor on `track.tscn` (top orthogonal view of the whole continuous Touge road, Track inspector with the
  spec-backed exports). `editor_touge_dressing_tscn.png` and `editor_hud_tscn.png` show the dressing and the HUD Control tree. The only Output errors are the
  box's missing Vulkan surface, which the editor falls back from to OpenGL. They are not project errors.
- `parity.txt`: full `tools/run_parity.sh`.

## Placeholders (no Arthur frame; for Arthur / Austin)
- Hold points = the corner plate's E / A / X marks (turn-in - 6 m, mid-arc, arc end + 6 m).
- Phase timer = lead_ms + QTE_ZONE_BASE_MS + tail_ms (1.7 s), and at least result_hold_s (0.6 s) after the score.
- QTE panel timer text (centre of the title row). The panel sits under the B.5a line-vs-line panel during playback.
- `qte_sweep.ready_s` is unused now.
