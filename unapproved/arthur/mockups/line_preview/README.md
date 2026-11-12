# Line preview mockup (unapproved)

B.5d during line select: a racing-line preview is drawn on the road as a row of flat chevrons, chaining phase by phase. These frames are rendered in Godot 4.6.3 from a **copy** of Gordon's two-corner editor scenes (`unapproved/gordon/two-corner/godot/scenes/`). Gordon's files are not edited. `run.sh` stages his track, dressing, cars, HUD and shaders into `godot/`, then overlays the files in this folder.

Camera-stop frames match Gordon's current build (shots11): his left-hand Touge hairpin (`HAIRPIN L`), his chase / Apex / Exit camera stops, his in-world IN / MID / OUT lane markers, and his dark navy touge asphalt. His debug box is left out. The intended differences are the B.5d chevrons and the grain / bevel / heavier type on the plates.

## What the frames show

Overview frames use a high camera above and outside the left hairpin so the whole hook is visible. Camera-stop frames use Gordon's B.5b poses (same math as `main.gd`, framed like `prototypes/two-corner/out/shots11/gif_frames/f00030.png` for Entry and the Apex / Exit stops in that sequence). Road, lamps and pools are his touge dressing, not the earlier pack overlay, so the asphalt stays dark navy grey outside the sodium pools (B.2a). Grit reads mainly inside the pools.

Chevrons (B.5d): painted flat on the road in the 3D layer, pointing in the direction of travel, evenly spaced. Each segment is solid in that segment's stance colour (POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`). A slight brightness ramp along a segment, no yellow-to-red gradient across the line. Locked / hovered segments are solid (hovered is a lighter, slightly gapped variant). Not-yet-chosen follow-on segments use the same hue, dimmer. No glow.

Canonical sequence everywhere: Entry OUT + POW, Apex EN, Exit POW. Placeholder bends (Austin 2026-11-12): the Entry segment stays in the chosen Entry lane. The Apex segment starts where Entry ended; POW bends to the outer line of the corner, EN cuts toward the inner line by 2/3 of a lane width, HAN runs mid-lane. Exit starts where Apex ended and uses the same map. This matches the lanes: OUT = POW, IN = EN, MID = HAN, the same on left and right turns.

### Pass 3 stance variants (camera-stop framing)

One contact sheet, plus the individual PNGs. Implied follow-on segments are drawn dimmer.

- `a_entry_out_pow.png` — Entry stop, OUT hovering POW. Chevrons show the green Entry segment and continue into the implied Apex EN and Exit POW (dimmer).
- `b_apex_pow.png`, `b_apex_han.png`, `b_apex_en.png` — Apex stop, Entry locked OUT/POW, hovering POW / HAN / EN. Each Apex line starts where the Entry line ends, and also draws the Exit POW preview chained from that Apex end (dimmer green).
- `c_exit_pow.png`, `c_exit_han.png`, `c_exit_en.png` — Exit stop, Entry OUT/POW and Apex EN locked, hovering POW / HAN / EN. Each Exit starts from the Apex EN end. Segment colours: green, red, then the hovered colour.
- `line_preview_stance_variants.png` — row 1 Entry A (centred); row 2 Apex POW / HAN / EN; row 3 Exit POW / HAN / EN.

### Overview (high camera)

1. `1_entry_out_pow.png` — Entry = OUT, hovering POW at Entry (implied follow-on drawn).
2. `2_apex_en.png` — Entry locked OUT/POW, Apex hovering EN.
3. `3_apex_pow.png` — Same, Apex hovering POW (the bend holds the outer line).
4. `4_exit_pow.png` — Entry OUT/POW, Apex EN, Exit hovering POW.
5. `5_locked.png` — All three locked: OUT/POW, EN, POW.
6. `line_preview_sheet.png` — labelled contact sheet.

### Camera stops (B.5b, matching shots11)

1. `1_entry_out_pow_camstop.png` — same beat as overview 1, from the fixed chase camera. Rival visible (Entry tell). IN / MID / OUT lane markers on the road. Rear-view on.
2. `2_apex_en_camstop.png` — same beat as overview 2, from the Apex stop. Geometry only (no cars, no mirror).
3. `4_exit_pow_camstop.png` — same beat as overview 4, from the Exit stop. Geometry only.
4. `line_preview_camstops_sheet.png` — labelled contact sheet of those three.

## HUD layout (these frames only)

Combined PLAN THE LINE panel, bottom right. Three phase rows (ENTRY, APEX, EXIT). The active row is amber-highlighted with a caret. On Entry you pick the lane (IN / MID / OUT, left-corner on-screen order) and the stance (POW / HAN / EN) on that row; each lane carries a small note of the stat it needs (OUT = POW, MID = HAN, IN = EN). On Apex and Exit you pick the stance the same way. Locked rows show the chosen lane (Entry) and a single coloured stance chip (POW / HAN / EN) — there is no second tag chip. The hovered stance on the active row is the highlighted chip. Pending rows show dashes. The race-split / tie-gap bar sits at the top centre, directly under the REAR VIEW label (the same slot when the mirror is off at the Apex and Exit stops). Gordon's files are untouched; this is only in the mockup HUD copies.

Pipeline: 3D at 640×480 with no AA, then RGB555 + 4×4 Bayer, then one 2× nearest upscale. The HUD is composited after that, drawn sharp and pixel-hard at 1280×960 (no font AA, 2 px hard shadow). Plates use a noisy fill, a hard bevel and light banding, with heavier titles, in a Racing Lagoon / Gran Turismo 2 direction.

## Godot paths

- Project: `godot/project.godot`
- Scene: `godot/scenes/line_preview.tscn`
- Scripts: `godot/scripts/line_preview.gd`, `godot/scripts/line_chevrons.gd`
- HUD overlays (copies, not Gordon's originals): `godot/scripts/hud.gd`, `godot/scripts/hud/hud_panel.gd`, `godot/scripts/hud/corner_plate.gd`, `godot/scripts/hud/plan_panel.gd`

Rebuild: `./run.sh` (needs `/workspace/tools/godot` 4.6.3 and Gordon's two-corner project). Nothing here is approved until Austin says so.
