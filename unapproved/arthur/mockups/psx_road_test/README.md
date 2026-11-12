# PSX road test (unapproved)

Austin asked for a before/after of the approved line-select Entry frame (`art/ui/line_select_cam/1_entry_pick.png`) with the road rebuilt from the downloaded asset packs, because the old road felt too smooth and "three.js". This folder is that test. The after frames are rendered in Godot 4.6.3, not Blender.

## Texture choice

**Pack:** PSX style urban stacked pack (valsekamerplant), CC0.  
**File:** `road1_alt.png` (256×128), with `concrete_bare.jpg` cropped for the kerb and gutter.

I looked at the other candidates first:

- `road2` / `road3` — same pack, but no painted lane markings (`road3`) or only edge lines (`road2`).
- `road4` — white edges and dashes, more posterised (41 colours). Less wear than `road1_alt`.
- `ps1-style-industrial-buildings` `road_lowres.png` — has a kerb and a yellow edge, but the textures are from textures.com and **must not be redistributed**.
- Kenney Retro Urban Kit `asphalt.png` — crunchy 64×64, CC0, but no lane paint; the kit pieces are chunky city tiles, not a Japanese night street.
- 3D Retro Shacks `Concrete Floor Texture.png` — CC0, 16-colour stained concrete, not a road.

`road1_alt` already has worn yellow edge lines and faded white dashes painted into the asphalt, and much more grit (about 5,200 unique colours). That is what Austin asked for: crustiness from the pack texture itself, not overlay lettering or added noise.

The approved hairpin is three lanes (10 m wide). The pack tile is two lanes, so `compose_road.py` tiles a native crop of the pack's asphalt (rows 16–58, 1:1 pack pixels, repeats left visible) and stamps the pack's own painted dashes and yellow edges at the existing divider and edge positions. World scale is 10 m across × 13.3 m along per texture repeat. No pack source files are in this folder; the composed `tex/road_3lane.png` is a CC0 derivative built at run time.

## Licences

| Pack | Licence | Redistribute the raw textures? |
|---|---|---|
| PSX style urban stacked pack (valsekamerplant) | CC0 | Yes (we still reference them by path and only commit the composed derivative) |
| Retro Urban Kit (Kenney) | CC0 | Yes (not used in the final frames) |
| 3D Retro Shacks (chilly_durango) | CC0 1.0 | Yes (not used) |
| Ps1 style industrial buildings (miziziziz) | Models CC0; textures from textures.com | **No** — "may not be redistributed by default" |

## Frames (all 1280×960)

- `before.png` — the existing approved Blender Entry frame, copied as-is (old generated asphalt, vector lane lines, HUD drawn at 640 then dithered and 2×).
- `after_smooth.png` — Godot, pack road, Q4 smooth texture filter, classic HUD composited at 640 then dithered (so the road change can be compared with the same HUD treatment as `before`).
- `after_nearest.png` — same, with nearest/closest sampling on the road and kerb.
- `after_smooth_sharpui.png` / `after_nearest_sharpui.png` — same 3D, but following the new B.5c: 3D is dithered and 2× upscaled first, then the HUD is drawn sharp at 1280×960 with bold drop-shadowed type and chunky bevelled plates (Racing Lagoon / Gran Turismo 1–2 / Test Drive). Stance colours stay Attack `#2CB84A`, Defend `#E8282C`, Neutral `#F0C828`.
- `road_test_sheet.png` — labelled side-by-side of all five, frames pasted 1:1, then one 2× nearest upscale.

At this camera distance, after RGB555 + Bayer, the smooth and nearest after-frames currently match pixel-for-pixel. The 192×256 pack tile is about 19 texels per metre; once that has been quantized, the filter difference does not survive. Both variants are still shipped.

## Godot scene

- Project: `godot/project.godot` (Godot 4.6.3, GL Compatibility, 1280×960)
- Main scene: `godot/road_test.tscn`
- Scripts: `godot/road_test.gd` (hairpin, cars, cameras, capture), `godot/hud.gd` (classic and sharp HUD)
- Shaders: `godot/shaders/` (`road.gdshader`, `road_near.gdshader`, `post.gdshader`, `bayer.gdshader`, `car_simple.gdshader`, plus glow, pool, sky)
- Rebuild: `./run.sh` (needs `/workspace/asset_packs`, `/workspace/tools/godot` 4.6.3, and the two-corner or repo car glbs, staged at runtime into `godot/cars/`, which is gitignored)

The 3D uses the B.2a palette (fog `#0B172B`, zenith `#010408`, ambient `#5575A0` at 0.8, pale sodium `#F0C894` at 0.85, hard 3-step pools). Camera matches the approved Entry chase (25 mm / 56.7° vertical, player + rival placement from `build_lsc.py`).

## What still looks off

- The mid-road is still quite dark, so the pack grit is easiest to see in the sodium pool and along the painted dashes. That is the night lighting, not a second texture pass.
- Car shine uses a simpler unlit shader with fog (`car_simple.gdshader`). The two-corner A.4 shader with vertex snap was dropping the car meshes in this viewport, so I froze the vehicle rigid bodies and used the simpler shader to keep the cars visible.
- A few stand-in S2000 tail glows are a touch large. The MX5 uses its own lamp FX from the glb.
- Emptiness, camera, and a full HUD redesign of the live two-corner build are out of scope here, as Austin asked.

Nothing in this folder is approved until Austin says so.
