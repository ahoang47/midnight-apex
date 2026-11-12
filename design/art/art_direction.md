# Midnight Apex — Art Direction (v2 draft)

> **Status:** draft v2, owner Arthur (Art Director). Not yet signed off by the lead, except the race-camera
> gap and lane Entry bullets in B.4, which Austin locked on 2026-11-06. Part A and the rest of Part B are unchanged.
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
everything about environments, districts, cameras, portraits and UI is in Part B as [VIBE] or [PROPOSAL], except the
race-camera gap and lane Entry bullets in B.4, which Austin locked on 2026-11-06.

**The look in one paragraph.** A PSX-leaning, early-PS2-era street racer at night: cheap geometry, rich hand-painted
textures, lighting and shine faked the way the hardware faked them, hard jaggy edges, banded 16-bit colour with ordered
dither. *Low poly is not low texture.* A modern/photoreal render with a retro filter on top is **not** the look — that
was tried (Tokyo v1) and rejected as "a cheap simulacrum of a PS2 game". The approved reference is Tokyo v2 and the
S2000 reference car (Appendix W).

Pitch alignment (`story/pitch.md`): cars and environments lean **Initial D** (grounded tuning
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
5. **[MUST]** *(added 2026-10-31 from the BRZ rebuild — pending lead review)* **Trust the blueprint; classify its lines
   before you override it.** When the blueprint seems to disagree with a photo, the usual cause is misread lines: glass
   or DLO edges taken for body edges, or the other way round. A low or small photo camera solve causes it too. Trace and
   classify the blueprint lines (body silhouette, glass/DLO, lamps, trim), then build from the blueprint alone, the
   S2000 way. Photos are a final visual check (A.1.3) and never set geometry. *(Correction to the lesson in A.1.3: the
   BRZ blueprint was right. Passes 2–3 misread its window lines and trusted a low photo camera. The blueprint-only
   pass 4 fixed the shape.)*
   *(Binding from 2026-10-31, lean rebuilds.)* Classification covers every line you build from, not just the silhouette:
   tell **body lines** (shutlines, arch edges, bumper and pocket edges) from **lamp/lens outlines** and glass before
   modelling a feature, and record them in the car's keyline table. The blueprint is the truth for lamp shape, lamp depth
   (side and top views) and arch gap; photos only confirm.

### A.2 Geometry
1. **[MUST]** Budget **≤ 2,000 triangles max per car**, everything included: body, glass, lamps, wheels, tyres,
   struts/arms, trim and FX quads (glow sprites). Mod parts ≤ 300 triangles each. Geometry carries the silhouette and
   the wheel arches; the **detail work lives in the shading and textures** (A.3, A.4), not in extra loops.
2. **[MUST]** Smooth shading with crisp *intended* edges (marked sharp / split normals). No faceted flat shading, no
   wavy highlights on large panels (hood, doors) — fix the topology, don't hide it.
3. **[MUST NOT]** Model brakes/calipers, engine bay or interior. Glass is **opaque** — no interior needed. Suspension
   is modelled only as the simple strut + arm rig in A.2.7, nothing more detailed.
4. **[MUST]** Stock body by default. Aftermarket parts only when asked; a mod must visibly change silhouette or livery.
5. Lamps, grilles, vents and badges are mostly painted, with only enough geometry to catch the silhouette (lamp
   recesses, intake openings). Headlamps follow A.2.8.
6. **[MUST]** **Mono body mesh:** the body is one mesh with the aero (spoiler, lips, skirts, mirrors) merged in. Separate
   objects only for the four wheels, the steering pivots and the strut follow nodes (A.2.7).
7. **[MUST]** **Suspension + steering rig:**
   - Wheels are separate objects, each pivoted at its hub centre; front wheels steer about a vertical pivot at the hub.
   - Body origin at the car's estimated centre of mass, so the engine's vehicle body (e.g. Godot `VehicleBody3D` with
     one `VehicleWheel3D` per corner) behaves without offsets.
   - Suspension travel about **±4–5 cm**, or less where the blueprint's arch gap does not allow it. Steering lock **±30°**.
   - **9-pose clearance test** before hand-off: full lock left / centre / full lock right × full bump / static / full
     droop, no wheel–body intersection in any pose. Keep the clearance report with the asset.
   - A simple **strut + arm** per corner on a separate **non-spinning follow node** that tracks only wheel position and
     steer (never wheel spin). Document the engine setup (node names, wheel radius, travel) in the asset README.
8. **[MUST]** **Headlamps: light molding + painted lamp art.** Give each headlamp a little real geometry — a shallow
   pocket (a few cm deep, depth from the blueprint side/top views) or a thin raised surround — traced from the
   blueprint's lamp outline (A.1.5). Do not over-carve the nose. Pocket walls/surround are dark trim. The lamp itself is
   **painted** on the lens faces (housing rim, projector/reflector with hotspot, inner lamp, indicator, lens highlight),
   with UVs planar to the lens so the art reads true in the front view, and a value range that does not clip to white
   after RGB555 + dither and the faked shine.

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
   livery texture/material (player vs opponent, per Appendix E of `design/godot-build-guide.md`).
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
- [ ] ≤ 2,000 triangles incl. wheels, struts and FX; mono body mesh; no brakes, interior, engine
- [ ] Rig: hub-pivoted wheels, origin at est. CoM, travel/lock per A.2.7, 9-pose clearance passes
- [ ] Headlamps: light molding (shallow pocket or thin surround) + painted lamp art that does not clip
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
- **Frame:** native 640×448 *(vibe check; the game standard is now 640×480, Q3 resolved)*, 1 sample, no AA (filter size 0), Standard view transform (no filmic), **bloom on neon
  only**, then RGB555 + 4×4 Bayer, then 2× nearest upscale (1280×896).
- **Composition:** storefronts never brighter than the car; avoid big flat cartoony panels in the hero shot.
- Scene budget was ~12k triangles including the car.

### B.2a Night palette: navy/teal + pale sodium [APPROVED 2026-11-11]
Approved by the lead (2026-11-11). This is the world palette for night scenes and **supersedes the warm sodium,
fog, sky and ambient values in B.2** (warm orange washes read as PS3/360). Source preset: `blend50` ("B HALF TEAL")
in `unapproved/arthur/mockups/tones/work/tones.py` (the rest of that study is unapproved).
| Group | Value |
|---|---|
| Sky/fog | fog `#0B172B`, zenith `#010408`, no city-glow band |
| Ambient | ambient `#5575A0` at 0.8 strength |
| Lamps | **every** street lamp is one pale cream sodium `#F0C894` (no alternating lamp colours); lamp strength 0.85 |
| Pools | hard painted pools, **3 steps**, pool strength 0.09 |
| Post | bloom 0.22 strength, 0 threshold; saturation 1.05 |
Orange stays on lamps and highlights only, over the cool navy/teal base with dark blue-black shadows.
B.2's car, window, wall, neon and signage colours still apply until re-checked against this base.

### B.2 Tokyo v2 palette [VIBE] (from the style-reference sheet)
*Sodium, sky/fog and ambient rows superseded by B.2a.*
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
- **Urban Street** (structured loops): a Tokyo Drift style import scene on **Japanese streets** (Q1, resolved
  2026-11-11). Uses the B.2a palette (fog `#0B172B`); fog distances 14–105 m as v2.

### B.4 Cameras [PROPOSAL]
- **Overworld:** angled semi-isometric (Racing Lagoon / PS1 Final Fantasy). Perspective with a long lens vs true
  orthographic is open (Q8). This overworld note is not the race camera.
- **Race (locked 2026-11-06; the rest of Part B is still proposal):** fixed rear third-person camera on the player.
  The player locks the 3-card line before corner playback. The rival's Entry pick is a stat (**POW**, **HAN** or **EN**), relative to the next corner. On screen that pick is drawn in the matching lane: POW on OUT, HAN on MID, EN on IN. POW on a left turn and POW on a right turn are the same choice, even though the OUT lane sits on opposite sides of the road.
  Entry can bluff by improper placement. Apex and Exit are
  inferred, not drawn as tells. Shared Touge, Wangan, and Street tendencies are the intended inference; the precise
  mapping is still TBD, and the older Aggressive, Defensive, and Precise rows are not that map. When the player is
  behind, draw the rival no farther ahead than keeps that lane readable from this camera. No distance number is
  approved; readability tests set it later. That cap is drawn
  spacing only. Cumulative DP, position, and the win condition stay on the real gap, and visible spacing does not
  show the exact size of a large lead. When the player is ahead, the trailer recedes in the top-center rear-view
  mirror. Distance makes headlights and lane harder to read, so the leader gets less Entry information. That is
  intentional. Do not "fix" it with a HUD lane marker, bigger lamps, or a cap on how far behind the rival is drawn.
  The mirror is the car's rear-view mirror, not a wet-road or screen-space reflection. B.1's dry-road rule still stands.
  Full rule: `design/06-pattern-read.md` (Lane Entry and visual gap). This lock does not change the project
  display (640×480, viewport stretch, keep aspect, in `project.godot`) and does not settle Q3 (that setting vs the
  640×448 vibe-check frames). A higher-resolution / CRT trial was an experiment only.
- **QTE:** dramatic close-ups and perspective shifts; same frame rules. QTE close-ups are not a reason to enlarge
  the mirror's lamps or to mark the trailer's lane.

### B.5 Characters, portraits, UI [PROPOSAL]
- Characters never appear in-world. JoJo-style 2D portraits/overlays use the same low-res, limited-palette treatment
  (palette size open, Q7). Whether painted silhouettes behind shop windows count as "characters in-world" is open (Q5).
- **Naming (Austin, 2026-11-12):** behind the screen, choices, stances, colours and playback logic are always **POW / EN / HAN**. **OUT / MID / IN** is visual only: road lane markers, on-screen stance-selection labels, lane-chip text, and where the chevrons sit physically. On the PLAN THE LINE panel, the ENTRY, APEX and EXIT rows all label the choices **OUT / MID / IN**, each with a small stat chip (**OUT · POW** green #2CB84A, **MID · HAN** yellow #F0C828, **IN · EN** red #E8282C). The pick itself is the stat. Example: the POW segment is green and is drawn on the OUT lane. POW on a left turn and POW on a right turn are the same choice. (Austin follow-up, 2026-11-12: "stance selection should say in/mid/out for all, with a chip explaining stat.")
- Faces follow `face_{scowling|grinning|focused}_{pow|en|han}.png` and `tell_*` overlays. Existing Appendix E filenames still use the suffixes `_atk|_def|_neu`, which map to **POW / EN / HAN**; player-facing labels use the new names.
- **POW / EN / HAN** colours should be reserved for UI and not used for world neon
  *(proposal)*. **POW** is `#2CB84A` (green), **EN** is `#E8282C` (red), **HAN** is `#F0C828` (yellow, dark text). Austin swapped the green and red on 2026-11-11 (under the old Attack/Defend names they had been POW `#E8282C` and EN `#2CB84A`). The third stance is **HAN** (Q6, resolved 2026-11-11 as the third stance, renamed HAN on 2026-11-12).
- Bitmap-style font, 9-slice panels drawn at native resolution.

### B.5b Line select: camera stops [APPROVED 2026-11-11]
Selection walks the corner before the line locks. **Entry:** the fixed chase camera, rival visible in its Entry lane
(the only tell). The player picks their Entry card. **Apex:** the camera moves to the corner apex and the player picks their
Apex card. **Exit:** the camera moves to the exit and the player picks their Exit card. At the Apex and Exit stops the
corner is shown **without the rival**: those stops show geometry only. The player gleans the rival's Apex/Exit from its
Entry, district tendencies, corner geometry and the lead/gap, never from an on-screen tell. Once all three are set the line
locks, the camera returns to Entry, and playback runs with the B.5a line-vs-line panel. Corner plate (top right)
marks the current stop E / A / X. Reference frames: `art/ui/line_select_cam/` (older Apex and Exit chips there are placeholders).
On-screen stance selection on the ENTRY, APEX and EXIT rows is written **OUT · POW**, **MID · HAN**, **IN · EN**. The pick itself is the stat. Road markers stay IN / MID / OUT.

### B.5c Crunchy 3D, sharp UI [MUST, APPROVED 2026-11-11]
The 3D scene is rendered at **native 640×480 with no anti-aliasing**, then **RGB555 + 4×4 Bayer** is applied, then a
**single 2× nearest-neighbour upscale** to 1280×960. The UI is composited **after** that upscale, drawn sharp at the
full 1280×960 output resolution, **pixel-hard**: no font or edge anti-aliasing, a hard 2 px drop shadow, bold chunky late-90s type and plates (Austin 2026-11-11, 10:21 PM to Gordon and 11:12 PM to Arthur). Larger screens scale the whole frame by whole numbers. Texture filtering inside the 3D scene follows Q4 (smooth) and is not affected.
Review images and contact sheets are judged from full-size frames; downscaled sheets are for layout only.

### B.5d Line preview during selection [APPROVED 2026-11-12, Austin]
While the player is choosing (B.5b camera stops), draw a racing-line preview on the road showing the path their choices
make. The line is built **phase by phase and chains**: the Entry segment starts from the chosen Entry stat and is drawn on that stat's lane; the Apex
segment **starts where the Entry segment ends** and its path changes with the Apex stat being hovered; the Exit
segment starts where the Apex segment ends and follows the Exit stat. Changing an earlier pick redraws every later
segment. Confirmed segments stay solid, and the hovered segment updates live as the player scrolls POW / EN / HAN. Visual
treatment (Austin 2026-11-12): a row of **flat chevrons painted on the road**, pointing in the direction of travel,
evenly spaced along the path, drawn in the 3D layer (subject to B.5c crunch). Each segment's chevrons take that
segment's stat colour, solid (**POW** #2CB84A, **EN** #E8282C, **HAN** #F0C828). The POW segment is green and is drawn on the OUT lane, HAN yellow on MID, EN red on IN. There is no yellow-to-red gradient across
the line; a slight brightness ramp along a segment is fine. The hovered segment uses a lighter or pulsed variant.
No glow or soft edges. Purely visual (Austin 2026-11-12): it does not
affect scoring and has no sim/ values. Where the chevrons sit (Arthur, placeholder until Austin approves; earlier draft was flipped): the **POW** segment holds the outer line of the corner (drawn on the OUT lane), the **EN** segment cuts across the full lane width to the inner line (drawn on the IN lane), and the **HAN** segment runs mid-lane (drawn on the MID lane); each segment starts from the previous end point.
The PLAN THE LINE panel (bottom right in the line-preview frames) has ENTRY, APEX and EXIT rows. Every row labels the choices **OUT / MID / IN**, each with a small stat chip (**OUT · POW**, **MID · HAN**, **IN · EN**), the same style on all three rows. The position text (OUT / MID / IN) is unframed; directly under it the stat (POW / HAN / EN) sits in its own small framed box with a pixel-hard plate-style border, filled in the stat colour (POW green #2CB84A, HAN yellow #F0C828, EN red #E8282C). There is no frame around the whole chip. The selected choice is marked by a highlight behind the position text and a brighter stat frame. Apex and Exit do not use plain POW / HAN / EN labels. The pick itself remains the stat (behind the screen, B.5 naming).

### B.5a Corner playback: line vs line [APPROVED 2026-11-11]
During the corner playback cinematic, show the LINE LOCKED panel with two rows, YOU and RIVAL, and both full 3-card
lines face-up from the start (no hidden cards, no flips) so the player can learn rival patterns. Columns are ENTRY /
APEX / EXIT; the column being played gets the amber outline, and the RESULT row (WIN / LOSS / TIE) fills in as each
phase plays. The corner plate (top right) shows the current phase. No pause or clash card beats. Reference frames:
`art/ui/line_vs_line/`. (Selection flow: B.5b.)

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
- Lowercase snake_case, `category_variant_direction` (from `design/godot-build-guide.md` Appendix E), e.g. `road_corner_left`,
  `face_grinning_pow.png`, `car_s2000_body.png`. Existing Appendix E face/tell files still use `_atk|_def|_neu` (POW / EN / HAN).
- Source-art layout (in use from 2026-10-31, see `art/README.md`):
  `art/vehicles/<car_id>/` → `README.md`, build script(s) at the top level, exports (`.glb`, `.blend`, optional
  `.obj/.mtl/.fbx`) and textures (`<car_id>_body.png`, `_atlas.png`, ...) beside them, `tex/` texture painters,
  `bp/` blueprint extraction + IoU, `ref/` blueprints, `renders/` (a few key renders + IoU overlays).
  `art/mood/<name>/` → vibe-check scenes (scripts + small previews). Engine-ready copies go under `res://assets/...`
  when the game imports them *(proposal)*.

### C.2 Open questions for the lead
- ~~Q1~~ **Resolved 2026-11-11:** Urban Street is a Tokyo Drift style import scene on Japanese streets.
- **Q2** Approve the Touge and Wangan palettes and fog distances (B.3).
- ~~Q3~~ **Resolved 2026-11-11:** game resolution is **640×480**. (Whether car review keeps the low-res frame in A.5
  is still worth confirming.)
- ~~Q4~~ **Resolved 2026-11-11:** textures use **smooth filtering**.
- **Q5** Do customer silhouettes painted into shop windows break "characters never rendered in-world"?
- ~~Q6~~ **Resolved 2026-11-11:** the third stance is **HAN** (resolved as the third stance on 2026-11-11, then called Neutral; renamed HAN on 2026-11-12).
- **Q7** Portrait palette limit (e.g. 32 or 64 colours per portrait)?
- **Q8** Overworld camera: perspective (long lens) or orthographic?
- **Q9** Mod attach points: which parts are swappable (wing, hood, bumpers, wheels) and where they attach?

Also pending: confirm the IoU bar (A.1.2), reserving POW / EN / HAN colours for UI (B.5).

### C.3 Doc conflicts found while writing (for Design)
- **K1** `design/godot-build-guide.md` says "Low-poly PS1-style" car body; the car budget is now ≤ 2,000 tris per car
  (A.2.1, 2026-10-31; the first reference builds were ~4.4k). Proposal: reword to "low-poly PSX/early-PS2 style,
  ≤ 2k tris per car incl. wheels".
- **K2** *(resolved by Q6 and the 2026-11-12 naming rule)* The third stance is **HAN**. Older Neutral / Steady / NEU labels are retired.
- **K3** Pitch says three Myth Drivers; plot outline and Sabine's sheet mention a fourth.
- **K4** *(resolved by Q3: 640×480)* Project display is 640×480; the approved vibe-check frames were 640×448 (Q3).
- **K5** "Night-only city" vs the story opening that establishes normal daytime life (needs a daytime look or a cut).
- **K6** Appendix E lists one car body shared by both cars; the art pipeline now has multiple models (S2000, BRZ) —
  shared-body-plus-livery still holds per model.
- **K7** *(resolved by Q1: Japanese streets)* Urban Street is "an Americanized scene" while inspirations and the vibe check are Japanese (Q1).

---

# Appendix W — Worked example: Honda S2000 (AP1, stock soft top)

Reference car for Part A. Source: `art/vehicles/s2000/`.
- **Build:** procedural Blender 4.2 script (`build_s2000.py`) from a four-view blueprint; 4.14 m long, wheelbase
  2.41 m as measured on the drawing, soft top as black fabric ending at the rear deck (trunk lid in body paint).
- **Triangles:** 4,354. **IoU:** side 0.961, top 0.992, front 0.925, rear 0.944. *(This is the original reference
  build, kept for history. The game version is the ≤ 2,000-tri lean rebuild in `art/vehicles/s2000/lean/`, see its README.)*
- **Textures:** `s2000_body.png` (1024², vector panel lines, baked Cycles AO, quantised), `s2000_atlas.png` (256²
  parts), `s2000_softtop.png` (fabric).
- **Rules applied:** opaque cool-tinted glass, no interior, no calipers, made-up badges/plate, smooth shading.
- **History of mistakes (don't repeat):** guessed proportions before using a blueprint; flat colour with no texture;
  panel lines traced from the raster blueprint; a modern render + retro filter; a wet mirror road; untinted env map
  making glass orange; over-spec'd parts (hardtop, calipers, interior) the lead didn't need.
- **Vibe check:** Tokyo v2 night street (Part B) — mood reference only.
