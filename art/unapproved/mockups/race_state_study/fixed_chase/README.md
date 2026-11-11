# Fixed original-v5 chase visibility / Entry-read study

## Primary deliverable (required top-centre mirror)
- `comparison_with_mirror.png` — annotated 2x2 study, 2620x2690.
- `01_ahead_pressure_mirror.png`
- `02_ahead_room_mirror.png`
- `03_close_behind_mirror.png`
- `04_far_behind_mirror.png`

## Unassisted control
- `comparison_unassisted.png` — annotated 2x2 control, same chase framing.
- `01_ahead_pressure_unassisted.png`
- `02_ahead_room_unassisted.png`
- `03_close_behind_unassisted.png`
- `04_far_behind_unassisted.png`

All gameplay files are 1280x960, exact 2x nearest of native 640x480 images saved in `raw/`. Mirror is exactly 192x64 native pixels at top centre, not an enlarged opponent cutout. Both comparison sheets state the mirror is a visual proposal, NOT IMPLEMENTED in the engine. No mirror appears in unassisted images.

## Exact fixed geometry and camera
Coordinate frame below is Blender Z-up, +Y forward along the straight. Yellow Miata ND is PLAYER, red S2000 is RIVAL throughout. Existing assets are used unchanged.

PLAYER root is fixed at (0, -28, 0.16), heading +Y, in Center. RIVAL x is always -3.3 (clean Outside relative to the same RIGHT HAIRPIN); both car roots have rotation XYZ (0,0,pi). Only rival Y moves:
1. Ahead under pressure: -22; +6 m longitudinal lead.
2. Ahead with room: -10; +18 m longitudinal lead.
3. Close behind player: -34; -6 m longitudinal lead.
4. Far behind player: -46; -18 m longitudinal lead.
6/18 m are centre-to-centre illustrative staging only, not thresholds. No distance adjustment was necessary.

Main camera matches original `lane/build_v5.py` straightaway chase transform:
- World location: (1.4, -35.6, 3.1).
- Offset from player root in world/travel-aligned axes: (1.4, -7.6, 2.94).
- Offset from the road-level player reference: (1.4, -7.6, 3.1).
- Look target: (3.6, -6, -0.9), i.e. original v5 ground-reference target offset (3.6, +22, -0.9).
- XYZ Euler approximately (82.324878, 0, -4.250655) degrees. Full matrices recorded in camera_staging.json.
- Perspective, lens 25 mm, horizontal sensor 36 mm, horizontal fit, 640x480, square pixels.
- Horizontal FOV 71.507775 degrees; effective vertical FOV 56.738093 degrees.
No orbit, zoom, recenter, overhead substitute, camera shake or per-state adaptation. Verification checks all four camera matrices/lenses exactly match and player position stays fixed.

## Visibility findings
1. Ahead/close: S2000 is fully visible in the forward frame. Native mesh footprint about 96x50 pixels; its outside lane placement and near gap are readable.
2. Ahead/far: S2000 remains visible, about 40x24 pixels. Outside lane is still readable relative to dividers; precise detail is reduced.
3. Close behind: rival is outside the forward frustum (left/below; part is behind the camera). It is NOT shown as a ghost or offscreen marker. Entry unavailable unaided.
4. Far behind: rival is entirely behind the forward camera. Entry unavailable unaided.
The two unassisted trailing frames are expected to be pixel-identical: neither contains rival information. This is a useful result, not a missing render.

## Actual mirror proposal / limits
Same rear camera and FOV in all four states:
- World mount: (0, -28, 1.60), above player roof, looking rearward.
- Look target: (0, -60, -2.2), a fixed ~6.77-degree downward pitch to retain road context.
- Lens 14 mm / 36 mm horizontal sensor; horizontal FOV ~104.25 degrees.
- Native render 192x64. Rendered with real scene depth and car geometry, then horizontally flipped and composited one-to-one at native rectangle x=224..415, y=16..79.
- No scaling, relocation, ghosting, enlarged lamps or alternate car gaps in the mirror. Forward-scene framing never changes.
- Ordinary front headlamp sprites use low emission .20. The original painted lamp pixels on the actual S2000 mesh are made emissive with a root-local lamp-region / texture-luminance mask; no lamp spacing or geometry is changed. No headlight throw or brake cue. No added mirror bloom is needed; markings are retained.

Ahead cases have no rival in the mirror, because it is in front of the rear camera. Both trailing cases show genuine headlights/car geometry. The close case is larger; the far case has only a small number of body/lamp pixels. Actual projected car footprint is about 45x21 native mirror pixels close, versus only 9x6 far. verification.json also records reference FX attachment projections, explicitly NOT measured visible-lamp centroids. Reflected lane markings remain the comparison reference. A 192x64 still supports a coarse lane/gap read close, not precise lateral position, range estimation or a reliable moving tell at distance. The Miata's own roof/rear silhouette occludes part of the lower rear view; it is genuine geometry and is not erased to improve the result.

Important orientation nuance: a rear-facing Z-up camera already reverses the world-X viewing basis; horizontal mirroring reverses it again. Do not assume an unqualified 'world left always becomes screen right' rule. This study uses the actual rear camera plus one horizontal flip and does not fake the orientation to satisfy that shorthand. Entry must be interpreted relative to the reflected road/corner context, NOT a fixed screen-left/right=stance label. No OUT/ATK text is added to the mirror or rival to give the answer away.

## Current mechanics / art
This is selection-start information only. Full player three-card line locks before playback. Outside=ATK Entry is held clean and constant; no Entry bluff. No explicit Apex/Exit tells, hidden/reactive badges, future stance assignments, projected true line, portrait, hand strip, braking or turn-in cue. No specialization assumptions, approved habit table, probabilities or guaranteed optimal continuation.

Reuses the same authored right hairpin, URBAN road/environment assets and PSX pipeline as the overview study. Half-teal palette is read directly from tones.py: fog #0B172B, zenith #010408, ambient #5575A0; every streetlamp #F0C894, three-step pools. Native EEVEE one sample/filter zero, 1-bit HUD text, angular 50/50 navy badge, glow-only small bloom, final RGB555 + 4x4 Bayer, exact nearest upscale. No CRT pass.

This remains Blender/PIL mockup work, not native Godot or an implemented mirror feature. Native stills do not establish dynamic readability, final HUD size, performance cost, physical camera calibration or any gameplay threshold. Original overview remains in its parent folder as superseded work; this folder is the corrected chase test.

All work stays in this network-box folder. No repository edits, commits, pushes or personal-computer access.
