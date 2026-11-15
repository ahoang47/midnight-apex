# Hard retune limit: study (draft, Barry, 2026-11-14)

> **Approved (Austin 2026-11-14): B = 20 %, live in sim/. See DECISION.md.**

Austin ("sounds good.") approved whole skill points at 10x resolution (S3: 19 to 48 points per level) and a **hard retune limit**, with no full respec.
This is a draft only. sim/ was not changed and nothing was committed.

## Model tested
- **Points.** Points = round(10·SP(L)) (the S3 table). Allocation is integer POW/HAN/EN. Each stat is kept at 25–50% of the total, and this is enforced.
- **Start.** L0 starts on the Street tune exactly: 1200/600/600.
- **New points.** Newly earned points are free. The policy is greedy: fill band floors first, then the largest deficit against the current district tune, never going above 50%.
- **Tunes (POW/HAN/EN).** Street 50/25/25, Wangan 25/25/50, Touge 45/25/30.
- **District changes.** At each change (R1→R2, R2→R3, before P1, M11, M21, M31) the player may move at most floor(B × already-spent points), from surplus stats to deficit stats. No other retuning is allowed.
- **Win % at an off-tune split.** Win % = live table(r) + [sweep(p) − sweep(p_tune)], where p is the POW share. HAN is always 25%, so EN = 75 − p. The sweep is `retune_sweep.py`, run with common random numbers across p.
  - rt1: all 15 tracks, 10/20/30 turns, p 25..50 in steps of 5, r 0.97..1.18, 4 profiles, 3 styles, N = 150 per style (25,920 jobs, 20 min).
  - Bilinear interpolation in r and p.
- **Walkers.** The campaign uses the live `_walk_round` round by round, with the split hooked per level. The arc and finale use the draft econ-v1 walker with the live table patched in (the `_WR` cache is bypassed).
- **Sanity check.** B = 100% reproduces the S3 baseline exactly: bosses 53.0/57.7/55.8 (52.9 before integer rounding of the L6 split), mixed 3+10/3+10/4+8, 60/60 13/15/18, finale 81.7/82.7/79.3/81.7.

## Achieved POW share (HAN 25%, EN = remainder)
R1 is always the Street tune (50%). R3 is always back to 45% by the boss.

| B | R2 entry (mixed / story) | R2 boss | R3 entry | Arc F1 (Touge) | Arc F2 Wangan: entry→billed | Arc F3 Street: entry→billed | Arc F4 (Touge) |
|---|---|---|---|---|---|---|---|
| 100% | 25.0 / 25.0 | 25.0 | 45.0 | 45 | 25.0→25.0 | 50.0→50.0 | 45 |
| 20% | 30.0 / 28.8 | 26.2 | 45.0 | 45 | 25.0→25.0 | 45.0→48.4 | 45 |
| 15% | 35.0 / 33.6 | 30.6 | 45.0 | 45 | 30.0→26.6 | 41.6→45.4 | 45 |
| 10% | 40.0 / 38.4 | 34.9 | 44.9 | 45 | 35.0→31.1 | 41.0→44.9 | 45 |
| 5% | 45.0 / 43.2 | 39.3 | 44.3 | 45 | 40.0→35.5 | 40.5→44.4 | 45 |
| 0% | 50.0 / 48.0 | 43.7 | 43.7 | 45 | 45.0→39.9 | 39.9→43.9 | 43.9→45 |

## Results (rt1 sweep)
| B | Story bosses 80/80 | Story min race | Mixed (wall+post) | 60/60 grinds | At-cap boss 60/60 (R1/R2/R3) | At-cap boss 80/80 | Finale billed 80/80 | Finale billed 60/60 | Arc grinds 60/80 · 80/60 · 60/60 |
|---|---|---|---|---|---|---|---|---|---|
| S3 / 100% | 53.0/57.7/55.8 | 50.5 | 3+10/3+10/4+8 | 13/15/18 | 31.6/39.5/30.3 | 94.9/90.6/92.9 | 81.7/82.7/79.3/81.7 | 34.7/41.7/31.6/34.7 | 7/6/6/7 · 6/6/6/7 · 11/7/7/9 |
| 20% | 53.0/57.7/55.8 | 50.5 | 3+10/3+10/4+8 | 13/15/18 | 31.6/40.1/30.3 | 94.9/91.6/92.9 | 81.7/82.7/78.6/81.7 | 34.7/41.7/**30.3**/34.7 | same |
| 15% | 53.0/56.7/55.8 | 50.5 | 3+10/5+9/4+8 | 13/16/18 | 31.6/40.2/30.3 | 94.9/93.8/92.9 | 81.7/83.9/77.3/81.7 | 34.7/42.7/**28.0**/34.7 | same |
| 10% | 53.0/50.0/55.8 | **48.0** (R2 oh1) | 3+10/6+8/4+8 | 13/19/18 | 31.6/**26.2**/30.3 | 94.9/**86.3**/92.9 | 81.7/84.1/77.1/81.7 | 34.7/41.2/**27.7**/34.7 | 60/60 11/9/7/9 |
| 5% | 53.0/46.0/55.8 | **44.7** | 3+10/**8**+6/4+8 | 13/22/18 | 31.6/**19.3**/30.3 | 94.9/**80.3**/92.9 | 81.7/75.1/76.9/81.7 | 34.7/**27.0**/**27.7**/34.7 | 60/80 7/6/6/7 (step 2 wall 6) · 60/60 11/12/7/9 |
| 0% (locked) | 53.0/**35.8**/55.8 | **35.8** (R2 boss) | 3+10/**10**+4/4+8 | 13/22/18 | 31.6/**11.9**/30.3 | 94.9/**72.2**/92.9 | 81.7/70.9/76.7/81.7 | 34.7/**19.3**/**27.7**/34.7 | 60/80 7/**7**/6/7 · 60/60 11/18/7/9; 80/80 M12 45.5 <50 |

