# Two-corner engine test (Godot 4.6.3)

> **UNAPPROVED.** This is the two-corner engine test, with provisional numbers. Phase 5 UI/camera follows AD B.5a/B.5b at **ab1c4a1**. It is the one exception to the combat freeze. The sim is pinned at **50928ed** (`50928ed0e268277e50f97a68c7d71151078e976e`, newest proto-build containing Barry's 53267c5 POW/EN/HAN rename and the c3ffc41 QTE rounding; Austin's 2026-11-12 naming rule: backend is POW/EN/HAN, IN/MID/OUT is visual only). The palette is Arthur's B.2a, committed at **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`).

> **2026-11-11: Three.js dropped (Austin).** The Godot build is the only one worked on and tested; parity is Godot vs the pinned sim.
> Notes below that mention `threejs/` are historical; that tree is not in this copy.

This is the working copy at `/workspace/prototypes/two-corner/`. The repo mirror is `unapproved/gordon/two-corner/`. This tree also has the `_pin/` worktree (sim at 50928ed), the historical `threejs/` tree (untouched), and local `out/`.

Tools that import the pinned sim (`tools/sim_parity.py`, `tools/check_driver_vs_run_match.py`, `spec/gen_constants.py`) look for `_pin/sim`. To re-run them, point those tools at a checkout of `50928ed` (`git worktree add _pin 50928ed`); do not use this branch's live `sim/`, which may move on. sim/ is unchanged after 53267c5. `spec/gen_art.py` also reads the logo from `_pin/art/logo/final/`. `spec/gen_constants.py` no longer writes the Three.js constants file (shots10).

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
- Godot scenes (since shots11): `godot/scenes/` holds `main.tscn` plus six sub-scenes; see **Editor workflow** below.

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
  - F9 dumps a TC3 token (clipboard + console / user://last_state.tc1, file name unchanged), F10 loads one from the clipboard

## State token
Since this pass: `TC3:<sim7>:<build10>:<base64url(json)>:<CRC-16/CCITT-FALSE>`, spec in `unapproved/gordon/playtest-state-spec.md` §0.5.
It records the sim pin and the build id (`tools/stamp_build.py` -> `godot/spec/build.json`), the seed, and every completed turn's picks and
exact phase scores (IEEE-754 bits). Load replays them through the core and checks rng draws and total bits ("replay desync" otherwise).
`python3 tools/decode_token.py '<token>'` decodes TC3, and flags older TC2/TC1 as outdated tokens. TC2 (A/S/D letters) and TC1 (sim 212eaab) must be replayed on the build that made them.
Stance letters in `line`, `hand` and `player_line`: `P` = POW, `E` = EN, `H` = HAN. On screen the lane is written **OUT (POW)**, **MID (HAN)**, **IN (EN)**.

## Phase 2 (display only, parity unchanged): scrolling straight + authored corner camera
- STRAIGHT (whole selection timer): StraightRoad strip mesh (road/verge/barrier textures from spec/gen_textures.py) scrolled by UV offset
  via the guide §14.2 RoadScroller (`scroll_speed` 0.05, transition_to_corner 1.5 for 0.5 s then 0.6 — GUIDE values in display.json road_scroller).
  Metres-per-UV (road_uv_length_m 500 → 25 m/s), tiles, lamp spacing, wheel cap, bob are PLACEHOLDERS. Lamps stream past; wheels spin; identical body bob.
- Corner: same scroller on the CornerRoad. Camera: §12.2 side-offset transition, then an authored path per turn type (Godot Path3D/PathFollow3D,
  Three.js CatmullRomCurve3): HP tight inside line, N90 hard cut to the apex. Rig modes BCH / BCL / BCR shown in the HUD. Keyframes are PLACEHOLDERS (display.json corner_cams).
- Overtakes (since shots9, Austin 2026-11-11 ~10 PM PT, replaces the hold-then-snap rule; timing updated shots12, Austin 2026-11-12:
  "Order only changes after exit QTE"): "if a pass occurs, it is visually shown during the dynamic play... if the exit lane is the same for
  both cars and one goes for a pass, then the passing car should go to an open lane for the pass animation, and then move into the position
  it needs to play for the next turn." The gap holds until the Exit QTE finishes, then eases over `pass_after_exit_s`. See the shots9 section below.
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
- Stance UI colours (Austin, swapped 2026-11-11; names as of 2026-11-12): POW #2CB84A (green), EN #E8282C (red), HAN #F0C828 (yellow) with dark text on yellow (`display.json` `stance_ui`).
- Backend, data, tokens and docs name stances by stat only (POW / EN / HAN, letters P / E / H). IN / MID / OUT is the on-screen lane (OUT = POW, MID = HAN, IN = EN), written **OUT (POW)** on the HUD.
- Filtering (Q4): world textures smooth (linear; the car albedo uses mipmaps per the A.8 shader sketch), no other mips. HUD stays crisp:
  NimbusSansNarrow Bold / BoldOblique at 1-bit (the mockups' fonts, `godot/fonts/README.md`), 640x480 nearest upscale (A.5).
- Plan the Line (Arthur's `/workspace/mockups/lane_chain/v5`): the 6-card hand is hidden and only decides which options are available.
  PLAN THE LINE panel (breadcrumb ENTRY > APEX > EXIT, options '<Stance> <phase>' with POW/EN/HAN chips, '<TAG> · none drawn' greying),
  ENTRY strip (OUT (POW), MID (HAN), IN (EN)), turn-in plate + 16-segment timer under the mirror,
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

## B.5d line preview (2026-11-12, display only, parity unchanged)

Austin approved Arthur's line-preview mockup (relayed by Arthur, commit **9a83828**) as the build reference. Purely visual; no gameplay or sim change.

- Flat chevrons on the road along the chained Entry → Apex → Exit line, pointing in the direction of travel, no glow. Colours are the stance UI set: POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`. Hovered segment at full strength; follow-on segments solid at 0.66 brightness and slightly thinner (Arthur pass 4 measures, `spec/display.json` `line_preview`, marked PLACEHOLDER). Scripts `godot/scripts/line_chevrons.gd` and the chevron shader/art are copied from Arthur's mockup and adapted here (credit in the script).
- Bend mapping is Arthur's, recorded as PLACEHOLDER: POW holds the outer line (−1 × lane width), HAN mid-lane (0), EN cuts to the inner line (+1 × full lane width, corner-relative via `track.gd`). Implied follow-on is Apex EN, Exit POW. Each segment starts where the previous one ends. Entry stays in the chosen Entry lane.
- One combined PLAN THE LINE panel at the bottom right (narrower so it clears the car). Lane chips read `OUT · POW`, `MID · HAN`, `IN · EN`. The race split bar sits under the rear-view mirror. Entry camera, Entry select framing, and Exit camera are unchanged.
- Known leftover: from the Entry chase cam the follow-on line vanishes over the crest (`_in_straight()` hides the hook mesh). Left as-is; same gap is in the mockup.
- Shots: `out/shots14/` (Entry / Apex / Exit × each stance hover, 640 and 1280; `compare_arthur_vs_gordon.png`). Shot harness: `--line-preview-shots <dir>` (seed 20261114 so every stance can be hovered at Exit).

## HUD look (2026-11-12, display only, parity unchanged)

Austin (12:55 PM PT): "I like his HUD look." Plate grain, bevel and heavier titles are ported from Arthur's line-preview `hud_panel.gd` (`plate_finish`) and fonts. Grain is drawn only on HUD plates, on the 1280×960 HUD layer after the 640×480 dither pass — never on the 3D or the road. Fonts: Nimbus Sans Narrow Bold / Bold Oblique, Nimbus Sans Bold (URW++ base35, AGPL-3 with Font exception), and Archivo Black (SIL OFL 1.1); licenses sit next to the files in `godot/fonts/`. Text is pixel-hard (no AA, hinting off, nearest). Colours unchanged. Every PLAN THE LINE row uses unframed OUT / MID / IN over a small framed POW / HAN / EN stat box (Austin via Arthur, 769f073). `entry_strip.gd` inlines those labels so Arthur's `run.sh` can symlink it onto his `hud_panel.gd`. Debug box keeps the 6x9 bitmap so F9/F10 and the seed stay readable. Cameras and gameplay unchanged. Shots: `out/shots15/`.


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
- **Passes after the Exit QTE (shots12, Austin 2026-11-12: "Order only changes after exit QTE"):** the visual gap holds the pre-turn value
  until the Exit QTE finishes, then moves to the post-turn value over `playback_flow.pass_after_exit_s` (PLACEHOLDER 2.5 s, the same length as the
  old `pass_u0..pass_u1` window). Leftover playback after the Exit hold is only ~0.16 s (HP) / ~0.23 s (N90), too short to read, so the animation
  continues into the RESULT / Enter-to-continue phase (Enter and auto-continue wait until the lerp finishes). `pass_u0` / `pass_u1` are unused.
  Lead/gap still from the sim: `_preview_lead` calls the same pure `Combat.resolve_turn` the core uses, and that value equals `core.submit_qte`.
  If the drawn order flips and the lines share a lane while the cars overlap, the passer takes the open lane, overtakes, and settles back onto its
  line (the open-lane plan is sampled on this same post-Exit window). No-clip check: the scripted run prints `MIN_SEP_OVERLAP` (lateral gap while
  the cars are within `car_len_m` along the road).
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
- Placeholders: all of display.json `playback_flow` (continue_s 6, lane_ease_s 0.35, blend 6/8 m, pass_after_exit_s 2.5, overlap 5.5/9 m, min_sep 2.6 m; pass_u0/pass_u1 unused since shots12).
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

## Editor workflow (shots11, 2026-11-12, UNAPPROVED)
Austin: "I think this is a good chance to work on your workflow for the editor with the two corner scene." The test used to build
everything in code under one Control. It is now split into scenes that open in the Godot 4.6.3 editor and show what the game draws.
No number, rule or sim value changed in the split. Values still come from `sim_constants.gd` (generated from the pinned sim) and
`spec/*.json` (display placeholders), and the split alone was pixel-identical on all 73 shots and 611 GIF frames (fixed-step A/B, `out/shots11/entry_pixel_diff.txt`).

**Open the project:** `godot --editor --path unapproved/gordon/two-corner/godot` (Godot 4.6.3; on the box the working copy is `/workspace/prototypes/two-corner/godot` and needs `--rendering-driver opengl3`;
the editor runs on the Compatibility renderer like the game). F5 runs `main.tscn`. A scene path after the project opens that scene directly,
e.g. `... res://scenes/track.tscn`. To validate every scene headless: `godot --headless --editor --path godot res://scenes/<name>.tscn --quit-after 120`
and check the output for `ERROR`.

**Which scene to edit for what**

| Scene | Script | Purpose / edit it for |
|---|---|---|
| `scenes/main.tscn` | `scripts/main.gd` | Composition: WorldVP (640x480 3D SubViewport) with CameraRig, Sky, PlayerCar, RivalCar, Track, Dressing; MirrorVP; Post (RGB555 + Bayer, 2x nearest); HudVP (1280x960) + HudRect; GlowVP. Game flow, cameras, passes and the QTE flow stay in `main.gd`. Child order matters (GlowVP stays last, so the post pass reads last frame's glow as before). |
| `scenes/track.tscn` | `scripts/track_road.gd` (@tool) | The Touge road surface: one continuous course (straight 45, hairpin L, join 47, N90 R, exit 30) plus each corner's scroll straight at runtime. Geometry comes from `display.json` `road` / `lane_width_m` / `districts.<dk>.lamp_period_m`, shown read-only in the inspector under "Spec values". |
| `scenes/touge_dressing.tscn` | `scripts/touge_dressing.gd` (@tool) | Lamps, verge, guardrail, cedar cards (B.5b Touge frames); the Street branch is kept for a Street corner. Props stream with the road scroll at runtime. |
| `scenes/sky.tscn` | `scripts/sky.gd` (@tool) | Painted sky cylinder + ridge band (`SkyCylinder` node); follows the camera at runtime. |
| `scenes/car.tscn` | `scripts/car.gd` (@tool) | Wraps a `.glb` from `assets/cars` (exports `model`, `env_texture`, `car_id` = key into `display.json` `car_shading`). `main.tscn` has PlayerCar (MX5) and RivalCar (S2000, overridden exports). The A.8 shading, wheel pivots, decals and glows are added at runtime. |
| `scenes/camera_rig.tscn` | `scripts/camera_rig.gd` | `Cam` (main camera) and `CornerPath/Follow` (the §13.3 authored playback path). Poses are still computed in `main.gd` `_update_camera`, unchanged. **The Entry camera and Entry selection screen are final (Austin 2026-11-12): don't change their placement, framing, motion or timing.** |
| `scenes/hud.tscn` | `scripts/hud.gd` + `scripts/hud/*.gd` | One Control per panel: MirrorFrame, CornerPlate, GapMeter, LineLockTimer, DebugHud, LineSelect (Lanes, EntryStrip, PlanPanel), LineLockedBanner, QtePanel, LineVsLine, ContinuePrompt (result line + Enter-to-continue countdown), FinishPanel, MainMenu. `hud.gd` picks which panels show; each panel script draws its part. Shared palette and helpers: `scripts/hud/hud_panel.gd`. |
| (no scene) | `scripts/art_kit.gd` | Shared mesh / material builders used by the scenes above and by `main.gd`, so the editor and the game build the same thing. |

**How @tool regeneration works**
- Generated geometry (road strips, dressing, sky mesh, car model) is built in `_ready()` when `Engine.is_editor_hint()` is true, as children with
  no owner, so it shows in the viewport but is **never saved into the .tscn**. At runtime the same functions run from `main.gd` (per corner, with
  the corner's district and scroll straight), and the editor-only build does nothing.
- To see a spec change: edit `spec/display.json` (or `race_config.json`), copy it to `godot/spec/`, then press **Rebuild road** / **Rebuild dressing**
  in the inspector (or reopen the scene). `district`, `preview_in_editor` and `preview_fog` (fog off by default so a top view stays readable) are
  editor-preview settings only.
- The HUD preview: pick a state in `Hud` > **Editor Preview** (select / lock / qte / play / result / finish / menu). The samples are display stand-ins,
  never used by the game. Text is rasterised for the 2x grid, so view the HUD at 200 % zoom to see it as the game shows it.
- Moving a HUD panel node in the editor only moves its selection box. Each panel still draws at the coordinates of the approved frames
  (post_lsc.py / post_clash.py / post_v5.py), so a layout change is a code change in that panel's script, not a drag.
- Placement in a .tscn that the runtime overwrites from the spec (viewport sizes, camera fov / near / far) is only an editor default; `main.gd`
  still sets it from `display.json` at start.
- The build id (`tools/stamp_build.py`) now also hashes `scripts/hud/*.gd` and `scenes/*.tscn`.
- Editor screenshots: `out/shots11/editor_track_tscn.png` (top view of the road, Track inspector), `editor_touge_dressing_tscn.png`, `editor_hud_tscn.png`.

## shots11 (2026-11-12): QTEs during playback, static Apex / Exit stops (UNAPPROVED)
Austin 2026-11-12: line select is Entry, then a static Apex stop, then a static Exit stop. The QTEs play during playback (entry, apex, exit),
each with a timer, and while a QTE runs the cars stay at that phase with the road scrolling until the timer runs out. The Entry camera and
Entry selection screen stay exactly as they were.
- **Selection:** Entry is unchanged, and corner 1 Entry select frames are pixel-identical to shots10. At the Apex and Exit stops the road and props are now static:
  the drawn scroll freezes while the scroller keeps running underneath, so the return to Entry (LINE LOCKED) is pixel-identical too.
- **Playback:** after LINE LOCKED the car drives its line, holds at the Entry point (turn-in - 6 m), the Apex point (mid-arc) and the Exit point
  (arc end + 6 m), the same E / A / X marks as the corner plate, and runs that phase's QTE there with the road still scrolling. Phase timer =
  lead_ms + QTE_ZONE_BASE_MS + tail_ms (1.7 s), and at least result_hold_s after the score goes up. The sweep, zone, score
  (max(0, 1 - |e| / (zone/2))) and unplayed = 0 are unchanged. The B.5a panel shows the phase being played, and the QTE panel sits under it with
  the timer. The three scores go to `core.submit_qte()` at the end of playback, and `resolve_turn` averages them as before.
- `qte_sweep.ready_s` is no longer used. Layout, timer text and hold points are PLACEHOLDERS (no Arthur frame).
- **Shots:** `out/shots11/`. Full-turn GIF `turn1_full_qte_in_playback.gif` (640 px, 10 fps), with a repo copy `turn1_full_qte_in_playback_400.gif`;
  `side_by_side_shots10_vs_shots11.png`; `entry_pixel_diff.txt`; `parity.txt`.
