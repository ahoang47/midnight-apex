# Mountain districts: every district is a pass, all three entry lanes (unapproved mockup)

Arthur (Art Director), 2026-11-15. Austin on `tight_districts`: *"Neither Wangan nor street give the sense of being on a
mountain pass. Also, please render all three lane placements."*

Built on `../tight_districts/` (left untouched). Same pipeline and look: Cel A soft, Godot 4.6.3 GL Compatibility, 3D at
640x480 with RGB555 + Bayer last, HUD at 1280x960 unshaded and uninked, one #F0C894 sodium, navy #0B172B fog, no LIMP tag.

- `mountain_districts_sheet.png`: 3x3, rows touge / wangan / street, cols entry OUT / MID / IN
- `{touge,wangan,street}_{out,mid,in}_cat.png`: the 9 frames (1280x960)

Every frame uses the same CAT chasing setup: the rival is 11 m ahead in the player's line with its taillights in the
chevrons and the red tail wash. The CAT CHASING tie-gap box is on. Player and chevrons sit on that lane, and the plan box
has that stance selected (OUT = A / POW, MID = S / HAN, IN = D / EN). No floating OUT / MID / IN markers.

## The three passes

| District | Road | Grade | Uphill (left, inside of the first corner) | Downhill (right) |
|---|---|---|---|---|
| Touge | 6.0 m, 2 lanes | 8.5 % (unchanged) | cut slope, cedars | guardrail, forest drop |
| Wangan: mountain skyline / turnpike | 7.5 m, 2 lanes | 6 % at the car, ramping to 8 % from s 10 to 60 m, 3 % bank in the sweeper | U drainage channel, 3 m cast retaining wall, shotcrete / rock cut above it, cedars on top, dark flank up to the ridge | Wangan parapet tight on the edge, fascia, the slope falling away with cedar tops below, then the bay 180 m down and 1 to 3.5 km out: city at the mountain foot, sodium port and quay road, cranes, the bay bridge, far shore |
| Street: hillside onsen town | 5.8 m back street + 1 m pavements | 8 % at the car, ramping to 10 % from s 6 to 30 m | dry-stone retaining walls with shopfronts set into the slope, houses on the terrace above, cedars, flank to the ridge | pipe handrail on the pavement, houses stepping down with their roofs below road level, stone steps down between them, the town's lights in the valley 90 m below |

The grade comes from the shared `elev(s, d)`, so cars, chevrons, camera, road, walls and props all climb together. It
steepens ahead of the car, so the road rises in frame and the camera pitches up. The drop reads from the void beyond the
parapet or handrail and the lights far below. They sit 3 to 10 degrees under the horizon, which puts them in the gap above
the parapet or roofs and under the ridge band.

Wangan keeps:
- tall sodium lamps with arms, staggered
- km posts
- the parapet
- lane lines
- a cantilever toll-road sign (generic: スカイライン SKYLINE / 料金所 2km TOLL / 湾岸方面)

Street keeps:
- poles and sagging wires
- two curve mirrors
- a vending machine (kept away from the camera)
- generic shop signs, no brands, boards dimmed below the car

## What changed (all marked `# MOUNTAIN:` in `godot/scripts/district_preview.gd`)

**District table**
- Per-district `grade` [at car, ahead, ramp start, ramp end], `bank` and `band`, with `grade_at`, `bank_at` and `elev`
  now on for every district.
- Street now uses the 2048x384 star sky. `street_sky.png` is 128 px tall and stretched its stars into vertical streaks on
  open sky.

**Frames and lanes**
- `_frames()`: 3 frames per district, named `<district>_<lane>_cat.png`.
- **Bug fix:** `_lane_d` passed "outside" / "center" / "inside" to `Track.lane_offset`, which expects "OUT" / "MID" /
  "IN". It always fell through to OUT, so every earlier districts / tight frame was OUT whatever was asked. It now passes
  the lane through.
- The chase camera now carries the lane shift (`_cam_d = d(lane) - d(OUT)`). OUT keeps the old framing, and MID / IN get
  the same view of their car. Before this, the IN car sat half out of frame on a camera parked on the OUT side.

