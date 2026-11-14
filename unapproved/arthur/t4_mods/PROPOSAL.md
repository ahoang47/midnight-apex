# T4 parts art — proposal (unapproved)

For Austin. Nothing here is final until he approves it.

**Canon (design/01, proto-build 68a1ecb):** T4 is the big Finale mods. They unlock when the PC wins the first training race after the rift (P1). Reiko sells them at full price. Wholesale is closed.

**Econ-v1 is not live.** This proposal and the mockup have no prices.

Rebuild the comparison frame with `./run.sh` (Godot 4.6.3). Frame: `t4_shop_compare.png`.

---

## 1. What exists today (T1–T3)

There is **no shop or garage UI art** to extend.

- `assets/ui/` is empty (`.gitkeep` only).
- Gordon has no shop or garage scripts on `proto-build`. The only Godot UI in play is the race HUD (E3B language: flat solid panels, 1–2 px hard borders, no bevel, gloss or grain; Archivo Black / Nimbus Sans Bold; pixel-hard at 1280×960).
- `design/07` §6.4 still has `PART_TIERS` as TBD, with placeholder names Street / Sport / Race / Rare. No part catalog (`sim/config/parts.json` is specified, not written). No official tier colours.
- Art direction already binds two things that matter here: **a fitted mod must change the silhouette or livery** (`art_direction.md` A.3), and **attach points are still open** (Q9: wing, hood, bumpers, wheels).
- Reiko has no character sheet. Her shop lives in Sabine's garage. After the rift she is businesslike and cool: she still sells, at full price, because she is a business owner (`story/plot.md` §2, Garage Crew Arcs).

So T1–T3 need a visual language before T4 can stand apart from them. This proposal sets all four tiers. Names on the mockup (Street Lip, Sport Spoiler, Race Wing, Finale Wing) are **stand-ins** until Barry's catalog exists.

---

## 2. Proposed T4 distinction

Same card anatomy at every tier: icon well, name, category, T# + rank stamp, primary / trade-off stat chips, a price row, a one-line "on the car" note. Tier is told by **border colour + stamp + how far the part's silhouette has stepped up**, not by a new card shape, glow, or rarity sparkle.

### Part icons

One icon family per category. The drawing is the part, seen clearly (here, a rear deck with the aero piece).

- **T1** stock-adjacent, dark steel, small shape (lip).
- **T2** cleaner metal, mercury-teal endplate accents, a real spoiler.
- **T3** machined pale steel, a proper race wing.
- **T4** a clearly bigger piece: taller wing, second element, larger endplates, a flat ice-teal mark on each plate. No bloom, no chrome rainbow, no neon.

Internal parts (engine, ECU, window) follow the same finish ladder even when the car-side mesh does not change.

### Shop card / frame

- Shared flat card: solid navy fill `#0A1020`, 2 px hard border, square corners, no grain or bevel.
- **T1** border and stamp: dim steel-navy `#3A4A68`.
- **T2** mercury `#5C8C98` (Mercury ambient from the tone study; teal, not a lamp).
- **T3** pale machined steel `#C4D0E0`. Not sodium. Sodium `#F0C894` sits too close to HAN `#F0C828` once a yellow chip is on the card, so it stays on world lamps only.
- **T4** ice teal `#A8D0C8` outer 2 px rule, plus a 1 px mercury inner rule. Optional flat `NEW` tag on first stock after P1. Selected card uses a slightly lighter fill, still flat.
- After the rift, the shop header reads **FULL PRICE** / **WHOLESALE CLOSED**. No figures.

### Garage view / install

Same frame language as the shop, not a second style. Loadout slots use the T# stamp and border of the fitted part. The 3/4 car well is the install view. On hover or confirm, a **flat 2 px outline in that tier's colour** traces the attached mesh. No glow sprite, no camera bloom.

### Car-side visual

**Recommendation: yes, a T4 part changes the car, but it is not a new shell.**

- Same attach points as T1–T3 (once Q9 is locked): wing, lip / bumper, hood, wheels.
- T4 is a bigger silhouette on those points (taller wing, deeper lip, denser hood vents, heavier wheel), plus a small ice-teal endplate or lip mark so a T4 car reads at race distance.
- Internal T4 parts that have no body attach stay icon-only on the car.
- Do not build a unique T4 body. Shells are a different system (canon 26).
- Budget still applies: ≤ 300 triangles per mod part (`art_direction.md` A.2).

