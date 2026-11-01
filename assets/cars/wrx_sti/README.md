# car_wrx_sti — Subaru Impreza WRX STI (GDB "bugeye", 2001-02), lean game version

Game-ready import of the lean build. Source, build scripts and review renders: `art/vehicles/wrx_sti/lean/` (README there).

| | |
|---|---|
| File | `car_wrx_sti.glb` (glTF binary, textures **embedded**: `wrx_wheel` 256², `wrx_body` 1024², `wrx_glow` 64²; PNG sources and the env map in `art/vehicles/wrx_sti/lean/tex/`) |
| Triangles | **1,966** total (cap 2,000), incl. wheels, struts/arms and FX quads |
| Blueprint IoU | side 0.978, top 0.978, front 0.956, rear 0.956 (gate side/top ≥ .95, front/rear ≥ .92) |
| Clearance | 9 poses (lock −30/0/+30° × bump/static/droop): all clear, tightest 18 mm (FL, steer -30 deg, travel +0.065) |

**Glow FX:** `WRX_FX_HeadGlow` (2 additive head-lamp glow quads, 4 tris, counted in the total) is **hidden by default**. Unhide it (or toggle `visible` from the headlight state) in Godot; it uses `wrx_glow.png`, additive, unshaded.

Materials in the .glb are plain Principled (baked albedo); the faked shine is the vehicle shader in
`design/art/art_direction.md` A.8 (env map: `art/vehicles/wrx_sti/lean/tex/`).

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
1. Import `car_wrx_sti.glb`. On the root `<CAR>-vehicle`, change the type to **VehicleBody3D** (or re-parent the
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
