# Round-ladder v1 — Austin's picks (simulated)

Barry / 2026-11-13. Study only, under `unapproved/barry/round-ladder-v1/`. No `sim/` or `design/` edits. No commit.

Austin's choices (2026-11-13): primary 3-crew walk (round step 1.07, player cap 1.07); **R3 Touge +0.03 target-r offset** (boss r = 1.10 at cap; every R3 lieutenant budget cut so at-cap r = `LADDER_R[j] × 1.10/1.07`); **R1 Street boss stays on Shibuya S1** with a **boss-only +0.01 offset** (r = 1.08). Player ceilings still follow the un-offset 1.07 cap (C1 / C2 / C3 unchanged). Live constants were not changed.

Combat is live G2_slant_m10 on the touge-lines-v1 draft tracks, one fixed tune per district (Street 50/25/25, Wangan 25/30/45, Touge 40/30/30), gravity on. Every quoted win rate is a 9×1000 run (seeds 20261112–20261120) at that **exact** r — no interpolation. 60/60 is `q_read` 0.6 + average QTE profile + `PACE_Q` 0.6 at the trial r; 80/80 is 0.8/0.8/`PACE_Q` 0.8. Lengths: lieutenants 20, crew boss 30.

Budgets are also shown normalized so the player's **end-of-R1 ceiling C1 = 353.10 = 100**. C2 = 404.15 (114.46), C3 = 462.57 (131.00).

Story-level arrivals and grind counts use the **stale v8c XP curve** (`progression.py`, not refit). `STORY_XP_LT_ROUND_OPEN` was applied to R2/R3 as the only crew in the walk; that is not a recommendation. Combat r uses a live 1.07 fill.

## Offsets, in numbers

Ceilings stay on the primary walk: R1 cap L12, R2 L29, R3 L46. Only opponent budgets move.

- R1 boss: B = C1 / 1.08 = **326.94** (was 330.00). Lieutenants unchanged.
- R3 every rung: B = (player cap at that rung) / (`LADDER_R[j] × 1.10/1.07`), boss B = C3 / 1.10 = **420.52** (was 432.31).
- Opp / player at the R3 boss = 0.909, at the R1 boss = 0.926; both still inside the 0.8–1.2 parity band.
- Side effect: R1 old head #2's budget (330.48) now sits **slightly above** the R1 boss (326.94), because the boss was cut and the old head was not. They are different lengths (20 vs 30). Flag only; not a new offset.

## At-cap results, every rung

Win rates are district means except where a direction or S1 layout is listed. Limp is the 60/60 three-bar-lock clash share.

### Round 1 — Street (boss on S1 at r = 1.08)

| Rung | Cap L | Opp. B | B / C1×100 | Target r | 60/60 | Limp % | 80/80 | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| kid1 | 2 | 288.62 | 81.74 | 1.13000000 | 95.9 | 5.1 | 99.9 |  |
| kid2 | 4 | 298.52 | 84.54 | 1.11000000 | 90.5 | 7.3 | 99.8 |  |
| mat1 | 7 | 308.50 | 87.37 | 1.10000000 | 87.2 | 8.0 | 99.7 |  |
| mat2 | 10 | 321.79 | 91.13 | 1.08000000 | 76.3 | 10.8 | 99.0 |  |
| OH1 | 11 | 327.39 | 92.72 | 1.07000000 | 67.8 | 12.8 | 98.3 |  |
| OH2 | 11 | 330.48 | 93.59 | 1.06000000 | 58.6 | 15.3 | 96.9 |  |
| boss | 12 | 326.94 | 92.59 | 1.08000000 | 69.0 (dist.) | 14.3 | 99.1 | S1 CW **57.5** / CCW **60.2** (limp 21.0 / 20.2); 80/80 S1 98.2 / 98.5 |

The 69.0 district-mean boss rate mixes S1 with the easier S3 layouts (78.5–79.6 at r=1.08, 30-turn, from the same sweep). The **S1 figures are the ones that matter** for this pick: **57.5 CW / 60.2 CCW**, limp 21.0 / 20.2. Both clear 50%. 80/80 on S1 is 98.2 / 98.5.

### Round 2 — Wangan (no extra offset)

