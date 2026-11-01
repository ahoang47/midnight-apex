# car_brz — Subaru BRZ (ZD8, 2022+) — detail pass

> **Game version (2026-10-31):** the lean build in [`lean/`](lean/README.md), **1,999 tris** (≤ 2,000 cap incl. wheels, struts, FX), hub-pivoted wheels + strut rig, headlamp light molding. Engine copy: `assets/cars/brz/`. The build below is the approved original, kept for history.

Second car built to the vehicle standard (`design/art/art_direction.md`, Part A), the same way as the S2000
(`art/vehicles/s2000`): straight from the four-view blueprint, gated on blueprint IoU, then painted.

| | |
|---|---|
| Triangles | **4,079** (≤ 5,000): body + cabin + mirrors 2,885, lamps 352, wheels/plates/badges 762, underbody 36, exhausts 22×2. FX quads (glow sprites, blob shadow) are extra, at 10 tris. |
| Blueprint IoU | side **0.9651**, top **0.9815**, front **0.9453**, rear **0.9275** (gate: side/top ≥ 0.95, front/rear ≥ 0.92). Approved pass-4 clay: .9660 / .9811 / .9432 / .9253 |
| Paint | **Blue** (WR-style, sRGB 28,78,196), matched to the side and rear 3/4 photos |
| Textures | `brz_body.png` 1024² (baked AO, painted form shading, vector panel lines, painted trim); `brz_atlas.png` 256² (wheel, tread, lamps, honeycomb, plate, badges); `brz_env.png` 256×128 (painted env map). All RGB555 + 4×4 Bayer |
| Rules applied | Opaque cool-tinted glass. No interior, brakes or calipers. Made-up brands only (KESTREL wordmark, chevron emblem, VORTA tyres, MIDNIGHT APEX plate). Faked shine (ambient + key + Blinn + painted env × fresnel, env ≤ 0.45). Lamps emissive with glow sprites. Blob shadow |

## Files
- **Build scripts**
  - `build_brz.py`: the grey clay. Geometry lives in `parts/brz_geo.py` (sections fitted to the blueprint) and `parts/brz_bp.py` (blueprint curves, lamp/trim/plate outlines). Writes `brz_clay.glb`.
  - `build_brz_detail.py`: the detail pass. It runs the clay with `DETAIL=True`, then:
    - joins the body, UVs it and bakes AO in Cycles
    - paints the body with `tex/make_body.py`, builds the atlas with `tex/make_atlas.py` and the env map with `tex/make_env.py`
    - adds the lamp decals, plates, badges and atlas wheels
    - builds the fake-shine materials
  - Outputs: `brz_lowpoly.blend` (packed, with blueprint planes as viewport-only refs), `.glb`, `.obj/.mtl`, `.fbx` (Principled BSDF swapped in for export), `tri_count.txt`.
- **Rendering:** `render_brz_detail.py` makes clean Cycles renders, PSX renders and the sheets (`bp/detail_sheets.py`).
- **`bp/`** (blueprint data and gate)
  - `extract.py` traces `ref/brz_blueprint.jpg` into `curves.json` and `bp_classes.npz`
  - `bpcompare.py` is the IoU gate and writes `iou_bpframe.json`
  - `classify_sheet.py`, `feature_overlay.py` and `coldiff.py` are review tools
- **`ref/`**
  - `brz_blueprint.jpg`: the four-view blueprint.
  - `brz_photo_rear34.jpg` and `brz_photo_side.jpg`: used only to check surface character and colour.
  - The front 3/4 dealer/studio photo (a black car) is **not** committed because its licensing is unclear. Its source URL wasn't recorded on the art box (TODO: add it if known). The photo-vs-render sheet skips any photo that is missing.
- **`renders/`**
  - clean detail renders: `brz_{front34,rear34,side,front}_detail_800.jpg`
  - PSX frames: `brz_psx_{front34,rear34}_detail.png`
  - `brz_bp_compare_detail_800.jpg`: blueprint | model at the same metres/px | IoU overlay
  - `brz_photo_vs_render_detail_800.jpg`
  - pass-4 clay sheets: `brz_clay_orthos_p4_800.jpg`, `brz_bp_line_classification_p4_800.jpg`, `brz_clay_bp_feature_overlay_p4_800.jpg`
- `keyline_table.md`: the pass-4 clay key-line table and the lesson below.

## Rebuild (Blender 4.2.3 headless + Python 3 with Pillow/NumPy/SciPy/OpenCV)
```
blender -b -P build_brz_detail.py                          # textures + model + exports (~12 s)
python3 bp/bpcompare.py                                    # IoU gate -> bp/iou_bpframe.json
blender -b brz_lowpoly.blend -P render_brz_detail.py -- detail   # renders + sheets (~30 s)
blender -b -P build_brz.py && python3 bp/bpcompare.py      # clay only (4,761 tris; .9660/.9811/.9432/.9253)
```
Both builds write `bp/tris_carframe.npy`, so run `bpcompare.py` right after the build you want to gate.

A test rebuild from a temp copy of this folder gave the same results: 4,761 clay tris and 4,079 detail tris, the same IoU, and byte-identical textures.

## How it was built
- **Clay pass 4.** Every station is fitted to the blueprint:
  - plan half-width from the top view
  - bottom and top from the side view
  - beltline from the side DLO bottom
  - hip/rear section from the rear-view outline

  The lead approved this shape.
- **Detail pass: geometry.** The approved silhouette is kept, with one small gated rear tweak:
  - The rear face rakes forward at the lamp/lip rows.
  - The p4–p7 rear columns get rounder plan corners. This is set via `BRZ_REAR_TWEAK`, which `build_brz_detail.py` sets. With the variable unset, the clay is unchanged.

  The lamp, plate and C-intake insets are replaced by atlas decals and paint. Only the grille and diffuser recesses stay as geometry.
- **Detail pass: painted shape.** Paint carries the BRZ identity that the user asked for:
  - door-scoop crease highlight with the concave shadow under it, following mesh column p3
  - hood valley between the fender ridges
  - rear-haunch highlight
  - rounded rear-face shading
  - bright ducktail-lip line
  - low, wide hex grille with fang corners
  - C-intakes, fender vent and side-skirt blade
  - swept boomerang taillights (atlas decal following the blueprint rear and side lamp outlines)
  - wedge headlights that are thin inboard and tall at the outer end

## Lesson (corrected)
Passes 2–3 trusted a low photo camera and decided that "the blueprint draws the car too tall", then moved the body away from it. That was wrong. **The blueprint was right; the window/DLO lines had been misread** (glass and body lines mixed up). The photo camera solve was about 4% small and low. Pass 4 went back to the S2000 method: classify the blueprint lines, build only from the blueprint, gate on IoU, and use photos only as a final visual check. The lead approved the result ("Way better").

## Known gaps
- The rear tweak is small because the IoU barely moves with it. The rear still reads a bit tall; painted shading carries most of the softening.
- The door scoop is paint over the existing mesh concavity; its geometry was not deepened.
- The C-intakes and grille-recess walls show slightly stepped edges at grazing angles.
- The haunch highlight is softer than in the photo, and the black lower rear bumper wraps the corners less than on the real car.
- Glow sprites and the blob shadow are not exported (`BRZ_FX` collection in the `.blend` only).
- Blueprint vs spec: the blueprint scale comes from the published length (4.265 m) and wheelbase (2.575 m). Its width reads about 1.80–1.85 m against the published 1.775 m, which is noted per Part A.1.1.
- Review frame: the PSX renders are 640×448, the same as the S2000 and Tokyo v2. The art-direction doc says 640×480.
