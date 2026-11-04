# Mazda MX-5 (ND, soft top): lean car for Midnight Apex (`mx5`)

**Status: DETAIL PASS done (2026-11-04), waiting for Austin's review.** Clay signed off by Austin the same day ("Great
pass. Go for detail."). Not committed or pushed. Game files: `assets/cars/mx5/` (`car_mx5.glb`, `car_mx5.tscn`).
Pipeline is a copy of the GR Corolla build (`art/vehicles/gr_corolla/`, the other Dimensions.com SVG car), clay and
detail stages, adapted for a closed soft-top roadster. Rebuild: `BLENDER=<blender 4.2> ./make_all.sh`.
Detail pass: see **Detail pass** below; the clay sections that follow are the signed-off clay record.

## Blueprint source
Dimensions.com "Mazda MX-5 Miata - Soft Top" **vector SVG** (1000×625 units), supplied by Austin.
- URL: https://cdn.prod.website-files.com/5b44edefca321a1e2d0c2aa6/671bed39359eabce94a53c20_Dimensions-Transport-Sports-Cars-Mazda-MX-5-Miata-Soft-Top.svg
- Saved as `bp/mx5_dimensions.svg`. **Local only** (gitignored; Dimensions.com licence is non-commercial, no
  redistribution). So are the rasters (`bp/raster_*`, `bp/work_*`) and every render that reproduces the drawing
  (`renders/mx5_bp_overlay_*`, `renders/mx5_clay_34_bpcheck_*`, `renders/raw/`). Download the SVG again to rebuild.
- Layers as on the GR: `2D$AG-OUTLINE` (4 closed silhouettes = IoU truth), `2D$AG-TRANSPORT` (body/DLO/lamp/wheel
  lines, regions classified by seed points in `bp/extract.py`), `2D$AG-DETAILS` (texture only), `2D$AG-DIAGRAM` (ground).
  This SVG has **no** dimensions layer.

**Generation: ND (2016+, ND1/ND2 share the body).** Read from the drawing: slim swept LED headlamps running back
along the fenders, large low trapezoid grille with a horizontal-bar mesh, round tail-lamp rings inside thin swept
tail lamps, fixed headlamps (no pop-ups: NA only), front-fender turn repeater, twin exhaust pipes on one side, and the
proportions: length 3,915 mm, wheelbase 2,313 mm (ND spec 2,310), height 1,237 mm (ND soft top 1,235), body width
1,735 mm. NC is 4,020 long / 2,330 wheelbase; NA/NB are ~3,950 / 2,265 with different lamps. Headlamps are fixed, so
there is no pop-up handling: they get the A.2.8 light molding (30 mm pocket + lamp-cap floor) like the other cars.

**Views:** side = car's right, nose RIGHT; plan nose right, image top = car left; front: car left on the image right;
rear: car left on the image left (all the same as the GR drawing). Ground v = 237.54 (side, front), 483.475 (rear).

**Scale:** S = 3.915 m (published ND length) / side-silhouette length = **7.106 mm per SVG unit**.

| Check | Drawing | Published ND |
|---|---|---|
| Length | 3,915 (by construction); plan 3,916 | 3,915 |
| Wheelbase | **2,313** | 2,310 |
| Height | 1,237 (side), 1,235 (front) | 1,235 |
| Width | body 1,734 (plan half-width .867); 1,925 with mirrors | 1,735 |
| Tyre | r .308 (circle fit) → 205/45R17 | 205/45R17 (Club/Sport) |
| Track | tyre centres y ±.746 → 1,492 | 1,495 F / 1,505 R |

## Clay pipeline
1. `bp/rast.py` + `bp/layers.py`: rasterise the layers (6 px/unit).
2. `bp/extract.py`: vector silhouettes, wheel circle fits, region classes, `bp/curves.json`, `renders/raw/line_classes.png`
   (seed points picked on `bp/work_reg_*.png` from `bp/regions_map.py`).
3. `bp/fair.py`: faired curves (`fair_curves.json`): ZB, ZT, ZBELT (hood-fender line → fender top → cowl → door belt →
   soft-top base → deck shut line), Z5 (glass top / A-pillar / share), W, Y5 (hood edge / screen edge / glass top /
   soft-top edge / trunk edge), front/rear envelopes (mirrors bridged).
4. `parts/mx5_geo.py`: 9-point half sections, **39 stations** (cabin 0.15 m incl. glass rear, header and cowl;
   arches 0.15 m; ends 0.08 m; soft-top end + deck start anchors).
5. `build_mx5.py` (headless Blender): one loft nose → tail with the closed soft top in it, one EXACT boolean for the
   pockets (headlamps, grille, side intakes), mirrors, twin exhaust, liners, floor, wheels, struts, rig, 9-pose clearance,
   `out/mx5_clay.blend` + `.glb`.
