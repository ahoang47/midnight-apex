# Line preview mockup (unapproved)

B.5d during line select: a racing-line preview is drawn on the road as a row of flat chevrons, chaining phase by phase. These frames are rendered in Godot 4.6.3 from a **copy** of Gordon's two-corner editor scenes (`unapproved/gordon/two-corner/godot/scenes/`). Gordon's files are not edited. `run.sh` stages his track, dressing, cars, HUD and shaders into `godot/`, then overlays the files in this folder.

Pass 2 matches Gordon's current build (shots11) for the camera-stop frames: his left-hand Touge hairpin (`HAIRPIN L`), his chase / Apex / Exit camera stops, his in-world IN / MID / OUT lane markers, and his dark navy touge asphalt. His debug box is left out. The intended differences are the B.5d chevrons and the grain / bevel / heavier type on the plates.

## What the frames show

Overview frames use a high camera above and outside the left hairpin so the whole hook is visible. Camera-stop frames use Gordon's B.5b poses (same math as `main.gd`, framed like `prototypes/two-corner/out/shots11/gif_frames/f00030.png` for Entry and the Apex / Exit stops in that sequence). Road, lamps and pools are his touge dressing, not the earlier pack overlay, so the asphalt stays dark navy grey outside the sodium pools (B.2a). Grit reads mainly inside the pools.

Chevrons (B.5d, Austin 2026-11-12): painted flat on the road in the 3D layer, pointing in the direction of travel, evenly spaced. Each segment is solid in that segment's stance colour (ATK `#2CB84A`, DEF `#E8282C`, NEU `#F0C828`). A slight brightness ramp along a segment, no yellow-to-red gradient across the line. Confirmed segments are solid; the hovered segment is a lighter, slightly gapped variant. No glow.

Placeholder bends (until Austin approves): the Entry segment stays in the chosen Entry lane. The Apex segment starts where Entry ended; ATK cuts toward the inside by 2/3 of a lane width, DEF holds the outside line, NEU runs mid-lane. Exit starts where Apex ended and uses the same map.

### Overview (high camera)

1. `1_entry_out_atk.png` — Entry = OUT, hovering ATK at Entry.
2. `2_apex_def.png` — Entry locked OUT/ATK, Apex hovering DEF.
3. `3_apex_atk.png` — Same, Apex hovering ATK (the bend changes).
4. `4_exit_atk.png` — Entry IN/DEF, Apex NEU, Exit hovering ATK.
5. `5_locked.png` — All three locked.
6. `line_preview_sheet.png` — labelled contact sheet.

### Camera stops (B.5b, matching shots11)

1. `1_entry_out_atk_camstop.png` — same beat as overview 1, from the fixed chase camera. Rival visible (Entry tell). IN / MID / OUT lane markers on the road. Rear-view on.
2. `2_apex_def_camstop.png` — same beat as overview 2, from the Apex stop. Geometry only (no cars, no mirror).
3. `4_exit_atk_camstop.png` — same beat as overview 4, from the Exit stop. Geometry only.
4. `line_preview_camstops_sheet.png` — labelled contact sheet of those three.

## HUD layout (these frames only)

Austin 2026-11-12: the old bottom-left ENTRY IN/MID/OUT strip and the bottom-right PLAN THE LINE panel showed the same choices, so they are one panel, still bottom right. Three phase rows (ENTRY, APEX, EXIT). The active row is amber-highlighted with a caret; on Entry you pick the lane (IN / MID / OUT, left-corner on-screen order) and the stance (ATK / NEU / DEF) on that row; on Apex and Exit you pick the stance the same way. Locked rows keep the chosen lane (Entry) and stance plus the POW / HAN / EN chip. Pending rows show dashes. The bottom-left strip is gone. The race-split / tie-gap bar moves to the top centre, directly under the REAR VIEW label (the same slot when the mirror is off at the Apex and Exit stops). Gordon's files are untouched; this is only in the mockup HUD copies.

Pipeline: 3D at 640×480 with no AA, then RGB555 + 4×4 Bayer, then one 2× nearest upscale. The HUD is composited after that, drawn sharp and pixel-hard at 1280×960 (no font AA, 2 px hard shadow). Plates use a noisy fill, a hard bevel and light banding, with heavier titles, in a Racing Lagoon / Gran Turismo 2 direction. Stance colours are unchanged.

## Godot paths

- Project: `godot/project.godot`
- Scene: `godot/scenes/line_preview.tscn`
- Scripts: `godot/scripts/line_preview.gd`, `godot/scripts/line_chevrons.gd`
- HUD overlays (copies, not Gordon's originals): `godot/scripts/hud.gd`, `godot/scripts/hud/hud_panel.gd`, `godot/scripts/hud/corner_plate.gd`, `godot/scripts/hud/plan_panel.gd`

Rebuild: `./run.sh` (needs `/workspace/tools/godot` 4.6.3 and Gordon's two-corner project). Nothing here is approved until Austin says so.
