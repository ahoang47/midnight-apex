# Subaru Impreza WRX STI (GDB "bugeye", 2001-02) — grey clay, blueprint-only

> **Game version (2026-10-31):** the lean build in [`lean/`](lean/README.md), **1,966 tris** (≤ 2,000 cap incl. wheels, struts, FX), hub-pivoted wheels + strut rig, headlamp light molding. Engine copy: `assets/cars/wrx_sti/`. This page documents the pass-2 clay trace the lean build is made from.

**Status: clay for shape sign-off.** It has no texture and no detail pass yet. The gold wheels, paint, badges and
lamp textures come after sign-off.

## Reproduce (headless)
```
python3 make_all.py
```
`make_all.py` runs `bp/extract.py`, then `bp/classify_sheet.py`, then `bp/fair.py` (pass 2 curve fairing), then
`blender -b -P build_wrx.py -- --render`, then `bp/bpcompare.py`, `bp/feature_overlay.py`, `bp/deliver.py` and
`bp/keylines.py`. It uses Blender 4.2 (`blender` on PATH, or set `BLENDER=/path/to/blender`). Blender's Python has no scipy, so
the build side (`parts/`) uses numpy only. The dev loop `./run_gate.sh` runs the build and the IoU gate without renders.

## Source
* **Blueprint:** `ref/wrx_blueprint.jpg`, the-blueprints.com "Subaru Impreza WRX (2001)", 1:25.
  * It is 1280×906 px, not 1024×724 as first stated.
  * Scale is S = 4.405 m / 770 px = 5.721 mm/px.
  * The sheet is coloured: blue paint, light glass at RGB ≈ 233,237,238, red lamps, and a white/grey watermark.
* **No photos.** Every body line is a traced blueprint curve (`bp/curves.json`).
* **Frames:**
  * side and top: x from the wheel contact patches, z from the tyre bottoms
  * front and rear: centred on the paint, same ground
  * top view: nose left; the image top is the car's right
  * front view: the car's left is on the image right
* **Line classes** (`renders/wrx_bp_line_classification_800.jpg`):
  * SIL: car-mask boundary
  * GLASS: boundary of the light regions inside the car mask
  * FEAT: dark strokes inside the paint, plus lamp edges
  * TYRE

## Model
| object | what | from |
|---|---|---|
| WRX_Body | lower loft. Sections = front/rear-view envelope × plan half-width; top = hood line / belt / deck; arches = circle fits | blueprint |
| WRX_Cabin | greenhouse loft: belt → DLO bottom → DLO top → roof rail → crown (side silhouette top) | blueprint |
| WRX_Decals | headlamps, fogs, side lenses, tail lamps, lower intake. Each is the convex hull of a blueprint mask component, ray-cast onto the body | blueprint |
| WRX_Mirror_L/R, WRX_Under, WRX_Liner_* | mirrors (black), hidden underbody, wheel-well liners | blueprint / sized for the rig |
| WRX_Scoop, WRX_LipSpoiler | the base WRX scoop and boot spoiler as drawn. Collection WRX_base_parts, **hidden** in the STI build | blueprint |
| STI_Scoop, STI_Wing, STI_FrontLip | STI stock parts, each ≤ 300 tris | **estimated** (see keyline_table.md) |

**Pass 2: one mono body mesh.** After the clearance check, every body piece in the table except the hidden base-WRX
parts and the wheels is joined into `WRX_Body`: cabin, decals, mirrors, liners, underbody and the STI scoop, wing and lip.
The per-part tri counts and the triangle soup `bp/tris_*.npy` are written before the join, so the IoU sets can still
tell the aero triangles apart. The four wheels stay separate objects under the Hub/Steer pivots.
| WRX_Wheel_* | STI 225/45R17: OD .634, W .225, rim .432 | sheet ~.63 OD |

Triangle counts are in `tri_count.txt`. The IoU results are in `bp/iou_bpframe.json`. The sets are:
* `sti_aero_masked` (the gate): the exported mono car, with the aero region (scoop, wing/spoiler and lip boxes)
  masked out of both the blueprint and the clay
