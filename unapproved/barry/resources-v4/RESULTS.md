# resources-v4: higher heat stakes, a pacing player, kappa per race length (DRAFT, NOT APPROVED)

Barry, 2026-11-13. Brief (Austin, approved to try): make in-race heat management about as valuable as line reads; leave 10-turn (grind) races easy on purpose; tune the 80% target on 20/30-turn races only.

Code: `resources_v4.py` (model; copied from `resources-v3/resources_v3.py`, which is unchanged), `run_v4.py` (full runs), `analyze_v4.py` (writes `analysis_v4.json`). Screens: `screen_stakes*.py`, `screen3.py`, `screen4.py`, `kfit.py` + `kfit_all.sh` (M1-M3), `fix_screen.py`, `kfit_fix.sh` (F1/F2/F8). Screens use small N and a single seed, so they only pick settings and are never quoted as results. Full runs: 9 batches × 1,000 races (seeds 20261112-20261120), all 15 stand-in laps × 10/20/30 turns × 3 boss styles, the 21-split tune grid plus the exact even spread, with common random numbers across tunes. **Clear** = mean difference ≥ 5 pp, same sign in all 9 batches. Nothing in `sim/` or `design/` was touched. Nothing is committed.

## What changed in the model (all PLACEHOLDER, all need Austin)

- **Heat stakes:** player recovery 1.0 × average load per turn (as v3), **release 0.3** (v3 0.8), so a lock lasts until the bar cools to 30%. **Aggressive-line surcharge AGG_STEP 1.0** (v3 0.25): the k-th repeat of a stance in one line costs 1 + 1.0·(k−1), so PPP costs 1+2+3. Overrun penalty is linear with floor 0.4: slope 2 (F2) or 4 (F1).
- **Boss heat is held at v3 rules** (recovery 1.0, release 0.8, capacity 3). When the boss shared the harsher player gauge (screen 3), it overheated so much that a no-read player won about 95%. **Story flag (Desmond/Nathaniel):** how bosses run their gauges is an identity question.
- **Kappa per race length** (multiplier on live κ 1.55/1.35/1.20): 10 turns ×1.5 (left at v3, not tuned), 20 turns ×2.1 (F2) / ×2.2 (F1), 30 turns ×1.85 (F2) / ×1.9 (F1).
- **Cap 1.10** (v3 1.05). At 1.05, average play at 20/30 turns could not get above roughly 45% with any κ that kept perfect-at-80% in range (`kfit_M*.json`, `fix_screen.json`).
- **Pacing players:**
  - *greedy*: picks the best stance on immediate value (it sees the overrun penalty on its gauge).
  - *best pacing* = "reserve" rule: soft ceiling at 70% of the bar. Price above it = 2 × the win-vs-tie edge per unit over. The ceiling drops by 0.5 × (planned load over the next 3 real corners − recovery) / capacity, so it holds back before heavy upcoming corners.
  - *average* = best pacing on 60% of turns and greedy on the rest. This mirrors read 0.6, but it is **my assumption**.
  - I also built a full forecast planner (`pacing="plan"`: it simulates the gauges 3-5 corners ahead and prices expected locked/overrun clashes). In screens 1-2 it did no better than greedy or the simple rationer, and the reserve rule beat it, so the reserve rule is the "best pacing" player. A stronger AI could find more.
- **"No reads, same pacing" player:** guesses each boss stance uniformly at random and plays its counter with the chosen pacing (`mode="randguess"`).
- NaN per-district bug (v3 `q8080.py`): the loop unpacked `((district, name), lap)` as `(dd, _)`, so `dd` was a tuple and never equal to "street", and the mean was taken over an empty set. `analyze_v4.py` selects by district name. All district numbers below are real.

## Candidates

| | F2_gentle (recommended) | F1_steep |
|---|---|---|
| Player recovery / capacity | 1.0 / 3 turns of avg load, both × r¹ | same |
| Release (hysteresis) | 0.3 | 0.3 |
| Repeat surcharge AGG_STEP | 1.0 | 1.0 |
| Overrun penalty | linear 1 − 2x, floor 0.4 | linear 1 − 4x, floor 0.4 |
| κ multiplier 10/20/30 | 1.5 / 2.1 / 1.85 (κ 2.33 / 2.84 / 2.22) | 1.5 / 2.2 / 1.9 (κ 2.33 / 2.97 / 2.28) |
| Cap | 1.10 | 1.10 |
| Boss gauge | v3 rules | v3 rules |

