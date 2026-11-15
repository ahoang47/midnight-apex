# econ-v1 recalibrated to the live stand-in tracks (DRAFT, Barry, 2026-11-13)

**Status: DRAFT. Not approved.** Nothing in `sim/` is edited, and nothing is committed or pushed. Austin approves the numbers first. Two picks below are still open.

Basis: Austin (Nov 13 2026) said "Keep the current stand-in tracks and recalibrate econ-v1 to them." The 15 tracks in `sim/config/tracks_v1.json` are used with the live engine (G2 heat), the live QTE mapping, and the four profiles (60/60, 60/80, 80/60, 80/80). Each win rate (WR) is the mean over the 3 boss styles, with ties counted as half.

## Method (all sim, no invented figures)
- **Tunes** (`run_tune_screen.py`, `tune_screen.json`): POW/HAN/EN is Street 0.50/0.25/0.25, Wangan 0.25/0.25/0.50 and Touge 0.45/0.25/0.30. These are the best 60/60 splits at r = 1.07.
- **Oracle**
  - `sweep_main.json`: N = 300 per track per style, r 0.94–1.24 in steps of 0.01, at 10, 20 and 30 turns.
  - `sweep_confirm30.json`: N = 1500, 30 turns, r 1.034–1.072.
  - Values between sweep points are linearly interpolated in r.
  - Exact-r checks: `point_confirm*.json`, N = 1500–3000 per style.
- **Machinery**
  - The econ-v1 draft walks and criteria (`../econ-v1/evaluate.py`, `run_betting_levers.py`, `run_finale_arc.py`) are unmodified and run on the live oracle via `oracle.py` and `econ_patch.py`.
  - Drivers: `run_drift.py`, `fit_ladder.py`, `fit_arc.py` and `run_final.py`.