6. `render_only.py` / `parts/render_mx5.py` (Workbench), `bp/iou.py`, `bp/deliver.py`, `bp/feature_check.py`
   (drawing lines over the clay orthos), `threeview/` (copies of `lean_common/threeview`), `bp/deliver_check.py`.

Clay materials: paint .66 grey, glass .16, **soft top .30** (so it reads apart from glass and paint), trim .08, under black.

## Clay results
**IoU** (vector OUTLINE vs clay triangles, car frame, 2 mm/px, no fitting): side **0.978**, top **0.993**,
front **0.971**, rear **0.953**: PASS (`out/bp/iou.json`). Feature lines (DLO, windshield, belt, grille, lamps, rear
window, exhaust) checked on `renders/raw/feature_*.png`.

**Triangles: 1,690 total (cap 2,000).** Mono body 1,478 = loft + pockets 1,348 (loft 1,272), mirrors 40, twin exhaust 32,
arch liners 56, floor 2; wheels 144 (4 × 10-sided); struts/arms 64; headlamp glow FX 4 (hidden). `out/tri_count.txt`.

**Rig** (same as the GR / lean cars, Godot `VehicleBody3D` / `VehicleWheel3D`):
- `MX5-vehicle` root (ground, mid-wheelbase) → `MX5_Body` (one mesh, origin at the COM estimate **x 0.0, z 0.45**:
  ND is ~50:50, EST), `Hub_FL/FR/RL/RR-wheel` empties at the hub centres, `Steer_FL/FR` (local Z) → `MX5_Wheel_XX`
  (origin = hub, spins about the axle), `Susp_XX` follow nodes (hub position + steer only, never spin; drive with
  `lean_common/susp_follow.gd`) → `MX5_Susp_XX` (strut + lower arm, 16 tris).
- Wheel x ±1.1567, hub z = tyre radius 0.308, tyre width 0.205, track 1.492. Lock ±30°.
- Travel: bump **35 mm F and R** (the drawn arch circle, r .354, is only ~4.6 cm above the tyre, so less than the
  4–5 cm default, per A.2.7), droop 50 mm.

**Clearance, 9 poses** (steer −30/0/+30 × bump/static/droop): **all clear.** Tightest **4.5 mm** (FL/FR, straight
ahead, bump); rear 8.6 mm at bump. The flat 20 mm / 30 mm entries are liner inner-wall offsets (as on the GR).
`out/bp/clearance.json`, `renders/mx5_clearance_800.jpg`.

## Renders (`renders/`)
- `mx5_threeview.png` / `_800.jpg`: clay three-view, 1 px = 4.4 mm, same layout as the S2000 / GR sheets.
- `mx5_clay_front34_800.jpg`, `mx5_clay_rear34_800.jpg`
- `mx5_clay_34_bpcheck_800.jpg` (local only): 3/4 front + rear clay, side/front/rear feature-line overlays and the
  4-view silhouette overlay with IoU.
- `mx5_bp_overlay_800.jpg` (local only), `mx5_clearance_800.jpg`, `mx5_line_classes_800.jpg`.

## Clay compromises / estimates
- **Hood:** the side-silhouette top over the hood is the ND's fender peaks; the hood centre is really ~2–3 cm lower. A
  2.5–3 cm centre dip (`HOOD_DIP`) was tried, with and without a crease on the peak row, and read as dents at this
  station density, so the clay hood is flat at fender height. Fender peaks are left to the AO/texture pass.
- **Body sides are slab-like:** the ND's sculpted side (front-fender sweep down into the door, rising into the rear
  fender) cannot be held by a 9-point section; it is panel-line / AO work for the detail pass.
- **Tail:** reads boxy in 3/4 (big flat rear face, vertical rear corners); rear IoU (0.953) is the lowest view.
- **Mirrors:** 3-ring 20-tri wedges, a bit small and blocky against the front-view outline.
- **Soft top:** one surface in the loft. The rear window is a glass band on the crown rows (x −1.22 … −0.95), the
  quarter behind the door glass is soft-top material; no fabric seams or bows (texture).
- **Estimated:** COM (0.0, 0.45), soft-top/rear-window x ranges, mirror ring sizes, exhaust outer pipe (only the inner
  pipe is a clean region in the drawing; the outer one is placed one pipe pitch, 80 mm, further out). The drawing puts
  the twin pipes on the car's right; kept as drawn.
- **Simplified pockets:** headlamp (8 pts, Fourier-smoothed), grille (8-pt Douglas–Peucker trapezoid), side intakes
  (6 pts). Tail lamps, reflectors, plate, fog/bumper slots: texture.
- **Shading QC:** 52 of 608 loft quads are non-planar by more than 5 %; worst 30.8 % at the cowl/A-pillar base and the
  soft-top quarter (triangulated anyway). No flipped or degenerate faces.
