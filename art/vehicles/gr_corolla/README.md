# Toyota GR Corolla (2022): lean car for Midnight Apex (`gr_corolla`)

**Status: DETAIL PASS done (2026-11-02), waiting for review.** Clay shape signed off by Austin earlier the same day.
Game-ready files: `assets/cars/gr_corolla/` (README there). Pipeline follows the WRX STI / S2000 / BRZ lean builds
(`art/vehicles/wrx_sti/build_wrx_lean.py`, `art/vehicles/lean_common/`). Not committed or pushed.

## Blueprint source
The blueprint is the Dimensions.com "Toyota GR Corolla Dimensions" **vector SVG**, saved as `bp/gr_dimensions.svg` (1000×675 units).
- Source URL: https://cdn.prod.website-files.com/5b44edefca321a1e2d0c2aa6/66d7707f02b335e39ad7963f_Dimensions-Transport-Compact-Cars-Toyota-GR-Corolla-Dimensions.svg
- It is free and publicly viewable.
- It replaces the earlier the-blueprints JPG preview, which is still kept in `ref/`. All tracing was redone from the SVG.

**Views in the SVG:** side, plan (top), front and rear. There are no transforms on any view.
- **Side:** the car's right side, nose to the right.
- **Plan:** nose to the right; the image top is the car's left.
- **Front:** the car's left is on the image right.
- **Rear:** the car's left is on the image left.
- **Ground lines:** v = 259.76 for side and front, 541.198 for rear.

### Line classes
The classes come from the Illustrator layers. Every stroke is the same colour, so the layers are what identify them.

| Layer | Use |
|---|---|
| `2D$AG-OUTLINE` (4 closed paths) | Body silhouette per view, including tyres, mirrors, wing and fin. This is the IoU truth. |
| `2D$AG-TRANSPORT` (311 paths) | Body, DLO, lamp, trim and wheel lines. Regions bounded by these lines are classified by seed points in `bp/extract.py`. |
| `2D$AG-DETAILS` (41 paths) | Surface creases and lamp internals. Kept for textures only; not modelled. |
| `2D$AG-DIAGRAM` | Ground lines. |
| `N-DIMENSIONS` | Dimension text and arrows. **Ignored**, except as a cross-check. |

The regions used are:
- **Side:** DLO glass, pillars, roof rail, hatch glass, wing, mirror, hood, headlamp, tail lamp, skirt, fender vent.
- **Top:** side glass, roof, windshield, hood, hood vents, wing, mirrors.
- **Front:** windshield, hood, mirrors, headlamps, grille, side intakes, lip, tyres.
- **Rear:** rear glass, wing, tail lamps, mirrors, diffuser, exhaust, tyres.

The line-class sheet is `renders/gr_corolla_line_classes_800.jpg`.

### Scale and cross-checks
Scale: S = 4.406 m / side-silhouette length = **7.7215 mm per SVG unit**.

| Check | Drawing | Published spec |
|---|---|---|
| Length | 4406 (by construction); plan view 4406.4 | 4406 |
| Wheelbase | **2657.3**; dimension text says 264 cm | 2639 (+0.7%) |
| Height | **1472.8** in the side view (shark fin), 1448.8 in the front view; dimension text says 145 cm | 1478 |
| Width | Body 1848 (half-width .924); 2074 with mirrors | 1851 |

The drawing's own geometry was kept for wheelbase and height (blueprint is truth).

## Pipeline (scripts)
`./make_all.sh` rebuilds everything (clay, then the detail pass). Clay steps:

1. **`bp/rast.py`** (uses `bp/layers.py`): rasterises each layer at 6 px per unit.
2. **`bp/extract.py`:**
   - Reads the vector silhouettes.
   - Fits circles to the wheels.
   - Labels and classifies regions.
   - Writes `bp/curves.json` and `renders/raw/line_classes.png`.
3. **`bp/fair.py`:** fairs the traced curves onto a 5 mm grid and writes `fair_curves.json` (plot in `renders/raw/fair_curves.png`):
   - arches bridged
   - antenna and mirrors bridged
   - hatch line fitted under the wing
   - DLO notches bridged
4. **`parts/gr_geo.py`:** section model.
   - 9-point half sections.
   - **35 stations:** doors 0.30 m apart, arches 0.18 m, nose and tail 0.10 m, plus anchors at the arch lips and roof end.
5. **`build_gr_corolla.py`** (headless Blender):
   - lofts one mono body, then cuts pockets with a single EXACT boolean
   - builds the wing, fin, mirrors, triple exhaust, liners, floor, wheels, struts and FX
   - builds the rig
   - runs the 9-pose clearance test
   - writes `out/gr_corolla_clay.blend` and `.glb`
