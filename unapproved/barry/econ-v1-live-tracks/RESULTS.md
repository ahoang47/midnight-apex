# econ-v1 recalibrated to the live stand-in tracks, round 2: bosses on the hardest track (DRAFT, Barry, 2026-11-13)

**Status: DRAFT. Not approved.** Nothing in `sim/` is edited, and nothing is committed or pushed.

Austin's pick (Nov 13 2026): tune each boss to the **hardest** live track in its district.
- Street boss: S1 Shibuya.
- Wangan boss: W3 C1 Outer.
- Touge boss and finale F1/F4: T3 Usui.

Targets at the cap, on that track: 60/60 at 30% or better, and 80/80 around 90–95%.

Round 1, which tuned Wangan to its district mean, is kept in `RESULTS_round1.md` and `proposed_constants_round1_superseded.json`. The method is unchanged except as noted below.

## Changes from round 1
- **Wangan hard cell.** The Wangan 30-turn hard cell is now W3 (`HARD_WANGAN=W3_C1_Outer` in `econ_patch.py`).
- **Oracle.** It merges the exact-r point checks (`ORACLE_POINTS`) on top of `sweep_main.json` and `sweep_confirm30.json`.
- **New measurements.** `point_confirm_hardest.json` covers W3 at r 1.044–1.055 and T3 at 1.073–1.077, N = 3000 per style.
- **Monotone ladder.** The ladder fit now forces each rung's r to be at least the boss r, so the ladder never steps back up.

## Boss and finale table (at cap, hardest track, measured)

| Fight | Track | r | 60/60 | 60/80 | 80/60 | 80/80 | N per style | Pass? |
|---|---|---:|---:|---:|---:|---:|---|---|
| R1 Street boss | S1 Shibuya | 1.044 | 31.6 | 72.4 | 71.0 | 94.9 | 3000 | ✓ |
| R2 Wangan boss | W3 C1 Outer | 1.055 | 39.7 | 63.0 | 80.7 | 90.7 | 3000 | ✓ |
| R3 Touge boss | T3 Usui | 1.071 | 31.9 | 69.2 | 70.2 | 93.5 | 3000 | ✓ |
| F1 Touge | T3 Usui | 1.075 | 34.7 | 72.6 | 74.1 | 94.7 | 3000 | ✓ |
| F2 Wangan | W3 C1 Outer | 1.058 | 41.7 | 64.2 | 84.2 | 92.5 | 1500 | ✓ |
| F3 Street | S1 Shibuya | 1.044 | 31.6 | 72.4 | 71.0 | 94.9 | 3000 | ✓ |
| F4 Touge | T3 Usui | 1.075 | 34.7 | 72.6 | 74.1 | 94.7 | 3000 | ✓ |

All three districts now have an r that meets both targets, so there's no forced trade-off. The choices:
- **Wangan W3** (N = 3000, 60/60 / 80/80):

  | r | 60/60 | 80/80 |
  |---|---:|---:|
  | 1.044 | 27.2 | 87.9 |
  | 1.046 | 30.3 | 86.4 |
  | 1.048 | 32.6 | 88.8 |
  | 1.050 | 35.5 | 89.6 |
  | 1.052 | 36.2 | 89.5 |
  | 1.055 | 39.7 | 90.7 |

  1.055 is the lowest measured r with 80/80 at 90 or above, so 60/60 has a wide margin there. The cost is that 60/80 is only 63.0 on W3.
- **Touge T3** (N = 3000, 60/60 / 80/80): 1.071 gives 31.9 / 93.5, 1.073 gives 34.2 / 94.1, 1.075 gives 34.7 / 94.7, and 1.077 gives 36.8 / 95.0. The R3 boss stays at 1.071. F1 and F4 move to 1.075, as Austin suggested.
- **Street S1**: 1.044 gives 31.6 / 94.9. That is inside the new 90–95 band, so it is no longer a trade-off.

Other tracks at these r, for reference (merged oracle, lower N):
- Street district mean: 42.9 / 96.3.
- Wangan district mean: 54.4 / 95.5.
- Touge district mean: 41.4 / 94.6.

## Proposed constants (`proposed_constants.json`)

