# S2000 (AP1-style roadster, soft top up), LEAN build: 2,000-triangle cap

**Status: first lean version, for review.** **1,916 triangles** total. Detail lives in a 1024² baked body texture and
a 256² parts/wheel atlas. The approved build (`../s2000_lowpoly.*`, `../build_s2000.py`, `../renders/`, 4,354 tris)
is untouched. Everything here is written to `lean/`.

## Reproduce
```
python3 make_lean.py        # from art/vehicles/s2000
```
It runs these steps in order:
* `tex/debrand_atlas.py`: copies the approved atlas with the real brands painted out (see below).
* `blender -b -P build_s2000_lean.py -- --render`: geometry, rig, 9-pose clearance, UV, colour + AO bake, materials,
  `.blend` / `.glb` and raw renders.
* `S2K_RD=lean/renders/raw/ bp/compare_lean.py`: IoU against the blueprint, in the approved compare frames.
* `bp/deliver_lean.py`: the review sheets in `lean/renders/`.

## Shape
The shape is the approved section functions from `build_s2000.py`, sampled on fewer points (9 of 12 per half-section)
and fewer, evenly spread stations:
* the nose and tail are dense, for the plan corners
* the arch stations sit at ±.378 / ±.33 / ±.20 / 0 about each axle
* mid-body stations are about 20 cm apart

No smoothing or re-fitting pass is run, so the flanks keep the approved, non-wavy sections. The soft top + windscreen
strip is ray-fitted onto the approved SoftTop / Windshield / WindshieldFrame and seated on the body at the belt and
deck. Glass is opaque and cool-tinted, with no interior.

## Where the triangles go (`tri_count.txt`)
| part | tris |
|---|---|
| lower body loft (+ cockpit lid, wells raised to R .405) | 1,244 |
| soft top + windscreen strip | 264 |
| mirrors (2 × 12) | 24 |
| arch tunnel + inner wall liners (4 × 20, 7-segment tunnel) | 80 |
| headlamp molding (2 × 12-corner surround: raised lip + dark inner wall) | 96 |
| **mono S2000_Body** | **1,708** |
| wheels, 10-sided, inscribed (rim and sidewall painted) | 144 |
| suspension: strut + lower arm per corner | 64 |
| **total** | **1,916** |

## IoU (blueprint gate: side/top ≥ .95, front/rear ≥ .92)
| view | lean | approved build |
|---|---|---|
| side | **.952** | .961 |
| top | .992 | .992 |
| front | .930 | .925 |
| rear | .951 | .944 |

The side view passes, but narrowly. Most of the loss comes from the 10-sided wheels: they are inscribed in the tyre
circle so they clear the wells, which shaves the wheel arcs off the side silhouette.

## Headlamp molding (light)
A thin molded surround around each painted headlamp, so the lens reads as set into the body. This is a post-step on
the finished lean (`make_lean.py`); nothing else in the model or the baked texture changes.
* **Outline:** `lean_common/lamps/molding_view.py` renders an unlit (albedo-only) 3/4 ortho close-up of the left lamp.
  `molding_outline.py` then takes everything that isn't body paint at the lamp, fills holes, and simplifies it to
  12 corners.
  The baked lamp art comes from the approved model, which was fitted to the blueprint.
* **Surround** (`molding_ring.py`), ray-cast onto the body along the same view and mirrored for the right lamp:
  * An outer edge 10 mm outside the outline, on the body (paint texel).
  * A lip 6 mm proud at the outline (paint texel).
  * An inner wall back down to the body 3 mm inside (darkest housing texel).
  * 2 bands × 12 corners × 2 tris per lamp = 96 tris, joined into `S2000_Body`.
* **Checks:** the 9-pose clearance and IoU were re-run and are unchanged. The `.glb` was re-exported.
  `molding.json` records the outline and UVs.

