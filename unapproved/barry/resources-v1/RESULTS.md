# resources-v1: raw first-pass sim of the fuel / brakes / suspension system

Barry, 2026-11-12. **Draft, not approved.** Austin okayed a raw first pass ("Is it possible to sim the numbers raw right now?"). Nothing in `sim/` or `design/` was changed, and nothing here is committed. Every number below comes from a run in this folder; every rule and constant tagged PLACEHOLDER is my invention and needs Austin's decision.

## Summary

**What I tested.** The card draw is gone. Each turn the player may drive any 3-stance line. Every stance spends a resource: POW burns fuel, EN wears brakes, and HAN loads suspension. Fuel and brakes never come back, and suspension recovers each turn. A tank's size is set by that stat's share of the build. Corners cost different amounts, and repeating a stance inside one line costs more. When a stance can't be paid for, it is penalised. Bosses keep their district lines but get one of three spending styles: balanced (the live 65/21/14), hot-early, or conserver.

**1. The retune meta shows up, and its strength depends on the empty rule.**
- With the **soft penalty** (the base model), retuning is worth about 5 pp over an even spread and about 9 pp over a car tuned for another district. One tune is close to best almost everywhere, so this is only a partial yes.
- With the **hard block** (you can't pick a stance you can't pay for), retuning becomes the main decision. On average:
  - the right tune beats an even spread by **19.5 pp** (clear in 129/135 cells);
  - it beats the tune that's best in the other districts by **27.8 pp** (clear in 130/135 cells);
  - no single tune comes within 2 pp of the best in more than 1 of 135 cells.

**2. Tracks do ask for different resources, but not the ones in Austin's examples.** Under counter play you spend whatever beats the district's signature stance:
- Wangan bosses run POW lines, so you counter with EN and burn **brakes**.
- Touge bosses run HAN lines, so you counter with POW and burn **fuel** (suspension comes second).
- Street burns fuel and brakes.

Corner physics only adjusts this. If Austin wants Wangan to burn fuel, either the district lines or the stance-to-resource mapping has to change.

**3. Combat targets.**
- The **live model already misses "perfect play at 80% beats the boss 10–25%"**: perfect play wins 98.4% there. Adding resources with a soft penalty doesn't fix that (98.7%).
- One setting hit all three targets for an **even-spread** car: hard block with stat leverage ×1.25 and smaller tanks. It gave perfect play 15.3% at r 0.8, 99.7% at r 1.0, and average play 67.3% at the 105% cap.
- **A retuned car overshoots on that same setting:** 43.6% at r 0.8 and 86.9% at the cap. If tuning is the meta, the targets should be measured with the right tune, and the setting re-fitted.

**4. "The stat mix barely matters" holds for payoff, not for win rate.**
- In the live model the mix is worth about +8% of payoff, but at the cap that moves average play's win rate by **8.2 pp** (best tune vs even spread). The gap between the best and worst tune averages 25.8 pp.
- Most of that is one direction: max POW was the best tune in 21 of 45 cells. So the live model rewards a "max POW" build, not retuning. The new hard-block model rewards a different build per district.

**5. Opponent styles are very readable as modelled, maybe too readable.** Knowing a boss's style (hot-early or conserver) instead of assuming the default line split is worth 32–45 pp for an average player. Retuning for the boss's style is worth much less: 1–2 pp on average, up to 25 pp in the worst cell.

