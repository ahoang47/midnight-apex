# resources-v3: all three resources regenerate, overrun allowed, lock with hysteresis (DRAFT, NOT APPROVED)

Barry, 2026-11-13. Code: `resources_v3.py` (model), `screen3.py` + `screen_B.py` (settings screens), `run_v3.py` (full runs), `analyze_v3.py` (writes `analysis_v3.json`). Full runs: 9 batches × 1,000 races (seeds 20261112–20261120), all 15 stand-in laps × 10/20/30 turns × 3 boss styles, the 21-split tune grid (each stat 25–50% in 5 pp steps) plus the exact even spread. Every tune sees the same races. **Clear** means a mean difference of at least 5 pp with the same sign in all 9 batches. Nothing in `sim/` or `design/` was changed, and nothing is committed.

The rules (Austin, 2026-11-13; these replace the whole-race-tank and hard-block versions):
- POW = engine heat, EN = brake/tire heat, HAN = suspension load. **All three cool down / recover every turn.**
- Each stance **adds load** to its resource. Each resource has a **capacity** and a **recovery per turn**. Both scale with that stat's share of the build, so the stat mix sets the recovery rate.
- **A stance is selectable while its bar is not full**, even if playing it pushes the load past capacity. That **overrun** is allowed, but the clash pays less.
- **When a bar is full (load ≥ capacity), that stance is locked.** It stays locked until recovery brings the load under a **release threshold** (hysteresis), not the moment it dips under full.
- No fixed tanks, no race-length scaling, no refills, no card draw. The live misread rule is kept.

## Plain-English summary

- **The combat targets are hit by the tuned car in two of the three candidates (A_mid and B_retune).** In A_mid, perfect play at 80% stats wins **17.2%** (target 10–25), perfect play at 100% wins **100%** (target ≥85), and average play at the 1.05 cap wins **67.2%** (target 60–75). B_retune: 17.0 / 100 / 68.0. C_light (the lighter-load option) misses average play at the cap: **56.7%**.
- **About the log numbers (≈50–52% average at the cap, ≈4–5% perfect at 80%):** those are the mean over **all 22 tunes**, including badly mismatched ones, not the tuned car. The tuned-car numbers above are the ones the targets are judged on. The **even car does miss**: in A_mid it gets 57.7% average at the cap and 4.7% perfect at 80% (both below target). See "What refit would fix the misses".
- **A hidden miss: perfect play at 80% averages 17% only because the race lengths cancel out.** In A_mid it is **46% at 10 turns, 5% at 20 and 0.3% at 30**. κ ×1.5 makes long races much more decisive than short ones. A per-length κ refit is needed (not run).
- **Locks are frequent but short.** On the tuned car (A_mid), some stance is locked in **63% of corners** and the read's counter is locked on **18% of read clashes**. But 91% of locks clear within one corner (mean 0.69 extra corners locked, about 13 locks per race). **50% of corners (18.7% of clashes) are played in overrun**, and an overrun clash pays about **30% less** on average. That works out to **5.6% of all payoff** lost to overrun. The even car locks far less (29% of corners, read counter locked 5.5%).
- **Locks build over the first lap, then level off.** In 30-turn races, A_mid's tuned car has a lock in 57% of lap-1 corners, then 77% in lap 2 and 78% in lap 3. Load carries over until it reaches a steady state.
- **Locks cluster in corner sequences.** The worst back-to-back pairs (A_mid) are ES→DR (92% of the time), ES→HP (87%), DR→ES and HP→DR (84%). N90 corners are the least locked (49%). So tight Touge-style chains are where the gauges bite.
- **Per-corner budgeting is a small factor.** My rationing player beats a greedy player by only **1.2 pp** (A_mid), 0.8 (B_retune) and 0.3 (C_light), and it is clear in 0–1.5% of cells. A stronger rationer (looks 4 corners ahead, 3× the price) gains **+2.5 pp** in A_mid (clear in 24% of cells, up to 11 pp in one cell). In B_retune it is −0.7 pp, worse than greedy. So pacing exists but is a minor skill, and the rule I used does not show it to be worth much.
- **Reads still decide races.** Perfect reads vs random stances on the same tuned car: **88.2 pp** (A_mid), 83.3 (B_retune), 89.1 (C_light), clear in 100% of cells. The live card-draw model was **89.9 pp** (v2 run, same seeds).
- **Retuning matters in A_mid and B_retune, much less in C_light.** Gaps are tuned minus even, and tuned minus the wrong-district tune:
  - A_mid: **+9.6** (clear in 59% of cells) and **+20.1** (81%).
  - B_retune: **+13.5** (73%) and **+26.3** (87%).
  - C_light: **+6.2** (56%) and **+7.1** (60%).
  - The worst wrong-district cell is harsh in A/B: 59.5 pp (A_mid) and 66.8 (B_retune), both on Wangan W3_C1_Outer, 30 turns, conserver boss, where a brake-heavy car wins 13–20% and a suspension-heavy one wins about 80%.