## Texture and materials
* `tex/s2000_body.png` (1024²): a Cycles diffuse-colour bake (selected-to-active) from the approved vector-painted
  meshes (Body, SoftTop, Windshield, WindshieldFrame, Lights, Trim) onto the lean UVs, with baked AO mixed at .30.
  Converted to sRGB, then quantised to RGB555 with a 4×4 Bayer dither. No panel lines were traced from raster.
* `tex/s2000_atlas_lean.png` (256²): the approved parts/wheel atlas with **every real brand removed** (art rule:
  made-up names only):
  * H emblem → Midnight Apex chevron
  * "Honda S 20-00" plate → "APEX / MA 2002"
  * "S2000" boot badge → "RS-20"
  * wheel centre cap H → plain cap
  * "POTENZA S-02" → "KAIDO K-2" (205/55R16 kept)

  The approved build's atlas still carries the real brands; that file is left as it was.
* Materials use the shared PSX fake-shine shader (`art/vehicles/wrx_sti/parts/psx_mat.py`: ambient + key + Blinn + painted
  env × Fresnel, env ≤ .45). The .glb gets Principled materials with the same textures.
* The tyre sidewall lettering reads correctly from outside on both sides (fixed in `lean_common/leanlib.wheel`).

## Rig (Godot VehicleBody3D / VehicleWheel3D)
```
S2000-vehicle               root, ground, blueprint car origin                -> VehicleBody3D
 ├─ S2000_Body              ONE mesh, origin = COM estimate at ride height
 ├─ Hub_FL-wheel …          empty at the static hub                            -> VehicleWheel3D
 │   └─ Steer_FL / FR       front: rotates about the vertical through the hub, ±30°
 │       └─ S2000_Wheel_FL  10-sided, origin = hub, spins about the axle
 └─ Susp_FL …               empty at the static hub: follows hub position + steer only, never spin
     └─ S2000_Susp_FL       strut + lower arm (16 tris)
```
| | front | rear |
|---|---|---|
| hub (glTF x, y, z) | ±.720, .315, +1.265 | ±.755, .315, −1.148 |
| tyre radius / width | .315 / .215 | same |
| travel (clearance-tested) | **+40 mm bump** / −50 mm droop | same |
| steer lock | ±30° | – |

* Body origin (COM estimate, 50/50 weight split): glTF (0, .46, +.0585), i.e. exactly mid-wheelbase (the root /
  blueprint origin is 5.85 cm behind it), 0.46 m up.
  Ground is at y 0. Ride height is the approved build's (blueprint) stance.
* **Bump is +40 mm, not the art doc's 45–50 mm.** The blueprint arch is only about 5 cm above the tyre, so more bump
  would need wider arches than the blueprint (an IoU / shape change). The well roofs are raised inboard of the outer lip
  (`R_WELL` .405), and the 7-segment liners keep their chord sag outside the tyre path.
* **Clearance:** 9 poses (lock −30/0/+30 × bump/static/droop), every corner, BVH tyre vs mono body: **all clear**.
  The tightest gap is 3.4 mm (FR, +30° + full bump). Report: `bp/clearance.json`.
* Blender source (`s2000_lean.blend`) is X-forward like the approved build. The .glb export re-expresses the rig in
  the same Godot axes as the WRX/BRZ leans, without rotating any node (`leanlib.conjugate_rig`).

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
* `s2000_lean.blend`: Blender source, textures packed. The blueprint planes are kept hidden.
* `s2000_lean.glb`: Godot import.
* `tri_count.txt`, `bp/clearance.json`, `renders/raw/iou.json`
* `renders/`:
  * `s2000_lean_orthos_800.jpg`: textured orthos + yellow blueprint silhouette + IoU
  * `s2000_lean_front34_800.jpg`, `s2000_lean_rear34_800.jpg`, and `_ref.png` (1280×896 review frames)
  * `s2000_lean_raking_side_800.jpg`
  * `s2000_lean_vs_old_800.jpg`
  * `s2000_lean_texture_800.jpg`
* `godot/susp_follow.gd`

## Known gaps
* There are no lamp glow sprites or blob shadow yet.
* The UV seams have not been reviewed in the 640×480 game frame.
