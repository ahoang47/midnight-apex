### (a) Retune gap at the cap (r 1.05), average play, base model

Mean over 5 tracks x 3 opponent styles per row (15 cells, 9,000 runs each). Gaps in percentage points; 'clear' = at least 5 pp with the same sign in all 9 batches.

| District | Turns | Even-spread win % | Best-tune win % | Best vs even (mean / max) | Clear vs even | Best vs best-on-other-tracks (mean / max) | Clear | Best vs best-on-other-districts (mean / max) | Clear | Most common best tune |
|---|---|---|---|---|---|---|---|---|---|---|
| Touge | 10 | 80.2 | 85.1 | 4.9 / 10.0 | 5/15 | 1.0 / 4.5 | 0/15 | 5.0 / 13.4 | 5/15 | P40/H35/E25 (9), P45/H30/E25 (4) |
| Touge | 20 | 87.9 | 92.8 | 5.0 / 10.4 | 5/15 | 1.8 / 7.0 | 2/15 | 10.5 / 18.0 | 14/15 | P40/H35/E25 (10), P45/H30/E25 (5) |
| Touge | 30 | 91.4 | 96.1 | 4.7 / 10.2 | 5/15 | 3.7 / 8.6 | 3/15 | 10.5 / 20.5 | 12/15 | P40/H35/E25 (10), P45/H30/E25 (5) |
| Wangan | 10 | 77.4 | 81.0 | 3.7 / 5.6 | 1/15 | 7.8 / 12.2 | 11/15 | 8.9 / 12.2 | 14/15 | P30/H25/E45 (9), P35/H25/E40 (4) |
| Wangan | 20 | 82.8 | 89.3 | 6.6 / 9.6 | 12/15 | 11.3 / 17.5 | 15/15 | 13.2 / 17.5 | 15/15 | P30/H25/E45 (12), P35/H25/E40 (2) |
| Wangan | 30 | 85.7 | 93.3 | 7.7 / 11.8 | 12/15 | 9.5 / 14.4 | 12/15 | 15.8 / 19.5 | 15/15 | P30/H25/E45 (12), P25/H30/E45 (2) |
| Street | 10 | 63.5 | 67.8 | 4.4 / 6.5 | 3/15 | 0.8 / 2.3 | 0/15 | 4.2 / 7.1 | 4/15 | P40/H35/E25 (12), P45/H30/E25 (1) |
| Street | 20 | 68.2 | 73.1 | 4.9 / 7.9 | 6/15 | 2.1 / 4.7 | 0/15 | 5.0 / 9.2 | 6/15 | P40/H35/E25 (10), P45/H30/E25 (4) |
| Street | 30 | 69.9 | 76.1 | 6.2 / 10.4 | 10/15 | 2.2 / 3.7 | 0/15 | 7.4 / 17.1 | 12/15 | P40/H35/E25 (6), P50/H25/E25 (5) |
| **All** | | | | 5.3 / 11.8 | 59/135 | 4.5 / 17.5 | 43/135 | 8.9 / 20.5 | 97/135 | |

By opponent style (all 15 tracks x 3 lengths = 45 cells each):

| Style | Best vs even (mean) | Clear | Best vs best-on-other-districts (mean) | Clear | Most common best tunes |
|---|---|---|---|---|---|
| balanced | 6.9 | 32/45 | 9.7 | 28/45 | P45/H30/E25 (19), P30/H25/E45 (12), P40/H35/E25 (6) |
| hot_early | 4.5 | 14/45 | 7.1 | 34/45 | P40/H35/E25 (28), P30/H25/E45 (9), P35/H25/E40 (6) |
| conserver | 4.6 | 13/45 | 10.1 | 35/45 | P40/H35/E25 (23), P30/H25/E45 (12), P45/H25/E30 (3) |

Retuning for the opponent style or race length, same track (cost of keeping the wrong tune):

| Switch | Mean gap (pp) | Max gap (pp) | Clear cells |
|---|---|---|---|
| Tune best vs balanced boss, used vs hot_early | 1.3 | 8.9 | 2/45 |
| Tune best vs balanced boss, used vs conserver | 0.9 | 4.0 | 0/45 |
| Tune best at 10 turns, used at 30 turns | 0.5 | 4.5 | 0/45 |

### (b) Does one tune win everywhere?

- Best single tune across all 135 cells: **P40/H30/E30**, mean win 79.8% (even spread 78.5%).
- Against each cell's own best tune it gives up 4.1 pp on average (max 11.8); it is within 2 pp of the best in 30/135 cells and clearly worse (5+ pp, all 9 batches) in 34/135.
- 9 different tunes are best somewhere: P40/H35/E25 (57), P30/H25/E45 (33), P45/H30/E25 (21), P35/H25/E40 (7), P50/H25/E25 (6), P25/H30/E45 (4), P35/H40/E25 (3), P45/H25/E30 (3), P30/H30/E40 (1).
- Best tune per district (mean win; the global tune's win in that district): Touge P40/H35/E25 90.9% (89.1%); Wangan P30/H25/E45 87.8% (80.7%); Street P40/H35/E25 71.9% (69.6%).

### (c) Combat targets (win %)

New model: all 15 tracks x 3 lengths x 3 opponent styles (135 cells x 9,000 runs). Live model: 15 tracks x 3 lengths (no styles), same seeds. Perfect = reads every Entry (q_read 1.0) and perfect timing (raw QTE 1.0). Average = q_read 0.6 and the 'average' QTE profile at the visible zone for that r.

| Play | r | Target | Live model, even spread (min-max by district x length) | New model, even spread (min-max) | New model, best tune per cell |
|---|---|---|---|---|---|
| perfect | 0.80 | 10-25 | 98.4 (95.1-100.0) | 98.7 (93.3-100.0) | 99.5 |
| perfect | 1.00 | wins (>= 85 per design/02 §0.4) | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) | 100.0 |
| perfect | 1.05 | - | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) | 100.0 |
| perfect | 1.10 | - | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) | 100.0 |
| average | 0.80 | - | 0.0 (0.0-0.0) | 0.0 (0.0-0.1) | 0.1 |
| average | 1.00 | - | 7.6 (2.4-14.8) | 19.8 (4.7-33.7) | 28.1 |
| average | 1.05 | 60-75 (cap 105%) | 64.2 (62.9-65.6) | 78.5 (63.5-91.4) | 83.9 |
| average | 1.10 | 60-75 if cap moves to 110% | 77.4 (73.8-80.2) | 88.7 (76.3-97.0) | 91.7 |

