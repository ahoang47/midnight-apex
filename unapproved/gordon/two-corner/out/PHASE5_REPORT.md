# Phase 5 report: B.5b camera stops + B.5a line vs line (Godot, 2026-11-11, Gordon)

UNAPPROVED engine test. Display, UI and camera changes only: scoring, RNG and the sim pin (212eaab) are unchanged.
Source repo state: **ab1c4a1** (`ab1c4a12f69b23ccd74cd8982629b73a4865a127`). Austin approved B.5a and B.5b on 2026-11-11.
Doc references below are to `design/art/art_direction.md` (AD) at ab1c4a1. Frame tools are `art/ui/line_select_cam/{build_lsc,post_lsc,make_tex}.py`
(LSC frames 1-4) and `unapproved/arthur/mockups/line_clash/post_clash.py` (the a1-a3 frames in `art/ui/line_vs_line/`).

## Verification (all PASS, `tools/run_parity.sh`)
- Godot vs sim: 4 single-race sets plus fuzz300 (300 races, 3600 clash values). max_abs_diff 0.0 everywhere (tol 1e-12).
- Dump/load (godot_resumed): 0.0.
- Restart test (menu -> race -> restart, 4 races, 48 values): 0.0.
- Plan the Line key test: 200 seeds, 166 locked by keys. At every step the camera stop equals the pick count, and the B.5a panel RESULT equals the sim's outcomes.
- Live check of the web export on :5176 (`node tools/live_check_godot.mjs`): menu -> entry -> apex -> back -> apex -> exit -> LINE LOCKED -> playback -> result. 10 shots in `out/shots5/live/`.
- Fix rounds this phase: 4 (a GDScript type-inference parse error; the chase cam mirrored for L corners hid the car under the Plan panel; a lamp glow in the lens at the Touge apex stop; the Street apex camera inside the facade). There was also 1 Phase 4 bug: the lamp-glow node creation had been swallowed into a comment.

## What changed
- **B.5b selection (AD:255-263).** Stop 0 (Entry) uses the fixed chase camera on the scrolling straight, with the rival in its lane and the mirror on. Stop 1 (Apex) and stop 2 (Exit) move the camera to the corner, hide both cars and the mirror, and freeze the scroller. Backspace walks back a stop. At lock (or timer auto-fill) the camera returns to the Entry chase pose and the LINE LOCKED banner shows (LSC frame 4) for a hold; then playback runs on the existing authored corner path.
- **B.5a playback (AD:265-270).** The line-vs-line panel replaces the Phase 4 LINE LOCKED strip. It has YOU and RIVAL rows, face up from the start, an amber outline on the column being played, and RESULT WIN/LOSS/TIE per phase as it plays. There is no pause and no clash beat. The panel stays up through RESULT/FINISHED with all three results.
- **New HUD from the frames:** B.5b timer (top left, 17 segments, SET while locked), corner plate (top right: corner name, VIEW/LOCK/PLAY, E/A/X diamonds, CAMERA STOP / PHASE label), and the rear-view mirror re-sized to the frame rect.
- **Touge dressing** now comes from the B.5b frames: fog, road paint, shoulder, guardrail, cedars, ridge and lamps.
- Kept: plain '<Stance> <phase>' option labels, POW/EN/HAN chips, 'none drawn' greying, the navy/teal palette, 640x480 without CRT, menu/restart, the overtake rule (hold through the corner cam, snap at rear chase), the provisional W=1 hook, the sim pin and the parity harness.

