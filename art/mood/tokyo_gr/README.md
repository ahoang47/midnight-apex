# mood_tokyo_gr — GR Corolla on the Tokyo v2 night street (vibe check, non-binding)

Mood reference only (`art_direction.md` Part B), same status as `art/mood/tokyo_v2/` (not a game standard).
Car: `assets/cars/gr_corolla/car_gr_corolla.glb` (detail pass, `art/vehicles/gr_corolla/`).

`scene_gr_tokyo.py` follows `tokyo_v2/scene_duo.py`: it runs `tokyo_v2/scene_v2.py`'s world section unchanged (exec
up to its render setup), deletes the S2000, imports the GR Corolla .glb exactly as Godot imports it, parks it one block
before the konbini (the duo's slot, under the sodium lamp at x −24), and gives it the scene's faked shine (ambient + 1
key + Blinn + painted env map × fresnel, fog → emission), a blob shadow, a headlight-throw decal and head/tail glow
sprites. Paint env is .22 cool-tinted (as the BRZ); glass .45. EEVEE Next 640×448, 1 sample, filter 0, Standard view
+ neon-only pass. `post_gr_tokyo.py` = the `post_duo.py` recipe (neon bloom → RGB555 + 4×4 Bayer → 2× nearest, 1280×896)
using `tokyo_v2/post_v2.rgb555`.

`scene_v2.py` writes its generated textures and a .blend next to itself, so run from a scratch copy of the repo
(with `art/vehicles/s2000` next to it, since `scene_v2.py` appends the S2000 before it is removed):
```
TOKYO_V2=<copy>/art/mood/tokyo_v2/scene_v2.py blender -b --python scene_gr_tokyo.py   # renders/raw/
TOKYO_V2=<copy>/art/mood/tokyo_v2/scene_v2.py python3 post_gr_tokyo.py                # renders/*.png, *_800.jpg
```
Renders: `renders/gr_corolla_tokyo_{hero_front34,rear34,establishing}.png` (+ `_800.jpg`).
Known artefact: the dark grille floor shares the body material, so under the neon env map it shows a coloured
reflection band.
