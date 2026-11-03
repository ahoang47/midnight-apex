# Character bases — source (male + female)

Game-ready files (glbs, textures, BoneMap, import guide): `assets/characters/base/` (README there).
This folder holds the source: `char_base.blend`, the build scripts, review renders, the UV templates and the Godot import log. Credits: `CREDITS.md`.
Run inside the repo, the scripts write textures and glbs to `assets/characters/base/`. Run anywhere else, they write next to `build/`.

## Files
| Path | What |
|---|---|
| `char_base.blend` | Both sexes in one file. **Male** collection: `CharBase_M` + `M_Body`, `M_Head`, `M_Hair_A`, `M_Hair_B`, `M_Hood`. **Female** collection: `CharBase_F` + `F_*` (with `F_Collar`). Also the shared action `deform_test` and both outfit images packed per sex. |
| `build/spec.py` | Skeleton, lofts, atlas layout, tune-up warp, shape-key factors, female mapping. |
| `build/paint_textures.py` | Paints the outfit atlases, head and hair into `assets/characters/base/textures/`. |
| `build/build_char.py` | Builds the blend, `assets/characters/base/char_base_{m,f}.glb`, `build/tris.json` and `build/uv_{m,f}.json`. |
| `build/render_checks.py`, `build/compose.py` | Review renders (via `/tmp/cb`) into `renders/`, plus the UV templates. |
| `build/godot/*.gd` | Headless Godot checks (inspect, BoneMap, retarget). Run them in a scratch Godot project that holds a copy of the glbs. They are not game scripts. |
| `godot_import_log.txt` | Godot 4.6.3 import, BoneMap and retarget results. |
| `renders/` | Turnarounds (`_800.jpg`), swap sheets, `builds_lineup.jpg`, `lineup_mf.jpg`, `tuneup_before_after.jpg`, `deform_check.jpg`, `uv_template_{m,f}.png`. |

## Skeleton (identical names and hierarchy, M and F)
There are 25 bones, all Mixamo `mixamorig:` names. It is a clean deform rig with no IK or poles. Rest pose is a T-pose with the root at the feet.
```
Hips
├─ Spine ─ Spine1 ─ Spine2
│                    ├─ Neck ─ Head ─ HeadTop_End*
│                    ├─ LeftShoulder ─ LeftArm ─ LeftForeArm ─ LeftHand
│                    └─ RightShoulder ─ RightArm ─ RightForeArm ─ RightHand
├─ LeftUpLeg ─ LeftLeg ─ LeftFoot ─ LeftToeBase ─ LeftToe_End*
└─ RightUpLeg ─ RightLeg ─ RightFoot ─ RightToeBase ─ RightToe_End*      (* non-deform)
```
| | Male | Female |
|---|---|---|
| Height (with Hair_A) | 1.83 m | 1.70 m |
| Head joint | 1.582 | 1.471 |
| Upper arm | 0.27 | 0.251 |
| Forearm | 0.27 | 0.251 |
| Hand | 0.16 | 0.149 |
| Heads tall | ≈6.6 | ≈6.6 |

Godot renames `:` to `_` (`mixamorig_Hips`). That is the same name Mixamo FBX files get in Godot.

**BoneMap → SkeletonProfileHumanoid.** For both glbs, 17 bones are required and **none are unmapped**. The unmapped bones are all optional (Root, eyes, jaw, fingers).

| Mixamo | Godot profile |
|---|---|
| Spine1 / Spine2 | Chest / UpperChest |
| Arm / ForeArm | UpperArm / LowerArm |
| UpLeg / Leg | UpperLeg / LowerLeg |
| ToeBase | Toes |
| All others | Same name |

Retargeted import uses Advanced Import → Skeleton3D → Retarget → Bone Map = `assets/characters/base/humanoid_bonemap.tres` (Auto-Map also works), with Rest Fixer → Overwrite Axis switched on. The result is `GeneralSkeleton` with nothing missing, and `deform_test` retargets onto it.

## Pieces and triangles
| Piece | Male | Female | Notes |
|---|---|---|---|
| Body | 686 | 686 | Torso, neck, arms, hands, legs, shoes in one mesh; outfit atlas |
| Head | 124 | 124 | Painted face, 128² |
| Hair_A | 70 (crop) | 90 (bob) | |
| Hair_B | 70 (quiff) | 144 (side-swept fringe + high ponytail) | |
| Add-on | 40 Hood | 20 Collar | Shown only with the alt outfit; uses the outfit atlas |