- **The core conflict from v2 is still there, in a milder form.** The candidates that give a real retune meta (A, B) are the ones where the tuned car locks the most (63–72% of corners, 18–23% of read counters). The low-lock candidate (C) has a weak retune meta and misses the average-play target. **Austin has to pick where on that line to sit.**
- **Street:** A_mid and B_retune now give Street similar win rates (tuned 64.7–65.8% vs Touge 65.4–66.9% and Wangan 71.3–71.5%), so it is no longer the easy district there. But it is still the **weakest retune signal**: in A_mid it gains +2.2 pp over even (clear in 4% of cells) and +4.8 over wrong district, vs 12–15 and 18–37 elsewhere. In C_light the order flips: Street is the easiest district (66.1% vs 49.0 and 54.9) and has the strongest retune signal.

## Candidates (all: cap 1.05, live misread rule, share curve exponent 1.5 for capacity and recovery, penalty floor 0.4, release 0.8)

| Name | Capacity (turns of avg load) | Recovery (× avg load per turn) | Capacity & recovery × r^ | κ scale | Penalty curve |
|---|---|---|---|---|---|
| A_mid | 3.0 | 1.0 | r¹ | ×1.5 | linear: 1 − 2·x, floor 0.4 |
| B_retune | 3.0 | 1.0 | r¹ | ×1.5 | quadratic: 1 − 4·x², floor 0.4 |
| C_light | 4.5 | 1.15 | r² | ×1.5 | quadratic: 1 − 4·x², floor 0.4 |

x = how far past capacity the load goes, as a fraction of capacity. "Avg load" = the cross-track average per-turn load of a player who reads 60% of corners (v2 calibration).

How they were picked: `screen_A.json` (81 configs: capacity 2/3/4.5, recovery 0.9/1.0/1.15, r exponent 0/1/2, κ ×1/1.25/1.5, release 0.7, linear penalty) and `screen_B.json` (release 0.6 vs 0.8, linear vs quadratic penalty, steeper share curves, cap 1.10). The screens used N 1,000, seed 7 and track #1 per district only, so they choose settings and are not quoted as results. Screen findings that shaped the choice:
- **Release 0.8 vs 0.6:** at 0.6 locks last about twice as long (mean 1.4–2.6 extra corners vs 0.4–1.3). Read counters are locked more often, and win rates are lower.
- **Quadratic vs linear penalty:** the quadratic curve gives slightly bigger retune gaps.
- **Steeper share curves (exponent 2.5):** a bigger gap at the same recovery, but more locks.
- **Cap 1.10:** pushes average play to 72–79%, but the retune gap falls to about 3 pp.

## Tables (full runs)

### Combat targets (win %)

Targets: perfect at 0.8 = 10–25; perfect at 1.0 ≥ 85; average at cap 1.05 = 60–75. "Tuned" = best of the 21 splits per cell (a small upward selection bias). "Wrong" = the split that is best over the other two districts' laps at the same length and boss style.

| Candidate | Perfect 0.8 tuned | Perfect 0.8 even | Perfect 1.0 tuned | Perfect 1.0 even | Avg cap tuned | Avg cap even | Avg cap wrong |
|---|---|---|---|---|---|---|---|
| A_mid | **17.2** ✓ | 4.7 ✗ | **100.0** ✓ | 99.9 ✓ | **67.2** ✓ | 57.7 ✗ | 47.1 |
| B_retune | **17.0** ✓ | 5.0 ✗ | **100.0** ✓ | 99.9 ✓ | **68.0** ✓ | 54.5 ✗ | 41.7 |
| C_light | **15.4** ✓ | 5.8 ✗ | **100.0** ✓ | 99.9 ✓ | 56.7 ✗ | 50.5 ✗ | 49.6 |

