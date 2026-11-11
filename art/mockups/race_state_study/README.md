# Race-state visual study — four conditions

## Deliverables
- `01_ahead_pressure.png`: S2000 ahead, Miata close behind.
- `02_ahead_room.png`: S2000 ahead, Miata farther behind.
- `03_close_behind.png`: S2000 close behind Miata.
- `04_far_behind.png`: S2000 far behind Miata.
- `four_panel_race_state_study.png`: 2x2 comparison, explicitly from the rival S2000's perspective, with physical-technique annotations and one overhead design diagram per condition.

The four gameplay frames are native 640x480 in `raw/*_native.png`, upscaled exactly 2x nearest to 1280x960. The annotated sheet is 2620x2860. There is no extra CRT pass.

## Controlled variables / roles
PLAYER is always the existing yellow Miata ND (`assets/cars/mx5/car_mx5.glb`). RIVAL is always the existing red S2000 (`assets/cars/s2000/car_s2000.glb`). These shells identify characters; no shell-dependent performance claim is implied.

The rival is held at the SAME world position (-3.3, -26) and the SAME orientation in all four images, not merely in the same lane. Camera, road, corner, lamps and all environment objects are identical. Only the Miata moves longitudinally. Both cars always travel +Y, before turn-in. S2000 stays cleanly in the outside-left lane; Miata stays in the centre lane. Neither car has pitch, yaw, braking, weaving or turn-in tells added.

Staging, in metres along the authored approach:
| condition | S2000 Y | Miata Y | centre separation |
|---|---:|---:|---:|
| ahead / pressure | -26 | -32 | 6 |
| ahead / room | -26 | -44 | 18 |
| close behind | -26 | -20 | 6 |
| far behind | -26 | -8 | 18 |
These are illustrative staging distances only, NOT gameplay thresholds, probabilities, optimality rules or balance numbers. The gap is centre-to-centre, not bumper clearance. Staging holds the rival's distance to turn-in constant to avoid adding another confounding variable.

## Current mechanics respected
- Track/corner authored and fixed; study is the selection-start snapshot.
- Full three-card player line is locked on the straight before playback, as stated on the sheet. A finished player selection UI is not proposed here.
- Rival Entry is the same visible Outside = ATK in every image. No improper placement or Entry bluff in this controlled study.
- No rival Apex/Exit tell, future card, true projected racing line, hidden/reactive badge, intent strip, portrait, hand count, motion tell or bluff layer appears in gameplay.
- External annotations are expressly titled `ILLUSTRATIVE CONTINUATION — NOT A STANCE TABLE`.
- External diagrams are marked `DESIGN DIAGRAM / NOT HUD`, with common outside Entry, a dashed candidate S2000 route and the Miata's schematic position at selection. Those paths are hypothetical continuations, NOT a revealed true line.
- No specialization-specific habit table is assumed or asserted. Future stance mapping remains unresolved. No future ATK/DEF/STY assignment is made.

## Physical continuation examples (not guaranteed best choices)
1. Tighter apex radius at an exit-speed cost under pressure.
2. Delayed/late apex to open and straighten the exit with space behind.
3. Conditional delayed apex/crossover behind the Miata only if it runs wide after apex; no promised opening or pass.
4. Smooth unforced arc and clean exit to preserve momentum instead of forcing a low-prospect pass from farther back.
All diagram paths begin with the SAME outside approach. They diverge only at/after turn-in. They do not move the rival into the inside lane on the planning straight. The diagrams are schematic physical examples, not vehicle dynamics simulations or tuned stance tables.

## Art implementation
Reused the `pattern_read` / `build_v5` asset-import and rendering pipeline, downloaded URBAN roads, barriers, buildings, tree packs, vertex-painted unlit lighting/fog, fake car shine, blob contacts and ordinary tail lamps. A second matching URBAN corner tile creates the right-hand 180-degree hairpin rather than keeping the old 90-degree placeholder. Same orthographic overhead-oblique camera in all four to keep near/far gaps directly comparable. Approach has clean three-lane markings.

`blend50` is read directly from existing tone presets: deep navy-teal fog #0B172B, zenith #010408, cool ambient #5575A0 and all lamps #F0C894. Three-step pools; glow-only bloom radius 3 with weight .22. HUD is 1-bit text and angular 50/50 navy panels at 640x480; final RGB555 + 4x4 Bayer and nearest upscale. HUD contains only HAIRPIN R and identity/Entry tags. Ordinary tail-light brightness is constant, not a braking tell.

## Verification / limitations
Checked all four final frames, sheet and design diagrams using image reads. Programmatic verification checks dimensions, exact nearest repetition, RGB555 levels, fixed rival position, role ordering, visible screen positions and 6/18 m separations. Results in verification.json.

This is a Blender/PIL design study, not native Godot or implemented gameplay. Wide overhead framing deliberately sacrifices car detail to show both cars and the full lead/gap relationship consistently. Labels make car identity explicit. The return carriageway clips at the right image edge, but the U-turn and direction are visible. Reused scenery has placeholder parking texture/infield treatment, not a finished circuit-art proposal. No timing, passing probability, physical optimum or specialization habit has been established by these stills.

## Rebuild
From this directory:
`TONE=blend50 /workspace/tools/blender-4.2.3-linux-x64/blender -b -t 6 -P build_study.py -- entry`
`python3 compose_study.py`
`python3 verify_study.py`

All generated work stays under `/workspace/mockups/race_state_study/`. Repository assets/docs were read only; no edits, commits, pushes or personal-computer access.
