# Line preview mockup (unapproved)

B.5d during line select: a racing-line preview is drawn on the road as a row of flat chevrons, chaining phase by phase. These frames are rendered in Godot 4.6.3 from a **copy** of Gordon's two-corner editor scenes (`unapproved/gordon/two-corner/godot/scenes/`). Gordon's files are not edited. `run.sh` stages his track, dressing, cars, HUD and shaders into `godot/`, then overlays the files in this folder.

## What the frames show

The camera sits high above and behind the car so the whole right hairpin is visible. Pack-road asphalt from the urban stacked pack (`road1_alt`, composed as in the psx_road_test) replaces the generated touge recipe. More lamps (22 m period) and a slightly brighter, still cool, base gain so the grit reads off-pool as well as in the sodium pools. No orange wash.

Chevrons (B.5d, Austin 2026-11-12): painted flat on the road in the 3D layer, pointing along the drive, evenly spaced. Each segment is solid in that segment's stance colour (ATK `#2CB84A`, DEF `#E8282C`, NEU `#F0C828`). A slight brightness ramp along a segment, no yellow-to-red gradient across the line. Confirmed segments are solid; the hovered segment is a lighter, slightly gapped variant. No glow.

Placeholder bends (until Austin approves): the Entry segment stays in the chosen Entry lane. The Apex segment starts where Entry ended; ATK cuts toward the inside by 2/3 of a lane width, DEF holds the outside line, NEU runs mid-lane. Exit starts where Apex ended and uses the same map.

1. `1_entry_out_atk.png` — Entry = OUT, hovering ATK at Entry.
2. `2_apex_def.png` — Entry locked OUT/ATK, Apex hovering DEF.
3. `3_apex_atk.png` — Same, Apex hovering ATK (the bend changes).
4. `4_exit_atk.png` — Entry IN/DEF, Apex NEU, Exit hovering ATK.
5. `5_locked.png` — All three locked.
6. `line_preview_sheet.png` — labelled contact sheet.

Pipeline: 3D at 640×480 with no AA, then RGB555 + 4×4 Bayer, then one 2× nearest upscale. The HUD is composited after that, drawn sharp and pixel-hard at 1280×960 (no font AA, 2 px hard shadow). Plates use a noisy fill, a hard bevel and light banding, with heavier titles, in a Racing Lagoon / Gran Turismo 2 direction. Stance colours are unchanged.

## Godot paths

- Project: `godot/project.godot`
- Scene: `godot/scenes/line_preview.tscn`
- Scripts: `godot/scripts/line_preview.gd`, `godot/scripts/line_chevrons.gd`
- HUD overlays (copies, not Gordon's originals): `godot/scripts/hud.gd`, `godot/scripts/hud/hud_panel.gd`, `godot/scripts/hud/corner_plate.gd`, `godot/scripts/hud/plan_panel.gd`

Rebuild: `./run.sh` (needs `/workspace/tools/godot` 4.6.3 and Gordon's two-corner project). Nothing here is approved until Austin says so.
