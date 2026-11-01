# WRX STI (GDB 2001-02), LEAN build: 2,000-triangle cap

**Status: first lean version, for review.**
* The body, aero, mirrors, liners, floor, head lamp pockets, fog lamp lenses, suspension and wheels total
  **1,962 triangles**, plus 4 for the optional head lamp glow quads (**1,966** with them).
* Detail lives in a painted 1024² body texture and a 256² wheel atlas.
* The pass-2 clay (`../build_wrx.py`, `../wrx_clay.*`, `../renders/`) is untouched for comparison.

## Reproduce
```
python3 make_lean.py      # from art/vehicles/wrx_sti; needs the pass-2 trace products (python3 make_all.py once)
```
It runs these steps in order:
* `bp/vectorize.py`: blueprint features become vectors.
* `tex/lamp/trace_lamps.py`: head lamp, fog lamp, indicator and side-marker outlines go to `bp/lamp_outlines.json`.
* `blender -b -P build_wrx_lean.py -- --render`: geometry, rig, clearance, UV, AO bake, painter, exports and renders.
* `WRX_OUT=lean bp/bpcompare.py`: IoU.
* `WRX_OUT=lean WRX_PFX=wrx_lean_clay bp/deliver.py`: the clay, suspension, clearance and raking sheets.
* `bp/deliver_lean.py`: the textured and comparison sheets.
* Optional: `blender -b lean/wrx_lean.blend -P tex/lamp/render_lamp_closeups.py` renders the head lamp close-ups (glow off/on).

## Where the triangles go (`tri_count.txt`)
| part | tris |
|---|---|
| body loft: 8-point sections, 40-odd stations, spent on the arches (11 cm), nose/tail (7 cm + plan-corner stations) and pillars; doors every ~59 cm (was 30 cm; the doors are straight in plan and use the pass-2 faired curves, raking-light check shows no ripple) | 1,096 |
| head lamp pockets (2 × [14-tri lens dish + 28-tri dark wall]) + the body re-triangulation around the two openings | 194 |
| cabin loft: 6-point sections; stations at the pillar edges plus ≤ 24 cm | 300 |
| STI scoop 18, wing 36, lip 12 (estimated, as in pass 2) | 66 |
| mirrors (2 × 12), floor 2, arch tunnel + inner wall liners (4 × 14) | 82 |
| fog lamp lens caps (2 × 8) | 16 |
| **mono WRX_Body** | **1,754** |
| wheels, 10-sided (rim and sidewall painted) | 144 |
| suspension: strut + lower arm per corner | 64 |
| head lamp glow quads, `WRX_FX_HeadGlow` (separate FX object, off by default) | 4 |
| **total** | **1,966** |

## What moved from geometry to texture
* Tail lamps, corner indicators and side markers. The head and fog lamps have small lens geometry plus their own atlas art; see the next section.
* The grille oval and lower intake.
* Black trim: B-pillar, sash, window surrounds, door handles, the scoop mouth, the lip.
* Panel and shut lines.
* A made-up plate ("MA 2001").
* The gold 10-spoke rims and the sidewall marks.

How the texture is made:
* Every feature is a vector shape (`bp/feature_vectors.json`):
  * Lamps, grille, trim and glass are blueprint class-mask contours, simplified.
  * Panel lines are thinned, traced and Douglas-Peucker'd blueprint dark strokes, filtered to keep shut and panel
    lines and drop hatch shading.
* The painter draws them anti-aliased into a 2 mm canvas for each view. Each texel samples the view that owns it (its
  dominant normal axis).
* Then baked AO and painted form shading are applied, and the result is quantised to RGB555 with a 4×4 Bayer dither.
* Materials use the shared PSX fake-shine shader (`parts/psx_mat.py`, the same formula as the BRZ: ambient + key +
  Blinn + painted env × Fresnel, env ≤ .45). The .glb gets Principled materials with the same textures.

