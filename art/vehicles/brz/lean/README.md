# BRZ (2nd-gen coupe, approved pass-4 shape, blue), LEAN build: 2,000-triangle cap

**Status: first lean version, for review.** **1,999 triangles** total. Detail lives in a 1024² baked body texture and
the existing 256² parts/wheel atlas. The approved pass-4 build (`../brz_lowpoly.*`, `../build_brz*.py`, `../renders/`,
4,079 tris without FX quads) is untouched. Everything here is written to `lean/`, plus two new helper scripts:
`../bp/bpcompare_lean.py` and `../bp/deliver_lean.py`.

## Reproduce
```
python3 make_lean.py        # from art/vehicles/brz
```
It runs these steps in order:
* `blender -b -P build_brz_lean.py -- --render`: geometry, rig, 9-pose clearance, UV, colour + AO bake, materials,
  `.blend` / `.glb` and raw renders. It opens `brz_lowpoly.blend` read-only and never saves over it.
* `bp/bpcompare_lean.py` (env `BRZ_TRIS` / `BRZ_IOU` / `BRZ_OD`): the pass-4 IoU gate (`bpcompare.py`) pointed at the
  lean tris.
* `bp/deliver_lean.py`: the review sheets in `lean/renders/`.

## Shape
* The shape is the approved pass-4 `parts/brz_geo.py`, using the same gated `BRZ_REAR_TWEAK` as `build_brz_detail.py`.
* Lower body: 9 of the 12 half-section points (`SUB = 0,1,3,4,5,6,7,9,11`, which keeps the fender ridge and hood edge)
  on 36 stations:
  * nose and tail dense, for the plan corners and ducktail
  * 7 per arch
  * mid-body about 25 cm apart
* The arch-lift code is the approved one. No smoothing or re-fitting pass is run, so the flanks keep the approved,
  non-wavy sections.
* Wheel wells: the bottom of the body no longer spans across the car at arch height. Inside each arch it runs:
  1. outer lip
  2. well roof (`R_WELL` .395 about the hub, inboard of the lip)
  3. a wall inboard of the tyre
  4. down to the floor

  The 7-segment liners close the arch tunnels.
* Greenhouse: 4 of the 6 pass-4 greenhouse rings (base, belt/glass bottom, glass top, roof edge), so the DLO lines are
  exactly the approved ones. Also the full pass-4 roof grid and a 3-tri shark fin.
* Glass is opaque, dark and cool-tinted, with no interior. It is a separate material and the same faces as pass 4.

## Where the triangles go (`tri_count.txt`)
| part | tris |
|---|---|
| lower body loft (incl. wheel-well floors) | 1,364 |
| greenhouse (glass + roof + fin) | 243 |
| mirrors (2 × 12) | 24 |
| arch tunnel + inner wall liners (4 × 20, 7-segment tunnel) | 80 |
| headlamp molding (2 × 10-corner surround: raised lip + dark inner wall) | 80 |
| **mono BRZ_Body** | **1,791** |
| wheels, 10-sided, inscribed (rim and sidewall painted) | 144 |
| suspension: strut + lower arm per corner | 64 |
| **total** | **1,999** |

## IoU (pass-4 gate `bpcompare`, blueprint frame; side/top ≥ .95, front/rear ≥ .92)
| view | lean | approved pass 4 |
|---|---|---|
| side | **.971** | .965 |
| top | .980 | .982 |
| front | .948 | .945 |
| rear | .932 | .928 |

All four views pass. Overlays are in `renders/raw/bpiou_*.png` (grey = both, blue = blueprint only, red = model only).

## Headlamp molding (light)
A thin molded surround around each painted headlamp, so the lens reads as set into the body. This is a post-step on
the finished lean (`make_lean.py`); nothing else in the model or the baked texture changes.
* **Outline:** `lean_common/lamps/molding_view.py` renders an unlit (albedo-only) 3/4 ortho close-up of the left lamp.
  `molding_outline.py` then takes everything that isn't body paint at the lamp, fills holes, and simplifies it to
  10 corners (convex hull, which bridges the chrome-texel notch on the top edge).
  The baked lamp art comes from the approved model, which was fitted to the blueprint.
* **Surround** (`molding_ring.py`), ray-cast onto the body along the same view and mirrored for the right lamp:
  * An outer edge 10 mm outside the outline, on the body (paint texel).
  * A lip 6 mm proud at the outline (paint texel).
  * An inner wall back down to the body 3 mm inside (darkest housing texel).
  * 2 bands × 10 corners × 2 tris per lamp = 80 tris, joined into `BRZ_Body`.
* **Checks:** the 9-pose clearance and IoU were re-run and are unchanged. The `.glb` was re-exported.
  `molding.json` records the outline and UVs.

