# Touge course environment (authored) — Arthur, pass 2 (clipping pass, Austin pt364u)

Authored Blender terrain built around Gordon's exact road export (road_surface.glb, s −96..1104, 7.5 m wide; lot = LotFloor).
The road surface stays code-generated. Every file is placed at the **identity transform** (world space, +Y up, metres).
Source: `art/env/touge/touge_env.blend`; rebuild scripts: `art/env/touge/build_scripts/` (terrain.py → post.py → assemble.py →
paint.py → blender_build.py; check_props.py is the clipping sweep). `SCRATCH_ONLY_main_gd_env_hooks.diff` there is the
verification hook Arthur used in a scratch copy of main.gd — reference only, not for scripts/.

## Files (assets/env/touge/)
| file | s range (course s, m) | tris | draw calls | materials |
|---|---|---|---|---|
| touge_t01.glb | −96 – 91.0 | 6,222 | 8 | touge_hill, touge_cutface, touge_cutrock, touge_gravel, touge_concrete, touge_guardrail, Emit_reflector, lamp_post |
| touge_t02.glb | 91.0 – 190.3 | 2,475 | 7 | as t01 without touge_concrete |
| touge_t03.glb | 190.3 – 281.3 | 2,708 | 8 | as t01 |
| touge_t04.glb | 281.3 – 373.9 | 1,606 | 7 | as t02 |
| touge_t05.glb | 373.9 – 583.2 (lot excluded) | 4,133 | 7 | as t02 |
| touge_t06.glb | 583.2 – 674.2 | 3,042 | 8 | as t01 |
| touge_t07.glb | 674.2 – 736.9 | 1,503 | 8 | as t01 |
| touge_t08.glb | 736.9 – 827.9 | 2,885 | 8 | as t01 |
| touge_t09.glb | 827.9 – 920.5 | 2,360 | 7 | as t02 |
| touge_t10.glb | 920.5 – 1104 (incl. the turn-4 underpass canyon 1036–1104) | 6,061 | 8 | as t01 |
| touge_lot.glb | 501.24 – 563.24 (turn-5 turnout, inside/left) | 704 | 4 | asphalt, touge_gravel, touge_cutface, touge_hill |
| touge_gallery_a.glb | walls 904 – 975 (R) + turn-5 deck 467 – 546 | 1,062 | 1 | touge_concrete |
| touge_gallery_b.glb | walls 975 – 997 (L) + turn-5 deck 439 – 467 | 367 | 1 | touge_concrete |
| touge_gallery_c.glb | walls 1068 – 1104 (run-out, L) + turn-4 bridge deck 319 – 399 | 442 | 1 | touge_concrete |
| touge_backdrop.glb | far ring 100 m → 2,600 m from the centreline (no s) | 1,768 | 1 | touge_hill |
| **total** | | **37,338** | 98 | (reference procedural build: 21,583 tris / 108 draws) |

Budget (Austin-approved): ~5k–10k tris and <50 draw calls per turn section, collision excluded → **all sections pass**
(largest t01 6.2k and t10 6.1k; the rest 1.5k–4.1k; max 8 draw calls). A section = one terrain mesh (up to 7 materials) + child
mesh `<section>_lamps` (lamp_post, vertex colour). touge_backdrop is drawn always (1 draw call, 1.8k tris).

Baked from Gordon's reference placement: 25 road lamps (lot lamps excluded — `turnout_lot/lot_lamps.glb` has them) and 300
guardrail segments. Lamp posts now run down to the ground (they stood 0.5–0.65 m above the drop-side verge) or onto the deck
lip on bridges. Each lamp head has an Empty `lamp_head_###` at the head's world position (lights / glow sprites).

## Collision proxies
`<name>_col.glb` for the 14 course files (not for touge_backdrop): terrain/walls/decks only (no lamps, rails, reflectors),
coplanar-dissolved and triangulated, POSITION + NORMAL only, no material. Tris: t01 1150, t02 600, t03 922, t04 283, t05 731,
t06 856, t07 325, t08 938, t09 512, t10 1388, lot 181, gallery_a 219, gallery_b 232, gallery_c 344.

