# Character bases — male / female (game-ready)

These are shared base bodies for every human character, one per sex, in the PS1 painted-outfit style. Source, build scripts and review renders are in `art/characters/base/` (README there).

| File | What |
|---|---|
| `char_base_m.glb` | Male base. Contains `CharBase_M` rig, the `M_Body`, `M_Head`, `M_Hair_A`, `M_Hair_B` and `M_Hood` meshes, and the animation `deform_test`. The tee outfit atlas is embedded. |
| `char_base_f.glb` | Female base. Contains `CharBase_F` rig, the `F_Body`, `F_Head`, `F_Hair_A`, `F_Hair_B` and `F_Collar` meshes, and the animation `deform_test`. |
| `textures/{m,f}/outfit_*.png` | Outfit atlases, 256². Male: `outfit_tee` / `outfit_hoodie`. Female: `outfit_tee` / `outfit_jacket`. |
| `textures/{m,f}/head.png`, `hair_a.png`, `hair_b.png` | 128² each. These are also embedded in the glbs. |
| `humanoid_bonemap.tres` | BoneMap from the Mixamo names to `SkeletonProfileHumanoid`. |

## Triangles (budget ≤ 1,200 per complete character)
| | Body | Head | Hair_A | Hair_B | Add-on |
|---|---|---|---|---|---|
| Male | 686 | 124 | 70 | 70 | Hood 40 |
| Female | 686 | 124 | 90 (bob) | 144 (fringe + ponytail) | Collar 20 |

Complete characters (Body + Head + one hair, plus the add-on for the alternate outfit):

| | Tee outfit | Hoodie / jacket outfit |
|---|---|---|
| Male | 880 | 920 |
| Female, Hair_A | 900 | 920 |
| Female, Hair_B | 954 | 974 |

## Import into Godot 4.6
1. **Skeleton and retarget.** Open the glb's Advanced Import Settings → `Skeleton3D` → Retarget → Bone Map, and load `humanoid_bonemap.tres`. Auto-Map also works, because the names are standard Mixamo. Keep **Rename Bones** and **Rest Fixer → Overwrite Axis** on, then Reimport.
   - The skeleton becomes `GeneralSkeleton`, using `SkeletonProfileHumanoid` names.
   - All 17 required bones are mapped. The unmapped bones are optional (Root, eyes, jaw, fingers).
   - Mixamo or any humanoid animation library then retargets onto both sexes.
   - Note that Godot renames `mixamorig:Hips` to `mixamorig_Hips`, which is the same name a Mixamo FBX gets.
2. **Nearest filtering.** On every material (Body, Head, Hair, add-on), set Texture Filter = **Nearest**. You can also set the project default `rendering/textures/canvas_textures/default_texture_filter`.
3. **Outfit swap.** An outfit is a texture, not a mesh. Set the Body material's albedo, and the add-on's, to another `textures/<sex>/outfit_*.png`. To make new outfits, paint over `art/characters/base/renders/uv_template_{m,f}.png`.
4. **Hood / collar add-on.** `M_Hood` belongs to `outfit_hoodie` and `F_Collar` belongs to `outfit_jacket`. Both are **visible on import**, so hide them (`visible = false`) when the tee outfit is on.
5. **Hair.** Show one of `*_Hair_A` / `*_Hair_B` and hide the other. Both are visible on import.
6. **Body build.** Every mesh has the blend shapes `Slim` and `Bulky`, with values from 0 to 1. Set the **same value on every MeshInstance3D** of the character (Body, Head, the hair shown and the add-on). For example: `mesh_instance.set("blend_shapes/Bulky", 1.0)`. Standard is both at 0.
7. **Scale.** The male is 1.83 m tall and the female 1.70 m (with Hair_A). The root sits at the feet and the model faces −Z after import (glTF).

`deform_test` is a three-key check animation (T-pose → A-pose → knee-up / head-turn pose). It is not gameplay animation.