By race length (tuned car), perfect 0.8 / perfect 1.0 / average at cap:

| Candidate | 10 turns | 20 turns | 30 turns |
|---|---|---|---|
| A_mid | 46.3 / 100 / 62.4 | 5.0 / 100 / 68.3 | 0.3 / 100 / 71.0 |
| B_retune | 46.4 / 100 / 63.2 | 4.6 / 100 / 69.2 | 0.2 / 100 / 71.6 |
| C_light | 46.0 / 99.9 / 57.6 | 0.1 / 100 / 57.2 | 0.0 / 100 / 55.2 |

By district, perfect at 0.8 (tuned): A_mid Touge 15.2 / Wangan 19.0 / Street 17.4. Perfect at 1.0 is 100 in every district.

### Overrun and lock metrics (average play at the cap)

"Corners with a lock" = turns where at least one stance was locked at some clash. "Lock duration" = extra corners a stance stays locked after the corner it filled in (0 = free again next corner); a lock still on at the finish counts to the finish. "Read counter locked" = share of correctly-read clashes where the counter stance was locked. "Read counter would overrun" = selectable but over capacity if played.

| Candidate / car | Corners with an overrun clash | Clashes in overrun | Avg penalty per overrun clash | Payoff lost to overrun (all clashes) | Corners with a lock | Locks per race | Lock duration mean (0 / 1 / 2 / 3+ corners) | Longest lock streak, mean / p90 / max (turns) | Read counter locked | Read counter would overrun (played anyway) | Read not played as counter |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_mid tuned | 50.0 | 18.7 | 29.9% | 5.6% | 63.1 | 13.0 | 0.69 (42 / 49 / 8 / 2%) | 8.9 / 13.7 / 30 | 18.0 | 17.4 (15.7) | 19.8 |
| A_mid even | 28.3 | 9.7 | 26.4% | 2.6% | 29.3 | 7.8 | 0.51 | 3.2 / 5.9 / 29 | 5.5 | 7.2 (6.8) | 5.9 |
| A_mid wrong | 40.2 | 14.3 | 27.1% | 3.9% | 43.4 | 10.6 | 0.58 | 4.6 / 7.8 / 30 | 10.7 | 13.0 (10.4) | 13.2 |
| B_retune tuned | 57.3 | 21.6 | 16.5% | 3.6% | 71.9 | 14.3 | 0.76 (38 / 49 / 11 / 2%) | 10.6 / 15.2 / 30 | 22.6 | 19.7 (18.8) | 23.4 |
| B_retune even | 29.4 | 10.1 | 13.0% | 1.3% | 30.6 | 8.0 | 0.52 | 3.4 / 6.2 / 29 | 5.8 | 7.3 (7.2) | 5.9 |
| C_light tuned | 31.8 | 11.1 | 10.7% | 1.2% | 45.9 | 8.6 | 0.94 (24 / 61 / 12 / 3%) | 5.5 / 9.1 / 29 | 12.5 | 9.6 (9.5) | 12.6 |
| C_light even | 2.2 | 0.7 | 8.7% | 0.1% | 3.0 | 0.7 | 0.71 | 0.5 / 1.5 / 14 | 0.5 | 0.1 (0.1) | 0.5 |

Note on "longest lock streak": this counts consecutive corners with *any* stance locked, not the same stance. With locks this short, a long streak means different stances taking turns being locked, not one stance stuck for the whole race.

Limp clashes (all three stances locked) round to 0.0% everywhere. A perfect reader at r 1.0 on A_mid's tuned car still has a lock in 56% of corners and a locked counter on 16.5% of read clashes, and wins 100%.

By race length, tuned car (corners with a lock / read counter locked):
- A_mid: 10 turns 53.4 / 13.7; 20 turns 65.5 / 19.1; 30 turns 70.5 / 21.3.
- B_retune: 66.8 / 20.4; 73.0 / 23.0; 76.0 / 24.2.
- C_light: 30.6 / 7.1; 50.7 / 14.1; 56.6 / 16.3.

By district, tuned car (corners with a lock / read counter locked):
- A_mid: Touge 75.3 / 27.3, Wangan 69.6 / 17.1, Street 44.6 / 9.7.
- B_retune: Touge 80.9 / 31.5, Wangan 80.8 / 23.1, Street 54.1 / 13.1.
- C_light: Touge 47.9 / 16.2, Wangan 51.8 / 11.2, Street 38.2 / 10.1.