- **Photo check (A.1.3):** done in the detail pass (see below).

## Detail pass (2026-11-04)
Same stage as `gr_corolla/build_gr_detail.py`: the signed-off clay geometry, rig and budget + UVs, baked AO, a painted
1024² body texture, a 256² parts atlas, head + tail lamp glow FX, PSX fake-shine materials and a game .glb.
```
python3 bp/vectors.py                                            (cd bp)  blueprint VECTORS for the painter
blender -b --factory-startup -P build_mx5_detail.py -- --geo-only        geometry, 9-pose clearance, clay frames
blender -b --factory-startup -P build_mx5_detail.py -- --render          UVs, AO, textures, .blend/.glb, textured renders
MX5_OUT=detail python3 bp/iou.py && python3 bp/deliver_detail.py  (cd bp)
blender -b detail/mx5_detail.blend -P threeview/render_views_detail.py -- mx5d xleft && python3 threeview/compose_detail.py
```
(or the detail half of `make_all.sh`; `render_detail_only.py` re-renders from `detail/mx5_detail.blend`).

**Files**
- `build_mx5_detail.py` (imports `build_mx5.py` as the clay), `bp/vectors.py` (→ `bp/feature_vectors.json`; the
  ND's maker-emblem ovals, front and rear, are dropped and never painted), `tex/make_body_mx5.py`,
  `tex/make_parts_mx5.py`, `tex/make_env.py`, `tex/quant.py`, `parts/psx_mat.py`, `parts/render_detail.py`,
  `bp/deliver_detail.py`, `threeview/render_views_detail.py` + `compose_detail.py`, `lineup/*_mx5.py`,
  `godot/make_tscn.py`. All copies of the GR detail scripts with MX-5 names, regions and livery.
- `detail/mx5_detail.blend` / `.glb`, `detail/tri_count.txt`, `detail/bp/{iou,clearance,rig_meta}.json`,
  `detail/tex/` (`mx5_body.png` 1024², `mx5_parts.png` 256², `mx5_glow.png` 128×64, `mx5_env.png` 256×128,
  `body_ao.png`, `lamp_uv.json`).
- `detail/renders/`: `mx5_detail_threeview.png` / `_800.jpg`, `mx5_detail_front34_ref.png` / `_800.jpg`,
  `mx5_detail_rear34_ref.png` / `_800.jpg` (640×448 PSX frame, RGB555 + Bayer, 2× nearest), `_lit_800` (lamps on),
  `_closeups_800`, `_texture_800`, `_vs_clay_800`, `_clearance_800`, `_lineup_800` (5-car lineup), `_godot46_800`.
  `mx5_detail_orthos_*` (blueprint silhouette over the textured orthos) is **local only** (gitignored, licence).
- Night in-scene shot: `art/mood/tokyo_mx5/` (README there).

**Geometry** (silhouette unchanged: IoU side **0.978**, top **0.993**, front **0.971**, rear **0.953**, PASS):
- loft faces carry the un-cut loft's split normals (custom normals), so the pocket boolean no longer facets the nose;
- grille and corner-garnish pockets: Douglas–Peucker corners + planar floors; headlamp stays the Fourier light molding
  (A.2.8: 30 mm pocket, lamp art on the floor);
- **mirrors tidied:** 3 × 5-point rings (rounded housing top, swept-back outer face), 26 tris each (+12 tris total);
- FX: head **and** tail glow quads in one hidden object `MX5_FX_LampGlow` (8 tris).

**Triangles: 1,692 total (cap 2,000).** Mono body 1,476 = loft + pockets 1,334, mirrors 52, twin exhaust 32, liners 56,
floor 2; wheels 144; struts 64; FX 8 (hidden by default).
**Clearance, 9 poses: all clear,** tightest 4.5 mm (FL/FR, straight ahead, bump), rear 8.6 mm at bump (unchanged).
**Rig** unchanged (`MX5-vehicle`, `MX5_Body` at the COM estimate, `Hub_XX-wheel`, `Steer_FL/FR`, `Susp_XX`).

**Paint: "Daybreak Yellow" (made-up name), RGB 226/182/38.** Why: the lineup is already WRX blue, S2000 red, BRZ blue
and GR white. Soul Red is the ND's signature colour, but it would put a second red roadster next to the S2000. Yellow is
the one warm, high-value colour left. It is also period-correct for a late-90s game: it nods to the NA's 1992 Sunburst
Yellow. And it stays readable against the navy / mercury night palette and under the pale sodium lamps (see
`detail/renders/mx5_detail_lineup_800.jpg` and the Tokyo shots).

**Texture (A.3)** `tex/make_body_mx5.py`, RGB555 + 4×4 Bayer, per-view 2 mm/px canvases sampled by the owning view:
- black fabric soft top (own near-matte material `MX5_SoftTop` on the same texture, faint weave, seams darker);
  black windshield frame (photo check); body-colour mirrors with dark glass faces; black thin sill strip, lower lip
  and rear diffuser band;
- panel / shut / DLO lines = TRANSPORT vectors, creases = DETAILS vectors (faint); lamp-internal detail lines inside
  the headlamp outline are left to the lamp atlas;
- **clay weak spots, painted as form shading from the DETAILS vectors:** (1) hood: fender-peak crest highlight +
  valley just inboard + shallow centre dip, along the top-view hood creases; (2) sides: the door scoop under the
  rear-fender crest line (highlight above, shadow below, fading to the front of the door), bright arch-flare lips,
  tucked rocker under the lower door line; (3) tail: highlight band above the tail crease, darker below, corners rolled
  off by normal (no seam where the owning view changes);
- lamps: ring tail lamps (red lens, lit LED ring, dark core, glint) + smoked outboard bars with a lit line; headlamp
  art in the parts atlas (smoked housing, one round projector with a lit LED ring where the drawing's circle is, LED
  line along the top edge); dark corner reflector recesses; grille black with horizontal slats + the drawing's cell
  grid in dark grey; fender side garnish chrome;
- flat made-up plates "RD 15-89" (front over the grille, rear in the drawing's plate box); made-up badge (chrome oval
  ring + chevron) where the emblem was; small illegible chrome script bar on the tail; no real brands.
- parts atlas: 205/45R17 sidewall with made-up "SOLANA" lettering (mirrored per side so it reads on both), gunmetal
  5-twin-spoke (10-spoke) 17" rim, tread strip; glow sprite atlas (warm head, red tail).
- Materials: `MX5_Paint_Body` (spec .26, down from the GR's .42: on this high-value yellow the key highlight on the
  faceted rear fender read as a white glyph), `MX5_SoftTop`, `MX5_Glass`, `MX5_Under`, `MX5_Lamp`, `MX5_Wheel`,
  `MX5_FX_Glow`; Principled in the .glb.

**Photo check (A.1.3),** public Wikimedia Commons photos of a Soul Red ND (2015 "Rubinrot-Metallic" side / front / rear
set and a 2016 Grand Touring front-left / rear-left pair), downloaded to a scratch folder only (not in the repo):
- matches: proportions and ride height, long low nose and short tail, wheel size vs arch, door-mounted body-colour
  mirrors, black soft top, slim headlamps with one round projector, wide low grille with horizontal slats, ring tail
  lamps with outboard bars, twin pipes, black lower lip and thin black sill;
- **fixed after the check:** the first textured pass painted the windshield frame / A-pillars body colour (the
  drawing has no colours); the photos show them black, so they're black now. The drawing's rear corner reflector
  regions were first painted as big red discs; the photos show dark recesses with slim reflectors, so they're repainted
  that way. The grille is painted as horizontal slats (photos) rather than the GR's honeycomb, with the drawing's cell
  lines kept in dark grey;
- not fixable in texture: the real fender peaks stand clearly proud of the hood, and the door is visibly concave.
  The clay keeps both flat (signed off), so the detail pass only paints them; at a low 3/4 angle the hood still reads
  flatter than the photos.

**Godot 4.6.3 check** (scratch copy of the project, Compatibility / OpenGL3 on llvmpipe, `import/blender/enabled=false`
as for the GR): `car_mx5.glb` imports with `MX5` as a VehicleBody3D and four VehicleWheel3D `Hub_XX`; `car_mx5.tscn`
loads with no script errors, settles at body y 0.000, drives and steers (22.9° at steering .40), struts follow travel
and steer, glow hidden. Raycast wheels sit ~2 cm under the static hub at rest (wheel y .287 vs .308), as on the WRX/GR.

**Weak spots (honest)**
- Hood centre dip / fender peaks and the door scoop are **paint only** (form shading). They read straight on and in
  the orthos, but less so at low 3/4 angles and in motion; the silhouette over the hood is still flat.
- The front fender behind the headlamp shows faceting under the key light, and front-view lines get stretched where the
  nose wraps into the fender (a few dark dashes over the fender top).
- Spec on the yellow had to come down (.26 detail / .15 in the Tokyo scene). At GR values a jagged white highlight
  (a "glyph") appeared on the faceted rear fender. The paint is a little less glossy than the GR as a result.
- Soft-top islands share UV islands with paint at their edges: with LINEAR filtering (the Tokyo scene) thin olive seams
  show along the top's edges. With the PSX nearest filter they don't.
- Mirrors are tidier but still small next to the photos (kept to the drawing's front-view extents).
- Front bump clearance stays at 4.5 mm (35 mm travel, drawing-limited); COM is still an estimate (0.0, 0.45).
- The door-handle recess comes straight from the drawing's TRANSPORT outline and reads a bit large and cartoonish.