6. **Then:**
   - `render_only.py` and `parts/render_gr.py` make the Workbench renders.
   - `bp/iou.py` runs the IoU gate.
   - `bp/deliver.py` makes the sheets.
   - `threeview/render_views.py` / `compose.py`: clay three-view (Workbench), adapted copies of `lean_common/threeview`.

## Clay results (signed off)
**IoU** (vector OUTLINE vs the clay triangle soup, car frame, 2 mm/px, no fitting):

| View | IoU | Gate |
|---|---|---|
| Side | **0.980** | .95 |
| Top | **0.991** | .95 |
| Front | **0.976** | .92 |
| Rear | **0.976** | .92 |

All four views pass. Results are in `out/bp/iou.json`, with overlays in `out/renders/raw/iou_*.png`.

**Triangles: 1,922 total (cap 2,000).**
- **Mono body: 1,710**
  - Loft: 1,146
  - Pockets: +414
  - Wing: 16
  - Fin: 4
  - Mirrors: 24
  - Triple exhaust: 48
  - Arch liners: 56
  - Floor: 2
- **Wheels:** 144 (4 × 10-sided)
- **Struts and arms:** 64
- **Headlamp glow FX:** 4, hidden

**Aero built into the mono body:**
- front lip, in the loft
- grille and big side intakes, as pockets
- flared arches, with 4-step arch lift and liners
- fender vents and hood vents, as pockets
- roof wing with endplates
- shark fin
- rear diffuser pocket
- triple exhaust
- light headlamp molding (A.2.8): 30 mm pocket with a lamp-cap floor

**Rig:**
- `GRC-vehicle` root.
- `Hub_FL/FR/RL/RR-wheel` empties.
- `Steer_FL/FR`.
- `Susp_XX` nodes driven by `godot/susp_follow.gd`.
- Body origin is at the estimated centre of mass: x +0.26 m (forward of mid-wheelbase), z 0.52 m.
- Steering lock is ±30°.
- Wheel and track data:
  - Wheel x ±1.3286; hub z = tyre radius 0.321
  - Tyre width 0.235; track 1.570

**Clearance, 9 poses** (steer −30/0/+30 × bump/static/droop; bump F 35 mm / R 45 mm; droop 50 mm). **All clear.**
- Tightest overall: **7.6 mm**, FL/FR, straight ahead at bump.
- Rear tightest: 8.8 mm at bump.
- At full lock with bump: 16.8 mm.
- Details are in `out/bp/clearance.json` and `renders/gr_corolla_clearance_800.jpg`. The flat 20 mm (front, at lock) and 30 mm (rear, droop)
  entries are the liner inner-wall offsets (front liner inner wall 20 mm inboard at lock, rear 30 mm), not a probe radius
  (the clay README said probe radius; that was wrong).

## Clay renders (`renders/`, 800 px jpg)
- `gr_corolla_clay_front34_800.jpg`
- `gr_corolla_clay_rear34_800.jpg`
- `gr_corolla_bp_overlay_800.jpg`: all 4 views of the clay silhouette over the SVG lines. A full-size png is alongside.
- `gr_corolla_threeview_800.jpg`: 1 px = 4.4 mm, same layout as `lean_common/threeview`.
- `gr_corolla_line_classes_800.jpg`
- `gr_corolla_clearance_800.jpg`

## Clay compromises / estimates (detail-pass changes are listed below)
- **Estimated values:**
  - The centre of mass (x +0.26, z 0.52) is an estimate.
  - Front bump is 35 mm, less than the rear's 45 mm, because the arch line sits about 2–4 cm above the tyre (A.2.7).
  - Track and tyre width are estimated from the drawing (track 1.570 m).
- **Wheelbase and height:** the drawing's 2657 mm wheelbase (+0.7% over spec) and ~1473 mm height were kept as drawn.
- **Detail left for textures:**
  - The DETAILS layer (creases, lamp internals).
  - Door handles, the plate, and the inner shapes of the grille mesh.
- **Simplified pockets:**
  - Hood vents, fender vents and the rear diffuser are 4-point pockets. The fender vent's two slots are one convex opening.
  - Headlamp and grille pockets have 8 points; the side intakes have 6.
  - Pocket wall depth is capped at 1.6× the nominal depth at grazing angles.
- **Wing:** a Douglas–Peucker profile swept across the span, 16 tris. Its upturned rear tip is slightly under-filled against the outline.
- **Mirrors:** simple 12-tri wedges, slightly fuller than the plan outline.
- **Shading QC:**
  - 62 of 544 loft quads are non-planar by more than 5%.
  - The worst is a narrow arch-lip wall quad at the front arch (46%), which is triangulated anyway.
  - No flipped or degenerate faces.