## Head lamp pocket (revision 3, light molding)
The lens no longer sits on the nose: it is set into a shallow pocket, as the blueprint draws it.
* **Line classes** (blueprint front / side / top), re-checked before building:
  * The closed grey ring around the white lens is the **lamp outline** (lens + chrome bezel). It is the pocket opening.
  * The line leaving it up and outboard toward the A-pillar (front view), and running back along the bonnet (top
    view), is the **bonnet/fender shut line**. It is a body line: painted, never cut.
  * The dark arc in front of the lens in the side view is the pocket wall in shadow. The small clear lens behind it
    is the side marker (painted).
* **Depth:** the blueprint puts the lens plane 10–15 cm behind the lean nose at its lower edge. The brief was a *light*
  pocket that doesn't over-carve the nose, so the lens is set back a constant **3.5 cm** along the local surface
  normal. On the bonnet-top part of the rim that is a longer step back along x, capped at 6 cm, which gives
  1.7–2.6 cm of normal depth there.
  * Lens x range: 1.86–2.09, against the blueprint's 1.87–2.06 (side view) and 1.86–2.02 (top view).
* **Geometry** (`parts/lamps_lean.py` `_pocket` + `build_wrx_lean.py` `cut_pocket`):
  * A 14-corner prism along +x (front view = the traced outline exactly) is cut out of the body loft with an exact
    boolean, with materials transferred.
  * The prism's back cap is the lens: a shallow rim + centre fan dish (14 tris, smooth shaded, `clay_lampcap`).
  * Its sides are the pocket walls (`clay_trim` class, painted black and AO-darkened by the body painter).
  * The old conforming lens faces (`WRX_HeadLamp_L/R`, 2 × 51 tris) are gone.
* **UVs:** the lens UVs are projected along x, so the painted lamp art (unchanged, `tex/lamp/paint_lamps.py`) reads
  true in the front view. The art's bezel follows the dish rim exactly, because the painter gets the densified rim.
* **Budget:** body flank stations went from 30 cm to ~59 cm (two fewer stations, 48 tris saved). IoU and clearance
  are unchanged.
* **Glow quad:** it now sits 2 cm in front of the recessed lens centre.

