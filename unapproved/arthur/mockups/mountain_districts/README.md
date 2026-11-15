# Mountain districts: every district is a pass, all three entry lanes (unapproved mockup), pass 2: perspective + hillside city

Arthur (Art Director), 2026-11-15. Austin on `tight_districts`: *"Neither Wangan nor street give the sense of being on a
mountain pass. Also, please render all three lane placements."*

Built on `../tight_districts/` (left untouched). Same pipeline and look: Cel A soft, Godot 4.6.3 GL Compatibility, 3D at
640x480 with RGB555 + Bayer last, HUD at 1280x960 unshaded and uninked, one #F0C894 sodium, navy #0B172B fog, no LIMP tag.

- `mountain_districts_sheet.png`: 3x3, rows touge / wangan / street, cols entry OUT / MID / IN
- `{touge,wangan,street}_{out,mid,in}_cat.png`: the 9 frames (1280x960)

Every frame uses the same CAT chasing setup: the rival is 11 m ahead in the player's line with its taillights in the
chevrons and the red tail wash. The CAT CHASING tie-gap box is on. Player and chevrons sit on that lane, and the plan box
has that stance selected (OUT = A / POW, MID = S / HAN, IN = D / EN). No floating OUT / MID / IN markers.

## Pass 2 (v2): perspective, and a real hillside city

Austin on v1: *"The street district feels off, it doesn't feel like city in the mountains, it feels very tacked on. Also
to help with the gradient, the side assets should be decreasing in height, to achieve perspective. Your issue is that
there's no perspective."*

**Files.** The v1 frames and `mountain_districts_sheet.png` are untouched. `MTN_V=1 ./run.sh` rebuilds them
pixel-identically; I checked wangan MID: 0 px differ.
- `mountain_districts_sheet_v2.png`: 3x3, rows touge / wangan / street, cols OUT / MID / IN
- `mountain_districts_v1_v2_mid.png`: MID lane, v1 against v2, one row per district
- `{touge,wangan,street}_{out,mid,in}_cat_v2.png`: the 9 frames

### What changed for perspective (all districts)

**Regular real-size verticals and hard edges**, so they shrink toward one vanishing point:
- **Touge:**
  - 法枠 lattice-framed cut slope in 4 m modules, with cells 2 m × 2.15 m and proud cast beams, so every cell edge is an
    inked line converging up the road. It replaces the smooth cut-slope slab.
  - Delineators every 8 m on both edges.
  - Sodium lamps every 32 m (was 48 m).
- **Wangan:**
  - Retaining wall with a pilaster at every 4 m joint and a proud coping.
  - The same lattice in shotcrete above the wall.
  - Delineators on every other parapet module.
  - Tall lamps every 32 m each side, staggered 16 m (was 48 m / 24 m).
- **Street:**
  - Balcony slabs every 3.1 m on the mid-rise fronts, regular window bays, and blade signs at the same height.
  - Poles every 20 m.
  - The footbridge.

**The cut gets shallower up the hill.** The Wangan wall steps down from 3.0 m to 2.1 m between s 16 and 126 m, and the
lattice and cedars sit on it, so the cut top drops as the road climbs away.

**The grade runs on into the distance.** Touge no longer crests in frame (8.5 % rising to 9.5 %, was 8.5 % then a
crest), so the rising road runs up to a vanishing point above the horizon in every district.

**Chase camera.** It is the same B.5b family: fixed, behind and right of the player, not mirrored, following the lane.
For all three districts it is now:
- 2.45 m up (was 3.1)
- 7.4 m back (was 7.6)
- a 47° lens (was 56.7°)
- aimed 34 m up the road (was 22 m)

The longer, lower view stacks the receding verticals and shows the road rising. The HUD is unchanged.

### Street v2: a city built into the mountain (Atami / Kitano / Onomichi / Mid-Levels)

**Uphill side (left):** 3- to 6-floor mid-rise blocks entered from the pavement.
- Ground-floor fronts: lit entrance, shutter, small shop, hotel lobby.
- Balcony slabs and lit windows, about a third lit, all below the car's brightness.
- Blade signs with generic boards only (ホテル, 旅館, ♨湯, スナック, 喫茶, 民宿), dimmed.
- Stair alleys climb between them.
- A **footbridge** crosses overhead from a 2nd floor to a pier 4.5 m past the downhill kerb.