Locks by resource (fuel / suspension / brakes), tuned car:
- A_mid: 40 / 31 / 29%.
- B_retune: 37 / 29 / 33%.
- C_light: 35 / 29 / 36%.

### Where locks cluster (tuned car, share of races with a lock at that corner)

| | A_mid | B_retune | C_light |
|---|---|---|---|
| Overall | 66.0 | 73.5 | 50.3 |
| By corner type (high → low) | DR 77, SW 72, HP 71, ES 71, IR 70, CR 65, CH 57, N90 49 | DR 82, SW 82, IR 78, HP 78, ES 76, CR 74, CH 65, N90 55 | SW 58, IR 56, CR 54, ES 54, DR 52, HP 47, N90 42, CH 41 |
| Worst pairs (prev → corner) | ES→DR 92, ES→HP 87, DR→ES 85, HP→DR 84 | ES→HP 94, ES→DR 94, IR→IR 90, HP→DR 90 | N90→SW 73, SW→IR 64, IR→SW 63, ES→HP 61 |
| Lightest pairs | CH→N90 43, ES→N90 44 | ES→N90 49, CH→N90 51 | IR→CH 28, N90→HP 36 |
| By lap, 30-turn races (lap 1 / 2 / 3) | 57 / 77 / 78 | 62 / 83 / 83 | 35 / 67 / 69 |
| By corner position in lap (1st → 10th) | 40 → 73 | 44 → 81 | 32 → 64 |

The rise within lap 1 comes partly from starting cold (load 0, a placeholder) and partly from carry-over.

### Per-corner budgeting: rationing vs greedy (average play at the cap, each player on its own best tune)

| Candidate | Greedy | Rationing (λ 0.6, 3-corner lookahead) | Gap | % cells clear | Largest cell | Strong rationing (λ 2, 4-corner lookahead) | Gap vs greedy | % cells clear (better / worse) | Largest cell | Corners with a lock: greedy / rationing / strong |
|---|---|---|---|---|---|---|---|---|---|---|
| A_mid | 66.0 | 67.2 | **+1.2** | 1.5 | 5.7 | 68.5 | **+2.5** | 23.7 / 0.7 | 11.4 | 64.9 / 63.1 / 50.0 |
| B_retune | 67.2 | 68.0 | **+0.8** | 0.0 | 2.6 | 66.5 | **−0.7** | 0.7 / 6.7 | 11.9 | 72.6 / 71.9 / 54.2 |
| C_light | 56.4 | 56.7 | **+0.3** | 0.0 | 2.0 | 56.4 | **0.0** | 0 / 0 | 4.3 | 45.0 / 45.9 / 35.7 |

Both rationers hold back only on correctly-read turns (a misread follows the live rule). The gap grows with race length (A_mid strong rationer: +2.0 / +2.4 / +3.1 at 10 / 20 / 30 turns). Rationing cuts locks a lot (A_mid: 65% → 50% of corners) but wins only a little more. A better pacing AI could find more; this measures my two rules only.

### Reads vs random (tuned car, average QTE at the cap)

| Model | Perfect reads (q 1) | Random stances, same tune | **Read gap** | % cells clear | Average reads (q 0.6) − random |
|---|---|---|---|---|---|
| A_mid | 99.7 | 11.6 | **88.2** | 100 | 44.5 |
| B_retune | 99.7 | 16.3 | **83.3** | 100 | 43.7 |
| C_light | 99.5 | 10.5 | **89.1** | 100 | 42.1 |
| Live card-draw model (from resources-v2 run, same seeds) | 99.9 | 10.0 | **89.9** | | 57.2 |

The random player picks uniformly among unlocked stances and ignores load. On A_mid it has a lock in 65% of corners.

### Retune gap (average play at the cap)

| Candidate | Tuned − even (pp) | % cells clear | Tuned − wrong district (pp) | % cells clear | Worst wrong-district cell | Best single tune for everything: mean loss vs each cell's best / max / % cells within 2 pp |
|---|---|---|---|---|---|---|
| A_mid | **9.6** | 58.5 | **20.1** | 80.7 | 59.5 (W3_C1_Outer, 30 turns, conserver: P30/H45/E25 wins 79.0, P30/H25/E45 wins 19.5) | P30/H35/E35: 8.5 / 32.5 / 13.3% |
| B_retune | **13.5** | 73.3 | **26.3** | 87.4 | 66.8 (W3_C1_Outer, 30, conserver: P25/H50/E25 79.7 vs P25/H25/E50 12.8) | P25/H35/E40: 11.6 / 29.6 / 0.7% |
| C_light | **6.2** | 56.3 | **7.1** | 60.0 | 21.0 (S1_Shibuya_Grid, 30, conserver: P50/H25/E25 68.1 vs P25/H50/E25 47.0) | P30/H45/E25: 4.0 / 12.2 / 35.6% |