**Sky and far camera**
- The sky cylinder is scaled x19 (r 4750; it looks the same because the scale is uniform). At r 250 it is depth-tested
  but writes no depth, so it drew over the valley 1 km+ out.
- `cam` / `glow_cam` / `mirror_cam` far plane is now 6000.

**New dressing**
- `_dress_wangan_mtn`, `_dress_street_mtn`.
- Helpers:
  - `_flank`: dark band to the ridge behind the uphill side, so nothing far below shows through.
  - `_valley_lights`: camera-facing quads from a 5-swatch palette (cream / teal / sodium / red / white), full-bright with
    a touch of fog. Size scales with distance, so each light is a steady 1 to 2 px dot at 640x480.
  - `_valley_floor`.
  - `_far_prop`.
  - `_pol`: places things by bearing and distance from the camera.
- `prop(..., level)`: buildings stay plumb on the grade; walls pitch with it.

The old `_dress_street` / `_dress_wangan` (tight) are still in the file but unused.

## Assets

**New, Blender by script** (`blender/build_mountain.py`, exported to `godot/assets/env/`, tris in
`godot/assets/env/tri_counts_mountain.json`):

| Asset | Tris | Notes |
|---|---|---|
| `mtn_retain_wall` | 20 | 4 m module, 3 m high, battered, U drainage channel at its foot |
| `mtn_stone_wall` | 8 | 4.5 m dry-stone module, battered |
| `mtn_house` | 20 | 6 x 7 x 5.4 m gable house, 3 dim `Emit_` windows |
| `mtn_handrail` | 24 | 2 m pipe rail |
| `mtn_steps` | 52 | 10 stone steps going down off the pavement |
| `mtn_toll_sign` | 22 | single-post cantilever toll-road sign |
| `street_curvemirror` | 24 | |
| `wangan_gantry_2l` | 168 | built, not placed in these frames |

**New textures** (`tex_src/make_tex.py`, quantised RGB555 + Bayer):
- `mtn_retain_concrete`
- `mtn_stonewall`
- `mtn_house_wall`
- `mtn_roof`
- `emit_house_window`
- `mtn_steps`
- `mtn_sign_toll`
- `valley_water`, `valley_land`
- `emit_valley_lights` (a 10x2 palette, unquantised)

**Reused:** wangan parapet, km post, lamp, crane, bridge, street shops 0 to 3, pole, vending, the touge kit (cut slopes,
cedars, verge, ridge band) and `wangan_sky`.

**Scene env tris:** touge 7,702 / wangan 17,774 / street 15,036, plus the two cars.

## Re-render

```
./run.sh                                   # textures + Blender + import + 9 frames + sheet
SKIP_ASSETS=1 ONLY="wangan" ./run.sh       # one district (3 frames)
python3 make_sheet.py                      # sheet only
```

## Weak spots

**Grade read**
- The grade reads mostly from the context (cut wall height, lights far below, roofs under the road) rather than from the
  road surface itself. At 6 to 10 % with the fixed B.5b chase the road only rises gently in frame. A steeper visual
  would need either a steeper grade or a lower camera.

**Valley lights**
- The lights are a noise field of single dots. They read as a city at night, but they have no structure up close (no
  blocks or street grid), and the far-shore and port clusters blend into one carpet.
- The cranes are barely visible at 1.9 km. Their red aviation lights don't read.
- The bay bridge is only a faint fogged silhouette near the horizon, with no deck lights.

**Wangan dressing**
- The toll-road sign is very small at s 62 m, so it only reads as a green fleck. The 2-lane gantry was built but not
  placed.
- The retaining wall is a large flat surface on the left in the IN frame, and its weep holes read as big dark blobs close
  to the camera.

**Street dressing**
- The terrace houses above the uphill walls are mostly hidden by the shopfront block nearest the camera.
- The right-side utility pole near the camera splits the frame down the middle, as in tight.

**Touge**
- Touge OUT is not pixel-identical to the approved `touge_cat`. About 0.8 % of pixels differ, almost all ink on cedar
  edges against the now-farther sky. Content and framing are unchanged.

**Tri budget**
- Wangan and street are over the old ~12k guide.
