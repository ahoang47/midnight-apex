# mood_tokyo_mx5 — MX-5 (ND) on the Tokyo v2 night street (vibe check, non-binding)

Mood reference only (`art_direction.md` Part B), same status as `art/mood/tokyo_gr/` (not a game standard).
Car: `assets/cars/mx5/car_mx5.glb` (detail pass, `art/vehicles/mx5/`).

`scene_mx5_tokyo.py` is `tokyo_gr/scene_gr_tokyo.py` with the MX-5. It runs `tokyo_v2/scene_v2.py`'s world section
unchanged (exec up to its render setup), deletes the S2000, imports the MX-5 .glb exactly as Godot imports it and
parks it in the same slot (under the sodium lamp at x −24, one block before the konbini). It gets the scene's faked
shine (ambient + 1 key + Blinn + painted env map × fresnel, fog → emission), a blob shadow, a headlight-throw decal
and head/tail glow sprites at the MX-5's lamp centres.
- Paint env .22 cool-tinted, as the GR / BRZ, but **spec .15**: at the GR's .55 the key highlight on the faceted rear
  fender read as a white glyph on the high-value yellow.
- The fabric top is near-matte (spec .05, env .03); glass .45.

EEVEE Next 640×448, 1 sample, filter 0, Standard view + neon-only pass. `post_mx5_tokyo.py` is the `post_duo.py`
recipe (neon bloom → RGB555 + 4×4 Bayer → 2× nearest, 1280×896) using `tokyo_v2/post_v2.rgb555`.

`scene_v2.py` writes its generated textures and a .blend next to itself, so run it from a scratch copy of the repo,
with `art/vehicles/s2000` next to it (`scene_v2.py` appends the S2000 before it is removed):
```
TOKYO_V2=<copy>/art/mood/tokyo_v2/scene_v2.py blender -b --python scene_mx5_tokyo.py   # renders/raw/
TOKYO_V2=<copy>/art/mood/tokyo_v2/scene_v2.py python3 post_mx5_tokyo.py                # renders/*.png, *_800.jpg
```
Renders: `renders/mx5_tokyo_{hero_front34,rear34,establishing}.png` (+ `_800.jpg`).

**Known artefact:** the scene samples the car textures with LINEAR filtering. Thin olive seams show where the soft
top's UV islands meet paint (they don't show with nearest filtering).
