# Resource meters (unapproved concept)

Early visual study of a left-side race HUD stack for a resource system Austin is exploring. Nothing here is approved, and nothing is in the sim. Line selection stays the same; the meters are purely visual. Cost tables and empty-state rules are not decided. Pip counts and drain amounts in these frames are made-up for the mockup, not balance numbers.

Rendered in Godot 4.6.3 from the line-preview project (Gordon's two-corner Entry chase frame + the current PLAN THE LINE HUD). The 3D stays crunchy at 640×480 (RGB555 + Bayer, 2× nearest). The HUD, including this stack, is pixel-hard at 1280×960 with the same plate grain, bevel and type as the line-preview plates.

## What the meters are

Variants A–C sit on the left under LINE LOCK. Variant D sits in a single wide plate at the bottom left, mirroring PLAN THE LINE, clear of the car:

1. **FUEL** (POW, green `#2CB84A`) — gas-pump icon on A–D. Does not recover during the race. Aggressive POW lines burn the most.
2. **BRAKES** (EN, red `#E8282C`) — a wheel (tyre, rim, five spokes) with the brake rotor and caliper visible through the spokes, so it reads as the wheel-and-brake package. Does not recover during the race.
3. **SUSP** (HAN, yellow `#F0C828`) — shock-absorber icon. Spent by HAN lines, recovers each turn.

On-screen labels on A–D are FUEL / BRAKES / SUSP, each with a small framed POW / EN / HAN stat note. Behind the screen the stats stay POW / EN / HAN.

Variant **E** replaces the POW/fuel row with **HEAT**: a standard dashboard coolant-temperature symbol (thermometer dipping into wavy coolant lines) and a HEAT reading with a POW chip. The bar is heat headroom left. It drains as POW lines heat the engine and does not recover during the race. Low is an overheat warning (hot tint on the bar + an OVERHEAT tag). Empty is limp mode (dark trough + LIMP tag, no slash through the icon; POW unavailable). The bar stays POW green unless the warning needs the hot tint (`#FF701C`). The POW chip stays green.

## Variants (each shown at full)

- `a_full.png` — **A.** Slim stack: icon + vertical segmented bar + label, each on its own plate.
- `b_full.png` — **B.** Horizontal LINE LOCK-style slanted pips to the right of each icon. Three slim plates, same width as LINE LOCK.
- `c_full.png` — **C.** One combined plate. Segmented ring around each icon, plus a short pip track.
- `d_full.png` — **D.** One wide framed plate at the **bottom left**, mirroring PLAN THE LINE. Three small icons in a left column (pump, wheel+brake, shock). To the right of each icon, a long thin continuous bar in a framed trough, spanning most of the plate. No pips: the fill length is freeform (any width, with a slanted depleting edge) rather than discrete ticks. Austin, 2026-11-13: "the bars are more 'freeform' when depleting vs discrete ticks" and "it should be in the bottom left." The shock icon is drawn larger and bolder on this variant.
- `e_full.png` — **E1.** International Rally-style layout (Austin, 2026-11-13: that GBC shot "shows a better HUD design"). One flat dark band under the play area: compact continuous HEAT / BRAKES / SUSP on the left (icon + stat chip + trough, like the T/G/E/S column), LINE LOCK (continuous bar, no pips) and the corner map in the middle, PLAN THE LINE chips on the right. The top stays minimal: rear view, a tighter tie-gap, and a floating flat turn sign (from the first reference). The road and the car stay clear. Art direction is flat: solid panel fills, 1–2 px hard borders, no plate grain, no bevels, no sheen (Austin: "the correct art direction is flatter is better"). Applied to every HUD element in E.
- `e2_full.png` — **E2.** Same language, but LINE LOCK and the corner name sit in slim flat strips flanking the rear view, and the bottom band holds meters, the map, and the plan with a little more width. Use this if the single band in E1 feels tight.

**Strongest of A–C: B.** It shares LINE LOCK's width and pip language, so the left column reads as one family, and drain / low / empty / refill are the easiest to judge at a glance. A is the most compact, but the short vertical ticks are harder to count and the plates sit narrower than LINE LOCK. C is a good late-90s gauge alternative; the rings are distinctive, but they compete a little with the circular brake icon and the track only has six pips.

## State strip

States are rendered for every variant (`a_`, `b_`, `c_`, `d_`, `e_` prefixes; E2 has `e2_full` and `e2_low`). The A–C contact sheet uses B. Variants D and E use a continuous ghost fill in the trough instead of ghost pips.

- `*_drain.png` — After locking Entry OUT/POW. Fuel / HEAT drops; the lost amount stays as a ghost. Brakes and suspension stay full.
- `*_low.png` — Fuel / HEAT and brakes in the warning colour, with a LOW badge on A–D and an OVERHEAT tag on E (hot tint on the HEAT bar). Stands in for a blink.
- `*_empty.png` — A–D: fuel empty (slash through the icon + EMPTY badge, red plate outline). E: limp mode (dark trough, no slash, LIMP tag). Brakes low, suspension mid. Fuel / heat and brakes do not come back.
- `*_susp_spent.png` — After an Apex HAN pick. Suspension spent (ghost fill). Fuel still empty / heat still limp.
- `*_susp_refill.png` — Next turn. Suspension recovers (RECOVER badge, bright fill). Fuel / heat stays empty / limp and brakes stay low.

## Sheet

- `resource_meters_sheet.png` — row 1: A / B / C at full; rows 2–3: state strip for B (drain, low, empty, then susp spent / refill).
- `resource_meters_d_sheet.png` — variant D at full, plus its drain / low / empty / susp spent / refill states.
- `resource_meters_e_sheet.png` — variant E1 at full, plus its drain / overheat / limp / susp spent / refill states.
- `resource_meters_d_vs_e.png` — before / after: D next to E1 and E2, so the declutter and the flat bottom-band layout can be judged together.

**E vs D, what was trimmed or moved.** LINE LOCK, PLAN THE LINE and the HAIRPIN plate leave the play area and sit in the bottom band (E2 parks LINE LOCK and the corner name in slim top strips instead). Meter text labels drop; identity is icon + POW / EN / HAN chip. The tie-gap box is shorter. Plate grain, bevels and bar sheen are gone on every E HUD element. The floating turn sign replaces the large top-right corner plate as the upcoming-turn cue (the name, map and E/A/X stops remain, just smaller, in the band).

**E1 vs E2.** E1 is the closer read of the International Rally reference: one strip, the road fully clear above. Everything fits in the band, though the plan chips and the map are compact. E2 is easier to read if you want a little more air in the plan, at the cost of putting chrome back beside the rear view. **E1 reads better** — the play area is the point of the reference Austin marked, and the flat band is doing the work.

## Godot paths

- Project: `godot/project.godot`
- Scene: `godot/scenes/resource_preview.tscn`
- Scripts: `godot/scripts/resource_preview.gd`, `godot/scripts/hud.gd`, `godot/scripts/hud/resource_stack.gd`

Rebuild: `./run.sh` (needs `/workspace/tools/godot` 4.6.3 and the line-preview project at `../line_preview/godot`). Nothing here is approved until Austin says so.