| Rung | Cap L | Opp. B | B / C1×100 | Target r | 60/60 | Limp % | 80/80 |
|---|---:|---:|---:|---:|---:|---:|---:|
| kid1 | 15 | 320.01 | 90.63 | 1.13000000 | 94.6 | 7.9 | 99.9 |
| kid2 | 18 | 333.63 | 94.49 | 1.11000000 | 89.8 | 9.6 | 99.7 |
| mat1 | 22 | 347.54 | 98.42 | 1.10000000 | 86.1 | 11.1 | 99.4 |
| mat2 | 26 | 365.40 | 103.48 | 1.08000000 | 76.9 | 13.2 | 98.3 |
| OH1 | 28 | 374.72 | 106.12 | 1.07000000 | 70.6 | 14.7 | 97.0 |
| OH2 | 28 | 378.25 | 107.12 | 1.06000000 | 62.0 | 17.7 | 94.4 |
| boss | 29 | 377.71 | 106.97 | 1.07000000 | 67.6 | 19.2 | 97.6 |

### Round 3 — Touge (+0.03 target-r offset)

| Rung | Cap L | Opp. B | B / C1×100 | Target r | 60/60 | Up / Down 60 | Limp % | 80/80 | Up / Down 80 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| kid1 | 32 | 356.29 | 100.90 | 1.16168224 | 94.3 | 94.4 / 94.2 | 7.2 | 99.9 | 99.9 / 99.9 |
| kid2 | 35 | 371.45 | 105.20 | 1.14112150 | 89.8 | 90.6 / 89.0 | 8.7 | 99.7 | 99.8 / 99.6 |
| mat1 | 39 | 386.93 | 109.58 | 1.13084112 | 87.0 | 86.7 / 87.2 | 9.2 | 99.6 | 99.6 / 99.5 |
| mat2 | 43 | 406.81 | 115.21 | 1.11028037 | 78.5 | 76.0 / 81.1 | 11.7 | 98.8 | 98.5 / 99.0 |
| OH1 | 45 | 417.19 | 118.15 | 1.10000000 | 71.7 | 69.9 / 73.6 | 13.7 | 97.8 | 97.8 / 97.9 |
| OH2 | 45 | 421.13 | 119.27 | 1.08971963 | 65.5 | 64.3 / 66.8 | 15.6 | 96.8 | 96.9 / 96.7 |
| boss | 46 | 420.52 | 119.09 | 1.10000000 | 63.8 | 60.3 / 67.4 | 20.0 | 97.3 | 96.6 / 98.1 |

Touge old head #2 is on the **actual grid** at r = 1.08971963 (1.06 × 1.10/1.07), not interpolated: **65.5** at 20 turns, 60/60 (uphill 64.3, downhill 66.8), limp 15.6. That cell was 46.0 at the un-offset r=1.06. It is no longer a wall.

The R3 crew boss at r=1.10 is **63.8** at 30 turns, 60/60 (uphill **60.3**, downhill 67.4), limp 20.0. 80/80 is 97.3 (96.6 / 98.1). The softest at-cap 60/60 cells left in the season are **R3 boss uphill 60.3** and **R1 S1 boss 57.5–60.2**. Both are above 50%, with limp still high on those tracks (19.3 uphill, 21.0 / 20.2 on S1).

## Walls-policy arrival at the bosses (stale XP, flagged)

Grind to cap only at mature #2 and the crew boss, then arrive at the boss with story XP only after that. Counts and arrival levels are from the stale v8c curve.

| Round | Arrive L / cap L | Arrive r | Grind still needed | 60/60 | Limp % | 80/80 | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| R1 Street | 10 / 12 | 1.06297971 | 6 | 48.5 | 19.3 | 97.3 | S1 CW 40.1 / CCW 39.8 (limp 25.1 / 26.0); 80/80 S1 95.9 / 96.3 |
| R2 Wangan | 27 / 29 | 1.05313730 | 8 | 53.0 | 23.6 | 93.9 | District mean. Comfortable enough after the mature #2 grind, then 8 more to cap. |
| R3 Touge | 44 / 46 | 1.08266452 | 8 | 50.9 | 24.1 | 95.1 | Uphill 47.7 / downhill 54.0; 80/80 up 95.0 / down 95.3. Uphill is still just under 50% on arrival. |

Even with the R1 boss offset, a walls-policy 60/60 player who has already ground at mature #2 still arrives at the **S1 boss at 39.8–40.1%** and needs the remaining 6 grind races to reach r=1.08 (57.5–60.2). R3 walls arrival is 50.9 district-mean but **47.7 uphill**. R2 arrives at 53.0.