By race length, tuned − even / tuned − wrong:
- A_mid: 10 turns 4.6 / 11.1; 20 turns 10.5 / 21.6; 30 turns 13.6 / 27.6.
- B_retune: 7.1 / 14.6; 14.7 / 30.3; 18.8 / 34.0.
- C_light: 2.8 / 2.8; 6.7 / 7.2; 9.1 / 11.3.

### By district (average play at the cap)

| Candidate | District | Tuned win | Even win | Tuned − even (clear %) | Tuned − wrong (clear %) | Worst wrong cell | Avg tuned split (POW/fuel, HAN/susp, EN/brakes) |
|---|---|---|---|---|---|---|---|
| A_mid | Touge | 65.4 | 50.8 | 14.6 (84) | 18.1 (91) | 35.4 | 0.26 / 0.25 / 0.48 |
| A_mid | Wangan | 71.5 | 59.6 | 11.9 (87) | 37.4 (100) | 59.5 | 0.27 / 0.45 / 0.28 |
| A_mid | **Street** | 64.7 | 62.5 | **2.2 (4)** | **4.8 (51)** | 8.5 | 0.37 / 0.32 / 0.31 |
| B_retune | Touge | 66.9 | 46.6 | 20.3 (100) | 28.1 (100) | 51.4 | 0.25 / 0.25 / 0.50 |
| B_retune | Wangan | 71.3 | 54.2 | 17.1 (100) | 44.9 (100) | 66.8 | 0.26 / 0.49 / 0.25 |
| B_retune | **Street** | 65.8 | 62.6 | **3.2 (20)** | **5.9 (62)** | 10.9 | 0.39 / 0.31 / 0.30 |
| C_light | Touge | 49.0 | 44.7 | 4.4 (40) | 4.7 (47) | 12.2 | 0.26 / 0.28 / 0.46 |
| C_light | Wangan | 54.9 | 46.9 | 8.0 (64) | 8.8 (69) | 19.6 | 0.25 / 0.48 / 0.27 |
| C_light | **Street** | 66.1 | 59.8 | 6.3 (64) | 7.9 (64) | 21.0 | 0.45 / 0.30 / 0.25 |

As in v1/v2, the tuned splits follow what you counter, not the corner names. Touge wants brakes (EN), Wangan wants suspension (HAN), and Street leans fuel (POW). Touge and Wangan tunes sit at the 25–50% grid edge, so a wider stat range would make their gaps bigger.

## What refit would fix the misses

1. **Average play at the cap ≈50–52% and perfect at 80% ≈4–5% in the log.** These are averages over all 22 tunes, not a miss for the tuned car. A_mid and B_retune hit all three targets on the tuned car. If Austin wants the targets to hold **for an untuned (even) car** too:
   - The screen point capacity 4.5 / recovery 0.9 / r¹ / κ ×1.5 / release 0.8 / linear penalty came close on track #1 (screen only). It gave even 14.2 / 99.6 / 59.5 and tuned 20.1 / 67.9, with gaps 8.4 / 19.4 pp and locks in 52% of corners.
   - The levers are: a little more capacity, slightly lower recovery, and the cap κ kept at ×1.5. That needs a full run before it can be quoted.
2. **C_light's average at the cap (56.7%) is below target.** Its higher recovery and r² scaling make the boss and player both run clean, so outcomes drift toward 50/50. In screens, moving the cap to 1.10 lifts average play to 72–79%, but the retune gap collapses to about 3 pp. The alternative is a lower recovery (≈1.0), which moves C toward A_mid.
3. **Perfect at 80% depends heavily on race length** (≈46% / 5% / 0% at 10 / 20 / 30 turns in every candidate). The fix is a separate κ per length: flatter for 30 turns, steeper for 10, instead of one ×1.5 scale on KAPPA_BY_LENGTH. Not run yet. This would also lift the 30-turn average slightly and lower the 10-turn one.
4. **Street's weak retune signal (A/B).** Street's corner mix (N90/CH-heavy) loads all three resources almost evenly, so no tune stands out there. Fixing it needs a Street-specific cost-table change (for example heavier brake load at N90), which is outside this sim's knobs.

