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
