# car_s2000 — Honda S2000 (AP1, soft top up), lean game version

Game-ready import of the lean build. Source, build scripts and review renders: `art/vehicles/s2000/lean/` (README there).

| | |
|---|---|
| File | `car_s2000.glb` (glTF binary, textures **embedded**: `s2000_atlas_lean` 256², `s2000_body` 1024²; PNG sources and the env map in `art/vehicles/s2000/lean/tex/`) |
| Triangles | **1,916** total (cap 2,000), incl. wheels, struts/arms and FX quads |
| Blueprint IoU | side 0.952, top 0.992, front 0.930, rear 0.951 (gate side/top ≥ .95, front/rear ≥ .92) |
| Clearance | 9 poses (lock −30/0/+30° × bump/static/droop): all clear, tightest 3 mm (FR, steer +30 deg, travel +0.040) |

**Glow FX:** none in this version (no lamp glow sprites or blob shadow yet; add them as FX quads inside the 2,000 budget).

Materials in the .glb are plain Principled (baked albedo); the faked shine is the vehicle shader in
`design/art/art_direction.md` A.8 (env map: `art/vehicles/s2000/lean/tex/`).

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
1. Import `car_s2000.glb`. On the root `<CAR>-vehicle`, change the type to **VehicleBody3D** (or re-parent the
   children under a new VehicleBody3D). `<CAR>_Body` stays a mesh child. Its origin is the COM estimate, so set
   `center_of_mass_mode = Custom` and use the `<CAR>_Body` position as `center_of_mass`.
2. On each `Hub_XX-wheel`, change the type to **VehicleWheel3D** and keep its transform (the static hub centre). Set
   `wheel_radius`, `suspension_travel` and `use_as_steering` (front) / `use_as_traction` as in the table above.
   VehicleWheel3D moves, steers **and spins** its children, so `Steer_XX` → `<CAR>_Wheel_XX` stay under it.
3. Each `Susp_XX` is a **Node3D sibling** of the wheels (a child of the VehicleBody3D) and holds `<CAR>_Susp_XX`
   (strut + lower arm, 16 tris). Attach `susp_follow.gd`, set `wheel` to the matching VehicleWheel3D, and set
   `steers = true` on FL/FR. Each physics frame the script copies the wheel's position (suspension travel) and its
   steering angle about +Y, never the spin.
4. Steering: set `VehicleBody3D.steering` within ±0.524 rad (±30°). The well clearance was tested only to that lock.
