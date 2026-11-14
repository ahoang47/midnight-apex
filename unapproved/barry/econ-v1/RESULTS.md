# econ-v1 — XP / mods / economy refit (draft)

**Status:** draft only, `unapproved/barry/econ-v1/`. No commits, no live `sim/` edits, no full test suite.
**Current default: Variant C** (Austin middle ground, 2026-11-13 evening). Variants A and B are kept below for history.
**Date:** 2026-11-13 (America/Los_Angeles).
**Combat:** live G2, touge-lines-v1 draft tracks, one fixed tune per district, 9×1000.
**Profiles:** 60/60, 60/80 (read/time), 80/60 (read/time), 80/80. Mixed sweeps are new (`results_mixed.npz`). 60/60 and 80/80 reuse the round-ladder-v1 r-sweeps. A `~` on a win rate means linear interpolation between exact grid points.

Constants: `proposed_constants.json`. Model: `model.py` (replaces stale `progression.py` in this folder only). G2 mixed lookup: `wr.py`.

---

## Iteration log (summary)

1. **Locked Variant A boss r** for criterion 9 (80/80 at cap ~85%, band 82–89). R1 Street boss stays on Shibuya S1 and is eased (r=1.040, S1 88.3 / 88.2). R2 Wangan r=1.025 (85.6%). R3 Touge r=1.053 (district 85.6%, uphill 83.3% — a touch harder on the uphill cell). Opponent budgets are `B = C_round / target_r`; player ceilings stay on the 1.07 chain (`C = 353.10 / 404.26 / 462.84`, caps L12 / 29 / 46).
2. **Mixed G2 sweep** (26 r, 9×1000) for 60/80 and 80/60. 80/60 is the fragile 10- and 20-turn profile at even-or-lower r (average heat + PACE_Q 0.6); 60/80 holds up better on short races and is weaker on long Touge uphill.
3. **Kid-r vs cap-jump.** The 1.07² jump in ceiling (Cₙ / Cₙ₋₁ = 1.1449) makes a +0.06 kid offset land at arrival r ≈ 0.95 if the player enters at the previous cap. That was a 15–20 grind-race wall at kid1 (iter 0). **Kids were raised** (r=1.18–1.20 at cap) so entry at the previous ceiling is r ≈ 1.02–1.03. R1 starts at L=0 as a stock car (k=1.00, no cap mods).
4. **Story / grind fit:** `story_fill = (0.62, 0.70, 0.93)`, `grind_frac=0.65`, taper τ=4.0, floor=0.22. High R3 fill is required so 80/80 story-only still reaches r ≈ 1.028 at the Touge boss (uphill 62.1%).
5. **R2 lieutenant retune** (kid2 1.16, mat1 1.12) so the mixed wall sits at mat1, not a 1-race kid2 dip.
6. **Aero, criterion 10, Austin's correction:** at most **one** aero, any of 6 slots, blocks that slot's regular mod. Compared best 1-aero vs best 0-aero only. **Did not tune stacking** (stacking is impossible). G2 sweep of a 10% one-slot shift toward the per-race best split (`results_aero.npz`). Priced at 1.75× the regular mod it replaces; pool stays 10%.
7. **Money / debt / floors** sized to the mixed modest-grind walk. Debt 160 clears by end of R1. T1/T2/T3 floors 0 / 13 / 30 (at or under each round's cap). Shop can fund the full 1.07 cap.

---

## At-cap bosses (Variant A) — criterion 9

| Round | Track | r | 60/60 | 60/80 | 80/60 | 80/80 |
|---|---|---:|---:|---:|---:|---:|
| R1 Street boss (S1) | district / **S1 CW / CCW** | 1.040 | 19.9~ / **15.0 / 15.7** | 63.1 / **54.6 / 55.1** | 52.7 / **47.6 / 48.7** | 91.5~ / **88.3 / 88.2** |
| R2 Wangan boss | district 30 | 1.025 | 15.9~ | 55.7 | 48.6 | **85.6~** |
| R3 Touge boss | district / **U / D** | 1.053 | 28.3~ / **24.4 / 32.1** | 56.0 / **50.9 / 61.2** | 60.3 / **56.0 / 64.6** | 85.6~ / **83.3~ / 88.0~** |

**80/80 is in the 85% band on the intended cells** (S1 88.3, Wangan 85.6, Touge uphill 83.3). Criterion 9 **PASS**.

**FLAG: 60/60 at cap is 15–28% on every boss (S1 15%, Wangan 16%, Touge uphill 24%), well below the 30–35% floor.** 60/60 cannot grind past the cap, so under Variant A they cannot be counted on to beat the game. This is not a tuning miss: on live G2, the r that puts 80/80 at 85% puts 60/60 at ~16–26%. The two floors cannot be met on the same target r. See Taste call 1 / Variant B.

Also: 80/60 is just under 50% at cap on R1 S1 (47.6 / 48.7) and on the R2 boss (48.6). Taste call 4.

Lieutenant at-cap (picked numbers, all four profiles) is in the walk appendix below. Note 60/60 at cap is already under 50% on R1 oh2 (48.4%), R2 oh2 (33.6%), R3 oh2 (44.5% / U 41.2%) and every boss — even a fully-capped 60/60 bounces on the last lieutenant and the boss.

---

## Per-round walks

Enter R1 at L=0 (stock). Enter R2 at C1 (L12). Enter R3 at C2 (L29). Combat power is 1.07 × P once past L=0, clipped to the current ceiling. Power is normalized so C1=353.10 is 100.

### 80/80, story-only (criterion 3)

Clears every rung at ≥50%, including Touge uphill. **PASS.** Tightest bosses: R1 S1 55.7 / 56.3 (r=1.000), R2 58.4 (r=0.977), R3 uphill 62.1 (r=1.028, L43).

| Rung | R1 Street r / 80/80 | R2 Wangan r / 80/80 | R3 Touge r / 80/80 (U/D) |
|---|---|---|---|
| kid1 | 1.020 / 94.7 | 1.031 / 90.7 | 1.030 / 91.9 (U89.1/D94.7) |
| kid2 | 1.063 / 98.1 | 1.029 / 90.6 | 1.019 / 90.2 (U87.0/D93.5) |
| mat1 | 1.016 / 81.5 | 1.010 / 80.8 | 1.007 / 67.8 (U64.1/D71.5) |
| mat2 | 0.996 / 71.8 | 0.997 / 77.1 | 1.005 / 65.0 (U62.0/D68.0) |
| oh1 | 0.998 / 71.8 | 0.977 / 66.5 | 1.007 / 66.2 (U63.2/D69.2) |
| oh2 | 0.999 / 74.2 | 0.979 / 66.5 | 1.016 / 70.9 (U67.5/D74.2) |
| boss | 1.000 / 62.6 (**S1 55.7/56.3**) | 0.977 / 58.4 | 1.028 / 65.4 (**U62.1/D68.7**) |

### Mixed 60/80 and 80/60 — modest grind (criterion 2)

Policy: grind 10-turn races at the first mixed <50% rung until both mixed profiles are ≥50% (district and hard cell), then grind to cap before the boss.

| Round | Wall | Wall grind | Then to cap | Total | Wall r after grind (60/80, 80/60) | Boss at cap (60/80, 80/60) |
|---|---|---:|---:|---:|---|---|
| R1 Street | mat1 | **3** | **10** | 13 | r=1.032 (63.6, 50.8) | 63.1 / 52.7 (S1 54.6/55.1 and **47.6/48.7**) |
| R2 Wangan | mat1 | **2** | **12** | 14 | r=1.026 (59.9, 55.9) | 55.7 / **48.6** |
| R3 Touge | mat1 | **7** | **2** | 9 | r=1.040 (58.2, 61.7; U53.4/58.3) | 56.0 / 60.3 (U50.9/56.0) |

Totals 13 / 14 / 9 — roughly flat, R3 a bit lighter. **R1 hits the 3–6 + ≤10 window exactly. R2's wall is a 2-race dip (short of 3–6) and then 12 to cap (just over 10). R3's wall is 7 (just over 6) and then only 2 to cap.**

**Why R2/R3 cannot all sit in 3–6 + 8–10 at once:** 80/80 story-only needs to arrive ~4 levels short of the R3 cap to still have ≥50% at r ≈ 1.028 against a cap-r of 1.053 (criterion 3 + 9). Mixed players share that story XP and only add the 3–6 wall grind (~2–4 levels), so they arrive at the boss already next to the cap. You can have a 3–6 mid-round wall, or 8–10 remaining to cap, or 80/80 story-only ≥50% at a cap-tuned-for-85% boss, but not all three on R3. Closest fit is above. Criterion 2 **FAIL (close)** — taste call 2.

Money: R1 end 111.5 after debt 0; R2 430; R3 767 (cash units, no shop spend deducted in the walk).

### 60/60 — hard-grind player

Can **reach every cap** (18 / 22 / 18 grind races if they grind every <50% rung, then sit at cap). 10-turn grind is only ~65% once they are near r=1.05; mid-round 10-turn at r≈1.03 is ~32–41%, winnable but not a juicy payout race (criterion 4, 60/60).

**They cannot beat the bosses at cap** (19.9 / 15.9 / 28.3 district; S1 15%, Touge uphill 24%). Expected attempts at 15–20% are 5–7, and they have no further grind lever. Under Variant A the campaign is not closable for 60/60.

---

## Criteria, pass / fail

| # | Result | Numbers |
|---|---|---|
| 1 Cap reachable, shop funds 1.07 | **PASS** | Caps L12/29/46. Mixed walk reaches cap each round. After debt, R1 money 111.5 covers 6×T1=96 (price 16). R2 pool covers 6×T2=168. R3 pool covers 6×T3=240. |
| 2 Mixed fair grind 3–6 + ≤8–10, flat | **FAIL (close)** | 3+10, 2+12, 7+2; totals 13/14/9. Structural conflict with crit 3+9, see above. |
| 3 80/80 story-only ≥50% (incl. uphill) | **PASS** | Worst bosses: S1 55.7, Wangan 58.4, Touge U 62.1. |
| 4 10-turn grind ~65–75%+ and pays | **PARTIAL** | Mixed 10-turn at the R1 wall r=1.032 is 77.5 / 75.8 (60/80, 80/60). At the R2 wall r=1.026: 66.9 / **62.4** (80/60 just under 65). R3 wall is after grind at r=1.040: 72.8 / 79.7. Grind purse is 55% of a wild. **60/60 10-turn at the R2 wall is 31.5%** — still winnable over a session, not a 65%+ feel. |
| 5 Mod tiers / floors / parity band | **PASS** | Floors T1=0, T2=13 (start R2, cap 29), T3=30 (start R3, cap 46). None above cap. At-cap opponent/player = 1/r = 0.83–0.98, inside 0.8–1.2. Story-only mid-ladder can dip below 0.8 for 60/60 (they are not the parity-band target). |
| 6 Debt by end R1; betting cannot break econ | **PASS** | Mixed and 60/60-hard both clear debt 160 by the R1 boss. `BET_MAX=20` (1:1 net) caps a perfect 4-race finale streak at 80, 33% of a T3 full-buy. Betting unlocks end of R2. |
| 7 Even level jumps, no dead stretches | **PASS** | +12 / +17 / +17. Every non-boss story rung grants ≥1 level on the story walk. |
| 8 Finale reachable at cap, sensible WR | **PASS, with a size flag** | To put 80/80 on the same 85% r against the *fixed* finale budgets 494.8 / 566.3 / 648.2 / 741.9, caps must be L61 / 75 / 93 / 112 (C=519.5 / 580.5 / 674.1 / 779.0). That is a **+66 level climb after L46**, more levels than the campaign. Win rates at those caps match the campaign bosses (Touge / Wangan / Street / Touge). Taste call 3. |
| 9 80/80 bosses at cap ~85% | **PASS** | 88.3 (S1), 85.6 (Wangan), 83.3 (Touge U) / 85.6 district. **60/60 FLAG 15–28%, below 30–35%.** |
| 10 Aero not dominant (1-aero vs 0-aero) | **PASS** at 1.75× | See next section. Stacking not tuned (impossible). |

---

## Criterion 10 — one aero vs none

Live rule, confirmed: **at most one aero**, any of the 6 slots, blocks that slot's regular mod. The part still pays its regular stats; only `AERO_POOL_FRACTION=0.10` of that one part is freely assignable. Shift of total combat power = `(0.27/6)×0.10 / 1.07 = 0.42%` of the split (L1 mass 0.009).

G2 9×1000, best 0-aero = district-fixed split, best 1-aero = same split with that 0.42% moved toward the touge-lines-v1 per-race best (`run_aero_sweep.py`, r = 1.025 / 1.040 / 1.050 / 1.070).

- **Mean delta (1-aero − 0-aero) is about +0.1 to +0.5 pp**, sometimes slightly negative when the r=1.07 60/60 "best" direction is a mismatch at another r or profile. Aero is not a uniform upgrade.
- **Situational peaks** are real on layouts where district-fixed is furthest from the best, especially **W3 C1 Outer CCW** (60/60 at r=1.05: +4.3 / +6.7 / +4.1 pp at 10/20/30; at r=1.07: +3.5 / +3.0 / +2.4). W1 can go the other way if the shift direction is wrong.
- 80/80 sees the same pattern at smaller practical value (they are already in the 80s–90s); one stand-out is Touge downhill at r=1.025 (+6.4 pp at 30, 68.5 → 74.9) when they are off-cap.

**Not dominant** at a **1.75×** price on the regular mod it replaces: the average gain is a fraction of a percentage point, and the player can simply not buy aero. Per-credit value of the *incremental* 0.75× is worse than buying the regular slot, except for a player who will retune for W3 / a few other outliers. Unlock end of R1 (in time for Wangan). Pool stays 10%. **No stacking-rule change.**

---

## Taste calls for Austin

1. **Variant A vs B (the 60/60 boss floor).** A meets 80/80 ~85% and leaves 60/60 at 15–28% on bosses — they can reach the cap (~18–22 grind/round) but cannot be counted on to close the game. B (boss r 1.08 / 1.07 / 1.10) puts 60/60 at ~69 / 68 / 64 (S1 ~58, Touge U 60) and 80/80 at ~99 / 98 / 97, i.e. the pre-criterion-9 feel. **These two goals cannot be met together on live G2.**
2. **Criterion 2 window vs 80/80 story-only.** Accept the close fit (13/14/9, walls 3/2/7), or relax "8–10 to cap" on R3, or let 80/80 do a little pre-boss grind (which weakens the "story-only" claim).
3. **Finale length.** Keep the fixed budgets and a L61–L112 cap climb, or cut finale B (conflicts with the fixed-input budgets).
4. **80/60 at cap just under 50%** on R1 S1 (47.6/48.7) and R2 boss (48.6). Easing those r by ~0.005 would put 80/60 over 50% and push 80/80 slightly above the 85% band (R1 S1 is already at 88.3).
5. **Aero price 1.75×** vs cheaper. 1.0× would make aero a mild no-brainer for min-maxers who retune W3; 1.75× keeps it a luxury.

---

## Flags for Desmond (story / docs) and others

- **Nathaniel / story:** `DEFAULT_CREW_ORDER` is Street → Wangan → Touge, one crew per district, no rematches. Debt clears end of R1, betting end of R2, finale after R3. The retired x1.30 opener step and opening-crew cap raise should come out of design/02, design/07 §1/§7/§8, the `DEFAULT_CREW_ORDER` note in `sim/equations.py`, and the `progression.py` docstring. Finale length (if Variant A caps are taken) is a narrative beat — a post-campaign climb bigger than the campaign itself.
- **Gordon / Godot:** three-crew order, unlock markers, one-aero slot UI (any of 6, mutually exclusive with that slot's regular mod), shop tiers at L0/13/30, retired opener-step UI.
- **Arthur:** no new art implied unless finale presentation changes with the longer cap climb.
- **Docs / test plan:** wording only in this draft; do not edit live files here. Level cap 150 → 46 campaign / 112 summit (Variant A). Finale caps 154–162 → 61/75/93/112 under the 85% targets.

---

## Appendix — at-cap lieutenants (Variant A)

Win rates at the round cap. 60/60, 60/80, 80/60, 80/80.

**R1 Street** (C=353.1): kid1 r=1.20 10t 99.4/99.9/100/100; kid2 1.16 97.4~/99.4~/99.7~/100; mat1 1.10 87.2/97.2/97.8/99.7; mat2 1.07 67.8/89.1/90.9/98.3; oh1 1.055 54.0/81.5/82.3/96.0; oh2 1.048 48.4/78.9/79.8/95.4; boss 1.040 — table above.

**R2 Wangan** (C=404.3): kid1 r=1.18 96.1/98.9/99.5/99.9; kid2 1.16 93.7/97.0/98.5/99.8; mat1 1.12 89.9/98.8/99.1/99.7; mat2 1.08 76.9/90.6/94.3/98.3; oh1 1.05 55.5/75.1/84.3/92.5; oh2 1.035 33.6/66.4/71.0/89.1; boss 1.025 — table above.

**R3 Touge** (C=462.8): kid1 r=1.18 94.4/98.3/99.4/99.8 (U 94.1/98.2/99.4/99.8); kid2 1.14 88.7~/95.2~/98.0~/99.6; mat1 1.10 71.7/88.8/92.1/97.8 (U 69.9/88.0/91.3/97.8); mat2 1.08 59.7/81.2/86.1/95.7 (U 57.5/79.5/84.4/95.4); oh1 1.065 50.0/73.6/79.5/93.0 (U 46.8/70.4/76.4/92.1); oh2 1.058 44.5/71.0/76.8/90.9 (U 41.2/67.1/73.3/89.4); boss 1.053 — table above.

Variant B at-cap bosses, for the taste call (same G2 tables): R1 r=1.08 60/60 69.0 (S1 57.5/60.2), mixed 92.4/92.7 (S1 88.1/87.1), 80/80 99.1 (S1 98.2/98.5). R2 r=1.07 67.6 / 87.5 / 91.2 / 97.6. R3 r=1.10 63.8 (U60.3) / 87.4 (U85.7) / 87.6 (U84.8) / 97.3 (U96.6).



---

# Variant C — Austin middle ground (2026-11-13, 2:58 PM PT)

Austin asked for a middle ground between Variant A (80/80 ~85% at cap, 60/60 15–28% on bosses) and Variant B (60/60 ~40%+, 80/80 mid-90s): **80/80 about 90% (88–92%) and 60/60 at least 30% against every boss variant**, including Shibuya S1 CW/CCW and Touge uphill. Relative intent kept: Touge a bit harder, S1 eased slightly. Non-boss levers (XP, story fill, grind taper, lieutenant r, and scoring 10-turn grind against wilds) were then iterated to fix criteria 2 and 4 and the 80/60-at-cap dip.

Constants: `proposed_constants.json` (`target_r_C`, `FINALE_R_C`, updated `story_fill` / grind). Walks: `eval_final_C.json`. Live G2, 9×1000, touge-lines-v1 tracks. A `~` is unused in the boss table below — those WRs are from the nearest exact sweep point (offsets ≤0.0006).

## Boss target r

| Round | r (published) | Exact grid r | 60/60 | 60/80 | 80/60 | 80/80 | Floors |
|---|---:|---:|---:|---:|---:|---:|---|
| R1 Street boss, **S1 CW / CCW** | 1.053 | 1.05313730 | 38.8 / **30.9 / 31.2** | 76.5 / **69.1 / 70.2** | 73.8 / **67.4 / 70.1** | 96.3 / **93.9 / 95.4** | 60/60 **PASS**. 80/80 **2–3 pp over 92** |
| R2 Wangan boss | 1.040 | 1.04051166 | 36.4 | 68.5 | 73.4 | **91.4** | **BOTH PASS** |
| R3 Touge boss, **U / D** | 1.066 | 1.06560224 | 37.4 / **33.7 / 41.0** | 65.8 / **61.4 / 70.1** | 69.4 / **66.4 / 72.4** | 90.8 / **89.6 / 91.9** | **BOTH PASS**. Touge uphill a bit harder than Wangan |

**Street S1 has no r that satisfies both floors.** Crossing points from the exact grid:

- 80/80 S1 first enters 88–92 at r=1.0405 (S1 88.3 / 88.2), where 60/60 S1 is 15.0 / 15.7.
- 60/60 S1 first reaches 30% on both directions at r=1.0531 (30.9 / 31.2), where 80/80 S1 is 93.9 / 95.4.
- Min-max compromise r=1.050 (exact): 60/60 S1 27.4 / 28.2 (1.8–2.6 short of 30%), 80/80 S1 92.7 / 94.2 (0.7–2.2 over 92).

**We take r=1.053** so the 30% floor holds on both S1 directions. That eases S1 more than a 90% 80/80 target would, and 80/80 lands 2–3 pp above the 92 cap (district 96.3). This is the remaining criterion-9 trade-off.

80/60 at cap is now well above 50% everywhere (S1 67.4 / 70.1, Wangan 73.4, Touge U 66.4). That dip is fixed.

## Criteria 1–10 under Variant C

| # | Result | Numbers |
|---|---|---|
| 1 Cap reachable, shop funds 1.07 | **PASS** | Caps still L12 / 29 / 46. Mixed walk reaches each cap. After debt, R1 money 106 covers 6×T1=96. R2 pool covers 6×T2=168. R3 pool covers 6×T3=240. Floors T1=0, T2=13, T3=30. |
| 2 Mixed fair grind 3–6 + ≤8–10, flat | **PASS** | Walls all at mat1. R1 **3+9**, R2 **3+9**, R3 **4+8**. Totals **12 / 12 / 12**, flat. (After the wall, mixed should spend the remaining 8–10 grind before later lieutenants if they don't want a mid-ladder dip; the count to cap is unchanged.) |
| 3 80/80 story-only ≥50% incl. uphill | **PASS** | Worst bosses: R1 S1 66.8 / 68.9 (r=1.012), R2 72.8 (r=0.999), R3 uphill **62.9** (r=1.032, L42). |
| 4 10-turn grind 65–75%+ for the intended player | **PASS** | Grind races are 10-turn wilds (kid1 budget), not the wall opponent. At the mat1 wall, mixed 10-turn vs wilds: R1 98.6 / 99.3, R2 88.2 / 94.1, R3 90.8 / 95.7. **60/60 vs those same wilds is 93.2 / 76.6 / 74.9** — also in or above the band. Grind purse is 55% of a wild (5.5 / 6.3 / 7.4). |
| 5 Tiers / floors / 0.8–1.2 parity | **PASS** | Same floors. At-cap opponent/player = 1/r = 0.89–0.96, in band. |
| 6 Debt by end R1; betting bound | **PASS** | Mixed and 60/60-hard both clear debt 160 by the R1 boss (mixed leftover 106). `BET_MAX=20` caps a perfect 4-race finale streak at 80 (33% of a T3 full-buy). |
| 7 Even jumps, no dead stretches | **PASS** | +12 / +17 / +17. Every non-boss story rung grants ≥1 level. |
| 8 Finale at cap, sensible WR | **PASS, size flag remains** | Same r targets as the campaign bosses. Caps **L63 / 76 / 95 / 114** (C=527.5 / 589.0 / 682.6 / 790.9). Climb **+68 from L46**, slightly larger than Variant A (+66 to L112) because the 90% r is higher than the 85% r, so C=B×r is higher against the same fixed finale budgets. WRs match the campaign bosses, including the S1 trade-off on Myth 3. Taste call unchanged: keep the climb, or cut finale B. |
| 9 80/80 ~90% and 60/60 ≥30% on every variant | **PASS on R2 and R3; trade-off on R1 S1** | Wangan 91.4 / 36.4. Touge U 89.6 / 33.7. S1: 60/60 30.9 / 31.2 (floor met), 80/80 93.9 / 95.4 (2–3 pp over 92). See table above. |
| 10 Aero not dominant (1 vs 0) | **PASS** at 1.75× | Unchanged from the 0-aero vs 1-aero G2 sweep. One aero, any of 6 slots, no stacking. Mean gain ~+0.1 to +0.5 pp, situational peaks on W3. |

## Per-round tables (Variant C)

Enter R1 at L=0 (stock, k=1.00). Enter R2 at C1 (L12). Enter R3 at C2 (L29).

### At cap (all four profiles)

Bosses are in the table above. Lieutenants at the round cap:

**R1 Street** (C=353.1): kid1 r=1.20 10t 99.4/99.9/100/100; kid2 1.16 97.4/99.4/99.7/100; mat1 1.10 87.2/97.2/97.8/99.7; mat2 1.07 67.8/89.1/90.9/98.3; oh1 1.065 63.1/86.2/88.5/97.8; oh2 1.058 57.8/83.9/85.2/96.7.

**R2 Wangan** (C=404.3): kid1 r=1.18 96.1/98.9/99.5/99.9; kid2 1.16 93.7/97.0/98.5/99.8; mat1 1.11 89.8/97.2/98.2/99.7; mat2 1.08 76.9/90.6/94.3/98.3; oh1 1.06 62.0/80.4/87.3/94.4; oh2 1.048 53.9/75.1/84.3/92.2.

**R3 Touge** (C=462.8): kid1 r=1.18 94.4/98.3/99.4/99.8 (U 94.1/98.2/99.4/99.8); kid2 1.16 92.2/97.0/98.9/99.8; mat1 1.12 78.5/96.0/97.5/98.8 (U 76.0/96.0/97.5/98.5); mat2 1.085 62.5/81.2/86.1/96.4 (U 59.9/79.5/84.4/96.1); oh1 1.075 57.1/76.9/82.7/94.7 (U 54.5/74.2/80.3/94.1); oh2 1.07 53.5/76.9/82.7/94.1 (U 50.7/74.2/80.3/93.6).

60/60 at cap is now ≥50% through every lieutenant except they still have to win the boss at 31–37%. That is closable (expected ~3 attempts at the cap). Under Variant A it was not.

### Mixed modest grind (criterion 2)

| Round | Wall | Wall grind | Then to cap | Total | After-wall r (60/80, 80/60) | Boss at cap |
|---|---|---:|---:|---:|---|---|
| R1 Street | mat1 | 3 | 9 | 12 | r=1.032 (63.6, 50.8) | 76.5 / 73.8 (S1 69.1/70.2 and 67.4/70.1) |
| R2 Wangan | mat1 | 3 | 9 | 12 | r=1.025 (59.9, 55.9) | 68.5 / 73.4 |
| R3 Touge | mat1 | 4 | 8 | 12 | r=1.042 (59.6, 63.8; U 54.9/60.5) | 65.8 / 69.4 (U 61.4/66.4) |

### 80/80 story-only (criterion 3)

| Rung | R1 Street r / 80/80 | R2 Wangan r / 80/80 | R3 Touge r / 80/80 (U/D) |
|---|---|---|---|
| kid1 | 1.020 / 94.7 | 1.031 / 90.7 | 1.030 / 91.9 (U89.1/D94.7) |
| kid2 | 1.063 / 98.1 | 1.029 / 90.6 | 1.029 / 91.9 (U89.1/D94.7) |
| mat1 | 1.016 / 81.5 | 1.009 / 80.8 | 1.018 / 74.8 (U71.1/D78.4) |
| mat2 | 0.996 / 71.8 | 0.997 / 77.1 | 1.002 / 63.9 (U60.5/D67.4) |
| oh1 | 1.007 / 78.5 | 0.994 / 77.1 | 1.008 / 67.8 (U64.1/D71.5) |
| oh2 | 1.009 / 78.5 | 0.999 / 78.0 | 1.020 / 74.8 (U71.1/D78.4) |
| boss | 1.012 / 74.0 (**S1 66.8/68.9**) | 0.999 / 72.8 | 1.032 / 68.4 (**U62.9/D74.0**) |

### 60/60 hard-grind player

Reaches every cap with **13 / 16 / 18** grind races if they grind every <50% rung. At cap they beat bosses at **31–37%** (S1 30.9 / 31.2, Wangan 36.4, Touge U 33.7) — closable, unlike Variant A. 10-turn grind vs wilds at those points is 75%+ once they are a few levels in (opening R1 kid1 vs a stock car is still 27.4% for 60/60; they grind that opener in 2 races to 85.9%).

## Key constants that changed (A → C)

- **Boss r:** Street 1.040 → **1.053**, Wangan 1.025 → **1.040**, Touge 1.053 → **1.066**.
- **Lieutenants (entry and wall):** R2 mat1 1.12 → **1.11** (so the mixed wall is 3 grind, not 2). R3 kid2 1.14 → **1.16** (so a 1-race 10-turn dip is not consumed as the round's wall). R3 mat1 1.10 → **1.12** (wall 4, not 7–8). Kids stay 1.18–1.20 so entry at the previous ceiling is r≈1.03.
- **story_fill:** (0.62, 0.70, 0.93) → **(0.62, 0.75, 0.80)**. R3 fill came down because easier bosses let 80/80 story-only still clear 50% at r=1.032; that leaves mixed the 8 grind to cap after the wall.
- **Grind:** frac 0.65 → **0.70**, taper τ 4.0 → **3.6**, floor 0.22 → **0.20**.
- **10-turn grind WR** is now scored against a wild/kid1 opponent at the player's current power (the live fiction), not against the lieutenant they are stuck on. That is what lets criterion 4 pass.
- **Finale r / caps:** 1.050/1.025/1.040/1.050 and L61/75/93/112 → **1.066/1.040/1.053/1.066** and **L63/76/95/114** (+68 from L46).
- Money, debt 160, prices, aero 1.75×, floors, unlocks, retired x1.30 opener: unchanged.

## Remaining conflicts and taste calls

1. **Street S1 cannot hit both floors.** We took r=1.053 (60/60 30% holds, 80/80 94–95%). The alternative closest-compromise is r=1.050 (60/60 S1 27–28%, 80/80 S1 93–94%). Austin can flip this if he would rather protect the 88–92 band than the 30% floor.
2. **Finale climb is still huge, and slightly larger than Variant A** (+68 vs +66). Same taste call: keep it, or cut the fixed finale budgets.
3. **After the mixed wall, later lieutenants can dip below 50% if the player banks the remaining 8–10 grind until the boss.** The count is correct; the nicer play is to spend those races before oh/mat2. Not a constant change — a UX / recommendation item for Gordon if needed.
4. Aero price 1.75× vs cheaper is still open, unchanged.

Desmond / Gordon / Arthur flags from Variant A still apply. Campaign cap stays 46; summit cap ticks up to 114 if Variant C finale caps are taken.

## Austin's picks (2026-11-13, econ-v1)
- Variant C locked.
- R1 Street boss (Shibuya S1) stays at r=1.053, which keeps 60/60 at 30% or better (80/80 is 93.9 / 95.4).
- The finale keeps its fixed budgets. The climb continues to about L114 (+68 from L46).
- Money is rescaled ×100 to USD: wild $1,000, crew $2,500, boss $8,000, debt $16,000, T1/T2/T3 $1,600/$2,800/$4,000, bets $500–$2,000. Pure rescale; balance unchanged. Older sections of this file still use the 1-unit scale (×100 to read in USD).

## Betting (USD, even money, unlocks after R2)

Austin asked whether even-money bets on every race from the moment betting unlocks (R3 grind, R3 ladder, and the finale) can let a player buy a big pile of mods early. This section is a new check on the x100 USD book: wild $1,000, crew $2,500, boss $8,000, R3 purses ×1.35 (grind $742.50, crew $3,375, boss $10,800), debt $16,000, T1 $1,600, T2 upgrade $2,800, T3 upgrade $4,000, bets $500–$2,000 at even odds (net +stake on a win, −stake on a loss).

Sim: `unapproved/barry/econ-v1/run_betting.py` and `betting_results.json`. Honest shop (a slot is T3 or T2 or T1, never stacked; aero is 1.75× T3 on one slot). Best legal T3 build = 5 regular T3 + 1 T3 aero = **$27,000** (full T1+T2+T3 path **$53,400**). T2 floor L13, T3 floor L30, 1.07 cap, and the content ceiling still bind. Four profiles, typical walks: 80/80 story-only, mixed 60/80 and 80/60 (12 R3 grind wins: 4 wall + 8 to cap), 60/60 hard (18 R3 grind wins). Policies: no-bet; likely-win at WR ≥65% and ≥50%, max stake; greedy always-max. Fixes also simmed: story/ladder only (no grind bets), cap stake at the purse, fair odds (net (1−p)/p, EV 0), BET_MAX $500, 3 bets per round. Monte Carlo: 4,000 wild-only T3 farms, 4,000 R3 walks, 1,500 R3+finale walks, seed 20261113, live G2 WR tables (exact-r preferred). Ladder losses retry the same rung (one story purse on the eventual win; bets paid every attempt). Ruin is cash hitting $0 (`zeroed`). A leftover under $500 after buying mods is not ruin. **Finale billed purse is not in canon; this sim pays the R3 boss purse, $10,800, on each of the four billed finale races, and $742.50 on finale XP grinds.**

### What the floors and the 1.07 cap actually do

Betting cannot buy levels and cannot raise a level's 1.07 ceiling. At R3 entry everyone is still on T2 only (L26 or L29, under the L30 T3 floor). Combat at L29 is clipped to C2 (404.15), which is only 0.873 of the R3 cap (462.84), r = 0.931 vs the R3 boss — unwinnable, T3 or not. The same clip means a hypothetical illegal T3 buy at L29 would not add a single point of combat. From L30 upward the 1.07 cap starts to swallow incremental T3: at the 80/80 story boss arrive (L41), **four regular T3 already sit on the 1.07 cap** (r = 1.0232, 80/80 uphill 58.1%). The last T3 plus the aero (the rest of the $27,000 package) bump that only to r = 1.0239 / 62.1%, a grid-jitter-sized gap, not a new cap. At L46 the full 5+aero package is what fills the R3 cap (T2-only at L46 would be 0.968 fill, r = 1.0315, 80/80 uphill 64.0% instead of 89.6%). Past L63 the T3 package no longer fills 1.07×P — that is the existing finale T3-only hole, and no amount of cash creates a T4.

Greedy shop matters: players buy each $4,000 T3 slot as soon as L ≥ 30 and they have the cash, they do not bank $27,000 and dump it in one go. That is why even-money winnings do not pile into a sudden mid-ladder power spike; they get converted into the next legal slot, and the 1.07 cap is already nearby.

### Entering R3

| Profile | Walk | L | Cash after T1+T2 | Still needs for 5 T3 + aero | 10-turn WR vs R3 kid1 |
|---|---|---|---|---|---|
| 60/60 | hard | 29 | $23,920 | $3,080 | 32.1% |
| 60/80 | mixed | 29 | $19,740 | $7,260 | 67.6% |
| 80/60 | mixed | 29 | $19,740 | $7,260 | 68.9% |
| 80/80 | story | 26 | $600 | $26,400 | 86.8% |

Debt is already clear for all four on these walks. 80/80 story-only barely paid off the $16,000 R1 debt and the $26,400 T1+T2 shop; they enter R3 with $600.

### Grind races to fund the best legal T3 (5 regular + 1 aero)

Two views. First, a wild-only money farm from R3 entry (XP still applies, L30 still binds). 4,000 trials.

| Profile | No-bet wins (attempts) | Likely-win / always-max wins (attempts) | Fair odds wins (attempts) | Notes |
|---|---|---|---|---|
| 60/60 | **5** (mean 12.5 att, p at entry 32%) | likely65: still **5** (they refuse the 32% bet). always-max: **8.3** wins / 16.7 att, profit **−$1,833**, 0.7% zeroed | 7.3 / 14.3, profit ≈ $0 | Betting at 32% even money is −EV. 60/60 should not bet the opening farm. |
| 60/80 | **10** (13.1 att) | **4.7** wins / 6.6 att, profit ≈ **+$5,050**, 0% zeroed | 10.6 / 13.6, profit ≈ $0 | Cuts the farm roughly in half. |
| 80/60 | **10** (12.1 att) | **4.3** wins / 5.7 att, profit ≈ **+$5,350**, 0% zeroed | 10.4 / 12.4, profit ≈ $0 | Same pattern. |
| 80/80 | **36** (37.2 att) | **12.3** wins / 13.3 att, profit ≈ **+$18,600**, ~13% zeroed (thin $600 bankroll) | 34.2 / 35.4, profit ≈ +$1,557 | This is the headline farm cut, 36 → 12, but it is an *optional* money grind. The story walk already funds the package from the boss purse. |

Story-only betting (no grind bets) matches no-bet on this farm, as it should. Capping the stake at the $742.50 grind purse is a partial nerf (80/80 19.6 wins, mixed 6.1–6.4). BET_MAX $500 leaves 80/80 at 23.1 wins. A 3-bet cap leaves 80/80 at 31.8. Fair odds almost restores the no-bet farm time.

Second, the *typical walk* (story purses count, so fewer dedicated money grinds):

- **60/60 hard, no-bet:** 3 grind wins plus the kid1 purse funds the $27,000 package at L31, before kid2. They already have it for every later R3 fight, including the boss at cap (uphill 33.7%). always-max does not get them to the boss earlier or stronger; it can delay the package (mean 5.6 grind wins, and in a thin tail they arrive at the boss slightly under fill, WR min 28.8%).
- **Mixed 60/80 and 80/60, no-bet:** 4 grind wins plus kid1/kid2/mat1 purses fund the package at L37, before mat2. After kid1 they already buy five regular T3 (L ≥ 30, cash ≈ $21,090); only the aero is waiting on the wall. With likely-win / always-max the aero lands about 2 grind wins earlier (often on the mat1 arrive, 95–98% of trials). Mid-ladder and boss WR do not move: 60/80 boss stays 61.4%, 80/60 stays 66.4%, both at cap. The 12 XP grind wins still have to be run.
- **80/80 story, no-bet:** 0 grind. They buy T3 slots as the seven story purses come in (one slot after each of mat1, mat2, oh1, oh2). They arrive at the boss with **four regular T3, $800, r = 1.0232, uphill 58.1%** — already on the 1.07 cap. The $10,800 boss purse finishes the 5th T3 + aero (leftover $600) **after** the boss, 100% of trials. always-max / likely50 never complete the full package *before* the boss in 4,000 trials (greedy shop keeps draining the bankroll into the next $4,000 slot, so they cannot bank $27,000). End of R3, only **80.8%** of always-max trials have the full 5+aero package (vs 100% no-bet); 67.7% hit $0 at some point, and the boss WR spreads from 38.6% (gambled away so many slots) to 62.1% (full package), mean 60.1%, p50 62.1%. likely65 is tamer (only bets the kids, mean profit +$2,139) and still arrives at 58.1%. So on the story path, betting is not how 80/80 gets a better R3 boss — no-bet already sits on the cap — and greedy always-max can make the boss *worse*.

### R3 boss and “noticeably earlier”

| Profile | No-bet boss (uphill) | always-max / likely65 boss | Full T3 before the boss | End-R3 cash no-bet → likely65 / always |
|---|---|---|---|---|
| 60/60 | 33.7% at cap, mean 2.9 tries | 33.7% (always min 28.8%) | 100% no-bet and likely65; 99.95% always | $37,285 → $60,235 / $54,435 (p50) |
| 60/80 | 61.4% at cap, mean 1.62 tries | 61.4% | 100% | $28,650 → $51,650 / $51,550 |
| 80/60 | 66.4% at cap, mean 1.49 tries | 66.4% | 100% | $28,650 → $54,650 / $53,650 |
| 80/80 | 58.1% at L41 on the 1.07 cap, mean 1.73 tries | likely65 58.1%; always mean 60.1% / p50 62.1% / min 38.6% | 0% for the full 5+aero package in every policy | $600 → $3,200 / $5,350 (p50); always 67.7% zeroed |

Betting does not get anyone to the R3 boss at a higher cap, and it does not cut the XP grind that mixed and hard still have to run to L46 (12 and 18 official grind wins, unchanged). The only “earlier” effect is the optional wild-only farm (mixed 10→5 attempts, 80/80 37→13). On the walks the game actually expects, that farm is not required.

End-R3 bankroll *is* where even money prints for anyone who bets only when they are a favorite: mixed and 60/60 likely65 leave R3 with about **+$22k to +$26k** expected bet profit. always-max on 60/60 is sloppier (mean profit +$16,176, p10 −$600) because they also fire into sub-50% fights. 80/80’s $600 roll plus always-max is the ruin case, not the printer.

### Finale: not trivial, and the T3 hole is the real problem

All four profiles can be at the step cap in XP (80/80 also has to grind the levels; L46→L63 / L76 / L95 / L114 takes **31 / 50 / 78 / 106** grind *wins*). Combat is the same with or without betting, because the 1.07 cap and the T3 package are already decided and there is no T4. Single-attempt WR at cap with the best legal T3, honest shop:

| Step | Dist | L | fill vs cap | r (designed r*) | 80/80 | 60/80 | 80/60 | 60/60 |
|---|---|---|---|---|---|---|---|---|
| F1 | Touge 30 | 63 | 1.000 | 1.0655 (1.066) | 89.6% | 61.4% | 66.4% | 33.7% |
| F2 | Wangan 30 | 76 | 0.968 | 1.007 (1.040) | 75.5% | 44.2% | 21.2% | 3.1% |
| F3 | Street 30 | 95 | 0.940 | 0.990 (1.053) | 54.3% | 18.6% | 2.4% | 0.0% |
| F4 | Touge 30 | 114 | 0.917 | 0.977 (1.066) | 21.3% | 4.9% | 0.1% | 0.0% |

This is the T3-only hole flagged in the Variant C write-up, not a betting effect. F1 still matches the designed r. From F2 on, fill slips under the cap and the designed r* is missed. 60/60 is effectively stuck at F3 (0% in 1,500 trials, even with 20–60 retries). 80/60 almost never clears F4 (0.07% no-bet). 60/80 “clears” F4 in 95.7% of trials only because the sim retries up to 60 times on a 4.9% fight (mean 19 tries). 80/80 clears all four in 100% of trials, but F4 is a 21.3% uphill (mean 4.6 tries), not a gimme.

Betting does not move any of those WRs, and it does not make any finale step trivial. What it *does* is print cash on the 31–106 even-money grind races when the player is a favorite, and burn cash when they are not:

| Profile | End-finale cash no-bet (p50) | likely65 (p50, mean profit) | always-max (p50, mean profit, % zeroed) |
|---|---|---|---|
| 80/80 | $138,098 | $379,898, **+$241,135** | $377,298, +$237,468, 67.5% zeroed at some point (usually the thin R3 start, they recover) |
| 60/80 | $163,920 | $355,920, **+$191,983** | $315,020, +$143,018, 0% zeroed |
| 80/60 | $128,618 | $304,875, **+$180,437** | $25,875, **−$80,934**, 7.0% zeroed (they fire always-max into 2.4% and 0% F3/F4 fights) |
| 60/60 | $101,208 (stuck after F2; 84.7% eventually win the 3.1% F2, mean 27 tries) | $200,158, **+$102,364** (they skip the 3% bets) | $5,110, **−$89,795**, 11.1% zeroed |

likely65 is the profitable policy: bet the high-WR F1 (and 80/80 F2) grinds, refuse the long shots. always-max is a money printer for 80/80 and 60/80 and a ruin policy for 60/60 and 80/60 once F2–F4 go under 50%. None of that changes the fight.

### Is it an exploit, and the smallest fix

**Power / timing exploit: no.** The L30 floor and the 1.07 cap do what they were supposed to do. Betting does not put a player on the R3 boss or a finale boss at a higher effective cap, and it does not cut the XP races to those fights. On the typical walks the full legal T3 package is already funded without betting (80/80: after the R3 boss purse; mixed: 4 grind wins into the R3 wall; 60/60: 3 grind wins plus kid1).

**Economy exploit: yes, on grind races.** Even money on a heavy favorite is a printer. The existing constants note (`bet_max_finale_gain: $8,000`) assumed a perfect streak on the *four billed finale races*. Once bets are allowed on every grind from R3 through the finale, that cap is meaningless: 80/80 likely65 leaves the finale about **+$241,000** expected, 60/80 about **+$192,000**. The optional 80/80 wild farm also shrinks from 36 winning grinds to 12.

**Ruin:** the $600 80/80 story start is too thin for greedy always-max (67.7% hit $0 during R3, and 19% fail to finish the T3 package by the end of R3). Mixed and 60/60, with a $20k–$24k R3 bankroll, do not go broke on R3 even under always-max (0% zeroed). The dangerous finale case is always-max on a long-shot billed fight (60/60, 80/60).

**Smallest fix, and the one we recommend: bets only on ladder / story / billed finale races, not on grind or wild races.** Keep BET_MIN $500, BET_MAX $2,000, even odds. That is the rule the $8,000 finale-gain note already assumed. Simmed as `story_only`:

- The wild-only T3 farm returns to the no-bet counts (80/80 36 wins, mixed 10, 60/60 5).
- 80/80 end-finale expected bet profit falls from **+$241,135** (likely65 on all races) to **+$1,746**.
- R3 boss WRs are unchanged for mixed and 60/60. 80/80 still arrives on the 1.07 cap without needing grind bets.
- 60/60 / 80/60 can still light their bankroll on fire if they always-max a 3% or 0% *billed* finale fight (story_only 60/60 finale profit −$79,100). That is a player-policy problem, not a grind printer; a client-side “you are a heavy underdog” warning would cover it.

**Fair odds** (payout depends on r, net (1−p)/p) is the right alternative if grind betting should stay as flavor. Simmed: farm times almost match no-bet (80/80 34 vs 36 wins, profit ≈ $0 on R3). It needs an honest r-table and should refuse or correctly price ~0% fights — the sim’s 0.05–0.95 odds clamp is not a production rule. Capping the stake at the purse, dropping BET_MAX to $500, or allowing only 3 bets per round all still leave a finale-grind printer (max $500 still puts 80/80 at about **+$59,800** over the finale). Those are not enough on their own.

Criterion 6’s “betting from end of R2 cannot break the economy” is a **fail under the current even-money, any-race rule**, and a **pass under the recommended story/ladder-only rule**. No live `sim/` edits and no commits in this pass; the recommendation is recorded on `proposed_constants.json` as `money.betting_audit_2026_11_13` without changing BET_MIN, BET_MAX, or the even-odds default.

## Betting levers (factorial) and T4

Austin’s correction: every betting idea is a separate lever that can combine, and LWN (story/ladder-only) is not the headline. This section replaces the single-fix recommendation above. Austin decides. Sim: `run_betting_levers.py`, `betting_levers.json`. 400 likely-win trials per cell (WR ≥ 65%, max stake). No commits, no live `sim/` edits.

### T4 design (money sink + the finale hole)

The T3-only hole at F2–F4 is real: T3 fill is 0.968 / 0.940 / 0.917 of cap, and 60/60 is stuck at F3 (0%) without a new tier. T4 is one upgrade tier, 6 slots, at most one aero at 1.75×, sized so six T4 slots equal `0.27 × P(L114)`. The 1.07 cap still clips. Floor **L47**, unlock after R3 (Mentor Confrontation). Wholesale (0.20 off list) runs from end of R1 through end of R3 and **does not** apply to T4.

With a full T4 package at the step cap, designed r and the 90% / 30% band come back:

| Step | Dist | L | grind wins from L46 (80/80 F1 is 34 from L43) | T3 r / 80/80 / 60/60 | T4 r / 80/80 / 60/60 / 60/80 / 80/60 |
|---|---|---|---|---|---|
| F1 | Touge 30 | 63 | 31 | 1.066 / 89.6 / 33.7 (T3 already fills) | 1.070 / 91.6 / 37.4 / 66.7 / 70.8 |
| F2 | Wangan 30 | 76 | 25 | 1.007 / 75.5 / 3.1 | 1.037 / 90.3 / 32.7 / 66.9 / 71.0 |
| F3 | Street 30 | 95 | 34 | 0.990 / 54.3 / 0.0 | 1.053 / 93.9 / 30.9 / 69.1 / 67.4 |
| F4 | Touge 30 | 114 | 34 | 0.977 / 21.3 / 0.0 | 1.070 / 91.6 / 37.4 / 66.7 / 70.8 |
| | | | **total 106** (80/80 34+25+34+34) | | |

F2 T4 r is 1.0366 vs r* 1.040 because `1.07 × P(76) = 587.0` sits 2 points under FINALE_C 589.0. 80/80 90.3 and 60/60 32.7 still hold the band. **Two regular T4 slots already fill the F2 cap; three fill F3; the full 5+aero package is what F4 needs.** Incremental shop therefore restores F2/F3 WR before the player has paid for the whole package.

Wholesale on T2/T3 raises R3 entry and end-R3 leftover (list T3 package $27,000 becomes $21,600):

| Profile | End R2 (enter R3) | End R3 no-bet, T3 bought |
|---|---|---|
| 60/60 hard | L29, $27,280 | $46,045 |
| 60/80, 80/60 mixed | L29, $23,100 | $37,410 |
| 80/80 story | L26, $4,600 | $10,000 |

T4 regular-upgrade prices swept at **$5,000 / $8,000 / $12,000 / $18,000** (packages **$33,750 / $54,000 / $81,000 / $121,500**). No-bet, official wins, every profile at every price in this sweep **clears all four finale steps at the T4 WRs above**. When the full package lands:

| T4 regular (package) | 60/60 / mixed full T4 by | 80/80 full T4 by | No-bet end cash 60/60 · mixed · 80/80 |
|---|---|---|---|
| $5,000 ($33,750) | F1 | F1 | $147,565 · $138,930 · $113,748 |
| $8,000 ($54,000) | F1 | F2 | $127,315 · $118,680 · $93,498 |
| $12,000 ($81,000) | F2 | F3 (partial T4 already fills F2) | $100,315 · $91,680 · $66,498 |
| $18,000 ($121,500) | F3 (partial fills F2) | F4 (partial fills F2 and F3) | $59,815 · $51,180 · $25,998 |

So T4 works as a **leftover sink** and as the **stat fix for criterion 8**. It does **not** work as a sink for an uncapped even-money grind printer (see below): players buy the package and keep the rest.

Finale billed purse is still the assumed $10,800 (not in canon). Scaled 10-turn finale wilds use B = C / 1.18.

### Levers and criterion 6 rubric

1. **Unlock:** after R2, or after R3 (promoter beat; wholesale has just ended).
2. **Eligible races:** any; story / ladder / billed finale only; wild / grind only.
3. **Bet-count cap:** none, or a total of 4, 8, or 16 bets after unlock.
4. **T4 regular price:** the four values above.
5. **Odds (optional):** even money, or fair net `(1−p)/p`. Fair was run at cap=none only.

**Criterion 6.** FAIL if likely-win mean bet profit is ≥ $40,000 (a printer) or a finale-step WR jumps by ≥ 8 pp vs no-bet. LEAK if profit is $16,000–$40,000. PASS otherwise. Hitting $0 because the shop just spent the last dollars on a T4 slot is not ruin. **Mixed “worth it”** if the mean of 60/80 and 80/60 profit is at least one R3 crew purse ($3,375).

Bet profit is almost invariant with T4 price (it changes leftover, not how often a favorite is offered). The compact table therefore reports likely-win mean profit vs no-bet at **T4 = $8,000** ($54,000 package). The same C6 call holds at the other three prices unless noted.

### Compact table (likely-win profit vs no-bet, T4 = $8,000)

| Unlock | Eligible | Cap | Odds | 80/80 | 60/80 | 80/60 | 60/60 | Mixed worth it? | C6 |
|---|---|---|---|---:|---:|---:|---:|---|---|
| R2 | any | none | even | $256,293 | $242,714 | $254,010 | $181,493 | Y | **FAIL** printer |
| R2 | any | 4 | even | $4,952 | $3,357 | $4,550 | $3,700 | Y | **PASS** |
| R2 | any | 8 | even | $11,259 | $9,702 | $11,142 | $8,057 | Y | **PASS** |
| R2 | any | 16 | even | $24,699 | $24,316 | $25,692 | $19,698 | Y | **LEAK** |
| R2 | story | none | even | $10,602 | $4,325 | $7,128 | $0 | Y | **PASS** |
| R2 | story | 4 | even | $4,514 | $2,728 | $2,908 | $0 | n | **PASS** |
| R2 | story | 8 | even | $10,002 | $3,680 | $5,663 | $0 | Y | **PASS** |
| R2 | story | 16 | even | $10,533 | $4,034 | $6,593 | $0 | Y | **PASS** (story already caps itself at the billed races) |
| R2 | wild | none | even | $244,855 | $238,248 | $246,937 | $180,420 | Y | **FAIL** printer |
| R2 | wild | 4 | even | $6,370 | $5,699 | $6,751 | $3,760 | Y | **PASS** |
| R2 | wild | 8 | even | $13,217 | $13,187 | $14,574 | $8,117 | Y | **PASS** |
| R2 | wild | 16 | even | $27,296 | $24,871 | $27,256 | $19,629 | Y | **LEAK** |
| R3 | any | none | even | $251,815 | $216,684 | $226,629 | $155,070 | Y | **FAIL** printer |
| R3 | any | 4 | even | $6,360 | $2,766 | $3,904 | $2,911 | borderline | **PASS** |
| R3 | any | 8 | even | $13,008 | $7,795 | $9,979 | $6,785 | Y | **PASS** |
| R3 | any | 16 | even | $26,758 | $19,147 | $23,504 | $18,309 | Y | **LEAK** |
| R3 | story | none | even | $7,089 | $1,945 | $4,095 | $0 | n | **PASS** |
| R3 | story | 4 | even | $6,578 | $1,825 | $2,810 | $0 | n | **PASS** |
| R3 | story | 8 / 16 | even | ~$7,057–$7,255 | ~$2,0–2.2k | ~$3.0–4.3k | $0 | n / borderline | **PASS** (only 4 billed finale races exist) |
| R3 | wild | none | even | $244,419 | $212,438 | $221,847 | $155,226 | Y | **FAIL** printer |
| R3 | wild | 4 | even | $6,450 | $3,153 | $4,028 | $2,803 | Y | **PASS** |
| R3 | wild | 8 | even | $12,981 | $7,113 | $9,878 | $6,271 | Y | **PASS** |
| R3 | wild | 16 | even | $26,948 | $18,454 | $23,447 | $18,120 | Y | **LEAK** |
| R2 | any | none | fair* | $8,484 | $2,732 | $6,450 | $121 | Y | **PASS*** |
| R2 | story | none | fair | −$5 | $35 | $5 | $0 | n | **PASS** |
| R2 | wild | none | fair* | $8,430 | $2,949 | $6,111 | $199 | Y | **PASS*** |
| R3 | any | none | fair* | $8,322 | $3,974 | $5,213 | $206 | Y | **PASS*** |
| R3 | story | none | fair | $54 | −$16 | −$67 | $0 | n | **PASS** |
| R3 | wild | none | fair* | $8,613 | $3,200 | $5,609 | $1,033 | Y | **PASS*** |

60/60 profit is $0 on story-only because likely-win refuses the 31–34% billed finale fights. Mixed F1 is 61.4% (just under 65%), so they also skip some billed Touge 30s.

\* **Fair odds as implemented clamp p into [0.05, 0.95].** A 99% favorite is then +EV by about $84 per $2,000 bet, which is where the ~$8.5k 80/80 “fair” residual comes from (a hundred finale grinds). **True fair odds on honest short prices would sit near $0** and mixed players would have little reason to bother unless they enjoy the variance. A production r-table must not clamp the short end.

No combo in this grid jumped a finale-step WR by 8 pp vs no-bet: once incremental T4 is in play, no-bet already sits on the designed r at F2–F4. Betting only changes cash. At T4 = $8,000, uncapped 80/80 likely-win does finish the full package at F1 (no-bet waits until F2), but F1 was already at 89.6% on T3, so the WR does not move.

### Money at each finale step (T4 = $8,000, no-bet vs a few likely-win combos)

No-bet leftover after shop, official wins: 60/60 F1–F4 $25,862 / $55,225 / $91,270 / $127,315; mixed $17,228 / $46,590 / $82,635 / $118,680; 80/80 $6,045 (full T4 not yet) / $21,408 / $57,452 / $93,498.

Likely-win *adds* the bet-profit column, almost dollar-for-dollar, at every later step. Examples at T4 = $8,000:

- R2 / story / cap none (even): 80/80 ends $10,602 over no-bet; mixed +$4,325 / +$7,128; 60/60 +$0. All WRs match no-bet.
- R3 / story / cap none (even, the late billed-only beat): 80/80 +$7,089; mixed +$1,945 / +$4,095; 60/60 +$0.
- R2 / any / cap 8 (even): 80/80 +$11,259; mixed +$9,702 / +$11,142; 60/60 +$8,057.
- R2 / any / cap none (even): 80/80 ends at $349,790 vs $93,498 no-bet. The $54,000 T4 package is a rounding error on a $256k print.

### Short list that pass, with trade-offs (not a ranking)

Austin picks. These five all pass criterion 6, keep the T4 sink honest, and do not move finale WRs. They differ in story timing, whether mixed players will bother, and how hard the cap/odds have to work.

1. **Unlock R2, story / ladder / billed finale only, no cap, even money.** The previous “smallest fix.” 80/80 about +$10.6k, mixed +$4.3k / +$7.1k (worth it), 60/60 +$0. Restores the spirit of `bet_max_finale_gain: $8,000`, plus whatever they also take on the R3 ladder. No new odds UI. 60/60 never fires likely-win on the 31–34% billed bosses.

2. **Unlock R3, story / billed finale only, no cap, even money.** The late promoter beat, after wholesale ends. Profit is capped by the four billed finale races: 80/80 about +$7.1k, mixed +$1.9k / +$4.1k (60/80 may not bother), 60/60 +$0. Tightest story alignment with “Reiko cut you off, so you can make extra cash betting.” Weakest “is betting worth it for mixed?” of the even-money passes.

3. **Either unlock, any or wild, cap 8, even money.** Lets mixed fire a handful of high-WR grinds after (or before) the T4 shop. About +$11–15k for 80/80 and mixed, +$6–8k for 60/60 (they will bet 10-turn wilds once WR ≥ 65%, which the scaled finale wilds are). Clearly worth it for mixed, still well under a T4 package. Cap 4 is the same idea at +$3–7k (R3 / any / cap 4 is borderline for 60/80). Cap 16 leaks to ~$20–27k.

4. **Either unlock, any or wild, no cap, true fair odds.** Flavor of betting on every favorite grind without a printer, *if* the posted line is honest on 99% shorts. Mixed profit would sit near $0 plus variance — “worth it” only as a toy. The clamped [0.05, 0.95] implementation in this sim is **not** that rule; it leaves 80/80 about +$8.5k.

5. **Unlock R3, wild only, cap 8, even money.** Late beat plus “you make it up on wilds, not on the billed Myth fights.” 80/80 +$13.0k, mixed +$7.1k / +$9.9k, 60/60 +$6.3k. Worth it for mixed. Same math as (3) with a cleaner eligible-race story.

What does **not** pass and should not be combined without one of the caps or fair odds: **uncapped even money on any race or on wilds**, at either unlock, at any T4 price in the sweep. That is a $150k–$256k printer. Losing wholesale and adding T4 do not soak it.

### Criteria 1–10 re-check (Variant C + wholesale + T4)

Campaign criteria **1–5, 7, 9, 10** are unchanged in structure: same XP, same 1.07 caps, same boss r, same aero rule. Wholesale on T2/T3 after R1 only makes the R2–R3 shop easier (still fills the 1.07 cap; debt still clears by end of R1 on the mixed walk — criterion 6’s debt half still holds). T4 floor L47 is immediately after the campaign cap L46, so there is no dead locked stretch (7).

**Criterion 8** was a fail on T3-only (F3/F4 unwinnable for 60/60, ugly for everyone). With T4 in this design and any price in the sweep, no-bet players can fund enough incremental T4 to sit on the designed band at every finale step, including 60/60 at 31–37%. **Pass**, with the 0.003 F2 r undershoot noted above.

**Criterion 6 (betting cannot break the economy)** is **conditional on the levers**: fail for uncapped even-money grind/any at either unlock; pass for the story-only, cap-4/8, and true-fair combinations in the short list. T4 is a leftover sink, not a printer sink.

Default constants are not locked to one combination. The sweep and the floor live on `proposed_constants.json` as `mods.price_T4_upgrade_sweep` and `money.betting_levers_factorial_2026_11_13`.

## Austin's betting pick (2026-11-13) — true fair odds

Austin locked the betting rules: **unlock after R2**, **true fair odds** with net payout `(1-p)/p` of the stake and **no 0.95 clamp**, **any race eligible**, **no bet-count cap**, stakes **$500–$2,000**. The late promoter beat and an R3-unlock betting package are dropped. Wholesale is unchanged (0.20 off list from end of R1 through end of R3) and does not apply to T4.

Sim: `run_betting_fair.py`, `betting_fair.json`. 4,000 trials, T4 regular $8,000, unlock R2 only. Likely-win bets max when WR ≥ 65%; always-max bets every eligible race with p in (0, 1). Refuse a bet at p = 0 (undefined odds) or p = 1 (net 0). Ruin = a lost bet left cash at $0; a shop leftover of $0 is not ruin. No-bet end cash: 60/60 $127,315; mixed $118,680; 80/80 $93,498.

| Policy | Odds | 80/80 profit mean / p50 / p10 | 60/80 | 80/60 | 60/60 | 80/80 cash p50 / p10 | Ruin 80/80 · 60/80 · 80/60 · 60/60 | C6 |
|---|---|---:|---:|---:|---:|---:|---|---|
| likely-win | fair | −$24 / +$682 / −$5,098 | −$92 / +$500 / −$12,173 | +$73 / +$753 / −$9,250 | −$127 / +$396 / −$12,660 | $94,180 / $88,400 | 0.25% · 0 · 0 · 0 | **PASS** |
| always-max | fair | −$85 / +$127 / −$6,286 | −$322 / +$491 / −$16,131 | −$3 / +$343 / −$15,638 | −$205 / +$1,671 / −$40,102 | $93,624 / $87,211 | 0.42% · 0 · 0 · 0.17% | **PASS** |
| likely-win | house 5% | −$360 / +$528 / −$5,416 | −$1,490 / −$887 / −$13,326 | −$979 / −$460 / −$10,367 | −$1,897 / −$1,397 / −$15,132 | $94,025 / $88,082 | 0.23% · 0 · 0 · 0.03% | **PASS** |
| always-max | house 5% | −$388 / −$139 / −$6,379 | −$2,505 / −$1,861 / −$17,873 | −$2,209 / −$1,642 / −$17,349 | −$7,127 / −$5,524 / −$44,949 | $93,358 / $87,119 | 0.17% · 0 · 0 · 0.05% | **PASS** |

True fair mean profit is noise around $0 (largest cell mean is +$73). Always-max has a fatter left tail, especially 60/60 (p10 profit −$40k), because they fire long-priced billed retries; ruin stays under 0.5%. The 5% house edge (`0.95 × (1-p)/p`) is a comparison only — EV ≈ −0.05(1−p)×stake per bet, about −$360 to −$1,900 likely-win and −$388 to −$7,100 always-max. **Criterion 6 passes.** No finale WR jump vs no-bet.

If the game posts p from the same model the player can see, expected value is zero and the player can only exploit noise. +EV appears if a hidden factor makes posted p understated: live heat or load the line ignores, a coarser r-table than the combat model, odds that assume an average profile when the player is 80/80, a rounded or bucketed line, or a race the player can reset after seeing a bad start before the bet locks. Production must use honest shorts (no 0.95 clamp): that clamp was itself a quiet +$8.5k printer for 80/80 on 99% finale grinds.

## Pre-finale story arc

The stretch from L46 to the finale caps (L63 / 76 / 95 / 114) was 31 / 25 / 34 / 34 grind wins with no story races. That fails the mixed 8–10-to-cap target and leaves 80/80 story-only three-plus levels behind with no T4 ceremony. Sweep: 2–6 story races before F1, 0–2 between finale steps, lengths 10/20/30, story_fill 0.75–0.85, r ladders, T4 unlock on a pre-F1 story race, purses $2,500 / $3,375 / $5,000 / billed $10,800. Sim: `run_finale_arc.py`, `finale_arc_recommended.json`. Opponents are placeholders for Desmond and Nathaniel.

**What the sweep showed.** Zero inter-step story races fail: mixed still need 25–34 grinds for F2–F4, and 80/80 story-only falls over on F2–F4 (0% without enough XP). One or two inter-step races plus story_fill 0.80 of each cap-to-cap gap is enough; two leaves room for a mid-step wall. Three to six pre-F1 races all work for XP; four is the campaign-shaped ladder (10, 20, 20, 30). Fill 0.80 matches R3 and gives mixed 6–7 grinds to each step cap (“8–10 or fewer”); fill 0.75 is 8–9 if the cap grind should feel identical to a campaign round. Post-R3 10-turn wilds are tuned to r = 1.12 vs current combat (purse $742.50) so 60/60 stays in the 65%+ band — the old finale grind B = C/1.18 was about r = 1.03 at the start of a gap and dropped 60/60 to ~40%.

### Recommended race list

Story fill **0.80** of the official cap-to-cap XP, weights (0.18, 0.24, 0.26, 0.32) before F1 and (0.40, 0.60) between steps. **T4 unlocks on P1**, still floor L47. Wall races (P3, M12, M22, M32) are 20-turn mid-step fights with B set so a mixed player arriving without a pre-race grind sits near r = 1.02 (Touge) or 1.00 (Wangan / Street). Openers are easy 10-turns at r* = 1.18. Billed finale r and B are unchanged.

| ID | Placement | Dist | T | r* | Opponent B | XP share (of step fill) | Purse |
|---|---|---|---:|---:|---:|---:|---:|
| P1 | After R3, before F1 | Touge | 10 | 1.180 | 382.78 | 0.18 | $2,500 |
| P2 | pre-F1 | Touge | 20 | 1.149 | 409.03 | 0.24 | $3,375 |
| P3 | pre-F1 wall | Touge | 20 | 1.020 | 483.25 | 0.26 | $3,375 |
| P4 | pre-F1 gate | Touge | 30 | 1.086 | 461.15 | 0.32 | $5,000 |
| F1 | Billed finale 1 | Touge | 30 | 1.066 | 494.8 | 0 | $10,800 |
| M11 | Between F1 and F2 | Wangan | 10 | 1.180 | 438.11 | 0.40 | $2,500 |
| M12 | F1–F2 wall | Wangan | 20 | 1.000 | 546.53 | 0.60 | $3,375 |
| F2 | Billed finale 2 | Wangan | 30 | 1.040 | 566.3 | 0 | $10,800 |
| M21 | Between F2 and F3 | Street | 10 | 1.180 | 485.77 | 0.40 | $2,500 |
| M22 | F2–F3 wall | Street | 20 | 1.000 | 625.54 | 0.60 | $3,375 |
| F3 | Billed finale 3 | Street | 30 | 1.053 | 648.2 | 0 | $10,800 |
| M31 | Between F3 and F4 | Touge | 10 | 1.180 | 564.89 | 0.40 | $2,500 |
| M32 | F3–F4 wall | Touge | 20 | 1.020 | 713.17 | 0.60 | $3,375 |
| F4 | Billed finale 4 | Touge | 30 | 1.066 | 741.9 | 0 | $10,800 |

P1 is the T4 beat (placeholder: Desmond / Nathaniel). 80/80 enters it at L43, leaves at L48, and can buy the first T4 immediately. Mixed already at L46 buy several T4 from leftover after the same race. Billed fights still grant no XP; the cap grind after the step's story races is what puts mixed and 60/60 on the designed finale r.

### Grind counts and win rates

Wall / to-cap / total grind wins per step (official XP path):

| Profile | pre-F1 → F1 | F1 → F2 | F2 → F3 | F3 → F4 | End L / cash / T4 |
|---|---|---|---|---|---|
| 80/80 story-only | 0 / 0 / **0** | 0 / 0 / **0** | 0 / 0 / **0** | 0 / 0 / **0** | L111 / $31,075 / 5+aero |
| 60/80 mixed | 5 / 1 / **6** | 0 / 6 / **6** | 1 / 6 / **7** | 3 / 4 / **7** | L114 / $77,790 / 5+aero |
| 80/60 mixed | 3 / 4 / **7** | 3 / 3 / **6** | 5 / 2 / **7** | 1 / 6 / **7** | L114 / $78,533 / 5+aero |
| 60/60 hard | 10 / 0 / **10** | 8 / 0 / **8** | 10 / 0 / **10** | 8 / 0 / **8** | L114 / $93,850 / 5+aero |

Mixed totals are 6–7 a step, inside “8–10 or fewer.” Each mixed profile hits a 3–5 race wall on two or three of the four steps; the other mid-races are a 0–1 nudge. 60/80 does not really wall on Wangan (district WRs are generous at these r); 80/60 takes that one. 60/60 uses the mid-step wall to climb all the way to cap (8–10 grinds) and still finishes every billed fight at the designed 30–37% band.

80/80 story-only never grinds, arrives three levels under each billed cap (L60 / 73 / 92 / 111), and stays ≥ 67.5% hard on every story and billed race (the low is P3 at r = 1.012; billed fights are 78.7 / 79.7 / 80.8 / 78.7). They fund incremental T4 from story purses: first slot after P1, two regulars by P4, five regulars by F2, full 5+aero by F3. End leftover is $31k vs $93k on the old 106-wild finale, so T4 still sinks cash without a grind printer.

### Criteria 1–10 re-check

1–5, 7, 9, 10 unchanged in the campaign proper (same XP through R3, same 1.07 caps, same boss r, same aero rule). **2** now holds after R3: mixed have one mid-step wall of 3–5 grinds on most steps and 6–7 to each finale cap, flat across the four steps. **3** holds: 80/80 story-only is ≥ 67.5% hard on the new arc and the billed fights (well above 50%), including Touge uphill. **4** holds for post-R3 10-turn wilds at r = 1.12 (60/60 about 75–88% depending on district; mixed higher). **6** debt half unchanged; betting half passes under the locked fair-odds rules above. **8** holds: mixed and 60/60 reach every finale cap with T4 and the designed 90% / 30% band (80/80 at cap would still be 89.6–93.9 / 60/60 30.9–37.4; story-only 80/80 is a few points under cap and still ~79%). T4 price is not locked; these walks use the $8,000 representative regular.