## Source table
| Value used | Value | Source |
|---|---|---|
| Stop flow Entry -> Apex -> Exit -> lock -> back to Entry -> playback | | AD:256-262 |
| Rival visible only at Entry; Apex/Exit show geometry only | | AD:257, AD:259-260 |
| Corner plate marks stop E / A / X, top right | rect 476,12-628,96 | AD:262; post_lsc.py:62-73 |
| Chase camera (Entry and lock return) | side 1.4, back 7.6, h 3.1, look ahead 22 / side 3.6 / y -0.9, 25 mm = fov 56.7 | build_lsc.py:245 |
| Mirror camera | 14 mm = fov 46.4, up 1.6, look back 32, y -2.2 | build_lsc.py:246 |
| Mirror rect + frame + REAR VIEW | 224,16,192,64 | post_lsc.py:46-48 |
| Apex stop camera | 19 mm = fov 70.8; outside 10.5 m, h 8; target in 2.5, y -0.8 (arc fractions .4222 / .5333, DERIVED from the hairpin frame) | build_lsc.py:247-249 |
| Exit stop camera | 19 mm; arc .75, out 7.5, h 7.5; target 24 m past exit, in 1.0, y -1.2 | build_lsc.py:250-252 |
| Timer panel, 17 segments, lit/unlit colours, SET when locked | | post_lsc.py:52-58 |
| LINE LOCKED banner (frame 4) | | post_lsc.py:120-131 |
| HUD palette WHITE/DIM/DIMMER/EDGE/EDGE_L/AMBER/AMBER_D/PANEL/INK/SOD | | post_lsc.py:15-16; post_clash.py:15-16 |
| Line-vs-line panel (option A): LINE LOCKED title, cols 241/331/421, amber outline + marker on current col, YOU/RIVAL rows, '>' separators, RESULT row | | post_clash.py:62-85 |
| Result chips WIN (amber) / LOSS (dark, EDGE_L outline) / TIE (EDGE) | | post_clash.py:43-47 |
| Corner plate in playback: PLAY + current phase, diamonds | | post_clash.py:48-54; AD:269 |
| RESULT values | sim `Combat.resolve_stance` (pure); same rule as post_clash.py:20 BEATS | sim @212eaab |
| Bloom (.22, 0), sat 1.05 (already in build) | | post_lsc.py:1, 26-27 |
| Lane width 3.3 m | | build_lsc.py:31 |
| Touge fog #0B172B, 9-78 m (replaces B.3's #2A3236 8-55 m for this test) | | line_select_cam/README.md:27; build_lsc.py:21 |
| Road half 5.0, edge line #BDBDA8 at 4.72 w .13, lane dividers 1.65 w .11 dashed 3/3, shoulder #969692 | | build_lsc.py:136-155 |
| Guardrail h 0.8 at road edge, profile/colours | | build_lsc.py:167-179 |
| Lamps: post d 7.3, head d 5.6, ~49 m spacing (rounded to 48 m to match the 6 m dash cycle, DERIVED) | | build_lsc.py:213-217 |
| Cedars spacing 4.5, h 11-16 out / 9-14 in, out d 9-34, in d 7.2-12, in p .8, w = h/3; texture recipe | | build_lsc.py:221-234; make_tex.py |
| Verge #46543A, ridge #101E32 | | make_tex.py (slope, ridge_far) |

## Placeholders (in no doc or frame; flagged, not invented as canon)
- Camera move time between stops, 0.8 s smoothstep; LINE LOCKED hold 1.2 s. The frames are stills and AD gives no timing.
- Mirror near plane 3.2 m.
- Inside guardrail on the Touge hairpin (the frames show only the outside rail).
- N90 stop poses: the hairpin's arc fractions are reused. There are no 90-degree frames.
- Street stop poses: there are no Street frames. The Touge values are used, with camera-out capped inside the facade (road half-width + sidewalk - 0.5 m).
- Corner plate name '90-DEGREE' for N90. The plate label after playback reads RESULT.
- Gap meter moved to (203,428) and the debug box to (14,64) or (14,106). They have no frame position.
- Props within 5.5 m of a stop camera are hidden (keeps lamp glows out of the lens).

## Conflicts with earlier steers and how they were settled
1. **Scrolling vs a 'fixed chase camera' at Entry.** Scrolling is kept at the Entry stop (B.5b does not forbid it). The Apex/Exit stops are static corner views with the scroller frozen, since they show corner geometry.
2. **Chase cam mirrored per corner direction (Phase 2) vs frame values.** The frame values are used unmirrored for both directions. Mirroring for the L hairpin put the player car under the Plan panel.
3. **Plan panel: Phase 4 Plan the Line vs the frames' PLAYER LINE LOCK selector with HAND counts.** The Phase 4 panel is kept (labels, chips, greying, hand hidden), as the brief asked. The lane/stance labels at the Apex/Exit picks are placeholders per AD:263, so no Apex/Exit lane chevrons are drawn.
4. **Playback camera.** AD B.5a is silent on cameras. The guide §13.3 authored corner path (Phase 2 steer) is kept. Only the unapproved line_clash README mentions apex/exit views.
5. **Two ambers.** The Plan panel keeps lane_chain v5's (255,176,40). The new B.5a/B.5b elements use the frames' (255,184,56).
6. **Turn-in plate, old timer and replay strip (Phase 4).** These are replaced by the B.5b timer, the corner plate and the B.5a panel.
7. **Touge fog/colours (B.3 #2A3236, 8-55 m vs frames #0B172B, 9-78 m).** The approved B.5b frames are used for this test. B.3 itself is not edited. Flag for Arthur if B.3 should follow.

## Outputs
- Shots: `out/shots5/godot_seed20261113_idx/` (corner 1 Touge HP L, corner 2 Street N90) and `out/shots5/godot_seed20261114_idx/`.
- Composites (`python3 tools/phase5_composites.py`): `out/shots5/composites/vs_line_select_cam.png` (Godot vs LSC 1-4), `vs_line_vs_line.png` (Godot vs a1-a3), `before_after_phase4.png`.
- GIFs of one full corner: `out/shots5/corner1_touge_HP_full.gif`, `out/shots5/corner2_street_N90_full.gif`.
- Web export: `out/godot_web` (served on :5176 on the box).

Note for this repo copy: only `out/shots5/composites/` is included (palette-quantised PNGs, about 3.6 MB total). The shot folders, GIFs, live shots and web export stay in the box prototype (`/workspace/prototypes/two-corner/out/`). The Phase 4 composites (`out/shots4/composites/`) were superseded and removed; they remain in git history.
