# mod_skill: fixed slot layout POW / HAN / EN + 1 flex (Austin t428u, 2026-11-18), spirit OFF

The same 4 slots in every round replace the per-district kits (PPHE Street, PHEE Wangan/Touge). The spirit meter is cut, so all win numbers come from the live tables or the live SimulationRunner with no spirit.
Kept unchanged: X = 0.60, the B3 setup base, spill, Mk1 list prices, catch-up, stock 3000, and the target ratios.
Files:
- `fixed_layout.py`: the layout model and the full-build tune check.
- `run_fixed.py` → `fixed_layout.json`: XP recalibration (the calibrate.py method) and the story / mixed / hard walks.
- `boss_engine_check.py` → `boss_engine_check.json`: engine boss checks.

## Flex choice
The flex slot is one physical mod. Its own stat (X floor) is set per round: **P in Street, E in Wangan, E in Touge**. That gives the same stat mix as the old PPHE / PHEE / PHEE, but the earned points carry over and nothing is stranded.

Full build at the cap, tune distance by flex choice:

| Flex | Street | Wangan | Touge |
|---|---|---|---|
| P / E / E (picked) | 0 | 0 | 0 |
| Free (no floor) | 0 | 0 | 0 |
| P everywhere | 0 | 1.29 (outside the share band) | 0 |
| H everywhere | 0.75 | 1.29 | 1.76 |

The free flex gives identical walk results to P / E / E.

## Ceilings (earned points per mod over stock)
Total points do not depend on the layout, and an on-tune full build exists in every round, so the ceilings come out the same as before.

| Round | Old ceiling / cap | New ceiling / cap | Exact for target ratio | Boss r at the cap (unclamped / live-clamped) | Target |
|---|---|---|---|---|---|
| R1 | 133 / 3532 | **133 / 3532** | 132.75 | 1.0443 / 1.0440 | 1.044 |
| R2 | 261 / 4044 | **261 / 4044** | 260.66 | 1.0554 / 1.0548 | 1.055 |
| R3 | 407 / 4628 | **407 / 4628** | 407.105 | 1.0709 / 1.0702 | 1.071 |

R3 at 407 falls 0.0001 short of r 1.071 when power is not clamped; 408 (4632) would reach it. The live cap power of 462.51 clamps both to r 1.0702, so I kept 407.

## XP (the calibration needs a change)
- **Story table:** the R1 boss XP drops from 154.3 to **26.5**. The old table paid extra to refill the Wangan E2 mod after the Street P2 points were stranded; with the fixed layout nothing is stranded. All other story XP entries are unchanged, and there is no shortfall anywhere.
- **Grind XP per win:** **13 / 12 / 14** (was 13 / 15 / 14). This matches the live mixed grind counts of 13 / 13 / 12.
- **Grind wins:**
  - Mixed walk: 13 / 13 / 12.
  - Hard walk: 13 / 14 / 18.
  - Filling a whole tier from grinds only: 532/13 = 41, 512/12 = 43, 584/14 = 42 wins.
- **With the old calibration held fixed** (R1 boss story XP 154.3, grind XP 13 / 15 / 14), story R2 carries extra points: R2 80/80 low is 62.8 vs 54.2, and R2 mixed grinds are 11 vs the live 13. That is why the table changes.

## Walks with the new calibration (P / E / E flex)
Columns: grinds; 80/80 low; boss 60/60 / 80/80; boss r; end points.

| Walk | R1 | R2 | R3 |
|---|---|---|---|
| Story | 0; 52.9; 0.2 / 52.9; 0.9954; 3393 | 0; 54.2; 0.7 / 57.7; 1.0056; 3946 | 0; 50.5; 1.5 / 55.9; 1.0288; 4517 |
| Mixed | 13; 81.9; 31.6 / 94.9; 1.044; 3532 | 13; 73.7; 39.5 / 90.6; 1.0548; 4044 | 12; 73.3; 30.3 / 92.9; 1.0702; 4628 |

- Story-only 80/80 stays at or above 50 everywhere (lowest 50.5).
- Max tune distance is 0 in every walk.
- XP lost past ceilings in the mixed walk: 30.1 / 93.0 / 82.7 (was 157.9 / 98.0 / 82.7).

## Boss checks at the cap, spirit off (60/60 ≥ 30, 80/80 ≤ 95)

| Boss | Table | Engine (9000 races, ± SE) | Result |
|---|---|---|---|
| Street, r 1.044 | 31.6 / 94.9 | 32.26 ± 0.49 / 94.74 ± 0.24 | Pass, but 80/80 is only about 1 SE under 95 |
| Wangan, r 1.0548 | 39.5 / 90.6 | 38.82 ± 0.51 / 90.99 ± 0.30 | Pass |
| Touge, r 1.0702 | 30.3 / 92.9 | 30.73 ± 0.49 / 92.72 ± 0.27 | Pass, 60/60 has 0.7 of headroom |

Street r scan in the engine (60/60 / 80/80):
- r 1.042: 28.48 / 93.91
- r 1.040: 25.34 / 93.56
- r 1.036: 18.83 / 91.40

So 1.044 is the only tested Street r that passes both checks. Below it, 60/60 fails. The Street boss works at its live ratio with spirit off.
