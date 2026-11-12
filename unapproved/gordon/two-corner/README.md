# Two-corner engine test (Godot 4.6.3)

> **UNAPPROVED.** This is the two-corner engine test, with provisional numbers. Phase 5 UI/camera follows AD B.5a/B.5b at **ab1c4a1**. It is the one exception to the combat freeze. The sim is pinned at **f0efecf** (`f0efecfbc18b495a0ba9df3bf956d8e89acc3477`, Barry's per-phase QTE averaging on the qte-v1 visible zone; re-pinned from 212eaab in shots10, Austin approved 2026-11-11 10:56 PM PT). The palette is Arthur's B.2a, committed at **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`).

> **2026-11-11: Three.js dropped (Austin).** The Godot build is the only one worked on and tested; parity is Godot vs the pinned sim.
> Notes below that mention `threejs/` are historical; that tree is not in this copy.

This copy lives at `unapproved/gordon/two-corner/` in the repo (Austin's 2026-11-11 directive: unapproved work that other bots need to reference goes in `unapproved/<owner>/`). The original `_pin/` worktree (sim at f0efecf), `threejs/`, the Godot web export, and the rest of `out/` are not included here. Key composites are under `out/shots5/composites/` (the Phase 4 composites were superseded and removed; they are in git history).

Tools that import the pinned sim (`tools/sim_parity.py`, `tools/check_driver_vs_run_match.py`, `spec/gen_constants.py`) look for `_pin/sim`. To re-run them, point those tools at a checkout of `f0efecf` (`git worktree add _pin f0efecf`); do not use this branch's live `sim/`, which may move on. `spec/gen_art.py` also reads the logo from `_pin/art/logo/final/`. `spec/gen_constants.py` no longer writes the Three.js constants file (shots10).

## Layout
- `spec/gen_constants.py` imports the pinned `equations.py` and writes `godot/scripts/sim_constants.gd`, citing `equations.py:<line>`
  above every constant. No value is typed by hand. Long floats are written as an exact mantissa / 2^k (Godot's decimal parser is not
  correctly rounded); `headless_run.gd` self-checks the IEEE-754 bits of every float.
- `spec/race_config.json`: corners (Touge HP L, Touge N90 R; corner 2 was Street N90 R until shots9 — one continuous Touge road, Austin 2026-11-11) and stats by constant name (Balanced builds from
  `simulate_win_rate`, opp_total = `SABINE_BUDGET`, r = `LADDER_R[6]` crew boss = 1.05, so 105/105/105 vs 100/100/100).
  Base stats only: no mods, parts or loadouts.
- `spec/display.json`: DISPLAY-ONLY placeholders (visual-gap cap, road, camera, mirror, QTE sweep).
- `spec/inputs/*.json`: scripted inputs `{seed, corners:[{pick:[hand idx...], qte:[entry, apex, exit]}]}`. Each phase score is null
  (unplayed = 0), a number in [0, 1], or `"0x<16 hex>"` IEEE-754 bits. Fewer than 3 picks means the timer ran out, and the line is auto-filled.
- `tools/sim_parity.py`: the real pinned sim functions (`pick_line`, `draw_weighted_hand`, `resolve_turn`) in `run_match` draw order.
  `tools/check_driver_vs_run_match.py` proves the order matches `run_match`. `tools/compare.py` and `tools/run_parity.sh` check the engines against the sim.
- RNG: CPython's `random.Random` (MT19937, `random()`, `choices` bisect) is ported exactly to JS and GDScript, so there is no pre-drawn stream.

## Run
- Parity (qte-v1 function bits, Godot vs sim, dump/load, restart test, Plan the Line + QTE key test vs sim): `tools/run_parity.sh`
- Restart test (Godot game loop): `tools/run_restart_test.sh`
- Screenshots + frame sequences (Godot): `tools/run_shots.sh [inputs-name] [outroot=out/shots5]`
- Live check of the web export on :5176: `node tools/live_check_godot.mjs` (writes `out/shots5/live/` relative to this directory). The web export and the Playwright install from `threejs/node_modules` are not in this copy, so this script is noted only.
- Godot, play (from this directory): `/workspace/tools/godot --path godot`
  - from the repo root: `/workspace/tools/godot --path unapproved/gordon/two-corner/godot`
  - add `--rendering-driver opengl3` on the box
  - user args: `-- --seed N` (prefills the menu seed), `--no-menu`, `--script-inputs res://spec/X.json --shots DIR` (skips the menu)
- Godot, headless: `/workspace/tools/godot --headless --path godot --script res://scripts/headless_run.gd -- ../spec/inputs/X.json --out f.json [--dump-after 0 --dump-to s.tc2 | --load s.tc2]`
- Godot web export: `out/godot_web/` (served at http://127.0.0.1:5176/)
- Three.js dev server: `cd threejs && npm run dev`, which serves http://127.0.0.1:5174/
  - query params: `?seed=N` (prefills the menu seed), `?menu=0` (straight into a race), `?script=X.json` (harness; skips the menu)
  - production build: `threejs/dist/` (`npm run build`), served by `npm run preview` at :5175
- Three.js headless: `cd threejs && node headless/run_race.mjs ../spec/inputs/X.json [--out f] [--dump-after 0 --dump-to s.tc1 | --load s.tc1]`
- Keys:
  - Main menu: Up/Down select, Enter confirm; on SEED, 0-9 type and Backspace delete (empty = random seed). QUIT is Godot desktop only
  - Finish screen: 1 restart same seed, 2 new race (random seed), 3 main menu (or Left/Right + Enter)
  - Plan the Line (selection, at the B.5b camera stops): Up/Down choose the option for the current phase (on ENTRY, Left/Right move the lane the way the road shows it: a left corner has IN on the left, a right corner OUT; no wrap), Enter sets it and moves to
    the next phase (Enter on EXIT locks the line), Backspace goes back one phase. After each turn: 'Press Enter to continue' with a countdown that auto-continues (playback_flow.continue_s, PLACEHOLDER).
    (Hidden legacy: 1-6 still pick a hand index directly.)
  - QTE (after LINE LOCKED, at the Entry, Apex and Exit camera stops): Space when the cursor is in the amber zone; no press before
    the cursor passes the zone's far edge = unplayed = 0
  - F9 dumps a TC2 token (clipboard + console / user://last_state.tc1, file name unchanged), F10 loads one from the clipboard

## State token
Since shots10: `TC2:<sim7>:<build10>:<base64url(json)>:<CRC-16/CCITT-FALSE>`, spec in `unapproved/gordon/playtest-state-spec.md` §0.5.
It records the sim pin and the build id (`tools/stamp_build.py` -> `godot/spec/build.json`), the seed, and every completed turn's picks and
exact phase scores (IEEE-754 bits). Load replays them through the core and checks rng draws and total bits ("replay desync" otherwise).
`python3 tools/decode_token.py '<token>'` decodes TC2 and TC1. TC1 tokens (sim 212eaab, builds up to 4322b31) replay on that build only.
Stance letters in `line`, `hand` and `player_line`: `A` = Attack, `S` = **Neutral** (the sim's internal letter for `Stance.NEUTRAL`; shown as NEU), `D` = Defend.

## Phase 2 (display only, parity unchanged): scrolling straight + authored corner camera
- STRAIGHT (whole selection timer): StraightRoad strip mesh (road/verge/barrier textures from spec/gen_textures.py) scrolled by UV offset
  via the guide §14.2 RoadScroller (`scroll_speed` 0.05, transition_to_corner 1.5 for 0.5 s then 0.6 — GUIDE values in display.json road_scroller).
  Metres-per-UV (road_uv_length_m 500 → 25 m/s), tiles, lamp spacing, wheel cap, bob are PLACEHOLDERS. Lamps stream past; wheels spin; identical body bob.
- Corner: same scroller on the CornerRoad. Camera: §12.2 side-offset transition, then an authored path per turn type (Godot Path3D/PathFollow3D,
  Three.js CatmullRomCurve3): HP tight inside line, N90 hard cut to the apex. Rig modes BCH / BCL / BCR shown in the HUD. Keyframes are PLACEHOLDERS (display.json corner_cams).
- Overtakes (since shots9, Austin 2026-11-11 ~10 PM PT, replaces the hold-then-snap rule): "if a pass occurs, it is visually shown during the
  dynamic play... if the exit lane is the same for both cars and one goes for a pass, then the passing car should go to an open lane for the
  pass animation, and then move into the position it needs to play for the next turn." See the shots9 section below.
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
- Stance UI colours (Austin, swapped 2026-11-11): ATK/POW #2CB84A (green), DEF/EN #E8282C (red), NEU/HAN #F0C828 (yellow) with dark text on yellow (`display.json` `stance_ui`).
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

## shots9 (display/flow only, scoring/RNG/pin unchanged): Austin's playtest, 2026-11-11 ~9:58-10:22 PM PT
- **After-turn pause:** once the RESULT row fills in, 'Press Enter to continue  N' counts down and auto-continues ("That should have a time limit").
  No pause was added to selection or playback (B.5a). Length `playback_flow.continue_s` = 6 s, PLACEHOLDER awaiting Desmond/Austin.
- **Entry lane with Left/Right:** on-screen direction (left corner: IN MID OUT left to right; right corner: OUT MID IN). The bottom-left ENTRY strip
  lists the lanes in that same on-screen order, so it is mirrored on left corners (post_v5.py:98 draws OUT MID IN). The player car eases into
  the highlighted lane while you choose.
- **Cars drive their lines:** both cars go Entry lane -> Apex lane (mid-arc) -> Exit lane, smoothly (`playback_flow.blend_*`, PLACEHOLDER).
  Apex/Exit lanes use the Entry lane rule (A outside, S centre, D inside), as the B.5b frames' labels do; no Apex/Exit lane mapping is approved.
  The chase camera stays on the road centre line (B.5b framing), so the car visibly moves across lanes.
- **Infinite scroll at every stop:** the road also scrolls at the Apex and Exit stops (Phase 5 kept it to Entry only). `hold_stop` in main.gd is a
  hook to hold the Apex stop pose with the road scrolling while a QTE plays later (not used by the flow yet).
- **Passes during playback:** the visual gap moves from the pre-turn value to the post-turn value across `pass_u0..pass_u1` of the playback
  (lead/gap still from the sim: `_preview_lead` calls the same pure `Combat.resolve_turn` the core uses, for the score in play). If the drawn order flips
  and the lines share a lane while the cars overlap, the passer takes the open lane, overtakes, and settles back onto its line. No-clip check: the
  scripted run prints `MIN_SEP_OVERLAP` (lateral gap while the cars are within `car_len_m` along the road).
- **One continuous Touge road:** straight 45, corner 1 (HP L), join 47 (= 10 + 45 - 8, so corner 1's playback ends exactly where corner 2's selection
  starts), corner 2 (N90 R), exit 30 (`scripts/course.gd`). Radius/angle stay the `road.by_code` PLACEHOLDERS. Corner 2 now uses the sim's Touge N90
  line set (`LINE_SET_C.touge.N90` DSA/DDS/DSS instead of Street's SSA/SDS/SSS), so the rival's corner-2 lines differ from before for the same seed.
  The Touge dressing is one-sided (cedars/lamps on the right of travel), so on corner 2 (a right turn) they sit on its inside, unlike the B.5b frames.
- **HUD on a 2x pixel grid (Austin 22:21: "now the text is really sharp and uncharacteristic of the vibe"; he chose "Draw HUD text pixel-hard on a
  2x grid (1280x960)"):** the HUD (640x480 design units) is drawn into a 1280x960 SubViewport at x2. Text is rasterised at size x2, 1-bit (no AA,
  no subpixel), with a 2 px shadow, and the 6x9 bitmap font and panels go up x2 nearest. The project base is 1280x960 with the game at x2. When
  the window fits 1280x960 or more, everything scales by a whole number of that (HUD nearest, world 640x480 at twice that). Below 1280x960 the
  scale is fractional and the HUD layer is shown linear. **Departs from art_direction.md:115/:141/:242 (integer nearest upscale of one 640x480 frame,
  viewport stretch) and the mockups' 1-bit 640x480 text (post_lsc.py:34) for the UI only, at Austin's request; flag for Arthur.**
- Placeholders: all of display.json `playback_flow` (continue_s 6, lane_ease_s 0.35, blend 6/8 m, pass window 0.2-0.9, overlap 5.5/9 m, min_sep 2.6 m).
- Demo input `spec/inputs/shots9_pass.json` (seed 3): both corners share the Exit lane and the drawn order flips in both. Shots in `out/shots9/`.


## shots10 (2026-11-11): re-pin to f0efecf + three timing QTEs per turn (Austin approved 10:56 PM PT: "Yes.")
- **Pin:** `_pin` is now `f0efecfbc18b495a0ba9df3bf956d8e89acc3477` (sim/ is unchanged at origin/proto-build 59f7e6d). Ported to GDScript:
  qte-v1 zone (`qte_zone_width`, `expected_hit_quality` with a bit-exact port of glibc's `erf`, `raw_qte_score`, `qte_sigma_over_a0`
  and the two bisections), `phase_raw_qte`, `mean_phase_qte` (with CPython 3.12+ `sum()` Neumaier compensation so the mean is
  bit-identical), `clash_progress` without the knot window, and `resolve_turn` with `player_qte_phases`. The PROVISIONAL W=1 hook is
  retired: its hidden window no longer exists in clash math. Constants cite `equations.py:<line>` in `sim_constants.gd`.
- **Game:** after LINE LOCKED, one timing QTE at each B.5b camera stop (Entry chase, Apex stop, Exit stop) over the scrolling road, then
  the camera returns to Entry and playback (B.5a) runs. Zone = `qte_zone_width(r, qte_window_mod)` x `QTE_ZONE_BASE_MS`, the same for
  all three. At this race's r = 1.05 that is 1.0 x 800 ms. Press score = max(0, 1 - |e| / (zone/2)) (the s in `expected_hit_quality`'s
  docstring). The cursor passing the far edge = unplayed = 0. The three scores go to `core.submit_qte()`, and `resolve_turn` averages them.
- **Placeholders** (display.json `qte_sweep`): lead_ms 700, tail_ms 200, ready_s 0.5, result_hold_s 0.6, key SPACE. The QTE panel
  layout, labels and the plate's 'QTE' / 'TIMING' words have no Arthur frame.
- **Parity:** `tools/qte_fn_test.py` checks 5,757 values bit for bit. Inputs are per-phase. fuzz300 mixes null / 0 / 1 / decimals /
  k/1024 / raw bits. The 200-seed key test now plays the three QTEs by Space through the real input path and sends the same picks and
  scores to the sim. Shots: `out/shots10/`.