* `sti_mono`: the same car, unmasked
* `no_aero`: the pass-1 gate, with the aero parts dropped
* `wrx_base`: the blueprint's own scoop and spoiler Line-by-line numbers are in `keyline_table.md`.

## Suspension + steering rig (Godot VehicleBody3D / VehicleWheel3D compatible)
```
WRX-vehicle            empty, ground origin, mid-wheelbase      -> Godot VehicleBody3D (import hint "-vehicle")
 ├─ WRX_Body           ONE mono mesh: body, cabin, aero, mirrors, liners (Blender-only roll / pitch / heave poses)
 └─ Hub_FL-wheel …     empty at the static hub centre            -> Godot VehicleWheel3D (import hint "-wheel")
     └─ Steer_FL/FR    front only: rotates about local Z (vertical axis through the hub). Blender authoring pivot
         └─ WRX_Wheel_FL  mesh, origin = hub centre, axle = local X (Godot: spins about the wheel node's X)
```
**What Godot drives:** the VehicleWheel3D node's transform. That covers:
* suspension travel along the wheel's down axis, from `wheel_rest_length` and `suspension_travel`
* steering, as a rotation about the node's up axis, on wheels with `use_as_steering`, from `VehicleBody3D.steering`
* wheel spin

**What the mesh needs:**
* The pivot is at the hub centre.
* The axle runs along local X.
* The mesh carries no baked steer or spin.

The `Steer_*` empties are identity at rest, so they import as plain Node3Ds and do nothing in Godot. They exist so
the Blender pose sheet can show lock without touching the hub. In Godot the body roll comes from physics. In Blender
the wheels stay planted and `WRX_Body` rotates, which is the same relative motion.

Suggested Godot values (estimates):
* `wheel_radius` 0.317
* `suspension_travel` 0.145 (+0.065 bump / −0.080 droop)
* `wheel_rest_length` ≈ 0.12
* `steering` ±0.524 rad (±30°)

**Lock ±30° (brief value).** The real GD steers about 33° inside and 28° outside, which gives a ~10.6 m kerb circle,
so 30° is the mean. The 30° is used symmetrically, with no Ackermann.

**Clearance** (`bp/clearance.json`, `renders/wrx_clay_steer_clearance_800.jpg`):
* Every corner is posed at lock {−30, 0, +30} × travel {+bump, 0, −droop}.
* Each posed tyre is BVH-overlap tested against the body, cabin, liners, underbody, mirrors and STI lip.
* Result: no interference. The tightest front gap is ~22 mm, to the FR liner at −30° + full bump.
* The liners are arcs of radius .415 (front) and .400 (rear) about the static hub, with inner walls at y .465 / .590.
  They are sized for tyre-corner reach at lock (.33 m) + bump (.065) + 15–20 mm.
* At full lock the front corner of the tyre leaves the arch opening outboard, as on the real car. The check is that
  it never passes through a panel or liner.

**Pose sheet:** `renders/wrx_clay_suspension_800.jpg` shows these poses:
* static
* full bump
* full droop
* roll right and roll left
* dive and squat
* **full left lock + roll** and **full right lock + roll**

The relative wheel travel per corner is printed in each cell.

### Retrofitting the S2000 and BRZ the same way
1. **Split the wheels.** Give each wheel mesh its origin at the hub centre, with the axle along local X. Both builds
   currently place wheel vertices in world space at the hub.
2. **Add the hierarchy:** the root `<CAR>-vehicle`, plus `Hub_XX-wheel` empties at the static hubs and `Steer_FL/FR`
   empties. Parent the body and its parts to `<CAR>_Body` instead of the scene root.
3. **Replace the underbody / wheel-well boxes.**
   * BRZ `build_under` has 0.72 × 1.6 m boxes at each axle that a steered tyre intersects. Replace them with arch-tunnel
     liners sized from that car's arch radius, tyre OD/width and track.
   * Re-check the inner liner wall: track/2 − (r·sin30 + w/2·cos30) − ~20 mm.
