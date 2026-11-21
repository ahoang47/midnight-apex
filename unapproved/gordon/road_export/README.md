# Touge road export (for Arthur)

Reference geometry of the road as the Godot game builds it today (`track_road.gd` / `art_kit.strip` / `course.gd`). Terrain is not included. Regenerate whenever the course spec or road builder changes; do not hand-edit these files.

## Files

- `road_surface.glb` — the exact CourseRoad mesh in Godot world space, +Y up, metres, every node at the identity transform (vertices already in world space). One object per turn (`Turn01`…`Turn10`). Vertex colour R holds the turn id (1–10 as 8-bit). `LotFloor` is the current drivable lot floor (authored `assets/env/turnout_lot/lot_floor.glb` placed with the game's LotArt frame). No hills, skirts, galleries, rails or lamps.
- `road_centreline.json` — 1 m samples over the dressed range, plus a reference block of current lamp poses, rail segment poses (at scroll 0) and gallery extents, and a header (units, axes, generator commit, specs).
- `README.md` — this file.

## How to regenerate

From the project root, with the Godot 4.6 binary:

```
godot --headless --path . --script tools/touge_race/road_export.gd
# optional: -- --out res://unapproved/gordon/road_export --display res://spec/display.json --config res://spec/race_config.json

```

The script reads `spec/display.json` and `spec/race_config.json`, builds the course with `TrackRoad.build_course`, and writes this folder. It does not commit anything.

## Coordinate conventions

Godot world space, +Y up, right-handed. First straight starts at the origin and travels -Z. Lateral d > 0 is right of travel (point(): x - tz*d, z + tx*d). Road surface is banked and graded.

- Units: metres.
- `s` is distance along the centre line (s = 0 at the start of the first 45 m approach straight). The dressed road (and these samples) run from s = -60.0 to s = 1075.011, which is 60 m of run-in and run-out past the course (`course.length` = 1015.011 m).
- `left_width` / `right_width` are metres from the centre line to the drivable edge. On open road both equal `road_half_m` (3.75). Over the turnout lot the inside edge grows with the taper to `road_half_m + pocket_w_m`.
- `section` is `gallery` when `course.groof_at` sees another leg overhead by at least `road_clear_m`, `bridge` when another leg's road lies under this deck by at least that amount, otherwise `road`.
- Turn cuts: see `header.turns` (turn *i* covers `[s0, s1)` from this view's `off` to the next, with run-in on turn 1 and run-out on turn 10).
- UV on the road mesh: `UV.x` = 0 at the left edge (d = −W) to 1 at the right (d = +W). `UV.y` = `s` in metres. The game tiles this as `(UV.y + scroll_m) / lamp_period_m` in `scroll_vertex_lit.gdshader`. The material on the glb is a preview only.
- Lamps: kit6 posts sit at `(W + lamp_out_d_m)` on the drop / outside at that `s`, and do not scroll. Rotations are Godot Euler (YXZ) in world space. The mesh arm points along local −X. Lot lamps are listed with `kind: lot`.
- Rails: W-beam modules every `guardrail_step_m` (4 m) on the outside, at d = drop_at(s) × (W + 0.45). Positions are at `scroll_m = 0` (editor / race start). In the current game they still stream with the road. `visible` follows `stream()` (hidden when the cap leaves no room, or over the lot on the lot side).
- Galleries: s-ranges where `touge_dressing._gallery` would build a wall (`groof_at` > 0 on both ends of a 2 m step), with the wall's distance past the edge (`gwall_at`) and roof height over this road.

## Generator

- HEAD: `060d9f3887426a26d8497518e6ad0edb9df672fb`
- Worktree dirty (files that affect this export): ["M scripts/course.gd", "M scripts/touge_dressing.gd", "M scripts/track_road.gd", "M spec/display.json"]
- Specs: res://spec/display.json + res://spec/race_config.json

## Verification (this run)

- In-game CourseRoad: verts=10800 tris=3600 aabb=min(-369.5867,-55.2000,-66.9106) max(3.7500,4.8000,112.6925)
- Reimported glb road objects (LotFloor excluded): verts=10800 tris=3600 aabb=min(-369.5867,-55.2000,-66.9106) max(3.7500,4.8000,112.6925)
- Vertex / triangle check: PASS (split objects may duplicate a row of verts at each turn seam; triangle count must match the source).
- AABB max component delta: 0.000046 m (pass ≤ 0.001)
- Centreline samples: 1136 (expected 1136 over the dressed 1 m grid). Course length 1015.011 m.
- Lot floor: LotFloor verts=330 tris=110 (Arthur's lot_floor.glb, baked through the game's LotArt frame into world space)
- Current procedural terrain (Terr* meshes) is listed in road_centreline.json under terrain_ref_counts. No triangle or draw-call budget is defined for environment sections.
