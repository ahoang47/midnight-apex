# car_rx7: Mazda RX-7 (FD3S), game version (paint15)

Approved by Austin 2026-11-20. Review renders, textures and Austin's drawings: `art/vehicles/rx7/`.

| | |
|---|---|
| Files | `car_rx7.glb` (glTF binary, textures embedded: body 1024², wheel 256²) |
| Triangles | 4,618 total. This is over the MX-5's 2,000 cap: the body is a carved visual hull (carve_v20), not hand-modelled. |
| Blueprint IoU | side 0.971, top 0.976, front 0.942, rear 0.956 |
| Glass and lines | Window shapes and door, hood and hatch lines are Austin's drawings (paint12/13), mirrored to be symmetrical; hood line shortened in paint14 |
| Shading | Painted value gradient in the albedo (darker low on the body, lit shoulders), painted at albedo level 0.92; normals split at 40° |
| Materials | `RX7_Paint_Body`, `RX7_Under`, `RX7_Wheel` |

## Rig
Same layout and axes as the MX-5 (`assets/cars/mx5/README.md`): +Y up, +Z forward, +X = car left, ground at y 0,
no node rotations or scales. `RX7-vehicle` imports as a VehicleBody3D, `Hub_XX-wheel` as VehicleWheel3D.

| | front | rear |
|---|---|---|
| hub (glTF x, y, z) | ±.730, .332, +1.207 | ±.730, .332, −1.207 |

* `RX7_Body` origin (COM estimate) is 0.45 m up, at mid-wheelbase.
* `Susp_XX` empties hold `RX7_Susp_XX`; use `susp_follow.gd` from the MX-5 folder as for the other cars.
* No `.tscn` or tuned VehicleBody3D values yet; that's engine work.

## Display
In the test scene the car used a copy of the MX-5's `spec/display.json` entry with tint 1. `spec/display.json` is
not changed in this commit.

Known global issue (not changed here): `shaders/car_vertex_lit.gdshader` adds moon and sodium light without a clamp,
so every car clips under lamps.