- **Hard cells on live tracks.** The live tracks have no CW/CCW and no uphill/downhill variants.
  - **Street:** `S1_Shibuya_Grid`. The R1 boss stays on S1 (Austin's pick).
  - **Touge:** `T3_Usui_Esses`, the worst live Touge track. It stands in for the draft "uphill" rule. **This is open pick B.**
  - **Wangan:** district mean.
- **Limitations**
  - Criterion 10 (aero) was **not** re-run on the live tracks.
  - Limp shares are not in the live sweep.
  - Arrivals below r = 0.94 are clamped to the 0.94 value. Only early story-only rungs come near that.

## 1. Drift: current live constants on the live tracks

At-cap boss WR, shown as 60/60 / 60/80 / 80/60 / 80/80. RESULTS targets are econ-v1's figures on the draft tracks.

| Boss (live r) | Cell | 60/60 | 60/80 | 80/60 | 80/80 | econ-v1 target (60/60 … 80/80) | Source |
|---|---|---:|---:|---:|---:|---|---|
| R1 Street (1.053) | S1 | 46.7 | 81.3 | 82.0 | **96.3** | 38.8 / 76.5 / 73.8 / 96.3 (dist.); S1 ~31 / 94–95 | main N300 |
| | district | 58.5 | 87.0 | 87.8 | 97.7 | | |
| | worst (S2 Ginza) | 35.7 | 71.7 | 73.1 | 93.4 | | |
| R2 Wangan (1.040) | district | 33.6 | 63.8 | 73.2 | 90.7 | 36.4 / 68.5 / 73.4 / 91.4 | confirm N1500 |
| | worst (W3 C1) | 22.8 | 48.7 | 68.5 | 86.5 | | |
| R3 Touge (1.066) | T3 Usui (hard) | **18.2** | 57.8 | 50.4 | 86.6 | 37.4 / 65.8 / 69.4 / 90.8; uphill 60/60 ≥30, 80/80 89.6 | confirm N1500 |
| | district | 35.3 | 69.8 | 69.3 | 92.4 | | |
| | T1 Akina | 56.5 | 86.4 | 84.8 | 96.9 | | |

The finale uses the same cells: F1/F4 Touge at 1.066, F2 Wangan at 1.040, F3 Street at 1.053.

Campaign walk (`drift_T3.json`; `drift_T1.json` is the same run with T1 as the Touge hard cell):

| | R1 | R2 | R3 |
|---|---|---|---|
| Mixed: wall rung, wall + post-wall grind | mat1 **1** + 11 = 12 | mat1 3 + 9 = 12 | kid1 **2** + 10 = 12 |
| 60/60 hard grind total | 12 | 15 | 22 (T1 hard: 18) |
| 80/80 story-only end level / cash | L8, $7,000 ($3,000 debt) | L26, $27,000 | L43, $54,000 |
| Mixed end cash | $10,600 | $41,190 | $77,100 |

Criteria under the live constants: 1 ✓, **2 ✗** (R1 wall 1, R3 wall 2), **3 ✗** (R3 mat2 80/80 hard 34.6, oh1 45.3), **4 ✗** (R3 10-turn grind 61.0 / 61.1, 60/60 30.2), 5 ✓, 6 ✓, 7 ✓, 8 ✓, **9 ✗** (Street 80/80 S1 96.3; Touge 60/60 T3 18–25). With the T1 hard cell, criterion 3 fails only on R3 mat2 (district 47.9).

Finale arc under the live constants:
- 60/60 billed hard WR: F1 24.6, F2 28.5 and F4 24.6, all under 30.
- 80/60 pre-F1 wall is 8 (over 6).
- F2 caps at L76, and combat there only reaches r = 1.0366 because the cap level rounds down.

## 2. Proposed constants (draft default; see `proposed_constants.json`)

| Ladder r (kid1 kid2 mat1 mat2 oh1 oh2 boss) | Live | Proposed |
|---|---|---|
| Street | 1.20 1.16 1.10 1.07 1.065 1.058 **1.053** | 1.20 1.159 1.095 1.071 1.065 1.058 **1.044** |
| Wangan | 1.18 1.16 1.11 1.08 1.06 1.048 1.040 | unchanged |
| Touge | 1.18 1.16 1.12 1.085 1.075 1.070 **1.066** | 1.182 1.163 1.132 1.097 1.079 1.071 **1.071** |

- **Boss budgets** (C / r): Street 335.33 → **338.22**, Wangan 388.72 (unchanged), Touge 434.19 → **432.16**.
- **Finale r\***: (1.066, 1.040, 1.053, 1.066) → **(1.070, 1.041, 1.044, 1.070)**.
  - Finale B is unchanged (fixed-budget logic), so C = B × r\* = 529.44 / 589.52 / 676.72 / 793.83.
  - Caps move from **L63 / 76 / 95 / 114 to L63 / 77 / 94 / 114**. The climb still ends at L114.
  - F2 is set to 1.041, not 1.040, so the cap rounds up to L77 and players really fight at r = 1.041. At 1.040 the cap is L76, combat is r = 1.0366, and 60/60 drops to 28.5.
  - F1 and F4 are set to 1.070 because the integer caps L63 and L114 only deliver r = 1.070. Any r\* from 1.070 to about 1.074 plays the same.
- **Finale arc**
  - The wall r_design values (P3/M32 1.020, M12/M22 1.000, relative to the 80/80 story reference) came back unchanged from the fit.
  - These B values are recomputed with econ-v1's `set_budgets_from_8080`: **P3 483.25 → 479.43, M21 485.77 → 489.64, M22 625.54 → 620.59, M31 564.89 → 560.43, M32 713.17 → 707.53**.
  - P1, P2, P4, M11 and M12 are unchanged.
- **Unchanged:** money, purses, debt, betting, T4 ($8,000 stand-in, P1 unlock, L47), mod tiers and floors, aero, campaign caps L12/29/46, XP, the arc shape and fill, and GRIND_R 1.12.

## 3. Results with the proposed set (`proposed.json`, `proposed.txt`)

### At-cap bosses and finale (measured at exact r, high N)

| Fight (r) | Cell | 60/60 | 60/80 | 80/60 | 80/80 | N per style |
|---|---|---:|---:|---:|---:|---|
| R1 Street / F3 (1.044) | S1 | **31.6** | 72.4 | 71.0 | **94.9** | 3000 |
| | district* | 42.9 | 80.4 | 79.7 | 96.4 | 1500 (interpolated 1.043–1.046) |
| R2 Wangan (1.040) | district | 33.6 | 63.8 | 73.2 | **90.7** | 1500 |
| F2 Wangan (1.041) | district | 34.9 | 65.3 | 74.5 | **91.5** | 1500 |
| R3 Touge (1.071) | T3 | **31.9** | 69.2 | 70.2 | **93.5** | 3000 |
| | district* | 41.6 | 74.8 | 76.6 | 94.6 | 1500 (interpolated 1.069–1.072) |
| F1 / F4 Touge (1.070 at cap) | T3 | **29.8** | 67.1 | 70.1 | **92.7** | 3000 |
| | district | 40.0 | 74.2 | 75.4 | 94.5 | 1500 |

### Campaign grind (unchanged from econ-v1)

| | R1 | R2 | R3 |
|---|---|---|---|
| Mixed: wall rung, wall + to cap | mat1 3 + 9 = 12 | mat1 3 + 9 = 12 | mat1 4 + 8 = 12 |
| 60/60 hard total | 12 | 15 | 18 |
| Mixed / 80/80 end cash | $10,600 / $7,000 (80/80 has $3,000 debt) | $41,190 / $27,000 | $77,100 / $54,000 |

- Lowest 80/80 story-only WR (district / hard):
  - R1 boss 70.4 / 61.6.
  - R2 boss 51.2.
  - R3 oh1 59.8 / 50.4, and mat2 60.1 / 51.1.
- Mixed 10-turn grind WR at the wall:
  - R1: 98.2 / 99.2, and 60/60 92.1.
  - R2: 90.1 / 94.4, and 76.8.
  - R3: 88.3 / 93.1, and 71.4.

### Finale arc (walk on the merged oracle)

Grind per step, shown as wall / to-cap for pre-F1, F1→F2, F2→F3, F3→F4:

| Profile | Grind per step | End |
|---|---|---|
| 60/80 | 5/1, 3/3, 0/7, 3/4 (6, 6, 7, 7) | L114, $77,790, 5 T4 + aero |
| 80/60 | 6/0, 3/3, 2/5, 5/2 (6, 6, 7, 7) | L114, $77,790 |
| 60/60 | 10, 7, 7, 8 | L114, $90,247.50 |
| 80/80 story-only | 0 | L111, $31,075, 5 T4 + aero by F2 |

- 80/80 story-only lowest hard WR is 59.3 (M12). Billed fights are 74.8 / 74.5 / 79.3 / 74.8.
- 60/60 billed hard WR in the walk is 31.1 / 35.2 / 31.6 / 31.1.
  - The walk's F1/F4 figure is 31.1 because it uses the N = 300 grid point at r = 1.07.
  - The N = 3000 exact check at r = 1.070 gives **29.8**.
- The arc evaluator reports no issues.

### Criteria
| # | Result |
|---|---|
| 1 | PASS |
| 2 | PASS (12 / 12 / 12; walls 3 / 3 / 4) |
| 3 | PASS (thin margins: R2 boss 51.2; R3 oh1 hard 50.4) |
| 4 | PASS |
| 5 | PASS |
| 6 | PASS |
| 7 | PASS |
| 8 | PASS |
| 9 | **FAIL, as a trade-off.** Wangan passes. Street S1 80/80 is 94.9 (over 92). Touge T3 80/80 is 93.5 (over 92). F1/F4 T3 60/60 is 29.8. |
| 10 | not re-run |
| Arc | PASS |

**Robustness** (`robustness.txt`, each rung moved ±0.003):
- Wangan: 0 of 12 moves fail.
- Street: 1 of 12 fail (mat1 +0.003 drops the wall to 1).
- Touge: 5 of 12 fail, all on the downward moves.
- The R3 fit sits close to the edges.

## 4. Trade-offs that need Austin's pick

### A. Street S1 (R1 boss, also F3)

On S1 no r gets 80/80 to 92 or below *and* 60/60 to 30 or above, the same as on the draft tracks. Measured on S1:

| r | 60/60 S1 | 80/80 S1 | N per style | Notes |
|---|---:|---:|---|---|
| 1.037 | 19.6 | **91.9** | 1500 | 80/80 in band. Full fit is in `alt_s1band.*`. The arc flags F3 60/60 at 20.4 in the walk. |
| 1.040 | 26.0 | 93.5 | 1500 (grid) | Compromise |
| 1.043 | 29.9 | 94.5 | 3000 | Floor just missed |
| **1.044 (default)** | **31.6** | **94.9** | 3000 | Floor met, 80/80 2.9 over the band. Same rule econ-v1 used. |
| 1.045 | 33.6 | 95.5 | 3000 | |

### B. Touge hard cell, because the live tracks have no "uphill"

- **B1 (default): T3 Usui, the worst live track.**
  - Boss at r = 1.071: 60/60 31.9, 80/80 93.5.
  - Finale at r = 1.070: 29.8 / 92.7.
  - Measured on T3: 1.066 gives 18.2 / 86.6, 1.069 gives 28.4 / 91.7, and 1.070 gives 29.8 / 92.7, so no r meets both.
- **B2: Touge district mean** (`alt_tougemean.*`, `fit_ladder_alt_tougemean.json`).
  - Boss and F1/F4 at r = 1.062, with a ladder of 1.182 1.163 1.121 1.087 1.075 1.070 1.062.
  - 60/60 31.5–31.8 and 80/80 90.6–90.7, both in band.
  - Criteria 1–8 and the arc pass.
  - The cost: on T3 the boss is 60/60 15.8 and 80/80 84.8, so the boss would have to avoid T3.
  - The climb ends at **L113**, because F1 caps at L62 and F4 at L113.
- **B3: T1 Akina as the hard cell** (the old draft mapping). T1 is the easiest live Touge track: 60/60 56.5 at r = 1.066. I don't recommend it.

### C. F1/F4 at 60/60 29.8 versus 30

Because the cap is an integer level, F1 (L63) and F4 (L114) deliver r = 1.070 at most. Two ways to get there:
- Accept 29.8 (N = 3000).
- Raise F1/F4 r\* to about 1.075 so the caps move to L64 and L115. This was not simulated.

## Files
- **Sweeps:** `sweep_main.json`, `sweep_confirm30.json`, `confirm30_table.json`, `point_confirm*.json`, `tune_screen.json`.
- **Drift:** `drift_T3.json/.txt`, `drift_T1.json/.txt`.
- **Fits:** `fit_ladder_v3.json` (default), plus `fit_ladder*.json` for the alternatives.
- **Results:** `proposed.json/.txt`, `alt_tougemean.*`, `alt_s1band.*`, `robustness.txt`.
- **Code:** `livesim.py`, `run_sweep.py`, `run_point_confirm.py`, `oracle.py`, `econ_patch.py`, `core.py`, `run_drift.py`, `fit_ladder.py`, `fit_arc.py`, `run_final.py`.
- **Constants:** `proposed_constants.json`.