**Downhill side (right):** a pipe handrail on the kerb.
- The near blocks have their roofs ~2.6 m below the road, with 6 floors going down the slope.
- More rows step down to the right, with their lit fronts below road level.

**Ahead:** past the 90 the mountain climbs straight on.
- Rows of blocks across the view step up the hill facing the street, with rooftop boards.
- Behind them is the dark mountain to a ridge line.
- The mountains close round the far side of the bay on the right, over the valley.

**Kept:** 5.8 m street, 8-10 %, poles and sagging wires, the curve mirror at the 90, a vending machine, generic signs
only.

**Removed:**
- Poles are on the uphill side only, so none splits the frame.
- No drop wires run over the camera.
- No rooftop board stands beside the camera.

### New for pass 2

Blender (`blender/build_mountain.py`) tris:

| Asset | Tris | Notes |
|---|---|---|
| `mtn_lattice_slope_g` / `_c` | 74 | |
| `mtn_retain_wall_p` | 24 | |
| `mtn_delineator` | 8 | |
| `mtn_block_up_a..d` | 168-244 | |
| `mtn_block_dn_a..d` | 226-344 | |
| `mtn_block_tier_a..c` | 232-514 | |
| `mtn_footbridge` | 98 | |
| `mtn_steps_up` | 80 | |

Textures (`tex_src/make_tex.py`):
- `mtn_lattice_beam`
- `mtn_lattice_fill_g` / `_c`
- `emit_delineator`
- `mtn_block_wall_a..c`
- `mtn_roof_flat`
- `emit_mtn_windows` (32-cell atlas)
- `emit_mtn_ground` (4 fronts)
- `emit_mtn_signs` (6 boards)
- `mtn_rail` (alpha)
- `mtn_bridge_fascia`

**Code:** `godot/scripts/district_preview.gd`, marked `MOUNTAIN PASS 2` / `v2`, gated by `V2` (`MTN_V=1` = v1):
- `_cam_cfg`
- `_dress_touge_v2`, `_dress_wangan_v2`, `_dress_street_v2`
- `_hill_y`, `_hill_mesh`, `_far_ridge`, `_block_far`, `_delins`
- `shaders/scroll.gdshader`: `gb_far` writes the far mountain masses to the G-buffer as sky, so the ink pass does not net
  their big far faces in black.
- Street v2 fog_far is 140 (was 110). Far tiers are fogged at most 55 % (walls) and 30 % (windows / signs).
- Wangan v2 bay sits 105 m down (was 180). The lower camera sees less over the parapet, so the light field sits nearer
  the horizon, at bearings 8-27°, 1.1-3.3 km out.

**Scene env tris (v2):** touge 9,970 / wangan 22,630 / street 44,730, plus the cars.

### Pass 2 weak spots

**Wangan**
- **IN shows only a thin strip of bay lights.** On the IN lane the parapet hides most of them, and MID shows fewer than
  v1. The lower, longer camera trades some of the drop for the climb.
- **The IN frame still has a big near wall on the left.** The pilasters and coping give it rhythm, but it is the largest
  surface in frame.

**Street**
- **The near uphill block reads flat close to the camera.** Its window bays are single flat panes at 4-5 m, with no
  frames or mullions.
- **The ridge line is mostly behind the HUD** (mirror, gap box and plate) at the centre of the frame. Only the far
  bay-side ridge on the right reads, and it is faint.
- **Floors below road level show mainly as lit fronts further down and to the right.** The near downhill blocks show
  only their roofs below the rail. From a road-level camera you can't look down their faces.

**Touge**
- **The lattice is a strong, regular pattern on the touge.** It is very readable, but it is a new look there. Austin may
  prefer it only on the Wangan skyline.

**Tri budget**
- Street v2 is about 45k env tris, mostly the far tier blocks; it could be cut with lower far LODs. It is over the old
  guide, though Austin has said there are no hardware limits.

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
