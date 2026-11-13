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

Scene triangles (env plus road grid, cars excluded): touge 7.7k, street 15.9k, wangan 14.5k. The road grid accounts for about 2.6k / 3.5k / 5.3k of those. Street and Wangan are over the ~12k guide. Fewer shop rows or a 2 m road grid would bring them under.

## Open points
- The course is unchanged in all three: the same 45 m straight into HP L (R 14 m), so the HUD reads HAIRPIN L everywhere. A real Wangan would more likely be a fast sweeper. That's a Design / Gordon call.
- In the game, road width, lane lines and dressing live in Gordon's files (`display.json` lane_width_m, `touge_dressing.gd`). Nothing of his is edited here.

## Rebuild
`./run.sh` paints the textures, builds the Blender kit, stages the project (symlinks from `../resource_meters/godot`, which must already be staged by its own `run.sh`), renders all three and makes the sheet. Use `SKIP_ASSETS=1 ./run.sh` for renders only, and `ONLY=touge ./run.sh` for a single district.
