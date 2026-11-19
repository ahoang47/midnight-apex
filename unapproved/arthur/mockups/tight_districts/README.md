# Tight districts: cat-and-mouse frames (unapproved mockup)

Austin, 2026-11-15: "I'm thinking of switching focus to the cat and mouse only gameplay, but keeping the distinct district
feel. So the roads do need to be a little tight to allow that feel. No need to draft up a full gameplay, one frame render is
fine. Will also need something for street."

This folder has one still per district in the cat-and-mouse **CAT (chasing)** presentation. Each still uses:
- the standard B.5b chase camera
- the rival 11 m ahead in the player's line, taillights in the chevrons, and a red tail wash on the road
- the districts mockup's big tie-gap box (CAT CHASING, −0.44 s)
- the E3B HUD

There is no pass or side-by-side. The look is Cel A soft, rendered in Godot 4.6.3 with GL Compatibility. 3D is at 640×480 with RGB555 + Bayer applied last. The HUD is drawn afterwards at 1280×960, with no shading and no ink. There are no floating OUT/MID/IN markers (chevrons only), no LIMP tag, a single #F0C894 sodium, and TXR navy fog #0B172B. This is a mockup, not a playable build.

| File | Road | |
|---|---|---|
| `touge_cat.png` | **6.0 m** (unchanged) | Reference. Same frame as `../districts/touge_cat.png`, re-rendered in Cel A soft. |
| `wangan_tight_cat.png` | **7.5 m** wall to wall (was 11.9 m, 3 lanes) | 2 × 3.5 m lanes + 0.25 m marginal strips, on a gentle R 85 m sweeper (SWEEPER L) |
| `street_tight_cat.png` | **5.8 m** kerb to kerb (was 8.4 m) | Two-way back street, no centre line, 1.0 m pavements, blind 90 L at the end (90-DEGREE L) |
| `tight_districts_sheet.png` | 1×3: touge, wangan, street, labelled with widths | |

## Why these widths
- **Wangan 7.5 m.**
  - This is two real expressway lanes: 3.5 m each, the upper end of Shuto practice, which runs 3.25–3.5 m. The marginal strips are only 0.25 m, and the cast parapets stand right on the road edge on both sides. There is no shoulder.
  - The cars sit at ±1.75 m. Following in one lane is the natural line. A pass means committing the whole other lane next to a wall, so it reads as hard but possible.
  - It stays distinct from touge and street through the elements below.
    - It is the only district with painted lanes (white edge lines and a 6/6 m dashed divider).
    - It has tall lamps on the walls, with arms reaching out over the centre line.
    - It has an overhead sign gantry and km posts.
    - The deck is elevated, with the bay, the city and the rest of the expressway beyond.
  - I didn't go to 7.0 m. That leaves no strip at the wall foot, and the chevrons start touching the edge lines.
- **Street 5.8 m.**
  - This is a Japanese two-way back street with no centre line. Solid white 路側帯 lines sit 0.55 m in from each kerb, and there are 0.12 m kerbs and 1.0 m pavements.
  - The cars sit at ±1.25 m, so two cars only just fit side by side. A pass would mean squeezing past with mirrors over the 路側帯, so single file reads as the default.
  - It is a touch narrower than touge (6.0 m), but it feels far tighter because the shopfronts are 1 m off the kerb on both sides. Touge has walls on one side only.
  - Below about 5.5 m it stops reading as two-way.
- **Touge stays 6.0 m** as the reference.

## What changed (all marked `# TIGHT:` in `godot/scripts/district_preview.gd`)
- **District table.** New widths, lane offsets and chevron scale (wangan 0.68, street 0.55). Wangan also gets its own road texture and the wangan_two_corner star sky, and street gets its own road texture.
- **Course, in memory only.**
  - Wangan becomes a gentle S: R 85 m, 60° left then right. The road runs to s 290, so the sweeper and the rest of the deck show beyond.
  - Street becomes a blind R 10 m 90° left.
  - The touge course is unchanged.