## Placeholders and assumptions (all need Austin's sign-off)

1. **Capacity** = CAP_TURNS × average per-turn load × share curve 3·s^1.5/Σs^1.5 × r^CAP_R_EXP. **Recovery** = REC_FACTOR × the same base × the same share curve × r^REC_R_EXP. The three share multipliers always sum to 3, so specialising moves capacity and recovery between resources without adding any. The same rule applies to all three resources.
2. **Overrun penalty**: x = (load − capacity) / capacity after the stance is added. Linear 1 − 2x or quadratic 1 − 4x², floor 0.4. It cuts only that side's own clash payoff.
3. **Lock**: at load ≥ capacity (checked after every clash and after passive load). **Release** when load < 0.8 × capacity after recovery (0.6 and 0.7 were screened).
4. **All three locked** → "limp": play the least-loaded stance at 0.4× payoff (never happened to a measurable degree).
5. **Cold start**: load 0 at the green flag.
6. **Passive corner load** (v1 table) is added every turn, before recovery.
7. **κ** = live KAPPA_BY_LENGTH × 1.5 (the screen covered 1.0–1.5). The cap stays at 1.05.
8. **Boss**: even stats, QTE 1.0, plays its planned line if the stance is unlocked, otherwise the unlocked stance with the lowest load share. It does not ration. Boss style blend 0.3 (v2).
9. **Player AI**: on a read turn it picks the stance with the best immediate value, including the overrun penalty it can see on its gauge. Rationing subtracts λ × cost × shortfall over a 3-corner lookahead (the track is known). On a misread it follows the live rule (tie w.p. q_read, else the losing stance), or a random unlocked stance if that one is locked.
10. **Corner costs, the repeat surcharge (+25% per repeat), track normalisation and the 60%-read calibration player** all carry over from v1/v2.
11. **Tune grid** 25–50% per stat; average QTE = live raw_qte_score; perfect = q_read 1, QTE 1.

## Decisions needed from Austin

1. **Where to sit on the lock vs retune line.**
   - B_retune: biggest retune meta (+13.5 / +26.3 pp), but a lock in 72% of corners and the read counter locked 23% of the time.
   - A_mid: middle ground (+9.6 / +20.1; locks in 63% of corners, 18% of read counters).
   - C_light: locks in 46% of corners and 12.5% of read counters, but the retune meta is weak (+6.2 / +7.1) and average play misses the target.
2. **Release threshold (hysteresis)**: 0.8 gives short locks (mostly cleared after one corner). 0.6 roughly doubles lock length. How long should a lock feel?
3. **Penalty curve**: linear (an overrun clash loses about 30% in A_mid) or quadratic (gentle small overruns, about 11–17% average loss). Floor 0.4 or something else?
4. **Combat targets for which car**: tuned only (A/B pass now), or the even car too (needs the capacity 4.5 / recovery 0.9 refit to be run)?
5. **Per-length κ**: approve refitting κ separately for 10/20/30 turns so perfect at 80% lands in 10–25 at every length, not just on average.
6. **Wrong-district penalty**: the worst cell is 59.5 pp (A_mid) or 66.8 (B_retune), on Wangan C1 Outer. Is that acceptable for a badly mistuned car?
7. **Street**: approve a Street cost-table change so Street asks for a distinct resource (currently its retune gap is only 2–3 pp over even in A/B).
8. **Cold start and boss behaviour**: should cars start the race at zero load, and should bosses manage their gauges (ration) instead of only falling back when locked? These touch boss character design, so Desmond and Nathaniel should be involved.
9. **Pacing**: budgeting is worth about 1–2.5 pp with my rationing rules. Is that the intended weight, or should resources pull harder?

## Raw result files not committed

`results_v3_A_mid.npz`, `results_v3_B_retune.npz`, `results_v3_C_light.npz` (≈7–8 MB each) are not in git, to keep the repo small (all committed npz together would be ≈88 MB). The analysis JSON/tables committed here hold every number quoted above. Rebuild any of them with this folder's `run_*.py` (fixed seeds 20261112–20261120).