---

## 3. Tier colour

| Tier | Marker | Hex | Role |
|------|--------|-----|------|
| T1 Street | dim steel-navy | `#3A4A68` | quiet stock |
| T2 Sport | mercury | `#5C8C98` | approved teal, used flat |
| T3 Race | pale steel | `#C4D0E0` | bright, not yellow |
| T4 Finale | ice teal + mercury inner | `#A8D0C8` / `#5C8C98` | top tier, no glow |

Reserved and not used as tier fills: POW `#2CB84A`, HAN `#F0C828`, EN `#E8282C`, hot orange `#FF701C`, sodium `#F0C894`. Menu room stays TXR-navy / blend50 (`#0B172B` family).

---

## 4. Asset list

Catalog size is TBD, so counts below assume the **six documented families**: primarily POW, primarily EN, primarily HAN, aero, window, and the unique/clash slot (v2). Aero and window each go in any slot. If Barry's catalog adds or cuts families, multiply or drop in step.

| Item | Count | Effort | Notes |
|------|------:|--------|-------|
| Category icon bases | 6 | M | One clear drawing per family (engine, brakes, susp, aero, window, unique). |
| Tier finishes on those icons | 6 × 4 = 24 | M | T1–T4 metal / silhouette steps. T4 must read as a bigger or tighter part. |
| Shop chrome | 1 set | S | Header, tabs, list, footer, FULL PRICE state. Flat E3B language. |
| Card frame + stamps | 4 | S | T1–T4 borders / stamps, including T4 double rule and NEW tag. |
| Shared card states | 6 | S | Rest, hover, selected, owned, locked, level-floor ("requires level N"). |
| Garage chrome | 1 set | M | Slot grid, 3/4 car well, install confirm. Same flat language. |
| Install outline | 4 colours | S | Flat 2 px trace in the tier colour. |
| Reiko shop moment | 1 still | S–M | Quiet `NEW STOCK` strip after P1, over-the-counter, no glow. Portrait only if we already have one; do not block T4 on a new Reiko sheet. |
| T1–T3 car meshes (if Q9 locks) | 4 attach × 3 = 12 | L | Existing gap, not T4-only. Wing, lip, hood, wheels. |
| T4 car meshes | 4 attach | M | Same points, bigger silhouette. No new shell. |
| T4 livery / endplate mark | 1 small atlas add | S | Flat ice mark, not a full livery. |

**Total unique drawings to approve this language:** 24 icons + 4 frames + shop/garage chrome + 1 unlock still = **about 32 2D assets**, then **4 T4 meshes** (and 12 T1–T3 meshes if we start the car-side program at the same time).

**Effort:** 2D language and the shop compare, about a short pass once approved. Car-side meshes wait on Q9 and are the longer piece (T4 alone is a few parts; T1–T3 as well is a real vehicle job).

Not in this pass: Reiko portrait, a full 3D shop interior, unique T4 shells, priced UI, substory-sidegrade art (those stay on the same frames with a different source tag, not a fifth tier).

---

## 5. Open questions for Austin

1. **Approve this T1–T4 colour ladder?** Steel-navy / mercury / pale steel / ice teal with a double rule. I kept sodium off the cards so it does not fight HAN yellow.
2. **Does a T4 part change the car model?** I recommend yes, on the existing attach points, not a new shell. If you want T4 icon-only for v1, say so and the meshes wait.
3. **Treat this as the language for all four tiers**, not a T4 skin on missing T1–T3 art?
4. **Placeholder rank names** Street / Sport / Race / Finale, or only T1–T4 stamps until Barry names the tiers? (07's "Rare" is a bad fit for T4; T4 is the finale set, not a drop rarity.)
5. **Unlock beat:** a quiet `NEW` / `NEW STOCK` strip in the existing shop, or a short over-the-counter still with Reiko (no new portrait required)?
6. **How many T4 SKUs** will the catalog actually have? Art multiplies from that number. Six families × one T4 each is the working assumption.

---

## 6. Mockup

`t4_shop_compare.png` — Reiko's parts shop, four aero cards in a row (T1–T4), current flat menu style, 1280×960, no prices (`—`). T4 is selected and tagged NEW, with the double ice / mercury rule and a visibly taller wing. Rendered in Godot 4.6.3 (not Blender, not a PIL-only final).
