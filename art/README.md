# art/

Source art for Midnight Apex. Rules: `velocity-shift/overview/art_direction.md` (Part A is binding for vehicles).
Naming: lowercase snake_case, `category_variant_direction`.

- `vehicles/<car_id>/` — one folder per car: build script(s), textures, `.glb`/`.blend` (+ `.obj`/`.fbx`), blueprint
  references, IoU overlays, a few key renders, `README.md`. Binary budget: keep each car folder modest (~15 MB).
- `mood/<name>/` — vibe-check scenes (non-binding mood reference). Scripts + a few small previews only; generated
  textures/renders/.blend are git-ignored and rebuilt by the scripts.

Toolchain: Blender 4.2.3 (headless, `blender -b --python ...`), Python 3 with Pillow + NumPy.