The at-cap boss columns are on the hardest track (S1 / W3 / T3). At-cap 60/80 · 80/60 for R2 is 62.8·80.6 (S3), 64.1·81.4 (20%), 66.6·82.2 (15%), 54.0·68.6 (10%), 45.6·59.3 (5%) and 37.3·46.1 (0%).
The lowest arc race for 80/80 is P3 55.9 at every B down to 10%. It is M12 50.9 at 5% and M12 45.5 at 0%.

## Targets
- **20%:** passes everything, including the arc evaluator's billed-finale 60/60 ≥30% (F3 30.3).
- **15%:** passes every target in the brief: 60/60 boss ≥30%, 80/80 cap 90–95%, story min ≥50%, mixed walls 3–6, finale steps ≤10. The one failure is the billed finale F3 (Street, POW 45.4%) for 60/60 at **28.0%**, against a 31.6% baseline.
- **10%:** fails story min (48.0), R2 60/60 at cap (26.2), R2 80/80 at cap (86.3), and F3 60/60 (27.7).
- **5% and 0%:** fail broadly. The 0% case reproduces the earlier "locked Touge carried into Wangan" result.

## Noise
- **Replicate rt2.** I re-ran the three hardest tracks at 30 turns, r 1.00–1.08, all p and profiles, with an independent seed set (N = 150 per style).
- **Δ difference.** The difference in Δ between replicates had sd 2.86 pp, so the SE per replicate is ≈2.0 pp. The largest single disagreement was 10 pp.
- **Averaged rerun.** Rerunning with rt1 and rt2 averaged (rtm) gives:
  - 20%: F3 60/60 30.7, all pass.
  - 15%: F3 60/60 29.2, and everything else passes.
  - 10%: F3 29.0, story min 48.0, R2 cap 60/60 26.6 / 80/80 85.6.
- **Verdict.** The 15% F3 miss (0.8–2.0 pp below 30) is inside noise, but it is below 30 in both runs. The 20% pass margin is +0.3/+0.7 pp, also thin. The baseline itself is only +1.6.

## Recommendation
**B = 20%** is the smallest value that keeps every target, including the billed-finale 60/60 floor. At 20%, the campaign is identical to S3, and the only finale change is F3 80/80 at 78.6 vs 79.3 and 60/60 at 30.3 vs 31.6.
If Austin treats the 60/60 ≥30% target as applying to campaign bosses only, **15%** passes, but F3 60/60 drops to about 28–29%.
**10% or less breaks the campaign** (the R2 Street→Wangan swing).

## Assumptions and flags
1. **The car split equals the skill-point split.** Win % depends only on the POW share, and HAN is fixed at 25% by the policy. The 20% of P that sits outside SP is still undefined in the sim (as before).
2. **Δ method.** An off-tune split is the live table plus a sweep delta. The sweep's absolute numbers are not used. Off-tune cells carry about 2 pp of noise.
3. **Teleport entry.** Live rounds start at the previous cap. Points earned between the previous round's end level and that cap are treated as new (free) points, applied after the retune. If they were treated as spent, the R2 numbers would get worse.
4. **Greedy policy.** The player always moves the full budget toward the new district tune. A smarter player who pre-balances (for example, buying EN in late R1) could do better. That case was not modelled.
5. **The arc uses the draft econ-v1 walker** (live table patched in). Arc entries come from each mode's campaign-end split (60/80 and 80/60 from mixed, 60/60 from hard, 80/80 from story).
6. **Touge hardest track (T3).** For 60/60, lower POW (25–35%) scores 2–5 pp better than the 45% tune. The tune was screened on the district mean, so I left it unchanged.

Files: retune.py, retune_sweep.py, retune_sweep_rt1/rt2/rtm.json, retune_results_rt1/rtm.json, retune_rt1.txt, retune_rtm.txt.
