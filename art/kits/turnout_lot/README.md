# Touge turnout parking-lot kit (approved)

Arthur (Art Director). Austin approved the **16 m two-row** kit on 2026-11-19.

Cel A soft, LotArt frame. The lot sits on the **inside of the bend** (cut / lattice side). Pocket 62 m × 16 m deep, 14 m tapers, 7.5 m road; two angled stall rows, 11 stalls per row at 2.5 × 5.0 m and 70°; curb 0.15 m; two sodium lamps (pool radius 6 m). Road paint (filled orange-red chevrons and a yellow centre line) is authored in LotArt with x < 0 (into the road). The white drop-side rail stays on Gordon's far side of the road; this kit does not add one.

The 11 m one-row study is kept only as comparison renders (`renders/w11_*.png`, `renders/turnout_11_vs_16.png`). It is not the approved kit.

## LotArt frame (Godot Y-up)

Origin = road edge at the lot entrance; +X into the lot (hill / inside of the bend); +Y up; +Z along travel. Glbs are straight in this frame (LotArt is a rigid entrance-tangent transform, not a path-curved mesh). Exports use `export_yup=True` (Blender stores (x, −z, y) for LotArt (x, y, z)).

## Piece → TurnoutLot child

Instance these under `WorldVP/Dressing/CourseDressing/TurnoutLot`. Packed scene: `scenes/turnout_lot.tscn`.

| Piece | Child of `TurnoutLot` | Tris |
|---|---|---|
| `glb/lot_floor.glb` | Floor | 110 |
| `glb/lot_curbs.glb` | Curbs | 44 |
| `glb/lot_stall_lines.glb` | StallLines | 63 |
| `glb/lot_wheel_stops.glb` | WheelStops | 220 |
| `glb/lot_back_wall.glb` | BackWall (mtn_lattice_slope_g along the mid back; cut-slope panels on the tapers) | 616 |
| `glb/lot_hill_top.glb` | HillTop (verge + cedar cards) | 218 |
| `glb/lot_lamps.glb` | Lamps (two posts on the back curb, arms toward the road / local −X, glow + pool) | 92 |
| `glb/lot_props.glb` | Props (children `Sign`, `Vending`) | 54 |
| `glb/lot_road_paint.glb` | LotArt (chevrons + yellow centre line, x < 0, in the road) | 27 |
| **Total** | | **1444** |

**Drop-in:** instance those children, then copy `LotArt.transform` onto Floor, Curbs, StallLines, WheelStops, BackWall, HillTop, Lamps and Props. Gordon currently builds those slots in course space and only moves LotArt onto the lot frame — without that copy, LotArt-space glbs will sit at the world origin.

Counts also live in `layout.json` and `tri_counts.json`.

## Shaders when instancing in the root project

- Floor / verge / cut / cedars: `scroll.gdshader` with `soft_surface=1`
- Stall lines, arrows, edge line, chevrons, centre line: `chevron.gdshader` (never inked)
- `Emit_*` (lamp head, vending face): `cel_k=0`
- Curbs, wheel stops, lattice, poles, sign, vending body: default prop toon + ink

## Rebuild

```
./run.sh                 # textures + 16 m / 2-row glbs + Cel A-soft renders + sheet
SKIP_TEX=1 ./run.sh
POCKET_M=80 TAPER_M=16 POCKET_W=16 ROWS=2 N_LAMPS=2 ./run.sh
```

`./run.sh` writes the approved pieces to `glb/`. An optional `ONLY=w11 ./run.sh` still builds the 11 m one-row comparison under `glb/w11/` (not committed).

## Renders

- `renders/godot_cel_race_cam_640.png`, `renders/godot_cel_lot_overview_640.png` — Godot Cel A soft (`CEL ON SOFT ON`) from a scratch copy of the root project (never Gordon's worktree). The live HUD is in the frame because these are the game viewport.
- `renders/w16_*.png` — Blender Cel A-soft stand-in frames for the approved 16 m kit.
- `renders/turnout_11_vs_16.png` — 11 m vs 16 m comparison (11 m is not the approved kit).
- `renders/turnout_sheet.png` — 16 m contact sheet.

## Weak spots

- Lattice modules along the mid wall are axis-aligned; taper flanks use a cheaper cut-slope panel instead of yawed modules (yawed copies presented a giant face to the road).
- Lamp pools are soft 6 m ovals under the heads (no overlap).
- The P sign is a painted plate; readable square-on, smaller at race-cam distance.