- **Budget history:**
  - The first build was 2,244 tris with 42 stations (arches 0.12 m, nose 0.075 m); the 0.10 m end spacing is new.
  - It also had the rear tyre touching at bump.
  - The station spacing was opened up and pocket points reduced. That brought the total to 1,922, and all 9 poses are now clear.

---

# Detail pass (2026-11-02)

Same approach as the WRX STI / S2000 / BRZ detail passes: keep the signed-off silhouette, fix the clay review notes,
then UVs + a painted PSX texture set + faked-shine materials, a game .glb and a Godot scene.

## Detail pipeline
1. **`bp/vectors.py`** → `bp/feature_vectors.json`: every TRANSPORT and DETAILS path of the SVG as a car-frame polyline
   (panel lines are drawn from these vectors, never traced from a raster) plus the classified region outlines
   (`approxPolyDP` 0.6 px) for fills. `bp/frames.py` is the one SVG ↔ car-frame mapping. The three closed paths that
   draw the real maker emblem (front grille, hatch ring + oval) are dropped here and listed in the json
   (`dropped_emblems`); nothing of the real badge is painted.
2. **`build_gr_detail.py`** (headless Blender; imports the clay script for the loft, wheels, liners, rig, clearance):
   - `--geo-only`: geometry, tri count, clearance, Workbench clay renders → `detail/renders/raw/`, `detail/gr_corolla_geo.blend`.
   - `--render` (full): UVs, Cycles AO bake, texel maps → `tex/make_body_gr.py`, `tex/make_parts_gr.py`, `tex/make_env.py`,
     fake-shine materials (`parts/psx_mat.py`, copied from the WRX), `detail/gr_corolla_detail.blend` + `.glb`,
     textured renders (`parts/render_detail.py`) → `detail/renders/tex_raw/`.
   - `render_detail_only.py` re-renders from the saved .blend.
3. `GRC_OUT=detail python3 bp/iou.py` (gate), `bp/deliver_detail.py` (sheets), `threeview/*_detail.py`, `lineup/`,
   `godot/make_tscn.py`. The night shot lives in `art/mood/tokyo_gr/`.

## Geometry changes (all re-gated)
| Clay note | Fix |
|---|---|
| Faceted nose shading | Custom split normals: after the boolean, every paint/glass loop takes the normal interpolated from the uncut loft (BVH lookup); pocket walls/floors stay flat. Crisp edges only where intended. |
| Jagged dark grille | Pocket outlines are Douglas–Peucker "corner" polygons (≤ 8 pts) with **planar** floors (plane fit, offset by depth); the mesh read is texture. |
| Jagged diffuser (saw-tooth) | The opening is now one 6-pt hull of the centre diffuser strip + the three exhausts; the big angular corner vents are **painted** (hex mesh), not cut. Exhausts sit inside the pocket. |
| Under-filled wing tip | Wing profile simplified at 5.5 mm (was coarser): 16 → 28 tris; the upturned tip now fills the outline. |
| Boxy mirrors | 3-ring tapered shell (stalk / inner / outer), 12 → 20 tris each. Still a fairly blocky read at PSX size. |
| — | Loft end caps above the sill line now carry body paint (rear plate area was `under` black). |
| — | Lamp glow FX: head **and** tail quads (`GRC_FX_LampGlow`, 8 tris, hidden by default). |

**Triangles: 1,888 total (cap 2,000; clay 1,922).** Mono body 1,672 = loft + pockets 1,494 (loft 1,146), wing 28, fin 4,
mirrors 40, triple exhaust 48, arch liners 56, floor 2; wheels 144 (4 × 10-sided); struts/arms 64; glow FX 8.
Breakdown: `detail/tri_count.txt`.

**IoU** (vector OUTLINE vs detail triangles, no fitting): side **0.978**, top **0.991**, front **0.978**, rear **0.978** — PASS
(`detail/bp/iou.json`).

**Clearance** (9 poses, unchanged spec): all clear, tightest **7.6 mm** (FL/FR, straight ahead, bump); rear 8.8 mm at bump;
16.8 mm at full lock + bump (`detail/bp/clearance.json`, `detail/renders/gr_corolla_detail_clearance_800.jpg`).
Mono body, rig (`GRC-vehicle`, `Hub_XX-wheel`, `Steer_FL/FR`, `Susp_XX`) and COM origin unchanged.

