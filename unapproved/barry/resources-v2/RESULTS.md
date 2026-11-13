# resources-v2: hard block, no card draw, refit (DRAFT, NOT APPROVED)

Barry, 2026-11-13. Code: `resources_v2.py` (model), `run_v2.py` (full runs), `analyze_v2.py` (writes `analysis_v2.json` and `tables_v2.md`), and `screen*.py` (settings screens). Full runs: 9 batches × 1000 races (seeds 20261112–20261120), all 15 stand-in laps × 10/20/30 turns × 3 boss styles, a 21-split tune grid (each stat 25–50% in 5 pp steps) plus the exact even spread. Same races for every tune (common random numbers). "Clear" means the mean difference is at least 5 pp and all 9 batch differences have the same sign. Nothing in sim/ or design/ was changed, and nothing is committed.

## Plain-English summary

- **The hard block works mechanically. But a "tuned" car and a "rarely runs dry" car are, in this model, two different cars.** The tune that wins most always specialises far enough to run dry. In the main candidate (A_mid), the best tune hits a block in 83% of races, and its read-counter is blocked on 14% of read corners. The tune that wins most while staying under the 15%-of-races limit is basically the even car: it gains only +0.2 pp over even, and is clear in 0% of cells. Unused tank capacity is worth nothing, so a retune only pays off when the player spends the tank down. **Goal 1 (rarely dry) and Goal 3 (meaningful retune gap) conflict, and no setting I tried hits both.** Austin has to pick which one gives.
- **Combat targets can be hit for the tuned car.** A_scarce gives perfect at 80% = 14.3%, perfect at 100% = 100%, average at cap 1.05 = 61.2%. A_mid_refill50 gives 16.9 / 99.9 / 63.1. A_mid narrowly misses: 25.4 (just over 25) and 58.4 (just under 60). The cap stays at 1.05; κ is scaled (×1.0–1.5 depending on candidate) and the tank size grows with r³. The even car is far below the tuned car on average play (42–55%). So the targets assume the player retunes.
- **The retune gap is meaningful only in the scarce setups.** A_mid: +10.3 pp vs even (clear in 78% of cells) and +11.2 vs the wrong district (73%). The worst wrong-district penalty fell to 33.6 pp (v1 was 40–59). A_scarce has a bigger gap (19.2 / 25.7) but brings back the extreme penalty (63.9). The generous tank (B) cuts blocks to 35% of races and 1.9% of read corners, but the gap falls to 2.6 / 0.9 pp, which is not a meta.
- **Street is still the odd one out.** It is the easiest district: tuned win about 64% vs about 55–56% for Touge and Wangan in A_mid. It also has the weakest retune signal: in A_mid, the gap vs wrong district is 5.6 pp, clear in 36% of cells, vs 13–15 pp elsewhere.
- **Reads, not pacing, decide races.** On a tuned car, perfect reads vs random stances = **84.5–88.9 pp** (live card-draw model: **89.9 pp**). Average reads (q 0.6) vs random = 42.6–44.6 pp (live 57.2). The pacing effect I could measure (my rationing AI vs greedy) = **0.0 pp**, with no cell above 0.2 pp. So, as built, the game is not a resource-pacing game. But see the caveat: this only measures my simple rationing rule, not the best possible pacing.
- **Lap refill matters.** With the same tanks, the 75% between-lap refill (A_mid) vs no refill (A_mid_norefill) changes the gap from 10.3 to 6.5 pp vs even. Blocked races at 20/30 turns go from 92/98% to 72/77%. A 50% refill is scarcer again (gap 16.9, blocked 99–100% at 20/30 turns). The refill is effectively a second tank-size knob.
- **Boss-style read value.** With a style blend of 0.3 it is **exactly 0 pp**: blending 30% style into 65/21/14 can never change which line is most likely, so knowing the style changes nothing. With the full style weights (blend 1.0, the v1 setup) it is **25.6–30.7 pp**: 0 for balanced, 47–57 for hot_early, 29–35 for conserver. "Modest" sits somewhere between, and needs a blend of about 0.35–0.6 or reshaped styles. I did not run that.

## Candidates (all use the live misread rule, SUSP_TANK_TURNS 5, SUSP_REC_FACTOR 1.1, TANK_REF_Q 0.6, cap 1.05)

| Name | Tank mode | Refill | TANK_FACTOR | SHARE_EXPONENT | DEMAND_SLANT | KAPPA_SCALE | TANK_R_EXP |
|---|---|---|---|---|---|---|---|
| A_scarce | per lap | 75% | 1.3 | 1.5 | 1.0 | 1.0 | 3 |
| A_mid | per lap | 75% | 1.6 | 1.5 | 1.0 | 1.25 | 3 |
| A_mid_refill50 | per lap | 50% | 1.6 | 1.5 | 1.0 | 1.25 | 3 |
| A_mid_norefill | whole race | none | 1.6 | 1.5 | 1.0 | 1.25 | 3 |
| B_generous | whole race | none | 1.6 | 1.0 | 0.5 | 1.5 | 3 |

