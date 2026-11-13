# resources-v2 tables (full runs: 9 batches x 1000 races, 15 laps x 10/20/30 turns x 3 boss styles)

## Combat targets and block rates (average play at the cap; perfect play at 0.8 / 1.0)

| Candidate | Perfect 0.8 tuned | low-dry | even | Perfect 1.0 tuned | even | Avg cap tuned | low-dry | even | Tuned: races with a block | races with a read blocked | read corners blocked | Even: races blocked | Wrong-district: races blocked | Low-dry: races blocked |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_scarce | 14.3 | 1.3 | 5.0 | 100.0 | 99.9 | 61.2 | 42.2 | 42.0 | 96.0 | 88.5 | 27.7 | 18.1 | 95.2 | 19.3 |
| A_mid | 25.4 | 4.1 | 8.0 | 100.0 | 100.0 | 58.4 | 48.3 | 48.1 | 83.3 | 67.9 | 14.0 | 5.6 | 79.7 | 7.0 |
| A_mid_norefill | 43.3 | 14.0 | 19.0 | 100.0 | 100.0 | 55.7 | 49.5 | 49.2 | 69.4 | 51.1 | 8.6 | 4.1 | 62.9 | 5.9 |
| A_mid_refill50 | 16.9 | 3.6 | 6.9 | 100.0 | 99.9 | 63.1 | 46.4 | 46.2 | 86.1 | 76.2 | 22.1 | 11.5 | 82.8 | 13.1 |
| B_generous | 22.6 | 6.5 | 8.8 | 100.0 | 100.0 | 57.7 | 55.6 | 55.1 | 35.3 | 15.6 | 1.9 | 4.4 | 44.6 | 7.8 |

## Retune gap (average play at the cap)

| Candidate | Tuned - even (pp) | % cells clear | Tuned - wrong district (pp) | % cells clear | Worst cell wrong-district penalty | Low-dry tune - even | % cells clear |
|---|---|---|---|---|---|---|---|
| A_scarce | 19.2 | 90.4 | 25.7 | 88.9 | 63.9 | 0.1 | 0.0 |
| A_mid | 10.3 | 77.8 | 11.2 | 72.6 | 33.6 | 0.2 | 0.0 |
| A_mid_norefill | 6.5 | 54.1 | 6.7 | 56.3 | 20.7 | 0.2 | 0.0 |
| A_mid_refill50 | 16.9 | 80.7 | 22.2 | 75.6 | 66.0 | 0.3 | 0.0 |
| B_generous | 2.6 | 16.3 | 0.9 | 0.0 | 3.9 | 0.5 | 0.0 |

## By district (average play at the cap)

| Candidate | touge tuned win | touge gap vs even | touge gap vs wrong | touge worst wrong | touge tuned blocked | wangan tuned win | wangan gap vs even | wangan gap vs wrong | wangan worst wrong | wangan tuned blocked | street tuned win | street gap vs even | street gap vs wrong | street worst wrong | street tuned blocked |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_scarce | 56.3 | 14.4 | 26.9 | 54.6 | 93.9 | 62.9 | 34.1 | 37.1 | 63.9 | 96.9 | 64.5 | 9.2 | 12.9 | 34.7 | 97.2 |
| A_mid | 55.8 | 10.4 | 12.8 | 30.3 | 84.8 | 55.3 | 13.9 | 15.3 | 33.6 | 76.9 | 63.9 | 6.5 | 5.6 | 18.2 | 88.1 |
| A_mid_norefill | 56.1 | 10.2 | 11.0 | 20.7 | 82.9 | 49.2 | 5.0 | 7.3 | 12.3 | 41.7 | 61.8 | 4.2 | 1.7 | 5.3 | 83.7 |
| A_mid_refill50 | 59.1 | 14.0 | 24.9 | 57.8 | 86.5 | 64.8 | 29.0 | 33.8 | 66.0 | 82.3 | 65.4 | 7.7 | 8.0 | 36.1 | 89.5 |
| B_generous | 57.7 | 5.1 | 0.8 | 3.9 | 42.2 | 51.4 | 1.1 | 1.7 | 3.7 | 11.6 | 64.1 | 1.7 | 0.1 | 0.4 | 52.1 |