## No-grind walks

Three separate cases, both picks applied. Story XP only inside the round; no grind races. Stale v8c XP, flagged.

- **(a) Round 1, starting fresh.** Prologue scripted XP is applied as in the official walk (scripted race 3 pays into the first kid cap), then story XP only through the Street ladder.
- **(b) Round 2 entered at max C1.** Player power starts at C1 (L12, 100 on the normalized scale). XP past the R1 cap is treated as already lost, so the R1 boss payout does not spill into R2 levels. Then story XP only through Wangan.
- **(c) Round 3 entered at max C2.** Same rule: start at C2 (L29, 114.46), story XP only through Touge.

"Stuck" means the first rung where 60/60 (district mean, or S1 mean for the R1 boss) drops below 50%. 80/80 is reported the same way.

### (a) Round 1 — Street, story XP only

| Rung | Arrive L / cap | Player / C1×100 | Opp. / C1×100 | r on arrival | 60/60 | Limp % | 80/80 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| kid1 | 2 / 2 | 92.36 | 81.74 | 1.13000000 | 95.9 | 5.1 | 99.9 |
| kid2 | 2 / 4 | 92.36 | 84.54 | 1.09250692 | 83.0 | 9.4 | 99.5 |
| mat1 | 3 / 7 | 93.10 | 87.37 | 1.06560224 | 63.1 | 14.1 | 97.8 |
| mat2 | 3 / 10 | 93.10 | 91.13 | 1.02159327 | 10.5 | 24.2 | 85.7 |
| OH1 | 3 / 11 | 93.10 | 92.72 | 1.00412702 | 1.5 | 28.9 | 76.7 |
| OH2 | 4 / 11 | 93.84 | 93.59 | 1.00267487 | 1.2 | 29.2 | 75.9 |
| boss | 4 / 12 | 93.84 | 92.59 | 1.01351139 | 1.1 (dist.) | 33.2 | 74.0 | S1 CW 0.9 / CCW 1.0; 80/80 S1 66.8 / 68.9 |

### (b) Round 2 — enter at C1, story XP only

| Rung | Arrive L / cap | Player / C1×100 | Opp. / C1×100 | r on arrival | 60/60 | Limp % | 80/80 |
|---|---|---:|---:|---:|---:|---:|---:|
| kid1 | 12 / 15 | 100.00 | 90.63 | 1.10339312 | 87.3 | 10.8 | 99.5 |
| kid2 | 13 / 18 | 100.80 | 94.49 | 1.06678285 | 67.2 | 16.0 | 96.2 |
| mat1 | 15 / 22 | 102.41 | 98.42 | 1.04051166 | 43.2 | 20.5 | 90.8 |
| mat2 | 16 / 26 | 103.23 | 103.48 | 0.99753892 | 2.8 | 29.1 | 77.1 |
| OH1 | 17 / 28 | 104.05 | 106.12 | 0.98048394 | 0.4 | 32.4 | 67.1 |
| OH2 | 18 / 28 | 104.88 | 107.12 | 0.97906598 | 0.3 | 32.5 | 66.5 |
| boss | 18 / 29 | 104.88 | 106.97 | 0.98048394 | 0.1 | 42.4 | 59.2 |

### (c) Round 3 — enter at C2, story XP only

| Rung | Arrive L / cap | Player / C1×100 | Opp. / C1×100 | r on arrival | 60/60 | Up / Down 60 | Limp % | 80/80 | Up / Down 80 |
|---|---|---:|---:|---:|---:|---|---:|---:|---|
| kid1 | 29 / 32 | 114.46 | 100.90 | 1.13432938 | 87.5 | 88.2 / 86.9 | 9.5 | 99.6 | 99.7 / 99.5 |
| kid2 | 30 / 35 | 115.37 | 105.20 | 1.09669265 | 69.8 | 67.6 / 72.0 | 14.4 | 97.5 | 97.4 / 97.7 |
| mat1 | 32 / 39 | 117.22 | 109.58 | 1.06968489 | 53.2 | 50.4 / 55.9 | 18.7 | 94.1 | 93.4 / 94.7 |
| mat2 | 33 / 43 | 118.15 | 115.21 | 1.02550731 | 11.9 | 9.3 / 14.5 | 30.1 | 77.3 | 74.6 / 79.9 |
| OH1 | 34 / 45 | 119.09 | 118.15 | 1.00797414 | 3.0 | 1.8 / 4.2 | 33.9 | 67.8 | 64.1 / 71.5 |
| OH2 | 35 / 45 | 120.04 | 119.27 | 1.00651643 | 2.6 | 1.5 / 3.7 | 34.6 | 66.2 | 63.2 / 69.2 |
| boss | 35 / 46 | 120.04 | 119.09 | 1.00797414 | 1.1 | 0.4 / 1.8 | 45.6 | 52.7 | 47.8 / 57.5 |