## Head and fog lamps (revision 2; head lamp geometry superseded by the pocket above)
* **Outlines:** `tex/lamp/trace_lamps.py` traces the bugeye head lamp (lens + chrome bezel), the corner indicator
  sliver and the side marker from the blueprint at sub-pixel precision, then Fourier-smooths them into
  `bp/lamp_outlines.json`.
  * Front view, car-left side (the watermark doesn't cross it): 8× bicubic crop, lens/bezel threshold, outline.
  * Side marker: traced from the side view the same way.
  * Fog lamp: the watermark crosses both fog lenses, so its outline is an ellipse fitted to the blueprint lamp-class
    contour.
  * Only outlines are taken from the sheet. No interior raster is copied.
* **Head lamp geometry** (`parts/lamps_lean.py`), `WRX_HeadLamp_L/R`, 51 tris each, joined into `WRX_Body`:
  * A lens face that conforms to the nose: the body's front facets, clipped in front view to the traced outline and
    lifted 4 mm along the lamp normal.
  * It follows the faceted corner exactly, so nothing cuts into the body, and there are no cracks or bulges. In front
    view the outline matches the blueprint exactly.
  * UVs are a planar projection along the lamp's own mean normal (≈ 17° outboard, 17° up), at uniform scale. That
    removes the corner stretch of the old per-view body paint.
* **Fog lamp geometry:** `WRX_FogLamp_L/R`, an 8-tri lens cap on the bumper, lifted 3–7 mm.
* **Art** (`tex/lamp/paint_lamps.py`): painted into the spare bottom-left quadrant of the 256² parts atlas
  (`tex/wrx_wheel.png`; head lamp tile 92 px, fog tile 30 px), then RGB555 + Bayer. All of it is vector-drawn from the
  projected outline:
  * Head lamp:
    * dark chrome bezel (lit top edge, shadowed bottom)
    * dark reflector cavity
    * main round reflector bowl with facet rings and a small hotspot (inboard, low)
    * secondary round lamp in the outboard-upper taper
    * lens highlight crescent and streak
  * Fog lamp: chrome rim, fluted lens, round reflector, hotspot.
  * Values are capped at 232 in the texture.
  * The `WRX_Lamp` fake-shine material uses ambient .66, key .30, spec .30, env .20 (≤ .45). Lights-off renders peak at
    246/255, so nothing clips to white.
* **Body texture:**
  * dark housing under the lenses
  * a clean rounded-square fog housing in place of the ragged blueprint black-ring contours
  * outline specks around the lamps removed
  * corner indicator (front sliver) and side marker painted as clear lenses with an amber bulb, from the traced outlines
* **Glow FX:** `WRX_FX_HeadGlow` is one 2-tri quad per lamp, 2 cm in front of the lens, with its own 64² RGBA sprite
  (`tex/wrx_glow.png`, alpha-blended emission). It is a separate node under `WRX-vehicle`. It is hidden in every review
  render. **Godot imports it visible**, so set `visible = false` and switch it on with the lights.
* **Known limit:** the blueprint's side and top views put the lamp about 5–9 cm further back, in a recessed pocket on the
  upper nose corner (side view x 1.88–2.08, top view x 1.86–2.02). The lean nose is fuller there, and the lens sits on
  the lean surface at x 1.93–2.13 (`lean/tex/lamp_uv.json`). So the lamp reads correctly from the front and 3/4 but
  only as a narrow edge in the pure side view. Matching the side view too would mean cutting a lamp pocket into the
  nose loft, which would change the approved body shape. Not done.
* IoU and clearance are unchanged (gate side .978 / top .978 / front .956 / rear .956; tightest wheel gap 18 mm).

## Rig (Godot VehicleBody3D / VehicleWheel3D)
```
WRX-vehicle                 root, ground, mid-wheelbase                       -> VehicleBody3D
 ├─ WRX_Body                ONE mesh (incl. head/fog lamp lenses), origin = COM estimate (x 0, z .50) at ride height
 ├─ WRX_FX_HeadGlow         2 glow quads (FX, off by default)
 ├─ Hub_FL-wheel …          empty at the static hub                            -> VehicleWheel3D
 │   └─ Steer_FL / FR       front: rotates about local Z (vertical through the hub), ±30°
 │       └─ WRX_Wheel_FL    10-sided, origin = hub, spins about the axle
 └─ Susp_FL …               empty at the static hub: follows hub position + steer only, never spin
     └─ WRX_Susp_FL         strut + lower arm (16 tris)
```
| | front | rear |
|---|---|---|
| hub (glTF x, y, z) | ±.743, .317, +1.247 | ±.738, .317, −1.247 |
| tyre radius / width | .317 / .225 (225/45R17) | same |
| travel (clearance-tested) | +65 mm bump / −80 mm droop | same |
| steer lock | ±30° | – |

* Ride height: ground at y 0. The body origin (COM estimate) is 0.50 m up at mid-wheelbase.
* **Clearance:** 9 lock × travel combinations, BVH, all clear. The tightest gap is 18 mm (FL, −30° + full bump).
  The arch chords are lifted 15 mm (`ARCH_SAG`) so the sparser arch stations never sag into the tyre path.
* **Strut change (this revision):** the struts/arms are no longer under `Steer_XX`. They now sit on separate
  `Susp_XX` nodes that follow only wheel position and steering, not spin. Geometry, tri counts and renders are unchanged.

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

## Estimated or known gaps (first version)
* There is no blob shadow yet.
* The tyre lettering is placeholder blocks. There are no badges yet.
* The UV seams are not yet reviewed in the 640×480 frame. The nose face shows a few shading creases from the
  sparse nose stations.