| Ladder r (kid1 kid2 mat1 mat2 oh1 oh2 boss) | Live | Proposed |
|---|---|---|
| Street | 1.20 1.16 1.10 1.07 1.065 1.058 1.053 | 1.20 1.159 1.095 1.071 1.065 1.058 **1.044** |
| Wangan | 1.18 1.16 1.11 1.08 1.06 1.048 1.040 | 1.18 1.16 1.11 1.08 1.06 **1.055 1.055** |
| Touge | 1.18 1.16 1.12 1.085 1.075 1.070 1.066 | 1.182 1.163 1.132 1.097 1.079 1.071 **1.071** |

Wangan oh2 is lifted to the boss r so the ladder stays non-increasing.

**Boss budgets (C / r):**
- Street: 335.33 → 338.22.
- Wangan: 388.72 → 383.19.
- Touge: 434.19 → 432.16.

**Finale:**
- r\*: (1.066, 1.040, 1.053, 1.066) → **(1.075, 1.058, 1.044, 1.075)**.
- B is unchanged, so C = 531.91 / 599.15 / 676.72 / 797.54.
- **Caps: L63 / 76 / 95 / 114 → L64 / 79 / 94 / 115.** The climb ends at **L115**, one level past the locked "about L114". Steps are +18 / +15 / +15 / +21 from L46.
- Each r\* is the r players actually get at the whole-number cap.
  - F2 is set to 1.058 rather than 1.055. At 1.055 the cap would round to L78, which only delivers r = 1.053.

**Arc budgets (B), recomputed** with econ-v1's 80/80-reference logic:

| Race | Live B | Proposed B |
|---|---:|---:|
| P2 | 409.03 | 412.29 |
| P3 (wall r_design 1.020 → 1.025) | 483.25 | 480.89 |
| P4 | 461.15 | 464.83 |
| M11 | 438.11 | 441.61 |
| M12 | 546.53 | 555.28 |
| M21 | 485.77 | 497.48 |
| M31 | 564.89 | 560.43 |

P1, M22 and M32 are unchanged.

## Campaign walk (`hardest.json`, `hardest.txt`)

| | R1 Street | R2 Wangan | R3 Touge |
|---|---|---|---|
| Mixed 60/80 and 80/60: wall rung, wall + to cap | mat1 3 + 9 = 12 | mat1 3 + 9 = 12 | mat1 4 + 8 = 12 |
| 60/60 hard grind total | 12 | 15 | 18 |
| Mixed end cash | $10,600 | $41,190 | $77,100 |
| 80/80 story-only end level / cash | L8, $7,000 ($3,000 debt) | L26, $27,000 | L43, $54,000 |

**80/80 story-only floors** (lowest district / hard WR per round):
- R1: boss 70.4 / 61.6 (S1).
- R2: oh1 54.1, and boss 67.1 / 67.2 (W3).
- R3: oh1 59.8 / 50.4, and mat2 60.1 / 51.1 (T3).

**Mixed 10-turn grind WR at the wall** (60/80 / 80/60, then 60/60):
- R1: 98.2 / 99.2, and 92.1.
- R2: 90.1 / 94.4, and 76.8.
- R3: 88.3 / 93.1, and 71.4.

## Finale arc (wall / to-cap grind per step: pre-F1, F1→F2, F2→F3, F3→F4)

| Profile | Per step | Total per step | End |
|---|---|---|---|
| 60/80 | 4/3, 4/2, 1/5, 4/3 | 7, 6, 6, 7 | L115, $77,790, 5 T4 + aero |
| 80/60 | 5/1, 4/2, 2/4, 6/1 | 6, 6, 6, 7 | L115, $77,047.50, 5 T4 + aero |
| 60/60 | 11, 7, 7, 9 | **11** (pre-F1), 7, 7, 9 | L115, $91,732.50 |
| 80/80 story-only | 0 | 0 | L112, $31,075, 5 T4 + aero |

- 80/80 story-only lowest hard WR is 59.3 (M12). Billed fights are 81.7 / 82.7 / 79.3 / 81.7.
- 60/60 billed hard WR in the walk is 34.7 / 41.7 / 31.6 / 34.7.
- The arc evaluator reports no issues.
- 60/60's pre-F1 step is 11 grinds; it was 10 in econ-v1. The arc checks only cap mixed players at 10.