## Kit (assets/env/touge/kit/)
| file | tris | material | notes |
|---|---|---|---|
| lamp_post.glb | 52 | lamp_post | env_vertex_lit: vertex colour = albedo; head (0.941,0.784,0.580), luma ≥ 0.5 = full-bright; post (0.16,0.16,0.18). Base at y = 0 |
| rail_seg.glb | 26 | touge_guardrail, Emit_reflector | the existing touge_guardrail module, re-exported |
| gallery_bay.glb | 10 | touge_concrete | 1 m-high pilaster, scale Y to the bay height; local +X points away from the road; every 8 m in the gallery files |
| line_chevron.glb | 2 | line_chevron | flat quad 0.9 m (X) × 1.0 m (Z), points **+Z**, origin at its centre on the ground (y = 0): lift ~0.05 m and scale X/Z in code (1.9 × 2.3 m now); code tints it (OUT/POW green, MID/HAN yellow, IN/EN red), alpha blend |

## Materials and textures (no embedded images)
The glbs carry **no embedded images** (exported with images off). Code maps each surface by its material `resource_name` and
loads `res://assets/tex/kit/env/<name lowercase>.png`. Terrain follows scroll_vertex_lit: UV0 only, U = 0..1 across / up the
face (repeats, `fract`), V = metres along s (tiled in-shader); no vertex colour, no UV1; AO / gradients baked into textures.
| material | where | U | V tile (m) | texture |
|---|---|---|---|---|
| touge_gravel | road skirt, verge, inside < 0.7 m | e/8 | 4 | existing |
| touge_cutface | inside cut 0.7–8.7 m (behind the lattice) | (e−0.7)/8 | 8 | new |
| touge_cutrock | steep faces (normal.y < 0.45): canyon terrace faces, cliffs | height above road/8 | 8 | existing |
| touge_hill | hillside, drop side, canyon benches, backdrop | e/8 (backdrop: x/8, V = z m) | 8 | new |
| touge_concrete | gallery walls, decks / soffit / fascia / lip, bays, drop-flip wing walls | height/8 or across/8 | 4 | new |
| asphalt | ground under the lot floor edge | (abs(d)−W)/8 | 8 | asphalt.png (copy of turnout_lot/lot_floor_lot_asphalt.png) |
| lamp_post | lamp posts (child mesh) | — | — | env_vertex_lit, vertex colour (no texture) |
| touge_guardrail / Emit_reflector | rails | as rail_seg | — | existing; Emit_* = emissive (cel_k 0) |
| line_chevron | chevron kit | 0..1 | — | line_chevron.png |
(e = metres out from the road edge; d = signed metres from the centreline. V is course s, so terrain textures scroll with
scroll_m like the procedural bands did.)

## Geometry notes (pass 2)
- One continuous constrained heightfield; road-aligned rows reproduce P_OUT / P_IN at the road edge (exact road-edge vertices:
  no gap / overlap). Under the road footprint the terrain is dropped, or sits 0.15 m below where it fills under an overhead deck.
- **Lattice side under an overhead road** (galleries a/b, turn-4 crossing): the lower road owns the ground out to e = 8.8, so
  the whole lattice module (W+0.7 → W+8.7, top 7.6) stands on its own cut and the gallery wall rises behind its top cap
  (was 3.45: modules were buried in the wall). The wall is split into 9 bands (smooth per-vertex light).
- **Drop-side flips** use Gordon's exact `course.drop_runs` (63, 253, 463, 647, 729, 799, 975; the rail reference was 1–3 m late).
  Lattice modules are 4 m and take the side of their centre, so the cut runs 2 m past each flip; that run and the transition are
  faced as a concrete wing wall (fixes the bare wedge at s ~975 beside the gallery-b wall).
- **Turn-4 underpass canyon** (s 1036–1104): stepped cut — 7 m rock faces (cutrock) with 1.4 m grass benches, ±0.9 m ledge
  jitter along s — on both sides, instead of one 30–45 m sheer face. Inside keeps P_IN to e = 16 so the lattice and the cedar
  band (9.5–15.5 at 7.6) stand on ground before the first step. Turn 4 there is a bridge: deck 319–399 with a 1.6 m lip.
- **Backdrop**: two rings share the 100 m boundary vertex for vertex (no seam): 100 → 700 m falls into a valley / climbs the hill,
  then a ridge line; 700 → 2,600 m far ranges past the 2,000 m overview far plane. No hard edge with fog off.
- Decks: soffit/fascia under the full road width; 1.6 m lip (rail W+0.45, delineators W+0.5/0.62, lamp posts W+1.2) wherever
  the road edge has no ground.
- Checks on the final build: 0 terrain points above any road surface; edge gaps only under the three decks; lattice faces clear
  of terrain everywhere (≤ 6 cm at the module foot); rails / delineators / lamps on ground or deck lip.