4. **Check arch-lip clearance.** Lip-to-tyre gap ≥ bump travel, or set bump to the measured gap.
   * BRZ: arch r .360/.368 vs tyre OD .632.
   * S2000: measure from its blueprint.
5. **Reuse the shared code.**
   * Copy `parts/clearance.py` (it only needs the object names) and the pose / clearance blocks of `parts/render_wrx.py`.
   * Add `bp/clearance.json` + the two sheets to their deliverables.
   * In the BRZ detail build, the atlas wheel UVs must survive the origin move. Apply the inverse offset to the mesh,
     not the UVs.

## Estimated (not on the sheet), also listed in keyline_table.md
* STI scoop, wing and front lip dimensions.
* Tyre size: STI spec, not traced.
* Lip-spoiler span ±.66, read off the rear-view band.
* Deck height under the spoiler.
* Suspension travel and lock.
* Top-view half-width clamped to .872. The top view reads .90 at the flares; the front/rear views and the sheet
  (1730) read .865–.87.
* Wheelbase kept at the traced 2.494. The sheet says 2.525, so the drawing is 1.2 % short.
* Roof height. The drawing is ~1.465, against 1.440 on the sheet.

## Pass 2 (clay): side waviness fix
**Cause.** Pass 1 lofted straight from the raw per-column traces, so blueprint-pixel noise became surface noise:
* The plan half-width W(x) jumped by up to 5 cm between neighbouring stations, from 0.855 at x .70 to 0.906 at .55
  to 0.878 at .45. The cause was mirror bleed in the top view plus 1 px (5.7 mm) tracing noise.
* The sill line jumped 3 cm (.166 to .200) near the front arch, where the tyre bridge ended.
* The `min(W, .872)` clamp put a slope kink into every section where W crossed it.
* The crown changed in steps at the windshield and rear-glass bases, which kinked the shoulder line.
* The stations were unevenly spaced (2.7 to 17 cm), so the facets varied in length and the smooth-shading banding
  varied with them.

**Changes.**
* `bp/fair.py` fairs every traced curve:
  * The mirror zone is bridged, the curve is low-passed (stronger on the flanks than at the nose and tail), then refit
    with a smoothing cubic spline. W now has about 0.5 mm/m² second difference along the doors, with 5.4 mm rms residual
    to the trace.
  * The sill is one quadratic between the arches.
  * The hood is a quadratic fit.
  * The front and rear envelopes are low-passed in z.
* The hood, belt and deck are one faired line (4 cm gaussian). The crown ramps instead of stepping, and the W clamp
  is a soft (C1) clamp.
* Every station has the same 11-point section. Stations are evenly spaced, ≤ 10 cm apart and equal within each span
  between the arch, windshield and rear-glass anchors. The nose and tail use an even 5.5 cm base plus the
  lamp-face stations.
* The cabin has its own even stations, ≤ 11 cm apart, between the pillar edges.
* **Roof-rail band above the rear door:** in pass 1, the rear-door sash corner was smoothed into the DLO-top line and
  dragged it down. The DLO top is now a quadratic fitted only to the door-glass interiors.
* **Nose and tail:** the section corners above and below the widest point are pulled in toward the tip, which keeps W
  and the IoU. The tail gets the upper corner only.
* Shading QC is written into `tri_count.txt`:
  * 0 flipped and 0 degenerate loft quads.
  * The non-planar quads (> 5 % of the diagonal) are only at the nose/headlamp corner and the arch-lip walls, none on
    the flanks.
* Visual checks:
  * `renders/wrx_clay_raking_side_800.jpg`: Cycles sun at 7° from ahead and from behind
  * `renders/wrx_clay_zebra_800.jpg`: reflection-stripe matcap, side, top and 3/4

**Still rough (detail pass):** the lamp decals still look faceted on the curved nose and tail corners. The front
bumper face has a few twisted quads at the headlamp corners.