**Recommended next step (needs Austin's go):** keep the hard block, then re-fit tank size and κ so the *correctly tuned* car hits the targets. Soften the wrong-district penalty, which reaches about 40–60 pp in Wangan. Also decide whether Wangan should burn fuel (see 2).

## How it was run

- **Model:** `resources_v1.py`. It is vectorised and reads the live sim read-only: LINE_SET_C, the 65/21/14 split, Phi/tau payoff (W0 0.10, T_MAX 0.75, L_MAX 0.25, TAU_*), V = r^κ with KAPPA_BY_LENGTH, OPPONENT_QTE 1.0, the visible QTE zone, the q_read read model, and the 15 official stand-in laps (`official_tracks()`).
  - Dropped: DECK_ALPHA, HAND_SIZE, assign_hand, and the MU/ETA share multipliers. Resources replace them.
- **Live model for comparison:** `run_old()` in the same file, which re-implements the card-draw engine.
  - `validate_old.py` checks it against the real `velocity_shift.match.run_match`. The 4 configs matched within 0.01–0.94 pp (live at N=3000, vectorised at N=20000; `validate_old.json`).
- **Main runs:** `run_resources_v1.py` and `run_hardblock.py`, analysed by `analyze.py` and `analyze_hb.py`. Outputs are `results.json`, `results_hb.json`, `analysis*.json` and `tables*.md`.
  - Every cell is **9 batches × 1,000 runs = 9,000 runs**, with batch seeds **20261112–20261120**.
  - All 22 builds in a cell (21-tune grid + even spread) see the same opponent lines and read rolls.
  - **Clear** means at least 5 pp with the same sign in all 9 batches.
  - Main run: 1,422 new-model cells and 360 live-model cells, 384 s on 8 cores. Hard-block rerun: 675 cells, 141 s.
- **Screening runs:** `calibrate.py`, `calibrate2.py`, `target_fit.py` and `hb_fit.py` used N=2,000 with seed 7, on track #1 of each district only. I used them to choose settings, and I don't quote them as results except where marked "screen".
  - Caveat: `calibrate.json` was produced before I normalised the share curve and with suspension recovery at 0.85, so rerunning `calibrate.py` today gives different numbers.
- **Tune grid:** every POW/HAN/EN split from 25% to 50% in 5 pp steps (21 tunes) at a fixed stat total, plus the exact even spread. Tunes are written P/H/E, for example P25/H50/E25.
- **Play levels:**
  - *Perfect* = reads every Entry (q_read 1.0) and raw QTE 1.0.
  - *Average* = q_read 0.6 and the PLACEHOLDER "average" QTE profile at the visible zone for that r. That is 0.6 at r ≥ 1.05 and lower below.
  - Both are the existing definitions.
- **Boss:** even-spread stats, QTE 1.0, and the same resource rules as the player.

## Results tables

## Base model (soft penalty)

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


## Hard-block B (full size)

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

## Placeholders and assumptions (all need Austin's decision)

| # | What | Value used | Where |
|---|---|---|---|
| 1 | Corner cost multipliers per stance (fuel, suspension, brakes) for HP, CR, DR, IR, N90, CH, ES, SW | e.g. HP 0.8/1.2/1.4, SW 1.4/0.9/0.6, ES 0.8/1.4/0.9 (full table in code) | `CORNER_COST` |
| 2 | Passive wear per corner (drained every turn, whatever line is driven) | 0–0.4 per resource (e.g. SW fuel 0.4, ES suspension 0.4, N90 brakes 0.4) | `CORNER_PASSIVE` |
| 3 | Base cost of one stance | 1.0 | `BASE_COST` |
| 4 | What makes a line "aggressive" | Repeating a stance inside one line: the k-th use costs 1 + 0.25·(k−1), so PPP costs 3.75 vs PHE 3.0 | `AGG_STEP` |
| 5 | Fuel/brake tank size | An even build holds TANK_FACTOR × the cross-track average race demand. 0.5 in the base model, 0.4 in hard-block B. Scales with race length (10/20/30 turns) | `TANK_FACTOR` |
| 6 | Suspension tank and recovery | Tank = 3 turns of average demand. Recovers 0.6 × average demand per turn. Does not scale with race length | `SUSP_TANK_TURNS`, `SUSP_REC_FACTOR` |
| 7 | How tank size follows the stat | Tank multiplier = 3·share² / Σ share². The three multipliers always sum to 3, so specialising doesn't create extra total tank | `SHARE_EXPONENT` = 2 |
| 8 | Tanks also scale with the stat total vs the boss (r) | Yes, linearly (r¹) | `TANK_WITH_R`, `TANK_R_EXP` |
| 9 | What an empty resource does | Base: soft, the unpaid share of a stance pays × 0.4. Variants: "downgrade" (the unpaid share drops one outcome step) and **hard block** (can't pick it) | `EMPTY_RULE`, `EMPTY_MULT`, `hard_block` |
| 10 | Stat leverage κ | Live KAPPA_BY_LENGTH (1.55/1.35/1.20). Hard-block B uses ×1.25 (1.94/1.69/1.50). Screens tried up to ×4 | `KAPPA_SCALE` |
| 11 | MU and ETA (stat-share payoff/timing bonuses) | Removed in the new model | — |
| 12 | Opponent styles | Lines ranked by cost at each corner, then the 65/21/14 split applied to that order. Hot-early: costliest first for the first half, cheapest after. Conserver: cheapest first for the first 2/3, costliest after. Balanced: the live split | `style_weights`, `HOT_SWITCH`, `CONS_SWITCH` |
| 13 | Boss stats and QTE | Even spread, QTE 1.0 (OPPONENT_QTE, never approved) | — |
| 14 | Player knows the boss's style | Yes in all main runs (scouted). Unscouted only in the scouting table | `scouted` |
| 15 | Player AI | Correct read → most likely line under the boss's current style, then choose each stance by expected progress difference minus a rationing price (0.6 × how far a resource is behind pace × cost). Misread → live rule (tie with prob q_read, else lose) | `RATION_LAMBDA` |
| 16 | Refill between laps / pit | None | — |
| 17 | Can the player see the boss's gauges | Not modelled (the AI ignores the boss's gauges) | — |
| 18 | Target definitions | Perfect = q_read 1.0 + raw QTE 1.0. "At 100% perfect play wins" read as ≥ 85% (design/02 §0.4). Targets checked on an even-spread car and on the best tune per cell | — |
| 19 | Track layouts | The 15 stand-in laps in `sim/config/tracks_v1.json` (placeholders already) | — |

## What worked and what didn't

**Worked**
- **The hard block makes retuning the main decision.** The best tune changes by district: Wangan wants brakes (P25/H30/E45), Street wants suspension (P25/H50/E25), and Touge is split between P45/H30/E25 and P25–30/H45–50/E25. A wrong-district tune clearly loses in 130/135 cells.
- **Suspension now matters under the hard block.** In the base model, no build with 45–50% HAN was best anywhere.
- **Hard-block B hits all three combat targets for an even-spread car**, on average across districts.
- **Removing the card draw doesn't break parity:** perfect play at r 1.0 still wins 99.7–100%.

**Didn't work, or still open**
- **Soft penalty:** retuning is only worth about 5 pp, one tune is near-best in many cells, and average play at the cap jumps to 78.5% (target 60–75).
- **Perfect play at r 0.8 is far above 10–25% in the live model and every soft variant.** A perfect reader wins most clashes, so only a much steeper stat leverage or the hard block pulls it down.
  - In the screen, κ ×3 alone got perfect play at 0.8 to 18.4%, but average play at the cap rose to 88.3%. The skill gap between perfect and average play is too wide for one stat knob to satisfy both targets.
- **Under hard-block B, a correctly tuned car overshoots both targets** (43.6% at r 0.8, 86.9% at the cap).
- **Street is much harder than the other districts** under hard-block B: an even car wins 55.9% at the cap vs 76.1% Touge and 70.1% Wangan, and perfect play wins only 3.3% at r 0.8.
- **The wrong-district penalty may be too harsh:** 40–59 pp in Wangan.
- **The resource each district burns is set by the district lines, not by corner physics** (see Summary 2).
- **The scouting effect (32–45 pp) is probably too large.** It comes from how I built the styles: they reorder which line is most likely, so a player who assumes the default split guesses wrong a lot.
- **A cap of 110% doesn't fit with these settings:** average play at r 1.10 is 87.0% even-spread under hard-block B (88.7% base).

## Recommended next tweaks (each needs Austin's go before I run it)

1. Choose the empty rule. I recommend the hard block, possibly softened so that an empty stance is allowed but always loses.
2. Decide whether the combat targets assume the right tune. If yes, re-fit tank size and κ on the best-tuned car.
3. Bring Street's difficulty in line: Street corner costs, or more Street suspension recovery.
4. Decide the stance-to-resource mapping vs Austin's examples (Wangan burns fuel?). That probably means changing LINE_SET_C (Nathaniel and Desmond) or the corner tables.
5. Make styles less of a giveaway: keep the line order and change only how much each line is used, or blend in the default split.
6. Add a between-lap refill option and boss-gauge visibility once Austin picks them.
7. Story and art flags: boss spending styles touch story characters (Desmond / Nathaniel). The gauges are with Arthur already.