How they were chosen: the screens (N 1000, track #1 per district, 27 cells) are in `screen_A…H.json`. **Screens A–D used older code** (before the misread-fallback fix, the random fallback and DEMAND_SLANT). Screens E–G used the "random belief" misread rule. Screen H, with the live rule, picked the final settings. Screen numbers differ slightly from the full runs (for example, A_mid screened at 19.4 / 61.5 but came out 25.4 / 58.4 in the full run). Only full-run numbers are quoted below.

## Tables (full runs)

### Combat targets (win %) and block rates (average play at cap 1.05)

Targets: perfect at 0.8 = 10–25; perfect at 1.0 ≥ 85; average at cap = 60–75.

| Candidate | Perfect 0.8 tuned | Perfect 0.8 even | Perfect 1.0 tuned | Avg cap tuned | Avg cap low-dry | Avg cap even | Tuned: % races blocked | Tuned: % races with a read blocked | Tuned: % read corners blocked | Even: % races blocked | Wrong-district: % races blocked |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_scarce | **14.3** ✓ | 5.0 | 100.0 ✓ | **61.2** ✓ | 42.2 | 42.0 | 96.0 | 88.5 | 27.7 | 18.1 | 95.2 |
| A_mid | 25.4 ✗ (0.4 over) | 8.0 | 100.0 ✓ | 58.4 ✗ (1.6 under) | 48.3 | 48.1 | 83.3 | 67.9 | 14.0 | 5.6 | 79.7 |
| A_mid_refill50 | **16.9** ✓ | 6.9 | 99.9 ✓ | **63.1** ✓ | 46.4 | 46.2 | 86.1 | 76.2 | 22.1 | 11.5 | 82.8 |
| A_mid_norefill | 43.3 ✗ | 19.0 | 100.0 ✓ | 55.7 ✗ | 49.5 | 49.2 | 69.4 | 51.1 | 8.6 | 4.1 | 62.9 |
| B_generous | **22.6** ✓ | 8.8 | 100.0 ✓ | 57.7 ✗ | 55.6 | 55.1 | 35.3 | 15.6 | 1.9 ✓ | 4.4 | 44.6 |

Definitions:
- "Tuned" = the best of the 21 splits per cell, chosen on that play level's own 9-batch mean. That carries a small upward selection bias.
- "Low-dry" = the best split whose races are blocked in no more than 15% of races.
- "Races blocked" = any stance the player wanted (including the deliberate tie/lose stance on a misread) was unaffordable at least once.
- "Read blocked" = the counter to a correct read was unaffordable.
- Limp (nothing affordable) rounds to 0.0% of clashes in every candidate.

Block-rate goal: no candidate's tuned car meets "≤10–15% of races". B meets "read corners ≤5%" (1.9%) and is close on races with a read blocked (15.6%). The even car meets both goals everywhere (4–18% of races, ≤0.7% of read corners). The max-win tune is blocked in ≤15% of races in 0% of cells (A candidates) and 34% of cells (B).

"Wrong district runs dry more": wrong-district tunes run dry about as often as the right tune (79.7 vs 83.3 in A_mid), because both are specialised. Only in B is it clearly more (44.6 vs 35.3). The cost of the wrong tune shows up as lost wins, not as more blocks.

### Retune gap (average play at cap)

| Candidate | Tuned − even (pp) | % cells clear | Tuned − wrong district (pp) | % cells clear | Worst cell, wrong district | Low-dry − even | % clear |
|---|---|---|---|---|---|---|---|
| A_scarce | 19.2 | 90.4 | 25.7 | 88.9 | 63.9 | 0.1 | 0 |
| A_mid | 10.3 | 77.8 | 11.2 | 72.6 | 33.6 | 0.2 | 0 |
| A_mid_refill50 | 16.9 | 80.7 | 22.2 | 75.6 | 66.0 | 0.3 | 0 |
| A_mid_norefill | 6.5 | 54.1 | 6.7 | 56.3 | 20.7 | 0.2 | 0 |
| B_generous | 2.6 | 16.3 | 0.9 | 0.0 | 3.9 | 0.5 | 0 |

"Wrong district" = the split that is best on average over the other two districts' laps, at the same length and boss style.

### By district (average play at cap)

| Candidate | Touge tuned / gap vs even / gap vs wrong / worst wrong | Wangan … | Street … |
|---|---|---|---|
| A_scarce | 56.3 / 14.4 / 26.9 / 54.6 | 62.9 / 34.1 / 37.1 / 63.9 | 64.5 / 9.2 / 12.9 / 34.7 |
| A_mid | 55.8 / 10.4 / 12.8 / 30.3 | 55.3 / 13.9 / 15.3 / 33.6 | 63.9 / 6.5 / 5.6 / 18.2 |
| A_mid_refill50 | 59.1 / 14.0 / 24.9 / 57.8 | 64.8 / 29.0 / 33.8 / 66.0 | 65.4 / 7.7 / 8.0 / 36.1 |
| A_mid_norefill | 56.1 / 10.2 / 11.0 / 20.7 | 49.2 / 5.0 / 7.3 / 12.3 | 61.8 / 4.2 / 1.7 / 5.3 |
| B_generous | 57.7 / 5.1 / 0.8 / 3.9 | 51.4 / 1.1 / 1.7 / 3.7 | 64.1 / 1.7 / 0.1 / 0.4 |

**A_mid, % cells clear vs wrong district:** Touge 88.9, Wangan 93.3, Street 35.6.

**A_mid average tuned split (fuel / suspension / brakes):**
- Touge 0.27 / 0.25 / 0.48
- Wangan 0.25 / 0.50 / 0.25
- Street 0.42 / 0.30 / 0.28

The Wangan and Touge tunes sit on the edge of the 25–50% grid, so a wider stat range would make the gaps larger.

### Block rates and gaps by race length (A_mid vs refill options)

| Candidate | Tuned % races blocked (10/20/30) | Tuned % read corners blocked | Even % races blocked | Gap vs even | Gap vs wrong |
|---|---|---|---|---|---|
| A_mid (75% refill) | 59.4 / 92.1 / 98.3 | 8.3 / 15.3 / 18.3 | 2.1 / 5.6 / 9.1 | 5.2 / 10.5 / 15.1 | 5.4 / 10.9 / 17.4 |
| A_mid_refill50 | 59.4 / 99.0 / 100.0 | 8.3 / 24.8 / 33.1 | 2.1 / 9.5 / 23.1 | 5.2 / 18.0 / 27.6 | 5.4 / 23.5 / 37.8 |
| A_mid_norefill | 59.4 / 72.4 / 76.5 | 8.3 / 8.4 / 9.0 | 2.1 / 3.9 / 6.4 | 5.2 / 6.6 / 7.7 | 5.4 / 6.9 / 7.7 |
| B_generous | 20.4 / 38.2 / 47.2 | 1.5 / 1.9 / 2.1 | 1.9 / 4.3 / 7.0 | 1.8 / 2.6 / 3.5 | 1.7 / 0.6 / 0.4 |
| A_scarce | 88.6 / 99.6 / 99.8 | 20.4 / 30.0 / 32.7 | 6.9 / 18.2 / 29.2 | 9.7 / 20.7 / 27.3 | 11.6 / 27.7 / 37.7 |

10-turn races are identical across refill options (no refill happens in a single lap). In lap mode the tank is sized for one lap, so a 10-turn race in A_mid gets a smaller gap (about 5 pp) than longer races.

### Reads vs pacing vs scouting (tuned car, average QTE at cap 1.05)

| Model | Perfect reads (q 1) | Random stances, same tune | **Read gap** | Avg reads (q 0.6) − random | Pacing gap (rationing − greedy) | Scouting value, blend 0.3 | Scouting value, blend 1.0 |
|---|---|---|---|---|---|---|---|
| A_scarce | 99.5 | 15.0 | **84.5** (100% cells clear) | 44.6 | 0.0 (max cell 0.2) | 0.0 | 25.6 (60% cells clear) |
| A_mid | 99.6 | 10.7 | **88.9** (100%) | 42.6 | 0.0 (max 0.1) | 0.0 | 29.7 (61%) |
| B_generous | 99.7 | 12.3 | **87.4** (100%) | 44.1 | 0.0 (max 0.0) | 0.0 | 30.7 (58%) |
| Live card-draw model | 99.9 | 10.0 | **89.9** | 57.2 | n/a | n/a | n/a |

Notes on how each measure works:
- The random-stance player picks uniformly among affordable stances, so it never gets blocked. A perfect reader on a tuned car is blocked in 54% of races (A_mid) and on 12% of read corners, and still wins 99.6%.
- The live random player plays 3 random cards from a 6-card hand.
- The live model has no boss styles. Its "tuned" car is its best stat split per lap and length, at r 1.05 with average QTE. Its average-play figure is 72.4% on the best split.

## Placeholders and assumptions (all need Austin's sign-off)

1. **Misread rule = live**: a misread clash ties with probability q_read, else loses. q_read 0.6 = "average".
   - I also tried a "random belief" rule (a misread = a random guess of the boss line, countered with resource awareness; screens E–G). It makes average play much stronger: average at cap was 80–94% for the tuned car, and never in 60–75 at a sane κ. **The combat targets only work with the live rule.**
   - Under the live rule, if the deliberate tie or lose stance is blocked, the player plays a random affordable stance.
2. **Hard block for both sides.** The boss falls back to its affordable stance with the most left. If nothing is affordable, the side "limps" at 0.4× progress (EMPTY_MULT 0.4).
3. **Tank size**:
   - tank = TANK_FACTOR × the demand of a q 0.6 player (TANK_REF_Q) over one lap (lap mode) or the race (race mode);
   - × a share curve 3·s^e/Σs^e (SHARE_EXPONENT e);
   - × r^TANK_R_EXP, with TANK_R_EXP 3: a stronger car gets a bigger tank. This is the main lever that put perfect at 0.8 in 10–25.
   - Suspension: tank = 5 turns of demand, recovering 1.1× per-turn demand each turn.
4. **Between-lap refill** puts back REFILL × tank for fuel and brakes only (suspension already recovers).
5. **Track wear** = district demand normalised so every track costs the same in total (TRACK_NORMALIZE). DEMAND_SLANT controls how much of that total follows the district's own resource mix (1.0 = all, 0.5 = half; the rest is spread evenly).
6. **κ** = live KAPPA_BY_LENGTH × KAPPA_SCALE (1.0–1.5). The cap stays at 1.05; I did not need 1.10 (in screens, 1.10 shrank the retune gaps to 2–9 pp).
7. **Boss styles** = STYLE_BETA 0.3 blend of the style weights into 65/21/14. This structurally zeroes the scouting value (see above).
8. **Rationing AI**:
   - It subtracts 0.6 × cost × shortfall from a stance's value when the tank plus recovery won't cover demand until the next refill.
   - Its pacing gap is 0.0. That says this rule almost never changes a choice; it does **not** prove that smarter pacing is worthless.
   - The rule only acts on read turns (misreads follow the live rule).
9. Tune grid = 25–50% per stat in 5 pp steps, plus even. Several tuned splits hit the grid edge.
10. Average QTE = live raw_qte_score(r, "average"). Perfect = q_read 1, QTE 1. The boss's QTE = 1.0 (live).

## Decisions needed from Austin

1. **The core conflict: rarely-dry vs retune meta.** In this model the winning tune always runs dry, and a tune that rarely runs dry is the even car. Options:
   - (a) Accept planned dryness. Use A_mid (or A_mid_refill50 to hit the combat targets): about 10–17 pp retune gap, but the tuned car is blocked in 83–86% of races and on 14–22% of read corners.
   - (b) Use generous tanks (B): read corners blocked 1.9%, but no retune meta (gap 0.9–2.6 pp). Retuning would then need a non-resource lever, such as stat effects on Φ like the live MU/ETA, or a wider stat range.
   - (c) Give leftover tank a value or put a cost on going dry (for example, leftover fuel boosts the final sprint, or a blocked stance also costs progress). That would let "tuned" and "rarely dry" line up. Not built, so no numbers.
2. **Refill**: 75% between laps (A_mid), 50% (scarcer, bigger gaps, worse blocking), or none (fewer blocks at 20/30 turns but a gap of only 6.5 pp). In lap mode, 10-turn races have a smaller gap (about 5 pp) because the tank is lap-sized.
3. **Misread rule**: keep the live tie/lose rule (needed for the combat targets as fitted), or move to a "random guess" rule. That would need the combat refit redone; average play was too strong in every config I screened.
4. **Combat fit**: A_scarce or A_mid_refill50 hit all three targets for the tuned car. A_mid misses by 0.4 and 1.6 pp. All use TANK_R_EXP 3 (tank grows with r³) and cap 1.05. Is a tank that scales with the stat ratio acceptable?
5. **Street**: still the easiest district (about 64% vs 55–56%) with the weakest retune signal (5.6 pp vs wrong district in A_mid). It needs a district-specific cost-table change, which is outside this sim's knobs. Which direction should it go?
6. **Wrong-district penalty**: A_mid's worst cell is 33.6 pp (down from v1's 40–59). The scarce setups bring back 64–66 pp. Is about 34 acceptable?
7. **Scouting**: pick a style blend between 0.3 (worth 0) and 1.0 (worth 26–31 pp), or reshape the styles. That needs one more run.
8. **Pacing**: reads dominate (read gap 85–89 pp vs live 90), and my rationing rule shows no pacing effect. Do you want a stronger pacing AI built to confirm that pacing really is a non-factor?

## Raw result files not committed

`results_v2.npz` (≈5.6 MB) are not in git, to keep the repo small (all committed npz together would be ≈88 MB). The analysis JSON/tables committed here hold every number quoted above. Rebuild any of them with this folder's `run_*.py` (fixed seeds 20261112–20261120).