### Where they get stuck, and grind to get past 50%

**60/60** gets stuck in every no-grind chapter. The first rung below 50%, and the grind races at *that* rung (stale XP payouts) needed to push 60/60 back to ≥50%, measured at each exact mid-grind r:

| Case | First stuck rung | Arrival r | 60/60 on arrival | Grind races to ≥50% | Then at | 60/60 after those races |
|---|---|---:|---:|---:|---|---:|
| (a) R1 Street | mature #2 | 1.02159327 | 10.5 | **4** | r=1.05457042, L7 | 54.0 |
| (b) R2 Wangan | mature #1 | 1.04051166 | 43.2 | **1** | r=1.04880885, L16 | 53.9 |
| (c) R3 Touge | mature #2 | 1.02550731 | 11.9 (up 9.3 / down 14.5) | **5** | r=1.06705231, L38 | 50.9 (up 47.7 / down 54.2) |

On (c), 5 races clear the 50% district mean but uphill is still 47.7. A sixth race (r=1.07556114, L39) takes district-mean 60/60 to 57.1 and uphill to 54.5. Use **6** if the bar includes the uphill cell.

The earlier rungs in each case stay above 50%: R1 mat1 is 63.1, R2 kid2 is 67.2, R3 mat1 is 53.2 (uphill 50.4). After the stuck rung, later no-grind arrivals collapse (R1 boss 1.1 district / 0.9–1.0 on S1; R2 boss 0.1; R3 boss 1.1, uphill 0.4). So one mid-ladder grind burst is what a 60/60 no-grind run actually needs, not a grind at the first kid.

**80/80 does not get stuck** on the district mean in any of the three cases. The lowest district-mean 80/80 cells are R1 S1 boss 66.8 / 68.9, R2 boss 59.2, and R3 boss 52.7. No grind is required to stay above 50% on those means. The only 80/80 cell under 50% is **R3 boss uphill at 47.8%** on a no-grind arrival (downhill 57.5). That is a last-rung direction dip, not a mid-ladder wall; I did not run a separate grind-path sweep just for that one cell.

## Remaining walls and dips at cap

- No at-cap 60/60 district-mean cell is under 50% with both picks applied. Touge OH #2 (65.5) and the Touge boss (63.8, uphill 60.3) are the late-season soft spots, not walls.
- R1 S1 boss 57.5–60.2 is the other soft at-cap cell. It is the intended first boss and is just clear of 50%.
- R1 OH2 58.6 at r=1.06 is the softest Street lieutenant; it was not offset.
- Limp stays elevated on the soft tracks: S1 boss 20–21%, Touge boss 20.0 (uphill 19.3), Wangan boss 19.2.
- Skip-grind / no-grind is still a cliff under G2 for 60/60. The picks do not change that; they only move the at-cap targets.
- Walls-policy (stale XP): arriving at the R1 S1 boss is still a 40% fight; arriving at the R3 boss is 50.9 mean / 47.7 uphill.

## Recommendation

The two picks do what Austin asked. At cap, R3 is no longer a 41% / 46% wall, and the S1 first boss sits at 57.5–60.2 rather than 48.5–50.5. Install them in the structural draft (`proposed_constants.json`). XP/economy remains deferred; the no-grind and walls-policy arrivals above should not be used as shipping grind targets.

## Files

- `RESULTS_picks.md` (this writeup)
- `proposed_constants.json` (updated with the picks and exact budgets)
- `picks_walks.json`, `picks_analysis.json`
- `results_picks.npz` + `results_picks_grind.npz` (exact-r 9×1000 runs) and the earlier `results_r_sweep.npz` (reused where r already sat on that grid)