## Win rates (full runs, tuned = best of 21 splits per cell)

Targets: perfect at 0.8 = 10-25 on 20/30 turns; perfect at 1.0 ≥ 85; average (read 0.6, QTE 0.6 raw at the cap, average pacing) at the cap = 60-75.

| | F2 tuned | F2 even | F1 tuned | F1 even |
|---|---|---|---|---|
| Perfect 0.8: 10 / 20 / 30 turns | 74.5 / **22.1** ✓ / **17.4** ✓ | 47.1 / 11.1 / 12.3 | 78.1 / **19.0** ✓ / **18.6** ✓ | 48.8 / 10.3 / 12.5 |
| Perfect 1.0 (all lengths) | **100.0** ✓ | 100.0 | **100.0** ✓ | 100.0 |
| Average 60/60 at cap: all | **75.0** (edge) | 68.0 | **77.3** ✗ | 70.3 |
| Average at cap: 10 / 20 / 30 | 74.9 / **79.5** ✗ / 70.7 ✓ | 71.6 / 72.3 / 60.3 | 75.7 / **82.2** ✗ / 74.0 ✓ | 72.5 / 75.0 / 63.6 |
| 80/80 at cap (pacing on 80% of turns) | 99.1 (98.8 / 99.2 / 99.2) | 97.1 | 99.2 (98.9 / 99.4 / 99.3) | 97.4 |
| Average at cap, wrong-district tune | 66.8 | | 67.8 | |

By district, average at the cap (tuned): F2 Touge 69.9 / Wangan 81.2 / Street 73.9. F1: 72.7 / 83.3 / 75.7. Perfect at 0.8 by district is pulled up by the easy 10-turn races: F2 30.8 / 28.0 / 55.2.

## Skill split (average QTE at the cap)

