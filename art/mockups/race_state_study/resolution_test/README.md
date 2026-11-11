# Resolution experiment ONLY — genuine 640 vs genuine 960

NOT a change to Midnight Apex's approved reference resolution. Static proposed UI and mirror, NOT an implemented engine feature. No future rival stance reveals, specialization assumptions, probabilities, thresholds or balance rules are introduced.

## Deliverables / where to look
- `display/`: twenty 1920x1440 gameplay PNGs: five cases x two native resolutions x CLEAN / CRT. Exact links in `manifest.json`.
- `native/`: ten original RGB555/Bayer gameplay composites plus ten standalone native mirror inserts.
- `raw/`: twenty genuine Blender source renders: forward and rear at each native resolution, BEFORE HUD/quantization.
- `comparisons/<case>_resolution_comparison.png`: five 2640x1560 sheets. Columns CLEAN640 / CRT640 / CLEAN960 / CRT960. Reduced full-game previews provide context only; do NOT judge CRT mask there. The 576x192 mirror and 640x320 main-view crops are copied from final display files at EXACTLY 1:1, not resampled.
- `comparisons/<case>_mirror_1to1_stack.png`: convenient 576-pixel-wide vertical stacks of all four actual display-space mirror crops. View at 100%; chat previews may resize images. `<case>_main_1to1_stack.png` provides corresponding main-view details.
- `comparisons/verification_genuine_960_detail.png`: expressly labelled 8x QA enlargement comparing actual high-resolution samples against a nearest-enlarged 640 source. This enlargement is NEVER used in gameplay.
- Scripts, shader/preset, source hashes, camera/staging metadata, observed findings and verification are included. Referenced model/asset-pack/font dependencies remain at their existing box paths; the archive does not redistribute entire asset packs.

## Exactly controlled scene
Original entry_matrix yellow Miata ND = PLAYER, red S2000 = RIVAL. Player is always Center `(0,-28,.16)`. Both cars retain +Y forward heading, root XYZ Euler `(0,0,pi)`. Only these five previously staged cases are rendered, not the full twelve:

| Case, from RIVAL perspective | Rival root XYZ | Truthful Entry |
|---|---|---|
| Close trailing Center | (0,-34,.16) | Center / STY |
| Far trailing Outside | (-3.3,-46,.16) | Outside / ATK |
| Far trailing Center | (0,-46,.16) | Center / STY |
| Far trailing Inside | (3.3,-46,.16) | Inside / DEF |
| Ahead far Center | (0,-10,.16) | Center / STY |

6/18 m are longitudinal root-centre staging gaps only, NOT thresholds or Euclidean separation across lanes. No gaps, models, player geometry, headlamp spacing/size, body pitch, scene or camera are adjusted. Entry lanes are relative to the SAME RIGHT HAIRPIN, not a general fixed screen-left/right stance rule.

Main camera: world `(1.4,-35.6,3.1)`, target `(3.6,-6,-.9)`, player-root offset in world/travel-aligned axes `(1.4,-7.6,2.94)`. 25 mm lens / 36 mm horizontal sensor, H FOV 71.507775 degrees, effective V FOV 56.738093 degrees.

Rear camera: world `(0,-28,1.6)`, target `(0,-60,-2.2)`, 14 mm lens / 36 mm sensor, H FOV 104.250033 degrees. Actual 192x64 or 288x96 render, ONE horizontal reflection, not a relocated overlay car. Same 3:1 framing and normalized footprint. Insert rectangle: native640 `(224,16)-(416,80)`, native960 `(336,24)-(624,120)`, final display BOTH `(672,48)-(1248,240)`. Own roof silhouette and genuine occlusion remain.

All main/rear camera matrices, lens/sensor settings, car locations, source dimensions and per-vertex normalized projections are verified against original entry_matrix. All FIVE freshly rendered/composed 640 natives are PIXEL-IDENTICAL to their existing entry_matrix counterparts.

## Art / true native resolution
Blender 4.2.3 EEVEE Next. Actual scene rasterization 640x480 AND 960x720; mirrors actual 192x64 AND 288x96. Resolution percentage 100, render samples 1, filter size 0: no AA accumulation. Original PSX painted low-poly meshes, faked shine, asset-pack environment, nearest pack textures, Half Teal palette: fog #0B172B / zenith #010408 / ambient #5575A0; all street lamps pale sodium #F0C894. No added headlight bloom or geometry manipulation.

HUD is freshly vector-drawn at each target native size, with proportional newly rasterized 1-bit font sizes, 45-degree-cut navy panels, 50/50 transparency and stance colors unchanged. Scaling coordinates/fonts by 1.5 requires integer pixel rounding, not a new layout. The 960 HUD is NOT a resized 640 bitmap. Contents stay MID/STY unconfirmed, Apex/Exit NOT SET, full sample hand 2/2/2, 0 LOCKED and sample 04.8s timer. No rival future slots.

RGB555 + 4x4 Bayer is applied at each native resolution. CLEAN640 is exact 3x nearest; CLEAN960 exact 2x nearest: matching 1920x1440 display size. Dither grain is consequently finer in display space at 960. Native RGB555 is preserved before CRT; CRT output legitimately contains additional display-intensity levels and is not re-quantized.