## Criteria
| # | Result |
|---|---|
| 1 Shop / caps | PASS |
| 2 Mixed grind 3–6 + 8–10, flat | PASS (12 / 12 / 12) |
| 3 80/80 story ≥ 50 | PASS (thin: R3 oh1 50.4, mat2 51.1 on T3) |
| 4 10-turn grind | PASS |
| 5 Floors | PASS |
| 6 Debt / betting | PASS |
| 7 Level jumps | PASS |
| 8 Finale reachable | PASS |
| 9 (new band) 60/60 ≥ 30 and 80/80 90–95 on the hardest track | **PASS on all 7 fights** (table above). econ-v1's coded 88–92 band would still flag Street at 94.9, Touge at 93.5 and F1/F4 at 94.7. |
| 10 Aero not a no-brainer | **PASS** (below) |
| Arc | PASS |

**Robustness** (`robustness_hardest.txt`, each rung moved ±0.003):
- Wangan: 0 of 12 moves fail.
- Street: 1 of 12 fail (mat1 +0.003 drops the wall to 1).
- Touge: 5 of 12 fail, all downward moves. They break the wall or 80/80 story mat2/oh1.
- R3 sits near its edges.

## Criterion 10: aero on the live tracks (`run_aero_live.py`, `aero_live.json`, `aero_live_summary.txt`)

**Method** (same as econ-v1, rerun on the live engine and tracks):
- **0 aero:** the district-fixed tune.
- **1 aero:** live rule, one aero with 10% of that part free, which moves 0.42% of the split (L1 mass 0.0042) toward the track's best split. The best splits come from `aero_best_splits_live.json` (60/60, r = 1.07, N = 150).
- **Full retune:** the track's best split. This is an illegal upper bound, shown for reference.
- All three are run at the proposed boss r, with paired seeds and N = 2000 per style.

**Mean change from adding 1 aero, across the 15 tracks** (pp, with range):

| Profile | 10-turn | 30-turn |
|---|---|---|
| 60/60 | −0.59 (−8.3 to +1.4) | −1.06 (−9.0 to +3.1) |
| 60/80 | −0.73 (−6.9 to +0.1) | −0.89 (−9.4 to +2.1) |
| 80/60 | −1.17 (−15.8 to +1.4) | −2.01 (−18.7 to +3.8) |
| 80/80 | −0.33 (−5.8 to +1.8) | −0.66 (−6.7 to +2.2) |

**Per track, 30-turn:**
- Biggest gain: W3 60/60 +3.1, 80/80 +2.2.
- Biggest loss: T3 60/60 −9.0, 80/80 −6.7.
- No effect: 6 tracks where the best split is the district tune (S1, S3, S4, S5, W1, W2). T1 is close to that: −2.3 / −0.1.

**Verdict: aero is not a no-brainer.** On average a single aero does not help. It wins only on a few tracks (W3, W5), loses elsewhere, and costs 1.75× the regular part. A full free retune is worth +3 to +3.5 pp on average for 60/60 and 60/80, and up to +22 on T5, but the one-aero rule doesn't allow that. No rule change is proposed.

**Caveat:** a 0.42% stat shift moving T3 by about 9 pp shows that live T3 has sharp stat thresholds. The T3 table has a similar step between r = 1.066 and 1.069 (18.2 → 28.4). The T3 boss numbers depend on the exact stats, so recheck them if the tunes or mod stats change.

## Open items for Austin
1. **Finale climb ends at L115**, not L114, because F1/F4 r\* is 1.075 as suggested. Keeping L114 would need F4 at r\* 1.070, where T3 is 29.8 / 92.7 (N = 3000). That misses the 60/60 floor by 0.2.
2. **Wangan boss at 1.055** is the lowest measured r with 80/80 at 90 or above on W3. At 1.048–1.050, 60/60 is 32.6–35.5 but 80/80 is 88.8–89.6.
3. **60/60 pre-F1 grind is 11.** There is no mixed-player failure.

## Files (round 2)
- **Sweeps:** `point_confirm_hardest.json`, `aero_best_splits_live.json`, `aero_live.json`, `aero_live_summary.txt`.
- **Fit and results:** `fit_ladder_hardest.json`, `hardest.json/.txt`, `robustness_hardest.txt`.
- **Constants:** `proposed_constants.json`.
- **Code:** `run_point_confirm2.py`, `run_aero_live.py`, and updates to `oracle.py`, `econ_patch.py`, `core.py` and `fit_ladder.py`.
- Round 1 files are unchanged.
