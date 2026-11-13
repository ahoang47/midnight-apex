# District looks (unapproved draft)

Austin, 2026-11-13: "The road also reads really wide. This works for wangan and maybe street but not for touge. Mind drafting up the looks for all 3 districts with this in mind, with the current HUD?" Follow-up: Wangan reuses the current E3B road as is, with its width, and gets its lane lines back.

Each frame is the E3B Entry chase frame (same camera, cars, chevrons and HUD state as `../resource_meters/e3b_full.png`). It's rendered in Godot 4.6.3 with the project's GL Compatibility renderer, which is what the Mobile setting falls back to on the box. The 3D is drawn at 640×480 with RGB555 + Bayer and a 2× nearest upscale. The E3B HUD (`hud.gd` + `resource_stack.gd`, unchanged) is drawn pixel-hard at 1280×960. Floating OUT / MID / IN markers are off everywhere, and the coloured chevrons stay on the road.

| Frame | Road | Character |
|---|---|---|
| `touge.png` | **6.0 m** asphalt (half 3.0), 2 narrow lanes, **no painted lines** (E3B no-line touge road texture). Cars at ±1.45 m, chevrons scaled to 0.58. | Inside: 0.7 m gravel shoulder, rock cut slope with a shotcrete toe and weep holes, grass lip, cedars on top. Outside (the drop): 0.5 m verge, W-beam guardrail tight to the edge with amber reflectors, slope falling away, cedar tops below. One sparse #F0C894 sodium lamp every 48 m. |
| `street.png` | **8.4 m** (half 4.2), 2 lanes with Gordon's lined street road (dashed centre, yellow edges), 0.15 m kerbs, 2.6 m pavements. Cars at ±2.0 m, chevrons 0.78. | Rows of 2–3 storey shops (glass fronts and shutters, sign bands, vertical boards, AC units, awnings), concrete utility poles with crossarms, a transformer and a small sodium lamp, sagging overhead wires along and across the street, and vending machines. Sign words are generic (喫茶, 酒店, スナック, ラーメン …), with no brands. Boards are dimmed so nothing is brighter than the car. |
| `wangan.png` | **11.9 m**: the E3B road as is (half 5.95, 3 × 3.3 m lanes), with the original lined touge-road texture (edge lines and dashed dividers back). Cars at ±3.3 m, chevrons 1.0. | Concrete shoulders, jersey barriers on both edges, deck fascia with the drop below, tall sodium lamps on the barriers with arms over the lanes (staggered every 24 m), and distant city towers plus the skyline band across the bay. |

`districts_sheet.png` shows all three side by side with labels.

Every lamp head and glow is the single pale sodium #F0C894. The palette is TXR navy fog (#0B172B) with Mercury-teal and cream window lights. There is no warm wash and no neon ribbons.

The road strips here use a 1 m × 1 m grid instead of Gordon's 3 m × 2 m. This keeps the painted lines from wobbling under PSX affine UVs near the camera.

## Assets

**Reused**
- Gordon / line-preview: course, road textures (`touge_road` no-line E3B override, `street_road`), `touge_verge`, cedar cards, the sodium lamp mesh, skies and ridge/skyline bands, the cars (MX-5 player, S2000 rival) and shaders.
- Packs (CC0, via `/workspace/district_scenes/assets`): the Urban Stacked `Jersey_barrier` geometry (re-textured), and the Kenney Retro Urban Kit rock, grass, windows, wall, garage, concrete and tiles textures. The 3D Retro Shacks concrete-barricade texture and the Urban Stacked jersey-barrier texture serve as paint bases.

**New** (`blender/build_assets.py` → `godot/assets/env/*.glb`; textures from `tex_src/make_tex.py` → `godot/art/env/`)

