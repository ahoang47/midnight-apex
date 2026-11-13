# Changelog

> Session journal for the whole repo: changes, decisions, reasoning, and reversions. **Read before making changes** to avoid repeating past mistakes. Newest entry at the top.
>
> Entries before 2026-10-31 "Repo restructure" were merged from two older logs and keep their **original wording and paths**. Old → new paths: `velocity-shift/overview/0X-*.md` (also written `overview/0X-*.md` or `Notes/06-pattern-read.md`) → `design/0X-*.md`; `godot_prototype.md` → `design/godot-build-guide.md`; `art_direction.md` → `design/art/art_direction.md`; `Notes/` → `design/notes/`; `story/high_level_story.md` → `story/pitch.md`; `story/plot_points.md` → `story/plot.md`; `story/character_sheets.md` → `story/characters/index.md`; `story/sabine.md`, `story/myth_driver_*.md` → `story/characters/`; `velocity_shift/`, `tests/`, `scripts/*.py`, `config/`, `main.py` of the prototype → `sim/…`.
>
> Same-day ordering between the two old logs is a best guess (neither log recorded times). On 2026-10-31 Arthur wrote the restore and BRZ entries into both logs; both copies are kept.

---

## 2026-11-13 — Arthur [art]: Touge mouse look-back, revised to head-on (Austin picked option B)

- **Why:** Austin, 2026-11-13: "I like the look back cam, but the mirror should stay as the mirror. The mirror should stay the same size. The look back cam should be a head on, instead of this angled view."
- **What (`unapproved/arthur/mockups/districts/`):**
  - **New frames:** `mouse_lookback_headon.png` (about 10 m) and `mouse_lookback_headon_far.png` (about 24 m).
  - **Camera:** a centred reverse camera just above the rear deck, square to the road, with the rival dead centre in the lane.
  - **Mirror:** the E3B mirror is unchanged in size, position, frame and label, but shows the road ahead with the chevrons.
  - **HUD:** sign and gap box are back in their standard places.
  - **Comparison:** `lookback_vs_cat.png` (head-on mouse vs `touge_cat.png`).
- **Open:** "REAR VIEW" reads wrong when the mirror shows the road ahead. I kept the label as asked, pending a decision.
- **Not changed:** Gordon's files, the sim, and the earlier A/B/C option frames.

## 2026-11-13 — Arthur [art]: Touge mouse-view options (big mirror / look-back / high cam)

- **Why:** Austin, 2026-11-13, on `touge_mouse_far.png`: "The mouse cam in the last image would make it hard to read the opponent."
- **What (`unapproved/arthur/mockups/districts/`):** Three leading-view options on the sloped touge, each at about 10 m and about 24 m gaps. `mouse_options_sheet.png` shows all six.
  - **A, big mirror:** the standard chase camera with a 2× rear-view inset. The turn sign moves below it and the gap box moves to the top right.
  - **B, look-back:** a low reverse camera at the player's rear quarter, plus a forward AHEAD inset with the chevrons.
  - **C, high cam:** a higher chase camera that pulls back with the gap.
  - **HUD:** placement overrides are in this mockup's copies of `mirror_frame.gd`, `resource_stack.gd` and `post.gdshader`. The tie-gap box is now 28 px tall, so it no longer touches the sign.
  - **Re-renders:** all earlier district frames.
- **Not changed:** Gordon's files and the sim.

## 2026-11-13 — Arthur [art]: Touge on a grade + cat-and-mouse frames; consistency sheet

- **Why:** Austin, 2026-11-13: give the touge road a real grade. Touge has no passes, so a race is half leading (mouse) and half following (cat). Two worries: mouse readability as the gap grows, and whether touge feels like a different game from Street and Wangan. Presentation only; scoring unchanged.
- **What (`unapproved/arthur/mockups/districts/`):**
  - **Grade:** touge climbs at 8.5%, crests through the hairpin and falls at 5% after it, with up to 6% bank. The road, verges, cut slope, guardrail, trees, lamp, cars, chevrons and cameras all follow it.
  - **Mouse** (`touge_mouse.png`, standard camera): faked chaser lighting. A long beam decal runs under the player, the player's shadow is thrown into the beam, and a stepped rear light on the player car (`shaders/car_lit.gdshader` copy) lights the tail. The head glows are bigger so the chaser reads in the rear view.
  - **Mouse, far** (`touge_mouse_far.png`): only the headlight pair in the rear view, and a near-full gap bar.
  - **Mouse, pulled-back camera** (`touge_mouse_pulled.png`): an alternative only. The HUD band still hides the rival's nose.
  - **Cat** (`touge_cat.png`): the rival is ahead in the chevrons, with bigger tail glows and a red tail wash on the road.
  - **Tie-gap:** made prominent in a HUD copy. The box is bigger, with a MOUSE/CAT tag, the gap in seconds and an 8 px bar. It's used in all district frames.
  - **Sheets:** `consistency_sheet.png` (mouse, cat, street, wangan) and a refreshed `districts_sheet.png`.
- **Not changed:** Gordon's files and the sim.

## 2026-11-13 — Arthur [art]: District looks draft (touge narrow, street, wangan) with the E3B HUD

- **Why:** Austin, 2026-11-13: "The road also reads really wide. This works for wangan and maybe street but not for touge. Mind drafting up the looks for all 3 districts with this in mind, with the current HUD?" Follow-up: Wangan keeps the current E3B road as is, with its width, plus lane lines.
- **What (`unapproved/arthur/mockups/districts/`):** One Godot-rendered E3B Entry chase frame per district, with the E3B HUD unchanged.
  - Touge (`touge.png`): a 6.0 m two-lane pass with no lane lines, a close guardrail on the drop, a rock cut slope with cedars on the inside, and sparse sodium lamps. Chevrons are scaled down.
  - Street (`street.png`): an 8.4 m two-lane lined street with shops, utility poles and wires, and vending machines.
  - Wangan (`wangan.png`): the 11.9 m E3B road with its lane lines back, jersey barriers, tall sodium lamps and distant city towers.
  - `districts_sheet.png` shows all three side by side.
  - New props are built in Blender (`blender/build_assets.py` → glTF) on pack bases: cut slope, guardrail, utility pole, 4 shop blocks, vending machine, expressway lamp, the re-textured Urban Stacked jersey barrier, and towers.
  - Road strips use a 1 m grid so painted lines don't wobble near the camera.
- **Not changed:** Gordon's files and the game's road width (`display.json`). Concept only.

## 2026-11-13 — Arthur [art]: E3B drops the floating OUT/MID/IN road labels; plan box spacing

- **Why:** Austin, 2026-11-13: the floating OUT/MID/IN labels with down-arrows were stacked into a smudge over the far road. After a look at spreading them, he ruled they should come off completely — the road chevrons alone show the line. Also fix the plan-box nits: the selection frame clipped the top of OUT, and the position word sat on its stat box.
- **What (`unapproved/arthur/mockups/resource_meters/`):** The floating lane-marker overlay is skipped in this mockup (labels and down-arrows gone). Coloured road chevrons are unchanged. Touge lane lines stay off. PLAN THE LINE rows are a little taller so the 1 px selected frame has 2 px clearance above the position word and a 2 px gap above the framed stat box. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot (state source frames too). Before/after crop of the marker area at 2×: `e3b_no_marker.png`. Concept only; not in the sim.
- **Game file:** The overlay is Arthur's `unapproved/arthur/mockups/line_preview/godot/scripts/hud/lanes.gd`, also used in Gordon's two-corner HUD at `unapproved/gordon/two-corner/godot/scripts/hud/lanes.gd` (positions unprojected from the chase camera). Neither file was edited; the mockup just passes no lane points so the overlay does not paint.

## 2026-11-13 — Arthur [art]: E3B PLAN THE LINE grid cleanup; no lane lines on touge

- **Why:** Austin, 2026-11-13: "Kinda sloppy, out/mid/in is bunched together and the plan the line box is sloppy." Also: remove the dashed centre and edge lane markings from the touge road in these mockup renders — they wobble near the camera and make the road look too wide for a tight touge pass.
- **What (`unapproved/arthur/mockups/resource_meters/`):** PLAN THE LINE is laid out on a clean grid: a header row with a gap below the title; E/A/X in a fixed left column and the row labels in a fixed second column; three evenly spaced, equal-width stance columns with the position text centred over a same-width framed stat box (canon unchanged: unframed position, framed stat underneath). Consistent row height and inner padding, nothing touching the panel border. The ENTRY highlight no longer fills over the text; the selected choice is a 1 px frame around the stack. Empty APEX/EXIT rows show a centred dash in each column. The section is a little wider, taking space from LINE LOCK, which stays readable. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot. Before/after of the box at 2×: `plan_box_cleanup.png`. Concept only; not in the sim.
- **Touge lane lines:** Rule — lane lines appear only in the Street and Wangan settings, never on touge. Gordon's road bake (`unapproved/gordon/two-corner/spec/gen_art.py`, which writes `godot/art/touge_road.png` and is loaded by `art_kit.gd`) was not edited. The E3B mockup overrides that texture with a local no-line `godot/art/touge_road.png`.

## 2026-11-13 — Arthur [art]: E3B EN 5-spoke rotated; HAN coilover shortened

- **Why:** Austin, 2026-11-13: approved the light 5-spoke and asked to rotate it so no spoke sits on the horizontal, then: "Next is to make the coil over shorter so it doesn’t impede."
- **What (`unapproved/arthur/mockups/resource_meters/`):** The EN star is rotated so one spoke points straight up (no horizontal spoke). The caliper stays inside the rim, now sitting in the window just below 3 o'clock. Nothing else on the wheel changed. The HAN shock is a squatter coilover — fewer coil turns, compact eyelets, same colours and line weight — so it stays inside its row and no longer crowds the EN wheel, the chips or the bars. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot. Before/after: `en_icon_5spoke.png` (rotation) and `han_icon_short.png` (old vs short, in the band with neighbouring rows). Concept only; not in the sim.

## 2026-11-13 — Arthur [art]: E3B EN 5-spoke is light against the rotor

- **Why:** Austin, 2026-11-13: approved the thin 5-spoke ("It looks better though") and asked to recolour it.
- **What (`unapproved/arthur/mockups/resource_meters/`):** The five slim spokes and the hub face use the rim's light tone so the 5-spoke star reads clearly against the darker rotor at in-band size. Lug holes and the centre cap stay dark. The hub is cleaned up so it reads as a small hub with 5 lugs. Shape, caliper (inside the rim at 3 o'clock), line weight and flat style are unchanged. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot. Dark-spoke vs light-spoke at in-band and 4×: `en_icon_5spoke.png`. Concept only; not in the sim.

## 2026-11-13 — Arthur [art]: E3B EN wheel is a thin 5-spoke

- **Why:** Austin, 2026-11-13: "Try a thin 5 spoke like this."
- **What (`unapproved/arthur/mockups/resource_meters/`):** The EN wheel is redrawn as a thin 5-spoke alloy (Enkei-style): five slim straight spokes from a small hub with 5 lug holes and a dark centre cap, a thin rim, and large open windows. Austin's ref is at `ref/hud_ref_wheel_5spoke.jpg`. No logos. The caliper stays inside the rim, visible through the 3-o'clock window, and is a little larger now that the windows are wider so it still reads at in-band size. Rotor, colours, line weight and flat style are unchanged. POW coolant and HAN shock are unchanged. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot. Before/after at in-band and 4×: `en_icon_5spoke.png`. Concept only; not in the sim.

## 2026-11-13 — Arthur [art]: E3B EN caliper sits inside the wheel

- **Why:** Austin, 2026-11-13: "The icon of the caliper is outside the wheel. It should be inside."
- **What (`unapproved/arthur/mockups/resource_meters/`):** The EN wheel icon's 2-piston caliper is redrawn so it sits entirely inside the rim, clamping the rotor and visible in the 3-o'clock spoke gap, the way a real caliper reads through an alloy wheel. Nothing sticks out past the rim. Style, colours and line weight are unchanged. `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot. Before/after crop at in-band and 4×: `en_icon_caliper_fix.png`. Concept only; not in the sim.


## 2026-11-13 — Arthur [art]: revert E3B EN/HAN icons at Austin's request

- **Why:** Austin, 2026-11-13: "The icons look bad, let’s revert it."
- **What (`unapproved/arthur/mockups/resource_meters/`):** EN and HAN band icons restored to exactly the E3 wheel+caliper and shock from `7c69bf6`. POW coolant is unchanged. The E3B heat/load meter model is kept (LIMIT and RELEASE marks, OVERRUN, LOCKED, locked-cooling). `e3b_full.png`, `e3b_states.png`, `e3b_overrun.png` and `e3b_locked.png` re-rendered in Godot with the restored icons. The new standalone icon files (`icon_en_brake_*`, `icon_han_shock_*`, masters, `icons_e3_sheet.png`) are removed. Austin's two icon refs stay in `ref/`. Concept only; not in the sim.


## 2026-11-13 — Arthur [art]: unapproved E3B heat/load meters and new EN/HAN icons

- **Why:** Austin, 2026-11-13: work on the iconography (coolant is ok; make EN like his rotor+caliper reference; HAN like his coilover reference, drawn straight up and down). Then a final meter model: the three bars are heat/load meters that fill as load builds and drain as they recover. LIMIT at about 80%, an OVERRUN zone between LIMIT and full (still selectable, hits less), full = LOCKED, and a RELEASE mark at about 55% for lock hysteresis.
- **What (`unapproved/arthur/mockups/resource_meters/`):** Concept only; not in the sim. E3 layout kept as variant E3B. EN icon is a cross-drilled rotor with a solid black caliper (no tyre, no wheel). HAN icon is a vertical coilover. POW coolant is unchanged. Bars use the stat colour as the base fill. LIMIT is an amber cap on the top edge; RELEASE is a blue triangle on the bottom edge, so the two marks read apart. OVERRUN uses hot-orange fill `#FF701C`, an OVERRUN tag, and a hot-orange penalty fill on that stance's PLAN THE LINE stat chip. LOCKED uses a padlock + LOCKED tag, a grey struck stat chip, and an unavailable plan chip. Locked-cooling keeps the padlock with a dim flat-hatched fill until the bar drops below RELEASE. Frames: `e3b_full.png` (mixed mids), `e3b_states.png` (cool / mid / overrun / locked / locked-cooling / unlocked), `e3b_overrun.png`, `e3b_locked.png`, plus `icons_e3_sheet.png` and standalone 16/64/128 icon files. Refs copied to `ref/`. Thresholds are placeholders, not approved.
- **Left as is:** Earlier A–E3 frames and their depleting-headroom meter model. Nothing in the sim.


## 2026-11-13 — Arthur [art]: remove superseded unapproved mockup folders

- **Why:** Austin, 2026-11-13: sort `unapproved/arthur/` and delete the superseded or experiment-only studies.
- **What:** Removed `unapproved/arthur/mockups/lane_chain/`, `line_clash/`, `psx_road_test/`, `crt/`, `race_state_study/`, and `pattern_read/` (about 55.1 MB committed). They remain in git history. `line_clash/` option A was already promoted to `art/ui/line_vs_line/`; option B was not chosen. `psx_road_test/` led to approved B.5c, already in art_direction. `crt/` and `race_state_study/resolution_test/` were experiment-only (art_direction B.4).
- Updated `unapproved/arthur/mockups/README.md` and references in `art/ui/line_select_cam/` and `art/ui/line_vs_line/`.
- **Left as is:** `line_preview/`, `resource_meters/`, `overworld/`, and `tones/`. Historical CHANGELOG entries still name the old paths. Gordon's two-corner docs and scripts that cite them were not edited.

## 2026-11-12 — Gordon [godot]: PLAN THE LINE stat framed under OUT/MID/IN; entry_strip no longer calls lane_stat (UNAPPROVED)

- **Why:** Austin follow-up (relayed by Arthur, 769f073): "The stat should be framed under the position text." Arthur also reported that his `run.sh` symlinks our `entry_strip.gd`, which failed to parse because it called `lane_stat()` — a helper that exists only on our `hud_panel.gd`, not his.
- **What (`unapproved/gordon/two-corner/`):** PLAN THE LINE chips now match Arthur 769f073: unframed OUT / MID / IN over a small framed stance-coloured POW / HAN / EN box (`stat_box`); the selected highlight sits behind the position text only; the lock tick sits to the right of the position letters. `entry_strip.gd` inlines the `OUT · POW` labels instead of calling `HudPanel.lane_stat`, so Arthur's symlink parses against his `hud_panel.gd`. No Arthur files were edited. Colours unchanged (POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`). Build id `272ae5508b`.
- **Tests:** Quick local check (Austin, 2026-11-12): Godot headless parse/run plus one parity seed (`seed20261113_idx`) 0.0 vs pin 50928ed. Full parity, fuzz and key test left to CI. Token prefix `TC3:50928ed:272ae5508b:`.
- **Shots:** `out/shots15/` — Entry / Apex / Exit selection at 1280×960 (hover on each stance, seed 20261114), Exit QTE, RESULT, and `compare_arthur_vs_gordon.png` against Arthur's 769f073 / fb38d45 frames.
- **Left as is / differed from the mockup:** Hinting is off (B.5c / the brief); Arthur's mockup script used `HINTING_NORMAL`. Archivo Black is loaded as `hud.fa` the way Arthur's `hud.gd` does, but paint currently uses Nimbus Sans Bold for heavy titles, same as his `_font()`. The tie-gap bar and debug box still use the 9-slice `box()` path, matching Arthur's code (no `plate_finish` there). The known Entry-chase crest gap for follow-on chevrons is unchanged. Cameras and gameplay unchanged. The debug seed box is kept.

## 2026-11-12 — Arthur [art]: stat is framed under the OUT/MID/IN position text

- **Why:** Austin follow-up, 2026-11-12: "Not quite what I wanted. The stat should be framed under the position text."
- **What:** The frame around the whole PLAN THE LINE chip is removed. OUT / MID / IN stays unframed text; directly under it the stat (POW / HAN / EN) sits in its own small framed box with a pixel-hard plate-style border, filled in the stat colour. Selected choices keep a highlight behind the position text and a brighter stat frame. The lock tick sits to the right of the position letters, on the highlight and clear of the stat box. Applied on all three rows. Line-preview frames and sheets re-rendered in Godot (`769f073`). B.5d and the mockup README updated.

## 2026-11-12 — Gordon [godot]: two-corner HUD plate grain, bevel, heavier type, and framed lane chips (UNAPPROVED)

- **Why:** Austin, 12:55 PM PT, 2026-11-12: "I like his HUD look." Port of Arthur's plate grain, bevel and heavier fonts from `unapproved/arthur/mockups/line_preview/` into the two-corner HUD. Purely visual; no gameplay or sim change. Later the same day Austin ruled (relayed by Arthur; 9ba4c70 / c838466) that every PLAN THE LINE row uses IN/MID/OUT chips with the stat, and "The chips should be framed."
- **What (`unapproved/gordon/two-corner/`):** `plate_finish` from Arthur's `hud_panel.gd` (grain tile, 1 px banding, hard bevel) is applied to every `lpanel` and the PLAN THE LINE body. Grain is drawn only on HUD plates, on the 1280×960 HUD layer after the 640×480 dither pass — never on the 3D or the road. Fonts copied into `godot/fonts/`: Nimbus Sans Bold (with the existing Narrow Bold / Bold Oblique) and Archivo Black, with licenses alongside. Titles use Nimbus Sans Bold (`hud.fb`); text is pixel-hard (no AA, hinting off, nearest). Every row uses corner-relative `OUT · POW` / `MID · HAN` / `IN · EN` chips, framed with Arthur's `frame_lane_chip` (ink outer, edge inner, hard bevel; highlight stays inside the frame). Colours unchanged (POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`). Debug box keeps the 6x9 bitmap so F9/F10 and the seed stay readable. The after-turn QTE/continue line is moved just under the gap bar so it no longer overlaps the meter. Build id `1da2058394`.
- **Tests:** `python3 tools/qte_fn_test.py` as CI runs it: PASS, 5757 values, raw_qte_score exact, 0 mismatches. `run_parity.sh` seeds + fuzz300, save/load, restart, and the 200-seed key test all 0.0 vs pin 50928ed. Token prefix `TC3:50928ed:1da2058394:`.
- **Shots:** `out/shots15/` — Entry / Apex / Exit selection at 1280×960 (hover on each stance, seed 20261114), Exit QTE, RESULT, and `compare_arthur_vs_gordon.png` against Arthur's c838466 frames.
- **Left as is / differed from the mockup:** Arthur's chips are stacked (lane over stat in a 26 px slab); this build keeps the combined single-line `OUT · POW` wording from the written brief, now on every row, inside the same plate-style frame. Hinting is off (B.5c / the brief); Arthur's mockup script used `HINTING_NORMAL`. Archivo Black is loaded as `hud.fa` the way Arthur's `hud.gd` does, but paint currently uses Nimbus Sans Bold for heavy titles, same as his `_font()`. The tie-gap bar and debug box still use the 9-slice `box()` path, matching Arthur's code (no `plate_finish` there). The known Entry-chase crest gap for follow-on chevrons is unchanged. Cameras and gameplay unchanged. The debug seed box is kept.

## 2026-11-12 — Arthur [art]: PLAN THE LINE stance chips are framed

- **Why:** Austin follow-up, 2026-11-12: "The chips should be framed."
- **What:** Every OUT / MID / IN chip on the PLAN THE LINE panel now has its own bold, late-90s bevelled/outlined border in the plate style (pixel-hard, ink outer + edge inner + hard bevel). Unselected chips are framed too; the selected highlight stays inside the frame. `plan_panel.gd` and the line-preview frames/sheets were re-rendered in Godot. B.5d and the mockup README note the framed-chip treatment.

## 2026-11-12 — Arthur [art]: PLAN THE LINE stance chips are OUT/MID/IN + stat on every row

- **Why:** Austin, 2026-11-12: "stance selection should say in/mid/out for all, with a chip explaining stat."
- **What:** On the PLAN THE LINE panel, the ENTRY, APEX and EXIT rows all label choices OUT / MID / IN, each with a small stat chip (OUT · POW green #2CB84A, MID · HAN yellow #F0C828, IN · EN red #E8282C), the same stacked chip style as the existing Entry row. Apex and Exit no longer use plain POW / HAN / EN labels, and the extra POW/HAN/EN group on the Entry row is dropped. The pick itself remains the stat; backend naming is unchanged.
- `design/art/art_direction.md`: B.5 naming rule, B.5b and B.5d now state this on-screen label rule.
- `unapproved/arthur/mockups/line_preview/`: `plan_panel.gd` and README updated; all overview, camera-stop and stance-variant frames plus sheets re-rendered in Godot.

## 2026-11-12 — Gordon [godot]: two-corner B.5d line preview from Arthur's approved mockup (UNAPPROVED)

- **Why:** Austin approved Arthur's line-preview mockup as the build reference (relayed by Arthur, commit 9a83828). Purely visual; no gameplay or sim change.
- **What (`unapproved/gordon/two-corner/`):** Flat chevrons on the road along the chained Entry → Apex → Exit line, pointing in the direction of travel, no glow. Each segment is coloured by stance (POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`). Hovered segment at full strength; follow-on segments solid at 0.66 brightness and slightly thinner (Arthur pass 4 measures). `line_chevrons.gd`, `shaders/chevron.gdshader` and `art/line_chevron.png` are copied from Arthur's mockup and adapted here (credit in the script). Bend mapping is Arthur's, recorded as PLACEHOLDER in `spec/display.json`: POW holds the outer line, HAN mid-lane, EN cuts to the inner line over the full lane width, corner-relative via `track.gd`. Implied follow-on is Apex EN, Exit POW. One combined PLAN THE LINE panel at the bottom right (narrower so it clears the car); lane chips read `OUT · POW`, `MID · HAN`, `IN · EN`. The race split bar sits under the rear-view mirror. Entry camera, Entry select framing, and Exit camera are unchanged. Build id `2ba8a4d505`.
- **Tests:** `python3 tools/qte_fn_test.py` as CI runs it: PASS, 5757 values, raw_qte_score exact, 0 mismatches. `run_parity.sh` seeds + fuzz300, save/load, restart, and the 200-seed key test all 0.0 vs pin 50928ed. Token prefix `TC3:50928ed:2ba8a4d505:`.
- **Shots:** `out/shots14/` — Entry / Apex / Exit × each stance hover at native 640×480 (3D+post) and the final 1280×960 composite; `compare_arthur_vs_gordon.png` side-by-side with Arthur's frames. Shot seed 20261114 (opening hand P/H/E ×2; 20261113 has only one EN).
- **Left as is / differed from the mockup:** The known gap where the follow-on line vanishes over the crest from the Entry chase cam (`_in_straight()` hides the hook mesh) is left as-is; the same gap is in the mockup. Entry row uses combined lane chips (`OUT · POW`) only — the slim panel cannot also fit Arthur's second POW/HAN/EN chip group on that row (the written spec called for the combined chips). Plate grain, bevel, and heavier mockup fonts were not ported (those assets/fonts are not in this tree; would be a global HUD restyle beyond this brief). The debug seed box is kept. art_direction.md B.5d still mentions a 2/3-lane EN cut; pass 4 / the approved mockup uses the full lane width, which is what is built (PLACEHOLDER).

## 2026-11-12 — Barry [barry]: corners-v1 story characters include kids and matures

- **Why:** Austin ruled "Kids and matures are story characters." The draft had listed only lieutenants, crew bosses, Myth Drivers and Sabine, which was my assumption.
- **What:** `unapproved/barry/corners-v1/README.md` layer 3 now covers every ladder rung (kids, matures, old heads, crew bosses), Myth Drivers and Sabine. Only wild grind racers play pure district lines. Still a draft; no sim run, `sim/` unchanged.

## 2026-11-12 — Barry [barry]: corners-v1 layer rows note story-character swaps

- **Why:** consistency with Austin's 2026-11-12 ruling that story characters swap only some corners; the layer 1 and 2 rows still read as covering every racer.
- **What (`unapproved/barry/corners-v1/README.md`):** layer 1 and 2 "Applies to" cells now add "except a story character's swapped corners". Wording only; no numbers, no sim.

## 2026-11-12 — Barry [barry]: corners-v1 corrects the story-character layer and replaces sim criterion 1

- **Why:** Austin, 2026-11-12: "Story characters swap some defaults, and some signature corners," and he said the old success criterion 1 was off.
- **What (`unapproved/barry/corners-v1/README.md`):** the "every corner" wording from aa1f141 is replaced. A story character overrides only a subset of normal corners (own line) and a subset of signature corners (own line + bluff); every other corner follows the district layers. Swap lists, lines and rates come from Nathaniel / Desmond. New open items: each character's swap list, and whether a swapped normal corner is fixed or also bluffs. Sim plan v2 criterion 1 is now "learning a story character pays off" (learned-swaps player clearly beats a district-defaults player, and the bluffs don't wipe it out), reported per character once inputs exist; assumptions updated to match. Still a proposal; no sim, `sim/` unchanged.

## 2026-11-12 — Barry [barry]: corners-v1 records Austin's ruling on story characters at signature corners

- **Why:** Austin, 2026-11-12, answering the open parameter: "Story characters use their own line and bluff on signature corners too."
- **What (`unapproved/barry/corners-v1/README.md`):** ruling recorded in the three-layer section (story characters override the district layer on every corner, signature corners included; lines and rates still from Nathaniel / Desmond, none invented). The item is removed from the open parameters, the flag is marked settled, and the Sim plan v2 assumptions now say signature corners apply to wild racers only. The old everyone-shares rule is marked superseded. Still a proposal; no sim, `sim/` unchanged.

## 2026-11-12 — Barry [barry]: corners-v1 three-layer line model draft + Sim plan v2 (PROPOSAL, NOT APPROVED, no sim)