- **Wangan dressing.**
  - wangan_two_corner parapet modules on both edges every 4 m (straight modules; over 4 m the R 85 bend is only 2 cm), plus the deck fascia and soffit.
  - Sodium lamps on the parapet tops, staggered 24 m, with sodium streaks on the bay below.
  - Piers with the crosshead cut to 72 % for the narrower deck, and two km posts.
  - The new two-lane gantry at 78 m.
  - Bay water at −16 m, the city tower cards, cranes on the right quay and the bay bridge.
- **Street dressing.**
  - The districts shops sit 1.0 m behind the kerb, with boards dimmed to 0.5 so nothing outshines the car.
  - Vending machines stand against the shopfronts, with none right beside the camera.
  - Utility poles stand on the pavement edge, with a service drop crossing the street every span.
  - The new curve mirror appears twice: at a mid-block driveway, and at the outside of the blind 90.
- **Other changes.**
  - Prop materials use the painted lossless `art/env/<material>.png` by name. Sign and km-post lettering skips the flatten.
  - The bay, fascia and soffit get Cel A soft smooth light.
  - Only the Cel A soft frame is written.

## Assets
**New** (Blender script `blender/build_tight.py`, which reuses the Builder from `../../experiments/wangan_two_corner/blender/build_wangan.py`; textures from `tex_src/make_tex.py`):

| Asset | Tris |
|---|---|
| `wangan_gantry_2l`: the Wangan gantry re-proportioned for 7.5 m (posts outside the walls, route sign + CURVE board, sign lamps) | 168 |
| `street_curvemirror`: orange curve mirror on a square pole, painted convex face (never reflective) | 24 |
| textures: `art/wangan_tight_road.png` (7.5 m, 48 m tile, staggered pools), `art/street_tight_road.png` (5.8 m, 24 m tile, trench patch, utility cover, gutter grates), `art/env/street_curvemirror.png` | — |

**Reused**
- From `experiments/wangan_two_corner`:

  | Asset | Tris |
  |---|---|
  | wangan_parapet | 28 |
  | wangan_pier | 116 |
  | wangan_kpost | 10 |
  | wangan_crane | 116 |
  | wangan_bridge | 416 |

  Also its textures: parapet, fascia, underside, pier, steel, signs, km post, silhouette, aviation / bridge lamps, water, streak, sky.
- From `mockups/districts`:

  | Asset | Tris |
  |---|---|
  | wangan_lamp | 42 |
  | wangan_tower_0..2 | 8 each |
  | street_shop_0..3 | 118–132 |
  | street_pole | 126 |
  | street_vending | 8 |

  Also the touge kit, the cars, the HUD (with its big tie-gap box) and every shader. The Cel A soft code comes from `experiments/cel_shaded`.

Scene triangles (environment and road grid, cars excluded): touge 7.7k, wangan 16.3k, street 14.3k.

## Re-render
```
./run.sh                 # textures + Blender props + import + touge / wangan / street + sheet
SKIP_ASSETS=1 ./run.sh   # renders + sheet only
ONLY=wangan ./run.sh     # one district (DISTRICT=wangan ... writes wangan_tight_cat.png)
```
`godot/` is self-contained. It is a dereferenced copy of `experiments/cel_shaded/godot` as staged on the box (districts → resource_meters → line_preview → Gordon's two-corner), with the changes above. It needs no staging and contains no symlinks. Textures that Godot extracts from the GLBs (`assets/**/<glb>_<material>.png`) are not committed, because Godot regenerates them on import.

## Weak spots
- **Wangan**:
  - The new gantry only reads as a small green sign at about 78 m. The cranes and bridge sit beyond the fog or out of frame in this camera, so the bay reads mostly as dark water, city lights and the rest of the deck.
  - The 4 m parapet joints get a crease ink line. That's believable as panel joints, but it's a bit regular.
  - The near lamp's head is above the top of the frame.
- **Street**:
  - The two curve mirrors are small at 640×480. The one at the 90 sits behind the turn sign.
  - The overhead wires mostly sit behind the mirror and HUD band.
  - The shop rows are placed straight along the course. On the inside of the R 10 corner they will crowd or overlap where the row bends. That part is out of view in this frame, and I have not checked it from another angle.
- **Tri budget.** Both new scenes are over the old ~12k guide (Austin has said there are no hardware limits).
- **Widths.** These are art proposals only. In the game the widths live in Gordon's `display.json` (lane_width_m and the dressing scripts), and none of his files were touched.