| Asset | Tris |
|---|---|
| `touge_cutslope_a/b` | 48 |
| `touge_guardrail` (4 m) | 26 |
| `street_pole` | 126 |
| `street_shop_0..3` | 118–132 |
| `street_vending` | 8 |
| `wangan_lamp` | 42 |
| `wangan_jersey` | 44 |
| `wangan_tower_0..2` | 8 |

Material names starting `Emit_` draw full-bright. Everything else is unlit through Gordon's scroll shader, with fog.

Scene triangles (env plus road grid, cars excluded; Austin has since confirmed there are no hardware limits): touge 7.7k, street 15.9k, wangan 14.5k. The road grid accounts for about 2.6k / 3.5k / 5.3k of those. Street and Wangan are over the ~12k guide. Fewer shop rows or a 2 m road grid would bring them under.

## Pass 2 (Austin, 2026-11-13): touge grade + cat and mouse

**Touge grade.** The touge road climbs at **8.5 %** up the approach. It eases over a crest inside the hairpin (0 % at about 75 % of the arc), then falls at 5 % out of it. Through the hairpin it banks up to 6 %, with the outside high. Everything reads its height from one `elev(s, d)`: the road grid, verges, cut-slope modules and guardrail (both pitched to the grade), cedars, the lamp, the cars (pitched and rolled), the chevrons (each corner sits on the road), and the chase and rear-view cameras. Street and Wangan stay flat. `touge.png` is re-rendered on the grade.

**Cat and mouse** is art presentation only; scoring is unchanged.
- `touge_mouse.png` (leading, rival 6.5 m behind, slightly inside). Same chase camera as every other frame. Faked lighting, no dynamic lights:
  - The chaser's beam is a long additive `headlight_throw` decal (17 m) that runs under and past the player.
  - The player's own shadow is thrown forward into that beam.
  - A rear light on the player car (`shaders/car_lit.gdshader`, a copy of the car shader plus one stepped, cone-limited halogen light) lights the tail and rear deck.
  - Bigger head glows on the chaser make it read in the rear-view inset.
- `touge_mouse_far.png` (rival 24 m back): the rear view shows only the headlight pair, and the gap bar is near full.
- `touge_mouse_pulled.png` (alternative): the same shot with the camera pulled 2.2 m back and 0.9 m up. It shows more of the beam around the car, but the rival's nose still sits under the HUD band, and the player car gets smaller. I kept the standard camera for `touge_mouse.png` so the camera family stays identical.
- `touge_cat.png` (chasing, rival 11 m ahead in the player's line): the taillights sit in the chevrons, with slightly bigger tail glows and a red tail wash on the road. Standard camera.

**Prominent tie-gap.** `godot/scripts/hud/resource_stack.gd` is a copy of the E3B HUD with one addition, `_paint_e_gap_big()`. When the state has `gap_s`, the tie-gap box is wider and taller. It carries a role tag (MOUSE LEADING / CAT CHASING / TIE), the gap in seconds and an 8 px bar instead of 5 px, with the same colours and position. Every frame here, Street and Wangan included, uses it so the HUD stays identical across districts.

`consistency_sheet.png` is a 2×2 of touge_mouse, touge_cat, street and wangan.

Rebuild the pulled-camera alternative with `MOUSE_CAM_TEST=1 ./run.sh`. Use `FRAME=touge_cat.png` to render one frame.

## Open points
- The course is unchanged in all three: the same 45 m straight into HP L (R 14 m), so the HUD reads HAIRPIN L everywhere. A real Wangan would more likely be a fast sweeper. That's a Design / Gordon call.
- In the game, road width, lane lines and dressing live in Gordon's files (`display.json` lane_width_m, `touge_dressing.gd`). Nothing of his is edited here.

## Rebuild
`./run.sh` paints the textures, builds the Blender kit, stages the project (symlinks from `../resource_meters/godot`, which must already be staged by its own `run.sh`), renders all three and makes the sheet. Use `SKIP_ASSETS=1 ./run.sh` for renders only, and `ONLY=touge ./run.sh` for a single district.
