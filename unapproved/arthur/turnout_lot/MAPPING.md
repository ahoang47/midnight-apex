# Turnout lot kit → Gordon's TurnoutLot slots

Frame (LotArt, Godot Y-up): origin = road edge at the lot entrance; +X into the lot (hill / inside of the bend); +Y up; +Z along travel. Glbs are straight in this frame (LotArt is a rigid entrance-tangent transform, not a path-curved mesh). Default kit is **11 m deep**.

## Piece → child node (11 m, use `glb/w11/`)

| Piece | Child of `WorldVP/Dressing/CourseDressing/TurnoutLot` |
|---|---|
| `lot_floor.glb` | Floor |
| `lot_curbs.glb` | Curbs |
| `lot_stall_lines.glb` | StallLines |
| `lot_wheel_stops.glb` | WheelStops |
| `lot_back_wall.glb` | BackWall (mtn_lattice_slope_g along the mid back; cut-slope panels on the tapers) |
| `lot_hill_top.glb` | HillTop (verge + cedar cards) |
| `lot_lamps.glb` | Lamps (two posts on the back curb, arms toward the road / local −X, glow + pool; pools r = 6 m, centres 19 m apart, no overlap) |
| `lot_props.glb` | Props (children `Sign`, `Vending`) |
| `lot_road_paint.glb` | LotArt (solid filled orange-red chevrons + yellow centre line; lives at x < 0, in the road) |

Packed scene: `scenes/turnout_lot_w11.tscn` instances each glb as a child of the matching empty slot, so `slot()` stays empty and the procedural placeholders are not built.

**Drop-in:** instance those children, then copy `LotArt.transform` onto Floor, Curbs, StallLines, WheelStops, BackWall, HillTop, Lamps and Props. Gordon currently builds those slots in course space and only moves LotArt onto the lot frame — without that copy, LotArt-space glbs will sit at the world origin.

16 m two-row comparison kit: `glb/w16/` + `scenes/turnout_lot_w16.tscn` (not the slot default; two angled rows fit at 16 m, not at 11 m).

Rebuild: `POCKET_M TAPER_M POCKET_W ROWS N_LAMPS ./run.sh` from this folder (default builds both 11 m and 16 m).
