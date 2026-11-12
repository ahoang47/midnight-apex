# slots-v2 follow-up: fixes for the strong-player mature #2 skips (V1, V2)

> **Status (2026-11-12):** Austin approved **b3**, the crew-local level floor ("Oh, neat. Yes approved.", 6:55 AM PT). It is live in the sim, and its approved record is `design/notes/slots-v2/README.md` (b3 section), which **supersedes the b3 parts of this file**. Fixes **a, a0, b, b2 and c were not chosen**. The rest of this file is kept as the study record and is **not approved**.

Barry [sim], 2026-11-11. Austin asked (10:58 PM PT): "sim the fixes for the strong mature #2 skips". This is a study only. Nothing here is live.

**Live constants used:** the approved `KNOT_WINDOW_105` r = 1.00 knot of 0.67, the aero free pool ≤ 10%, and `sim/config/winrate_n4000.json` as rebuilt in 5e5d902.

**Method:** the same share-aware oracle and statistical bar as `RESULTS.md`.
- 244-point share grid, N = 4000 races, 9 paired banks (seeds 20261113–15 × 10/20/30 turns).
- A rung is **clear** when its pooled mid is ≥ 50.
- A newest mod is **decisive** when the rung isn't clear without it and is clear with it.

**Schedule:** slots-v1 scheme C. j = 3 is mature #2 and j = 6 is the crew boss.

**Forced-player convention:** if a rung isn't clear at the skip state, the player grinds to the rung's level cap.

**Profiles:** weak, average, strong. **Policies:**
- balanced 2/2/2
- window: one window mod
- aero10: one aero part with a 10% pool

**Files:**
- `fixes.py` writes `results_fixes.json` and `fixes.log`.
- `fix_summary.py` writes `results_fixes_summary.json`.
- `floor_cost.py` writes `results_floor_cost.json`.
- The grid banks (`counts/`, about 44 MB) stay in `/workspace/barry-drafts/slots-v2/` and are not committed.

## The problem (base, live constants)

The strong player clears two mature #2 rungs without grinding, and in both the newest mod is decisive:
- **V1: R1 Wangan j3**, 47.86 → 52.49.
- **V2: R2 Touge j3**, 47.84 → 52.67 (48.03 → 52.67 with aero10).

Under the live knot, average and weak have no decisive rungs.

## Fixes simmed

| Fix | What changes |
|---|---|
| **a** | P2 grind-matched prices (from `RESULTS.md`). The wallet earns +1 per race and starts at 0. Prices: R1 Touge 1.73, R1 Wangan 3.17, R1 Street 3.33, R2 Wangan 1.73, R2 Street 3.5, R2 Touge 3.5, R3 Street 1.91, R3 Touge 3.67, R3 Wangan 3.67. |
| **a0** | Same as a, but the R1 opening set is pre-funded. |
| **b** | Level floor on the mature #2 tier: floor = rung level cap. A gated tier is released at the first later rung where the player meets the floor. |
| **b2** | Floor = the level of a player who never grinds, + 1. |
| **b3** | Crew-local floor = the level of a player who reached the previous boss's cap and has not ground in this crew, + 1. |
| **c** | The tier unlocked by mature #2 is delayed one rung, so it is first equipped at j = 4. |

## Results

### Grind races over the whole game

| Fix | Weak (bal / win / aero10) | Average | Strong | Decisive (any policy) | Dead wins |
|---|---|---|---|---|---|
| base | 141 / 141 / 141 | 153 / 153 / 153 | 121 / 121 / 121 | **V1, V2** | 9 |
| a | 141 / 141 / 141 | 145 / 143 / 143 | 180 / 181 / 181 | **R2 Street j3** 47.86 → 52.42 (48.07 → 52.42 aero10); **R1 Touge j3** 37.48 → 59.79 (window, aero10) | 9 |
| a0 | 141 / 141 / 141 | 153 / 153 / 153 | 171 / 171 / 171 | **R2 Street j3** (as in a) | 9 |
| b | 141 / 141 / 141 | 153 / 153 / 153 | 197 / 197 / 197 | none | 9 |
| b2 | 141 / 141 / 141 | 153 / 153 / 153 | 106 / 106 / 106 | **V2 remains** (R2 Touge j3 47.84 → 52.67) | 9 |
| **b3** | 141 / 141 / 141 | 153 / 153 / 153 | **100 / 100 / 100** | **none** | **9** |
| c | 141 / 141 / 141 | 153 / 153 / 153 | 100 / 100 / 100 | none | **18** |

### Margins at the walls (balanced)

Each cell gives the pooled mid range at skip over the 9 mature #2 and 9 boss rungs. Columns:
- **Min margin:** the smallest margin below 50 among the forced walls.
- **Max forced mid:** the highest mid at a forced wall.