## Real CRT processing / exact common settings
Unchanged upstream shader `/workspace/tools/crt/slang-shaders/crt/shaders/crt-easymode.slang` (GPL attribution retained), copied into `shader/`. Base upstream preset `crt/crt-easymode.slangp`; local restrained preset `crt_easymode_restrained.slangp`. Shader SHA256 and every parameter are in `crt_parameters.json`. No Pillow scanline/mask substitute: all ten CRT frames are actual librashader-cli OpenGL3 renders, three shader frames per image, input NATIVE composite -> output 1920x1440.

Same parameters for every case and BOTH resolutions:
```
SHARPNESS_H=.85; SHARPNESS_V=1
MASK_STRENGTH=.08; MASK_DOT_WIDTH=1; MASK_DOT_HEIGHT=1
MASK_STAGGER=0; MASK_SIZE=1
SCANLINE_STRENGTH=.15
SCANLINE_BEAM_WIDTH_MIN=1.5; SCANLINE_BEAM_WIDTH_MAX=1.5
SCANLINE_BRIGHT_MIN=.35; SCANLINE_BRIGHT_MAX=.65
SCANLINE_CUTOFF=1000
GAMMA_INPUT=2; GAMMA_OUTPUT=2
BRIGHT_BOOST=1.05; DILATION=0
```
Cutoff is explicitly 1000 so the scanline function runs at BOTH 480 and 720 source rows (the upstream default 400 would disable it). Same output mask pitch. Easymode's source-row cosine is sampled at different phases at 3x versus 2x; at exact 2x the vertical scanline alternation is much weaker. This is an integer-sampling consequence, not a missing CRT pass or separately tuned preset. Full-frame encoded RGB mean CRT/clean ratios are about 1.0004 (640) and 1.0053 (960): restrained processing preserves average encoded brightness to within ~0.6%. These are image measurements, not calibrated monitor luminance or readability scores.

## Actual native-pixel limitations
Whole-mesh PROJECTED extents below are before own-car occlusion, not guaranteed visible footprints. Divider figures project the real .11 m paint width at the rival's root Y; a dash may not occur exactly there and raster coverage/occlusion can still remove it.

| Case / view | 640 mesh pixels | 960 mesh pixels | Divider width pixels, 640 -> 960 |
|---|---|---|---|
| 03_close_behind_center (rear) | 27.5 x 20.9 | 41.2 x 31.4 | 1.34 -> 2.01 |
| 04_far_behind_outside (rear) | 9.4 x 5.7 | 14.2 x 8.6 | 0.46 -> 0.68 |
| 04_far_behind_center (rear) | 7.6 x 5.7 | 11.5 x 8.6 | 0.46 -> 0.68 |
| 04_far_behind_inside (rear) | 9.4 x 5.7 | 14.2 x 8.6 | 0.46 -> 0.68 |
| 02_ahead_room_center (forward) | 33.6 x 24.1 | 50.4 x 36.2 | 1.94 -> 2.91 |

- Close trailing Center: two headlamp clusters are separate at both resolutions; 960 gives their lens/body shape more samples. The forward view STILL only shows a clipped hood at the lower edge. Visible hood change bounds against the identical empty forward scene are `(2,459)-(208,480)` at640 and `(3,689)-(312,720)` at960. More pixels do not repair near-plane clipping or remove the roof obstruction in the mirror.
- Far trailing all three lanes: absent from forward view at BOTH resolutions. The mirror keeps distinct coarse lateral placements against reflected road context; 960 refines the rival/paint samples, but precise lamp-pair/tyre-in-lane judgments remain limited. At far distances the lane paint is still subpixel-width at these source resolutions. Do NOT read this as guaranteed Entry certainty.
- Far trailing Center specifically: the car is ABOVE the own-roof silhouette here, not roof-occluded. Its tiny footprint and faint road paint are the limiting issues in this exact setup; we did not erase roof geometry to make that true.
- Ahead far Center: center-lane body position is visible at both resolutions; 960 refines body silhouette, rear lamps and nearby road detail. Rear mirror correctly has no rival because the S2000 is ahead.
- Restrained CRT slightly softens/diffuses tiny lamp and lane edges and reduces hard-pixel contrast; it creates no new positional information. Clean960 remains beside CRT960 to expose that trade-off. The far pair remains small even when sharper than640.

These STILL images do NOT validate animated tell readability, motion stability, monitor behavior, player deductions or dynamic occlusion. Raising the reference resolution is NOT approved. No future Apex/Exit stance mapping or specialization table is implied.

## Reproduce on the box
From this directory, with existing referenced assets and installed tools:
```
TONE=blend50 /workspace/tools/blender-4.2.3-linux-x64/blender -b -t 6 -P build_resolution_test.py -- entry
python3 compose_resolution_test.py
bash run_resolution_crt.sh
python3 make_comparisons.py
python3 verify_resolution_test.py
```
Runner uses the installed crt micromamba environment and librashader-cli, matching `/workspace/mockups/crt/run_crt.sh`. Runtime version saved in `logs/librashader_version.txt`.

All ten native composites, all twenty final gameplay frames, five sheets and actual display-space mirror detail stacks were visually inspected with Read. Verification also checks actual native dimensions/render settings, differing high-frequency 960 samples (not an enlarged640 raster), original640 pixel identity, RGB555, exact integer upscales, invariant normalized projections, actual unchanged upstream shader and matching final dimensions.

All writes are under `/workspace/mockups/race_state_study/resolution_test/`. Existing entry_matrix and repository files are unchanged; no commits, pushes, personal-machine access or engine implementation.
