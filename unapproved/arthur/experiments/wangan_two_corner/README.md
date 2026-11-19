# Wangan two-corner playtest (Cel A soft) — Arthur, unapproved experiment

Austin (2026-11-15): "Think we can mock up a Wangan track in Godot as well? Same rules, any assets that don't exist, make them
in blender?" → he picked **Two-corner Wangan playtest**. This is the touge `cel_two_corner` Cel A soft playtest moved onto the
Bayshore route: same RaceCore flow (SELECT → TIMING → RESULT), same QTE, same B.5b camera stops (Entry chase, Apex, Exit),
same rear view, same HUD. Only the course, the dressing, the cameras and the district look change. Nothing here is approved.

## What was built
- **Course** (`W1_Bayshore_Run`): an elevated 3-lane expressway over the bay.
  - **SW "SWEEPER L"**: one 60° arc at R 85 m.
  - **IR "INC RADIUS R"**: 60° in two arcs, 45 m then 110 m (30° each), so the corner opens up on exit. Effective R is 77.5 m.
  - Both are fast and wide, not hairpins. Stats, rung 6 and no-mods are unchanged from Gordon's two-corner build.
- **Deck**:
  - The road has painted lanes (6/6 m dashes), edge lines, shoulders, drain slots, an expansion joint every 40 m, and pools of sodium light under the staggered lamps.
  - Curved concrete parapets are bent per 4 m onto the path. Each side has a fascia band, a lip and a soffit.
  - A pier stands every 40 m and a km post every 30 m. Sodium lamps are every 48 m, staggered left and right.
  - There are overhead sign gantries: 湾岸線 BAYSHORE RTE 東 EAST, 出口 2km EXIT 3, and 速度注意 CURVE.
- **Far scene**:
  - A painted city skyline band with lit towers.
  - A bay water plane with broken sodium reflection streaks under the lamps.
  - Four container cranes on the right quay, each with an aviation light.
  - A cable-stayed bridge ahead past the finish.
  - The star sky was repainted at 384 rows so the stars stay round.
- **Style**: the locked Cel A soft rules.
  - Toon bands and the 1 px #040810 near-side ink go on cars and props only, and the ink fades into fog (`ink_near` 12 / `ink_far` 150).
  - The road, shoulders, deck, sky and water are lit smoothly, with no bands. Lane paint, chevrons, streaks and shadows are on the decal layer and never inked.
  - RGB555 + Bayer runs last. The HUD is composited after and never shaded.
  - 3D renders at 640×480 and the HUD at 1280×960, with a 2× nearest upscale.
  - TXR navy fog is #0B172B. The only light colour is sodium #F0C894, with no neon. Godot 4.6.3 GL Compatibility.
- **Rules**:
  - No floating OUT/MID/IN lane markers (I turned off the `lanes` branch in `main.gd`).
  - The rear view shows what's behind whenever the chase camera is up.
  - No LIMP tag.

## Blender assets (`blender/build_wangan.py` → `godot/assets/env/*.glb`, counts in `tri_counts.json`)
| asset | tris | note |
|---|---|---|
| wangan_parapet | 28 | new; 4 m profile module, bent onto the curve in Godot (`wangan_dressing.gd`) |
| wangan_pier | 116 | new; T-pier with bearing caps |
| wangan_gantry | 210 | new; truss gantry with 3 hand-lettered signs and sodium sign lamps |
| wangan_kpost | 10 | new; green km post |
| wangan_crane | 116 | new; container crane silhouette + aviation lamp |
| wangan_bridge | 416 | new; cable-stayed bridge silhouette, deck lamps cut to ±x faces (was 552) |
| wangan_lamp | 42 | from the districts kit (galv pole + sodium head) |
| wangan_tower_0/1/2 | 8 each | from the districts kit (lit tower cards) |

Textures are hand-painted in code in `tex_src/make_tex.py` and quantised to RGB555 + Bayer. The water streak is the only one
saved unquantised, because it is a soft decal. Every `art/env/*.png.import` uses `compress_to=0`, so nothing is VRAM-compressed.
The `assets/env/wangan_*_*.png` files are textures that Godot extracts from the GLBs on import. They are not committed, and
Godot regenerates them.