| | F2 | F1 |
|---|---|---|
| **Reads, best pacing:** perfect read − random guess (same tune) | **22.6 pp** (100% clear; 10/20/30: 37.1 / 13.8 / 16.9) | **19.0** (86.7%; 35.5 / 9.5 / 12.0) |
| Reads, greedy: perfect − random | 71.5 (100%) | 69.7 (100%) |
| Reads, read 1.0 vs 0.6 (best pacing) | 18.2 (100%) | 16.2 (100%) |
| **Pacing at read 0.6:** best − greedy | **15.5 pp** (80% clear; 8.8 / 14.7 / 22.9) | **15.0** (80%; 9.2 / 13.8 / 22.1) |
| Pacing at read 1.0: best − greedy | 0.1 | 0.0 |
| Average pacing (60%) − greedy, read 0.6 | 8.6 (53%) | 8.5 (55%) |
| **Pacing ÷ reads** (brief's metric) | **0.69** | **0.79** |
| Random guess + best pacing wins | 77.4 | 81.0 |
| Random guess + greedy wins | 28.4 | 30.2 |

Read this table carefully. The brief's ratio is met, but **partly because reads lost value, not only because pacing gained it**. A no-read player who paces perfectly wins 77% at the cap, so the two skills **substitute for each other rather than add**. A perfect reader gains nothing from pacing (0.1 pp), and a perfect pacer gains only 14-17 pp from reads at 20/30 turns. Measured from the average player, the two upgrades are about even: perfect reads +18 pp, perfect pacing +15.5 pp. Pacing grows with race length (+9 pp at 10 turns, +23 pp at 30), so long races are where heat management bites. v3 for comparison: reads 83-89 pp, pacing 1-2.5 pp.

## Retune gaps (average play at the cap)

| | F2 | F1 | v3 B_retune |
|---|---|---|---|
| Tuned − even | 7.0 (52.6% clear; 10/20/30: 3.3 / 7.2 / 10.4) | 6.9 (53.3%) | 13.5 |
| Tuned − wrong district | 8.2 (59.3%; 4.0 / 8.5 / 12.1) | 9.5 (57.0%) | 26.3 |
| Worst wrong-district cell | 29.1 (T1_Akina_Switchbacks, 30 turns, hot_early: P45/H30/E25 70.2 vs P30/H30/E40 41.1) | 35.4 (W4_Tatsumi_Sprint 30, hot_early) | 66.8 |
| By district, tuned − even / − wrong | Touge 7.0 / 13.5, Wangan 13.0 / 10.0, **Street 0.9 / 1.0** | Touge 7.2 / 14.1, Wangan 12.5 / 13.3, Street 1.0 / 1.0 | |

Tuning still matters on Touge and Wangan, but the gaps are about half of v3's. Street has no retune meta at all: the tuned split averages about even (0.34 / 0.32 / 0.34). The even car now meets the average target too (68.0), which is another sign the retune meta got weaker.

## Feel (F2, average player at the cap, tuned car; F1 within 0.5 pp)

| | Average | Best pacing | Greedy | Even car (avg) | Perfect at 1.0 | v3 B_retune |
|---|---|---|---|---|---|---|
| Corners with some stance locked | 51.9% | 40.1 | 64.0 | 45.1 | 6.0 | 71.9 |
| Mean lock length (extra corners after the lock corner) | 3.26 | 3.18 | 3.49 | 3.70 | | 0.76 |
| Lock length 0 / 1 / 2 / 3 / 4+ corners | 5 / 6 / 36 / 21 / 32% | | | | | 38 / 49 / 11 / 2+ |
| Locks per race | 4.7 | 3.6 | 6.1 | 4.5 | | 14.3 |
| Read's counter locked (share of read clashes) | 19.8% | 14.8 | 26.9 | 22.9 | 2.1 | 22.6 |
| Clashes played in overrun | 7.3% | 5.4 | 9.2 | 6.5 | 0.2 | 21.6 |
| Corners with an overrun clash | 21.8% | 16.2 | 27.7 | 19.6 | 0.5 | 57.3 |
| Limp clashes (all three locked, 0.4 payoff) | 7.3% | 5.2 | 10.9 | 11.6 | 0.4 | ~0 |
| Payoff lost to overrun + limp (all clashes) | 7.2% | 5.2 | 10.2 | 9.5 | | 3.6 |

So the gauges now bite less often but harder: about 5 locks a race instead of 14, each lasting about 3 corners instead of under 1. Lock time builds by lap in 30-turn races: 43 / 65 / 69% of corners (greedy 55 / 81 / 84). By length (average): locked corners 43 / 54 / 59%, read counter locked 16 / 20 / 24%, lock length 2.3 / 3.2 / 3.6. By district (average): Touge 52%, Wangan 61%, Street 43% of corners locked. Locks by bar: engine 32%, suspension 40%, brakes 28%. Limping (all three locked) is new in v4 at about 7% of clashes. Austin should look at it on feel; it is the "car is cooked" state.

## Targets hit / missed

- ✓ Perfect at 80%, 20 and 30 turns: F2 22.1 / 17.4, F1 19.0 / 18.6.
- ✓ 10-turn races easy: perfect at 80% wins 75-78%; average at the cap wins 75%.
- ✓ Perfect at 100% ≥ 85: 100.
- ✗/edge: **Average 60/60 at the cap.** F2 is 75.0 overall (top edge) but **79.5 at 20 turns**. F1 is 77.3 overall and 82.2 at 20. The cause: at 20 turns, the κ that brings perfect-at-80% down into 10-25 also pushes the cap player up. In `kfit_fix.log` at 20 turns, no κ in 1.25-2.0 gives both (F2 at κ ×2.0: 28.6 / 79.1). Cap 1.05 is too low and 1.10 too high for 20 turns; somewhere around 1.07-1.08 would likely fit, but I didn't run it because it isn't an allowed cap value.
- ~ Pacing vs reads: the ratio is 0.69-0.79 (target 1/3-1/2+), but see the substitution caveat. A perfect reader gets no value from pacing.
- ✗ Retune meta weaker than v3 (tuned − even about 7 pp vs 13.5), and Street still has none.
- 80/80 at the cap ≈ 99% (v3 also ≈ 99%).

## Open questions for Austin (one at a time)

1. Is substitution OK (great pacing can stand in for reads), or should reads stay the core? If reads should stay the core, the next step is to cap how much pacing can rescue a misread, e.g. no reserve pricing on unread turns.
2. Average player definition: pacing on 60% of turns (my assumption).
3. Boss gauges held at v3 rules (story; Desmond/Nathaniel).
4. Cap: 1.10 fits 30 turns; 20 turns would want about 1.07-1.08 or a different κ/heat mix.

---

# v4b: restoring the retune meta (DRAFT, NOT APPROVED)

Barry, 2026-11-13. Austin: fix the weaker retune meta first, and leave the pacing-vs-reads question as it is. Starts from F2_gentle. Files are in `retune/`:
- `resources_v4b.py`: a copy of `resources_v4.py`, which is unchanged.
- `screen_r1.py` → `screen_r1.jsonl`.
- `kfit_b.py` / `kfit_b.sh` → `kfit_b_*.json`, `kfit_b.log`.
- `run_v4b.py` → `results_v4b_*.npz`, `results_v4b_meta.json`.
- `analyze_v4b.py` → `analysis_v4b.json`.

Same full-run method as v4: 9 × 1,000, seeds 20261112-20261120, 15 laps × 10/20/30 × 3 styles, 21 splits plus even.

## New levers in resources_v4b.py (PLACEHOLDER)

- **STAT_M_W:** the player's clash payoff × (1 + STAT_M_W × (share of the stance played − 1/3)). This is the live model's M idea, applied to all three stats; the live M uses 0.5 on the POW/EN share only. The boss is even, so it gets ×1.
- **DIST_SIG:** a per-district load signature (Street brakes, Touge suspension, Wangan engine). It was screened but **not used**: it raised the retune gaps but dropped pacing to 2-10 pp.
- **DEMAND_SLANT** (already in v2; 1 = raw mix): 2 doubles each track's deviation from an even load mix. v4b also fixes a cache: capacity calibration now follows DEMAND_SLANT and DIST_SIG. Results at the old settings are byte-identical.

## What the screen showed (`screen_r1.jsonl`; 36 configs, N 300, seed 7, cap 1.10)

| Lever | Retune gaps | Pacing gap | Street |
|---|---|---|---|
| Steeper share curve (exponent 2.5-3.5) | No better on its own | Down | Gap stays ~0-5 |
| Per-district signature | Up | Collapses (2-10 pp) | |
| M weight | Up | Down a little | Moves only modestly on its own |
| **DEMAND_SLANT 2 + M weight** | Up | Mostly kept | ~12-16 |

The last row is the best trade. Higher M also lifts the tuned car's win rate, so cap and κ were refit: `kfit_b.log`, all 15 laps, caps 1.07 / 1.08 / 1.10.

## Candidates (both = F2_gentle + the changes below)

F2_gentle carries over unchanged: release 0.3, repeat surcharge 1.0, overrun linear slope 2 with floor 0.4, capacity 3 / recovery 1.0 × r¹, share-curve exponent 1.5, boss at v3 heat rules, reserve-rule pacing (ceiling 0.7, price 2, lookahead 0.5 over 3 corners), average player = pacing on 60% of turns.

| | **G2_slant_m10 (recommended)** | G1_slant_m05 |
|---|---|---|
| DEMAND_SLANT | 2.0 | 2.0 |
| STAT_M_W | 1.0 | 0.5 |
| κ multiplier 10 / 20 / 30 | 1.75 / 2.25 / 2.25 (κ 2.71 / 3.04 / 2.70) | same |
| Cap | **1.07** | 1.08 |

## Win rates (full runs, tuned car; even car in brackets)

| | G2: 10 / 20 / 30 turns | G2 all | G1: 10 / 20 / 30 | G1 all |
|---|---|---|---|---|
| Perfect at 80% (target 10-25 at 20/30) | 55.6 / **14.9 ✓** / **20.9 ✓** [32.9 / 9.8 / 14.2] | 30.5 | 53.0 / **14.4 ✓** / **19.9 ✓** | 29.1 |
| Perfect at 100% (≥ 85) | 100 / 100 / 100 | **100 ✓** | 100 | **100 ✓** |
| 60/60 at the cap (60-75) | 71.9 / **69.4 ✓** / **63.9 ✓** [63.1 / 56.1 / 45.5] | **68.4 ✓** [54.9] | 73.7 / 72.4 ✓ / 67.0 ✓ [67.9 / 63.2 / 53.6] | **71.0 ✓** [61.6] |
| 80/80 at the cap | 98.4 / 97.7 / 97.9 | 98.0 [94.1] | 98.6 / 98.2 / 98.3 | 98.3 [95.7] |
| 60/60, wrong-district tune | | 41.8 | | 49.7 |

- **10-turn grind races are the easiest for the average player** (71.9 vs 69.4 / 63.9), and perfect at 80% wins 56% there.
- **By district** (G2, average at the cap, tuned): Touge 55.8, Wangan 73.3, Street 76.1. Touge is the hardest district; at 30 turns it is the low cell.
- **Perfect at 80% by district:** 14.7 / 24.6 / 52.1. Street's number is high because of the 10-turn races.

## Retune gaps (average play at the cap)

| | G2 | G1 | v4 F2 | v3 B_retune |
|---|---|---|---|---|
| **Tuned − even** | **13.5** (93.3% of cells clear; 10/20/30: 8.9 / 13.3 / 18.4) | 9.5 (74.8%) | 7.0 | 13.5 |
| **Tuned − wrong district** | **26.7** (100% clear; 15.1 / 28.5 / 36.3) | 21.3 (92.6%) | 8.2 | 26.3 |
| **Street:** − even / − wrong | **13.5 / 28.1** (86.7% / 100% clear) | 8.3 / 18.6 | 0.9 / 1.0 | 2.2 / 4.8 (v3 A_mid) |
| Touge: − even / − wrong | 12.0 / 16.3 (93% / 100%) | 7.4 / 12.9 | 7.0 / 13.5 | |
| Wangan: − even / − wrong | 15.1 / 35.5 (100% / 100%) | 12.7 / 32.4 | 13.0 / 10.0 | |
| Worst wrong-district cell | 60.6 (S5_Harbor_Warehouses, 30 turns, conserver: P50/H25/E25 91.3 vs P25/H25/E50 30.7) | 59.8 (W1_Bayshore_Run 30, hot_early) | 29.1 | 66.8 |

Average tuned splits (POW / HAN / EN), G2: Street 0.47 / 0.27 / 0.26 (engine-heavy), Touge 0.32 / 0.26 / 0.43 (brake-heavy), Wangan 0.26 / 0.35 / 0.40. **Flag for Desmond/Arthur:** Street now wants an engine-heavy car and Touge a brake-heavy one. Check this against story and art expectations before anyone treats it as canon.

## Skill split (average QTE at the cap)

| | G2 | G1 |
|---|---|---|
| Reads, best pacing: perfect read − random guess | 28.8 (99.3% clear; 10/20/30: 46.5 / 21.5 / 18.5) | 27.0 (97.8%) |
| Reads, greedy pacing: perfect − random | 75.1 | 75.8 |
| Reads 1.0 vs 0.6 (best pacing) | 22.4 | 19.9 |
| Pacing at read 0.6: best − greedy | 15.3 (70.4% clear; 8.3 / 16.8 / 20.9) | 15.1 (71.1%) |
| Pacing at read 1.0 | 0.8 | 0.2 |
| Average pacing − greedy | 6.1 | 6.1 |
| **Pacing ÷ reads** | **0.53 ✓** (v4 F2: 0.69) | 0.56 ✓ |
| Random guess + best pacing / + greedy wins | 71.2 / 24.1 | 73.0 / 24.0 |

The substitution caveat from v4 still holds, a little weaker: a no-read player with perfect pacing wins 71% (F2: 77%), and a perfect reader still gains about nothing from pacing.

## Feel (G2, average player at the cap, tuned car)

| | Average | Best pacing | Greedy | Even car | Perfect at 1.0 | v4 F2 avg |
|---|---|---|---|---|---|---|
| Corners with some stance locked | 66.6% | 51.0 | 74.3 | 50.8 | 0.1 | 51.9 |
| Mean lock length (extra corners) | 3.76 | 3.62 | 3.75 | 3.86 | | 3.26 |
| Lock length 0 / 1 / 2 / 3 / 4+ corners | 5 / 6 / 26 / 22 / 42% | | | | | 5 / 6 / 36 / 21 / 32 |
| Locks per race | 5.6 | 4.1 | 6.6 | 5.0 | | 4.7 |
| Read's counter locked | 30.1% | 20.1 | 34.6 | 27.4 | 0.0 | 19.8 |
| Clashes in overrun (corners with one) | 8.8% (26.4) | 6.2 (18.6) | 10.5 (31.4) | 7.3 (21.8) | 0 | 7.3 (21.8) |
| Limp clashes (all three locked) | 10.3% | 6.4 | 12.2 | 14.5 | 0 | 7.3 |
| Payoff lost to overrun + limp | 10.0% | 6.6 | 11.8 | 11.4 | 0 | 7.2 |

- **By race length** (average player): locked corners 58 / 68 / 73%, read counter locked 24 / 31 / 36%, lock length 2.6 / 3.7 / 4.2 corners.
- **30-turn races by lap:** 59 / 80 / 81% of corners locked.
- **By district:** Touge 68%, Wangan 68%, Street 64% of corners locked.
- **Locks by bar:** engine 28%, suspension 40%, brakes 32%.
- **Cost of the retune fix:** the tuned car now runs hotter (the M bonus pushes it to lean on its strong stances). The average player has a lock in 2 of 3 corners and the read's counter locked 30% of the time (v4 F2: 52% / 20%). G1 is a bit lighter: 63.0% / 27.0%, limp 8.8%.

## Targets: G2 hits all of them; feel is the open issue

- ✓ Perfect at 80%, 20/30 turns: 14.9 / 20.9. ✓ Perfect at 100%: 100. ✓ 60/60 at the cap (1.07): 68.4 overall (69.4 / 63.9 at 20/30). ✓ 10-turn races easiest: 71.9, with perfect at 80% at 55.6.
- ✓ Tuned − even 13.5 (93% of cells clear). ✓ Tuned − wrong district 26.7 (100% clear). ✓ Street 13.5 / 28.1.
- ✓ Pacing ÷ reads 0.53.
- **Feel not yet approved:**
  - Locks are heavier than v4: 67% of corners for the average player, read counter locked 30%, limp 10% of clashes. G1 is the lighter option but misses tuned − even (9.5, target ~12).
  - STAT_M_W 1.0 is double the live M weight (0.5) and applies to all three stats (live: POW/EN only, plus HAN through q_eff). That counts as a stat-formula change, so it needs Austin's approval.
  - Cap 1.07 is a new cap value.

## Raw result files not committed

`results_v4_F1_steep.npz`, `results_v4_F2_gentle.npz` and `retune/results_v4b_G1_slant_m05.npz` (≈15 MB each). Only `retune/results_v4b_G2_slant_m10.npz` (the approved candidate) is committed are not in git, to keep the repo small (all committed npz together would be ≈88 MB). The analysis JSON/tables committed here hold every number quoted above. Rebuild any of them with this folder's `run_*.py` (fixed seeds 20261112–20261120).

## G2 made live in sim/ (2026-11-13, after Austin's approval)

Austin approved G2_slant_m10 ("I'm happy with this new resource system"). It is now the live engine: `sim/velocity_shift/equations.py` (heat section) + `heat.py`, `match.py`, `simulation.py`; the card draw is deleted. `retune/live_spotcheck.py` races the live sim with G2's own tuned split per cell (track × length × boss style), 300 races per cell, and compares to the G2 full runs (`retune/live_spotcheck.json`):

| Measure | Live | G2 full runs |
|---|---|---|
| 60/60 at the cap 1.07, all / 10 / 20 / 30 turns | 68.6 / 72.3 / 69.3 / 64.4 | 68.4 / 71.9 / 69.4 / 63.9 |
| 60/60 at the cap by district (Touge / Wangan / Street) | 56.0 / 74.2 / 75.7 | 55.8 / 73.3 / 76.1 |
| Perfect at 80 %, 10 / 20 / 30 turns | 55.6 / 14.7 / 21.2 | 55.6 / 14.9 / 20.9 |
| Perfect at 100 % | 100 | 100 |
| 80/80 at the cap | 98.0 | 98.0 |

- One rule detail had to match the study exactly: the boss's gauges lock only when it plays into them, not from passive corner load (`BOSS_HEAT_LOCK_ON_PASSIVE = False`). With passive locking on for the boss too, Wangan came out about 1.7 pp easier.
- `retune/export_tuned.py` writes `sim/config/heat_g2_tuned.json` (the per-cell G2 tuned splits), which `sim/scripts/balance_gauntlet.py` uses in CI.
- **Caveat for Austin/Desmond:** the targets assume a car retuned per track, race length and boss style. One fixed split per district (best on average) gives the average player at the cap: Street 74 / 77 / 73, Touge 58 / 52 / 40, Wangan 66 / 71 / 68 (10 / 20 / 30 turns). So Touge misses 60–75 unless the player retunes per track.
- **Tuned split vs heat demand:** Street's load mix is brake-heavy but its best car is engine-heavy (POW 0.47); Touge's load mix is engine-heavy but its best car is brake-heavy (EN 0.43). This comes from STAT_M_W and the counter stances, not from gauge size. Worth a sanity check before the splits become canon.