## Block rates by race length (average play at the cap, % of races with any wanted stance blocked)

| Candidate | Tuned blocked | Tuned read corners blocked | Even blocked | Wrong blocked | Gap vs even | Gap vs wrong |
|---|---|---|---|---|---|---|
| A_scarce | {10: 88.6, 20: 99.6, 30: 99.8} | {10: 20.4, 20: 30.0, 30: 32.7} | {10: 6.9, 20: 18.2, 30: 29.2} | {10: 86.8, 20: 99.3, 30: 99.6} | {10: 9.7, 20: 20.7, 30: 27.3} | {10: 11.6, 20: 27.7, 30: 37.7} |
| A_mid | {10: 59.4, 20: 92.1, 30: 98.3} | {10: 8.3, 20: 15.3, 30: 18.3} | {10: 2.1, 20: 5.6, 30: 9.1} | {10: 53.4, 20: 88.7, 30: 97.1} | {10: 5.2, 20: 10.5, 30: 15.1} | {10: 5.4, 20: 10.9, 30: 17.4} |
| A_mid_norefill | {10: 59.4, 20: 72.4, 30: 76.5} | {10: 8.3, 20: 8.4, 30: 9.0} | {10: 2.1, 20: 3.9, 30: 6.4} | {10: 53.4, 20: 65.6, 30: 69.6} | {10: 5.2, 20: 6.6, 30: 7.7} | {10: 5.4, 20: 6.9, 30: 7.7} |
| A_mid_refill50 | {10: 59.4, 20: 99.0, 30: 100.0} | {10: 8.3, 20: 24.8, 30: 33.1} | {10: 2.1, 20: 9.5, 30: 23.1} | {10: 53.4, 20: 95.7, 30: 99.5} | {10: 5.2, 20: 18.0, 30: 27.6} | {10: 5.4, 20: 23.5, 30: 37.8} |
| B_generous | {10: 20.4, 20: 38.2, 30: 47.2} | {10: 1.5, 20: 1.9, 30: 2.1} | {10: 1.9, 20: 4.3, 30: 7.0} | {10: 20.2, 20: 48.2, 30: 65.5} | {10: 1.8, 20: 2.6, 30: 3.5} | {10: 1.7, 20: 0.6, 30: 0.4} |

## Cells

| Candidate | % cells where the max-win tune is blocked in <=15% of races | % cells read-blocked <=5% | % cells where some tune is blocked <=15% | Perfect 1.0 tuned races blocked | Perfect 1.0 read corners blocked | Tuned clashes in limp (%) |
|---|---|---|---|---|---|---|
| A_scarce | 0.0 | 0.7 | 45.9 | 90.4 | 33.1 | 0.0 |
| A_mid | 0.0 | 14.8 | 100.0 | 78.5 | 22.3 | 0.0 |
| A_mid_norefill | 0.0 | 40.0 | 100.0 | 78.5 | 17.6 | 0.0 |
| A_mid_refill50 | 0.0 | 14.8 | 71.1 | 79.3 | 26.3 | 0.0 |
| B_generous | 34.1 | 84.4 | 100.0 | 55.6 | 6.9 | 0.0 |

## Reads vs pacing vs scouting (average QTE at the cap, tuned car)

| Candidate | Perfect reads (q 1) | Random stances, same tune | Read gap | % cells clear | Avg (q 0.6) - random | Pacing gap (rationing - greedy) | Largest cell pacing effect | Scouting value, style blend 0.3 | Scouting value, style blend 1.0 | % cells clear (1.0) |
|---|---|---|---|---|---|---|---|---|---|---|
| A_scarce | 99.5 | 15.0 | 84.5 | 100.0 | 44.6 | 0.0 | 0.2 | 0.0 | 25.6 | 60.0 |
| A_mid | 99.6 | 10.7 | 88.9 | 100.0 | 42.6 | -0.0 | 0.1 | 0.0 | 29.7 | 60.7 |
| B_generous | 99.7 | 12.3 | 87.4 | 100.0 | 44.1 | 0.0 | 0.0 | 0.0 | 30.7 | 57.8 |
| live model (card draw, r 1.05) | 99.9 | 10.0 | 89.9 | | 57.2 | | | | | |