Complete characters, all well under the 1,200 budget:

| Sex | Combination | Tris |
|---|---|---|
| Male | Tee | **880** |
| Male | Hoodie | **920** |
| Female | Bob + tee | **900** |
| Female | Bob + jacket | **920** |
| Female | Ponytail + tee | **954** |
| Female | Ponytail + jacket | **974** |

**Reading as clothed, the PS1 way.** The silhouette has steps where clothes would end:
- the torso flares slightly at the tee hem (z ≈ 0.965)
- the upper arm is sleeve-thick, with a step at the sleeve hem (x ≈ 0.30)
- the legs follow a straight-jeans silhouette with a flared hem at the ankle
- the feet are sneaker-shaped

Everything else is paint. With the hoodie or jacket atlas, the sleeve step reads as fabric bunching. Because the body is one mesh, there is no poke-through and no holes.

## Outfit atlas layout (UV units, v up, 256 px)
| Region | Rect | Notes |
|---|---|---|
| torso | (0, .50)–(.625, 1) | Front of the body = centre column, seam at the back. Top = collar, bottom = crotch cap. |
| neck | (.625, .90)–(1, 1) | |
| arm L / R | (.625/.8125, .52)–(…, .90) | Bottom of the rect = shoulder, top = wrist |
| hand L / R | (…, .40)–(…, .52) | |
| thumb L / R | (…, .36)–(…, .40) | |
| leg L / R | (0/.3125, .04)–(…, .50) | Bottom = ankle, top = crotch |
| shoe L / R | (.625/.8125, .10)–(…, .36) | Seam under the sole |
| add-on | (.625, 0)–(1, .10) | Hood / collar |