## Textures and materials
| Texture | Size | Content |
|---|---|---|
| `detail/tex/gr_corolla_body.png` | 1024² | Body: smart-project UVs (62°), vector-painted per view (owner view by face normal; nose/tail wrap-around faces stay on the end views), baked AO, form shading, RGB555 + 4×4 Bayer, 4 px gutters. 66 % texels used. |
| `detail/tex/gr_corolla_parts.png` | 256² | Wheel disc (gunmetal 15-spoke, 5 lugs, made-up "VORTA 235/40R18" sidewall), tread strip, headlamp lens tile. |
| `detail/tex/gr_corolla_glow.png` | 128×64 RGBA | Glow sprites: warm head (left), red tail (right). |
| `detail/tex/gr_corolla_env.png` | 256×128 | Painted env map for the faked shine (not in the .glb, as on the other cars). |

**Livery:** "Apex White" body with gloss-black roof, pillars, wing and mirrors (Circuit-Edition-like, and distinct from the
blue/red/blue lineup), matte-black lower aero and sills, a thin red accent along the rear diffuser (a matching line on the front-lip top edge
barely shows, since those lip faces point mostly down).
Glass is one cool, dark, opaque material (`GRC_Glass`).

**Painted detail:** panel/shut lines from the TRANSPORT vectors (3 px, mid grey) and faint DETAILS creases; door
handles; hex mesh in the grille and side intakes; slats in the hood and fender vents; hex mesh in the rear corner vents
and fins in the diffuser; tail lamps (red, lit bar, reversing lamp); flat made-up plates "KT 22-16" (front and rear,
reading correctly); made-up **apex chevron** emblem on the nose and hatch where the maker emblem was; a small red block
badge with illegible white marks on the grille. No real brand marks or legible model names.

**Headlamps (A.2.8):** the clay's 30 mm Fourier pocket is the light molding (dark trim walls); the lens floor carries
the lamp art from the parts-atlas tile (housing, LED DRL strip, two projectors with hotspots, amber corner, glint) with
planar UVs (|y|, z), so both lamps mirror the same art and read true from the front. The tile is scaled to the full
blueprint lamp outline.

**Wheels:** the outer cap UV runs `+side`, so the sidewall lettering reads correctly on both sides (checked in the
front/rear 3/4 renders: left and right).

**Materials in the .glb** (plain Principled, baked albedo, as the other cars): `GRC_Paint_Body`, `GRC_Glass`,
`GRC_Under`, `GRC_Lamp`, `GRC_Wheel`, `GRC_FX_Glow`. In the .blend they are the fake-shine node trees (ambient + key
+ Blinn + painted env × fresnel; paint env .30 cool-tinted, glass .45).

## Detail renders (`detail/renders/`)
- `gr_corolla_detail_front34_800.jpg` / `_rear34_800.jpg` (+ `_ref.png` 1280×896 review frames: 640×448, RGB555 + Bayer, 2× nearest)
- `gr_corolla_detail_lit_800.jpg`: lamps on (glow sprites visible)
- `gr_corolla_detail_orthos_800.jpg`: textured orthos with the blueprint silhouette edge and IoU
- `gr_corolla_detail_threeview.png` / `_800.jpg`: 1 px = 4.4 mm
- `gr_corolla_detail_texture_800.jpg`: body | parts atlas | glow
- `gr_corolla_detail_vs_clay_800.jpg`: signed-off clay | detail clay | textured
- `gr_corolla_detail_closeups_800.jpg`: headlamp, grille, rear diffuser, wheel lettering
- `gr_corolla_detail_clearance_800.jpg`
- `gr_corolla_detail_lineup_800.jpg`: WRX, S2000, BRZ and GR from their .glb files (`lineup/`)
- `gr_corolla_detail_godot46_800.jpg`: Godot 4.6.3 check (see `assets/cars/gr_corolla/README.md`)
- Night vibe check: `art/mood/tokyo_gr/renders/`

## Detail compromises
- **Tail lamps** are painted on the body texture (not a separate emissive material); the lit look comes from the glow
  sprites, as on the WRX. Head lamps are lit via `GRC_Lamp` + sprites.
- **One body material** carries paint, black trim, pocket walls and grille mesh, so the env term (.30) also lands on the
  dark grille floor; under strong neon (Tokyo shot) the planar grille floor shows a coloured reflection band.
- **Mirrors** are improved but still read slightly boxy at close range (40 tris for the pair).
- **Hood/side creases** come from the drawing's TRANSPORT lines; on white paint they read busier than on the darker cars,
  so the line value was lifted (lighter grey).
- Rear corner vents and the diffuser fins are texture only (cutting them gave the saw-tooth read).
- Planar wrap-around faces at the nose/tail use the front/rear canvas, so a few steep transition faces stretch slightly.
