# Two-corner engine test (Godot 4.6.3)

> **UNAPPROVED.** This is the two-corner engine test, with provisional numbers. Phase 5 UI/camera follows AD B.5a/B.5b at **ab1c4a1**. It is the one exception to the combat freeze. The sim is pinned at **212eaab** (`212eaab99282fbc1c6fd5a9fc50048445ae01716`). The palette is Arthur's B.2a, committed at **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`).

> **2026-11-11: Three.js dropped (Austin).** The Godot build is the only one worked on and tested; parity is Godot vs the pinned sim.
> Notes below that mention `threejs/` are historical; that tree is not in this copy.

This copy lives at `unapproved/gordon/two-corner/` in the repo (Austin's 2026-11-11 directive: unapproved work that other bots need to reference goes in `unapproved/<owner>/`). The original `_pin/` worktree (sim at 212eaab), `threejs/`, the Godot web export, and the rest of `out/` are not included here. Key composites are under `out/shots5/composites/` (the Phase 4 composites were superseded and removed; they are in git history).

Tools that import the pinned sim (`tools/sim_parity.py`, `tools/check_driver_vs_run_match.py`, `spec/gen_constants.py`) look for `_pin/sim`. To re-run them, point those tools at a checkout of `212eaab` — do not use this branch's live `sim/`, which has moved on. `spec/gen_art.py` also reads the logo from `_pin/art/logo/final/`. `spec/gen_constants.py` still writes a Three.js constants file if `threejs/src/core/` exists.

## Layout
- `spec/gen_constants.py` imports the pinned `equations.py` and writes `godot/scripts/sim_constants.gd` and
  `threejs/src/core/simConstants.js`. No value is typed by hand. Each engine self-checks the IEEE-754 bits of every float.
- `spec/race_config.json`: corners (Touge HP L, Street N90 R) and stats by constant name (Balanced builds from
  `simulate_win_rate`, opp_total = `SABINE_BUDGET`, r = `LADDER_R[6]` crew boss = 1.05, so 105/105/105 vs 100/100/100).
  Base stats only: no mods, parts or loadouts.
- `spec/display.json`: DISPLAY-ONLY placeholders (visual-gap cap, road, camera, mirror, QTE needle).
- `spec/inputs/*.json`: scripted inputs `{seed, corners:[{pick:[hand idx...], timing:1..10}]}`. Fewer than 3 picks means the timer ran out, and the line is auto-filled.
- `tools/sim_parity.py`: the real pinned sim functions (`pick_line`, `draw_weighted_hand`, `resolve_turn`) in `run_match` draw order.
  `tools/check_driver_vs_run_match.py` proves the order matches `run_match`. `tools/compare.py` and `tools/run_parity.sh` check the engines against the sim.
- RNG: CPython's `random.Random` (MT19937, `random()`, `choices` bisect) is ported exactly to JS and GDScript, so there is no pre-drawn stream.

## Run
- Parity (Godot vs sim, dump/load, restart test, Plan the Line key test): `tools/run_parity.sh`
- Restart test (Godot game loop): `tools/run_restart_test.sh`
- Screenshots + frame sequences (Godot): `tools/run_shots.sh [inputs-name] [outroot=out/shots5]`
- Live check of the web export on :5176: `node tools/live_check_godot.mjs` (writes `out/shots5/live/` relative to this directory). The web export and the Playwright install from `threejs/node_modules` are not in this copy, so this script is noted only.
- Godot, play (from this directory): `/workspace/tools/godot --path godot`
  - from the repo root: `/workspace/tools/godot --path unapproved/gordon/two-corner/godot`
  - add `--rendering-driver opengl3` on the box
  - user args: `-- --seed N` (prefills the menu seed), `--no-menu`, `--script-inputs res://spec/X.json --shots DIR` (skips the menu)
- Godot, headless: `/workspace/tools/godot --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/X.json --out f.json [--dump-after 0 --dump-to s.tc1 | --load s.tc1]`
- Godot web export: `out/godot_web/` (served at http://127.0.0.1:5176/)
- Three.js dev server: `cd threejs && npm run dev`, which serves http://127.0.0.1:5174/
  - query params: `?seed=N` (prefills the menu seed), `?menu=0` (straight into a race), `?script=X.json` (harness; skips the menu)
  - production build: `threejs/dist/` (`npm run build`), served by `npm run preview` at :5175
- Three.js headless: `cd threejs && node headless/run_race.mjs ../spec/inputs/X.json [--out f] [--dump-after 0 --dump-to s.tc1 | --load s.tc1]`
- Keys:
  - Main menu: Up/Down select, Enter confirm; on SEED, 0-9 type and Backspace delete (empty = random seed). QUIT is Godot desktop only
  - Finish screen: 1 restart same seed, 2 new race (random seed), 3 main menu (or Left/Right + Enter)
  - Plan the Line (selection, at the B.5b camera stops): Up/Down choose the option for the current phase (Left/Right also work on ENTRY), Enter sets it and moves to
    the next phase (Enter on EXIT locks the line), Backspace goes back one phase. Enter on the result = next corner / finish.
    (Hidden legacy: 1-6 still pick a hand index directly.)
  - Space stops the timing needle
  - F9 dumps a TC1 token (clipboard + console / user://last_state.tc1), F10 loads one (clipboard in Godot, prompt in the browser)

## State token
`TC1:<git7>:<base64url(json)>:<CRC-16/CCITT-FALSE>`. The JSON holds the seed plus `rng_draws` (replay counter), the phase, line, hand, picks, totals and history.
Load reseeds, replays the draws and re-derives the line and hand, so a desync is detected. Tokens work across engines.
Stance letters in `line`, `hand` and `player_line`: `A` = Attack, `S` = **Neutral** (the sim's internal letter for `Stance.NEUTRAL`; shown as NEU), `D` = Defend.

## Phase 2 (display only, parity unchanged): scrolling straight + authored corner camera
- STRAIGHT (whole selection timer): StraightRoad strip mesh (road/verge/barrier textures from spec/gen_textures.py) scrolled by UV offset
  via the guide §14.2 RoadScroller (`scroll_speed` 0.05, transition_to_corner 1.5 for 0.5 s then 0.6 — GUIDE values in display.json road_scroller).
  Metres-per-UV (road_uv_length_m 500 → 25 m/s), tiles, lamp spacing, wheel cap, bob are PLACEHOLDERS. Lamps stream past; wheels spin; identical body bob.
- Corner: same scroller on the CornerRoad. Camera: §12.2 side-offset transition, then an authored path per turn type (Godot Path3D/PathFollow3D,
  Three.js CatmullRomCurve3): HP tight inside line, N90 hard cut to the apex. Rig modes BCH / BCL / BCR shown in the HUD. Keyframes are PLACEHOLDERS (display.json corner_cams).
- Overtakes: AUSTIN OVERRIDE of guide §13.2 step 9a — no swing_overtake(). Cars hold position through the corner camera and snap to the
  new visual-gap positions when the camera reaches the rear chase lock (END_TURN swing back, transition_to_straight_s).
- Frame sequences: scripted runs write seq_select*/seq_corner*/seq_snap* PNGs + frames_640.json; `python3 tools/frame_compare.py out/shots3` makes GIFs and numbers.
- Live check: `URL=... TAG=... node threejs/headless/live_check.mjs`.

## Phase 3 (display/art only, parity unchanged): Arthur's art direction
Sources (pin 212eaab): `design/art/art_direction.md` (Part A binding for cars, Part B [VIBE]/[PROPOSAL]), the psx-night-street-art-direction skill,
`art/README.md`, `art/mood/*`, game-ready `assets/cars/*`. Nathaniel's story/world files were NOT read or applied (Austin's scope change).
- ONE look only: 640x480 internal (A.5), RGB555 + 4x4 Bayer dither, nearest upscale to 1280x960. CRT filter, the low-res mode and the C/R toggles were removed (Austin).
  PSX vertex snapping and affine texturing stay.
- `spec/gen_art.py` writes every stand-in texture to `spec/art/` (copied to `threejs/public/art/`, `godot/art/`): district road strips with the
  stepped 4-band sodium pools painted in (B.1), verge, guardrail, cedar cards, ridge/skyline bands, painted sky strips (fog-matched horizon),
  facades (pre-lit windows, no lettering), blank neon panels, cut-out props, glow sprites, blob shadow, headlight throw, 6x9 bitmap font, 9-slice panel.
  `assets/env`, `assets/ui`, `assets/fonts` are empty at the pin, so ALL environment/HUD art is a stand-in.
- `spec/display.json` `districts` (B.3 Touge / Urban Street palettes, fog ranges, lamp spacing) and `car_shading` (A.4/A.8 + per-car README values).
  Each value carries `_source`; PLACEHOLDER marks anything the doc does not give.
- Cars: A.8 faked-shine shader per material (paint/softtop/glass values from the MX5 README; S2000 uses A.8 defaults), MX5 FX_LampGlow quads shown
  additively, S2000 stand-in lamp glows, blob shadow + headlight-throw decals.
- HUD: drawn at 640x480 with the bitmap font and 9-slice panels (Three.js `src/hud.js`, Godot `scripts/hud.gd`).
- Composites: `python3 tools/art_composites.py out/before_art_shots out/shots3 _pin out/art_composites`. Those source trees are not in this copy.

## Main menu + restart (Austin 2026-11-10, display/flow only)
- Main menu: approved V3 logo (`art/logo/final/v3_white_on_black.png`, downsampled to 384 px with hard 1-bit alpha by `spec/gen_art.py` -> `logo_v3.png`),
  START RACE, SEED (typed, or RANDOM), QUIT (Godot desktop only). The scrolling Touge straight is the backdrop; its timer never runs.
- Finish screen: RESTART SAME SEED / NEW RACE / MAIN MENU. Every start builds a fresh RaceCore (fresh MT19937 from the seed) and resets every display-side race variable.
  Random seeds come from Math.random / randi (display side), never the sim RNG.
- Restart test: `spec/inputs/restart_test.json` = 4 races chained by `restart: [same, new, menu]`, driven through the same key handler the player uses.
  Each restart asserts state == cold start, and all 4 races are compared with the pinned sim (`tools/run_restart_test.sh`).
- Headless runners (`headless_run.gd`, `run_race.mjs`) and scripted shots never show the menu.

## Phase 4 (2026-11-11, display/art/UI only, parity unchanged): Arthur's palette + Plan the Line
- Palette: art_direction.md **B.2a**, committed at origin **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`), values copied from
  `/workspace/mockups/tones/work/tones.py` preset `blend50` into `spec/display.json` `palette` (fog #0B172B, zenith #010408, no city glow,
  ambient #5575A0 x0.8, every lamp #F0C894 x0.85, 3-step pools x0.09, bloom 0.22 / threshold 0 as a glow-only pass, saturation 1.05).
  `palette.calib` holds display calibration gains (not doc values) that scale the mockup light terms onto our stand-in textures.
- Stance UI colours (Austin): ATK #E8282C, DEF #2CB84A, NEU #F0C828 with dark text on yellow (`display.json` `stance_ui`).
- Third stance is **Neutral / NEU** everywhere player-facing (Q6, Austin). The sim keeps the internal letter `S` (combat.gd, race_core.gd unchanged).
- Filtering (Q4): world textures smooth (linear; the car albedo uses mipmaps per the A.8 shader sketch), no other mips. HUD stays crisp:
  NimbusSansNarrow Bold / BoldOblique at 1-bit (the mockups' fonts, `godot/fonts/README.md`), 640x480 nearest upscale (A.5).
- Plan the Line (Arthur's `/workspace/mockups/lane_chain/v5`): the 6-card hand is hidden and only decides which options are available.
  PLAN THE LINE panel (breadcrumb ENTRY > APEX > EXIT, options '<Stance> <phase>' with POW/EN/HAN chips, '<TAG> · none drawn' greying),
  ENTRY strip (OUT = Attack, MID = Neutral, IN = Defend, same lane rule as the tell), turn-in plate + 16-segment timer under the mirror,
  player lane chevrons over the road, 'Line locks at turn-in'. Corner playback: LINE LOCKED strip with the current phase in amber,
  then per-clash results in the same strip. Gap meter moved to the top right. Scripted inputs are unchanged (`pick` = hand indices).
- Shots: `out/shots4/`; composites (`python3 tools/phase4_composites.py`, paths are relative to this directory): `out/shots4/composites/`. Those Phase 4 composites were removed from this copy in Phase 5 (superseded; see git history).

## Phase 5 (2026-11-11, display/UI/camera only, parity unchanged): B.5b camera stops + B.5a line vs line
Sources: `design/art/art_direction.md` at **ab1c4a1** (`ab1c4a12f69b23ccd74cd8982629b73a4865a127`) B.5b (lines 255-263) and B.5a (265-270), both approved by Austin
2026-11-11; reference frames `art/ui/line_select_cam/` (with `build_lsc.py`, `post_lsc.py`, `make_tex.py`) and `art/ui/line_vs_line/` (built by
`unapproved/arthur/mockups/line_clash/post_clash.py`, option A). Full source table: `out/PHASE5_REPORT.md`.
- **Selection walks the corner (B.5b).** Entry: the fixed chase camera (frame values, build_lsc.py:245) on the scrolling straight, rival in its Entry lane,
  rear-view mirror on. Apex: the camera moves to a raised view from the corner's outside (build_lsc.py:247-249). Exit: the camera moves to the exit
  (build_lsc.py:250-252). At the Apex and Exit stops the corner is shown with no cars and no mirror, and the straight stops scrolling. Backspace walks
  back a stop. When the line locks (Enter on Exit, or the 12 s timer auto-fills), the camera returns to Entry with the LINE LOCKED banner (frame 4),
  then playback runs. The B.5b timer (17 segments) sits top left; the corner plate (top right) marks the stop E / A / X.
- **Playback (B.5a).** The Phase 4 LINE LOCKED strip is replaced by the line-vs-line panel: YOU and RIVAL rows, both full lines face up from the start
  (no flips), amber outline on the column being played, RESULT (WIN / LOSS / TIE) filling in per phase. No pause or clash beats. The corner plate shows
  the phase being played. RESULT is computed with the sim's own pure `resolve_stance` (no RNG), and the key test checks it equals the sim's outcomes.
- **Kept:** Plan the Line option labels ('<Stance> <phase>'), POW/EN/HAN chips, 'none drawn' greying, the navy/teal palette, 640x480 without CRT,
  menu and restart, the overtake rule (cars hold through the corner camera and snap when it returns to rear chase), the provisional W=1 hook, the sim pin
  and the parity harness. The playback camera is still the guide §13.3 authored path.
- **Touge dressing** now comes from the approved B.5b Touge frames (road paint, guardrail, cedars, ridge, lamps, fog 9-78 m); see the report.
- Shots: `out/shots5/` on the box prototype (GIFs `corner1_touge_HP_full.gif`, `corner2_street_N90_full.gif`). This copy keeps only `out/shots5/composites/` (`vs_line_select_cam.png`, `vs_line_vs_line.png`, `before_after_phase4.png`, palette-quantised to fit the size budget); `python3 tools/phase5_composites.py` needs the full frame sets.
