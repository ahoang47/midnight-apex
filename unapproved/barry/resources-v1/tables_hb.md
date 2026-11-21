### Hard-block B (hard block, KAPPA_SCALE 1.25, TANK_FACTOR 0.4): retune gap at r 1.05, average play

| District | Turns | Even win % | Best-tune win % | Best vs even (mean pp, clear) | Best vs best-on-other-tracks (mean pp, clear) | Best vs best-on-other-districts (mean pp, clear) | Most common best tune |
|---|---|---|---|---|---|---|---|
| Touge | 10 | 75.7 | 92.8 | 17.0 (15/15) | 7.6 (12/15) | 14.3 (14/15) | P25/H50/E25 (6), P30/H45/E25 (5) |
| Touge | 20 | 74.6 | 93.0 | 18.4 (15/15) | 8.8 (12/15) | 13.7 (15/15) | P45/H30/E25 (9), P25/H50/E25 (5) |
| Touge | 30 | 77.9 | 94.0 | 16.1 (14/15) | 11.8 (9/15) | 13.9 (12/15) | P45/H30/E25 (6), P30/H45/E25 (4) |
| Wangan | 10 | 72.8 | 87.0 | 14.1 (15/15) | 21.5 (13/15) | 41.6 (15/15) | P25/H30/E45 (9), P25/H35/E40 (3) |
| Wangan | 20 | 66.0 | 73.2 | 7.3 (11/15) | 24.5 (15/15) | 39.8 (15/15) | P25/H30/E45 (6), P25/H35/E40 (5) |
| Wangan | 30 | 71.5 | 83.9 | 12.3 (14/15) | 22.9 (13/15) | 59.0 (15/15) | P25/H30/E45 (10), P25/H35/E40 (5) |
| Street | 10 | 58.6 | 81.2 | 22.6 (15/15) | 10.6 (12/15) | 16.7 (14/15) | P25/H50/E25 (9), P30/H45/E25 (3) |
| Street | 20 | 56.6 | 87.3 | 30.6 (15/15) | 7.6 (10/15) | 23.6 (15/15) | P25/H50/E25 (12), P30/H45/E25 (3) |
| Street | 30 | 52.4 | 89.5 | 37.1 (15/15) | 16.1 (15/15) | 27.9 (15/15) | P25/H50/E25 (13), P30/H45/E25 (2) |
| **All** | | | | 19.5 (max 58.6; 129/135) | 14.6 (max 63.6; 111/135) | 27.8 (max 75.8; 130/135) | |

| Switch | Mean gap (pp) | Max gap (pp) | Clear cells |
|---|---|---|---|
| Best-vs-balanced tune used vs hot_early | 1.2 | 12.0 | 3/45 |
| Best-vs-balanced tune used vs conserver | 2.4 | 25.4 | 7/45 |
| Best-at-10-turns tune used at 30 turns | 2.2 | 16.6 | 6/45 |

Dominance: best single tune **P30/H40/E30** (mean 74.4%, even 67.3%) gives up 12.5 pp on average vs each cell's best (max 39.6); within 2 pp in 1/135 cells, clearly worse in 119/135. Best tunes: P25/H50/E25 (48), P25/H30/E45 (25), P30/H45/E25 (17), P45/H30/E25 (17), P25/H35/E40 (13), P35/H40/E25 (6), P25/H25/E50 (3), P40/H30/E30 (2), P25/H45/E30 (2), P25/H40/E35 (1), P35/H30/E35 (1).

| Play | r | Target | Even spread (min-max by district x length) | Best tune per cell |
|---|---|---|---|---|
| perfect | 0.80 | 10-25 | 15.3 (2.9-26.4) | 43.6 |
| perfect | 1.00 | wins | 99.7 (98.4-100.0) | 100.0 |
| average | 1.00 | - | 3.8 (0.1-12.1) | 10.6 |
| average | 1.05 | 60-75 | 67.3 (52.4-77.9) | 86.9 |
| average | 1.10 | 60-75 if cap is 110% | 87.0 (77.1-94.9) | 96.9 |

By district, even spread: perfect0.8: touge 20.8, wangan 21.7, street 3.3; perfect1.0: touge 99.9, wangan 99.8, street 99.4; average1.0: touge 4.5, wangan 5.1, street 1.6; average1.05: touge 76.1, wangan 70.1, street 55.9; average1.1: touge 92.5, wangan 88.2, street 80.5
