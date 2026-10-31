# mood_tokyo_v2 — Tokyo night street (vibe check, non-binding)

Mood reference only (`art_direction.md` Part B). The lead approved this look ("much more PSX") but it is **not** a game
standard and will likely not ship. The car is `art/vehicles/s2000`.

**Rebuilt 2026-10-31.** The original scene scripts were lost in the box wipe; these were rebuilt from the recorded
recipe and the surviving 800-px frames in `renders/original_800/` (the approved originals — use those as the true
reference). The rebuild follows the same recipe but is not pixel-identical; its triangle count is 8,728 incl. the car
(original ~12k).

Recipe: everything unlit (texture × vertex colour → linear fog 14–105 m → emission), stepped sodium pools painted into
the dry road texture, unlit neon + additive glow billboards, pre-lit facades and cut-out props, car with faked shine
(ambient + one key + Blinn + painted env map, cool-tinted glass), blob shadow + headlight-throw decal; EEVEE Next
640×448, 1 sample, filter 0, Standard view; post: neon-only bloom → RGB555 + 4×4 Bayer → 2× nearest (1280×896).

```
blender -b --python scene_v2.py    # textures (make_tex_v2.py), scene .blend, raw + neon passes
python3 post_v2.py                 # bloom/quantise/upscale, _800.jpg previews, contact sheet
python3 make_style_reference.py    # palette + annotated crops
```

## Duo: S2000 + BRZ (added 2026-10-31, vibe check, non-binding)
`scene_duo.py` reruns `scene_v2.py`'s world and S2000 section unchanged, so the single-car scene is not touched. It
then parks the S2000 and the BRZ (`art/vehicles/brz/brz_lowpoly.blend`) side by side:
- both noses face down the street
- about 1 m gap between the doors
- the BRZ is staggered 1.1 m back
- they sit under the sodium lamp one block before the konbini, so the storefront stays in the distance
- each car has its own blob shadow, headlight-throw decal and lamp glow sprites

The BRZ gets the scene's own fake shine. Its paint env is 0.22 with a cool tint, lower than the S2000's 0.45, because
the neon env map blotched its darker blue panels. `post_duo.py` is the same post as `post_v2.py`: bloom → RGB555 + Bayer
→ 2× nearest, 640×448 → 1280×896.
```
blender -b --python scene_duo.py    # tokyo_duo.blend + raw/neon passes in renders/duo/
python3 post_duo.py                 # duo_*.png, _800.jpg previews, duo_contact
```
Previews: `renders/duo/duo_{hero_front34,rear34,side_by_side,establishing}_800.jpg` and `duo_contact_800.jpg`.
A test rebuild from a temp copy of the repo layout matched the box render pixel for pixel.
