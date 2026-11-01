# car_s2000 — Honda S2000 (AP1), stock soft top — reference car

> **Game version (2026-10-31):** the lean build in [`lean/`](lean/README.md), **1,916 tris** (≤ 2,000 cap incl. wheels, struts, FX), hub-pivoted wheels + strut rig, headlamp light molding. Engine copy: `assets/cars/s2000/`. The build below is the approved original, kept for history.

Binding reference for the vehicle standard (`design/art/art_direction.md`, Part A; Appendix W).

| | |
|---|---|
| Triangles | **4,354** (≤ 5,000 budget) |
| Blueprint IoU | side **0.961**, top **0.992**, front **0.925**, rear **0.944** (gate: side/top ≥ 0.95, front/rear ≥ 0.92) |
| Textures | `s2000_body.png` 1024² (vector panel lines, baked AO), `s2000_atlas.png` 256² (lamps, grille, wheel, badges, plate), `s2000_softtop.png` 512² (fabric) — RGB555 + Bayer |
| Top | stock black fabric soft top, ends at the rear deck; trunk lid in body paint |
| Rules applied | opaque cool-tinted glass, no interior, no brakes/calipers, made-up badges/plate, smooth shading with crisp edges |

## Files
- `build_s2000.py` — builds everything procedurally (calls `tex/make_atlas.py`, `tex/make_softtop.py`, `tex/make_body.py`).
- `s2000_lowpoly.glb` (engine), `.blend` (blueprint planes packed as viewport-only refs), `.obj/.mtl`, `.fbx`.
- `bp/` — blueprint extraction (`extract.py` → `curves.json`, `planes.json`) and IoU overlay (`compare.py`).
- `ref/` — the four-view blueprint and its crops. `renders/` — clean 1280 views, close-up of the soft top, IoU overlays.

## Rebuild
```
blender -b --python build_s2000.py -- --no-render          # model + textures + exports (~20 s)
blender -b --python build_s2000.py -- --no-export --compare && python3 bp/compare.py   # IoU overlays
blender -b --python build_s2000.py -- --no-export --clean  # clean Cycles renders (CPU, a few minutes)
```
Tested with Blender 4.2.3 on Linux; output is pixel-identical to the pre-loss build.

## History
Restored 2026-10-31 after the art box was wiped (files recovered verbatim from the last S2000 zip sent in chat).
Known weak spots from the last review: a dark streak under each headlight, windshield frame a touch thin and slightly
behind the blueprint line, some faceting on the nose and rear bumper up close.