## How to run (box: `/workspace/tools/godot` 4.6.3, Blender 4.2.3, xvfb)
```
./run.sh assets     # repaint textures + rebuild the Blender kit + reimport
./run.sh play       # play it. F7 cel on/off, F8 Cel A soft / original Cel A (also --cel 0|1, --cel-soft 0|1)
./run.sh playtest   # scripted race (spec/wangan_pass.json, seed 3) at fixed 30 fps: key shots on/off, frame dumps,
                    # both videos, playtest/checks.py, make_sheet.py   (OUT=/tmp/wtc by default)
./run.sh perf       # real-time llvmpipe frame times, cel off/on twice
```
`spec/wangan_pass.json` is a scripted run with a real pass on both corners. `godot/tools/find_pass.gd` found it.
- Corner 1: picks 4/5/0, QTE 0.8. The player takes the lead.
- Corner 2: picks 0/1/3, QTE 0.3. The rival comes back and wins 3.75 to 3.44.
- The closest side-by-side gap is 3.26 m.

## Outputs
- `wangan_two_corner_contact_sheet.png`: 9 frames, Cel A soft.
- `wangan_two_corner_compare_sheet.png`: cel off next to Cel A soft, same game frames.
- `frames/`: entry select, apex stop, exit stop and playback apex for each corner, plus `finish.png` and `mirror_check.png` (rear view ×3, cel off / Cel A soft / ink mask). `frames/cel_off/` has the same frames with cel off.
- `wangan_two_corner_run.mp4`: 960×720, 7.2 MB, 55 s. The full-res copy is at `/workspace/wangan_two_corner_run.mp4` (1280×960, 32 MB).
- `playtest/checks.json`, `playtest/hud_check.png`, `playtest/mirror_check.png`.

## Playtest checks (`playtest/checks.py`, 1647 frames at 30 fps)
| check | result |
|---|---|
| HUD untouched | bright HUD text pixels 100.0% identical cel on vs off (line lock, plan panel, plate, gap bar) |
| Mirror ink flood | rear-view inset ink 6.2% mean / 10.5% max (outlines of parapet, lamps, deck edge only; no flood) |
| Decals inked | 0 of 869k chevron pixels and 0 of 282k lane-paint pixels inked |
| Road crawl | near-road frame-to-frame change 8.3 (cel on) vs 10.6 (off): calmer than the plain renderer |
| Isolated road specks | 0.96% on vs 0.55% off. These are static texels (drain slots, joint teeth) carried on the scrolling road. They don't shimmer. |
| Posterisation (hard steps in the de-dithered luma) | road 25.7 vs 43.8 off, sky 23.1 vs 24.2, bay 17.0 vs 22.1: no banding added on big surfaces |

## Frame times (llvmpipe, box, real time, full scripted race)
| | mean | p50 | p95 | p99 |
|---|---|---|---|---|
| cel off | 45.8–46.0 ms | 44.7–45.4 | 52.1–54.3 | 58.0–60.2 |
| Cel A soft | 72.9–74.7 ms | 71.9–73.7 | 85.2–89.4 | 90.3–97.1 |

That is about 9 ms slower than the touge Cel A soft (64.7–65.5 ms). The extra cost is the bigger soft-blurred surfaces: water
and a wider road. llvmpipe is a CPU rasteriser, so these numbers only compare builds against each other and say nothing
about a real GPU.

## Bugs found in the playtest and fixed
1. Floating OUT/MID/IN lane markers were showing in the HUD on the straights. They are now turned off, per the rules.
2. The water streaks read as dashed white lines. They are repainted as soft, wobbly, broken streaks.
3. The fascia drip stains were blotchy and noisy. I calmed them.
4. The stars were stretched into rain-like streaks, because the old 128-row sky was stretched. I made a new 384-row `wangan_sky`.
5. The IR exit cut camera sat too low and close, so the back of the parapet filled the frame. I moved it to d_in −14/−12.5 at h 4.4/3.8.
6. There was no pass in the scripted run (MIN_SEP 99). The seed 3 inputs above now give a pass and a lead change.
7. New PNGs were imported with `compress_to=1` (VRAM). `run.sh assets` now forces 0.
8. Engine fixes:
   - A duplicate `k` in `_stop_pose` caused a parse error.
   - `build_static` was typed `Node3D` but is given a SubViewport.

## Honest weak spots
- **Lamp poles**: they are 1–2 px wide, so they come out almost pure ink, as dark lines against the navy sky. In the rear view they nearly vanish. The lamp heads are mostly above the frame at the stops.
- **Expansion joints**: the soft road blur wipes out most of the joint teeth, and what survives shows as small dark dashes.
- **Bay**: it is very dark. The reflection streaks only read near lamps, and the cranes and bridge are faint at fog distance.
- **Gantries**: they read only as a small green sign far ahead on the entry straight. None of the stops frames one up close.
- **Course length**: the course is short. Each corner is about 90 m of arc, so at these speeds the sweepers feel brief.
- **Cost**: Cel A soft costs about 27 ms per frame on llvmpipe over cel off.
