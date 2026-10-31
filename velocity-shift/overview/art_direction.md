# Midnight Apex — Art Direction (v2 draft)

> **Status:** draft v2, owner Arthur (Art Director). Not yet signed off by the lead.
> **Restore note (2026-10-31):** the original v2 file was never committed and was lost when the art box was wiped
> (Oct 31 2026, ~11:31 AM PT). This file is a **reconstruction** from the approved skill text, the chat record,
> the surviving style-reference sheet and the S2000 build files. Structure (Parts A/B/C, Q1–Q9, K1–K7, Appendix W)
> and every binding rule match v2; wording, and any proposed numbers marked *(re-proposed)*, may differ from the lost text.

## How to read this doc

| Tag | Meaning |
|-----|---------|
| **[MUST]** | Binding. Applies to every vehicle asset. A car that breaks it fails review. |
| **[VIBE]** | Mood reference taken from the approved Tokyo v2 vibe-check scene. Not a standard. |
| **[PROPOSAL]** | Art's suggestion; needs the lead's (or Design's) approval before anyone relies on it. |
| **[OPEN]** | Unanswered question, listed in Part C. |

**Scope.** Only Part A is binding, and it covers **cars only** (lead's call, 2026-10-31: "The key rules are for the cars only.
The scene will likely not make it to the game."). The Tokyo v2 street scene was a vibe check to see a car in context;
everything about environments, districts, cameras, portraits and UI is in Part B as [VIBE] or [PROPOSAL].

**The look in one paragraph.** A PSX-leaning, early-PS2-era street racer at night: cheap geometry, rich hand-painted
textures, lighting and shine faked the way the hardware faked them, hard jaggy edges, banded 16-bit colour with ordered
dither. *Low poly is not low texture.* A modern/photoreal render with a retro filter on top is **not** the look — that
was tried (Tokyo v1) and rejected as "a cheap simulacrum of a PS2 game". The approved reference is Tokyo v2 and the
S2000 reference car (Appendix W).

Pitch alignment (`velocity-shift/story/high_level_story.md`): cars and environments lean **Initial D** (grounded tuning
culture, atmospheric roads); characters lean **JoJo** and are never rendered in-world (portraits/overlays only).

---

# Part A — Vehicle standard [MUST]

### A.1 Build from references
1. **[MUST]** Build every car from orthographic blueprints (top, front, rear, side). Scale to the real car's published
   length; when the drawing and the spec sheet disagree, note it in the asset README.
2. **[MUST]** Pass the silhouette-overlay gate: render orthographic silhouettes at the blueprint scale and compute IoU.
   **Side/top ≥ 0.95, front/rear ≥ 0.92.** *(Bar proposed by Art; see Q-list note.)* Keep the overlay images
   (`compare_side.png`, `compare_top.png`) with the asset.
3. **[MUST]** *(added 2026-10-31 after v2, from the BRZ build — pending lead review)* The IoU gate is necessary, not sufficient. Also check the **window line, roof line, hood/nose height and
   wheel size** against at least one real side photo, and compare 3/4 renders side by side with real 3/4 photos
   (lesson from the BRZ: a 98 % silhouette still hid a too-tall body with slit windows, because the blueprint drew the
   glass white like the background).
4. **[MUST]** *(added 2026-10-31 after v2, lead's request on the BRZ)* Shape sign-off at **clay**: stop at untextured grey clay and get the lead's approval of the shape before
   texturing and detailing.

### A.2 Geometry
1. **[MUST]** Budget **≤ 5,000 triangles** per car (body, glass, lamps, wheels, tyres, trim). Mod parts ≤ 300 triangles each.
2. **[MUST]** Smooth shading with crisp *intended* edges (marked sharp / split normals). No faceted flat shading, no
   wavy highlights on large panels (hood, doors) — fix the topology, don't hide it.
3. **[MUST NOT]** Model brakes/calipers, suspension, engine bay or interior. Glass is **opaque** — no interior needed.
4. **[MUST]** Stock body by default. Aftermarket parts only when asked; a mod must visibly change silhouette or livery.
5. Lamps, grilles, vents and badges are mostly painted, with only enough geometry to catch the silhouette (lamp
   recesses, intake openings).

### A.3 Textures — "low poly ≠ low texture"
1. **[MUST]** Painted body texture **1024²** with **baked AO** (crevices, panel gaps, wheel wells).
2. **[MUST]** Panel lines are **drawn as vector polylines** (single clean lines). Never trace panel lines from raster
   blueprint images (that produced doubled, sketchy pencil lines on the S2000).
3. **[MUST]** Parts atlas **256²** (lamp internals, grille mesh, wheel face, badges, plates). Fabric/trim sheets **512²**.
4. **[MUST]** Painted details: door handles, fuel lid, lamp internals (projectors, reflectors, LED strips), grille mesh,
   tyre sidewall lettering (must read correctly on both sides — mirror the UVs, not the text), plates flat on their bracket.
5. **[MUST]** Quantise textures to ~5 bits/channel (RGB555) with ordered (Bayer) dither at authoring time; import
   lossless (PNG), no texture compression that smears the dither.
6. **[MUST]** Made-up names, badges, plates and liveries. **No real brands or logos.** Shared body mesh + swappable
   livery texture/material (player vs opponent, per Appendix E of `godot_prototype.md`).
7. Avoid decals wrapped over strong curvature — they bend; put plates/badges on flat sub-panels.

### A.4 Materials and faked shine
1. **[MUST]** No ray-traced, SSR, probe or PBR reflections. Shine is faked:
   `colour = albedo × (ambient + key·N·L) + blinn_spec(key) + envmap(reflect(V,N)) × fresnel`,
   with a fixed ambient, **one** key direction, Blinn specular and a **painted equirect environment map** read by the
   reflection vector. Env-map strength **≤ 0.45** at grazing angles.
2. **[MUST]** Glass: opaque, dark, **cool-tinted** (blue/cyan cast) with the same env-map shine. An untinted env map
   turns glass orange under sodium light — tint it.
3. **[MUST]** Lamps emissive; head and tail lamps get additive **glow sprites/billboards** that travel with the car.
4. **[MUST]** Ground contact is a **blob shadow** decal (no shadow maps on the car). Headlight throw on the road is a
   decal at reduced strength (full strength floods the foreground).

### A.5 Review frame
1. **[MUST]** Review every car in the reference frame: **640×480** *(Q3)*, no anti-aliasing, integer **nearest**
   upscale, **RGB555 + 4×4 Bayer** dither. Also provide clean 1280 turntable-angle renders (front 3/4, rear 3/4,
   side, front) for shape review. *(The lead was asked on 2026-10-31 whether car review should keep this frame now that
   running the whole game at it is only a proposal — see Q3.)*
2. **[MUST]** Run the vehicle checklist (A.7) and list known weak spots honestly in the hand-off.

### A.6 Deliverables per car
`.blend` (with blueprint planes packed as viewport-only references), `.glb` (engine import), optional `.obj/.mtl` and
`.fbx`, body/atlas/fabric PNGs, the build script(s), the IoU overlays and a few key renders, plus a short `README.md`
(tri count, IoU, references, known deviations). Repository layout: `art/vehicles/<car_id>/` (see C.1).

### A.7 Vehicle checklist (must pass)
- [ ] Silhouette IoU passes the gate; window/roof/hood/wheel lines checked against photos; clay signed off
- [ ] ≤ 5,000 triangles; no brakes, interior, engine
- [ ] Crisp single panel lines; no UV seams visible on body
- [ ] Plates flat; tyre lettering reads correctly on both sides
- [ ] Shine reads as a painted env map (not mirror, not plastic); glass cool-tinted, not orange
- [ ] Lamps glow (emissive + sprites); blob shadow present
- [ ] No real brands; livery separable from body
- [ ] Checked in the reference frame (A.5)

### A.8 Godot 4.x (Mobile renderer) notes for vehicles *(sketch, untested in Godot)*
- Vehicle material: `render_mode unshaded;` shader that does the A.4 formula with uniforms for ambient, key direction,
  spec power, env equirect `sampler2D` and fresnel; no scene lights affect the car.
- Render 3D into a low-res `SubViewport` (no MSAA/FXAA/TAA), nearest-upscale to the window, then one quantise/dither
  pass (RGB555 + 4×4 Bayer) as a canvas shader.
- glTF clamps vertex colours to 0–1: store at half scale, double in the shader.

```glsl
shader_type spatial;
render_mode unshaded, cull_back;
uniform sampler2D albedo_tex : source_color, filter_nearest_mipmap;
uniform sampler2D env_equirect : source_color;
uniform vec3 key_dir = vec3(0.4, 0.8, 0.3);
uniform float ambient = 0.55;
uniform float spec_power = 48.0;
uniform float env_strength = 0.45;
varying vec3 wn; varying vec3 wv;
void vertex() { wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
                wv = normalize((MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz - CAMERA_POSITION_WORLD); }
void fragment() {
  vec3 n = normalize(wn); vec3 l = normalize(key_dir); vec3 v = -normalize(wv);
  vec3 alb = texture(albedo_tex, UV).rgb * COLOR.rgb * 2.0;
  float diff = ambient + max(dot(n, l), 0.0) * (1.0 - ambient);
  float spec = pow(max(dot(n, normalize(l + v)), 0.0), spec_power);
  vec3 r = reflect(-v, n);
  vec2 euv = vec2(atan(r.z, r.x) / 6.2831853 + 0.5, acos(clamp(r.y, -1.0, 1.0)) / 3.1415927);
  float fres = env_strength * pow(1.0 - max(dot(n, v), 0.0), 2.0) + 0.08;
  ALBEDO = alb * diff + vec3(spec) + texture(env_equirect, euv).rgb * fres;
}
```

---

# Part B — Scene, world and presentation guidance [VIBE] / [PROPOSAL]

Nothing in Part B is binding. It records what made the Tokyo v2 vibe check work so environment work (if any) starts
from the right place.

### B.1 What made Tokyo v2 read as PSX/PS2 [VIBE]
- **Everything unlit:** `texture × vertex colour → linear fog → emission`. Lighting is painted into textures and vertex
  colours, including **stepped sodium-light pools** painted onto the road texture (banded, not smooth gradients).
- **Dry, matte road.** No wet roads, puddles, mirror floors or screen-space reflections (lead: "I think it's dumb").
- **Linear fog** colour-matched to the painted sky (v2 used ~14–105 m), skyline as painted cards.
- **Signs:** unlit, full-bright neon textures plus additive glow billboards; made-up shop names only; flat ribbon wires.
- **Props:** dense, cheap alpha-cutout cards (bikes, bins, menu boards, cones, roadworks barrier), vending machines
  pre-lit, sidewalks lit by vertex colour.
- **Facades:** pre-lit night textures × vertex light; lit and dark windows, window lettering, AC units.
- **Car in scene:** fake env-map shine + Blinn spec, emissive lamps + glow sprites, blob shadow, headlight-throw decal.
- **Frame:** native 640×448, 1 sample, no AA (filter size 0), Standard view transform (no filmic), **bloom on neon
  only**, then RGB555 + 4×4 Bayer, then 2× nearest upscale (1280×896).
- **Composition:** storefronts never brighter than the car; avoid big flat cartoony panels in the hero shot.
- Scene budget was ~12k triangles including the car.

### B.2 Tokyo v2 palette [VIBE] (from the style-reference sheet)
| Group | Hex |
|---|---|
| Car | body paint `#C70D0F`, panel line `#2C0406`, soft top `#1E1E20`, head glow `#FFF2CC`, tail glow `#FF1F14` |
| Light | sodium `#FF9947`, road ambient `#9597AD`, vertex ambient `#ADADC8`, warm window `#FFD28C`, cool window `#B4E1FF`, dark window `#161C2A` |
| Sky/fog | zenith `#060614`, horizon `#42284A`, city glow `#784246`, fog `#30263F`, skyline `#120E1C` |
| Walls | `#C4B8A0` `#8E8A84` `#96523C` `#D6D2C8` `#6E7C88` `#A8A074` `#604032` `#5A826E` `#E2D4B4` `#80788C` `#B8B0AA` `#464850` |
| Neon | `#FF3C8C` `#3CC8FF` `#FFAA28` `#78FF78` `#C85AFF` `#FF4632` |
| Signage | konbini `#6E3CAA` / `#FAC828`, drug `#285ADC`, parking `#14783C`, cleaning `#DC283C`, cone `#F05014` |

### B.3 Districts [PROPOSAL]
Each district needs its own identity (pitch). Values below are Art proposals for sign-off (Q2); the original v2 numbers
were lost with the box and are **re-proposed** here.
- **Touge** (mountain roads, fog-heavy, narrow visibility): cold desaturated greens/blue-greys, sparse sodium/white
  lamps, guardrails and cedar cards. Fog colour ≈ `#2A3236`, near/far ≈ 8–55 m *(re-proposed)*.
- **Wangan** (highway, neon horizon): deep navy sky with a magenta/orange horizon band, long sodium lamp rows, concrete
  barriers, distant lit skyline cards. Fog ≈ `#1C1A30`, near/far ≈ 30–220 m *(re-proposed)*.
- **Urban Street** (structured loops, "Americanized scene" — meaning open, Q1): Tokyo v2 palette is the starting point if
  it's an import scene on Japanese streets; fog ≈ `#30263F`, 14–105 m (as v2).

### B.4 Cameras [PROPOSAL]
- **Overworld:** angled semi-isometric (Racing Lagoon / PS1 Final Fantasy). Perspective with a long lens vs true
  orthographic is open (Q8).
- **Race:** third-person cinematic chase framing; car readable at 640×480.
- **QTE:** dramatic close-ups and perspective shifts; same frame rules.

### B.5 Characters, portraits, UI [PROPOSAL]
- Characters never appear in-world. JoJo-style 2D portraits/overlays use the same low-res, limited-palette treatment
  (palette size open, Q7). Whether painted silhouettes behind shop windows count as "characters in-world" is open (Q5).
- Faces follow `face_{scowling|grinning|focused}_{atk|def|neu}.png` and `tell_*` overlays (Appendix E).
- Stance colours (Attack / Defend / Neutral-or-Steady) should be reserved for UI and not used for world neon
  *(proposal; stance name is Q6)*.
- Bitmap-style font, 9-slice panels drawn at native resolution.

### B.6 Engine-side environment notes [PROPOSAL]
- Unlit + vertex-colour environment shader with linear fog uniform; no dynamic lights or shadows on art.
- Glow sprites as additive billboards; blob shadows as decals/quads.
- Road kit per Appendix E (`road_straight` ~30 units, `road_corner_left/right`, `barrier_*`), one tiling track texture
  with painted light pools baked per segment.

### B.7 Scene mockup checklist [advisory]
- Fog meets the sky; storefronts not brighter than the car; no mirrored text or visible cut-out backs; no ground
  reflections, only blob shadows; no wet road.

---

# Part C — Naming, layout, open questions, doc conflicts

### C.1 Naming and folders
- Lowercase snake_case, `category_variant_direction` (from `godot_prototype.md` Appendix E), e.g. `road_corner_left`,
  `face_grinning_atk.png`, `car_s2000_body.png`.
- Source-art layout (in use from 2026-10-31, see `art/README.md`):
  `art/vehicles/<car_id>/` → `README.md`, build script(s) at the top level, exports (`.glb`, `.blend`, optional
  `.obj/.mtl/.fbx`) and textures (`<car_id>_body.png`, `_atlas.png`, ...) beside them, `tex/` texture painters,
  `bp/` blueprint extraction + IoU, `ref/` blueprints, `renders/` (a few key renders + IoU overlays).
  `art/mood/<name>/` → vibe-check scenes (scripts + small previews). Engine-ready copies go under `res://assets/...`
  when the game imports them *(proposal)*.

### C.2 Open questions for the lead
- **Q1** Urban Street "Americanized": a Tokyo-Drift-style import scene on Japanese streets, or actual American streets?
- **Q2** Approve the Touge and Wangan palettes and fog distances (B.3).
- **Q3** Resolution: 640×480 (project setting, current default) or 640×448 (approved shots)? And should **car review**
  keep the low-res reference frame (A.5) now that running the whole game at it is only a proposal?
- **Q4** Texture filtering: smooth (as in the approved shots) or sharp/unfiltered (harder PS1 feel)?
- **Q5** Do customer silhouettes painted into shop windows break "characters never rendered in-world"?
- **Q6** Third stance name for art/UI files: **Neutral** or **Steady**?
- **Q7** Portrait palette limit (e.g. 32 or 64 colours per portrait)?
- **Q8** Overworld camera: perspective (long lens) or orthographic?
- **Q9** Mod attach points: which parts are swappable (wing, hood, bumpers, wheels) and where they attach?

Also pending: confirm the IoU bar (A.1.2), reserving stance colours for UI (B.5).

### C.3 Doc conflicts found while writing (for Design)
- **K1** `godot_prototype.md` says "Low-poly PS1-style" car body; the approved reference car is ~4.4k tris (PS2-era
  budget). Proposal: reword to "low-poly PSX/early-PS2 style, ≤ 5k tris".
- **K2** Third stance called "Neutral" in some docs and "Steady" in lockout tables/UI asset list (Q6).
- **K3** Pitch says three Myth Drivers; plot outline and Sabine's sheet mention a fourth.
- **K4** Project display is 640×480; the approved vibe-check frames were 640×448 (Q3).
- **K5** "Night-only city" vs the story opening that establishes normal daytime life (needs a daytime look or a cut).
- **K6** Appendix E lists one car body shared by both cars; the art pipeline now has multiple models (S2000, BRZ) —
  shared-body-plus-livery still holds per model.
- **K7** Urban Street is "an Americanized scene" while inspirations and the vibe check are Japanese (Q1).

---

# Appendix W — Worked example: Honda S2000 (AP1, stock soft top)

Reference car for Part A. Source: `art/vehicles/s2000/`.
- **Build:** procedural Blender 4.2 script (`build_s2000.py`) from a four-view blueprint; 4.14 m long, wheelbase
  2.41 m as measured on the drawing, soft top as black fabric ending at the rear deck (trunk lid in body paint).
- **Triangles:** 4,354. **IoU:** side 0.961, top 0.992, front 0.925, rear 0.944.
- **Textures:** `s2000_body.png` (1024², vector panel lines, baked Cycles AO, quantised), `s2000_atlas.png` (256²
  parts), `s2000_softtop.png` (fabric).
- **Rules applied:** opaque cool-tinted glass, no interior, no calipers, made-up badges/plate, smooth shading.
- **History of mistakes (don't repeat):** guessed proportions before using a blueprint; flat colour with no texture;
  panel lines traced from the raster blueprint; a modern render + retro filter; a wet mirror road; untinted env map
  making glass orange; over-spec'd parts (hardtop, calipers, interior) the lead didn't need.
- **Vibe check:** Tokyo v2 night street (Part B) — mood reference only.
