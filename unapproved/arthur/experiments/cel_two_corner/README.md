# Cel A on the two-corner test (experiment, unapproved)

Austin, 2026-11-14: "I like Cel A. Are you able to apply this to the two corner test and do a quick playtest?"

This is a test only, not a direction. It is Cel A from `../cel_shaded/` (commit f470dcc) ported onto Gordon's playable two-corner test. Gordon's folder (`unapproved/gordon/two-corner/`) is **not edited**: `stage.py` symlinks his Godot project in, and this folder owns only the files below. No models or textures are changed. It is all shaders, post and one script.

## Toggle
- Project setting `cel/enabled` (in `godot/project.godot`, default on), user arg `-- --cel 0|1`, or **F7** live in game.
- Off is Gordon's look exactly: every cel shader branches back to his original code, and the four G-buffer viewports stop rendering.

## What was ported
- **Three-band toon ramp, texture flattening, car posterise / hard spec / 3-step env**: the Cel A shaders (`godot/shaders/*.gdshader`, `cel.gdshaderinc`), with a `cel_on` global around each change.
- **Ink**: 1 px at 640×480, #040810, near side only, fading into the Touge fog (#0B172B, 9–78 m). Cel A's still frames used a global switch and rendered the frame two extra times. A game can't do that inside one frame, so here each shader picks colour / normals / depth from its **camera's cull layers** (layers 19 and 20, which no object uses). Four extra SubViewports render in the same frame from cameras copied off the main and rear-view cameras: main normals, main depth, mirror normals, mirror depth. The rear-view passes only render while the mirror is shown.
- **RGB555 + 4×4 Bayer dither**: kept, unchanged.
- **HUD**: untouched. It stays Gordon's 1280×960 pixel-hard layer, composited over the post rect after the dither. The 3D stays at 640×480.
- `godot/scripts/main.gd` is Gordon's script plus the blocks marked `# CEL:` (viewports, toggle, fog → ink, road flatten, decal layer, perf counter).

## Fixes made during the playtest
1. **The rear-view filled with ink.** The mirror looks down a grazing road, where depth climbs fast from row to row, so every row passed the "neighbour is farther" test. The fix is that a silhouette now also needs a real break in 1/depth. 1/z is affine across any flat surface, so its second difference is about 0 on planes. This is `lap_k` in `post.gdshader`, and it also stopped a few ink rows on the far road. See `playtest/mirror_check.png`.
2. **Car decals were inked.** The blob shadow and headlight throw are StandardMaterial3D planes, and they drew into the G-buffer as solid shapes with a dark outline. They are now on layer 18, which the colour cameras see and the G-buffer cameras don't.
3. **Asphalt speckle crawl.** The touge asphalt sits at luma 0.092 / 0.124, and 0.124 falls exactly on a 10-step posterise boundary, so the road broke into specks that crawled as it scrolled. Road strips now use radius 6 (as Cel A did) and 9 steps, and the road reads flat and calm.

## Playtest: what ran
Godot 4.6.3 (GL Compatibility, `--rendering-driver opengl3` under xvfb; the box has no GPU, so this is **Mesa llvmpipe software rendering**). The game ran its own scripted-input path through the real game loop: `spec/shots9_pass.json`, seed 3, the full race. That covers corner 1 (Hairpin L) and corner 2 (N90 R), each with the Entry select, the Apex and Exit camera stops, LINE LOCKED, playback with three QTEs, RESULT with the pass after the Exit QTE, the countdown, and the finish screen. Both cars swap places on both corners. The run takes about 55 s of game time. There were no errors in any Godot log; the only warning was "Could not set V-Sync mode" from the software driver.

- `frames/cel_on/*.png`: 12 key frames at 1280×960 (the final judged frame with the HUD).
- `frames/cel_off/*.png`: 5 cel-off matches. The run is deterministic at a fixed 30 fps, so these are the same game frames.
- `cel_two_corner_compare_sheet.png`: off | on for those 5 frames.
- `cel_two_corner_run.mp4`: the whole run, cel on, 1280×960 at 30 fps (CRF 30 so it fits the repo; a CRF 20 copy is at `/workspace/cel_two_corner_run.mp4` on the box). `off_vs_on_side_by_side.mp4`: the whole run off | on, at 640×480 each.
- `playtest/`: the mirror, HUD and motion checks, plus the numbers and scripts behind them. `./run.sh playtest` rebuilds everything, and `./run.sh perf` re-measures.

## Findings
**Performance** (real-time scripted race, wall time per frame, 4 runs, llvmpipe):

| | mean frame | avg fps | p95 |
|---|---|---|---|
| cel off | 46.7–48.5 ms | 20.6–21.4 | 53–57 ms |
| cel on | 65.5–66.1 ms | 15.1–15.3 | 79–80 ms |

Cel on costs about +18 ms a frame (+37 %) on a software rasteriser: four extra 640×480 / 192×64 geometry passes, plus a 9-tap post. On a real GPU those passes are small, but **this box can't measure that**. Please check it on a GPU machine before reading anything into the absolute fps.

**HUD contamination: none.** In the same game frame, every fully opaque HUD pixel (63,940 at frame 60) is identical with cel on and off. Only the translucent plate fills differ, because they show the 3D through them (`playtest/hud_check.png`). The HUD gets no toon shading and no ink.

**Mirror: correct after fix 1.** The rear-view ink comes from its own G-buffer, flipped the same way as its colour. Lines sit on the rail, kerb and trees, and nothing crosses the inset border. The cedar trunks in the mirror do read busy.

**Shimmer, crawl and popping.** Two measures were used:
- **Temporal colour change** (mean |frame t − t+1|, cel on ÷ cel off, same frames; `playtest/temporal_diff.json`):
  - forests 0.91–1.19×
  - far road and horizon 0.97–1.10×
  - near road 0.40–0.71×, so cel is calmer there because the flattened asphalt removes the grain crawl.

  The ink adds at most about 20 % flicker on the cedar walls, and nothing on the road.
- **One-frame ink pops** (`playtest/ink_pops.json`): about 60 % of ink pixels change in a single frame, against about 31–37 % for the cel-off colour edges. In absolute terms the ink line is about twice as jumpy as plain image edges.

Where it shows:
1. **Cedar cards.** The inner card-against-card silhouettes crawl as the forest streams past. It's visible but low contrast, because the ink is navy on dark green and fades into the fog. In the distance it mostly vanishes into the fog, as intended.
2. **Car outlines.** They step a pixel with the PSX vertex snap and the body bob, so they pop slightly; that is the same as Gordon's silhouette, only now drawn.
3. **Lane lines.** No ink: the paint is in the texture, and the chevrons are kept out of the G-buffer. The dashed centre line keeps Gordon's existing zig-zag; that's his road mesh, it shows with cel off too, and the 1 m-grid fix from the districts mockup isn't in his build.
4. **No popping on static views.** The Apex and Exit stops are pixel-stable frame to frame.

## Honest read
Cel A holds up in play better than I expected. The cars, guardrail posts and road edges keep a clean, steady hand-drawn line through both corners, the HUD is untouched, and the flattened road is actually calmer in motion than the original. The weak spots are the cedar walls (fine line crawl as they stream past) and the busy trunks in the rear-view, plus a software-renderer frame cost that needs checking on a GPU. If we keep going, the next step is thinning ink on the cedar cards rather than changing the look.
