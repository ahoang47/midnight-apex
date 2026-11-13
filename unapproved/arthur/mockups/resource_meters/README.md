# Resource meters (unapproved concept)

Early visual study of a left-side race HUD stack for a resource system Austin is exploring. Nothing here is approved, and nothing is in the sim. Line selection stays the same; the meters are purely visual. Cost tables and empty-state rules are not decided. Pip counts and drain amounts in these frames are made-up for the mockup, not balance numbers.

Rendered in Godot 4.6.3 from the line-preview project (Gordon's two-corner Entry chase frame + the current PLAN THE LINE HUD). The 3D stays crunchy at 640×480 (RGB555 + Bayer, 2× nearest). The HUD, including this stack, is pixel-hard at 1280×960 with the same plate grain, bevel and type as the line-preview plates.

## What the meters are

Variants A–C sit on the left under LINE LOCK. Variant D sits in a single wide plate at the bottom left, mirroring PLAN THE LINE, clear of the car:

1. **FUEL** (POW, green `#2CB84A`) — gas-pump icon. Does not recover during the race. Aggressive POW lines burn the most.
2. **BRAKES** (EN, red `#E8282C`) — a wheel (tyre, rim, five spokes) with the brake rotor and caliper visible through the spokes, so it reads as the wheel-and-brake package. Does not recover during the race.
3. **SUSP** (HAN, yellow `#F0C828`) — shock-absorber icon. Spent by HAN lines, recovers each turn.

On-screen labels are FUEL / BRAKES / SUSP, each with a small framed POW / EN / HAN stat note. Behind the screen the stats stay POW / EN / HAN.

## Variants (each shown at full)

- `a_full.png` — **A.** Slim stack: icon + vertical segmented bar + label, each on its own plate.
- `b_full.png` — **B.** Horizontal LINE LOCK-style slanted pips to the right of each icon. Three slim plates, same width as LINE LOCK.
- `c_full.png` — **C.** One combined plate. Segmented ring around each icon, plus a short pip track.
- `d_full.png` — **D.** One wide framed plate at the **bottom left**, mirroring PLAN THE LINE. Three small icons in a left column (pump, wheel+brake, shock). To the right of each icon, a long thin continuous bar in a framed trough, spanning most of the plate. No pips: the fill length is freeform (any width, with a slanted depleting edge) rather than discrete ticks. Austin, 2026-11-13: "the bars are more 'freeform' when depleting vs discrete ticks" and "it should be in the bottom left." The shock icon is drawn larger and bolder on this variant.

**Strongest of A–C: B.** It shares LINE LOCK's width and pip language, so the left column reads as one family, and drain / low / empty / refill are the easiest to judge at a glance. A is the most compact, but the short vertical ticks are harder to count and the plates sit narrower than LINE LOCK. C is a good late-90s gauge alternative; the rings are distinctive, but they compete a little with the circular brake icon and the track only has six pips.

## State strip

States are rendered for every variant (`a_`, `b_`, `c_`, `d_` prefixes). The A–C contact sheet uses B. Variant D uses a continuous ghost fill in the trough instead of ghost pips.

- `*_drain.png` — After locking Entry OUT/POW. Fuel drops; the lost pips stay as ghosts. Brakes and suspension stay full.
- `*_low.png` — Fuel and brakes in the warning colour (amber outline and pips), with a LOW badge on fuel. Stands in for a blink.
- `*_empty.png` — Fuel empty (slash through the icon + EMPTY badge, red plate outline). Brakes low, suspension mid. Fuel and brakes do not come back.
- `*_susp_spent.png` — After an Apex HAN pick. Suspension spent (ghost pips). Fuel still empty.
- `*_susp_refill.png` — Next turn. Suspension recovers (RECOVER badge, bright fill). Fuel stays empty and brakes stay low.

## Sheet

- `resource_meters_sheet.png` — row 1: A / B / C at full; rows 2–3: state strip for B (drain, low, empty, then susp spent / refill).
- `resource_meters_d_sheet.png` — variant D at full, plus its drain / low / empty / susp spent / refill states.

## Godot paths

- Project: `godot/project.godot`
- Scene: `godot/scenes/resource_preview.tscn`
- Scripts: `godot/scripts/resource_preview.gd`, `godot/scripts/hud.gd`, `godot/scripts/hud/resource_stack.gd`

Rebuild: `./run.sh` (needs `/workspace/tools/godot` 4.6.3 and the line-preview project at `../line_preview/godot`). Nothing here is approved until Austin says so.