Variants (track #1 of each district x 3 lengths x 3 styles = 27 cells, even spread / best tune per cell):

| Variant | Perfect r 0.8 | Perfect r 1.0 | Average r 1.05 | Average r 1.10 | Best vs even at avg r 1.05 (mean pp) | Clear vs even |
|---|---|---|---|---|---|---|
| base | 98.5 / 99.5 | 100.0 / 100.0 | 78.3 / 83.9 | 88.7 / 91.8 | 5.6 | 14/27 |
| hard_block | 51.8 / 71.3 | 99.6 / 100.0 | 69.1 / 84.3 | 84.0 / 93.9 | 15.2 | 26/27 |
| downgrade | 95.6 / 98.0 | 100.0 / 100.0 | 72.1 / 77.0 | 85.9 / 88.8 | 4.9 | 8/27 |
| kappa_x3 | 31.2 / 46.3 | 100.0 / 100.0 | 92.6 / 95.0 | 99.4 / 99.6 | 2.3 | 3/27 |

### (d) How much the stat mix matters: live model vs new model

Average play at r 1.05, 21 tunes at a fixed total. Spread = best tune minus worst tune; per cell, then averaged. New model uses the balanced boss (the live model has no styles), plus all styles for reference.

| Model | Cells | Spread best-worst (mean / max pp) | Best vs even (mean / max pp) | Cells where best beats even clearly |
|---|---|---|---|---|
| Live (card draw, MU/ETA) | 45 | 25.8 / 44.4 | 8.2 / 14.5 | 35/45 |
| New, balanced boss | 45 | 31.6 / 52.8 | 6.9 / 10.4 | 32/45 |
| New, all styles | 135 | 30.7 / 52.8 | 5.3 / 11.8 | 59/135 |

Live model best tunes: P50/H25/E25 (21), P30/H25/E45 (9), P45/H30/E25 (8), P25/H25/E50 (5), P35/H25/E40 (1), P40/H35/E25 (1).

### Live vs new: retune gap and dominance on the same 45 cells (average play, r 1.05; new = balanced boss)

| Model | Best vs best-on-other-districts (mean / max pp) | Clear | Best single tune | Its mean loss vs each cell's best (pp) | Cells clearly worse |
|---|---|---|---|---|---|
| Live | 5.7 / 16.0 | 28/45 | P50/H25/E25 | 3.7 | 15/45 |
| New (base) | 9.7 / 20.5 | 28/45 | P45/H30/E25 | 4.5 | 14/45 |

### Scouting value (knowing the boss's style vs assuming the default 65/21/14), average play r 1.05, track #1 per district

| Style | Win gain from knowing the style, even spread (pp) | Same, with the best tune (pp) |
|---|---|---|
| hot_early | 44.8 | 34.2 |
| conserver | 32.2 | 28.7 |

### Track demand (per turn, perfect counter-player vs 65/21/14 boss, incl. passive wear) and even-spread tanks

| Track | Fuel | Suspension | Brakes |
|---|---|---|---|
| T1_Akina_Switchbacks | 1.40 | 1.51 | 0.86 |
| T2_Irohazaka_Ladder | 1.63 | 1.45 | 0.68 |
| T3_Usui_Esses | 1.59 | 1.42 | 0.69 |
| T4_Myogi_Descent | 1.70 | 1.41 | 0.71 |
| T5_Hakone_Ridge | 1.78 | 1.30 | 0.71 |
| W1_Bayshore_Run | 0.93 | 0.71 | 1.45 |
| W2_Daikoku_Loop | 0.87 | 0.81 | 1.42 |
| W3_C1_Outer | 0.95 | 0.62 | 1.49 |
| W4_Tatsumi_Sprint | 1.04 | 0.65 | 1.44 |
| W5_Aqualine_Flyer | 0.93 | 0.71 | 1.45 |
| S1_Shibuya_Grid | 1.72 | 1.05 | 1.22 |
| S2_Ginza_Blocks | 1.64 | 1.23 | 1.18 |
| S3_Shinjuku_Underpass | 1.52 | 1.19 | 1.29 |
| S4_Roppongi_Hill | 1.41 | 1.29 | 1.21 |
| S5_Harbor_Warehouses | 1.45 | 1.39 | 1.26 |
| **Cross-track average** | 1.37 | 1.12 | 1.14 |

Even-spread tanks at r 1.0 for a 10-turn race: fuel 6.85, suspension 3.35 (recovers 0.67/turn), brakes 5.69 (fuel and brakes scale with race length; suspension does not).