## Texture and materials
* `tex/brz_body.png` (1024²): a Cycles diffuse-colour bake (selected-to-active) from the approved vector-painted
  pass-4 meshes onto the lean UVs, with baked AO mixed at .30. Converted to sRGB, then quantised to RGB555 with a 4×4
  Bayer dither.
  * Bake sources: BRZ_Body, Lamps, Under, Exhausts, and Parts with its wheels removed, so the wheels don't print onto
    the arch lips.
  * The approved blue comes straight from the bake.
* `tex/brz_wheel_atlas.png`: the approved 256² atlas, unchanged. It is already brand-free:
  * "KESTREL" badge / chevron
  * "VORTA APEX-R" tyres
  * "MIDNIGHT APEX / KS 27-04" plate
* Materials use the shared PSX fake-shine shader (`art/vehicles/wrx_sti/parts/psx_mat.py`, env ≤ .45). The .glb gets
  Principled materials with the same textures.

## Rig (Godot VehicleBody3D / VehicleWheel3D)
```
BRZ-vehicle                 root, ground, mid-wheelbase                       -> VehicleBody3D
 ├─ BRZ_Body                ONE mesh, origin = COM estimate at ride height
 ├─ Hub_FL-wheel …          empty at the static hub                            -> VehicleWheel3D
 │   └─ Steer_FL / FR       front: rotates about the vertical through the hub, ±30°
 │       └─ BRZ_Wheel_FL    10-sided, origin = hub, spins about the axle
 └─ Susp_FL …               empty at the static hub: follows hub position + steer only, never spin
     └─ BRZ_Susp_FL         strut + lower arm (16 tris)
```
| | front | rear |
|---|---|---|
| hub (glTF x, y, z) | ±.760, .316, +1.2875 | ±.775, .316, −1.2875 |
| tyre radius / width | .316 / .215 | same |
| travel (clearance-tested) | +45 mm bump / −50 mm droop | same |
| steer lock | ±30° | – |

* Body origin (COM estimate, 53 % front): glTF (0, .46, +.077), i.e. 7.7 cm ahead of mid-wheelbase, 0.46 m up.
  Ground is at y 0, at the pass-4 ride height.
* **Clearance:** 9 poses (lock −30/0/+30 × bump/static/droop), every corner, BVH tyre vs mono body: **all clear**.
  * The tightest vertex gap is 16 mm (FL, straight + full bump).
  * A finer surface sample shows the closest approach is about 4 mm, at the outer arch lip at full lock + full bump.
  * Report: `bp/clearance.json`.

## Godot 4 setup (strut follower)
The .glb uses Godot axes: +Y up, **+Z forward, +X = car left**, ground at y 0. No node carries a rotation or scale.
1. Import `<car>_lean.glb`. On the root `<CAR>-vehicle`, change the type to **VehicleBody3D** (or re-parent the
   children under a new VehicleBody3D). `<CAR>_Body` stays a mesh child. Its origin is the COM estimate, so set
   `center_of_mass_mode = Custom` and use the `<CAR>_Body` position as `center_of_mass`.
2. On each `Hub_XX-wheel`, change the type to **VehicleWheel3D** and keep its transform (the static hub centre). Set
   `wheel_radius`, `suspension_travel` and `use_as_steering` (front) / `use_as_traction` as in the table above.
   VehicleWheel3D moves, steers **and spins** its children, so `Steer_XX` → `<CAR>_Wheel_XX` stay under it.
3. Each `Susp_XX` is a **Node3D sibling** of the wheels (a child of the VehicleBody3D) and holds `<CAR>_Susp_XX`
   (strut + lower arm, 16 tris). Attach `godot/susp_follow.gd`, set `wheel` to the matching VehicleWheel3D, and set
   `steers = true` on FL/FR. Each physics frame the script copies the wheel's position (suspension travel) and its
   steering angle about +Y, never the spin.
4. Steering: set `VehicleBody3D.steering` within ±0.524 rad (±30°). The well clearance was tested only to that lock.

## Files
* `brz_lean.blend`: Blender source, textures packed. The blueprint planes are kept hidden.
* `brz_lean.glb`: Godot import.
* `tri_count.txt`, `bp/clearance.json`, `bp/iou_bpframe.json`, `bp/tris_carframe.npy`
* `renders/`:
  * `brz_lean_orthos_800.jpg`: textured orthos + yellow blueprint silhouette + IoU
  * `brz_lean_front34_800.jpg`, `brz_lean_rear34_800.jpg`, and `_ref.png` (1280×896 review frames)
  * `brz_lean_raking_side_800.jpg`
  * `brz_lean_vs_old_800.jpg`
  * `brz_lean_texture_800.jpg`
* `godot/susp_follow.gd`

## Known gaps
* Pass 4's FX quads (blob shadow, lamp glow) are not carried over.
* The UV seams have not been reviewed in the 640×480 game frame.