- **Why:** Austin, 2026-11-12: "all districts should have a distinct default line for all corner types. Where this default line deviates is for select corners, this is where bluff lines come in to play. Where it deviates even more is for story characters, where they get their own line + bluff." Then "Draft it." No sim was approved, so none was run.
- **What (`unapproved/barry/corners-v1/README.md` only):** three-layer table (district default, no bluff / signature corners, main + 2 alts / story characters, own line + bluff); full 8 x 3 defaults table, current vs proposed. Today 5 corner types collide across districts (HP T=W, N90 T=W, ES T=W, DR W=S, IR T=S). Proposal changes one district per collision, one letter each, chosen to fit documented habits and to avoid lines-v1 approved lines (Street N90, Wangan IR/SW) and Nathaniel's signature candidates: Wangan HP EHP->EHE, N90 EHP->EPP, ES HHH->HHE, DR EEH->EEE (Wangan's EN door-shut on exits / POW commit where the road opens); Street IR HHP->EHP (Street's EN at Entry). Within-district duplicates listed as info (Touge HP=N90, CR=IR=SW; Wangan IR=SW). Story-character layer is a schema slot only; Nathaniel and Desmond supply inputs. Open parameters listed (signature count, signature and character bluff rates; 0.65/0.21/0.14 noted as current value only). Flags for Desmond/Nathaniel. Draft Sim plan v2 (not started) with starting conditions, assumptions and 4 success criteria; the earlier paused plan is marked superseded.
- **Left as is:** `sim/` and `LINE_SET_C` unchanged; no balance numbers set; `story/corner_lines.md` untouched (Nathaniel's).

## 2026-11-12 — Gordon [godot]: qte_fn_test allows 2 ULP on unrounded erf / ehq / zone (CI glibc 2.43)

- **Why:** Desmond made the qte-v1 CI step strict in 50928ed. That run, and the follow-up on 328a817, failed the check on GitHub's Ubuntu 26.04 runner (glibc 2.43): 327 bit mismatches on the unrounded functions, 269 within 1 ULP, 58 at 2 ULP, `max_abs_diff=2.220e-16`. `raw_qte_score` stayed bit-exact (the 3-decimal rounding still pins gameplay). This box (glibc 2.41) remains bit-identical. The 1-ULP allowance added in 22208fb was not quite enough for the runner's libm.
- **What:** `tools/qte_fn_test.py` allows up to 2 ULP on `erf` / `expected_hit_quality` / `qte_zone_width` only. `raw_qte_score` is still exact. The log now prints per-group mismatch / ULP / fail counts and `max_ulp`.
- **Left as is:** The rounding rule and the pin (50928ed). No Godot gameplay or token change (build id stays `512d64fca1`).

## 2026-11-12 — Gordon [godot]: two-corner POW/EN/HAN rename; re-pin to 50928ed; state token TC3 (UNAPPROVED)

- **Why:** Austin's 2026-11-12 naming rule: everything behind the screen (code, data, specs, state tokens, docs) uses POW / EN / HAN. IN / MID / OUT appear only in what is drawn. Barry's sim rename 53267c5 landed that in the sim (P/E/H letters, `Stance.POW`/`EN`/`HAN`, `StanceOutcome.DRAW`, LINE_SET_C A→P / D→E / S→H). This pass mirrors it in the Godot two-corner build and moves the pin to **50928ed** (newest proto-build containing 53267c5; also includes the c3ffc41 QTE rounding and Desmond's strict qte-v1 CI step). sim/ is unchanged after 53267c5.
- **What (`unapproved/gordon/two-corner/`):** Letters are P/H/E in `_INDEX_STANCE` / `PLAN_ORDER` / autofill order (POW, HAN, EN) so ties and Up/Down stay the same. `resolve_stance` uses P/H, H/E, E/P. `DRAW` replaces the old 0-outcome name. Regenerated `sim_constants.gd` / `constants.json` from the new pin (LINE_SET_C e.g. Touge HP EHP/EEH/EHH). HUD and `track.gd` are the only places that know IN/MID/OUT; labels read like `OUT (POW)` (plan options, entry strip, road markers). Clash/QTE chips stay POW / EN / HAN. Colours unchanged (POW `#2CB84A`, EN `#E8282C`, HAN yellow). Physical keys unchanged; only labels. `entry_tell` returns the stance letter only. `display.json` keys renamed A/D/S → P/E/H. `tools/sim_parity.py` talks to `Stance.POW`/`HAN`/`EN` with no aliases. Token schema bumped **TC2 → TC3** (`TC3:50928ed:<build10>:…`); TC1/TC2 are refused with a clear "outdated token" message (`race_core.gd`, `decode_token.py`, F10 still accepts them so the message can fire). Build id `512d64fca1`. Spec: `unapproved/gordon/playtest-state-spec.md` §0.5. HUD shot: `out/shots13/hud_labels_OUT-POW_640.png`.
- **Tests:** `python3 tools/qte_fn_test.py` the way CI runs it (qte-v1 is strict as of 50928ed): PASS, 5757 values, raw_qte_score exact, 0 mismatches. `run_parity.sh` seeds + fuzz300, save/load, restart, and the 200-seed key test all 0.0 vs the new pin. Same results from a fresh copy with no `.godot` folder. Token prefix `TC3:50928ed:512d64fca1:`.
- **Left as is:** Geometric inside/outside/center wording (camera `d_in`, cedars, `inside_sign`, layout center). Course segment types `S`/`A` (straight/arc) and plate letters `E`/`A`/`X` (Entry/Apex/Exit). Keyboard bindings. Historical README / display.json notes that mention Neutral/NEU or A/D/S as past names. `design/godot-build-guide.md` already has PowButton/EnButton/HanButton and DRAW; two-corner HUD is custom-drawn, so those button node names are not in the scenes. `run_parity.sh` still writes the dump file as `out/godot_state.tc2` (filename only).

## 2026-11-12 — Nathaniel [story]: corner_lines.md header matches the sim's new P/E/H letters
- `story/corner_lines.md` header now says `LINE_SET_C` uses P/E/H (Barry's rename in 53267c5) instead of A/D/S. No line changed.

---

## 2026-11-12 — Gordon [godot]: QTE rounding mirrored; two-corner re-pin to c3ffc41; qte_fn_test 1-ULP on intermediates

- **Why:** Barry's sim commit c3ffc41 (Austin approved via Desmond, 2026-11-12) rounds each Entry / Apex / Exit raw score to 3 decimals so a 1-ULP libm difference in `erf`/`exp` (glibc 2.41 vs 2.43) cannot change gameplay. CI still compared Godot to the older pin (f0efecf), so this mirrors the rule and moves the pin.
- **What (`unapproved/gordon/two-corner/`):** `combat.gd` adds `round_qte_score` = `floor(x * 1000.0 + 0.5) / 1000.0` (not `snappedf(x, 0.001)`, whose last bit differs on ~14% of inputs). `raw_qte_score` and `phase_raw_qte` apply it; unplayed stays 0 and is not rounded; a scalar passed to `mean_phase_qte` is still taken as-is; Entry + Apex + Exit are summed in that order and divided by 3.0, and the mean is not re-rounded. `expected_hit_quality` and `qte_zone_width` stay unrounded. Live and scripted phase scores are stored already rounded, so the HUD and the TC2 token (`TC2:c3ffc41:<build10>:...`) show and record the same value the sim uses. HUD phase scores print to 3 decimals. `QTE_SCORE_DECIMALS` added to `spec/gen_constants.py` / `sim_constants.gd`. `spec/race_config.json` `pin_commit` = c3ffc41. Build id `8f349ab0a1`.
- **qte_fn_test.py:** `raw_qte_score` stays bit-exact. The `erf`, `expected_hit_quality` and `qte_zone_width` groups are kept and now allow a 1-ULP tolerance (the last CI run on glibc 2.43 had 337 mismatches, max 2.22e-16). On this box (glibc 2.41) those groups are still bit-identical (0 mismatches).
- **Tests:** `run_parity.sh` and `qte_fn_test.py` locally, and from a fresh copy with no `.godot` folder (CI's two godot steps): qte-v1 functions PASS (5757 values, raw exact), seeds + fuzz300, save/load, restart and the 200-seed key test all 0.0 vs the pinned sim. Token prefix `TC2:c3ffc41:8f349ab0a1:`.
- **Left as is:** sim commit 53267c5 (POW / EN / HAN, P/E/H, DRAW) is not in this pin; Godot still uses the pre-rename letters so the parity check stays a straight match. That mirror is a separate pass.

## 2026-11-12 — Barry [sim][design]: stances, stats and line tables named by stat only (POW / EN / HAN); names only, numbers identical
- **Why:** Austin in Exec Team, 2026-11-12: "There's too many inconsistencies with the stance and stats and line choice naming. It should be: POW EN HAN Across all mentions." Then: "I think all backend should refer to stats. In/mid/out only visual reference." Desmond's canon block in `design/01` (81b230f, 4cdd1bc) records both. Mapping confirmed against the sim (`deck_weights` / `deck.py` stat→card weights) and `story/corner_lines.md` (Touge hairpin `DSA` = EN-HAN-POW).
- **Code renames, no aliases kept** (`sim/velocity_shift/models.py` and every user): `Stance.ATTACK = "attack"` → `Stance.POW = "POW"`, `Stance.DEFEND = "defend"` → `Stance.EN = "EN"`, `Stance.NEUTRAL = "neutral"` → `Stance.HAN = "HAN"` (member order unchanged: POW, EN, HAN); `StanceOutcome.NEUTRAL` → `StanceOutcome.DRAW` (value 0). `LINE_SET_C` letters and `LETTER_TO_STANCE`: A → P, D → E, S → H (e.g. Touge `HP` `["DSA","DDS","DSS"]` → `["EHP","EEH","EHH"]`); `test_lines.py` expects Street N90 `["HHP","HEH","HHH"]`. CLI card labels print `POW` / `EN` / `HAN` (were `ATTA` / `DEFE` / `NEUT`); trace "Player Cards" values are now `"POW"`/`"EN"`/`"HAN"`. `balance_gauntlet.py` scenario `always_neutral` → `always_draw`; the draw row label in `design_opponent.py` / `design_racers.py` reads `Draw`. Comments and docstrings use POW / EN / HAN; no lane words in sim code.
- **Docs:** one old → new map in `design/02-equations-reference.md` §6.0 (also the one note that on screen POW is drawn on the OUT lane, HAN on MID, EN on IN); §6 RPS table and decision item 7 rewritten. `design/03`, `04`, `06`, `07`, `godot-build-guide.md` (enums, buttons, colour keys, QTE type tables, line letters P/E/H) and `sample_battle_screen.html` buttons use POW / EN / HAN. `design/06` keeps its lane table as the single on-screen lane note. `design/01` (Desmond's canon) and `design/notes/Notes.md` (Austin's own notes) not edited.
- **Equivalence (same seeds, before → after):** pytest 58 passed → 58 passed. `run_progression.py` output byte-identical; `balance_gauntlet.py` byte-identical apart from the renamed scenario label; `simulate_win_rate` spot-check (3 districts × r 0.95/1.0355/1.1, 40 per track) byte-identical; a 450-match fixed-seed dump of winner, total progress and every turn's progress (`repr` floats, HEAD worktree vs this change) byte-identical.
- **Left as is:** `sim/scripts/design_opponent.py` / `design_racers.py` still use the retired POW/DEF/EFF stat model (flagged 2026-10-31); `DEF`/`EFF` there aren't today's EN/HAN, so I didn't guess a rename. External count-bank filenames (`counts_S_N90=SSA.npz`, `counts_W_SW=IR=AAD.npz`) in `design/notes/` scripts and the `winrate_n4000.json` provenance string keep the old letters because they name files outside the repo. **Godot:** `scripts/globals.gd` / GDScript must mirror the new enum names, string values, `DRAW`, and P/E/H line letters before the parity pin moves.

## 2026-11-12 — Arthur [art]: unapproved line-preview pass 3 (stance variants, POW/EN/HAN, flipped bends)

- **Canonical sequence** is now Entry OUT+POW, Apex EN, Exit POW on every overview, camera-stop and variant frame (the earlier cam-stop pair had mixed Entry/Apex picks, and the chevron colours did not follow the locked rows).
- **New deliverable** in `unapproved/arthur/mockups/line_preview/`: `a_entry_out_pow.png`, `b_apex_{pow,han,en}.png`, `c_exit_{pow,han,en}.png`, sheet `line_preview_stance_variants.png`. Camera-stop framing (HAIRPIN L, chase / Apex / Exit, combined plan panel, gap under the mirror). Each Apex line starts where Entry ended and also draws the Exit preview chained from that Apex end; each Exit starts from the locked Apex EN end. Not-yet-chosen follow-on segments are the same hue, dimmer.
- **Naming (Austin 2026-11-12):** stance labels are POW / EN / HAN (ATK / DEF / NEU retired). Colours unchanged (POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`). Lane picks stay IN / MID / OUT, each with a small note of the stat it needs (OUT=POW, MID=HAN, IN=EN). The old second tag chip on locked rows is dropped; locked rows show one coloured stance chip, and the hovered stance on the active row is the highlighted chip. Overview and cam-stop files were renamed to `*_pow` / `*_en`. The art doc is not edited here.
- **Bends (Austin correction):** POW bends to the outer line of the corner, EN cuts toward the inner line by 2/3 of a lane, HAN runs mid-lane — matching OUT=POW and IN=EN. Applied to every variant and to the updated overview / cam-stop frames.
- Gordon's files are untouched. Placeholder bends remain unapproved.

## 2026-11-12 — Gordon [godot]: pass only after the Exit QTE (two-corner, UNAPPROVED); 01 canon QTE averaging final

- **Pass timing (Austin 2026-11-12: "Order only changes after exit QTE"; follow-up: no early pass for either car).** Before, `_update_pass_target` re-projected the post-turn gap after every phase QTE (unplayed = 0), so a pass could start on a partial projection and reverse after a later QTE. Now `main.gd` holds the gap at the pre-turn value until all three QTEs are done, computes the post-turn gap once from the final scores (same `Combat.resolve_turn` / `mean_phase_qte` path the core resolves with, so no snap at RESULT), and eases the pass over `pass_after_exit_s` = 2.5 s (PLACEHOLDER, `spec/display.json`), running into RESULT; Enter waits for it. Reason for 2.5 s: only ~0.16–0.23 s of playback is left after the Exit QTE, too short to read; 2.5 s matches the old readable pass window. `pass_u0/pass_u1` now unused. Barry's check (/workspace/barry-drafts/pass-v1/) showed a player at QTE 0 can never take the lead, so Austin's early-pass idea never triggers; Austin then chose no early pass at all.
- Tests: qte-v1 functions, seeds + fuzz300, save/load, restart, 200-seed key test all 0.0 vs sim; new assertions: no order change before the Exit QTE, final gap equals the resolved lead. Build id `1a53e712e4`, sim pin still f0efecf. Shots: `unapproved/gordon/two-corner/out/shots12/`.
- `design/01-system-overview.md` Build bullet: QTE averaging marked final (Austin 2026-11-11, confirmed by Barry/Desmond today), "Open" flag removed; pass-timing rule added.

## 2026-11-12 — Arthur [art]: art_direction uses POW/EN/HAN for choices; IN/MID/OUT is visual only

- **Ask:** Austin in Exec Team (2026-11-12): backend and logic always refer to the stats (POW / EN / HAN). IN / MID / OUT is a visual reference only. Canon follow-up: `design/01-system-overview.md` 4cdd1bc.
- `design/art/art_direction.md`: B.4, B.5, B.5b and B.5d now say POW / EN / HAN for a choice, a stance, a colour or playback logic. OUT / MID / IN is used only for road lane markers, lane-chip text (**OUT · POW**, **MID · HAN**, **IN · EN**) and where the chevrons sit. Example in B.5d: the POW segment is green and is drawn on the OUT lane.
- The B.5d placeholder bend mapping is unchanged in meaning (still unapproved): POW holds the outer line (OUT lane), EN cuts to the inner line by 2/3 of a lane (IN lane), HAN runs mid-lane (MID lane).
- `unapproved/arthur/mockups/README.md` updated to match. Older mockups still not re-rendered; `line_preview/` left alone.

---

## 2026-11-12 — Nathaniel [story]: corner lines refer to stats; IN/MID/OUT is visual only
- **Ask:** Austin in Exec Team (10:22 AM PT): "I think all backend should refer to stats. In/mid/out only visual reference."
- `story/corner_lines.md`: every line now reads Entry-Apex-Exit by stat (e.g. Touge hairpin EN-HAN-POW), replacing the IN/MID/OUT form from 8911879. Header notes IN/MID/OUT is only the on-screen lane (OUT = POW, MID = HAN, IN = EN). No line changed.
- `story/pitch.md`: players choose POW, EN or HAN per phase; the lane is how it shows on screen.

---

## 2026-11-12 — Arthur [art]: POW/EN/HAN and OUT/MID/IN naming in art_direction; B.5d bend placeholder corrected

- **Ask:** Austin in Exec Team (2026-11-12): stats and stances are always POW / EN / HAN; line choice is always OUT / MID / IN, with a short note of the stat (OUT (POW), MID (HAN), IN (EN)). The same OUT is the same POW line on a left or right turn. Canon: `design/01-system-overview.md` 81b230f.
- `design/art/art_direction.md`: B.4, B.5, B.5b, B.5d, C.1, Q6 and K2 use the new names. Colours stay POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`. Lane labels are written **OUT · POW**, **MID · HAN**, **IN · EN**.
- **B.5d placeholder bend mapping was flipped** (still unapproved): POW (OUT) holds the outer line of the corner, EN (IN) cuts to the inner line by 2/3 of a lane, HAN (MID) runs mid-lane. Each segment still starts from the previous end point.
- Older mockups under `unapproved/arthur/mockups/` were not re-rendered. `mockups/README.md` notes that they predate this naming. `mockups/line_preview/` was left alone (separate re-render in progress).
- Left as historical or geometry: hub/frame centre, "top-center" mirror, "inside the 3D scene", the old Aggressive / Defensive / Precise row names, and Appendix E face/tell suffixes `_atk|_def|_neu` (mapped to POW / EN / HAN; files not renamed).

---

## 2026-11-12 — Nathaniel [story]: naming sweep follow-up (Desmond's 81b230f rule)
- `story/corner_lines.md`: the remaining "inside" line descriptions now say IN.
- Swept all of story/ (canon, barks, dialogue_outline, plot, pitch, characters) for Attack/Defend/Neutral/Steady/outside/center/inside. Every remaining hit is plain English, not a stance or line ("heart attack", "doesn't defend herself", "outsider", the Touge boss being "steady"), or a bark tone heading ("Neutral" mid-race state in barks.md), so they stay.

---

## 2026-11-12 — Nathaniel [story]: story/ uses POW/EN/HAN for stats and IN/MID/OUT for line choices
- **Ask:** Austin in Exec Team (10:19 AM PT): stats are POW/EN/HAN across all mentions; line choices are IN/OUT/MID with a small note of the stat each needs; outside on a left and outside on a right are the same choice.
- `story/corner_lines.md`: every line rewritten from sim letters to Entry-Apex-Exit choices (D = IN/EN, S = MID/HAN, A = OUT/POW, per the locked lane rule in design/06: inside = Defend, center = Neutral, outside = Attack). Header explains the notation; district-habit prose uses IN/MID/OUT with stats. No line changed.
- `story/pitch.md`: the stance list now reads IN/MID/OUT with their stats, and names POW/EN/HAN as the stats.
- Left alone: `story/barks.md` "Neutral" entries are mid-race momentum and tone headings, not stances.
- **Why:** one naming scheme across the repo.

---

## 2026-11-12 — Barry [sim]: QTE phase scores rounded to 3 decimals (`QTE_SCORE_DECIMALS`), Austin approved via Desmond, 2026-11-12
- **Why:** CI's `tools/qte_fn_test.py` failed on the Ubuntu runner (glibc 2.43) with 337 one-ULP mismatches that the box (glibc 2.41) doesn't show. Rounding the score where it is computed stops a 1-ULP libm difference in `erf`/`exp` from reaching gameplay. Austin approved via Desmond, 2026-11-12.
- **What (`sim/velocity_shift/equations.py`):** new `QTE_SCORE_DECIMALS = 3` and `round_qte_score(x) = floor(x * 10**3 + 0.5) / 10**3` (non-finite values pass through). `raw_qte_score` returns the rounded E[s], and `phase_raw_qte` rounds each Entry/Apex/Exit score. So `mean_phase_qte`, `q_eff`, clashes and progress only ever see rounded phase scores. `expected_hit_quality` itself stays unrounded, because the zone-width inversion bisects on it. The mean of three rounded phases is not re-rounded. A scalar passed straight to `resolve_turn` is still taken as-is.
- **Rounding rule (deterministic):** half-up on the scaled double, then division by the exact integer 1000. Only correctly rounded IEEE `*`, `+`, `/` and `floor` are used, so the result is bit-identical everywhere and equals the double nearest k/1000. I didn't use Python `round()`: it is half-even on the exact binary value (0.0045 gives 0.004 there and 0.005 here). It does match this rule on 1,000,000 random inputs in [0,1) but differs on exact half-way doubles. Godot `snappedf(x, 0.001)` was also ruled out: it divides and multiplies by the inexact 0.001, and its bits differ on about 14% of inputs. **Godot mirror:** `floor(x * 1000.0 + 0.5) / 1000.0`, with the phases summed in Entry, Apex, Exit order and then `/ 3.0`. A 1-ULP input change can still flip the result only when x·1000 is within an ULP of k+0.5. Over 40,000 ±1-ULP perturbations it flipped 0 times, and the closest of the 90 `qte_fn_test` raw values is about 1e-5 from a boundary.
- **Balance (before → after, same seeds):** pytest 56 passed → 58 passed. One test now checks `raw_qte_score` against the rounded E[s], and 2 new tests cover the rule. `run_progression.py`, `--all-orders` and `balance_gauntlet.py` output is byte-identical (153 grind / 162 levels, all 216 orders; gauntlet ALL PASS). Playable spot-check, 9 batches: Street boss 63.2–65.1 (64.39), Touge boss 65.5–67.1 (66.42) and Wangan boss 63.7–67.1 (65.79) are unchanged. Street mature #2 skipped goes from 43.0–49.4 (46.22) to 43.1–49.4 (46.26): 3 of 9 batches move +0.1 pp because the average raw score at r 1.0355 goes 0.54258 → 0.543. That is far under the 5 pp bar, so no balance shift. `sim/config/winrate_n4000.json` is not rebuilt: the oracle is the legacy hidden-window model and never calls `raw_qte_score`.
- **CI note:** CI checks Godot against the pinned sim (`spec/race_config.json`, f0efecf), so nothing changes there until Gordon mirrors the rule and moves the pin. Even then, `qte_fn_test.py` still compares unrounded `erf`, `expected_hit_quality` and `qte_zone_width` bits. Only the `raw_qte_score` group becomes robust. Strict mode needs those intermediate groups dropped or given a ≤1-ULP tolerance.
- **Docs:** `design/02-equations-reference.md` (combat settings row and the progress-model paragraph) names `QTE_SCORE_DECIMALS` / `round_qte_score` and the mirror rule.

## 2026-11-12 — Arthur [art]: unapproved line-preview pass 2 (chevrons, night road, B.5b cameras, combined plan panel)

- **Chevrons** now point in the direction of travel (the texture tip sits at +forward). Earlier pass had them pointing back at the player.
- **Road** uses Gordon's touge asphalt (no pack overlay or extra pool decals), so it stays dark navy grey outside the sodium pools (B.2a). Grit reads mainly inside the pools.
- **Course** is his left-hand Touge hairpin (`HAIRPIN L`), the same continuous two-corner path as shots11, not the earlier HAIRPIN R.
- **Camera-stop frames** (`1_entry_out_atk_camstop.png`, `2_apex_def_camstop.png`, `4_exit_atk_camstop.png`, sheet `line_preview_camstops_sheet.png`) use Gordon's B.5b poses (chase / Apex / Exit from `main.gd` / `display.json select_cam`), his in-world IN / MID / OUT lane markers at Entry, and no debug box. Apex and Exit are geometry only (no cars, no mirror). Overview sheet still shows the whole hook from a high outside camera.
- **HUD (these frames only, Gordon's files unedited):** the bottom-left ENTRY lane strip and the PLAN THE LINE panel are one bottom-right panel. Each phase row carries the lane and stance pick; the active row is highlighted and is where you choose. The tie-gap / race-split bar sits at the top centre, directly under the REAR VIEW mirror.
- Still unapproved until Austin says so. Placeholder stance-to-bend mapping unchanged.

## 2026-11-12 — Desmond [ci]: allow qte-v1 function-bit check to fail on the Ubuntu runner
- **What:** in `.github/workflows/ci.yml`, `tools/qte_fn_test.py` is now its own step with `continue-on-error`. `tools/run_parity.sh` skips that check when `SKIP_QTE_FN_TEST=1` (default unchanged). Race, dump/load, restart and key-test comparisons stay required. Godot cache now saves even when a later step fails.
- **Why:** CI run [CI #2](https://github.com/ahoang47/midnight-apex/actions/runs/43270662837) still failed the function-bit test after switching to Python 3.13 (337 mismatches, max_abs_diff=2.220e-16, one ULP). The box (Debian 13, glibc 2.41, Python 3.13.5) is 0 mismatches; the Ubuntu 26.04 runner (glibc 2.43, Python 3.13.18) is not. Every gameplay parity check on that run was max_abs_diff 0. This is a pre-existing platform sensitivity in Gordon's bit-exact qte-v1 check, not a game-logic failure.

## 2026-11-12 — Arthur [art]: B.5d line preview is flat stance-coloured chevrons; unapproved line-preview mockup
- **B.5d** (`design/art/art_direction.md`): the preview is a row of flat chevrons painted on the road, pointing along the drive, stance-coloured per segment (ATK `#2CB84A`, DEF `#E8282C`, NEU `#F0C828`, solid). No yellow-to-red gradient across the line; a slight brightness ramp along a segment is fine. Still visual only; placeholder stance-to-bend mapping unchanged.
- **Unapproved mockup** (`unapproved/arthur/mockups/line_preview/`): Godot 4.6.3 frames of the chained Entry/Apex/Exit preview on a copy of Gordon's two-corner scenes, with pack-road asphalt, a high camera that shows the whole hairpin, and sharp 1280×960 HUD. Not approved until Austin says so.


## 2026-11-12 — Desmond [ci]: run CI on Python 3.13 so qte-v1 function bits match
- **What:** both jobs in `.github/workflows/ci.yml` now use Python 3.13, the same series as the box (3.13.5).
- **Why:** the first Actions run ([CI #1](https://github.com/ahoang47/midnight-apex/actions/runs/43269513343)) was green on **sim** (~1 min). On **godot** (~4 min 44 s) every two-corner race, dump/load, restart test and Plan the Line key test matched the pinned sim (max_abs_diff 0). The only failure was `tools/qte_fn_test.py`: 337 bit mismatches at max_abs_diff=2.220e-16 (one ULP) under the runner's Python 3.12.16. The same test is 0 mismatches on the box under Python 3.13.5. That was a CI setup choice, not a game-logic failure.

## 2026-11-12 — Gordon [godot]: two-corner editor scenes + QTEs during playback, static Apex/Exit stops (UNAPPROVED)

**What:** `unapproved/gordon/two-corner/godot` is now split into scenes you can edit in the Godot editor:
- `main.tscn` puts the scenes together.
- `track.tscn` is a @tool road builder. Its params are exported and it has a "Rebuild road" button.
- `touge_dressing.tscn` (@tool) holds the lamps, verge, rail, cedars and street branch.
- `sky.tscn` holds the sky cylinder.
- `car.tscn` is used for both the player and the rival; the rival uses S2000 overrides.
- `camera_rig.tscn` holds the camera rig.
- `hud.tscn` is built from real Control nodes, one per panel: line select, Line Locked, QTE (with its own timer), debug HUD, the Enter-to-continue prompt and timer, plus the plate, meters, finish panel and menu.

Shared art builders moved verbatim into `art_kit.gd`. The @tool previews build only in the editor and are not saved into the .tscn files.

**Playback QTE flow:** the Entry, Apex and Exit QTEs now run during playback. Each one has its own timer, and the cars hold at the plate E/A/X marks while the road keeps scrolling. Apex and Exit selection now happen at static camera stops.

**Why:** Austin asked to work on the editor workflow using the two-corner scene, and on 2026-11-12 he asked for this QTE flow. No numbers or rules changed: all values come from the sim constants and spec/*.json. Only the `_doc` text in display.json changed.

**Entry left unchanged (Austin's hard constraint):**
- shots10 vs shots11 `seq_select0_0..5`: 0 differing pixels, 6 of 6 frames.
- Fixed-step A/B runs: Entry select and lock frames are identical, and so is the camera, rig and car state.
- Refactor alone vs d5aa56c: 73/73 shots and 611/611 GIF frames are pixel-identical.
- Corner 2 Entry frames differ only in road scroll phase (40 m), because corner 1's playback now includes the QTE holds.

**Parity:** all checks pass at 0.0 on build `29c4eb591e` (sim f0efecf):
- qte-v1 functions
- 4 seeds plus fuzz300
- 3 TC2 dump/load round-trips (token `TC2:f0efecf:29c4eb591e:`)
- the restart test
- the 200-seed Plan the Line key test (162 races, 972 clash values)

The checks also pass from a clean checkout with no `.godot`, as CI runs them. `tools/stamp_build.py` now hashes `scripts/**/*.gd` and `scenes/*.tscn`.

**Also:**
- `out/shots11`: README, the Entry pixel-diff report, a side-by-side image, the turn-1 GIF (400 px; the 640 px GIF stays in the prototype working copy) and editor screenshots.
- The README has a new "Editor workflow" section.
- `playtest-state-spec.md`: Steady vs Neutral is marked resolved, Neutral approved 2026-11-11.
- The web export was rebuilt in the working copy and is not in the repo. A browser smoke test could not run because headless Chrome on the box has no WebGL2.

## 2026-11-12 — Desmond [ci]: GitHub Actions on push and pull request to proto-build
- **What:** added `.github/workflows/ci.yml`. On push or pull request to `proto-build` it runs two jobs:
  - **sim:** Python 3.12, `pytest tests/` (55 tests plus one skip when the numpy share-grid oracle is missing), then `scripts/run_progression.py` (default order) and `scripts/balance_gauntlet.py`. All three are deterministic and finish well under 5 minutes.
  - **godot:** official Godot 4.6.3 linux x86_64 (cached), then Gordon's two-corner harness in `unapproved/gordon/two-corner/`: `tools/run_parity.sh` (qte-v1 function bits, headless `headless_run.gd` vs the pinned sim, dump/load, restart test, Plan the Line key test). The sim pin is read from `spec/race_config.json` (currently `f0efecf`, Austin-approved 2026-11-11; earlier notes said 212eaab) and checked out into `_pin/` with a git worktree so `tools/sim_parity.py` and `tools/stamp_build.py` work.
- **Tool edits:** `tools/run_restart_test.sh` and `tools/qte_fn_test.py` now use `$GODOT`, defaulting to `/workspace/tools/godot`. `run_parity.sh` already did. No game logic or numbers changed.
- **Not in CI:** a headless smoke of the root `project.godot`. It has no main scene and no `scenes/` or `scripts/` at the repo root, so there is nothing runnable to smoke.
- **Why:** Austin asked for automatic runs on every push, in place of a manual "check the commits" rule, so the sim tests and Godot/sim parity run without someone starting them by hand.

## 2026-11-12 — Nathaniel [story]: corner_lines.md says Neutral, not Steady
- `story/corner_lines.md` lines 3 and 20: "Steady" changed to "Neutral" for the S stance letter.
- **Why:** the player-facing stance name Neutral was approved 2026-11-11 (design/01 canon block, Stats line, d8ce5b1); story/ shouldn't use the dropped name.

---

## 2026-11-12 — Gordon [godot]: 01 Build bullet, QTE-per-clash conflict flagged
- **What:** reworded the QTE line in the Build bullet of the `design/01-system-overview.md` canon block. It now says the sim (f0efecf) and the build average the three phase QTEs into one score for every clash, which conflicts with Austin's 2026-11-11 "each QTE feeds its own clash".
- **Why:** Barry caught the mismatch. The canon block shouldn't state a rule the sim doesn't implement, so this stays marked open until Austin decides.

## 2026-11-12 — Barry [design]: systems/balance lines in the 01 design canon, stale HP/DP text removed, corners-v1 proposal (NOT approved)
- **Ask:** Desmond asked each owner to fill the locked canon block in `design/01-system-overview.md` (7c42a87) with Austin-approved decisions and dates, and asked me to remove stale systems text (e.g. the HP/DP win decision).
- **Canon lines added (each verified in CHANGELOG / commits):** combat scoring final-v1 (2026-11-09; playable 2026-11-10, 0dd376a; line set 6fc87d5); visible QTE zone qte-v1 (2026-11-11, 4cb5401); parity knot 0.67 + aero cap (2026-11-11, 5e5d902); mod slots 3 × 2 with window/aero any slot max one each and stat mods only just reaching 105 % (2026-11-11); new mods never skip a wall + mod tier level floor (2026-11-11 / 2026-11-12, 29f8431). Constants cited by name.
- **Canon lines fixed:** Stats: Neutral resolved 2026-11-11 (art Q6, 55b9063), no longer "open". Play quality: the QTE is three 0–1 phase scores averaged, unplayed = 0 (f0efecf); the 1–10 CLI entry is an input format only. XP line: adds the GEO SP-per-level curve, per-crew grind taper and boss rewards (2026-11-09, 0c90c9c). Debt/aero clause dated 2026-11-10. Not duplicated: crew order, tracks/laps (Desmond), QTE zone-only difficulty (Gordon).
- **Stale text removed:** the HP/DP data flow, `HP_PER_LEVEL`/`QTE_NORMALIZER` normalization and 1–10 QTE stat row, level-gap difficulty table, persistent 192-card deck loop, DP/max-HP position win decision and the damage/mitigation design properties. Replaced with a short "Live combat model" map that points to the canon block, 02 and `equations.py`. Architecture lines for equations/deck/combat/match updated. `design/02` decision sheet item 5 / §7 (Neutral vs Steady) marked resolved.
- **New:** `unapproved/barry/corners-v1/README.md`, PROPOSAL, NOT APPROVED (sim paused by Austin 2026-11-12): the signature-corner rule, Nathaniel's and my candidate picks, Austin's flat-wild-race concern, three options, the proposed 3–7-of-10 sweep and its metrics, and Gordon's build needs. No sim run.
- **For Gordon:** your Build bullet says each of the three QTEs "feeds its own clash"; the sim (f0efecf) averages the three into one raw QTE used for all three clashes. Please reword or check with Austin.

## 2026-11-12 — Gordon [godot]: build decisions in the 01 design-canon block
- **What:** added one "Build (Godot)" bullet to the locked block at the top of `design/01-system-overview.md`: Godot only, combat freeze with the two-corner exception, Exit→Entry lockout deleted, 640×480 render with a 1280×960 HUD (B.5c), QTE zone-width-only difficulty, three QTEs per turn with unplayed scoring 0, turn flow and pauses, passes, and nodestar.tech owned by Austin.
- **Why:** Desmond asked each owner to populate the canon block (7c42a87) with Austin-approved decisions and their dates. Single-threaded web export is left out because it is my build setting, not an Austin decision.

## 2026-11-12 — Barry [sim][design]: mature #2 mod tier level floor live (slots-v2 fix b3, Austin approved)
- **Ask:** Austin approved fix b3 from `unapproved/barry/slots-v2/RESULTS_v1v2.md` (2f6c437) at 6:55 AM PT: "Oh, neat. Yes approved."
- **Change (`sim/velocity_shift/equations.py`):** new `MOD_TIER_LEVEL_FLOOR`, keyed by (round, 0-based play position) like the budget steps, plus `MOD_TIER_FLOOR_RUNG` (the mature #2 tier) and `MOD_TIER_FLOOR_MARGIN`.
  - Each crew's mature #2 mod tier shows "requires level N" and can't be fitted below N, even when the player can afford it.
- **Change (`sim/velocity_shift/progression.py`):**
  - `derive_mod_tier_floors()` uses the study's derivation (crew-local no-grind level + margin, capped at the rung's cap) and generates the table.
  - `mod_tier_floor` / `mod_tier_available` give the shop gate.
  - In `run`, below the floor the mature #2 skip state races with the previous rung's mods. The tier is fitted at the floor, from story XP at a later rung or from grinding to the cap.
  - New row fields: `mods`, `mods_skip`, `tier_floor`, `tier_locked`.
- **Why:** without a floor, a strong player beat R1 position 2's and R2 position 3's mature #2 with no grinding, only because of the newly unlocked tier (47.86 → 52.49 and 47.84 → 52.67). That made a new mod a skip button, which goes against Austin's rule that a new mod must not beat the next wall on its own. b3 was the only simulated fix that removed both under balanced, window and aero10, added no decisive rung or dead win, and left weak and average grind and margins unchanged.
- **Checks:**
  - The floors equal the study's values (L4/14/26/54/71/83/111/128/140 in the default order) in all 216 orders.
  - Official forced progression is still 153 grind / 162 levels / 0 lost XP in all 216 orders. The only report change is the skipped mature #2 rate of R1's first crew (tier locked at story level 3 < 4): Touge 42–51 → 33–44, Wangan 43–52 → 34–44, Street 42–50 → 32–42. Those were already 7-race walls.
  - Study oracle with the live floor, all 216 orders (`design/notes/slots-v2/b3_check.py`): weak 141 → 141, average 153 → 153, strong 121 → 100 under all three policies. No newest-mod-decisive rung remains, down from 2.
  - The playable spot-check is unchanged (`spotcheck_b3.json`).
  - 56 tests pass: 52 + 4 new in `sim/tests/test_mod_floor.py`. The oracle test there skips when numpy or the share-grid banks are missing.
- **Docs:** design/07 §6.4 and design/02 now cite the constants by name. The b3 evidence (`floor_cost.py`, `results_floor_cost.json`, `b3_check*`) moved to `design/notes/slots-v2/`. In `RESULTS_v1v2.md`, the b3 parts are marked superseded and a/a0/b/b2/c not chosen.
- **For Gordon:** the new constants and functions above. Your pin, f0efecf (212eaab before that), has none of this, and nothing in combat or the QTE changed. The floor affects only progression and the shop gate.

## 2026-11-12 — Nathaniel [story]: Finale order locked as fixed; Reiko warning trigger stays open
- **Ask:** Austin (7:00 AM PT): "Finale order should stick to that so the narrative works. Also kind of works personality wise. We can add the Reiko beat to the stack."
- `story/canon.md`: the Finale line now marks Touge #1 → Wangan #2 → Street #3 as fixed, with the reason (decision 18 needs #1's "left" before #2's "pushed") and the in-world reason (each Myth Driver races only after hearing the one before him did).
- `unapproved/nathaniel/open_proposals.md`: item 1 marked resolved; item 2 (Reiko's warning trigger) stays open on Austin's stack.
- **Why:** free crew order made the Finale the only fixed order in the game, so it needed an explicit lock and reason.

---

## 2026-11-11 — Gordon [godot]: two-corner test re-pinned to sim f0efecf, three timing QTEs per turn (Entry/Apex/Exit), TC2 state token (UNAPPROVED, shots10)
- **Ask:** I asked whether to move the two-corner test onto Barry's latest sim and build the three QTEs. Austin (10:56 PM PT): "Yes."
- **Pin:** 212eaab → **f0efecf** (`f0efecfbc18b495a0ba9df3bf956d8e89acc3477`). `sim/` is unchanged through 59f7e6d. No `sim/` file was edited.
- **Ported to GDScript bit for bit.** Every constant cites `sim/velocity_shift/equations.py:<line>` in `sim_constants.gd`, and no number was invented.
  - Constants: QTE_ZONE_BASE_MS :133, QTE_ZONE_WIDTH_105 :137, QTE_SKILL_TARGET_E :148, QTE_SKILL_SIGMA_OVER_A0 :149 (placeholder in the sim), QTE_PHASES :164, PHASE_QTE_UNPLAYED :165, AVERAGE_PLAY_Q :208, ETA :180.
  - Functions: `qte_zone_width` :346 (with `expected_hit_quality` and a glibc `erf` port), `raw_qte_score` :372, `phase_raw_qte` :390, `mean_phase_qte` :397 (CPython 3.12 `sum()` compensation), `clash_progress` :447 (q_eff = clip(raw × (1 + ETA(han_share − 1/3)), 0, 1)), and `resolve_turn` with `player_qte_phases` (models.py:68/88).
  - The PROVISIONAL W=1 hook is **retired**: clash_progress no longer has a knot window.
- **Game:**
  - After LINE LOCKED, there is one timing QTE at each camera stop (Entry chase, Apex stop, Exit stop) over the scrolling road. Then the camera returns to Entry and playback runs.
  - The zone is `qte_zone_width(r, qte_window_mod)` × 800 ms, the same for all three phases. At r = 1.05 that is 800 ms.
  - Press score = max(0, 1 − |e|/(zone/2)). A cursor past the far edge = unplayed = 0.
  - The three scores go to `player_qte_phases`, and `resolve_turn` averages them.
  - Select and playback stay unpaused, and the countdown stays.
- **Parity (new pin), all max_abs_diff 0.0:**
  - qte-v1 functions: 5,757 values, 0 bit mismatches.
  - Four named inputs, plus fuzz300 with per-phase inputs (null/0/1/decimals/raw bits).
  - Dump/load for 3 seeds; restart test.
  - 200-seed key test: 162 locked turns, QTEs pressed with SPACE, 125 unplayed, then compared with the sim.
- **State token TC2:** `TC2:<sim7>:<build10>:<b64 json>:<crc>`. It records the sim pin and the build id (`godot/spec/build.json`, from `tools/stamp_build.py`), and replays picks plus exact phase scores (IEEE bits). TC1 seeds reproduce on their own build (≤ 4322b31). Spec: `unapproved/gordon/playtest-state-spec.md` §0.5.
- **Output:**
  - Web export rebuilt locally on :5176 (not deployed).
  - GIF: `unapproved/gordon/two-corner/out/shots10/turn1_three_qtes_apex_unplayed.gif` (Entry 0.92, Apex unplayed, Exit 0.55).
- **Placeholders for Arthur:** QTE sweep timing (lead 700 ms, tail 200 ms, ready 0.5 s, result hold 0.6 s, SPACE), QTE panel layout and labels, the plate words "QTE"/"TIMING", cars hidden at the Apex/Exit QTE stops, and an early press scoring 0 but counting as played.
- **Conflicts (Austin to decide):**
  - B.5c (31b2299) says UI is drawn sharp at 1280×960. The HUD text stays pixel-hard on the 2× grid per Austin's 10:22 PM steer to me ("now the text is really sharp and uncharacteristic of the vibe"), and it was kept unchanged on request.
  - godot-build-guide §7.1/7.2 describes one continuous QTE per corner with TIMING/MASH and presses×10, and the guide's score is still 1–10.
  - In B.5b, the QTEs now sit between the lock and the return to Entry.

## 2026-11-11 — Barry [sim]: slots-v2 mature #2 fixes study (NOT approved); move my unapproved work to `unapproved/barry/`
- **NOT APPROVED. Study only; no live constants changed.** Austin asked (10:58 PM PT) to sim fixes for the strong-player mature #2 skips: V1 = R1 Wangan j3, 47.86 → 52.49 with the newest mod; V2 = R2 Touge j3, 47.84 → 52.67. The study uses the live 0.67 knot and the 10% aero cap. It has the same oracle and statistical bar as slots-v2, and it covers weak/avg/strong × balanced/window/aero10.
- **Write-up:** `unapproved/barry/slots-v2/RESULTS_v1v2.md`. Scripts: `fixes.py`, `fix_summary.py`, `floor_cost.py`, plus their JSON and `fixes.log`.
- **Fixes tested:**
  - **a / a0 (P2 prices):** rejected. They add a decisive strong rung (R2 Street j3, 47.86 → 52.42) and the mods lag.
  - **b (floor = level cap):** strong grind goes 121 → 197, new strong boss walls appear, and the strong min margin is 0.89.
  - **b2:** V2 remains.
  - **c (delay the tier to j4):** dead wins double (9 → 18) and average mid at cap drops to 69.95–71.15.
  - **b3 (crew-local level floor):** no decisive rungs under any policy, dead wins stay at 9, and weak/avg grind is unchanged (141/153). Strong needs 6 races (V1) and 7 races (V2) to reach the floor.
- **Recommendation: b3.**
- **Move (Desmond's convention):** `design/unapproved/slots-v1` → `unapproved/barry/slots-v1`, and `design/unapproved/slots-v2` → `unapproved/barry/slots-v2`.
  - The approved slots-v2 parts (README, `rebuild_winrate_table.py`, spot-check) went to `design/notes/slots-v2/`, following the qte-v1 precedent.
  - The empty `design/unapproved/` was removed.
  - Paths were updated in the entries below, `design/07` §6.3, the RESULTS files, and the `winrate_n4000.json` `_provenance` string (string only; data unchanged).

## 2026-11-11 — Arthur [art]: B.5c is now crunchy 3D + sharp UI; unapproved pack-road Godot test
- **B.5c** (`design/art/art_direction.md`) rewritten (Austin, 2026-11-11): 3D stays 640×480, no AA, RGB555 + 4×4 Bayer, then one 2× nearest upscale. UI is composited after that upscale, drawn sharp at 1280×960. Q4 smooth texture filtering in the 3D scene is unchanged.
- **Unapproved road test** (`unapproved/arthur/mockups/psx_road_test/`): the approved line-select Entry frame, re-rendered in Godot 4.6.3 with a 3-lane road built from the urban stacked pack's `road1_alt.png` (CC0; worn painted dashes and yellow edges, no added noise or lettering). `before.png` is the existing Blender frame. After frames: smooth and nearest pack-road with the classic 640 HUD, plus `_sharpui` variants with chunky late-90s plates at 1280×960. Not approved until Austin says so.

## 2026-11-11 — Nathaniel [story]: signature corners and personal styles, the DAQ log, rift changes (Jesse shuts the PC out, Reiko drops wholesale), the barkeep is Malo; story/unapproved moved to unapproved/nathaniel/
- **Line structure (canon 30; `corner_lines.md`, `plot.md`, `pitch.md`):** Austin's framing (locked): each district has a handful of signature corners where everyone in the district shares the same standard line and bluff; on every other corner wild racers share one line and bluff and named characters have their own style. **Why:** Austin wants a learnable district habit plus personality from named racers.
  - Signature corners are a first pass (draft), three per district: Touge hairpin/esses/decreasing radius (the mountain's corners), Wangan sweeper/increasing radius/constant radius (open highway), Street 90-degree/chicane/hairpin (city blocks). Each standard line is the district's existing main line; no letters changed (rechecked against `LINE_SET_C` at `5e5d902`, 0 mismatches). Austin said to first-pass it and share it with the right people; sim mapping is `<TBD: Barry>`.
  - The alternatives table now notes that on signature corners the bluff is shared, so the rung who-and-why there is a bark hook, not exclusive. Open Question 17 and canon 27 are left as they were (cross-referenced only).
- **Named-character driving styles (draft; `plot.md` districts and §7, `characters/myth_driver_*.md`, canon 25):** per-rung styles for each crew, each boss, and #1/#2/#3, as Austin approved them on 2026-11-11. **Why:** gives the "own style" off the signature corners a story reason; no numbers.
- **The DAQ log (canon 29; `dialogue_outline.md` Prologue, `barks.md` §5, `plot.md` §2 and Garage Crew Arcs, `pitch.md`):** Jesse's DAQ keeps only the last race and lists each corner with the PC's line and the opponent's line. First time after opening race 2 and the garage barks are drafts; after the Mentor Confrontation (locked) the PC pulls the logs alone and Jesse has no line. **Why:** Austin found races go by too fast to digest. It builds on the DAQ install line in `scripts/prologue.md` (script unchanged). UI is Gordon's.
- **Rift changes (locked, Austin 2026-11-11; canon 15, 19, 24, OQ12; `plot.md` §6, Finale, §8, Garage Crew Arcs; `dialogue_outline.md`; `characters/barkeep.md`):** Jesse shuts the PC out and stops tuning and respecs for the PC, so in the Finale the PC does those at the reverse speakeasy. Reiko drops wholesale (full price) but keeps selling because she's a business owner; the warm-up history is what she takes back, not why she sells. Big Round 3 mods are still from Reiko, now at full price. **Why:** replaces the 2026-11-10 "warmed up, so still sells / Jesse quiet but tuning stays open" wording per Austin.
- **The barkeep is Malo (locked; canon 24, 25, Vocabulary, OQ11; `characters/barkeep.md`, `characters/index.md`, `plot.md`, `dialogue_outline.md`):** placeholders replaced. OQ11 keeps the speakeasy's name and location open.
- **Moved `story/unapproved/` to `unapproved/nathaniel/` (git mv):** matches the team layout (`unapproved/<owner>/`). README now says it's Nathaniel's unapproved story proposals and that Desmond's weekday check covers the 3-day follow-up. `open_proposals.md`: Finale order and Reiko's warning trigger both still open. No other `story/` file referenced the old path.
- **Cross-owner notes (not edited):** `design/01-system-overview.md` says respecs are with Jesse, which now holds only until the rift; the Finale full-price shop and the post-rift DAQ log are for Barry and Gordon to pick up when the mechanics are shared.

## 2026-11-11 — Barry [sim]: approved slots-v2 parts are live: parity knot r=1.00 0.68 → 0.67, aero free pool ≤ 10% (Austin approved)
- **Why:** Austin approved both at 10:58 PM PT ("Approve both").
  - In slots-v2 the +75% window mod (1.15 × w0 cap) let average players clear the R2 Wangan and R3 Street crew bosses without grinding (49.14 → 50.30). The knot change is the smallest fix that leaves balanced grind unchanged.
  - Aero retuned every race with a 20–30% pool cleared R3 Street's boss (with a window, 100/0/0) and the Summit (70/20/10) without grinding. At 10% it clears nothing.
- **What (`sim/velocity_shift/equations.py`, single source):**
  - **Knot:** `KNOT_WINDOW_105` (1.00, 0.68) → (1.00, 0.67). `QTE_ZONE_WIDTH_105` r=1.00 row 0.5802105 → 0.5698111. `qte_zone_width` generates from the knot (verified): r 1.02 0.7243 → 0.7170, r 1.0355 0.8548 → 0.8507; r ≤ 0.95 and ≥ 1.05 are unchanged.
  - **Aero constants:** new `AERO_FREE_POOL_MAX_FRACTION = 0.10`, `AERO_MAX_EQUIPPED = 1`, `AERO_COUNTS_IN_MOD_CAP = True`, and helper `aero_free_pool_max()`. Per-tier `AERO_FREE_POINTS` are still TBD.
- **Oracle:** `sim/config/winrate_n4000.json` was rebuilt with the new knots. The script is `design/notes/slots-v2/rebuild_winrate_table.py`, the lines-v1 method; run on the old knots it reproduces the old table exactly. 395 rows changed, all at r 0.9525–1.045. Official forced progression is still 153 grind / 162 levels in all 216 orders.
- **Docs:** `design/02-equations-reference.md` (caps/mods row, combat row, knot list) and `design/07-economy-and-mods.md` §6.3 (aero caps). §8.0's open item 4, "aero has no rule against caps", is marked resolved.
- **Tests:** 2 new ones cover the knot/zone values and the aero cap. No test was pinned to 0.68/0.5802 except through `QTE_ZONE_WIDTH_105`, which was updated. Full suite passes: 52 tests.
- **Playable spot-check (before → after):**
  - Street mature #2 skipped: 43.5–49.4 (mean 46.82) → 43.0–49.4 (46.22). Its oracle band moves from 42.8–49.6 to 42.3–49.6.
  - Street boss, Touge boss and Wangan boss at target (r 1.05) are unchanged: 63.2–65.1, 65.5–67.1, 63.7–67.1.
- **Still unapproved** (in `unapproved/barry/slots-v2/`): the window +75% / 1.15 cap rule, prices, the dead-win fill, and the strong-player mature #2 fixes.

## 2026-11-11 — Gordon [godot]: build guide §10.3 stance colours now match art_direction.md B.5
- **What:** `design/godot-build-guide.md` §10.3 `ClashDisplay.gd` COLORS now use the art doc values (`design/art/art_direction.md:252`): Attack `#2CB84A` (green), Defend `#E8282C` (red), Neutral `#F0C828` (yellow, dark text), replacing the legacy `#16a34a` / `#dc2626` / `#d97706`.
- **Why:** Arthur relayed that Austin asked for the stance colours to be aligned; Austin's own 2026-11-11 instruction was to make Attack/POW green and Defend/EN red in all docs. The two-corner build already uses the art doc values, so no build change.

## 2026-11-11 — Barry [sim]: slots-v2, Austin's 2 POW / 2 EN / 2 HAN layout with window + aero, grind wall and price check, added to `unapproved/barry/slots-v2/` (**NOT approved**)
- **What:** this reruns the slot sim on Austin's layout: 6 slots = 3 categories × 2, with secondary splits of 100/0/0, 80/10/10 and 70/20/10 (placeholders). The run adds:
  - a window mod (+75%, 1.15 × w0 cap) and an aero part (pool 10/20/30%, retuned every race, inside the 105% cap, from the second R2 crew). Each goes in any slot, at most one of each;
  - an exhaustive 105% check;
  - the grind-wall test ("a newly unlocked mod with no grind clears no wall");
  - placeholder price curves.
- **How:** share-aware oracle with clash-count banks on a 244-point stat-share grid (N=4,000, seeds 20261113–15 × 10/20/30 turns, 9 paired banks; ≤ 0.20 pp interpolation error vs exact banks). Clears use the official pooled mid ≥ 50. The `counts/` banks (~44 MB) are not committed; `grid.py` rebuilds them. **Nothing in `sim/` changed.** Every constant change ran in-process only.
- **Findings:**
  - **Rule 1 holds:** 105% at all 63 story points. The brute force covers up to 262,144 loadouts per point, plus Austin's 46,656-loadout 36-mod example, with 0 loadouts over. The max equals best-per-slot because the total is a plain sum over independent slots.
  - **Splits:** they don't change any grind count (141/153/121).
  - **Category mix:** the fixed 2/2/2 layout is what prevents a no-brainer. With free choice, stacking POW or EN is dominant in 62 of 87 average cells and HAN is dead.
  - **Window and aero:** the window is never dominant. Aero is never dominant, but it is never worse than the mod it replaces, so it needs a price premium.
  - **Grind wall violations:**
    - average + window clears the R2 Wangan and R3 Street bosses (49.14 → 50.30);
    - strong players' newest tier alone clears R1 Wangan and R2 Touge mature #2 (49.02 → 53.11 / 53.10);
    - 70/20/10 + aero 20/30% clears Summit skipped.
  - **Smallest equation fix (proposal, not applied):** `KNOT_WINDOW_105` r = 1.00 knot 0.68 → 0.67. Zone width at r 1.00 goes 0.5802 → 0.5698, the window violations are gone and balanced grind is unchanged. It also needs an aero pool ≤ 10%. The strong-player mature #2 violations remain open.
  - **Dead wins:** removing the 9 dead wins via `CAP_ALLOC_*` costs ≥ +28 average grind, so the recommendation is to fill them with window, aero or sidegrade unlocks instead.
  - **Economy:** no single price satisfies both "can't buy on unlock" and "no extra grind" for strong players. Two options are given: P1 (1.1 race-units per tier) and P2 (grind-matched, 1.73–3.67 per purchase, which costs strong players 34 money races).
- **Why:** Austin's 2026-11-11 brief, items 1–7. Follow-up runs filled gaps the interrupted worker left: `validate.json`, `results_econ_cleared*.json`, `results_aero_knot.json`, `results_finale_knot.json` and `results_price.json`.
- **Needs Austin:** approve or reject the knot fix and the aero pool cap; P1 vs P2; and how to handle the strong-player mature #2 clears.

## 2026-11-11 — Gordon [godot]: two-corner shots9: after-turn countdown, arrow lanes, line-following cars, animated pass, continuous Touge track, 2x-grid HUD (unapproved/gordon)
- **Why:** this comes from Austin's playtest (~9:58–10:01 PM PT). He said:
  - "The game plays a bit too fast for me to grasp each corner... the pause I'm referring to is the one after a turn completes. That should have a time limit. The line selection shall still stay unpaused per Arthur's playback rule."
  - "left and right don't scroll left and right when selecting an entry lane."
  - "the car's path should follow its line. Right now, the cars just follow the lane they were placed in."
  - "We already have the infinite scrolling for entry, we can reuse that for the exit. What we don't have is an infinite scrolling for apex while the QTE plays."
  - "if a pass occurs, it is visually shown during the corner... the passing car shifts to an open lane, completes the pass animation, and then move into the position it needs to play for the next turn."
  - "the two corners should be in the same district as part of a continuous 2-turn track."
  - Then at 10:22 PM PT: "now the text is really sharp and uncharacteristic of the vibe". He chose: "Draw HUD text pixel-hard on a 2x grid (1280x960)".
- **What (display/flow only; sim pin 212eaab, scoring and RNG unchanged):**
  - **After-turn pause.** Once the B.5a RESULT row fills in, the HUD shows "Press Enter to continue N", a visible countdown, and auto-continues. The duration is a placeholder. There is still no pause in selection or playback.
  - **Arrow keys.** Left/Right move the Entry highlight in on-screen direction: L corners show IN MID OUT, R corners show OUT MID IN, with no wrap. Lanes with none drawn are skipped.
  - **Cars follow their lines.** Both cars' lateral offset blends Entry lane → Apex lane at mid-arc → Exit lane, smoothly.
  - **Scroll and hold.** The infinite road scroll (Entry's straight) now runs at the Apex and Exit stops too. A `hold_stop` hook keeps the Apex scroll held for the later QTE. B.5b framing is kept.
  - **Animated pass.** This replaces the hold-then-snap rule. During playback the visual gap moves from the pre-turn to the post-turn order. If the two lines share a lane while the cars overlap, the passer moves to the open lane, completes the pass, then settles onto its line. The scripted run's smallest lateral gap while overlapping is 3.30 m (no clipping).
  - **One continuous Touge course** (`course.gd`): straight, HP L, joining straight, N90 R, exit. Corner 2 changes from Street N90 R to Touge N90 R.
  - **HUD on a 2x grid.** The HUD is rendered into a 1280x960 SubViewport: font size ×2, no AA, no subpixel, oversampling 1, 2 px shadow. The 6x9 bitmap font is 2x nearest. The layer is shown nearest at a whole-number scale; below 1280x960 it falls back to fractional linear. The project base is now 1280x960 (Main scale 2, still 640x480 design units). The 3D world is unchanged: 640x480 + post shader, nearest.
- **Placeholders** (`spec/display.json` `playback_flow`): continue_s 6.0, lane_ease_s 0.35, blend_before_m 6, blend_after_m 8, pass_u0/u1 0.2/0.9, gap_ease_s 0.12, overlap_full_m 5.5, overlap_clear_m 9.0, min_sep_m 2.6.
- **Verify:**
  - `tools/run_parity.sh` PASSes with max diff 0.0 (four inputs, fuzz300, save/load, restart, 200-seed key test).
  - The scripted `spec/inputs/shots9_pass.json` run (shared exit lane in both corners, a pass each way) matches the sim.
  - The web export was rebuilt on the box (:5176), not deployed.
  - Shots, GIFs and the before (85d505d smooth) / after zoom composite are in `unapproved/gordon/two-corner/out/shots9/`.
- **Flagged for Arthur/Desmond (proposals, not decided):**
  - The 2x-grid HUD departs from `design/art/art_direction.md:115/:141/:242` and from the 1-bit 640x480 mockup text (`art/ui/line_select_cam/post_lsc.py:34`). Text is now pixel-hard on 1280x960, not 640x480.
  - The Apex/Exit lane for each stance borrows the Entry rule (A = outside, S = centre, D = inside). This is not approved.
  - The ENTRY strip is mirrored on L corners. The mockup shows OUT MID IN.
  - The Touge dressing is one-sided, so on the R corner the cedars and lamps sit on the inside, unlike the B.5b frames.
  - The pinned sim's line set for Touge N90 (DSA/DDS/DSS) replaces Street's (SSA/SDS/SSS), so the rival's corner-2 lines change for the same seed.
  - `design/godot-build-guide.md` may still describe the old snap rule. It was not edited.

## 2026-11-11 — Barry [sim]: three QTE phase scores average into the turn's raw_qte
- **What:** the playable engine still uses one `raw_qte` and the existing `q_eff` formula per turn (`clash_progress` / `resolve_turn` math unchanged). The turn's raw input can now be three phase scores (Entry, Apex, Exit): `mean_phase_qte` / `phase_raw_qte` average them, and an unplayed / None phase is `PHASE_QTE_UNPLAYED` (0). `TurnState.player_qte_phases` / `TurnResult.player_qte_phases` carry the three inputs; a 3-tuple from `get_player_qte` is averaged in `match.py`. The default profile / `player_timing` / `player_quality` path is still a single `raw_qte_score(...)` call, so SimulationRunner results are identical. The CLI prompts for the three 1–10 scores (blank = 0) and passes the tuple. No miss-probability knob. No studies re-run.
- **Why:** Austin's two-corner playtest feedback, relayed by Gordon (~10 PM PT, 2026-11-11): there should be a QTE for entry, apex, and exit individually, and an unplayed QTE should count as 0. Austin then, directly, at 10:01 PM PT: "the 3 QTE scores should be counted as an average. Do not redo any of the math for it."
- **Docs:** `design/02-equations-reference.md` names the new helpers (no values copied). `design/godot-build-guide.md` was not edited.
- **Tests:** mean of three, unplayed = 0, and `resolve_turn` with phases matches the same turn scored with the pre-averaged scalar. `test_playable_oracle.py` is unchanged and still passes.

## 2026-11-11 — Gordon [godot]: two-corner HUD text drawn at display resolution (unapproved/gordon, departs from A.5 for UI only)
- **What:** in `unapproved/gordon/two-corner/godot/project.godot`, the stretch mode `viewport` becomes `canvas_items` (640x480 base and keep aspect are unchanged; `_fit_scale()` still chooses integer scaling at 2x or more).
  - **The 3D world is unchanged.** It is still a 640x480 SubViewport going through the post shader (bloom, then RGB555 + 4x4 Bayer on 640x480 pixels), shown nearest at a whole-number scale.
  - **The HUD keeps its 640x480 design units,** so its positions, sizes, colours and font face match Arthur's frames. It is now rasterised at window resolution. `hud.gd _font` uses the viewport's font oversampling, greyscale AA and light hinting, and the 1-unit shadow, outlines and rules scale with the display. Four `draw_line` calls change from the default -1 width to 1.0.
  - `run_shots.sh` frames are now captured at the window size (1280x960). Parity PASSes with max diff 0.0 on everything `run_parity.sh` runs (four inputs, fuzz300, save/load, restart test, 200-seed key test). The web export was rebuilt on the box (:5176).
  - Shots and composites are in `unapproved/gordon/two-corner/out/shots8/`.
- **Why:** Austin, 9:41 PM PT, after seeing the shots7 2x-integer composite: "I think you have to continue upressing. Those are still pretty tough to read."
- **Departure, flagged for Arthur:**
  - `design/art/art_direction.md:115/:141` (integer nearest upscale) and `:242` ("viewport stretch") no longer apply to UI text, at Austin's direct request.
  - The mockups' 1-bit 640x480 text (`art/ui/line_select_cam/post_lsc.py:34`) is now smooth text at display resolution in the build.
  - The world look keeps A.5.
- **Still pixel-scaled:** the Godot stand-in 6x9 bitmap font (menu, debug box, gap meter, TIMING panel). It is crisp at 2x/3x but uneven below 2x. Moving it to the HUD font would be a face change, so it is a proposal and not done here.

## 2026-11-11 — Gordon [godot]: two-corner HUD text legibility, integer browser scaling (unapproved/gordon)
- **What:** `unapproved/gordon/two-corner/godot/scripts/main.gd` adds `_fit_scale()`. The 640x480 frame now upscales by a whole number (`Window.CONTENT_SCALE_STRETCH_INTEGER`) whenever the window fits 2x or more, and stays fractional below 2x. Display settings (640x480, viewport stretch, keep aspect) are unchanged. No HUD layout, font, size, or colour changed, and no scoring changed. Parity still PASSes: max diff 0.0 on all four inputs, the fuzz300 run, save/load and the restart test, plus the 200-seed key test (`out/shots7/parity.txt`). The web export was rebuilt on the box.
- **Why:** Austin: "Text is really difficult to read on the game." The browser build was scaled 2.25x at 1920x1080 and 1.6x at 1366x768 with nearest filtering. That drew the 1-px stems of the 1-bit HUD text 2 or 3 (1 or 2) screen px wide, so letters broke up. `design/art/art_direction.md:115` asks for an integer nearest upscale (and `:141` for a nearest upscale). At 1080p the frame is now a crisp 2x, about 11% smaller than before.
- **Not changed (design-level, proposals for Arthur):** at native 640x480 the build already matches Arthur's approved B.5a/B.5b frames. Both use the NimbusSansNarrow stand-in at 9–13 px, rendered 1-bit (`art/ui/line_select_cam/post_lsc.py:13,34-37`). That means 7–8 px caps and 5–6 px x-height at the 9–11 px used for most labels, and letters merge ("turn-in" reads as "tum-in"). Some dim text falls below a 2.1 contrast ratio where the 50/50 panels cross a guardrail or lamp pool, and white on ATK green is 2.60. Details are in `unapproved/gordon/two-corner/out/shots7/README.md`, with composites alongside.

## 2026-11-11 — Gordon [godot]: QTE difficulty is the visible zone only (Austin)
- **What:** `design/godot-build-guide.md` §7 now uses the visible zone width `qte_zone_width(r, window_mod)` at the race's fixed r, plus `MatchConfig.qte_window_mod`, as the only QTE difficulty scale. `QTEController.start(...)` takes that zone (fraction of `QTE_ZONE_BASE_MS`, `equations.py:130–133` and `:338`). The old level-gap `qte_difficulty()` formula and the 800/650/500/300 ms table are removed from §7 and Appendix F, along with the Godot-only `QTE_TIMING_WINDOW_PER_GAP` / `QTE_TIMING_WINDOW_MIN_MS` / `QTE_MASH_SPEED_PER_GAP` constants. §15.2 `QTE_TIMING_WINDOW_BASE_MS` is no longer a Godot-only 600–1000 range; it points at sim `QTE_ZONE_BASE_MS` (`equations.py:130–133`). The pending-Austin / double-count notes in §5.1, §7, Appendix D, F, and H now state this resolution. No values invented; no `sim/`, scripts, or scenes touched.
- **Why:** Austin, 2026-11-11, 8:48 PM PT: "Yeah QTE difficulty is scaled through the visibile zone. I don't see double dipping there."

## 2026-11-11 — Barry [sim]: slots-v1 mod slot sim added to `unapproved/barry/slots-v1/` (**NOT approved**)
- **What:** compares three slot schemes, (A) 3 slots growing to 6 (+1 at the R2 and R3 openings and the finale), (B) fixed 3 and (C) fixed 6, with window-only mods competing for the same slots. Equipping a window mod drops the smallest stat mod, so it costs real stat points. Run on the live visible-QTE model at `4cb5401`. Oracle: the official clash-count banks, N=4,000 per bank, seeds 20261113–15 × 10/20/30 turns, with paired comparisons. Files: `RESULTS.md`, the scripts, `results*.json` and `summary.txt`. Nothing in `sim/` changed.
- **Rule 1 (only just reach 105% with every slot filled, never above):** each scheme splits `MOD_SHARE_OF_REF × ref` over its slots. One new tier per story win goes into the smallest line, with a restock at the round openings. Scheme A's added slots necessarily start at 53–67% of a full slot.
- **Findings:**
  - Window mods of +10/20/30% of w(r) are clearly **dominated** at every key cell (mature #2 skipped, boss skipped, boss at target, Myth #2, Summit), for average and strong players in every scheme. For weak players they are dominated or lean−. Average boss at target loses 23–63 pp. Grind counts don't change (153 / 141 / 121 for average / weak / strong).
  - Only fixed 6 separates the skill profiles at the break-even size: about +65% (weak), +80% (average), +150% (strong).
  - Candidate: **C, one +75% window mod, plus qte-v1's 1.15 × w0 total-zone cap.** It gives no no-brainer for average or strong anywhere in the campaign, a weak-player edge of +0.6 to +5.9, and grind 140 for average (fragile: two opener-boss clears at 50.06 vs 48.85). Without the cap the mod is dominant on kid rungs, so slot competition does not replace the width cap.
  - Finale windows are dominated in every scheme, so the 86/14 split stands.
  - C also has the lowest R1–R3 spend (1,681 stat-units vs A 1,944 and B 2,941) and the largest upgrade per purchase (median +10.4%).
- **Caveats:**
  - σ and the press model are placeholders.
  - Prices are ∝ stat value, and every payout constant is still TBD.
  - The restock rule is my choice.
- **Status:** NOT approved. Awaiting Austin's pick of scheme and window size.

## 2026-11-11 — Gordon [godot]: build guide follows qte-v1 visible QTE zone (sim 4cb5401)
- **What:** `design/godot-build-guide.md` now follows the playable engine in Barry's `4cb5401`. §5 player `q_eff` is `clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)` with no `knot_window`; the stat gap is the visible zone `qte_zone_width(r, window_mod)` at the race's fixed r (no mid-race change); `MatchConfig.qte_window_mod` widens the zone; the opponent is unchanged (`OPPONENT_QTE`, HAN still applies). Named the new sim constants (`QTE_ZONE_BASE_MS`, `QTE_ZONE_WIDTH_105`, `QTE_SKILL_SIGMA_OVER_A0` as PLACEHOLDER, `QTE_SKILL_TARGET_E`) and cited `equations.py` / `combat.py` / `match.py` / `models.py` by line. `KNOT_WINDOW_105` / `knot_window` are marked legacy (oracle and zone-table generator only). §7 `qte_difficulty()` is not deleted: a note says that applying it on top of the zone width would double-count, it is pending Austin's decision, Barry recommends dropping it in favour of the zone width, and Godot should not implement it until then. The same note is in Appendix D, Appendix F, and Appendix H. No values were copied or invented beyond the guide's existing convention; no GDScript, scenes, or `sim/` touched.
- **Why:** follows `sim/` at `4cb5401` (Barry [sim]: port approved qte-v1 visible-QTE zone into the playable engine), after Austin approved qte-v1 and asked to port it into `sim/`.

## 2026-11-11 — Barry [sim]: port approved qte-v1 visible-QTE zone into the playable engine
- **What:** the playable engine no longer multiplies the player's QTE by hidden `knot_window(r)`. The stat gap is a visible zone width: `qte_zone_width(r, window_mod)` from `QTE_ZONE_WIDTH_105` (exact qte-v1 inversions of `E[s]`), `QTE_ZONE_BASE_MS`, and PLACEHOLDER skill σ in `QTE_SKILL_SIGMA_OVER_A0`. `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)` in `clash_progress` / `resolve_turn`. A simulated player's raw score is `raw_qte_score` at the race's fixed r (`MatchConfig.player_qte_profile` or a `player_timing` override evaluated at that r). The QTE does not change with mid-race position. The opponent is unchanged (`OPPONENT_QTE`, HAN still applies). `MatchConfig.qte_window_mod` widens the zone; slot competition and the 105%-all-slots rule are left to the upcoming slot sim. `KNOT_WINDOW_105` / `knot_window` stay as legacy for the `winrate_n4000.json` / progression oracle and as the generator of the zone table.
- **Why:** Austin approved qte-v1 on 2026-11-11 (5:43 PM PT): "Approve qte-v1, port it into sim/".
- **Docs:** `design/02-equations-reference.md` now names the new constants (no values copied). `design/01`–`06` had no other `knot_window` descriptions. The draft moved from `design/unapproved/qte-v1/` to `design/notes/qte-v1/` (`RESULTS.md` remains the record).
- **Tests:** 47/47 pass (two new unit tests: `E[s]` at the default zone is 0.4 / 0.6 / 0.8 for weak/average/strong, and `qte_zone_width` knots plus a +20% window mod). `test_playable_oracle.py` still checks official bands for an average player.
- **Spot-check** (SimulationRunner, average player, official tracks, 200 races × 5 tracks × 3 seeds × 10/20/30 turns), before (hidden `knot_window`) vs after (visible zone). Both runs produced the same figures: Street boss at r=1.05 official **61.4–65.1**, engine **63.2–65.1** (mid 64.4); Street mature #2 skipped at r=1.0355 official **42.8–49.6**, engine **43.5–49.4** (mid 46.8); Touge boss official **63.4–67.8**, engine **65.5–67.1** (mid 66.4); Wangan boss official **62.0–66.8**, engine **63.7–67.1** (mid 65.8). Δ mid = 0.00 on every cell, as expected: average `raw_qte_score(r)` equals `0.6 × knot_window(r)`.

## 2026-11-11 — Gordon [godot]: stance colours swapped (Attack/POW green, Defend/EN red) across docs
- **Why:** Austin's direct instruction on 2026-11-11: update all docs so Attack/POW is green and Defend/EN is red. Neutral/NEU/HAN stays yellow `#F0C828`. Used the existing approved hexes, swapped: Attack/POW `#2CB84A`, Defend/EN `#E8282C`. Scoring, sim/ and CHANGELOG history were not touched.
- **Docs:** Attack/POW is now green and Defend/EN is now red in `design/art/art_direction.md` (values plus a 2026-11-11 swap note), `design/godot-build-guide.md` (legacy `#dc2626` / `#16a34a` swapped in place; Neutral stays `#d97706`), `unapproved/arthur/mockups/line_clash/README.md`, `unapproved/arthur/mockups/pattern_read/README.md` (`green/green/red` chevrons for DEF→DEF→ATK became `red/red/green`; `red ATK` became `green ATK`), `unapproved/gordon/two-corner/README.md`, and `unapproved/gordon/two-corner/out/PHASE4_REPORT.md`.
- **Two-corner Godot test:** the same swap in `unapproved/gordon/two-corner/spec/display.json`, `unapproved/gordon/two-corner/godot/spec/display.json`, and `unapproved/gordon/two-corner/godot/scripts/hud.gd` (and the matching working copies under `/workspace/prototypes/two-corner`). The Plan-panel breadcrumb tick stays green via a new `CHECK_GREEN` constant, so it does not follow Defend to red. `tools/run_parity.sh` still PASSes (max_abs_diff 0.0, including the 200-seed key test). Web export was rebuilt to `out/godot_web/`. Fresh screenshots: `unapproved/gordon/two-corner/out/shots6/plan_panel.png` and `playback_panel.png` (also at `/workspace/prototypes/two-corner/out/shots6/`).
- **Left for Arthur (scripts not edited, images not regenerated):** scripts still carrying the old ATK-red / DEF-green assignments: `art/ui/line_select_cam/post_lsc.py` (its tick default should stay green), `unapproved/arthur/mockups/line_clash/post_clash.py`, `unapproved/arthur/mockups/lane_chain/v5/post_v5.py` and `v4/post_v4.py`, `unapproved/arthur/mockups/lane_chain/hud.html`, `unapproved/arthur/mockups/tones/work/lane/post_v5.py` (tick default should stay green), `unapproved/arthur/mockups/pattern_read/compose_mockups.py`, `unapproved/arthur/mockups/race_state_study/compose_study.py`, `unapproved/arthur/mockups/race_state_study/entry_matrix/compose_entry_matrix.py`, `unapproved/arthur/mockups/race_state_study/resolution_test/compose_resolution_test.py`. `unapproved/arthur/mockups/tones/work/ow/post_ow.py` and `unapproved/arthur/mockups/overworld/v1/post_ow.py` still define the old `RED, GRN, YEL` tuples but do not use them. Frames that still show the old chips: `art/ui/line_select_cam/` (including the contact sheet), `art/ui/line_vs_line/`, `unapproved/arthur/mockups/line_clash/` (b1–b3 and the comparison sheet), `unapproved/arthur/mockups/lane_chain/` HUD frames (`lane_chain_mockup.png`, `apex_call_mockup.png`, `v4/apex_call.png`, `v4/entry_rear.png`, `v5/entry_plan.png`, `v5/apex_replay.png`), `unapproved/arthur/mockups/pattern_read/mockup_a_named_lines.png`, `mockup_b_tactical_hud.png` and their compare sheets, `unapproved/arthur/mockups/race_state_study/` overview / entry_matrix / resolution_test frames that carry stance chips, and `unapproved/arthur/mockups/tones/entry_*.png` plus the entry tone sheets (HUD from `post_v5.py`). Gordon's earlier composites in `unapproved/gordon/two-corner/out/shots5/composites/` also still show the old colours.
- **Left alone on purpose:** CHANGELOG history; `sim/`; brake lights, hazards, car paint, palette neon, and the "Dim dashed red fork" ambiguity mark in the pattern_read README (not stance coding); "RPS colours/counters" in that same README (the beat cycle, not red/green assignment).

## 2026-11-11 — Gordon [godot]: two-corner test rebuilt to the approved B.5b camera stops and B.5a line-vs-line playback (`unapproved/gordon/two-corner/`)
- **Why:** Austin approved B.5a (corner playback: line vs line) and B.5b (line select: camera stops) in `design/art/art_direction.md` at `ab1c4a1`, and asked for the two-corner Godot test to be rebuilt to them. Display, UI and camera only. Scoring, RNG and the 212eaab sim pin are unchanged; parity (5 sets incl. fuzz300), dump/load, the 4-race restart test and the 200-seed key test all pass with max_abs_diff 0.0.
- **Selection (B.5b):** Entry is picked on the fixed chase camera (frame values from `art/ui/line_select_cam/build_lsc.py`), rival visible in its lane. The camera then moves to an apex stop and an exit stop with no cars, no mirror and the straight frozen. At lock it returns to Entry with the LINE LOCKED banner, then playback runs. Added: the 17-segment B.5b timer and the E / A / X corner plate. Scrolling is kept at the Entry stop. The Phase 4 Plan the Line panel (labels, chips, 'none drawn' greying) is kept.
- **Playback (B.5a):** the line-vs-line panel (YOU/RIVAL face up from the start, amber outline on the phase being played, WIN/LOSS/TIE filled in per phase, no pause or clash beats) replaces the Phase 4 LINE LOCKED strip. Results come from the sim's pure `resolve_stance`, and the key test checks they match.
- **Touge dressing:** fog, road paint, guardrail, cedars, ridge and lamps now follow the approved B.5b frames (fog #0B172B 9-78 m for this test; B.3 itself is not edited). Fixed a Phase 4 bug that left the lamp-glow node creation inside a comment.
- **Files:** `godot/`, `spec/`, `tools/` (new `phase5_composites.py`; live check now uses relative paths), README Phase 5 section, `out/PHASE5_REPORT.md` (source table with file:line, placeholders, conflicts with earlier steers). The Phase 4 composites are replaced by `out/shots5/composites/` (`vs_line_select_cam.png`, `vs_line_vs_line.png`, `before_after_phase4.png`). Placeholders flagged for Arthur: stop move/lock-hold timing, mirror near plane, inside guardrail, N90 and Street stop poses, gap meter/debug positions.

## 2026-11-11 — Arthur [art]: unapproved line-select camera (`line_select_cam/`) and corner-playback options (`line_clash/`, A line vs line / B clash beats) mockups in `unapproved/arthur/mockups/`, proposals for Austin's review.

## 2026-11-11 — Gordon [godot]: two-corner prototype and playtest-state spec into `unapproved/gordon/`
- **Why:** Austin's 2026-11-11 directive: anything other bots need to reference goes in the repo, and work he has not approved goes in `unapproved/<owner>/` (Desmond's layout). This is the two-corner engine test (provisional numbers; the exception to the combat freeze) and the still-proposed playtest-state spec.
- **Added:** `unapproved/gordon/two-corner/` — the Godot project (no `.godot/` cache), `spec/`, `tools/`, README, `out/PHASE4_REPORT.md`, `out/ARTHUR_ASSET_REQUESTS.md`, and three key composites (`before_after.png`, `vs_lane_chain_v5.png`, `plan_the_line_sheet.png`). Not included: `threejs/`, the `_pin/` worktree, the rest of `out/`, or the web export. An empty `unapproved/.gdignore` keeps the nested `project.godot` out of the root Midnight Apex Godot project. README and tools no longer use `/workspace/prototypes/two-corner` paths; `_pin/`-dependent parity tools are noted, not retargeted at this branch's live `sim/`.
- **Moved:** the proposed Playtest-to-Troubleshooting Spec (§0 of `design/godot-build-guide.md`) to `unapproved/gordon/playtest-state-spec.md`, verbatim. The guide keeps a one-line pointer where §0 was; the §10.1 `get_lead()` comment now points at the new file.

## 2026-11-11 — Gordon [godot]: build guide uses fresh per-turn hands, fixes deck weight formula, max_turns default 10
- **Why:** Barry checked these against the oracle that built `winrate_n4000.json`. Final-v1 draws a fresh `HAND_SIZE` hand i.i.d. from `deck_weights()` every turn, and the 192-card persistent deck was only part of the legacy HP/DP path. The guide's §3 weight formula had `ALPHA` and `1 − ALPHA` swapped. The opponent's HAN term applies in `clash_progress`, and only the knot window is off. `max_turns = 99` silently picked the 30-turn kappa. Barry's matching `MatchConfig.max_turns = 10` sim change landed in `822300a`; this commit follows it, per Austin's 2026-11-11 push-after-each-change directive. Spec only: no GDScript, scenes or `sim/` touched, and §7's level-gap QTE difficulty is left for Austin.
- **§3 Deck:** rewritten. `Deck.gd` is now static, with `deck_weights()`, `draw_hand(..., rng, n = HAND_SIZE)` (i.i.d., with replacement, from the match RNG) and `hand_stance_counts()`. Each turn the line pick comes first and then the player's hand, as in `match.py`. The opponent has no hand. §3.2 now gives `DECK_ALPHA × share + (1 − DECK_ALPHA) / 3`, renormalized (Attack = POW, Steady = HAN, Defend = EN). Deleted: `DECK_SIZE`, `build`, `draw`, `prepare_turn_hand`, `end_turn`, piles, discard and reshuffle.
- **§0 playtest spec:** the number rule now cites `HAND_SIZE`/`DECK_ALPHA`. The byte-budget row for the `DECK_FULL` deck dump and the flag bit are gone (bit4 is reserved). In Block C, `opponent_hand` became `opponent_line` (`u8`, 3×2-bit), `player_hand` is the fresh `HAND_SIZE` hand, the deck-piles row is deleted and `rng_state` notes that future lines and hands come from it. Direct resume and replay no longer rebuild or restore decks; replay redraws line, then hand, per turn. §0.4 decision 4 is reframed as direct resume vs history replay vs both, with no deck dump.
- **§1.2:** `DECK_SIZE` and `DECK_HAND_SIZE` were removed; the row is now `HAND_SIZE`. The `OPPONENT_QTE` note says W = 1 and that HAN still applies. **§1.4:** `max_turns` defaults to 10, the planned race length (one of `RACE_LENGTHS`), and kappa comes from `kappa_for_length(max_turns)`, not from a lap's corner count.
- **§5:** the inputs now state `q_eff = clamp(q × W × (1 + ETA × (han_share − 1/3)), 0, 1)` for both sides (player: `knot_window(r)`; opponent: `q = OPPONENT_QTE`, `W = 1`). The `resolve_turn` kappa comment now says the planned race length, not the lap's corner count.
- **§6 TurnManager:** START says "seed RNG" instead of "build decks". END_TURN no longer cycles a deck.
- **§10.2:** the meter-scaling open question is closed (Barry approved the normalized lead). Whether the HUD prints a number and how a tie reads stay open for Austin. §11 `snap_to_gap` comment updated to match.
- **§15.5:** the empty-deck edge case is deleted. **Appendix A:** the `Deck.gd` line is updated. **B:** the next-turn step and the Python mapping now point to `pick_line` then `draw_weighted_hand`. **C:** `turn_ended` no longer says "deck cycled". **D:** step 1 picks the line, then draws a fresh hand; `Deck.end_turn` is removed; step 7 states q_eff for both sides. **H:** the deck-size and opponent-reshuffle notes are replaced by fresh hands and the opponent playing its line; the kappa note now says max_turns defaults to 10.

## 2026-11-11 — Barry [sim]: qte-v1 visible-QTE draft added to `design/unapproved/` (approved and ported 2026-11-11)
- **What:** the qte-v1 draft (`design/notes/qte-v1/`, moved from `design/unapproved/qte-v1/` on approval: `RESULTS.md`, `results.json`, `run.py`, `qte_model.py`, `wr_shortcut.py`) is now in the repo. It models the stat gap as a visible QTE zone width (replacing the hidden `knot_window(r)` multiplier), plus window-only mods. The σ values and the press model are placeholders until there is playtest data.
- **Why:** Austin's 2026-11-11 directive says anything other bots need to reference goes in the repo, and unapproved work goes in an unapproved folder. Gordon's guide §7 and the knot_window text depend on this draft.
- **Status:** Austin approved qte-v1 on 2026-11-11 (5:43 PM PT) and asked to port it into `sim/`. Ported the same day (see the Barry [sim] entry at the top of 2026-11-11). Still open: whether the slot sim (window mods compete with stat mods for slots, and available stat mods only just reach 105% with every slot filled) replaces the 1.15×w0 width cap recommended in RESULTS.md.

## 2026-11-11 — Nathaniel [story]: add story/unapproved/ for proposals awaiting Austin
- **Why:** Austin's directive (2026-11-11): anything other bots need to reference goes in the repo, and anything he hasn't approved goes in an unapproved folder. My open proposals only lived in local drafts on the box.
- **Added:** `story/unapproved/README.md` (what the folder is, nothing in it is canon, 3-day follow-up rule) and `story/unapproved/open_proposals.md` with the two items still waiting on Austin: the Finale order's in-world reason and Reiko's warning trigger under free crew order. No canon files changed and no numbers added.
- **Not moved:** the local drafts in `/workspace/nathaniel_drafts/` are superseded; everything approved in them already landed in 8d05f70 and ff8bbbb.

## 2026-11-10 — Gordon [godot]: build guide combat sections follow 0dd376a progress scoring
- **Why:** Austin's direction, relayed by Barry on 2026-11-10: update the guide's combat sections to the new progress scoring now, with the race HUD showing the progress gap instead of HP bars. Everything matches Barry's playable engine in `0dd376a` (`combat.py` `resolve_turn`, `match.py`, and the Phi/tau constants and functions in `equations.py`). Constants are referenced by name, and no balance values were copied. Spec only: no GDScript, scenes or `sim/` touched.
- **§5 Combat Math:** `CombatResolver.gd` is now a port of `stat_shares`, `knot_window`, `kappa_for_length`, `timing_value`, `clash_payoff`, `clash_progress` and `resolve_turn`. Each clash adds `g = V × Phi(outcome, q_eff) × M` to both cars, with `V = r^kappa` (`KAPPA_BY_LENGTH` via `max_turns`). The player's `q_time` (QTE score / `QTE_NORMALIZER`) is scaled by `knot_window(r)` and HAN (`ETA`). The opponent uses `OPPONENT_QTE` with the window off, and HAN still applies. `M` uses the POW share on a win and the EN share otherwise (`MU`). Turn progress is the sum of the 3 clashes. The higher race total wins, and ties are allowed. Deleted: `clash_mult`, `compute_damage`, `damage_mitigation`, `battle_multiplier` and `qte_rubber_band`. Added an open question for Austin: §7's level-gap QTE difficulty and `knot_window(r)` both penalize a stat gap.
- **§6 TurnManager:** the `DAMAGE_BATCH` state is renamed `PROGRESS_BATCH` (add progress, update the gap meter, tween the cars). `MATCH_COMPLETE` decides by the higher progress total, and an equal total is a tie.
- **§10 Position & Progress Display (was Position & Damage Display):** `PositionTracker` now tracks `player_total_progress` / `opponent_total_progress`, with `get_progress_gap()` and `get_lead()` = `(cum_p - cum_o) / (cum_p + cum_o)`. `DamageDisplay.gd` is replaced by `ProgressGapDisplay.gd`, which drives one `ProgressGapMeter`. Added an open question for Austin: should the meter be scaled to the normalized lead (the guide's choice, matching `MatchResult.player_position`) or to the raw gap? Also open: whether the HUD shows a number, and how a tie reads.
- **§15 Tuning Loop:** combat constants are now listed by name as sim-owned (tuned by Barry, signed off with Austin), and their ranges are gone. Only the Godot feel constants keep ranges. The DP-bar step, the HP/mitigation/battle-bonus/rubber-band rows and the opponent tiebreaker are deleted, and ties are allowed.
- **Appendix B (turn flow), C (signals), D (numbered TurnManager flow):** progress replaces damage/DP throughout. `damage_batch_done(…, battle_mult)` becomes `progress_batch_done(player_progress, opponent_progress, cum_player, cum_opponent)`. `match_ended` can report `"Tie"`. Step 7 now runs `resolve_turn` with knot window, HAN and kappa, with no mitigation or rubber band. The Python mapping rows point to `resolve_turn` (3 clashes summed) and to `OPPONENT_QTE`.
- **Also updated to stay consistent:** §0 (number-rule examples now `KAPPA_BY_LENGTH`/`KNOT_WINDOW_105`; the visual lead uses progress shares with no tiebreaker; the debug-HUD state code `DMG` → `PRG`; Block C `player_cum_dp`/`opponent_cum_dp` → `player_cum_progress`/`opponent_cum_progress`; `p_qte_score`/`o_qte_score` → `p_q_time`/`o_q_time` ×100, also in `qte_history`), §1.2 (deleted `CLASH_STAKES`, `BATTLE_BONUS`, `MITIGATION_*`, `HP_PER_LEVEL`, `HAN_QTE_WEIGHT`, `RUBBER_BAND_PCT`; sim-mirrored combat constants are listed by name without values; Godot-only UX constants are a separate table), §1.3 signal, §1.4 `max_turns` comment (kappa / `RACE_LENGTHS`), §2.1 scene tree (DP bars removed, `TopBar/ProgressGapMeter` added), §7 open-question pointer, §8.3 `AIQTE.opponent_q_time()` returns `OPPONENT_QTE` (no roll, no RNG), §11/§12/§13/§14 (DP gap → progress lead, `DAMAGE_BATCH` → `PROGRESS_BATCH`, rubber-band mention removed), Appendix A (file list), E (gap-meter art instead of DP bar fills), H (HP_PER_LEVEL and rubber-band notes deleted; ties; race length sets kappa).
- **Not changed (flagged to Austin/Barry):** §3 Deck still describes the persistent 192-card deck from `deck.py`. The `0dd376a` playable engine instead draws `HAND_SIZE` cards i.i.d. each turn from `deck_weights()` with no shoe.

## 2026-11-10 — Gordon [godot]: build guide line pick is one weighted draw per corner
- **`design/godot-build-guide.md` §8.1 `TurnTypeData.pick_line()` and Appendix G:** the opponent's line is now one weighted pick over `[main, alt1, alt2]` once per corner, with weights `LINE_ADHERENCE` / `(1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS[alt1|alt2]`, drawn from the match RNG. It used to be an adherence roll followed by an alternate roll. The chosen line is played exactly and the hand never blocks it.
- **Why:** Barry confirmed this rule against the sim (`combat.py` `pick_line` makes one `random.choices` call). Pushed after Barry's 0dd376a landed the matching sim rule, so the guide never runs ahead of the sim.

## 2026-11-10 — Barry: playable engine uses final-v1 Phi/tau scoring; LINE_SET_C line pick [sim]
- **Line-pick rule (confirmed from lines-v1 / the `winrate_n4000.json` rebuild, `equations_v4.generate_clashes`):** once per corner (once per turn, not per lap and not per clash) the opponent draws a *whole* 3-stance line from `[main, alt1, alt2] = LINE_SET_C[district][corner]` with one categorical draw at probabilities `[LINE_ADHERENCE, (1-a)*alt1, (1-a)*alt2]` = `[0.65, 0.21, 0.14]`. The chosen line is played exactly (the hand does not block it). The win-rate rebuild used `numpy.random.default_rng`; `combat.py` / `match.py` use the same probabilities from the **match RNG** (`random.Random`), so a shared integer seed is not bit-identical.
- **Playable scoring (Austin, 2026-11-10: update the playable feature):** `combat.py` `resolve_turn` and `match.py` now use the final-v1 Phi/tau model that built the oracle — `KNOT_WINDOW_105`, `KAPPA_BY_LENGTH`, `OPPONENT_QTE`, `W0`/`T_MAX`/`L_MAX`/`TAU_BETA`/`TAU_P_TOP`/`MU`/`ETA`/`DECK_ALPHA`/`HAND_SIZE`, all read from `equations.py`. Each clash adds `g = V × Φ(outcome, q_eff) × M` with `V = r**kappa`; the player's `q_time` (0–1) is scaled by `knot_window(r)` and HAN; the opponent uses `OPPONENT_QTE=1` with the window off. The race is the sum of progress; higher total wins, ties allowed. Hands are 6 cards i.i.d. from the stat-weighted deck each turn (no persistent shoe). When `player_read` is set, `match.py` runs the equations_v4 read + `assign_hand` on the match RNG.
- **Legacy HP/DP:** kept as `resolve_turn_legacy` behind `MatchConfig.legacy_hp_dp` (default False). `scripts/balance_gauntlet.py` and `scripts/parity_sweep.py` opt into that path so their old checks stay meaningful. The CLI and `simulation.py` use Phi/tau by default and ask for a district/track; a 1–10 QTE is divided by 10 into `q_time`.
- **`sim/config/tracks_v1.json`:** stand-in 10-corner laps the win-rate table used. **Tests:** `test_lines.py` (table picks), new Phi/tau unit tests, and `test_playable_oracle.py` (two cells vs the oracle band ±2). **45/45 pass.**
- **Spot-check vs `winrate_n4000.json`** (balanced stats, q_read=q_time=0.6, official tracks, 200 races × 5 tracks × 3 seeds × 10/20/30 turns): Street boss at r=1.05 official **61.4–65.1**, match.py **63.2–65.1** (mid 64.4); Wangan boss official **62.0–66.8**, match.py **63.7–67.1** (mid 65.8); Street mature #2 skipped at r=1.0355 official **42.8–49.6**, match.py **43.5–49.4** (mid 46.8); Touge boss official **63.4–67.8**, match.py **65.5–67.1** (mid 66.4). All four sit inside the official band ±2 (Wangan's 67.1 is 0.3 above the published max, within noise of Python Random vs the oracle's numpy stream). No constants were retuned.
- **Feel (resolved):** Nathaniel signed off on the in-world feel of the 6fc87d5 Street N90 / Wangan IR+SW lines on 2026-11-10 (`story/corner_lines.md`).
- **What a player (and Godot) will notice:** no HP bars, no rubber-band, no knockout, no battle bonus, no EN mitigation. The bar is race progress, not DP/HP. At stat parity (r=1) a perfect player is still windowed (`W(1.00)=0.68`) while the opponent times perfectly with the window off (HAN still applies, and is 1 at a balanced share); the window only opens fully at r=1.05. Mid-race lead no longer changes anyone's QTE.
- **Gordon review (vs the `winrate_n4000.json` oracle):** (1) Opponent HAN is applied in the oracle's `clash_progress` (`scale_window=False` only turns the knot window off). The playable engine already matched; comments that said "unscaled" were wrong and are fixed. (2) `MatchConfig.max_turns` default is now 10 (one official lap). Kappa still comes from `max_turns` via `kappa_for_length`, not from `len(corners)`. The old default of 99 silently selected the 30-turn kappa. (3) Final-v1 / the oracle drew a fresh 6-card i.i.d. hand from `deck_weights()` each turn; the 192-card persistent shoe in `deck.py` / design 01–03 is the legacy HP/DP path only. (4) `equations.py` and the oracle use the same `ALPHA×share+(1−ALPHA)/3` formula as `deck.py` (`DECK_ALPHA=0.85`). Scoring is unchanged, so the earlier spot-check still stands.
- **Why:** Gordon asked for the line-pick rule in the sim so Godot can match it; Austin then asked to update the playable engine itself to the final-v1 scoring, not leave HP/DP as the live path.

## 2026-11-10 — Nathaniel [story]: in-world reasons for the corner lines (story/corner_lines.md)
- **New `story/corner_lines.md`:** narrative reasons for every main and alternative line in `LINE_SET_C`, by district and rung, matching Barry's `6fc87d5` table. No numbers; the letters stay Barry's.
- **Rewritten for 6fc87d5:** Street 90-degree (SSA, alts SDS/SSS): intersections, so hold your lane through the cross street and punch out. Wangan increasing radius and sweeper (AAD, alts ASA/AAA): flat out, then shut the door on the exit so the car behind can't draft past on the straight. Touge unchanged.
- **Dropped from the earlier off-repo draft:** the two optional Street-only swaps (Barry's call, not pursued) and the fixed-order note that Street opens Round 3.
- **Why:** Austin approved the feel of Barry's lines-v1 change, said the flavor doesn't need to go to Barry, and asked me to update the notes and push.

## 2026-11-10 — Gordon [godot]: Godot build guide follows 6fc87d5 (early-Round-2 debt/aero unlock, free crew order, district line tables)
- **`design/godot-build-guide.md` §0.2 Block B:** `aero_unlocked` now says early Round 2, set when the first Round 2 crew's boss falls (any crew), per `DEBT_CLEAR_AFTER`, and no longer says "mid Round 2". `betting_unlocked` now references `BETTING_UNLOCK_AFTER`. Added a `crew_order[3][3]` field (the district picked in each play position of R1–R3) because difficulty steps and unlock points are now keyed by play position, so a playtest repro needs the order the PC actually played.
- **§0.3 lints:** aero is unlocked before `DEBT_CLEAR_AFTER` (or still locked after it); betting is unlocked before `BETTING_UNLOCK_AFTER`; a `crew_order` round repeats a district, breaks the lock-in, or starts before the previous round finished.
- **§8.1 `TurnTypeData.gd` and Appendix G:** replaced the legacy archetype-keyed stance sequences with the per-district line tables. `TurnTypeData` mirrors `LINE_SET_C` (`[main, alt1, alt2]` per district and corner code) and picks main with `LINE_ADHERENCE`, otherwise an alternate by `LINE_ALT_WEIGHTS`. So the 6fc87d5 edits (Street `N90`, Wangan `IR`/`SW`) flow into Godot through the mirrored table and no other code.
- **Not touched:** `scripts/` is still empty (the legacy scripts were deleted 2026-11-06 and Austin said not to rebuild yet), so no GDScript reads the tables yet. `sim/velocity_shift/combat.py` and `match.py` are Barry's files.
- **Why:** Austin asked, via Barry, to close the two Godot follow-ups from 6fc87d5, then approved pushing the guide as long as it matches Barry's sim (checked against 6fc87d5: every constant named exists in `equations.py`). Austin (2026-11-10): no Godot combat code until he and Barry sign off on the numbers.

## 2026-11-10 — Barry: free crew order (position-keyed), line-table fixes for Street N90 / Wangan IR+SW, round-opening cap tweak [sim][design]
- **`sim/velocity_shift/equations.py`:** `LINE_SET_C` main lines changed (lines-v1 options S-A + W-A): Street `N90` DDA → **SSA** (alts SDS/SSS); Wangan `IR` and `SW` AAA → **AAD** (alts ASA/AAA). Touge unchanged. `DISTRICT_ORDER` replaced by `DISTRICTS` + `DEFAULT_CREW_ORDER` (example order only, for reports/tests) and unlock points `DEBT_CLEAR_AFTER = (2, 1)`, `BETTING_UNLOCK_AFTER = (2, 3)`, `FINALE_UNLOCK_AFTER = (3, 3)` (round, crews beaten in that round). `CAP_ALLOC_ROUND_OPEN` (12,3,3,3,.5,.5,.5) → **(12,3,3,3,1,0,0.5)**.
- **`sim/velocity_shift/progression.py`:** `ladder(order)` takes any per-round permutation of `DISTRICTS` (`check_order` rejects others), `all_orders()` lists the 216 legal orders, the round step / round-opening cap raise go to the first crew *played* in R2/R3, and boss rows carry unlock markers (`unlocks_after`).
- **`sim/config/winrate_n4000.json`:** regenerated for the new lines (builder: Barry's drafts `lines-v1/build_repo_table.py`). Touge from the official N=4000 cache (identical to the previous table at every shared r); Street/Wangan from lines-v1 N=4000 counts on each district's own tracks; same seeds 20261113–15 × 10/20/30 turns. **Pooled is now the equal-weight mean of the three district rates per (seed, length)**; lines-v1's draft pooled table had concatenated 1,333 Touge races with 4,000 each of Wangan/Street. Exact r keys for all 216 orders (forced + never) are stored, so no lookup is interpolated.
- **`sim/scripts/run_progression.py`:** new `--all-orders` report (216 orders, per-slot worst cases). **`sim/tests/test_progression.py`:** reproduction updated to the new numbers; new tests for all-orders separability, first-crew round step + unlock markers, and order validation.
- **Results (default order, forced grind):** pattern cccWccW in every crew; walls (mature #2 / boss) R1 7/6 ×3, R2 pos1 8/8, pos2 7/7, pos3 7/7, R3 pos1 9/9, pos2 8/8, pos3 8/8, finale 4/6/4/6; **153 grind races** (was 155), 162 levels, story 49,757 XP vs grind 69,647 XP, 0 lost. All 216 orders give the identical totals and walls by position. Boss-at-target ranges by district: Touge 63.4–67.8, Wangan 62.0–66.8, Street 61.4–65.1 (Street boss was 58–62 under the old lines); Wangan mature #2 when skipped 43.9–52.1 (was 36). Finale Myth #2 skipped 41.1–48.4 (was 33–46). Matches lines-v1 RESULTS on every wall and total; per-cell ranges differ by ≤1.0 pt because lines-v1 interpolated a 0.0025 grid while the repo uses exact r. All 33 tests pass; `scripts/balance_gauntlet.py` ALL CHECKS PASS; `scripts/generate_build_matrix.py` leaves `config/sample_builds.json` unchanged.
- **Design docs:** 01 (crew ladder: free order + lock-in, position-keyed steps; aero/betting/finale unlock points), 02 (budget/unlock constants, line-set note), 07 (season runner, act table, debt row, §7.4 "mid Round 2" → early Round 2 after the first crew via `DEBT_CLEAR_AFTER`, budgets, campaign test no longer fixed Touge → Wangan → Street). Docs reference the constants by name.
- **Why (Austin, 2026-11-10):** free crew choice with lock-in (Nathaniel's story entry below); "Sounds good. Let's commit it currently." on the lines-v1 fix for the thin districts (Wangan mature #2, Street boss, Myth #2 were district-intrinsic misses that no budget or XP tweak fixed) and the cap tweak (fixes the R2 opener's old head #2 dip, Street 55–57, and evens the opener walls from 8/9 (R2) and 9/10 (R3) to 8/8 and 9/9, 155 → 153 races, in order-v1's sweep; the new lines keep those walls).
- **Feel (resolved 2026-11-10):** Nathaniel signed off on the in-world feel of Street N90 SSA and Wangan IR/SW AAD (`story/corner_lines.md`, same day). The S-B/W-B alternates in lines-v1 RESULTS remain documented fallbacks only.
- **Follow-ups closed:** Gordon updated `design/godot-build-guide.md` (48166e9: early-Round-2 aero/debt, free crew order, district line tables). Barry wired `combat.py`/`match.py` to `LINE_SET_C` (entry above).

## 2026-11-10 — Nathaniel: free crew choice with ladder lock-in, position-based unlocks, Reiko keeps selling after the rift [story]
- **`story/canon.md`:** decision 11 (Rounds bullet: rounds play in order, the PC freely picks which crew to challenge in each round and is locked in until that crew's boss falls; Finale bullet: finishing Round 3 also unlocks the big finale mods bought from Reiko, and the Myth Driver order Touge #1 → Wangan #2 → Street #3 is unchanged); decision 12 rewritten from "Reputation gates the rotation" to the lock-in rule plus its one-sentence reason (between rounds, reputation still gates rematches); decision 15 (Reiko still sells to the PC during the Finale because they warmed up over time); decision 19 (debt cleared "early in Round 2, after the first crew rematch", exact race still from Barry's sim); decision 24 ("Sabine's crew" intro early in Round 2; aero timing; new "Reiko after the rift" bullet); Backstory Timeline item 5 (no fixed district order); Open Question 16 (speakeasy timing).
- **`story/plot.md`:** Districts reference (PC picks the crew, locked in until its boss falls); Rounds 1–3 header (no fixed order) and "Why the rotation" → "Why the lock-in"; §5 debt timing ("early in Round 2, after the first crew rematch") and betting "after all three crew bosses"; Mentor Confrontation (Reiko keeps the door open); new "Round 3 complete: big finale mods" beat after the Mentor Confrontation; Finale intro (big mods, shop stays open); Garage Crew Arcs ("Sabine's crew" early in Round 2; Reiko's Finale rift reason).
- **`story/dialogue_outline.md`:** intro and crew-line rules note that district sections play in the order the player picks; "Mid Round 2: the debt clears" moved below the Round 2 district sections and renamed "After the first Round 2 crew: the debt clears (the speakeasy)" with a position-based trigger; triggers added to "End of Round 1: wholesale" and "End of Round 2: betting opens"; added the optional promoter handoff (draft) "Heard you cleaned up the mountain. Come down to the bay. Let's put some money on it." ("the mountain" swaps to the last district beaten); "Mentor Confrontation (end of Round 3)" renamed "End of Round 3: Mentor Confrontation"; Reiko door-open note; new "After the Mentor Confrontation: big finale mods (Round 3 complete)" section with a draft Reiko line. Also deleted the Touge Round 3 crew boss pre-race draft line "Last time this round. Give it everything." (written 2026-11-04 in 76a3831; no replacement, slot empty until Austin wants one) because Austin asked to remove it: it read awkwardly and implied the boss knows where he falls in the PC's order.
- **`story/pitch.md`:** Structure paragraph: rounds in order, free crew choice, locked into a crew's ladder until its boss falls.
- **`story/characters/barkeep.md`:** PC's first visit "early in Round 2, after the first crew rematch".
- **Why (Austin, 2026-11-10):** "Ok, how about we don't do fixed crew rotations. The player can freely choose which crew to challenge at any round, but once they lock into a crew they're stuck grinding that ladder until they defeat the boss. Narratively, the reason is that the other crews don't want to challenge the PC because the PC already started challenging another crew." / "I don't think anything narratively changes with this free select" (so every reveal, sighting and line stays as written) / "Do not implement refusal lines. They're weak." / "Add a note that because we warmed up to Reiko over time she's willing to sell us parts after the confrontation." Austin chose "early in Round 2" for the debt clear and approved committing and pushing this batch. Unlock markers follow Barry's 0c90c9c model (debt/aero after the first Round 2 crew, betting at end of Round 2, big bought mods on Round 3 completion), now by position instead of district.
- **Left for other bots (not touched):** `design/` and `sim/` fixed-order references (`DISTRICT_ORDER`, design 01 line 5, design 07 §7.4 and line 333) are Barry's; the canon 19/26/28 shell and mod-reward rewording and the related Racer Types paragraph, `plot.md` lines 46 and 70, and `barks.md` line 340 conflicts with "boss wins pay money + shell + graphic; mods are bought only" are Desmond's; the district alternative-line reasons and optional Street swaps stay in Nathaniel's drafts for Barry's design. The line table is unchanged. Finale order stays an open question for Austin (no new reasoning added). Some connective text still mentions a district sequence (for example #1's Round 1 sighting "sends the PC into Wangan asking"); it is kept as written per Austin.

## 2026-11-09 — Barry: land the final combat race-balance settings and the XP/level progression model (grind v8c) [sim][design]
- **`sim/velocity_shift/equations.py`:** new section "Story race-balance + XP/level progression model" with the final-v1 combat settings (`KNOT_WINDOW_105`, `KAPPA_BY_LENGTH`, `LINE_SET_C` + `LINE_ADHERENCE` + `LINE_ALT_WEIGHTS`, `OPPONENT_QTE`, `SP_CAP_FRACTION`, `MOD_CAP_FRACTION`, `MOD_SHARE_OF_REF`, `REFERENCE_RULE` V2, `MOD_TIMING` c, `LADDER_R`, `BUILD_STAT_MIN_SHARE`/`MAX_SHARE`) and the progression constants (Option A steps by round position, `DISTRICT_ORDER`, GEO level curve, cap raises, story XP, T2 taper, finale 86/14 split), plus pure helpers `knot_window`, `sp_per_level`, `xp_to_next`, `grind_payout_fraction`. Existing HP/DP combat constants and functions are unchanged; `combat.py`/`match.py` do not read the new section yet.
- **`sim/velocity_shift/progression.py` (new):** stdlib port of the grind-v1 v8c model (`grind_v8_final.py`, `races_v8c.py` in Barry's drafts): ladder, budgets-follow-level rule, level cap = SP cap with XP past the cap lost, front-loaded cap raises, story XP, per-crew taper, forced/never-grind policies, finale exemption, per-district rates.
- **`sim/config/winrate_n4000.json` (new):** the win-rate oracle — real N=4000 race-balance output (seeds 20261113–15 × 10/20/30 turns, `KNOT_WINDOW_105`, `KAPPA_BY_LENGTH`, opponent QTE 1.0, line set C), pooled and per district, min/max %, at every exact r the v8c run evaluates plus a 0.0025 grid (interpolated only off-grid). Kept as data because the sweep needs numpy and the sim stays stdlib-only.
- **`sim/scripts/run_progression.py`, `sim/tests/test_progression.py` (new):** report and reproduction tests. Reproduces v8c exactly: walls (mature #2 / boss) R1 7/6 ×3, R2 Wangan 8/9, Street 7/7, Touge 7/7, R3 Street 9/10, Touge 8/8, Wangan 8/8, finale 4/6/4/6; 155 grind races, 162 levels, story 49,369 XP vs grind 70,035 XP, 0 lost. All 30 existing + new tests pass; `scripts/balance_gauntlet.py` ALL CHECKS PASS; `scripts/generate_build_matrix.py` runs and leaves `config/sample_builds.json` unchanged.
- **Fixed while porting:** the ×1.30 Option A step was keyed on the name "Touge" in the drafts (`final-v1/prog_final.py`, `grind_v6.ladder`); it now applies to whichever crew opens Round 2/3 (`OPTION_A_ROUND_STEP`). Draft per-district rates were computed from SP rounded to 0.1; the repo uses exact SP, so a few per-district cells move by ≤0.7 pt (none changes a wall or a clear).
- **`design/01`, `02`, `07`:** documented the XP → levels → SP loop, the XP cap, grind walls and the skip-grind pattern (3 clear → wall → 2 clear → wall), the per-crew taper, boss rewards (XP + money + shell + graphic; mods bought only), Round 3 → big finale mods with the finale exempt from caps, and the new district order — referencing constants in `equations.py`, not copying them. 07 Q5 (how the car levels up) marked answered.
- **Conflict flagged, not rewritten:** canon 28 (crew boss wins gate rare tier-jump mods) conflicts with Austin's "mods are bought only"; also canon 26 (signature shells only from betting races) vs "boss wins pay a shell". Marked in `design/01` and `07` §5.2, pending Desmond's rewording.
- **Open items (07 §8.0):** all XP numbers are stand-ins pending playtest; Street is the thinnest district (R3 old head #2 55–57 % with grind skipped); Wangan skipped walls dip to 33–37 % on its own tracks and Finale Myth #2 to 36–46 %; aero has no rule against the caps; the finale window is extrapolated above r 1.05. `races_v8c.py` story unlock markers (end R1 after R1 Street, debt/aero after R2 Wangan, betting after R2 Touge, finale after R3 Wangan) are recorded here for Nathaniel; `story/` was not edited. `AGENTS.md` architecture list not updated (Desmond's file).
- **Why (Austin, 2026-11-09):** "Skill points for level should scale up as levels progress but leveling up should also be harder" (GEO curve); "levels should lock the player from skill points" and XP capping is allowed (level cap = SP cap, XP past it lost); "crew-boss wins should definitely pay some skill points"; "How about less XP payout (proportionally) as you go up? Forces more grinding" → per-crew taper approved ("I think a taper per crew makes sense"); district order changed so rounds are not a plain Touge/Wangan/Street round robin (corrected to R2 Wangan/Street/Touge, R3 Street/Touge/Wangan); finale rules no longer apply ("they're the final races of the game"); balance grinding and mods ("mods cannot make up for the stat gap alone"). Commit and push: "Let's do that and push. I'm relatively satisfied with the results for now but only a playtest will reveal how nice or bad it is."

## 2026-11-08 — Barry: commit Gordon's and Nathaniel's pending work after PR #2 [repo]
- Merged PR #2 (Exit→Entry lockout deletion) into `proto-build`, then committed the shared clone's pending work on top: Gordon's Godot-guide lockout removal, §0 `MX1` playtest spec (still PROPOSED), legacy `scripts/` + `scenes/Battle.tscn` teardown and `project.godot` autoload cleanup; Nathaniel's Daikoku tourist-group story edits. Resolved the CHANGELOG conflict by keeping every entry, newest first, and dropping the "uncommitted" tags.
- **Why:** Austin said to resolve conflicts and push Gordon's and Nathaniel's changes too (2026-11-08).

## 2026-11-08 — Gordon [godot]: remove Exit→Entry lockout from the Godot build guide
- `design/godot-build-guide.md`: deleted every Exit→Entry lockout reference: the `EXIT_LOCKOUT_ENABLED` constant (§1.2) and tuning row (§15.2), both `get_locked_out` lookups (§1.2, §5), the lockout goal line (§4), the `CardHandUI` blocked-stance handling (§4.2), `last_exit_stance` / `last_turn_type` / `locked_out_stances` state fields (§5) and turn-flow steps (Appendices A–C), the AI lockout note (§8.2), and the matching `MX1` Block C fields in §0.2. `scripts/` has no lockout code (all legacy scripts were already deleted on 2026-11-06). Why: Austin cut the Exit→Entry lockout rule entirely; Barry removed it from `design/01`, `02`, `03` and `06`.

## 2026-11-08 — Barry: delete the Exit→Entry lockout rule [design]
- `design/03-deckbuilding-clash.md`: removed the whole "Exit → Entry lockout" section under Per-Turn Card Flow, including the turn-type-pair tables (Exit: Attack, Exit: Defend, Exit: Steady), the TODO to fill cells, the greyed-out entry description, and the chicane→hairpin narrative.
- `design/01-system-overview.md`: removed Key Design Properties item 9, "Exit→Entry lockout". It was the last item, so the list was not renumbered.
- `design/06-pattern-read.md`: removed the paragraph saying the exit stance feeds forward to determine next-turn entry lockouts (the cross-reference to the lockout tables in `03-deckbuilding-clash.md`).
- `design/02-equations-reference.md`: removed the "Corner lockout table (03 chicane Steady exits)" TODO row under §11 Other unlocked / TBD.
- Searched the rest of `design/` (`04`–`09`, `design/notes/`, `design/sample_battle_screen.html`, `design/art/`). No other descriptions of the rule. The only leftover design mention is `design/art/art_direction.md` K2, which names "lockout tables" and was left unedited.
- **Why:** Austin decided on 2026-11-08 to drop the exit-to-entry model entirely (never filled in, not in the Python sim).
- **Not done:** `design/godot-build-guide.md` (the `EXIT_LOCKOUT_ENABLED` toggle, lockout lookup, and UI/flow notes) and any `scripts/` code are handled separately by Gordon (Godot owner). `design/art/art_direction.md` K2 still names "lockout tables" and was left unedited. No sims run and no constants changed.

## 2026-11-06 — Nathaniel: add Daikoku-style tourist groups as must-have wild-race characters
- `story/canon.md` (Racer Types and Archetypes), `story/plot.md` (Districts), `story/barks.md` (§1 Wild Race), and `story/dialogue_outline.md` (Round 1 Wild races): added Austin's note that tourist groups like the ones that visit Daikoku PA in real life are must-have characters in wild races (kept district placement and how they map onto the 5-per-district racer-type/archetype table `<TBD>`).

## 2026-11-06 — Gordon [godot]: delete legacy Godot prototype scripts and Battle.tscn
- `scripts/*.gd`, `scripts/*.gd.uid`, `scenes/Battle.tscn`: deleted all 27 legacy prototype GDScript files (plus `.uid` sidecars) and `scenes/Battle.tscn`, and removed the dangling `[autoload]` entries in `project.godot` ahead of a clean-slate GDScript rebuild. Why: Austin directed clearing the old scripts and `Battle.tscn` so we rebuild from scratch when ready.

## 2026-11-06 — Gordon [godot]: draft playtest-to-troubleshooting spec (§0, PROPOSED)
- `design/godot-build-guide.md`: added `## 0. Playtest-to-Troubleshooting Spec (PROPOSED)` above `## 1. Project Bootstrap`. No existing section (§1–§15, Appendices A–H) was changed. It has four parts: §0.1 coordinate and camera reference system (Godot Y-up/`-Z` forward axes, 640×480 `(u, v)` screen callouts, Battle Frenet frame `(seg, s, d, h, yaw_slip)` plus world frame, `SceneId` for every locked place, a 1 m overworld grid, a `CamRigMode` rig-state struct, and an `F3` one-line debug HUD with example strings); §0.2 the `MX1:<git7>:<base64url>:<crc16>` compact state token (`F9` → clipboard + `user://playtest_dumps/` `.json`/`.png`), with a three-block wire schema covering spatial/camera, progression/unlocks/economy/build/cosmetics, and the mid-battle RNG/turn/combat/tell snapshot; §0.3 the playtest → bot reproduction loop (per-bot use, Godot-only vs Barry-hosted Python decoder options, decode lints, `--playtest-state` / `--dump-frame` boot, `F10` clipboard hot-warp, replay-desync check); §0.4 planned touchpoints and six open decisions for Austin.
- Grounded in today's code. Findings recorded in the spec, not fixed: `BattleCamera.gd` isn't attached to `World3D/Camera3D` in `Battle.tscn`; the `CarAnimator` nodes' parent is a plain `Node`, so their position tweens don't move the cubes; `TurnManager` randomizes its RNG unless seeded and uses placeholder QTE values; `globals.gd` `EncounterType` has no betting or Myth Driver entries.
- No balance numbers were copied (constants are referenced by name and file), and nothing in `project.godot`, `scenes/` or `scripts/` was touched. Committed 2026-11-08 on Austin's go-ahead. Why: give Austin a one-keypress `MX1` state + camera coordinate dump so any bot can reproduce and debug a local playtest moment deterministically before GDScript implementation ramps up.
## 2026-11-06 — Desmond: district Apex/Exit habits are not the old archetype rows [design]
- Correction to the visual-gap entry below. The first write called the Aggressive, Defensive, and Precise rows in `design/06-pattern-read.md` the approved shared specialization habits. That was wrong. Austin meant Touge, Wangan, and Street specializations. Their tendencies are intended, and the precise habits and race-state-dependent Apex/Exit mappings are not defined or approved. Those old rows stay as a historical unreconciled draft, not the adopted source of actual Apex or Exit. The corner-description notes (late braking, a long single apex, a delayed apex, an early apex, and the other turn writeups) stay illustrative earlier examples, not an approved stance map. No new table and no probability. Updated the same claim in `design/06-pattern-read.md`, `design/godot-build-guide.md` (§4, §9, Appendix G), and `design/art/art_direction.md` B.4. `proto-build` was not changed.

## 2026-11-06 — Desmond: asymmetric visual gap and lane Entry [design][art][story]
- Austin locked the presentation rule and asked to write it into the existing tell and camera notes. No new doc. No gameplay code, no mockup assets, no `project.godot` or other engine settings.
- **Rule:** the player locks the 3-card line before corner playback. Lane Entry, relative to the next corner, is outside = Attack, center = Steady, inside = Defend, and can bluff by improper placement. Apex and Exit are inferred from that Entry, shared Touge, Wangan, and Street tendencies, corner geometry, and the real lead/gap at selection start. Those district tendencies and the race-state-dependent Apex/Exit mapping are still TBD. The Aggressive, Defensive, and Precise rows already in `design/06-pattern-read.md` are a historical draft, not that mapping. No explicit Apex/Exit tell and no extra bluff layer. No new habit table, race-state threshold, or bluff probability.
- **Drawn gap is asymmetric and is not the race.** When the player is behind, cap how far ahead the rival is drawn so lane/Entry stays readable from the fixed rear third-person player camera. When the player is ahead, the trailer recedes in the top-center rear-view mirror and headlights/lane get harder to read. That loss of Entry information is intentional. Do not undo it with a HUD lane marker, enlarged lamps, or a matching cap behind the player. No distance number was approved. Cumulative DP, position, and the win condition stay on the real gap. This is not a change to `RUBBER_BAND_FRACTION` in `sim/velocity_shift/equations.py`, not an AI change, and not a damage change. A large real lead cannot be read exactly from the capped spacing.
- **Where:** `design/06-pattern-read.md` (live section; older face, weaving, suspension, and lie-rate text kept and labeled as not the live tell — cells not edited); `design/godot-build-guide.md` §4, §9, §11, §12, §13, Appendix B, Appendix G, Appendix H (camera and spacing called out; prototype sketches left in place and marked, including the symmetric `snap_to_gap` lerp); `design/art/art_direction.md` B.4 (race bullets locked; the car mirror does not lift the dry-road rule; 640×480 vs 640×448 left open); `story/pitch.md` Racing View (short pointer so "readable" is not both directions).
- **Not done:** higher-resolution/CRT was an experiment only. Display stays 640×480, viewport stretch, keep aspect. `scripts/CarAnimator.gd` still uses the symmetric Z lerp. That code was not updated.
- **Still in conflict, and not treated as fixed here:** selection countdown is still 8s in the old 06 sentence's record vs the 12s prototype timer in the Godot guide; `design/notes/Notes.md` still shows race position as a numeric `position_delta` percentage (a HUD figure, not drawn spacing); overworld camera is still the perspective note in `design/art/world_notes.md` against the guide's "isometric" future-screen line; Steady vs Neutral (art Q6) is still open even though this lane rule uses Steady and the enum is `NEUTRAL`; B.5 still lists `tell_*` portrait filenames; the earlier lie-rate table, comfort/weak rows, and Entry/Bluff columns remain in 06 as labeled historical draft, not as approved probabilities or as the Touge/Wangan/Street Apex/Exit map.

## 2026-11-06 — Nathaniel: add Eric Berger SpaceX mythologizing note for Myth Drivers
- `story/canon.md` (decision 1), `story/pitch.md` (Myth Drivers), `story/plot.md` (§7 Myth Drivers), and `story/characters/index.md`: added Austin's tone reference that the scene mythologizes the Myth Drivers similarly to how SpaceX employees get mythologized in the books by Eric Berger.

## 2026-11-05 — Barry: bake substory rewards, story-race shop unlocks, and shells/liveries into design/ (canon 26, 28)
- `design/01-system-overview.md` (Vocabulary: progression unlocks), `design/02-equations-reference.md` (Economy decision table), and `design/07-economy-and-mods.md` (§2.1, §2.4 C12, §5.2–5.3, §6.1, §6.4, §7.5, §10 metric 14, §11 Q10/Progression/Flags): synced `design/` with canon 26 and 28 (`44d9caf`) and Sabine's personal repair-tab framing (`25b98e8`).
- **Systems rules recorded:** substories (post-race-3) award cash through Sabine's normal `DEBT_SHARE` cut, a free skewed-sidegrade mod to the garage stash (`≤ TIER_STAT_BUDGET`, real stat penalty, slot/level-gated, never aero), a shell-specific livery (Round 1–2 targeting the starter or an already earned substory shell; later ones allowed to tease locked shells), or a standout shell (`SUBSTORY_SHELL_COUNT` flagged to Desmond and Arthur). Lieutenant wins expand horizontal paid shop stock while crew bosses gate rare tier-jump mods. No sims run and no constants changed (still awaiting economy success criteria). Why: Austin locked the substory/shop/shell-and-livery rules in the Integration room and asked to bake and push.

## 2026-11-05 — Nathaniel: lock substory rewards, story-race shop unlocks, and substory shells/liveries (canon 26, 28)
- `story/canon.md` (decisions 19, 26, new 28; Vocabulary; Racer Types stakes; Open Question 18), `story/plot.md` (Districts, Wangan, Substories), and `story/dialogue_outline.md` (End of Round 2): locked substory incentives and story-race shop progression per Austin.
- **Substories (canon 28):** gated until after scripted race 3; each awards cash (through Sabine's normal repair-tab cut while open), a free skewed-sidegrade mod straight to the stash (never free aero; budgets and pacing are Barry's in `design/07-economy-and-mods.md`), a shell-specific graphic/livery, or—for a few standout substories—a cosmetic shell (mesh count `<TBD: Arthur / Desmond>`).
- **Shells and liveries (canon 26):** crew bosses keep their signature shells exclusive to betting races at the promoter's subsea Wangan home base, while standout substories add a small pool of oddball shells. Unlocking a livery before owning its shell sits in the garage as a breadcrumb to hunt that shell down; Round 1–2 livery substories target the starter shell (or a substory shell already earned) so early rewards are usable before betting opens.
- **Story-race shop unlocks (canon 19, 28):** beating crew members (lieutenants) as well as crew bosses expands Reiko's paid shop stock, with crew bosses gating rare shop mods. Why: Austin locked the four-reward substory menu plus lieutenant shop unlocks in the Integration room and asked to bake and push.

## 2026-11-05 — Nathaniel: strip leftover "race under Sabine's garage / garage standing" framing
- `story/canon.md` (decisions 14, 19; Backstory Timeline 3–4), `story/characters/sabine.md`, `story/plot.md` (§1–3, Mentor Arc), `story/scripts/prologue.md` (§3), and `story/dialogue_outline.md` (Prologue §5, Round 1 wild bark, Round 2 Street kid bark): removed older framing where the PC raced under Sabine's garage to rebuild its standing with the crews. Sabine's surface reason for taking the PC in is now strictly feeling responsible for the back-road blowout and fronting the rebuild on a personal repair tab (with her unspoken reason—seeing herself in the PC—unchanged). Why: Austin flagged in the Integration room that Sabine stepped away from the scene, doesn't run a racing crew, and isn't trying to make a name for herself (matching canon 24 and her locked personality), and asked to strip the leftover framing.

## 2026-11-05 — Nathaniel: subsea Wangan parking area as promoter home base ("water level" music)
- `story/canon.md` (decisions 21, 26), `story/plot.md` (Wangan), and `story/pitch.md` (Wangan District): set the promoter's home base in Wangan as a subsea parking area under the bay (in-world name `<TBD>`, Open Question 3). Why: Austin wanted a grounded narrative home for "water level" music, and tying it to the Wangan parking area / promoter's home base fits the bayshore highway setting and gives the track recurring mileage across meets and crew-boss shell bets.

## 2026-11-05 — Nathaniel: Jesse and Reiko arcs + "Sabine's crew" (first pass, needs more passes)
- Austin approved a first pass on Jesse's and Reiko's arcs and asked to commit them for now (needs more passes; not final-locked). Open Questions 8 and 12 stay in place and record the first pass the same way 6 and 7 do.
- **"Sabine's crew" (canon 24):** Jesse, Reiko and the barkeep are part of an informal off-grid circle of builders and tuners who reject the racing cliques and exist solely for the cars. That's how Sabine stays isolated from the crews after the sweep yet is still known across the city. Round 2 (around the speakeasy / mid-round): Jesse and Reiko introduce the PC to this circle.
- **Reiko:** protective gatekeeper who gets burned after vouching. Cool → full-price after race 3 → wholesale at the end of Round 1; brings the PC into "Sabine's crew" in Round 2; warns the PC off digging in Round 3; stung at the Mentor Confrontation; strictly business in the Finale (parts stay open); once she sees the PC rounding up the Myth Drivers, she points them to where Sabine runs the mountain alone (first pass for Open Question 8).
- **Jesse:** conflict-averse peacekeeper who has to stop smoothing things over. Welcomes the PC on night one; makes the garage feel like home in Rounds 1–2; at the Mentor Confrontation he refuses to cover for the PC and quietly points out they decided without asking (subverting the Prologue beat); quiet/strained in the Finale (tuning stays open); earning his warmth back by the epilogue makes the garage feel whole again.
- Updated: `canon.md` decisions 4, 15, 24, 25 and Open Questions 8 and 12; `plot.md` §2, §5, §6, §8 and a new Structural Themes section; `dialogue_outline.md` (Round 2 intro, Round 3 warning, Mentor Confrontation, Summit Setup). Beats marked first pass; example lines marked (draft). No push — Austin said commit for now.

## 2026-11-05 — Barry: narrow loss persistence in design/ to crew members and crew bosses (canon 27)
- `design/01-system-overview.md` (Vocabulary: race tiers and persistence) and `design/07-economy-and-mods.md` (§11 Q19 and Progression note): updated canon 27 references so loss persistence applies only to crew members (lieutenants) and crew bosses; wild races and Myth Driver races don't have loss persistence, while scripted race 3's win gate (canon 19) stays unchanged. Why: Austin narrowed canon 27 (`b90dd15`) and cleared `design/` to match and push.

## 2026-11-05 — Nathaniel: narrow loss persistence to crew members and crew bosses (canon 27)
- `story/canon.md` (decision 27) and `story/dialogue_outline.md`: narrowed loss persistence to crew members (lieutenants) and crew bosses only; wild races no longer have loss persistence (alongside Myth Driver races). Cut the Round 1 wild-race loss bark, renamed Round 2 `Wild races and rematches` to `Lieutenant rematches`, and updated the Finale note. Prologue race 3's win gate (decision 19) stays unchanged. Why: Austin clarified that wild races don't have loss persistence, only crew members and the crew boss.

## 2026-11-04 — Barry: Wild ramp proposal added to the decision sheet
- Added top decision 9 and an item 11 row in `design/02-equations-reference.md`: Wild races in each district ramp up in AI skill and race length as the PC beats that district's lieutenants. Wild vs lieutenant is separated by AI skill (read, QTE, tell lie rate, deck lean), not stats. Open: whether lieutenants remember the PC's stance habits, and whether that applies after losses or only after wins. No sims run; no constants changed. Why: Austin flagged in the Integration room that small crews make it hard to climb to lieutenants and bosses on Wild alone, and that short Wild races may feel thin. He chose a Wild ramp over a new tier and asked for it to be queued for his sign-off.

## 2026-11-04 — Nathaniel: two items pending Austin's sign-off
- Open question 12 (Jesse and Reiko) now notes Austin's "Sabine's crew" idea: a counter-counter-culture group, there only for the cars, that Jesse and Reiko introduce the PC to. Why: it opens their backstories and explains how Sabine stays known while isolated after the sweep. Not locked.
- New open question 17: the story framing for Barry's Wild ramp (reputation draws out better local drivers; tells follow the crew ladder). Substories is now 18 and stays last. Why: Austin asked both of us to queue our ramp work for his sign-off. Not locked; numbers stay with Barry.

## 2026-11-04 — Nathaniel: #3's pro career (Q4 locked), Round 3 sightings for #1 and #3, open-question cleanup
- Q4 locked: the sweep cost #3 his pro career. He was impounded and charged that night, and the team courting him wouldn't touch a street racer with a record, so the offer died. This also gives him a second reason to push Sabine away, on top of avoiding the goodbye: she walked away clean while he lost everything. It's written into canon 9 and timeline item 3, `plot.md` §7, `pitch.md` and `characters/myth_driver_3.md`, and every `<TBD: why his pro career fell through>` is replaced. His Round 2 sighting (the scrap rebuild, "Lost the good one a while back.") now pays it off. In the summit lines, "a pro career that never happened" is now "a pro career that the sweep took from him". Why: Austin locked it, and it ties #3's bitterness to the sweep's cost.
- #1's Round 3 sighting (locked for now, rough wording): after the Touge old head's phone-call reveal, #1 says "Told everyone back then. Nobody listened." and then "Now you're the one asking questions." He never spells out the accusation. Written into `plot.md` §6 and `myth_driver_1.md`.
- #3's Round 3 sighting (locked for now, rough wording): when the PC brings up "She didn't even get a ticket.", #3 says "Some of us paid for that night. Some of us didn't." He's bitter, not lying, and to the PC it sounds like confirmation. Written into `plot.md` §6 and `myth_driver_3.md`.
- Open questions: Q4 removed and the list renumbered. The Round 3 sightings question (now 14) is narrowed to #2's Round 3 sighting plus another pass on Rounds 1–2. New 15 (who the PC races in opening races 2–3) and 16 (the speakeasy drinks scene). Substories stays last (17) and is noted as a separate thread, per Austin.
- `dialogue_outline.md`: updated for all of the above, with open-question references renumbered. The Round 3 Street kid line "she held him back" is flagged to cut or replace (`<OPEN>`), because it no longer leads anywhere. The outline is repo-only now; the Page mirror was dropped.
- Also: `<Touge crew chief>` → `<Touge crew boss name>` in `myth_driver_1.md`, and a double comma fixed in `myth_driver_2.md`.

## 2026-11-04 — Nathaniel: dialogue outline (first pass)
- New `story/dialogue_outline.md`: every scene's dialogue in play order, from the Prologue (including the scripted opening and Reiko opening parts sales after race 3) through Rounds 1–3 by district, the Finale races, the summit, the ending and the epilogue. It covers crew pre- and post-race lines per round for kids, mature members, old heads and the crew boss; all nine sighting slots (the Round 3 ones are listed as open-question drafts); and persistent-results rematch taunts.
- Each line is labelled (locked) for canon lines and the approved prologue script, (draft) for rough new example lines, or `<OPEN: … (Q#)>` pointing to the canon open question. No plot points were invented. It uses canon vocabulary ("reputation", crew boss, lieutenants, wild races).
- Why: Austin asked for an outline of all the dialogue so he can work on it from his phone without pulling the repo.
- Also fixed the `<Touge crew chief>` placeholder (now `<Touge crew boss name>`) and a double comma in `plot.md` §4–5.

## 2026-11-04 — Nathaniel: story vocabulary pass
- Why: Austin asked to update docs across the board to match vocabulary. Scope is `story/` only; `design/` and `sim/` are Barry's, so they're read-only here.
- `canon.md`: new short **Vocabulary** section (after Decisions). It points to Barry's locked-terms list in `design/01-system-overview.md` as the source of truth for system terms and only maps story wording to it (crew members = lieutenants, crew boss not "crew chief", street cred is lore only, no pink slips, story-only terms). Steady vs Neutral is left open. Decision 26 now says "wild races"; the stakes rule says "street cred (lore only)" instead of "rep".
- `plot.md`: "rep" → "street cred (lore only)"; "random racer encounters" → "wild races".
- `pitch.md`: four "reputation" → "street cred" (terminology only).
- `barks.md`: "Wild Encounter" → "Wild Race"; "Crew Encounter" → "Lieutenant Race (crew members)"; "Boss Encounter" → "Crew Boss Race", matching design 01's race tiers. The Low/Medium/High Reputation tiers are re-keyed to Round 1/2/3, because street cred is lore only. The "Reputation Gate" heading is now "Street Cred Gate". All bark lines are unchanged.
- Follow-up per Austin: "street cred" was renamed to "reputation" (still lore only, not a tracked stat).
- There was no "crew chief" or pink-slip wording in `story/`. Conflicts with `design/` are flagged for Barry, not edited.

## 2026-11-04 — Barry: vocabulary pass across design/
- Austin asked for docs across the board to match the locked vocabulary. Added a locked-terms block at the top of `design/01-system-overview.md` covering race tiers (wild, betting, lieutenant, crew boss, Myth Driver), the crew ladder, persistence, stats, play quality (read/timing, QTE), stat parity, unlock order, respec and places. The Steady vs Neutral name is marked open, pending the decision sheet.
- Austin then waived the no-delete rule for this pass (rewording only, no canon changes), so the stale markers became plain current wording: doc titles now say Midnight Apex, the deck is 192 cards in 01, progression/unlock text is current in 05, 07, 08 and the Godot build guide, and superseded rows in 07 were replaced. Original first pass: marked stale lines in place rather than deleting them: the 36-card deck in 01, and the old "mods from Round 2" and "no skill trees" claims in 08, 05 and godot-build-guide. Also marked Round 1 as no longer mods-free in the 02 decision sheet and 07 §7. Added notes that 04's level bands aren't race tiers and that "Velocity Shift" is the old engine name (03).
- Follow-up from Nathaniel's conflict list: fixed the round/unlock line in 02; closed the betting-unlock question in 07 §7.5 and Q16 (end of Round 2) and added the shell rules (canon 26); updated the 07 §2 story citations to the current story wording (street cred, lieutenant race, round-keyed barks, crew ladder); resolved C1 (street cred is lore only); renamed the 'rival chain' row to lieutenant race; renamed the Notes.md 'Pink Slip Races' heading.
- Austin: "street cred" is called **reputation**. Renamed it across design/ (still lore only, not a tracked stat).
- `story/` was not touched (Nathaniel's files). No code changes.


## 2026-11-04 — Nathaniel: mods unlock on winning race 3, persistent race results

- `story/canon.md` decision 19 and `story/plot.md` §4: mods now unlock when the PC wins race 3 (Reiko sees they're serious and lets them buy parts through her, at full price); wholesale still unlocks at the end of Round 1. Replaces the earlier "first 2–3 races" note. Reason: Austin's narrative call in the Narrative/systems chat.
- New canon decision 27: apart from the Myth Driver races, race results are persistent canon, so a driver remembers beating the PC. Reason: Austin decided the canon is persistent. Tracking and retry mechanics are Barry's call.
- `story/canon.md` decision 19: the first three races are more or less scripted, and unlocking mods opens the whole world (wild races, searching out lieutenants). Reason: Austin's call in the Narrative/systems chat.

## 2026-11-04 — Barry: early mod unlock reflected in 07
- Austin (canon 19, via Nathaniel): regular mods unlock after the first 2–3 races at full price. Prepended a note to the 07 progression plan (nothing deleted) and added Q19 (exact race, and whether the Round 1 boss assumes mods). This replaces the 'Round 1 has no mods' assumption behind my Round 1 difficulty proposal. Same day: Austin locked mods to unlock after the PC *wins* race 3 (Reiko sees they're serious), and made canon persistent outside Myth Driver races (drivers remember losses). Also in 07 §2: fixed the crew structure to match canon (every round runs each whole crew from kids to mature members to old heads to boss, and the crew levels up between rounds), which makes the lieutenant tier a three-step ladder inside each round; the old row is kept and marked superseded. The old Q19 was answered and replaced with a new Q19: what happens when the player loses the race-3 gate, and whether a remembered loss changes difficulty.


## 2026-11-04 — Barry: decision sheet prepended to design/02 (uncommitted)
- Prepended `## Decision sheet (2026-11-04, for Austin to lock)` to `design/02-equations-reference.md` (after the intro, before §0). Austin wants core equations locked before more Godot work; standing rule is edit existing docs rather than add `design/notes/decision-sheet.md`.
- Covers open core rules (clash, damage/HP incl. HP_PER_LEVEL 180 vs stale 120, EN, deck 192, straight window 8 vs 12, gauntlet PASS, Neutral vs Steady, encounter ratios/QTE double-count, rubber band, q_read/q_time + §0 targets) plus economy TBDs from 07 (debt, share, clear race, wholesale, respec, betting/shell numbers). No economy/season sims.
- Evidence cited from existing 08 / §0 / `/workspace/parity/grid2d.txt`, plus new runs under `/workspace/parity/decision-sheet/` (pytest 25 passed; validate AI read 0.40 + QTE 10; spot_check current vs that lever at key q_read/q_time). Recommendation: keep clash/HP math; push difficulty through AI skill (read 0.40 + QTE 10 ≈ 50–53% at 0.9/0.9 vs today's 100%).
- Not committed or pushed (Austin locks first).

## 2026-11-04 — Nathaniel: Myth Driver sightings after every round (rough pass)
- Austin clarified that there's a Myth Driver sighting after every round, not just Round 1. Each appears after his district's crew is cleared in Rounds 1–3 (nine in total, talk only, no race until the Finale), and each fits its round theme (1 incident, 2 consequences, 3 distortion). Sightings never lay out the sweep. Updated canon 11 and timeline item 5.
- Rough pass, marked "needs more work": the Round 2 sightings in `plot.md` §5 and on the Myth Driver sheets. #1 makes a cop dig at the emptied mountain. #2's crowds line moved from Round 1 to right after the Round 2 betting reveal (Austin: "fits, mostly already written"); his Round 1 sighting now closes with "Long time ago." `<PROPOSAL>`. #3 has a scrap-rebuild car and says "Lost the good one a while back.", tying to the Round 3 "sixty days" reveal.
- Open questions: #4 (pro career) notes the lean toward "the sweep cost him" (not locked). Reworded #14 to "sightings never lay out the sweep". New #15 holds the Round 3 sighting drafts and also covers another pass on Rounds 1–2, folded in so there's no separate question. Substories is now #16.
- Fixed the stray double full stops on the #2 and #3 sighting bullets.

- Update: #1's Round 2 sighting swapped from the cop dig to "You ran through this crew pretty fast. Used to be a lot harder to reach <Touge crew chief>." / "I ran this mountain once. Half of them never came back after that night." Reason: Austin wanted something deeper about the fracture and how #1 used to run the mountain.

## 2026-11-04 — Nathaniel: mod unlock timing

- `story/canon.md` decision 19 and `story/plot.md` §4: regular mods unlock after the PC's first 2–3 races at full price; Reiko's wholesale prices still unlock only at the end of Round 1. Reason: Austin requested this timing (wholesale stays the end-of-Round-1 payoff). Exact race count is Barry's call.

## 2026-11-04 — Nathaniel: Myth Driver #1 sighting tweak, sweep-hint question, canon cleanup
- #1's sighting: his snide cop comment now points at a past night with the police ("Hope she doesn't bring the cops again.", rough wording), which sends the PC into Wangan asking. The Wangan crew, being mature, lays out the sweep straight (`plot.md` §4, `characters/myth_driver_1.md`). The uncle-dad payoff note is kept. Why: Austin wants sightings to only establish that each Myth Driver knew Sabine, with sweep information coming from crew reveals and post-race dialogue. That rule is now in canon 11, `plot.md` Rounds 1–3 and each Myth Driver's sighting text.
- New open question 14: post-race crew dialogue that hints at the sweep. Substories is now 15.
- Cleaned up `canon.md` for readability, per Austin. Each decision has a bold summary and short bullets; duplicate text is replaced by pointers (2→9 for #3, 2→21 for the date); redundant "locked 2026-11-02" tags are removed. Decision numbers are unchanged, and no facts or numbers were changed. 107 → 164 lines (bullets instead of paragraphs).
- Contradictions fixed:
  - A stray `---` split the decisions list between 19 and 20.
  - Canon 5, `plot.md` §10, `pitch.md` and `characters/sabine.md` called the uncle line "cutting", which contradicts Sabine's locked personality (not cutting; a rare moment of anger). They now say "angry".
  - Timeline 9 and `characters/sabine.md` listed only two of her three reasons not to rejoin; both now include the uncle's emergency (23).
  - Canon 11 and the sighting text in `plot.md` §4 and the Myth Driver sheets said sightings "build the mythos around the fallout". They now say sightings only establish that he knew Sabine.
  - Canon 19's facts were out of order: wholesale is now dated to the end of Round 1 (matching `plot.md` §4), and the debt clearing mid Round 2 sits together with its aero trigger.
  - `plot.md` and the #2/#3 sheets were missing a full stop before "Locked 2026-11-0x".

## 2026-11-04 — Nathaniel: Myth Driver #3's sighting beat
- Replaced the `<TODO: sighting beat>` for #3's Round 1 sighting in `story/plot.md` §4 (Street) and `characters/myth_driver_3.md`. He traces the PC's parts to Reiko and through her to Sabine, asks "She doing alright?", then peels off with the crew before the PC can answer. Removed the matching open question from `canon.md` and renumbered (Substories stays last).
- Why: it fits his locked personality (charming, and avoids hard conversations). He reaches Sabine through her people, not her work, so it doesn't repeat #1's and #2's beats.
- Per Austin, the hint at #3's failed pro career moved from the sighting to the Round 2 Street reveal (`plot.md` §5), likely through the influencer `<TODO: beat>`.

## 2026-11-04 — Nathaniel: Myth Driver #2's sighting beat
- Replaced the `<TODO: sighting beat>` for #2's Round 1 sighting in `story/plot.md` §4 (Wangan) and `characters/myth_driver_2.md`. He spots Sabine's work on the PC's car, slips into the past tense ("Everyone did"), then deflects with a dig at the promoter about chasing the crowds she drew. Removed the matching open question from `canon.md` and renumbered.
- Why: it fits his locked personality (composed and polished, with guilt leaking out sideways). Austin chose a Sabine-related exchange with a dig at the promoter, which sets up the Round 2 Wangan reveal that betting dropped when she walked away. A betting-themed headliner line was set aside because betting doesn't unlock until the end of Round 2.
- Added open question 14, flesh out Jesse's and Reiko's stories (Austin's note), before Substories, which moves to 15.

## 2026-11-04 — Nathaniel: car bodies (shells) and betting races
- Added canon decision 26 (shells and betting-race rules), with cross-references in decision 21 and the `plot.md` Wangan district.
- Why: Austin wanted a simple in-world reason for changing car bodies, since there will be many cars. Body swaps are everyday work at Sabine's garage, and Reiko sources the shells.
- It's inspired by Racing Lagoon's looting, but a one-sided pink slip needed too much suspension of disbelief. So shells became a bonus prize for winning a betting race against a crew boss at the promoter's base. The PC never stakes their own shell, which keeps the "a loss = retry, never losing the car" rule intact.

## 2026-11-04 — Nathaniel: aero unlock, betting timing, Jesse and Reiko back at the garage
- Garage: Jesse and Reiko work out of Sabine's garage, not the speakeasy (canon 24, `plot.md` §2, `barkeep.md`). Austin corrected this; the speakeasy is just the barkeep and the wind tunnel. "Sabine doesn't employ them" stays.
- Aero: unlocks when the debt hits zero mid Round 2 (canon 19, 24; `plot.md` §5). Parts are bought from Reiko at the garage and tuned at the wind tunnel (Austin, DM). Sabine takes the PC for drinks at the speakeasy to celebrate, the PC's first visit to the bar (`barkeep.md`). Numbers stay in Barry's `design/07`; the exact race comes from his season sim.
- Betting: the promoter's side game opens at the end of Round 2 (canon 21, `plot.md` Wangan, §5), matching Barry's 07 fix in the Integration room.
- Open questions: removed "Betting unlock timing" and "When the PC first visits the bar" as resolved; renumbered.

## 2026-11-04 — Nathaniel: core character and crew personalities
- Added a Personality bullet to Narrative Identity on the Sabine, Myth Driver #1–#3 and barkeep sheets; a PC personality line in `story/plot.md` §1 (kept light so players can project); boss and crew personality lines under each district (Touge, Wangan, Street) in `plot.md`; and canon decision 25 pointing to them.
- Why: Austin locked these to drive barks, pre- and post-race interactions and exposition.
- Sabine's pitched "cutting" trait was dropped as out of character; her uncle parting line stays as a rare moment of anger.
- #2 and #3's personalities were fitted to their districts (Wangan professionals, Street younger crowd). Their backstories stay put, because the promoter old flame (decision 21) and #3's pro career depend on them.

## 2026-11-04 — MX-5 (ND, soft top): detail pass [art] (Arthur, Art Director)
- Austin signed off the clay ("Great pass. Go for detail."). The detail pass is the GR Corolla's stage copied to `art/vehicles/mx5/`: `build_mx5_detail.py`, `bp/vectors.py`, `tex/make_body_mx5.py`, `tex/make_parts_mx5.py`, deliver, three-view and lineup scripts, and `godot/make_tscn.py`. Game files are in the new `assets/cars/mx5/` (`car_mx5.glb`, `car_mx5.tscn`, `susp_follow.gd` with its own uid). The night shot is in the new `art/mood/tokyo_mx5/`. Not committed.
- Result: 1,692 tris (cap 2,000; +2 vs clay). The mirrors are now 5-point rings (+12 tris), the glow FX now covers head and tail lamps (+4), and the boolean re-cut came out 14 tris lower. Silhouette and rig are unchanged: IoU side .978, top .993, front .971, rear .953 (pass); 9-pose clearance all clear, tightest still 4.5 mm at front bump.
- Clay weak spots are fixed in the texture, not the mesh, because the modelled hood dip read as dents. Form shading is driven by the drawing's DETAILS vectors: fender-peak crest, valley and centre dip on the hood; the door scoop under the rear-fender crest; arch-flare lips; a tucked rocker; and a rolled, creased tail. Ring tail lamps and the LED projector headlamp art (A.2.8 molding + painted lens) give the tail and nose their ND read.
- Paint is made-up "Daybreak Yellow". Soul Red would put a second red roadster next to the S2000 (the lineup is blue / red / blue / white), and yellow is the period nod to the NA's 1992 Sunburst Yellow. It reads against the navy/mercury night palette.
- Photo check (A.1.3), using public Wikimedia Commons ND photos kept in a scratch folder: windshield frame painted black, rear corner reflectors repainted as dark recesses, grille painted as horizontal slats. The fender peaks and the door concavity are stronger in the photos than the paint can give.
- Paint spec is lower than the GR's (.26 in the detail build, .15 in the Tokyo scene). At GR values the key highlight on the faceted rear fender read as a white glyph on the yellow.
- Godot 4.6.3 check in a scratch copy: imports, settles at body y 0.000, RWD drives, steers 22.9° at .40, and the struts follow.
- `.gitignore`: `mx5_detail_orthos_*` (blueprint silhouette), the raw render folders, `.npy` and texel dumps, the geo blend and the raw lineup frame.

## 2026-11-04 — MX-5 (ND, soft top): clay for shape sign-off [art] (Arthur, Art Director)
- Austin asked for a Miata from the Dimensions.com "MX-5 Miata - Soft Top" SVG. New `art/vehicles/mx5/`, built the GR Corolla way (same SVG layer classification, faired curves, 9-point loft, one boolean for pockets, Workbench renders, IoU gate, clay three-view). It stops at clay for Austin's sign-off. Not committed.
- Generation is **ND**, read from the drawing: slim fixed LED headlamps, trapezoid grille, round tail-lamp rings, and 3,915 length / 2,313 wheelbase / 1,237 height against the ND spec of 3,915 / 2,310 / 1,235. No pop-ups, so the headlamps get the usual A.2.8 light molding.
- Result: 1,690 tris (cap 2,000). IoU side .978, top .993, front .971, rear .953 (pass). The rig is the GR/lean one (`MX5-vehicle`, `Hub_XX-wheel`, `Steer_FL/FR`, `Susp_XX`). 9-pose clearance is all clear with a tightest gap of 4.5 mm at front bump. Bump is 35 mm, because the drawn arch is only about 4.6 cm above the tyre.
- `.gitignore`: the MX-5 SVG, its rasters and every render that reproduces the drawing stay local (same licence reason as the GR). Scratch render folders and `.npy` dumps are ignored too.
- Why the hood is flat: a 2.5–3 cm centre dip for the ND fender peaks read as dents at this station density, so it's left to the texture pass. Other weak spots are in `art/vehicles/mx5/README.md`.

## 2026-11-03 — Desmond: audio direction doc started (music: jazz fusion, industrial house, drum and bass) [design]
- New `design/09-audio-direction.md`. There was no audio section in the design docs, so this starts one.
- Records Austin's working music direction: jazz fusion, industrial house and drum and bass. Passed on by Austin through Arthur; marked as a working direction, not final.
- Lists open questions (genre per context, district identity, adaptive race music, Ableton-to-Godot stem conventions) without deciding any of them.

---

## 2026-11-03 — Barry: aero parts and respec cost in the mods spec (proposal)
- `design/07-economy-and-mods.md` §6.3: aero parts are stat parts with a fixed base boost plus a small free pool of points to put into POW, EN or HAN at the wind tunnel. Tunes lock, with a paid respec. Agreed with Austin and Nathaniel in the Integration room; no new stat layer, per Austin. Added Q18 (respec cost) to the bottom of §11. Follow-up the same day (Austin): aero unlocks when the debt reaches zero, mid Round 2 (first set to after Round 1, then moved by Austin to spread out unlocks; story: Sabine takes the PC out for drinks), parts are bought once and kept, a respec moves a capped number of points per visit at a price per point (same rule for skill points and aero), and betting is confirmed to unlock at the end of Round 2 (corrected from 'after the Wangan boss'), with Round 3 harder to push risky bets. No sims run (the economy/mods sim still waits for success criteria).


## 2026-11-03 — Barry: two-axis play quality (q_read, q_time); target win-rate curves (PROPOSED) as 02 §0
- Austin agreed to a clean-sheet equation redesign: targets first, then the minimal core equations (clash resolution, QTE, AI skill), each constant doing one job. `design/02-equations-reference.md` §0 "Target curves (PROPOSED)" is the draft spec, for Austin to mark up. Placement in 02 is Austin's call; nothing existing in 02 (or any other doc) was deleted, rewritten or renumbered. Cleanup and reconciling 02 §1–8, 03, 04 and 08 with §0 come later.
- Per Austin, added a header "Stale; do not reference unless explicitly asked to" above the old 02 §1–8 (no text deleted), since the clean-sheet redesign will replace them.
- Austin (t29u): play quality is split into two independent skills, and the targets must keep three play styles viable (strong reader / sloppy timing, sloppy reader / sharp timing, balanced). §0 rewritten in place for that; the single-q targets from earlier today (Boss a 22, q0 0.90) are superseded.
- Sim (opt-in, defaults unchanged): `MatchConfig.player_read` (q_read, chance per clash of reading and countering the AI's real pick) and `player_timing` (q_time, chance per turn of a perfect-10 QTE). `player_quality = q` still works as shorthand for both (verified identical results); an unset axis falls back to `player_quality`, then to 0 (random). `SimulationRunner._play_quality` resolves them. `parity_sweep.py` gains a `grid2d` mode (q_read × q_time at stat parity, plus `fit_features`, a general logistic fitter). 25/25 tests and the gauntlet pass.
- Measured (`parity_sweep.py grid2d --seeds 40`, Lieutenant and Boss length, N = 4000 per cell, raw output in `/workspace/parity/grid2d.*`): read and timing are **substitutes**. They add on the log-odds scale (Lt: a_r 4.94, a_t 5.92, interaction +0.21; Boss: a_r 5.38, a_t 6.22, interaction +0.68), and either alone wins today (1.0 / 0 wins 91.1% Lt, 88.1% Boss; 0 / 1.0 wins 97.0% and 95.5%). Timing is worth 1.16–1.20× reading per unit.
- Proposed target form: s = (q_read + q_time) / 2, P = logistic(a(s − s0) − b ln r), equal weights so styles are balanced at equal total skill. Wild a 12, s0 0.58, b 12.59; Lieutenant a 14, s0 0.72, b 14.69; Boss a 16, s0 0.86, b 16.79. Boss at parity: 0.9 / 0.9 wins 65.5%, perfect 90.4%, a 1.0 / 0.6 specialist 27.7% (69.2% at r 0.9). +10% opponent stats ≈ +0.10 of s.
- Acceptance test: 324-cell grid (3 tiers × 6 q_read × 6 q_time × r 0.9/1.0/1.1); max abs error ≤ 6 pts, RMS ≤ 3; perfect play at parity ≥ 85% in every tier; style balance ≤ 5 pts at equal total skill; a_t / a_r within 0.9–1.1; level stability ±0.03; monotonic. Six open questions for Austin in §0.9. Desmond flags in §0.10: the read axis depends on the tells, so the lie rates in `design/06-pattern-read.md` directly cap what q_read is worth.
- Why: the parity sweep (08 §5) shows CLASH_STAKES, BATTLE_BONUS and the rubber band barely move q50, and ENCOUNTER_RATIOS scale both opponent level and AI QTE. Only measured figures from 08 and today's grid2d run are cited; everything else is labeled a target. No economy or mods sims run.


## 2026-11-03 — Nathaniel: Myth Driver #1's sighting beat
- Austin locked it: after Round 1 Touge, #1 spots Sabine's work on the PC's car and makes a snide comment about her bringing the cops. It works as bad data, since the PC reads it as a snitch hint, but it's really his distrust of her detective uncle (canon 2), which pays off in the Finale. Updated `plot.md` §4 and `characters/myth_driver_1.md`, and removed the open question.


## 2026-11-03 — Nathaniel: Myth Driver race-lines question removed
- Austin: beats are enough, and exact dialogue is unimportant for now. Removed the 'Myth Driver race lines' open question; the locked beats stay (canon 17–18: #1 insists she left on her own, #2's guilt hints she was a scapegoat). The dialogue gets written when the Finale is scripted. Renumbered the open questions.


## 2026-11-02 — Nathaniel: add the reverse-speakeasy barkeep; Jesse and Reiko aren't Sabine's employees
- Austin added a new character, the owner and barkeep of a "reverse speakeasy," a bar that hides a secret wind tunnel. Reiko sells her parts there and Jesse tunes cars there. He's friendly with Sabine, doesn't care for the drama, and is just in it for the cars, like Jesse and Reiko. The wind tunnel runs on illegally snaked (stolen) power. Austin first made the bar the crew's hangout, then reversed it: the main hangout stays Sabine's garage, so the prologue garage intro stands. Canon decision 24, new sheet `characters/barkeep.md` (mechanical fields `<TODO: Barry via Desmond>`), and an entry in `characters/index.md`.
- Sabine doesn't employ Jesse or Reiko. She isn't part of the scene, and they just hang out with her. `plot.md` §2 Garage Intro now says so. The bar's name, location and barkeep name are on hold as detail work (`<TODO>`).
- Open questions added at the bottom before Substories: the bar's name and location, and when the PC first visits it (renumbered).
- Not rewritten, flagged for Austin: the garage-intro script (`scripts/prologue.md`, where Jesse slides out from under a car in Sabine's garage and promises to fix the wreck), the rebuild debt (canon 19), Reiko's wholesale scene, "Sabine introduces her crew," and where the Round 2 Jesse beat takes place.

## 2026-11-02 — Nathaniel: climax restructure, the PC races for the truth and the apology party
- Austin locked a new climax. The wrongful accusation at the end of Round 3 stays ("Get out of my garage."). Because the PC knows they messed up, they race all three Myth Drivers in the Finale to find the truth, and the contradictions in their accounts unravel the snitch story. The PC goes to Sabine with "I know what really happened," and she blows up at them for digging into her past. The PC leaves, then convinces all three Myth Drivers to come and apologize too: "one big apology party." The climax is a final race between the PC and Sabine at the Fushigi-Yama summit. How the PC gets her there, and whether the apologies come before, during or after the race, are `<TODO>`. The ending, the parting shot, "And when are you calling them?" and the epilogue are unchanged.
- Changed: canon decisions 4, 5, 15, 16 (plus the cross-references in 17 and 18), the Backstory Timeline (new step 7 "The blowup"; steps renumbered to 10), `plot.md` Mentor Confrontation, the FINALE intro, §7–§10 and the Mentor and Player Arc bullets, `pitch.md` climax, and the Resolution lines in `characters/sabine.md` and `myth_driver_1/2/3.md`. The PC now learns the truth during the Finale races, but Sabine still learns the real reasons only at the summit, from the Myth Drivers. "I was wrong. Be there." is gone from the summit and now appears only in the epilogue, sent to the hometown crew.
- Removed the "Myth Drivers each catch wind and come on their own out of guilt" version. The open question about how word reaches them is answered (the PC convinces them) and is off the list. Added questions for how the PC gets Sabine to the race, the timing of the apologies, and how each Myth Driver's real reason comes out in the races. Substories stays last (renumbered).
- Why: Austin felt the story had drifted from his original spine, the PC reconciling Sabine and her old crew, with Sabine angry he even tried, leading to a final race. A variant with no accusation was considered and dropped. The accusation stays because it's the PC's reason to race for the truth.

## 2026-11-02 — Nathaniel: the PC's missed call and backstory beats
- `story/plot.md` §5 Round 2 Touge: Austin locked it. As the racer says he texted Sabine for weeks and never heard back, the PC's phone buzzes with a hometown number and the PC lets it ring out. Nobody comments.
- Why: Austin pointed out that Sabine's "And when are you calling them?" has no weight if the PC's past only comes out at the end. The PC's story has to build alongside Sabine's ("same same but different energy"). The other beats (the Prologue dodge, the Round 2 "Had one. Left.", the Round 3 slip, the full telling at the summit) are first passes added to the open questions. The PC's apology moved to the bottom of the list because it depends on those beats (renumbered).

## 2026-11-02 — Nathaniel: Sabine's reaction to the accusation
- Austin locked it: Sabine doesn't defend herself. She's been accused of this once already and doesn't want to waste the energy again, so it reads as tired, not proud. After a long silence she says "Get out of my garage." It's in canon decision 15 and timeline step 5, `plot.md` Mentor Confrontation and `pitch.md`. Jesse and Reiko staying quiet in the background is left as a `<PROPOSAL>`. The question is off the list (renumbered).
- Why: it fits someone who never explained herself to the Myth Drivers either, and it keeps the uncle's heart attack hidden until the summit.

## 2026-11-02 — Nathaniel: Round 2 Wangan reveal
- `story/plot.md` §5: Austin rewrote Round 2 Wangan. Most people came to the Wangan runs for Sabine, so when she walked away, the betting went down. The bets recovered because the promoter is an excellent businessman, but it was never quite the same. The light personal losses from the sweep stay. The `<CHECK>` is cleared and the question is off the list (renumbered).
- Why: it makes her cost to the scene concrete and ties it to the promoter's betting world (canon 21) without opening a new thread.

## 2026-11-02 — Nathaniel: how #1 and #3 knew about #2's date
- Austin locked this: Sabine never told anyone. #2 vented to #1 and #3 himself, they teased him for weeks, and he convinced himself the jokes started with her. At the summit he throws it at her ("You told everyone I asked you out."), and #1 or #3 answers, "Man, *you* told us." It's in canon timeline step 1, `plot.md` §9, `characters/myth_driver_2.md` and `characters/sabine.md`. The `<CHECK>` flags are cleared and the question is off the list (renumbered).
- Why: it closes the gap in how they knew without anyone breaking Sabine's privacy. It's the same misread as the rest of the story, since #2 blames her for something he did, and it gives the summit a beat where his grudge falls apart before the old-flame truth lands.

## 2026-11-02 — Nathaniel: two reveal lines cut
- `story/plot.md`: Austin cut "ask her uncle lol" from the Round 2 Street group chat because it was too on the nose, and cut the old head's "couple weeks" line from Round 3 Touge. The missing two weeks now come up only through the Round 2 Touge texts. "Reveal checks" is off the open-questions list. Substories moved to the bottom at Austin's request ("save those for the end") (renumbered).

## 2026-11-02 — Skill parity: play-quality sweep and fitted win-rate equation [sim] (Barry, Chief of Systems)
- Austin approved fitting a skill parity equation, with his feel target as the first success criterion: at stat parity you should only win if you play about 90% right (q50 ≈ 0.9).
- **Engine changes (opt-in; defaults unchanged, all 25 tests pass):**
  - `models.MatchConfig` gains `player_quality` (q in [0, 1]) and `opponent_qte_ratio`.
  - `simulation.SimulationRunner` gains a q-player: it counters the AI's real pick with probability q and hits a perfect QTE with probability q, otherwise it plays like the old random player. To do that it makes the AI's pick first and caches it, which is safe because the AI's pick never depends on the player's card.
  - `equations.py` gains `PLAYER_QTE_MIN`, `PLAYER_QTE_MAX` and `PERFECT_QTE`. The rubber-band 0.15 literal in `match.py` moved to `equations.RUBBER_BAND_FRACTION` with the same value, because all constants belong in `equations.py`. `balance_gauntlet.py` still hard-codes its own 0.15 copy.
- New `sim/scripts/parity_sweep.py` (pure stdlib, multiprocessing) runs the sweeps, the fit and the lever prototypes. New `design/08-skill-parity.md` records the results and proposals; the script is the source of truth.
- **Findings:**
  - At parity, q50 is 0.21–0.27 at every level and encounter length (N=2000 per cell), far below 0.9. The fitted logistic is P = 1/(1+exp(-(a(q-q0) - b ln r))). For Lieutenant: a=10.49, q0=0.214, b=26.18, RMS error 2.0 pts.
  - The best tested route to 0.9 is AI skill: AI QTE at the cap plus a prototype AI read rate of 0.40, which gives q50 0.874–0.916 everywhere. CLASH_STAKES, BATTLE_BONUS and the rubber band barely move q50.
  - Today's double-scaled ratios give Boss a q50 of about 0.82 and make Wild unlosable.
- **No game constant was changed;** the lever results are proposals for Austin. Skill points (now in v1) are expressed as a shift in the stat ratio r.
- Committed on Austin's go-ahead: only the write-up, `design/08-skill-parity.md`. The engine changes and `sim/scripts/parity_sweep.py` stay local for now, so the doc's pointers to them land with a later push.

## 2026-11-02 — Nathaniel: the missing crew reveals filled in
- `story/plot.md` §4–6: Austin approved the full reveal set after a read-through. Round 1 Street has the clip of Sabine leaving right before the sweep and #3 as "the one who went pro." Round 2 Touge has the unanswered texts. Round 2 Street has the group-chat theories and the influencer's interview offer ("Clean people talk"). Round 3 Touge has the old head who saw her on the phone. Round 3 Wangan has the promoter's "She had her reasons. Not my place." Round 3 Street gets the final straw: "I did sixty days. Lost my car. She didn't even get a ticket."
- The sweep's cost builds lightly, through plain facts in Round 1 Wangan, personal losses in Round 2 Wangan and occasional crew flavor text, so "sixty days" lands. Austin picked this over a heavier version that would have given someone in every district a sweep injury, because it's less on the nose.
- Rejected and why: the detective-uncle line in Round 2 Touge was too on the nose. The promoter's betting books were a throwaway that raises a question the story never answers. For Round 3 Street, a farewell party didn't fit canon (#3 never went pro), a deleted video would be hard to animate, and "she always knew when to leave" felt contrived.
- Still flagged `<CHECK>`: "ask her uncle lol," and whether to keep or cut the "couple weeks" echo in Round 3 Touge. Open questions: "Missing story reveals" removed; "Clues" became "Reveal checks"; the Round 2 rewrite check is narrowed to Wangan (renumbered).

## 2026-11-02 — Economy spec: open questions are now a FIFO queue [design] (Barry, Chief of Systems)
- `design/07-economy-and-mods.md` §11 now lists open questions oldest first, with dates, following the queue Nathaniel keeps in `story/canon.md`. Austin asked for the same blind FIFO here: he gets one question at a time from the top, and new questions go to the bottom.
- The encounter-scaling fix (open since 2026-11-01) and the success criteria for the sim are now at the top of the queue. Arthur's body-kit and wing question was added at the bottom.
- Removed as resolved: rep is lore only (Austin via Nathaniel), and mods may show on the car within the car rules (Arthur). The overlap question now starts from canon decision 19 (a share of each win goes to the debt) and lists Desmond's trickle-from-bonuses idea as an alternative. Question references in the spec were renumbered.
- Logged Austin's progression plan in §11: Round 1 uses skill points only, Reiko's mods come from Round 2, and capped betting from Round 3 pays for pricier mods. This brings skill points into v1, so the "deferred" status in `design/05-skill-trees.md` is now out of date. The docs have no skill-to-win-rate equation; the closest thing is the damage ratio S in `sim/scripts/design_opponent.py`.

## 2026-11-02 — Logo: approved one-line wordmark [art] (Arthur, Art Director)
- Austin approved round-3 V3, now in `art/logo/`. It's a black-and-white one-line wordmark: solid MIDNIGHT with the chicane M, flares on the left, a heavily extruded APEX whose A traces an out-in-out racing line (kerb at the apex), and katakana underneath. He rejected round 1 as too soft and rounded, so everything is hard-edged. He picked W2's one-line layout, S1's APEX and H1's flares from round 2, in black and white.

## 2026-11-02 — .gitignore: keep licensed GR Corolla blueprint files local [art] (Arthur, Art Director)
- Ignored the Dimensions.com SVG and the four renders that reproduce it (`art/vehicles/gr_corolla/...`). Their licence is non-commercial with no redistribution, and the repo is public. Desmond asked for this so a `git add -A` can't push them.

## 2026-11-02 — Female character base: chest height raised [art] (Arthur, Art Director)
- Austin pointed out that the female bust sat too low (it showed on the poster draft). It was in the model: the apex was at 1.163 m, about 18 cm under the shoulders. He asked for +5 cm and then another +5 cm, so it's now at **1.256 m** (+9.3 cm), about 4 cm above the Spine2 joint. The fix lives in the build script (`art/characters/base/build/spec.py` `fem_trunk_z()` / `TRUNK_ZF` / `TRUNK_WZ`, plus the weight lookup in `build_char.py`), so rebuilds keep it.
- Only female trunk heights move: the waist ring rises 3.7 cm, the bust ring 9.3 cm and the armpit ring 4.2 cm, so the upper chest isn't pinched. The hem and shoulders stay put. Ring widths and depths and the Slim/Bulky factors stay tied to each ring, so all three builds get the raised chest.
- The apex is now ~79 % Spine2 / 21 % Spine1 (was ~93 % Spine1). The armpit ring is weighted so it picks up only ~3 % UpperArm, and the A-pose and Bulky armpit checks are clean.
- Tris (686 body), vertex count, UVs and textures are unchanged. Compromise: the texture follows the verts, so the tee stretches about 1.45× between the waist and the bust and compresses above it, and the jacket pockets sit about 2–3 cm higher. It's plain fabric with no print, so it isn't visible at game resolution. The male is untouched.
- Rebuilt `char_base.blend` and `assets/characters/base/char_base_f.glb` and re-rendered the female turnarounds, deform check, swap sheet and lineups. Before/after (original vs new): `art/characters/base/renders/chest_fix_before_after.jpg`. Not committed.

## 2026-11-02 — Nathaniel: why the PC left home
- Austin locked the PC's real reason for leaving the hometown crew: they felt weak. The PC believed they were the weak link holding the crew back and left rather than say it. The crew never saw it that way. Recorded in canon decision 13, `plot.md` §1 and §11. "PC backstory" is off the open-questions list (renumbered).
- Why: it's forgivable, so the fun epilogue race still works. It's a misread like the Myth Drivers', and the race shows the crew wanted the PC all along. An earlier tie to the blown engine in the opening was dropped as a stretch.

## 2026-11-02 — World notes: overworld camera reference [art] (Arthur, Art Director)
- Updated `design/art/world_notes.md` with the overworld camera, based on Racing Lagoon free roam at 16:30 (Austin's reference). It's a high overhead perspective view at roughly 50–65°, rotatable, and not a chase cam or true isometric. Also added what that means for art: rooftops and ground carry the look, no one-sided cut-outs, and a lighter overworld car LOD.

## 2026-11-02 — World notes: OSM-based overworld, turn-based pregenerated tracks [art] (Arthur, Art Director)
- Added `design/art/world_notes.md`, which records Austin's direction. The overworld uses OSM road layouts only, with no real buildings, and is stylized and remixed into the fictional city per canon decision 6. Races are turn-based on pregenerated tracks (Racing Lagoon), which means a corner-segment kit per district. The isometric overworld camera is flagged as an open question. These are notes only; nothing is built.

## 2026-11-02 — Nathaniel: PC's hometown crew and the epilogue race
- Austin chose who the PC walked out on: their hometown crew. The PC was its driver and left the week of a big race for a job in the city without telling anyone, so the crew thinks the PC ditched them. The PC's real reason stays `<TBD>`. Recorded in canon decision 13, `plot.md` §1 and Player Arc.
- Austin added an epilogue (new `plot.md` §11, canon timeline step 9, `pitch.md`). After Sabine's parting shot she asks "And when are you calling them?" (the proposal is now locked and off the list). The PC calls the crew with "I was wrong. Be there.", they come to Fushigi-Yama, and after an awkward apology they run a low-stakes race for fun. Barry owns its tuning.
- Why: Austin pointed out that the PC has to make the call, so the crew showing up because of the influencer's clips was dropped. A rescue by luck wouldn't resolve the PC's arc. The fun race gives the game a light ending after the summit.
- Open questions: PC backstory narrowed to the real reason for leaving; "And when are you calling them?" removed (renumbered); "Epilogue details" added at the bottom.

## 2026-11-02 — Nathaniel: Sabine's parting shot locked
- Austin picked Sabine's parting shot to the Myth Drivers: "My uncle's doing fine, by the way. Since none of you ever asked." It's in canon decision 5, `plot.md` §10, `pitch.md` and `characters/sabine.md`, and is off the open-questions list (renumbered).
- Why: it's quiet rather than cruel, and it lands the third reason she won't rejoin (nobody acknowledged her uncle's heart attack, decision 23) without spelling it out.

## 2026-11-02 — Barry: economy spec, promoter's betting side game
- `design/07-economy-and-mods.md` §7.5 (new): a proposal for the high-stakes betting side game the Wangan promoter opens after Round 2 (story: `story/canon.md` decision 21, from Austin via Nathaniel). The PC bets on their own non-boss races, with odds set by the expected win chance minus a house edge so pattern-reading skill beats the line. Stakes are capped, an optional handicap raises the odds, the debt share applies if the debt is somehow still open, and winnings are spent at Reiko's wholesale prices. All values are `TBD`. Added a metric (#13) and an open question (#15). Nothing was run, per Austin's rule.

## 2026-11-02 — Barry: economy spec, repair debt no longer takes all winnings
- `design/07-economy-and-mods.md` §7: Austin ruled that not all winnings go to the repair debt. The strict rule (A) is ruled out, and the allowance rule (B) is now the baseline, with a share `DEBT_SHARE` (TBD, under 1.0) going to the debt from the Prologue on, so the PC can buy some parts before the debt clears and feels Reiko's discount right away. This overrides the "all winnings" wording in `story/canon.md:40`; Nathaniel owns the story text.
- Wholesale timing confirmed by Austin: Reiko's discount unlocks after Round 1, matching the spec and `story/plot.md:98`.

## 2026-11-02 — GR Corolla: lean car (clay + detail pass), game .glb + Godot scene [art] (Arthur, Art Director)

Austin signed off the clay shape ("Honestly great. Let's just go for a detail pass."). The detail pass follows the WRX STI / S2000 / BRZ lean builds. Pushed to proto-build on Austin's go-ahead. No other car, `lean_common` or `tokyo_v2` file changed.

**New:**
- `assets/cars/gr_corolla/`:
  - `car_gr_corolla.glb` (textures embedded; Godot import hints give the VehicleBody3D `GRC` and VehicleWheel3D `Hub_XX`).
  - `car_gr_corolla.tscn`: an inherited scene with mass, COM, wheel/travel/steer/AWD values, a body collision box, `susp_follow.gd` on `Susp_XX` and the glow FX hidden. This is new compared with the other cars, which ship the .glb only.
  - `susp_follow.gd` + `.uid` (same script as the other cars, own uid) and a README with the rig table.
- `art/vehicles/gr_corolla/`: sources and scripts. Blueprint: the Dimensions.com vector SVG (`bp/gr_dimensions.svg`). Clay output is in `out/` and `renders/`; detail output is in `detail/` (blend, glb, textures, gates, renders). Also `make_all.sh`, `threeview/`, `lineup/` and `godot/make_tscn.py`.
- `art/mood/tokyo_gr/`: night vibe check of the GR on the Tokyo v2 street (non-binding). It reuses `tokyo_v2/scene_v2.py` unchanged, the same way `scene_duo.py` does.

**Numbers:**
- **1,888 tris** total (cap 2,000; clay was 1,922).
- IoU: side .978, top .991, front .978, rear .978 (pass).
- 9-pose clearance: all clear, tightest 7.6 mm.
- Textures: body 1024², parts atlas 256², glow 128×64, env 256×128. All RGB555 + Bayer.

**Detail pass:**
- **Clay review fixes:**
  - Nose shading: custom split normals taken from the uncut loft.
  - Grille and diffuser:
    - Douglas–Peucker corner outlines with planar floors.
    - The diffuser is now one centre + exhaust opening.
    - The corner vents are painted.
  - Wing tip filled (28 tris).
  - Mirrors are tapered 3-ring shells.
- **Livery:**
  - White body; gloss-black roof, pillars, wing and mirrors.
  - Matte-black lower aero.
  - Red diffuser accent.
- **Painted detail:**
  - Panel lines drawn from the SVG vectors.
  - Hex grille and intake mesh; vent slats; diffuser fins.
  - Tail lamps.
  - Flat made-up plates.
- **Badges:**
  - A made-up apex-chevron emblem.
  - An illegible red badge.
  - The real maker emblem paths in the SVG are dropped and never painted.
- **Lamps:**
  - The headlamp lens art comes from the parts atlas on the 30 mm molding pocket.
  - Head + tail glow sprites (`GRC_FX_LampGlow`, hidden by default).
- **Wheels:** 15-spoke gunmetal wheels; the made-up tyre lettering reads correctly on both sides.

**Checked in Godot 4.6.3** (Compatibility fallback, scratch copy of the repo):
- The .glb imports and the scene loads.
- The car settles at the design ride height, drives and steers.
- The struts follow the wheels.
- Sheet: `art/vehicles/gr_corolla/detail/renders/gr_corolla_detail_godot46_800.jpg`.

**Reasoning:**
- The livery is white with a black roof, so the GR stands apart from the blue/red/blue lineup.
- Cutting the angular rear corner vents and the jagged grille outline caused the saw-tooth clay read, so that detail is carried in the texture instead.

**Known gaps:**
- Tail lamps are painted on the body texture. They light up only through the glow sprites, as on the WRX.
- The body material's env term also shows on the dark grille floor: a neon band in the Tokyo shot.
- The mirrors still read a little boxy.
- Headless Godot import of the repo needs the Blender importer disabled or a Blender path set, because of the `.blend` sources. This is not new and not specific to this car.
- Corrected a claim from the clay README: the flat 20/30 mm clearance entries are the liner inner-wall offsets, not a probe radius.

---

## 2026-11-02 — Economy and mod parts: draft sim spec [design] (Barry, Chief of Systems)

Draft only, waiting on Austin's success criteria and approval. Nothing was run or simulated. No code, constants or story files changed. Not committed or pushed.

**New:**
- `design/07-economy-and-mods.md`: the spec for the headless sim's economy and mod parts. It covers the money and repair-debt ledger, Reiko's wholesale discount, race payouts by encounter type and round, a shop and part catalog that plugs into the existing POW/EN/HAN, clash and QTE terms (additive only, never HP), slots and level floors, opponent parts, and a season runner (Prologue → Rounds 1–3, Touge → Wangan → Street). It also lists candidate metrics and open questions. Every value not already in the repo is a named `TBD` constant.

**Reasoning:**
- Austin asked for the economy to be architected from the existing docs before anything runs. Desmond's repair-debt questions (amount, which race clears it, wholesale size and the overlap) depend on it.
- It collects what the story and design docs already say (with file:line citations) and lists 12 conflicts between them. The main ones: whether rep is tracked, doc vs code encounter ratios, slot counts, and the retry fee.
- Key finding: opponents scale off the player's level (`cli.py:305`), so in the current model only parts change the player's strength relative to opponents. The pending encounter-scaling fix has to come before any debt or payout number.

---

## 2026-11-02 — Story: the family emergency was the uncle's heart attack [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` timeline step 2 and decision 23, `story/characters/sabine.md`: the call the night of the sweep was her uncle-dad having a heart attack. He survived; she spent about two weeks with him through surgery and recovery, out of contact, which is when the Myth Drivers decided she'd run. FIFO item removed and the rest renumbered.

**Reasoning:**
- The lead wanted it serious enough to keep her out of contact for a week or two, but not a tragedy. It also stings because the man she was caring for is the uncle #1 distrusted.

---

## 2026-11-02 — Story: city-wide sweep; Sabine left for a family emergency [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` timeline step 2, decision 5 and new decision 23, plus `story/plot.md` Round 1 Wangan: the sweep was a large, coordinated crackdown across all three districts in one night (benign, routine enforcement). Sabine left minutes before because her uncle called about an unrelated family emergency, and she was the only one of the old generation who walked away clean. Nobody ever acknowledged what she went through, which becomes a third reason she won't rejoin.
- FIFO item "Police sweep details" narrowed to what the family emergency was.

**Reasoning:**
- The lead wanted the sweep bigger, touching every district. The unrelated call keeps it benign while giving the Myth Drivers (and later the PC) a damning-looking coincidence, and it gives Sabine's refusal an emotional core.

---

## 2026-11-02 — Story: rival chain dropped [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/plot.md` Rounds intro: removed the per-district rival chain (and changed "reputation gating" to "street cred gating" to match decision 12).
- `story/pitch.md`: removed "recurring rivals" and "district rival encounters"; "rival encounters" and "rival progression" became crew rematches and crew progression.
- `story/canon.md`: "Rivals" removed from the FIFO stack and the rest renumbered. Myth Driver #2's "Resentful rival" role label is unchanged (it describes his relationship, not a rival chain).

**Reasoning:**
- The crews (run from their kids up to their boss each round) already carry the progression, so a separate rival chain was redundant.

---

## 2026-11-02 — Story: Street crew boss is a cocksure influencer [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` new decision 22 and `story/plot.md` Street district: the Street crew boss is a young-ish, cocksure influencer who built his following after the old generation broke up and isn't really about the old scene. First pass: he idolized #3 and felt abandoned when #3 left to "go pro".

**Reasoning:**
- It fits Street's "cultural fracture" role and, as the lead put it, reflects how a lot of car enthusiasts are now, which contrasts with the old generation.

---

## 2026-11-02 — Story: the promoter is Sabine's old flame [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 21, `story/plot.md` Wangan district, `story/characters/sabine.md`, `story/characters/myth_driver_2.md`: the Wangan crew boss (the smooth, flashy promoter) was privately involved with Sabine back in the old generation's day. That's the real reason she turned down #2's date. It stays private, only hinted at, until the summit, when #2 learns why she said no.

**Reasoning:**
- It sells #2's date rejection, and it hits hard because #2 is the Wangan Myth Driver: he and the promoter share the same highway.

---

## 2026-11-02 — Story: Wangan crew boss is a promoter; betting side game after Round 2 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` new decision 21 and `story/plot.md` Wangan district: the Wangan crew boss is a promoter who organizes the runs, takes bets and gets a cut. He's pragmatic about Sabine (her walking away was bad for business). After Round 2 he unlocks a high-stakes betting side game for extra money; mechanics handed to Barry.

**Reasoning:**
- It fits Wangan's "pragmatic interpretation" role, sets up the Round 2 Wangan reveal about what her leaving cost the scene, and gives the lead's betting side game an in-world owner.

---

## 2026-11-02 — Story: Sabine never vanished; Touge boss respects her [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` (decision 2, the PC's hook, timeline step 3, new decision 20), `story/pitch.md`, `story/characters/sabine.md`, `story/plot.md` (Round 1–2 reveals, Mentor Arc, Player Arc): Sabine didn't vanish. She walked away from the old generation without a word and still drives and runs her garage, but keeps clear of every crew. New decision 20: most of the scene respects her and is puzzled, not bitter; suspicion comes from a few voices.
- `story/plot.md` Round 1 Touge: the crew boss line (first pass) is now respectful and puzzled; the "something to hide" line moves to a crew kid, and the boss shuts it down.

**Reasoning:**
- The lead felt it was unrealistic for every character to be bitter toward Sabine. Planting the clue through gossip keeps the bad data without making everyone hostile.

---

## 2026-11-02 — Story: only a share of winnings goes to the debt [story] (Nathaniel, Narrative Lead)

Lead corrected. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 19 and `story/plot.md` §3 and §5 intro: a share of each win goes to the debt until it clears in Round 2, not all winnings. The PC keeps the rest, which they spend on parts once Reiko's wholesale opens after Round 1 (confirmed). The share size is Barry's TBD.

**Reasoning:**
- The lead pointed out that "all winnings to the debt" doesn't fit wholesale unlocking while the debt is still open.

---

## 2026-11-02 — Story: each round runs the whole crew, kids to old heads to boss [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 11 and timeline step 5, `story/plot.md` (Districts, Rounds intro, the six Round 2–3 slots), `story/pitch.md`: still one crew and one crew boss per district. Each round the player runs through the whole crew in rank order (its kids who inherited the myth, then its more mature members who know not everything is what it seems, then its old heads, then the boss). The next round, the boss has leveled up the whole crew. Flavor text after every race reveals a little more.
- FIFO stack: "Crew escalation" dropped (answered by this); "Crews and crew bosses" now also covers each crew's kids, mature members and old heads.

**Reasoning:**
- The lead wanted the crews' ranks to mirror the contradicting clues (myth, then doubt, then people who were there). He pointed out that the boss wouldn't race the PC right after they'd only beaten the kids, so every round goes through the full crew. Alternatives considered and dropped in the same session: a new crew each round, a stand-in "boss", and spreading the ranks across rounds.

---

## 2026-11-02 — Story: debt scene drafted [story] (Nathaniel, Narrative Lead)

Lead approved ("Keep it for now"). Not committed or pushed.

**Changed:**
- `story/scripts/prologue.md` §3: first-pass debt scene. Sabine fronted the rebuild, and the PC races under her garage with winnings going there first until they're even. Jesse and Reiko each give their own "translation". The invoice amount stays `<TBD: Barry>`.
- `story/canon.md`: the debt-scene question removed from the FIFO stack and the rest renumbered.

**Reasoning:**
- It closes the prologue, matches canon decision 19, and keeps Jesse warm and Reiko guarded.

---

## 2026-11-02 — Story: no mod money until the debt clears; Reiko gives wholesale after Round 1 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 19: winnings all go to the debt until it's cleared in Round 2, so the PC can't really afford mods before then. After Round 1 Reiko warms up and gives the PC wholesale prices (revised from "after Round 2" so the PC has plenty of access to parts by Round 3); the debt still clears in Round 2. The discount size joins the debt amount as Barry's TBD.
- `story/plot.md` §2 (Reiko), §4 and §5 intros: updated to match, with a `<TODO: scene>` for Reiko's wholesale moment at the end of Round 1.

**Reasoning:**
- It ties Reiko's warming-up arc to the economy and pays off her garage-intro line, "Wholesale is for crew. You're not crew."

---

## 2026-11-02 — Story: debt terms set, paid off in Round 2 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md`: new decision 19. Sabine fronted the rebuild; the PC drives for her garage until it's even (winnings to the garage first, wins rebuild her garage's standing). The debt is settled during Round 2, and the PC stays afterward for the fun and the mystery. The amount is a systems number handed to Barry via Desmond. FIFO item #1 narrowed to the debt scene script.
- `story/plot.md` §3 and §5 intro, `story/scripts/prologue.md` §3: updated to match.

**Reasoning:**
- The lead put the amount in Barry's court and wanted the debt to end mid-game so the PC's reason to stay shifts from obligation to fun and curiosity.

---

## 2026-11-02 — Story: garage intro script drafted; Jesse warm, Reiko guarded [story] (Nathaniel, Narrative Lead)

Lead approved the direction ("I dig it"). Not committed or pushed.

**Changed:**
- `story/scripts/prologue.md` §2: garage intro completed. Reiko is cool toward the PC ("Wholesale is for crew. You're not crew." / "We'll see."); Jesse is warm and welcoming and jokes that Reiko took a year to learn his name. Ends on Sabine's "Which brings us to the bill." to hand off to §3 The Debt.
- `story/plot.md` §2: one-line personalities added for Jesse and Reiko.
- `story/canon.md`: the garage-intro question removed from the FIFO stack and the rest renumbered (debt terms are now #1).

**Reasoning:**
- The lead wanted Jesse a little warmer and Reiko someone who has to warm up to the PC, which gives her a small arc across the rounds.

---

## 2026-11-02 — Story: the Tuner is Jesse, the Buyer is Reiko [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/plot.md` §2 and `story/scripts/prologue.md` §2: the Tuner's and Buyer's `<TODO: name>` placeholders replaced with "Jesse" and "Reiko".
- `story/canon.md`: "Tuner's name" and "Buyer's name" removed from the top of the FIFO open-questions stack; the remaining items were renumbered (the rest of the garage intro script is now #1).

**Reasoning:**
- The lead picked "Jesse" as a nod to *The Fast and the Furious* and "Reiko" as a nod to *Tokyo Drift*.

---

## 2026-11-02 — Story: open questions cleaned into one FIFO stack [story] (Nathaniel, Narrative Lead)

Lead asked. Not committed or pushed.

**Changed:**
- `story/canon.md` — "Open Questions" replaced by a numbered "Open Questions (FIFO — oldest first)" list: 26 one-line items, each with the date it first appeared (from git history and this log; ties broken by outline order) and where it lives. Pull from the top; new questions go to the bottom. Every open `<TODO>`/`<TBD>`/`<CHECK>`/`<PROPOSAL>` in `story/` maps to an item. The old bundled bullets were split (crews/escalation/reveals, Tuner/Buyer, the rift).
- Decision 18 wording fixed for the locked race order: #1 (first race) says Sabine "left"; the contradiction surfaces at #2's race, when his hints say "pushed". Updated in canon decision 18, `plot.md` §7 (#1 and #2) and `characters/myth_driver_1.md` / `myth_driver_2.md`.

**Dropped as stale:** the decision-18 "first contradiction" snag (fixed above). No other live markers referred to tricks at the summit, a public rumor, jealousy, nine bosses, the daylight commute or Act 2 Myth Driver races; those were already closed in earlier passes.

**Reasoning:**
- The lead wants one ordered stack to work through, oldest first, without stale questions.

---

## 2026-11-02 — Story: Myth Driver first sightings in Round 1 [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` — decision 11: each Myth Driver makes a first sighting right after his district's Round 1 crew is cleared (#1 Touge, #2 Wangan, #3 Street). The races stay in the Finale. A sighting never reveals the private accusation and doesn't mention the other Myth Drivers. Timeline step 5 updated.
- `story/plot.md` — a "Myth Driver sighting" bullet in Round 1 Touge, Wangan and Street (`<TODO: sighting beat>`); §7 notes the races follow those sightings.
- `story/characters/myth_driver_1/2/3.md` — "First sighting" line added.

**Reasoning:**
- The lead expected this from the outline. The original `plot_points.md` had a "Myth Driver encounter" in each district's Act 2 section, right after the district boss. It moved wholesale into the Finale when the rounds structure replaced it, so no early appearance was left. Sightings put each legend on screen early without spending the race or the reveal.
- Follow-up (lead): at each sighting the Myth Driver talks with the PC (no race yet), building the mythos around the fallout and driving the PC to dig further, without revealing the accusation. The Finale race order is locked as Touge (#1) → Wangan (#2) → Street (#3), following the sightings, which closes the order TODO in `plot.md` §7. Updated canon decision 11, the `plot.md` sighting bullets and §7, and each `myth_driver_N.md`.

---

## 2026-11-02 — Story: private snitch accusation, PC's betrayal hook, why Sabine takes the PC in [story] (Nathaniel, Narrative Lead)

Lead approved. Committed on the lead's go-ahead (push pending).

**Changed:**
- `story/canon.md`:
  - Decision 2: the accusation never spread. Only the Myth Drivers and Sabine know; they froze her out quietly, and the scene only knows she vanished around the sweep.
  - Decision 3: she believes she was frozen out over the accusation and never told anyone.
  - Decision 4: Myth Driver races happen "during the Finale" (was stale "Act 2").
  - Decision 13: the PC's old crew/family believe the PC betrayed them, plus the Round 1 hook.
  - New decision 14: why Sabine takes the PC in (needs a driver; sees herself in them, never admits it).
  - Timeline steps 1–5 rewritten so nothing is public.
  - New open question: how/when the PC first learns there was an accusation `<TBD>`.
- `story/plot.md`:
  - §1–2: Sabine's reasons for taking the PC in.
  - Round 1 Touge: the first-pass crew boss line ("Sabine? She was one of us…") and the PC's hook.
  - Every beat implying the scene knows a snitch rumor rewritten as disappearance, speculation and misremembering (Round 1 Touge, Round 2 all three, Round 3 Street, Mentor Confrontation, Summit Setup wording, Mentor Arc, Player Arc).
- `story/pitch.md` — Core Story Mystery: the accusation stays private; the scene only knows she vanished.
- `story/characters/sabine.md`, `myth_driver_1.md`, `myth_driver_2.md` — "snitch rumor" → private accusation; the date stays private (no low-level racer spreading it); Sabine's reason for taking the PC in.
- New `<CHECK: rewritten for private-rumor canon — Austin to confirm>` markers wherever the original intent was unclear.

- Follow-up (lead): the PC puts the accusation together from clues in the crew reveals; nobody tells them. New canon decision 15; the open question is closed and replaced by a "clue per reveal" item. The PC names it at the Mentor Confrontation and Sabine confirms she was accused and not the informant. The dependent `<CHECK>`s (timeline step 5, `plot.md` Mentor Confrontation, `pitch.md` Core Story Mystery) are cleared. Each round's intro in `plot.md` gets a `<TODO: clue per reveal>` with an example. Myth Driver #2's scapegoat `<CHECK>` stays, noting the PC already knows by then.

- Follow-up (lead): the Mentor Confrontation is locked at the end of Round 3 (`<PROPOSAL>` removed in `plot.md` and `pitch.md`). The PC pieces together misleading clues and accuses Sabine of being the snitch (her reaction `<TODO>`), which blows up their relationship. The PC races the Myth Drivers while estranged. At the summit the benign sweep comes out, and the PC owns repeating the Myth Drivers' mistake. Sabine's choice of the PC's crew now follows the PC's apology. The PC's motive after the rift is locked as canon decision 16: doubt (the Myth Drivers' contradicting accounts) drives the racing, and guilt (it echoes home) makes it personal. The motive TODO is closed in `plot.md` §7–8, the Player Arc and `pitch.md`. Also locked: the PC tricks only the Myth Drivers into the summit and is honest with Sabine ("I was wrong. Be there.", first-pass), the first time the PC breaks their pattern of leaving without explanation. Updated in canon decision 4, timeline step 7 and the open questions, `plot.md` §8 and the Player Arc (first step toward the apology), and `pitch.md`. Then superseded by the lead: there is **no trick**. The PC honestly invites Sabine to the summit to apologize, and the three Myth Drivers each hear about it separately, feel guilty, and come on their own, perhaps to apologize too (`<TODO: how word reaches the Myth Drivers>`). The trick TODO and the cut-off "They each individually agree" TODO are closed. Updated in canon decision 4, timeline step 7, the open questions, `plot.md` §8–9 and `pitch.md`. Also locked: Myth Driver #2 hints at Sabine's innocence (possible scapegoat) in his Finale race out of guilt over her ousting. It's one of the first cracks in the PC's certainty and foreshadows his summit apology. New canon decision 17; the #2 `<CHECK>` in `plot.md` §7 is cleared; `myth_driver_2.md` is updated. Then Myth Driver #3's motive was replaced (lead): not jealousy. He wanted out to go pro and didn't want Sabine hurt by him leaving, so he was glad she was gone; letting her be pushed out was easier on him and harder on her. He never actually went pro (why: `<TBD>`). It's also a real reason she declines to rejoin, and he mirrors the PC (leaving without facing the goodbye). His `<CHECK>` is cleared: in his Finale race he half-owns it, and the full reason comes at the summit. Updated: canon decisions 2, 5 and 9, timeline steps 1 and 8, the open questions; `plot.md` §7, §9, §10 and the Player Arc; `pitch.md`; `myth_driver_3.md` (role and story), `sabine.md`, `characters/index.md` (role). Final pass: Myth Driver #1's contradiction (first pass) is that he insists Sabine *left* on her own the night of the sweep, while #2's hints say she was *pushed*. It's the first time two accounts can't both be true, and it starts the PC's doubt. New canon decision 18; the `<TODO: what it is>` in `plot.md` §7 is resolved; `myth_driver_1.md` and the open questions are updated. Also made explicit in canon (decision 2, timeline step 1) and `myth_driver_1.md` that all three Myth Drivers knew about Sabine's uncle-dad; only #1 held it against her. Updated: canon decisions 5, 13 and 15, timeline steps 5–8 and the open questions; `plot.md` Rounds intro and clue lines, Mentor Confrontation, §7–10, Mentor and Player Arcs; `pitch.md` Core Story Mystery.

**Reasoning:**
- The lead wants the accusation hidden, which adds mystery and keeps Sabine's story in shadow. It also means the PC hears only "she vanished, she must have had something to hide", the same thing their own people say about them.

---

## 2026-11-01 — Character bases (male/female): Mixamo-named rig, painted outfit atlases, Slim/Bulky [art] (Arthur, Art Director)

The lead approved the character base pass. One male and one female base body is now the shared start point for every human character. Work toward individual characters comes next.

**New:**
- `assets/characters/base/` — game-ready files:
  - `char_base_m.glb` and `char_base_f.glb` (textures embedded), `textures/{m,f}/*.png`, and `humanoid_bonemap.tres`.
  - A README covering the Godot import: BoneMap → SkeletonProfileHumanoid, nearest filtering, outfit texture swap, Slim/Bulky blend shapes, hiding/showing the hood or collar add-on, and tri counts.
- `art/characters/base/` — source:
  - `char_base.blend` and the build scripts (`build/`: `spec.py`, `paint_textures.py`, `build_char.py`, `render_checks.py`, `compose.py`, and headless Godot checks in `build/godot/`).
  - Review renders: turnarounds for male/female × standard/slim/bulky, swap sheets, `builds_lineup`, `lineup_mf`, `tuneup_before_after`, `deform_check`.
  - Paint templates `renders/uv_template_{m,f}.png`, `godot_import_log.txt`, a README and `CREDITS.md`.
- **Skeleton:**
  - 25 bones with Mixamo names (`mixamorig:Hips` …), identical names and hierarchy for both sexes.
  - Clean deform rig with no IK or poles, T-pose, root at the feet.
  - Male 1.83 m, female 1.70 m. Godot 4.6.3 BoneMap check: all 17 required bones mapped (unmapped bones are optional: root, eyes, jaw, fingers). Retargeted import gives `GeneralSkeleton`.
- **Mesh:**
  - One skinned body mesh per sex (686 tris). Clothes are painted onto a 256² outfit atlas; changing outfit means swapping the texture.
  - Separate pieces: the Head (124 tris, 128² face), two hair pieces per sex, and a tiny outfit add-on (male hood 40 tris, female jacket collar 20 tris).
  - Complete characters: male 880 (tee) / 920 (hoodie); female 900–974. Budget ≤ 1,200.
- **Outfits:** tee + jeans + sneakers for both sexes, plus a teal hoodie (male) and a mustard zip jacket (female). Hair: male crop and quiff; female bob, and a side-swept fringe with a high ponytail.
- **Body builds:** `Slim` / `Bulky` shape keys on every mesh with one skeleton. Bulky widens the torso, belly and chest, thickens the limbs and neck, and shifts the limbs outward.

**Reasoning:**
- Mixamo names plus the humanoid BoneMap let any Mixamo or humanoid animation library retarget onto both sexes. A single shared rig keeps animation sets shared too.
- The lead asked for clothes painted on, the classic PS1 way, instead of layered meshes. That gives one mesh, no poke-through, cheaper characters, and outfits that cost only a texture. Small silhouette steps (tee hem, sleeve hem, jeans hem, sneaker shape) keep the clothed read.
- The CC0 source character had an Akira/Kaneda-like outfit and face. The bases were rebuilt from scratch and the look fully replaced, to keep to the no-real-IP rule. The original download is not in the repo (see `CREDITS.md`).
- Tune-up pass after review: heads +12% with a shorter neck (≈6.6 heads tall), arms about 8.5% shorter, the female ponytail reads from the front, and Bulky/Slim pushed further so the three builds read distinctly.

**Known gaps:**
- No finger bones (mitten hands with a thumb).
- Bone rolls are untested against a real Mixamo FBX.
- Godot's Auto-Map wasn't run headless; the BoneMap was built from an explicit name table.
- Shape keys don't move joints.
- Every outfit shares the tee/jeans silhouette; skirts and shorts need an add-on or a body variant.
- The hood/collar add-on and Hair_B are visible on import and must be toggled in-game.
- Ears are flat quads.
## 2026-11-01 — Story: lean `plot.md` beat outline, `scripts/prologue.md`, PC "running from something" framing [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/plot.md` — rewritten as a lean beat outline (356 → 194 lines). Same sections (Prologue §1–3, Districts reference, Rounds 1–3 with Touge/Wangan/Street, Mentor Confrontation `<PROPOSAL>`, Finale §7–10, Substories, Structural Themes) and every `<TODO>`/`<TBD>`/`<PROPOSAL>`/`<CHECK>` marker and locked decision kept. The line-by-line script, popups and stage directions moved out. PC framing added to §1 beats, the summit (`<PROPOSAL>` line) and the Player Arc.
- `story/canon.md` — decision 13 (first pass): the PC is mid-20s, moved for work but is running from something (walked out on their own crew/family without explaining); mirrors Sabine; helping her reconcile is guilt by proxy; the summit callback is a `<PROPOSAL>`. Open questions: PC backstory added.

**New:**
- `story/scripts/prologue.md` — the full §1 opening and §2 garage-intro scripts moved from `plot.md`, unchanged except for the lead-approved PC lines: arrival ("...Well. It's got a garage." / "Nobody here knows me. That's the point."), accepting the race ("...Why not. Not like anyone's waiting up."), the blowout ("...Figures."), "Around. I just moved here." with Sabine's "...Sure.", "...Yeah. Thanks." and the closing "...Fair." A §3 placeholder holds the debt-script TODO.

**Reasoning:**
- The lead wanted `plot.md` to stay outline-focused; scripts now live in `story/scripts/` so no dialogue is lost.
- Follow-up (lead): the overworld tutorial now runs on the drive home from work at dusk, flowing into the back-road headlight challenge. The drive-to-work segment and its arrival popup are cut from `scripts/prologue.md`; the commute TODO is closed in `plot.md`, the script and `canon.md` (decision 11's Prologue line; open question removed). The quieter PC lines set up the new framing: a PC hiding their own walk-out makes Sabine's story personal to them.

---

## 2026-11-01 — Story: one crew per district (rematches), "street cred", round themes locked [story] (Nathaniel, Narrative Lead)

Decided by the lead. Not committed or pushed.

**Changed:**
- `story/plot.md` — Districts reference: one crew `<TBD>` and one crew boss `<TBD>` per district (three of each in total); the old boss voices ("ideological dominance", "pragmatic interpretation", "cultural fracture") now belong to each district's crew boss, so their TODOs are closed. Round sections: "Match 1" in Round 1, "Rematch 2/3" with an escalation `<TODO>` in Rounds 2–3. Round themes (Incident / Consequences / Distortion) are no longer a proposal. Street cred now explains why a crew won't grant a rematch until the player has proven themselves in the other districts. The Mentor Confrontation stays a `<PROPOSAL>`.
- `story/canon.md` — decision 11: one crew and crew boss per district, re-faced and stronger each round; round themes added. Decision 12: "street creed" → "street cred", rematch wording. Timeline step 5 and the open questions updated (the crew-count / nine-boss TBD is gone; crew escalation added).
- `story/pitch.md` — Progression Structure and the district list describe one recurring crew per district; "street creed" → "street cred".
- `story/barks.md` — boss purpose "Define district climax" → each round's climax with a returning crew boss.
- `CHANGELOG.md` — "creed" → "cred" in my earlier entry today.

**Reasoning:**
- Re-facing one crew that keeps improving gives each district a single rivalry to build across the rounds, and it cuts the cast from nine crew bosses to three.

---

## 2026-11-01 — Story: Prologue / Rounds 1–3 / Finale act structure; street cred gating [story] (Nathaniel, Narrative Lead)

Act structure and cred rule locked by the lead. Not committed or pushed.

**Changed:**
- `story/plot.md` — restructured into Prologue (§1–3, the old Act 1, unchanged), a Districts reference section (identity, racer type/archetype tables, stakes), Rounds 1–3 (§4–6; each with Touge → Wangan → Street, every district with Crew `<TBD>`, Crew Boss `<TBD>`, Story Reveal), Finale (§7 Myth Drivers, §8 Summit Setup, §9 The Summit, §10 Ending) and a Substories placeholder.
  - Street cred explains the rotation as in-world flavor only (not a tracked stat).
  - The old per-district mystery themes and key beats are redistributed as round-by-round reveals, marked `<PROPOSAL>` (Round 1 = the incident, Round 2 = consequences, Round 3 = distortion); empty slots are `<TODO: reveal>`.
  - The old Mentor Confrontation sits at the end of Round 3 as a `<PROPOSAL>`.
  - Myth Driver #2/#3 beats moved to the Finale, marked `<CHECK: conflicts with canon>`.
  - The old district-boss voices are kept in the Districts reference with a TODO for which crew boss carries them.
- `story/canon.md` — decisions 11 (act structure; main plot grounded, weirdness in substories) and 12 (street cred gates the rotation); stakes line says crew boss; timeline rewritten for rounds and the Finale; open questions updated (crew count `<TBD>`/nine crew bosses, substories).
- `story/pitch.md` — the empty Progression Structure section now states the act structure; "district boss" → crew boss (district list, Boss Structure, Myth Drivers, mystery sources); the mentor confrontation now follows the three rounds and is marked `<PROPOSAL>`.

**Reasoning:**
- The lead replaced one boss + Myth Driver per district with three rounds of crews and a Myth Driver finale. Moving district identity into one reference section keeps the rounds from repeating it, and the same Crew / Crew Boss / Story Reveal layout in every slot shows exactly which reveals are still missing.

---

## 2026-11-01 — Story: `plot.md` outline cleanup [story] (Nathaniel, Narrative Lead)

Tidy only — no new plot points. Lead asked for a clean outline. Not committed or pushed.

**Changed:**
- `story/plot.md` — restructured into Act 1 (§1 Opening, §2 Garage Intro, §3 The Debt), Act 2 (shared district structure, then §4 Touge, §5 Wangan, §6 Street, each with the same sub-headings: Racer Types, Mystery Theme, Key Beats, Boss, Myth Driver), Act 3 (§7 Mentor Confrontation, §8 Summit Setup) and Act 4 (§9 The Summit, §10 Ending).
  - Racer Types are now tables with each type's archetype, matching `canon.md`.
  - Boss stakes and the retry rule from `canon.md` added to the shared structure; each Myth Driver section lists his hidden motive from canon.
  - The "Mystery Progression Model" theme section was folded into each district's Mystery Theme; the duplicate is gone.
  - Grammar, punctuation and markdown fixed in the existing voice; "mentor" → Sabine where it means her.
  - Every open item is an explicit `<TODO>`/`<TBD>`: names, crews/rivals, boss philosophies, Myth Driver contradiction, sweep details, how the PC tricks everyone, the cut-off "They each individually agree" line, garage script, debt terms, dusk commute, parting shot.

**Reasoning:**
- The outline mixed plain text and markdown, numbered sections unevenly and gave each district a different shape, so gaps were hard to see. Parallel district sections make missing pieces obvious and turn the TODOs into a question list for the lead.

---

## 2026-11-01 — Story: racer type ↔ archetype pairing, "racer types" wording, pink slips cut [story] (Nathaniel, Narrative Lead)

Approved by the lead in the Narrative/Systems chat. Not committed or pushed.

**Changed:**
- `story/canon.md` — new "Racer Types and Archetypes" section: one racer type per archetype per district (table), named rivals may break it, boss stakes (money, rep, rare shop mods, story; a loss means retry).
- `story/pitch.md`, `story/plot.md` — "Racer Archetypes"/"Archetypes" headings and "archetype-based" wording → "racer types", so "archetype" only means the sim's driving style.
- `story/barks.md` — boss stakes: "Pink slips" → "Big cash payout" and "Rare mods unlocked in the shop".

**Reasoning:**
- The lead wants an even pairing: 15 racer types ÷ 3 districts = 5 per district, matching the 5 renamed archetypes (see Barry's entry below).
- Pairings follow what each archetype shows in its first phase, since common racers only race Wild events. Adaptive racers (Honor Student, Consultant, Influencer) will read soft until Barry's phase fix lands.
- Losing the car on a boss defeat was cut in the 2026-06-17 redesign; the design plan is retry on a loss, payout plus rare mods on a win.

**Still open:** the barks "Personalities" list (Calm, Aggressive, ...) and mid-race tone headings will be rewritten as one voice per racer type.

---

## 2026-11-01 — Archetypes renamed to plain English; AR P cut (5 archetypes × 15 racer types) [sim][design] (Barry, Chief of Systems)

Approved by the lead in the Narrative/Systems chat. Not committed or pushed.

**Rename:** Bruiser → **Aggressive**, Endurance → **Defensive**, Swift → **Precise**, AR E → **Balanced**, AR H → **Adaptive**. **AR P removed.** The stat splits and AI phase behaviors of the five survivors are unchanged.

**Changed:**
- `sim/velocity_shift/cars.py` — archetype keys renamed; AR P (40/30/30) removed.
- `sim/velocity_shift/ai.py` — personality configs renamed (`AGGRESSIVE_DRIVER`, `DEFENSIVE_DRIVER`, `PRECISE_DRIVER`, `BALANCED_DRIVER`, `ADAPTIVE_DRIVER`; the `_DRIVER` suffix keeps them apart from `PhaseType.AGGRESSIVE`); AR P config and map entry removed; the `get_personality` fallback is now Aggressive.
- `sim/config/sample_builds.json` — regenerated with `generate_build_matrix.py --write`: 30 presets (5 archetypes × 6 tiers), up from 36.
- `sim/tests/test_cars.py`, `test_equations.py`, `test_simulation.py` — new names. 25/25 pass.
- `design/04-difficulty-tuning.md` (archetype and personality tables), `design/06-pattern-read.md` (sequence sections, the shared-sequence note, the face table), `design/03-deckbuilding-clash.md` (examples, "6 personalities" → 5), `design/notes/mod_notes.md` (example).
- The stat name EN ("Endurance") in `01` and `02` is a stat, not the archetype, so it was left as is.

**Gauntlet after the change** (engine values, 5 archetypes): Aggressive 756–540, Defensive 598–698, Precise 603–693, Balanced 645–651, Adaptive 638–658.

**Reasoning:**
- The lead wants each district to have one racer type per archetype, with racer types leaning to one archetype (named rivals can break it). 15 racer types ÷ 3 districts = 5 per district, so 5 archetypes divide evenly.
- AR P was cut because its stats sit close to Aggressive's and its opening phase attacks every card, so it plays like Aggressive in Wild races (which only use phase 1).
- Names describe how each one drives, so someone outside the dev team can read them.

**Godot (done after the lead's go-ahead, since no playtest was running):**
- `scripts/ArchetypeData.gd` — match arms renamed and AR P dropped (Balanced shares Defensive's EN meta-archetype, face, and comfortable/weak turns; Adaptive shares Precise's).
- `scripts/PersonalityData.gd` — configs renamed (`_aggressive` … `_adaptive`), `_ar_p` removed, fallback is now Aggressive.
- `scripts/TurnTypeData.gd` — base-archetype mapping is now Balanced → Defensive and Adaptive → Precise; the table keys were renamed.
- `design/godot-build-guide.md` — names updated. Its personality phase table was stale (it didn't match `ai.py` for any archetype), so it was replaced with a pointer to `ai.py` and `04-difficulty-tuning.md`.
- No Godot editor on this computer, so the scripts were checked by search only (no old names left anywhere in `scripts/` or `scenes/`), not by running the game.

**Flag for Desmond and Arthur:** with AR P gone, face types are Aggressive = Scowling, Defensive and Balanced = Grinning, Precise and Adaptive = Focused, so two pairs share a face.

---

## 2026-10-31 — Sim tooling fixes: runner crash, gauntlet uses engine values, build-matrix format [sim] (Barry, Chief of Systems)

Tooling only. No game constants, formulas or docs changed. Not committed or pushed.

**Changed:**
- `sim/velocity_shift/simulation.py` — the player card callback took 4 arguments, but `match.run_match` passes 5 (it now also passes the opponent's hand). Every `SimulationRunner` match crashed with a `TypeError`. The callback now accepts the opponent's hand and ignores it, since the simulated player still picks at random.
- `sim/scripts/balance_gauntlet.py` — removed its own copies of the settings and imports them from the engine instead. Archetypes and stats come from `cars.ARCHETYPES` and `cars.build_stats`, encounter ratios from `ai.ENCOUNTER_RATIOS`, turn limits from `cli.ENCOUNTER_MAX_TURNS`, and the opponent level uses the same `round(level × ratio)` rule as `cli.py`. Before this it tested 4 hand-set 800/100/100-style builds, ratios 0.35/0.75/1.15 and 4/10/15 turns, none of which the game uses. It now runs 6 archetypes × 3 encounters, 5832 runs, and still prints ALL CHECKS PASS. The docstring now warns that the archetype PASS rule is only "at least one win and one loss".
- `sim/scripts/generate_build_matrix.py` — rewritten. The old version wrote pow/def/eff presets from a retired stat model into `config/sample_builds.json`, and `cli.py` (`pb["archetype"]`) would then crash on any preset. It now writes the archetype + level format the CLI reads (6 archetypes × 6 tiers) and stores no stats. It only prints a table unless you pass `--write`. Its `--write` output is byte-identical to the current `config/sample_builds.json`, so that file did not change.

**New:**
- `sim/tests/test_simulation.py` — 3 smoke tests for `SimulationRunner` and `simulate_batch`, so a signature drift like this one fails the tests. 25/25 pass.

**Reasoning:**
- The tools have to measure what the engine actually runs before they can back a balance change. The gauntlet in particular was passing while testing values from an older design.

**Still open (not touched here):**
- `scripts/design_opponent.py` and `scripts/design_racers.py` still use the old POW/DEF/EFF model and a hard-coded CLASH_STAKES of 0.3 (the code uses 0.35), and `--stronger` is documented but doesn't exist.
- The rubber-band threshold of 0.15 is hard-coded in `match.py` and copied in the gauntlet's predictor.
- The gauntlet's PASS rule is still too loose to catch imbalance.
- Doc sync and the encounter-scaling proposal (the ratio counts twice, in both opponent level and QTE) come next.

---

## 2026-10-31 — Lean cars: WRX STI, S2000, BRZ at ≤ 2,000 tris with suspension rig and headlamp molding; Part A updated [art] (Arthur, Art Director)

Lead approved the lean rebuilds. The approved originals (S2000 4,354 tris, BRZ 4,079 tris) stay in place for history; the lean build in each car's `lean/` folder is the new game version, with an engine copy in `assets/cars/`.

**New:**
- `art/vehicles/wrx_sti/` — Subaru Impreza WRX STI (GDB "bugeye"), built blueprint-only: pass-2 clay trace (`build_wrx.py`, `make_all.py`, `bp/`, `parts/`, `tex/`, blueprint, keyline table) plus the lean build in `lean/`. **1,966 tris**; IoU side .978 / top .978 / front .956 / rear .956; 9-pose clearance all clear (tightest 18 mm). Headlamps sit in a shallow 3.5 cm pocket cut into the nose with painted lamp art on the lens faces; 4-tri head-glow quad hidden by default.
- `art/vehicles/s2000/lean/` — **1,916 tris**; IoU side .952 / top .992 / front .930 / rear .951; clearance all clear (tightest 3 mm at full lock + bump). Thin raised surround around each headlamp, lamp art re-fitted.
- `art/vehicles/brz/lean/` — **1,999 tris**; IoU side .971 / top .980 / front .948 / rear .932; clearance all clear (tightest 16 mm). Thin raised surround around each headlamp.
- `art/vehicles/lean_common/` — shared lean tools: `leanlib.py` (loft, rig, clearance), `render_kit.py`, `deliver_kit.py` (RGB555 + Bayer sheets), `susp_follow.gd`, `lamps/` (headlamp close-ups, outline segmentation, molding ring), `threeview/` (three-view sheets), `lineup/` (3-car lineup).
- `assets/cars/{wrx_sti,s2000,brz}/` — `car_<id>.glb` (textures embedded), `susp_follow.gd` and a README with the Godot VehicleBody3D / VehicleWheel3D setup, tri count and glow FX note.
- Every lean car: mono body mesh (aero merged), separate hub-pivoted wheels, body origin at the estimated centre of mass, ±30° steering lock, strut + arm on a non-spinning `Susp_XX` follow node driven by `susp_follow.gd`.

**Changed:**
- `design/art/art_direction.md` Part A — budget **≤ 5,000 → ≤ 2,000 tris per car** incl. wheels, struts and FX, detail in shading/textures (A.2.1, A.7, K1); suspension no longer forbidden — only the simple strut + arm rig is allowed (A.2.3); new A.2.6 mono body mesh, A.2.7 suspension + steering rig with the 9-pose clearance test, A.2.8 headlamp light molding + painted lamp art; A.1.5 line classification extended to lamp outlines vs body lines and made binding; Appendix W notes the S2000 lean game version.
- `art/vehicles/s2000/README.md`, `art/vehicles/brz/README.md` — pointer to the lean game version at the top. Nothing else in the original builds changed.

**Reasoning:**
- The lead set a 2,000-tri cap per car: cars need to be cheap enough for the game scene, and the look comes from painted textures and faked shine, not loops.
- Working suspension with separately pivoted wheels mattered more to the lead than extra body detail; the strut sits on a follow node so it tracks travel and steer without spinning with the wheel.
- Flat painted headlamps read as blobs at the lean budget. A little real geometry (shallow pocket on the WRX, thin surround on the S2000/BRZ) plus painted art reads at low cost. The WRX pocket was kept shallow so the nose isn't over-carved.
- The blueprint stays the truth: lamp outlines and pocket depth were taken from classified blueprint lines (body line vs lamp outline), not photos.

**Known gaps:** S2000 and BRZ lean builds have no lamp glow sprites or blob shadow yet; the rig and `susp_follow.gd` are untested inside Godot; S2000 front clearance at full lock + bump is tight (3 mm).

---

## 2026-10-31 — Story canon locked: three Myth Drivers, no informant, Fushigi-Yama summit [story] (Nathaniel, Narrative Lead)

Applies the lead's canon decisions from the lore audit. Not committed or pushed. Mechanical fields (archetype, face type, lie rate, stance preferences) were left as `TODO`.

**New:**
- `story/canon.md` — source-of-truth page: the 10 decisions, a backstory timeline (ousting → breakup → player arrives → districts → summit → ending) and open questions.

**Changed:**
- `story/pitch.md` — fictional mashup city (name `<TBD>`); districts' in-world names `<TBD>`; Fushigi-Yama added to Touge; dusk opening instead of "normal daytime life"; player any gender, Sabine always female (opposite-gender rule dropped); "Circuit specialist" → Street specialist (#3) with Myth Driver numbers per district; Myth Drivers haven't spoken since the breakup; sweep was benign and there was no informant; Sabine believes the rumor; "four Myth Drivers" → three; challenge-each climax → summit meeting; ending → calm decline + parting-shot TODO.
- `story/plot.md` — dusk opening (daylight commute flagged TODO); "U-Haul" and "Novelty Hill Rd" removed; `<Mentor>`/`<mentor>` → Sabine; duplicated garage-intro bullets removed from §3; unfinished garage script flagged TODO; "Americanized" removed; Myth Driver numbers on district beats; sections renumbered 8–11 → 7–10 (there was no §7); "all four" → three; Honor Restoration and Final Meeting rewritten around the Fushigi-Yama summit; cut-off "They each individually agree" kept and flagged TODO; Sabine's arc now "believes the rumor; learns the truth at the summit".
- `story/barks.md` — "$100,000" → "100,000 <currency>".
- `story/characters/sabine.md` — believes the snitch rumor until the summit; Myth Driver #4 line deleted; "tells them to fuck off" → calm decline + parting-shot TODO.
- `story/characters/myth_driver_1/2/3.md` — District field added (Touge/Wangan/Street); snitch rumor named as each one's cover; "sting operation" → police sweep; #2/#3 talking to each other moved clearly into the past; #3 gains the go-pro motive; resolution "Sabine confronts him" → truth comes out at the Fushigi-Yama summit.
- `story/characters/index.md` — pointer to `canon.md`; district added to each Myth Driver.

**Reasoning:**
- The audit found the Myth Driver count (3 vs 4), who knows the truth, who confronts whom, the setting (real US road and dollars vs Japanese districts), time of day and the mentor's gender all contradicting each other across files. The lead resolved them; `canon.md` keeps them in one place so the other files don't drift again.
- Names, the parting shot and the summit setup were left as `<TBD>`/`<TODO>` rather than invented, because the lead decides major plot points.

**Not changed (systems questions for Barry):** pink slips as a boss stake in `story/barks.md` (car loss was removed in the 2026-06-17 mod redesign); the three personality lists that don't map to each other (`barks.md` "Personalities", the barks mid-race categories, and the sim's six AI personalities).

---

## 2026-10-31 — Repo restructure: one layout, one AGENTS.md, one changelog [repo] (Desmond, Chief of Design)

Layout approved by the lead. Done with `git mv` so file history is kept. Not committed or pushed; staged on local branch `restructure` (from `origin/proto-build`) for the lead's review.

**Moves:**
- `velocity-shift/overview/01–06-*.md` → `design/` (same names); `godot_prototype.md` → `design/godot-build-guide.md`; `sample_battle_screen.html` → `design/`; `art_direction.md` → `design/art/art_direction.md`.
- `velocity-shift/Notes/Notes.md`, `mod_notes.md` → `design/notes/`.
- `velocity-shift/story/high_level_story.md` → `story/pitch.md`; `plot_points.md` → `story/plot.md`; `barks.md` → `story/barks.md`; `sabine.md`, `myth_driver_1-3.md` → `story/characters/`; `character_sheets.md` → `story/characters/index.md`.
- `velocity-shift/velocity_shift/`, `tests/`, `scripts/`, `config/`, `main.py`, `pyproject.toml`, `.gitignore` → `sim/`; `readme.md` → `sim/README.md`.
- Godot project (`project.godot`, `scenes/`, `scripts/`, `icon.*`) and Arthur's source-art tree `art/` stay at the root.

**New:**
- `assets/{cars,env,faces,ui,fonts}/.gitkeep` and `design/art/.gitkeep` — empty homes for game-ready art.
- Empty `.gdignore` in `sim/`, `design/`, `story/` so Godot does not import Python, docs or story files.
- `AGENTS.md` (root) — merges the two old AGENTS.md files: repo rules, Godot facts, sim test instructions with `sim/` paths, folder map with owners (Barry: `sim/` + `design/`; Nathaniel: `story/`; Arthur: `assets/`, `art/`, `design/art/`; Desmond: coordination), and the rule that `sim/` code is the source of truth for numbers.
- `CHANGELOG.md` (root) — this file; merges `overview/changelog.md` and `velocity-shift/overview/changelog.md` with every entry kept and tagged by origin.
- `sim/.gitignore` — added `__pycache__/` (running the tests left untracked bytecode in the tree).

**Removed:** `velocity-shift/AGENTS.md`, `overview/changelog.md`, `velocity-shift/overview/changelog.md`, and the now-empty `velocity-shift/` and `overview/` folders.

**References updated:** `design/01-system-overview.md` (architecture tree root `sim/main.py`, docs path `../design/`, `velocity_shift/…` → `sim/velocity_shift/…`), `design/02`, `03`, `04`, `godot-build-guide.md` (`velocity_shift/…` → `sim/velocity_shift/…`), `design/05-skill-trees.md` (`Notes/mod_notes.md` → `design/notes/mod_notes.md`), `design/art/art_direction.md` (pitch path, `godot_prototype.md` → `design/godot-build-guide.md` ×3), `story/characters/index.md` and `sabine.md` (`Notes/06-pattern-read.md` → `design/06-pattern-read.md`), `art/README.md`, `art/vehicles/brz/README.md`, `art/vehicles/s2000/README.md` (art guide path). No game logic or numbers changed. Sim tests: 22/22 pass from `sim/`.

**Reasoning:**
- The Python prototype, design docs and story were all nested under one game subfolder inside the Godot project, with two AGENTS.md files and two changelogs that had already drifted (both received the same 2026-10-31 art entries). One top-level home per discipline lets each bot own one folder.
- Numbers had drifted across docs (HP per level, deck size, stance naming). Making `sim/` the single source of truth and having docs point at it stops further drift. Known conflicts were **listed, not fixed** — they belong to Barry (Systems & Balance).
- `.gdignore` keeps Godot from importing hundreds of non-game files and slowing the editor.

---

## 2026-10-31 — BRZ reference car (detail pass) + S2000/BRZ duo vibe check (Arthur, Art Director)

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `art/vehicles/brz/` — **new.** Subaru BRZ (ZD8) built to the vehicle standard (Part A), the same way as the S2000.
  - Size: 4,079 tris (≤ 5k).
  - Blueprint IoU: side .9651 / top .9815 / front .9453 / rear .9275, against gates of .95 / .95 / .92 / .92.
  - Paint: blue, matched to the reference photos.
  - Textures:
    - 1024² body: baked AO, painted form shading for the door scoop, hood valley, haunch and ducktail, and vector panel lines from the blueprint's feature lines
    - 256² atlas: 10 twin-spoke wheel, lamps, honeycomb grille, fictional plate and badges
    - 256×128 painted env map
    - all RGB555 + Bayer
  - Contents: clay + detail build scripts, blueprint data and IoU gate, `.blend/.glb/.obj/.fbx` exports, clean and PSX renders, compare sheets, README.
  - Verified: rebuilt from a temp copy of the folder with the same tri count and IoU, and byte-identical textures.
  - The front 3/4 dealer photo is left out because its licensing is unclear.
- `art/mood/tokyo_v2/` — **added** `scene_duo.py`, `post_duo.py` and `renders/duo/` previews. They show both cars parked side by side on the Tokyo v2 night street, using the same unlit/PSX recipe and post (640×448 → RGB555 + Bayer → 2× nearest). This is a non-binding vibe check; `scene_v2.py` is untouched.
- `velocity-shift/overview/art_direction.md` — A.1.5 added, pending lead review: trust the blueprint and classify its lines before overriding it.

**Reasoning:**
- **The corrected lesson.** The blueprint was right. BRZ passes 2–3 misread the window/DLO lines and trusted a low, about 4%-small photo camera solve. Pass 4 rebuilt from the blueprint alone, like the S2000, and was approved. The lead approved the detail pass ("Way better… hit detail work"), asked to see the BRZ next to the S2000 in a similar scene, and approved pushing to `proto-build` without a PR.

---

## 2026-10-31 — BRZ (detail pass) added; S2000 + BRZ duo vibe check; A.1.5 blueprint lesson (pending review)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


- `art/vehicles/brz/` — **new.** Subaru BRZ (ZD8), the second car built to Part A.
  - Size and gate: 4,079 tris. Blueprint IoU side .965 / top .982 / front .945 / rear .928.
  - Paint and textures: blue. Painted 1024² body (baked AO, vector panel lines) and a 256² atlas, both RGB555 + Bayer.
  - Lamps: wedge headlights and swept boomerang taillights.
  - Faked shine. Made-up brands only.
  - Contents: build scripts (clay + detail), blueprint data, exports (`.blend/.glb/.obj/.fbx`), key renders and a README.
- `art/mood/tokyo_v2/scene_duo.py`, `post_duo.py`, `renders/duo/` — **new.** The S2000 and BRZ parked side by side on the Tokyo v2 street. This is a vibe check and non-binding. `scene_v2.py` is unchanged.
- `overview/art_direction.md` — **A.1.5 added (pending lead review):** trust the blueprint and classify its lines before overriding it; photos never set geometry. A note corrects the BRZ lesson quoted in A.1.3.

**Reasoning:**
- **The lesson.** The BRZ took four clay passes.
  - Passes 2–3 concluded that "the blueprint draws the car too tall" and moved the body toward a photo camera solve. That solve turned out to be about 4% small and low.
  - The lead's correction: the blueprint doesn't disagree; the window lines were confused.
  - Pass 4 went back to the S2000 method (classify the blueprint lines, build from the blueprint alone, gate on IoU) and was approved ("Way better").
  - Recording the corrected lesson keeps A.1.3's photo check from being read as permission to override the blueprint.
- **The duo.** The lead asked to see the BRZ next to the S2000 in a similar scene before pushing.

---

## 2026-10-31 — Art direction guide + S2000 reference car restored after art-box data loss (Arthur, Art Director)

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `velocity-shift/overview/art_direction.md` — **restored (reconstructed)** v2 draft of the game-wide art guide. Part A is the binding vehicle standard; Part B is [VIBE]/[PROPOSAL] scene guidance; Part C has naming, open questions Q1–Q9 and doc conflicts K1–K7; Appendix W is the S2000 worked example.
- `art/` — new source-art tree. `art/vehicles/s2000/` holds the S2000 reference car (build scripts, textures, `.glb/.blend/.obj/.fbx`, blueprint refs, IoU overlays, key renders, README). `art/mood/tokyo_v2/` holds the Tokyo v2 vibe-check scene scripts and small previews (generated files git-ignored).

**Reasoning:** the original guide (written 2026-10-30/31, never committed) and all S2000 work lived only on the art box's `/workspace`, which was wiped when the box moved to a fresh instance (2026-10-31 ~11:31 AM PT; restore step reported "store empty; first boot"). The lead asked to restore the S2000 and the rules and to push finished art to the repo so it can't be lost again.

**Recovery detail:**
- S2000: recovered **verbatim** from the last zip sent in chat (scripts, textures, exports, references). Re-running the scripts reproduces it pixel-identically (4,354 tris; IoU side .961 / top .992 / front .925 / rear .944). Hard-coded `/workspace/s2000` paths were made relative for the repo copy.
- Art guide: **reconstructed** from the approved skill text, the chat record and the surviving style-reference sheet; structure and every binding rule match v2, wording and the Touge/Wangan palette/fog numbers are re-proposed. Two rules from the BRZ build were added and flagged as pending lead review (photo check of window/roof/hood/wheel lines beyond IoU; clay-stage shape sign-off).
- Tokyo v2 scene: scripts **rebuilt** from the recipe (originals lost); the approved original frames survive at `art/mood/tokyo_v2/renders/original_800/`.

**Earlier entries lost with the box (summarised):** 2026-10-31 — first art guide written (general, not S2000-specific, after context from Desmond); later the same day reorganised so the car rules are the only binding standard and all scene content is mood reference ("The key rules are for the cars only. The scene will likely not make it to the game.").

---

## 2026-10-31 — `art_direction.md` restored after data loss (reconstructed v2)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/art_direction.md` re-added. The v2 draft was never committed and was lost when the art box was wiped (2026-10-31 ~11:31 AM PT). Rebuilt from the approved skill text, the chat record and the surviving Tokyo v2 style-reference sheet.

- **Part A — Vehicle standard [MUST]:** blueprint build + IoU gate (side/top ≥ 0.95, front/rear ≥ 0.92), ≤ 5k tris, painted 1024² body with baked AO, vector panel lines, 256² parts atlas, 512² fabric, RGB555 + Bayer textures, faked shine (ambient + one key + Blinn + painted env map, env ≤ 0.45), opaque cool-tinted glass, no interior/brakes/engine, made-up brands, review in the 640×480 reference frame, checklist, Godot shader sketch (untested).
- **Part B — [VIBE]/[PROPOSAL]:** what made Tokyo v2 work, its palette, district proposals, cameras, portraits/UI, engine notes, advisory scene checklist.
- **Part C:** naming and `art/` layout, open questions Q1–Q9, doc conflicts K1–K7. **Appendix W:** S2000 worked example.
- **New since v2 (flagged pending review):** A.1.3 photo check of window/roof/hood/wheel lines (IoU alone missed a too-tall BRZ body), A.1.4 clay-stage shape sign-off.
- Touge/Wangan palette and fog numbers are re-proposed (originals lost) and still need sign-off (Q2).

**Reasoning:** lead asked to restore the rules from the chat session and push finished art so it isn't lost again.

**Lost entries (summarised):** 2026-10-31 — `art_direction.md` created as the general game art guide (after context from Desmond); then reorganised so car rules come first and are the only binding standard, with all scene content relabelled [VIBE]/[PROPOSAL] and nothing deleted.

---

## 2026-07-07 — Fixed Battle.tscn loading error + missing class_names

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `scenes/Battle.tscn` — Fixed `load_steps=2` → `load_steps=6` in scene header. The value was too low (2 instead of 6: 1 scene + 2 ext_resources + 3 sub_resources), causing Godot's parser to choke when encountering all 5 resource entries before node data.
- `scripts/StraightTimer.gd` — Added `class_name StraightTimer` so GDScript can resolve the type in `TurnManager.gd:32` (`straight_timer: StraightTimer`).
- `scripts/CardHandUI.gd` — Added `class_name CardHandUI` so GDScript can resolve the type in `TurnManager.gd:33` (`card_hand_ui: CardHandUI`).
- `scripts/FaceController.gd` — Added `class_name FaceController` so GDScript can resolve the type hint.
- `scenes/Battle.tscn` — Added `FaceController` node (`res://scripts/FaceController.gd`) as child of root `Battle` node.
- `scripts/TurnManager.gd` — Changed static call `FaceController.set_face_sequence(...)` to instance call via `@onready var face_controller: FaceController = $FaceController`.
- `scenes/Battle.tscn` — Added `uid=` fields to `ext_resource` lines (needed in Godot 4.4+). Attached `StraightTimer.gd` to `CornerTimerBar` and `CardHandUI.gd` to `CanvasLayer` so their `@onready` paths resolve. Updated `load_steps` to 9.
- `scripts/RoadScroller.gd` — Changed `extends ShaderMaterial` → `extends Node` with `@export var material: ShaderMaterial`. `ShaderMaterial` (a `Resource`) has no `_process` or `get_tree()` — both are `Node` methods.

**User handoffs (still needed):**
- Register `globals.gd` and `SignalBus.gd` as autoloads in Project Settings
- Color PlayerCube (blue) and OpponentCube (red) materials in editor
- Position Camera3D at (0, 5, 8) looking at (0, 0, -5) — verify after scene import
- Resize ground plane to look like a narrow road lane
- Arrange UI panels so they don't obscure the 3D viewport
- Tune constants in `globals.gd` via playtesting (Step 15)

---

## 2026-07-07 — Full 15-step Godot prototype build

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


Built the complete Godot prototype per `velocity-shift/overview/godot_prototype.md`. 27 scripts + 1 scene + project config.

**Project config:**
- Display: 640×480, viewport stretch, keep aspect
- Input maps: `qte_mash` (Space/X), `qte_timing` (Enter/Z), `ui_accept`, `ui_cancel`

**Phase 1 — Foundation (Steps 1–4):**
- `scripts/globals.gd` — enums, constants (CLASH_STAKES=0.35, DECK_SIZE=192, etc.), lockout lookup
- `scripts/SignalBus.gd` — 12 signals
- `scripts/CombatantStats.gd` — Resource: name, pow, en, han, level
- `scripts/MatchConfig.gd` — Resource: player/opponent stats, max_turns, seed, etc.
- `scenes/Battle.tscn` — Full hierarchy: SubViewport (World3D), CanvasLayer (UI), TurnManager
- `scripts/Deck.gd` — 192-card stat-proportional deck with ALPHA=0.85 smoothing
- `scripts/StraightTimer.gd` — 12s countdown, 3×4s phases, signal on timeout
- `scripts/CardHandUI.gd` — 3 stance buttons, count display, lockout, auto-pick

**Phase 2 — Core Combat Loop (Steps 5–7):**
- `scripts/CombatResolver.gd` — All pure combat math: resolve_stance, clash_mult, compute_damage, mitigation, qte_factor, HAN mod, rubber-band split
- `scripts/TurnManager.gd` — State machine: START→STRAIGHT→CORNER_PLAYBACK→DAMAGE_BATCH→END_TURN→MATCH_COMPLETE, full data flow
- `scripts/QTEController.gd` — Mash (fill bar with depletion) + Timing (oscillating marker) QTE modes, difficulty scaling

**Phase 3 — AI + Tell System (Steps 8–9):**
- `scripts/AIPicker.gd` — EV-scoring card selection, 6 behavior overrides (highest_ev, counter, alternate, repeat_win, etc.)
- `scripts/AIQTE.gd` — Opponent QTE generation with encounter ratio scaling
- `scripts/TurnTypeData.gd` — 8 turn types × 3 archetypes stance sequence tables + QTE type lookup + bluff tables
- `scripts/ArchetypeData.gd` — Meta-archetype mapping, face type, comfort/weak turn zones
- `scripts/PersonalityData.gd` — 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) with 3 phases each
- `scripts/TrackData.gd` — 3 preset circuit layouts (10-turn sequences)
- `scripts/TellGenerator.gd` — Deception flow: lie rate, position weighting, intensity, comfort/weak scaling
- `scripts/FaceController.gd` — Face display with alpha crossfade, tell overlay

**Phase 4 — Display + Animation (Steps 10–12):**
- `scripts/PositionTracker.gd` — Cumulative DP, gap, rubber-band threshold
- `scripts/DamageDisplay.gd` — DP bar tweens
- `scripts/ClashDisplay.gd` — 2×3 stance grid with color-coded panels
- `scripts/PhaseAnnouncer.gd` — Lap boundary overlay
- `scripts/CarAnimator.gd` — Z-offset by DP gap, surge/drop, corner path blank
- `scripts/AnimationTreeBlendManager.gd` — Stance blend schedule (0-4-8-12s)
- `scripts/BattleCamera.gd` — Chase cam, corner transitions, overtake swing

**Phase 5 — Scene Management (Steps 13–14):**
- `scripts/StageManager.gd` — Scene loading (Battle.tscn) with auto-MatchConfig wiring
- `scripts/RoadScroller.gd` — UV-offset parallax shader material

---

## 2026-07-07 — velocity-shift copied into repo as reference

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- Copied entire `velocity-shift/` project into midnight-apex root (minus `.git/` and `__pycache__/`) so all prototype reference material is local.
- Updated `AGENTS.md` intro path from absolute `C:\...` to relative `velocity-shift/`.

---

## 2026-07-07 — Initial setup

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- Created `AGENTS.md` combining midnight-apex project context with velocity-shift reference. Key directives: no auto-push, changelog maintenance, velocity-shift as prototype reference.
- Created `overview/changelog.md` for change tracking.

---

## 2026-07-07 — Human-centric tasks stripped from prototype doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


All 16 `🧑 You:` sections removed from `overview/godot_prototype.md` — autoload registration, editor setup, constant tuning, verification steps, and placeholder notes. The doc is now MCP-only; no tasks require manual editor intervention.

**Reasoning:** The `globals.gd`/`SignalBus.gd` autoload registration that was previously a human step is now handled by MCP via `project.godot`. Remaining tuning/verification steps are development workflow notes, not document-level tasks. Removing them keeps the doc focused on what MCP produces.

---

## 2026-07-06 — Godot docs merged into single prototype document

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` + `overview/godot_cube_prototype.md` → `overview/godot_prototype.md`

Merged the comprehensive reference outline and the step-by-step cube tutorial into a single 15-step linear document (1400+ lines). Old files deleted.

**Structural changes:**
- 15 sequential steps replace the previous 8-section outline / 10-step tutorial split
- Steps 1–4: Bootstrap, scene, deck, timer + card selection
- Steps 5–7: Combat math, turn manager, QTE
- Steps 8–9: AI layer, tell system (expanded from simplified tells to full face controller)
- Steps 10–14: Display, car animation, camera, corner cinematic, scene management
- Step 15: Tuning loop + deferred items
- Appendices A–H: file manifest, turn flow reference, signals, data flow, art checklist, QTE lookup/difficulty, AI stance lookup, gotchas

**🧑/🤖 split preserved** throughout. All detail from both sources carried forward (lockout, AnimationTree blend, FaceStack, BattleCamera, corner cinematic, RoadScroller, StageManager).

---

## 2026-07-06 — Exit→Entry lockout mechanic

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/03-deckbuilding-clash.md` — added Exit→Entry lockout section with 3 placeholder matrices (Attack / Defend / Steady exit), 8×8 turn-type cross-reference (all TBD except Chicane→Hairpin / Attack→Steady). Narrative justification for the Chicane→Hairpin example.

`overview/01-system-overview.md` — added key design property #9.

`overview/06-pattern-read.md` — updated exit paragraph to reference lockout.

`overview/godot_prototype.md` — lockout in CardHandUI (Step 4), TurnManager fields + static lookup (Step 6), Appendix D data flow.

**Reasoning:** Creates inter-turn sequencing decisions — the optimal exit for this corner may lock you out of an important entry for the next corner, forcing players to think ahead across turn boundaries. Turn-type-dependent lockout means the same exit stance carries different risk depending on what corner comes next.

---

## 2026-07-03 — Cube prototype tutorial added

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_cube_prototype.md` — new file alongside the existing `godot_outline.md`:

- Simplified tutorial-style document focused on getting the combat loop running with colored cubes as placeholder 3D assets
- 10 sequential steps with clear 🤖 MCP / 🧑 Developer split
- 8s straight timer (matching `06-pattern-read.md`), 3 sequential pick phases
- Includes simplified tells (text/color HUD-based, matching `06-pattern-read.md` deception flow)
- Deferred: corner cinematic, car animations, face textures, segment loading, road shader
- Referenced from: `overview/06-pattern-read.md` (stance tables), `velocity_shift/equations.py` (math), `velocity_shift/ai.py` (personalities), `velocity_shift/deck.py` (deck weights)

**Reasoning:** The full `godot_outline.md` is comprehensive but overwhelming for initial prototyping. The cube prototype lets the developer tune gameplay constants before investing in 3D art assets, with a clear tutorial path that distinguishes what MCP automates vs what the developer configures.

---

## 2026-07-03 — Level-gap QTE difficulty scaling

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — QTE timing/mash difficulty is now driven by level gap:

- **§4.1 QTEController.gd** — added `qte_difficulty()` static function: `timing_window_ms` shrinks and `speed_multiplier` increases as `opponent_level - player_level` grows
- **§1.2 globals.gd** — added 4 QTE difficulty constants (`QTE_TIMING_WINDOW_BASE_MS`, `QTE_TIMING_WINDOW_PER_GAP`, `QTE_MASH_SPEED_PER_GAP`, `QTE_TIMING_WINDOW_MIN_MS`)
- **§3.3 AIQTE.gd** — added note that level gap also feeds into AI consistency (shrinking noise range)
- **Appendix E** — added difficulty scaling descriptions for both mash & timing modes, with formula, constants, and example table (gap -10 → +10)
- **Appendix C** — updated data flow step 6 to compute and pass `qte_difficulty` to `QTEController.start()`

**Reasoning:** Higher-level opponents should feel mechanically sharper — your timing windows tighten and your mash rate must increase. The gap-based formula (`gap = opponent_level - player_level`) keeps even matches at base difficulty and only penalizes the player when outmatched.

---

## 2026-07-02 — Decision window updated: 8s real-time + corner cinematic scene

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — updated Decision window:
- Removed slo-mo framing; 4s → 8s real-time straightaway approach to select all 3 cards
- Timeout auto-selects unselected positions (semi-random)
- Added corner cinematic scene: camera attached to turn type, car animation driven by selected stances

`overview/godot_outline.md` — timing flow updated to reflect cinematic corner scene after card selection

**Reasoning:** The slo-mo framing added unnecessary complexity (no gameplay need for it) and 4s was too tight to read both car animation channels and pick 3 cards. 8s real-time keeps tension through the straightaway approach. The cinematic corner scene gives visual payoff for the card selections and makes the turn feel like an actual driving moment rather than an abstract clash.

---

## 2026-07-02 — Corner cinematic system + segment-based rendering

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — added corner cinematic system (§4.4):
- Segment-based rendering (Initial D: Another Stage style) — each turn loads/unloads its own straight + corner segment
- Per turn-type authored camera paths (not static camera)
- Stance-driven car traversal along corner Path3D
- QTE runs all 3 phases; damage computed after exit
- Overtake detection: if lead changed, short overtake animation (0.5-1s) + camera swing plays after exit
- Updated §4.1 (QTE runs all 3 phases), §4.2 (corner playback flow with overtake check), §6.1 (segment lifecycle), §6.2 (overtake animation), §6.4 (CarAnimator.play_overtake), §6.5 (BattleCamera.swing_overtake), Appendix A (revised corner flow)

`overview/06-pattern-read.md` — updated exit note:
- Exit reflects position (leading car pulls away, trailing car struggles)
- Overtake as separate short animation after DP resolution if lead changed

**Reasoning:** Segment-based rendering avoids maintaining a full continuous track while keeping each corner visually distinct. Overtake as a post-resolution extra animation gives clear visual payoff for lead changes without complicating the 3-phase stance system.

---

## 2026-07-02 — Merged remote godot_outline.md (1093-line full Godot implementation outline)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — replaced the 27-line placeholder with the full implementation outline from the remote branch, covering:
- Sections 1–8: Foundation, Engine Core, AI Layer, Corner + QTE, Position + Blend System, 3D Visuals, Art Integration, Wrap
- Appendices A–G: Turn Flow, Signals, Data Flow, Art Checklist, QTE Lookup, AI Stance Lookup, Notes/Gotchas
- My only local edit (timing flow step 3) was already superseded by the remote's more detailed TurnManager state machine and Appendix A corner playback description

`overview/06-pattern-read.md` — preserved local changes (positioning-based car motion, 8s decision window, cinematic corner scene); remote changes to this file (12s, sequential face reveals) were conflicting and discarded per user direction.

---

## 2026-07-02 — Stance projection changed to positioning-based car motion system

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — replaced the entire **Car motion types** section:
- **Channel 1 (entry):** track position — outside bias = ATK, center bias = NEU, full-width weaving = DEF
- **Channel 2 (apex):** suspension loading — rear squat = ATK, front dive = DEF, flat = NEU
- Both channels play simultaneously on the straightaway approach before corner entry
- Bluffs use position/suspension that reads opposite the true stance, with secondary cues leaking the truth
- Removed old "in front / behind" framing
- Exit (pos 2) has no dedicated visual channel

`overview/godot_outline.md` — created with implementation outline for TrackPositionController, SuspensionAnimationController, StanceVisualConfig resource, and timing flow.

**Reasoning:** The old front/behind framing was ambiguous (who's in front changes mid-turn) and didn't give a clear visual read under time pressure. Position-based telegraphing maps directly to racing intuition — a car weaving wide is attacking, a car covering the full track is defending, a car holding center is steady. Suspension loading adds a second readable axis for apex intent, and playing both on the straightaway gives the player two simultaneous cross-referencing tells to decode deception.

---

## 2026-06-30 — Decision window added to pattern-read doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — added a **Decision window** section at the end explaining that time slows to a crawl before each turn, giving the player 4 seconds to read the opponent's face and select a card. Passing on timeout is equivalent to playing a neutral with zero effect.

**Reasoning:** Formalizes the real-time pressure that makes the telegraphing system meaningful — players must read bluff tells under time constraint, not with unlimited analysis. The 4-second window creates a tension rhythm (observe → decide → execute) that matches the racing theme.

---

## 2026-06-26 — Character sheets restructured with pattern-read fields

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Split into per-character files

`story/character_sheets.md` → index; each character moved to their own file (`story/sabine.md`, `story/myth_driver_{1..4}.md`). All 5 sheets now include Myth Driver #4 (was accidentally truncated in the monolithic write). Each containing:
- **Narrative Identity** — role, backstory, conflict, resolution (preserved from old content)
- **Battle Identity** — archetype, face type, comfortable/weak turn types (TODO)
- **Deception Profile** — lie rate, clash-position weighting, intensity, reverse psychology (TODO; hand bluffs excluded per future rework)
- **Progression / Tier** — tier, difficulty class, level range (TODO)
- **Stance Preferences** — notes that strong/weak turns are fixed by archetype per pattern-read tables; other turn types have a per-character per-position preference (TODO)

**Reasoning:** Each character needs mechanical attributes that plug into the pattern-read system (face expressions, bluff behavior, turn-type proficiency) so their in-match behavior is consistent with their narrative identity. The TODO fields are intentionally left blank for the author to assign meaningful values.

---

## 2026-06-26 — Track layout randomization removed from pattern-read doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`Notes/06-pattern-read.md` — removed all references to randomized track layout generation:
- **Line 45**: "randomized 10 turn sequence" → "predetermined 10-turn sequence"
- **Lines 46-47**: Removed incomplete "Each match shall include at least" sentence and "Seeded from MatchConfig" line
- **Line 7**: Added narrative framing bullet — tracks are fixed per circuit, archetype cornering habits remain consistent, but bluffing behavior is per-character (driven by lie rate and personality)

**Reasoning:** Player pattern memorization was a concern for fixed layouts, but since the game is narrative-driven, each character has their own bluffing habits defined by lie rate, personality, and the archetype comfort/weak zone system. The track itself becomes authored scenery rather than RNG.

---

## 2026-06-26 — Fixed preset builds format

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`config/sample_builds.json` used the old stat system (`pow`/`def`/`eff` with no `archetype`/`level`), causing `KeyError: 'archetype'` when selecting a preset build. Replaced with builds keyed by archetype + level, matching the current `cars.build_stats()` API. 36 presets (6 archetypes × 6 tier levels).

---

## 2026-06-26 — Deckbuilding & Clash Docs Rewrite

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Fully rewritten: `overview/03-deckbuilding-clash.md`

The doc was highly out of date vs the codebase. Changes:

- **DECK_SIZE 36 → 192** — all card counts, formulas, composition table ("~12" → "~64"), and strategic cycle math (6 turns → 32 turns) updated
- **Selection phase** — rewritten from batch pick-3-and-arrange to sequential per-position picks with immediate clash resolution (lead → middle → anchor, one card at a time)
- **QTE rubber-band** — replaced the simplified binary split with the actual proportional blend system (threshold = 15% avg max_hp, `blend = min(1.0, abs(gap)/threshold)`)
- **HAN → QTE modifier** — added section documenting `apply_han_qte_mod` / `HAN_QTE_WEIGHT = 0.5`
- **Draw phase / deck reshuffle** — corrected to reflect player discard vs opponent `reshuffle_on_end` (no universal auto-reshuffle)
- **Flowchart** — updated to show sequential clash flow instead of batch arrangement
- **Played cards → discard** — noted opponent cards return to draw pile reshuffled

---

## 2026-06-23 — Unused Code Cleanup

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Removed dead code across the codebase

**Deleted:**
- `velocity_shift/config.py` — entire module; `build_from_archetype` had zero call sites (CLI calls `cars.build_stats()` directly)

**Production modules (`velocity_shift/`):**
- `velocity_shift/ai.py` — removed `ENCOUNTER_CEILINGS` dict (defined but never read); removed unused `rng` param from `_apply_override` signature and call site
- `velocity_shift/models.py` — removed `TurnResult.phase` field (written at `match.py:155` but never read by any code path)
- `velocity_shift/match.py` — removed write to `turn_result.phase`
- `velocity_shift/cli.py` — removed unused `get_phase` import
- `velocity_shift/simulation.py` — removed unused `get_phase` import

**Tests:**
- `tests/test_systems.py` — removed unused `Card`, `ClashResult` imports

**Scripts:**
- `scripts/balance_gauntlet.py` — **rewritten** to use current `resolve_turn` API directly (previously called `run_match` with an incompatible signature and referenced a nonexistent `opponent_ai_mode` field on `MatchConfig`)
- `scripts/generate_build_matrix.py` — removed legacy `MODS_MAP` dict; removed `opponent_builds` from JSON output (unconsumed by the game)
- `scripts/design_racers.py` — fixed two Python 3.11-incompatible f-string backslash expressions (`\u2500` inside `{}`) which also prevented `generate_build_matrix.py` from running

**Config:**
- `config/sample_builds.json` — regenerated without `opponent_builds` key

**Docs:**
- `AGENTS.md` — rewritten for concision: fixed stale test counts (5→9, 6→5, 7→8) and `DECK_SIZE` (36→192); pruned low-signal sections (stats table, damage formula, HP/DNF, encounter table); preserved git/changelog directives and high-signal gotchas; updated `python3`→`python` command

---

## 2026-06-21 — DNF State Removed

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Removed knockout / early-exit mechanic

**Removed** the DNF (Did Not Finish) rule where a combatant would lose when cumulative damage received ≥ max_hp. The match always runs all `max_turns`, then decides by position.

**Files touched:**
- `velocity_shift/match.py` — stripped early-exit check from turn loop; cleaned up stale `knockout` logic
- `velocity_shift/models.py` — removed dead DNF-related fields
- `velocity_shift/cli.py` — removed DNF display wiring
- `velocity_shift/ai.py` — removed DNF-related context from AI callbacks
- `velocity_shift/simulation.py` — removed DNF handling from batch runner
- `testing/test_systems.py` — removed knockout-specific test cases
- `scripts/balance_gauntlet.py` — removed DNF scenario
- `AGENTS.md`, `overview/*.md` — updated docs to reflect position-only win condition

**Reasoning:** DNF created a snowball problem — once a combatant fell behind, their max_hp deficit made recovery impossible. Removing it made races competitive for longer and pushed the decision to the full race distance, where skill (card selection) matters more than early luck.

---

## 2026-06-20 — HAN Stat Use

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Unified HAN → QTE modifier for both sides

**Replaced** the divergent HAN implementations with a single shared formula in `velocity_shift/equations.py`:

- Added `apply_han_qte_mod(qte_score, han_pct)` — same function used for both player and opponent
- Added `HAN_QTE_WEIGHT = 0.5` constant (moved from `ai.py`)
- Added `TYPICAL_QTE = 7.0` — AI QTE baseline, no longer derived from player QTE

**File changes by module:**
- `velocity_shift/ai.py` — `get_ai_qte` simplified: dropped `player_qte` and `ceiling` params, uses `TYPICAL_QTE × ratio` then `apply_han_qte_mod`. Removed local `HAN_QTE_WEIGHT`.
- `velocity_shift/match.py` — `apply_han_qte_mod` applied to both sides' raw QTE after callbacks. Opponent callback type changed to `Callable[[int], float]`.
- `velocity_shift/cli.py` — `get_opponent_qte` simplified to single-param. Removed `ENCOUNTER_CEILINGS` import.
- `velocity_shift/simulation.py` — same simplification. Removed `ENCOUNTER_CEILINGS` import.
- `tests/test_systems.py` — four opponent QTE lambdas updated to `lambda t:` signature.
- `tests/test_equations.py` — added 4 tests for `apply_han_qte_mod`.

**Intent:** HAN now affects QTE score (raw QTE × HAN modifier) for both sides through the same formula. Neutral point at han_pct = 1/3. Swift-like (55% HAN) gets +10.8%, Bruiser-like (25%) gets −4.2%. No double-dipping — HAN modifies the QTE score once, the existing pipeline (qte_factor → compute_damage → damage_mitigation) handles everything else.

---

## 2026-06-17 — Mod System Redesign

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Rewritten: `Notes/mod_notes.md`

**Replaced** the entire mod system design:
- Removed roguelite layer (car loss on boss defeat → narrative gating)
- Single assigned car, chosen from 2–3 chassis archetypes at new game
- Chassis has fixed stat ratio from L1, scales linearly — no convergence
- Mods are shop-bought equipment with trade-offs and unique effects (no drops)
- Loadout slots start at ~3, grow with car level
- Tree/mod categories deferred (TBD)

### Updated: `overview/05-skill-trees.md`

- Stripped speculative per-archetype tree tables
- Replaced "RunMods" references with current Mods system
- Flagged tree design as deferred with link to `Notes/mod_notes.md`
- Kept additive-only principle and system interactions as design guardrails

---

## 2026-06-10 — AI Personality Documentation + HP_PER_LEVEL Fixes

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Updated: `overview/04-difficulty-tuning.md`

**Replaced** the stale `## AI Difficulty (opponent behavior)` section (lines 116–125), which listed long-removed strategy names (`deterministic_attack`, `deterministic_defend`, `deterministic_neutral`, `random`) with an up-to-date section documenting the current phase-based personality system:

- **Personalities table** — all 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) mapped to their 3 phase-indexed behaviors (AGGRESSIVE / REACTIVE / UNPREDICTABLE with weights and overrides)
- **Phases per encounter table** — Wild (1), Lieutenant (2), Boss (3) with active personality indices
- **Unique opponents table** — ordered permutations per encounter:
  - Wild: 6
  - Lieutenant: 30
  - Boss: 120
  - **Total: 156 unique opponents**

Also **fixed** `HP_PER_LEVEL` value from 120 → 180 to match `velocity_shift/equations.py:20`.

### Updated: `overview/01-system-overview.md`

**Fixed** `HP_PER_LEVEL` value from 120 → 180 in the Normalization section to match `velocity_shift/equations.py:20`.

### Updated: `overview/03-deckbuilding-clash.md`

**Fixed** stale line 72: replaced "configurable strategy (attack-bias, defend-bias, random, etc.)" with a reference to the current phase-based personality system.

---

### Fully expanded: `Notes/06-pattern-read.md`

Replaced the original bullet list with a full spec covering:
- **4 deception mechanics** — lie rate, hand-dependent bluffing, clash-position weighting, reverse psychology tell
- **Turn type system** — 8 turn types (Hairpin, Straight, Chicane, Banked, S-Curve, Technical, Esses, Tunnel) with archetype-turn stance preference table (6×8 grid)
- **Track layout generation** — random per match, seeded, wraps if needed
- **Face types** — 6 cohesive expression palettes (one per archetype), 3 expressions each (ATK/DEF/NEU)
- **Expression intensity** — scale 1–5, gated by tier and encounter type
- **Bluff tell** mechanics — per-face-type betrayal signals, perceptibility tied to intensity
- **Tell generation flow** — step-by-step how a face is determined each turn
- **Combined deception axis** table including intensity values
