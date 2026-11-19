# Asset requests for Arthur: two-corner test (pin 212eaab)
Rules that apply to every item (art_direction.md):
- Textures are quantised at authoring time to RGB555 with a 4x4 Bayer dither (A.3.5).
- Export lossless PNG. Godot import: Lossless (compress/mode=0), no mipmaps, no VRAM compression.
- Filtering is nearest for now. Q4 is still open.
- Environment art is unlit: texture x vertex colour, then linear fog (B.1/B.6). Lighting, including the stepped 4-band sodium pools, is painted in.
- Meshes ship as .glb. Names are snake_case `category_variant_direction` (C.1 / guide Appendix E).
- Engine copies go under `res://assets/...` (C.1, proposal).
- Scene budget: about 12k tris per frame including the car (B.1, vibe). Two cars use up to 4k, which leaves about 8k for the environment.
- Per-asset tri counts and environment texture sizes below are MY PROPOSALS, because the doc doesn't give them. Only the car numbers are doc values.

| # | Name | Purpose in scene | Budget | Format / import | Needed by |
|---|---|---|---|---|---|
| 1 | `road_straight` (+ track texture `road_touge.png`, `road_street.png`) | Scrolling StraightRoad strip, ~30 units (guide App. E). Each texture has the lane lines and the painted, stepped 4-band sodium pools for that district's lamp spacing (Touge 48 m, Street 16 m), baked per segment (B.6) | ≤ 200 tris (proposal); texture 256x512 (proposal; stand-in 176x576 / 176x192) | .glb + PNG. UV v = metres along the road, repeat on v | Both builds, every selection shot and GIF |
| 2 | `road_corner_left` / `road_corner_right` | CornerRoad arcs (Touge hairpin L, Street 90 R), same lane layout as #1 | ≤ 300 tris each (proposal) | .glb, shares the track texture | Both builds, corner cams + GIFs |
| 3 | `barrier_straight` / `barrier_corner_left` / `barrier_corner_right`, Touge guardrail variant | W-beam guardrail on posts, 1.0 m tall, Touge edge (B.3) | ≤ 150 tris per 30 m segment (proposal); 64x256 atlas | .glb + alpha-cutout PNG (cut-out, no blend) | Touge selection + hairpin |
| 4 | `prop_cedar_a/_b` cards | Cedar tree cards along the Touge verge (B.3) | 2–4 tris each (cross card); 128x256 | Alpha-cutout PNG, card UVs | Touge shots |
| 5 | `sky_touge`, `sky_street` (cylinder strip or equirect) | Painted night sky. The horizon must match the fog colour (Touge #2A3236; Street zenith #060614, horizon #42284A, city glow #784246) | Cylinder ≤ 96 tris; 512x256 equirect or 8x128 strip (proposal) | PNG, no fog applied (App. E skybox) | Both builds, every shot |
| 6 | `skyline_street`, `ridge_touge` cards | Distant skyline (#120E1C, lit windows) and far Touge ridge silhouette | 1 band; 512x96 / 512x64 | Alpha-cutout PNG, repeat on u | Both builds, horizon |
| 7 | `facade_street_*` (4–6 variants) | Pre-lit night facades with lit (warm #FFD28C / cool #B4E1FF) and dark (#161C2A) windows, AC units, window lettering (B.1). Storefronts must not be brighter than the car | ≤ 40 tris per building (proposal); 256x512 per facade or one 512x1024 atlas | PNG; × vertex light; facade height 24 m | Street selection + 90 corner + finish |
| 8 | `sign_neon_*` (3–6) + matching `glow_neon_*` billboards | Full-bright neon signs with **made-up** shop names (B.1), plus additive glow billboards and flat ribbon wires. Please avoid stance-like hues (B.5). **Needs canon names: the stand-ins are blank** | 2–8 tris each; 64x128 sign, 64x64 glow | PNG (sign unlit; glow additive) | Street shots |
| 9 | `prop_street_*` cut-outs (cone, bike, bin, menu board, roadworks barrier, plant) + `prop_vending` (pre-lit) | Dense, cheap sidewalk dressing (B.1) | 2–4 tris per card; vending box ≤ 24 tris; 64x64–128x128 | Alpha-cutout PNG | Street shots |
| 10 | `lamp_sodium` (Touge sodium/white, Street sodium) + `glow_lamp` | Lamp posts with emissive heads and additive glow, placed on the painted pools | ≤ 60 tris (proposal); glow 64x64 | .glb with vertex colour + PNG glow | Both builds |
| 11 | `sidewalk_street`, `verge_touge` strips | Sidewalk lit by vertex colour (B.1); Touge grass/gravel shoulder | ≤ 50 tris per segment; 128x128 | PNG, tiling | Both builds |
| 12 | S2000 FX quads: head/tail `glow` sprites, blob shadow, headlight-throw decal | A.4.3/A.4.4 MUSTs. The S2000 README says "Glow FX: none in this version". The build currently uses stand-in sprites | Inside the car's 2,000-tri cap (S2000 lean is 1,916, so 84 are free: about 4 glow quads plus a blob quad = 10 tris) | Inside `car_s2000.glb` as hidden FX nodes, like `MX5_FX_LampGlow` | Both builds, rival car in every shot |
| 13 | `blob_shadow`, `headlight_throw` shared decals (if not per car) | Ground contact + reduced-strength throw (A.4.4) | 2 tris each; 64x128 | PNG, alpha | Both builds |
| 14 | `font_*` bitmap font | HUD text, bitmap style (B.5). Appendix E asks for 1 .ttf/.otf | Stand-in is 6x9 px, ASCII 32–126 | .ttf/.otf pixel font, or a PNG atlas + metrics JSON | Both builds, all HUD/menu shots |
| 15 | `panel_*` 9-slice (4 per App. E), buttons idle/pressed (ATK/DEF/STEADY), timer bar fills, QTE marker/target, outcome icons (WIN/LOSS/TIE), position icons (1st/2nd), gap meter frame/fill | HUD and menu chrome at native 640x480 (B.5) | Native-res PNGs, 4 px corners on the stand-in | PNG, nearest; stance colours as hex (none are given) | Both builds: HUD, menu, finish screen |
| 16 | Menu logo placement / native-res logo variant | The main menu uses the approved V3 `v3_white_on_black.png`, downsampled to 384x71 with hard alpha. Please confirm the use and size, or supply a native-res pixel version | 1 PNG | PNG, nearest | Main menu shots |
| 17 | Mood/target frame for the Touge | No Touge mood render exists (B.3 is text only), so the build can't be judged against one | 640x480 frame | PNG | Touge comparisons |