## Make a new outfit = paint a new atlas
1. Open `renders/uv_template_m.png` or `uv_template_f.png`. They are 1024 px (4×) and show the regions, the wire, and the default tee underneath.
2. Paint the outfit on top (the tee, jacket, uniform, coveralls…). Keep the front of each part in the centre column of its region. Use flat PS1 colours with a little noise.
3. Scale it down to **256×256** with nearest or box filtering, then save it as `assets/characters/base/textures/<sex>/outfit_<name>.png`. You can also add a painter function in `build/paint_textures.py`, which applies the RGB555 + Bayer pass for you.
4. In Godot, set the albedo of the Body material (and the add-on's, if shown) to the new texture, with Nearest filtering. The mesh doesn't change.
5. If the outfit needs a new silhouette (a skirt, a long coat, a cap), add a small add-on loft in `spec.lofts()` that uses the `addon` region, or a new small region. Keep it under about 60 tris.

**Rebuild:**
```
cd art/characters/base; B=/path/to/blender   # Blender 4.2.3
python3 build/paint_textures.py
$B -b -P build/build_char.py
$B -b char_base.blend -P build/render_checks.py && python3 build/compose.py
```

## Body variants: Standard / Slim / Bulky
There is **one skeleton**. The variants are the shape keys `Slim` and `Bulky`, which live on the Body mesh, the head, the hair and the add-ons. Set the same value on every mesh of the character.
- **Bulky:**
  - trunk ×1.34–1.42 wide, depth up to ×1.55 at the belly and ×1.42 at the chest (height-dependent profile)
  - arms ×1.34, legs ×1.32, neck ×1.32, hands ×1.12, shoes ×1.08, face ×1.06
  - arms shift outward 4 cm and legs 2.2 cm so they clear the wider trunk and hips, which also reads as slightly wider shoulders
- **Slim:** trunk ×0.78–0.88, limbs ×0.80, neck ×0.86, with arms and legs shifted inward slightly.
- Add-ons use the trunk/head factors at their height, so they keep fitting.

## Weights and deformation
Weights are analytic, computed in the original reference space, so they follow the warped bones exactly. Fixes built in:
- **Armpit:** the trunk blends into Shoulder, and the outer shoulder corner blends 70 % into the upper arm.
- **Hip:** the trunk blends into UpLeg.
- **Neck:** the neck blends to the head.

The `deform_test` action is shared by both rigs:
- f1: T-pose
- f20: A-pose (45° arms, 15° elbows)
- f40: knee-up pose, head turn, chest twist

See `renders/deform_check.jpg`.

## Tune-up pass (this revision)
- **Head:** ×1.12 and lowered 2 cm, giving a shorter visible neck (≈6.6 heads tall). Hair and ears follow.
- **Arms:** about 8.5 % shorter. Upper arm and forearm go 0.29/0.30 → 0.27/0.27 m on the male, and the female maps from that. With arms down the fingertips land at upper/mid thigh (male ≈0.75 m). In the 45° A-pose they sit at hip level (male 0.955 m).
- **Female Hair B:** side-swept fringe over the brow, hair over the temples and ears, and a high ponytail that swings out past the head silhouette on her left. It reads from the front and 3/4.
- **Bulky/Slim:** pushed further, see above.
- **Clothes:** restructured from layered meshes to the painted atlas (user direction).

## Female chest-height fix (2026-11-02)
- The female bust apex sat at 1.163 m, about 18 cm under the shoulders. Austin had it raised twice (+5 cm, then another +5 cm), so it's now at **1.256 m** (+9.3 cm), about 4 cm above the Spine2 joint (1.218). `spec.fem_trunk_z()` remaps female trunk heights only, in male reference z: waist ring 1.12 → 1.16 (1.079 m), bust ring 1.25 → 1.3505 (1.256 m) and armpit ring 1.36 → 1.405 (1.307 m), so the upper chest isn't pinched against the bust. The hem and the shoulder ring and above don't move.
- Ring widths and depths, and the Slim/Bulky factors, stay keyed to each ring's original height, so Basis, Slim and Bulky all carry the raised chest.
- Weights follow the new heights (`TRUNK_WZ`). The apex ring is ~79 % Spine2 / 21 % Spine1 (13 % Shoulder at the sides). The armpit ring is weighted a little below its new height so it stays Spine2/Shoulder with only ~3 % UpperArm, which keeps the A-pose armpit clean.
- Tris (686), vertex count and UVs are unchanged, and the textures were not repainted. The texture follows the vertices, so the tee stretches about 1.45× vertically between the waist and the bust and compresses about 0.5× from the bust to the armpit. The jacket's slash pockets sit about 2–3 cm higher and a little taller. It's plain fabric with no print, so it doesn't show at game resolution. The male geometry is exactly the same.
- See `renders/chest_fix_before_after.jpg`.

## Renders
| File | What |
|---|---|
| `renders/turnaround_{male,female}_{standard,slim,bulky}_800.jpg` | Front / side / back |
| `renders/swap_sheet_{male,female}.jpg` | 2 outfits (texture swap) × 2 hair |
| `renders/builds_lineup.jpg` | M slim/std/bulky + F slim/std/bulky, one row, same ortho scale |
| `renders/tuneup_before_after.jpg` | Old vs new standard male and female (rebuilding it needs the old renders, `BEFORE_DIR`; they are not in the repo) |
| `renders/lineup_mf.jpg` | Male and female at the same scale with height lines |
| `renders/chest_fix_before_after.jpg` | Female chest-height fix: original (1.163) vs new (1.256), front + A-pose sides for standard/slim/bulky |
| `renders/deform_check.jpg` | Deformation check |
| `renders/uv_template_m.png`, `uv_template_f.png` | Paint templates |

## Known limitations
- Bone rolls are 0 and the rig is untested against a real Mixamo FBX (that needs an Adobe login). The Godot path uses BoneMap + rest fixer.
- Godot's Auto-Map can't run headless, so the BoneMap was built from the explicit table above.
- There are no finger bones (mitten hands with a thumb).
- Shape keys don't move bones. The joint pivots stay at the standard positions, which is fine for this level of variation.
- The male Hood and female Collar are hidden by default in the blend but visible on glb import. Toggle them with the outfit.
- The sleeve and hem steps are baked into the body, so every outfit shares the tee/jeans silhouette. A skirt or shorts would need an add-on, or a second body variant.
- The ears are flat quads.

> Not committed: the full-size `renders/turnaround_*.png` that `compose.py` also writes (the `_800.jpg` copies are committed), plus `*.blend1` and `__pycache__`. See `.gitignore`.
