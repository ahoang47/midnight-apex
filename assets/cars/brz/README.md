# car_brz — Subaru BRZ (ZD8, 2nd gen), lean game version

Game-ready import of the lean build. Source, build scripts and review renders: `art/vehicles/brz/lean/` (README there).

| | |
|---|---|
| File | `car_brz.glb` (glTF binary, textures **embedded**: `brz_body` 1024², `brz_wheel_atlas` 256²; PNG sources and the env map in `art/vehicles/brz/lean/tex/`) |
| Triangles | **1,999** total (cap 2,000), incl. wheels, struts/arms and FX quads |
| Blueprint IoU | side 0.971, top 0.980, front 0.948, rear 0.932 (gate side/top ≥ .95, front/rear ≥ .92) |
| Clearance | 9 poses (lock −30/0/+30° × bump/static/droop): all clear, tightest 16 mm (FL, steer +0 deg, travel +0.045) |

**Glow FX:** none in this version (no lamp glow sprites or blob shadow yet; add them as FX quads inside the 2,000 budget).

Materials in the .glb are plain Principled (baked albedo); the faked shine is the vehicle shader in
`design/art/art_direction.md` A.8 (env map: `art/vehicles/brz/lean/tex/`).

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
1. Import `car_brz.glb`. On the root `<CAR>-vehicle`, change the type to **VehicleBody3D** (or re-parent the
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