| Fix | Profile | Mature #2 mid at skip | Boss mid at skip | Forced walls | Min margin | Max forced mid |
|---|---|---|---|---|---|---|
| base | weak | 16.00–16.54 | 9.50–9.60 | 18 | 33.46 | 16.54 |
| base | avg | 46.67–46.87 | 48.78–49.05 | 18 | 0.95 (window 0.93, aero10 0.49) | 49.05 |
| base | strong | 47.90–82.78 | 53.37–86.42 | 1 | 2.10 (aero10 1.96) | 47.90 |
| a | weak | 0.01–13.50 | 4.13–7.78 | 18 | 36.50 | 13.50 |
| a | avg | 0.92–43.75 | 42.34–49.33 | 18 | 0.67 | 49.33 |
| a | strong | 24.06–82.82 | 34.92–86.26 | 4 | 5.53 | 44.47 |
| a0 | avg | 30.64–46.87 | 48.78–49.05 | 18 | 0.95 | 49.05 |
| a0 | strong | 33.57–82.82 | 34.92–86.26 | 4 | 5.53 | 44.47 |
| b | weak | 14.94–15.76 | 9.50–9.60 | 18 | 34.24 | 15.76 |
| b | avg | 35.96–38.48 | 48.78–49.05 | 18 | 0.95 | 49.05 |
| b | strong | 42.16–81.08 | 48.11–82.87 | 6 | **0.89** | 49.11 |
| b2 | strong | 47.86–82.65 | 53.37–86.42 | 2 | 2.10 | 47.90 |
| **b3** | weak | 16.00–16.54 | 9.50–9.60 | 18 | 33.46 | 16.54 |
| **b3** | avg | 38.48–46.87 | 48.78–49.05 | 18 | 0.95 (aero10 0.49) | 49.05 |
| **b3** | strong | 41.84–82.65 | 53.37–86.42 | 3 | 2.14 (aero10 1.97) | 47.86 |
| c | weak | 14.94–15.76 | 9.50–9.60 | 18 | 34.24 | 15.76 |
| c | avg | 35.96–38.48 | 48.78–49.05 | 18 | 0.95 | 49.05 |
| c | strong | 41.84–81.08 | 53.37–86.42 | 3 | 2.14 | 47.86 |

Two notes on margins:
- The average player's 0.95 / 0.49 pp margins are the existing knife-edge boss walls (`RESULTS.md`). They are the same in every fix except a, where the margin is 0.67.
- None of the fixes makes the average margin worse except a.

## Feel cost of each fix

**a / a0 (P2 prices): rejected.**
- They add a new strong violation (R2 Street j3) and leave R1 Touge exposed.
- Under a, R1 Touge starts with 0 mods: weak/avg kid mid is 0.01, and mods lag on 63 rungs for weak and avg.
- Grind moves onto the kids and mature #1.
- Strong gets new boss walls: R1 Street 38 grind, R3 Touge 50.

**b (floor = cap): fixes V1/V2 but is harsh.**
- Strong grind goes 121 → 197.
- Strong gets new boss walls: R1 Street 40, R2 Wangan 41, R3 Street 49.
- Strong min margin falls to 0.89.
- 43 strong rungs run below their scheduled mods.

**b2 (global no-grind floor): doesn't fix V2.**

**b3 (crew-local floor): fixes both with no new violations and the same 9 dead wins.**
- *Weak:* identical to base.
- *Average:* only one cell changes. R1 Touge j3's skip mid drops 46.79 → 38.48, because the tier is gated at L3 < floor 4. Average still grinds 7 there, and mid at cap stays 72.4.
- *Strong at the two fixed rungs:*
  - V1, R1 Wangan j3: now forced. The floor is L14 vs L8 at skip. **6 grind races reach the floor**, where the full loadout clears at 80.87 (grind to cap is 13).
  - V2, R2 Touge j3: floor L83 vs L77. **7 races to the floor**, then 80.87 (grind to cap is 16).
- *Strong elsewhere:*
  - R3 Touge j3 was already a strong grind wall (18) and is unchanged.
  - R2 Wangan j3 is gated by 1 level (53 vs 54), so strong clears it without the tier at 51.39.
  - Total strong grind goes down, 121 → 100. That is an artifact of the grind-to-cap convention: grinding at mature #2 levels up the old-head walls. Old-head grind is removed (R1 Wangan 19 → 0, R2 Wangan oh5 28 → 0, R2 Touge 22 → 0), with a new R2 Wangan oh4 grind of 19.
- *UI cost:* the mature #2 tier shows a "requires level N" lock until the player has ground about one level past where a no-grind run arrives.

**c (delay the tier to j = 4): also no violations, but worse.**
- Dead wins double (9 → 18), because the mature #2 win no longer unlocks anything new.
- The 105% cap isn't reached at mature #2. Average mid at cap falls from 72.09–72.51 to 69.95–71.15.

## Recommendation

**b3, the crew-local level floor on the mature #2 tier.** It is the only fix that:
- removes both V1 and V2 under all three policies;
- adds no decisive rung and no dead win;
- leaves weak and average grind and boss margins unchanged.

The cost lands only on strong players who skip, about 6–7 grind races per affected crew.

If b3 goes live:
- Its floors would be per-crew constants derived from the progression tables (`LOCAL_L` + 1 in `fixes.py`; values in `results_floor_cost.json`): R1 Touge L4, R1 Wangan L14, R1 Street L26, R2 Wangan L54, R2 Street L71, R2 Touge L83, R3 Street L111, R3 Touge L128, R3 Wangan L140.
- `sim/tests` would need a test that no strong-profile mature #2 is decisive.
