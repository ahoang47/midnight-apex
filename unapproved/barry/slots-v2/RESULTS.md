# slots-v2 — Austin's 2 POW / 2 EN / 2 HAN slot layout, window + aero, grind wall, economy (NOT approved)

> **2026-11-11 10:58 PM PT: two parts are APPROVED and live** (see `design/notes/slots-v2/README.md`): the `KNOT_WINDOW_105` r = 1.00 knot 0.68 → 0.67, and the aero free pool ≤ 10% (`AERO_FREE_POOL_MAX_FRACTION`). Everything else here is still not approved.

Barry, 2026-11-11. **Draft for Austin's review, not approved.** Main runs 8:55–10:36 PM PT, follow-ups 10:40–10:50 PM PT. The model is the live visible-QTE sim (`qte_zone_width`, `expected_hit_quality`, `QTE_SKILL_SIGMA_OVER_A0`). That math is unchanged since `4cb5401`, and `f0efecf` only averages the phase scores. The follow-ups ran at `4322b31` and reproduce the `results.json` finale cells exactly. **Nothing in `sim/` was changed.** Every "after" number comes from patching a constant in-process.

Every number below comes from a file in this folder. The file is named next to each number.

## Setup

- **Layout (Austin, 2026-11-11):** 6 slots = POW, POW, EN, EN, HAN, HAN. Each slot holds a mod of its own category at that slot's top unlocked tier. The tier values follow the slots-v1 scheme-C schedule (`../slots-v1/slots_model.py`): one tier per story win, a 6-mod restock at round openings, and mods summing to `MOD_SHARE_OF_REF × ref` exactly.
- **Secondary split (placeholder):** 100/0/0, 80/10/10, 70/20/10 (primary / secondary / tertiary). With 70/20/10, each mod comes in two sidegrade variants, depending on which other stat gets the 20.
- **Window mod:** +75% zone, any slot (that slot's stat mod is removed), at most one, with the zone capped at 1.15 × w0 (slots-v1 candidate).
- **Aero (design/07 §6.3):** goes in any slot, at most one, counts inside the 105% cap. Its value is (1 − pool) × the slot's tier, using the slot's split, plus pool × tier assigned freely to POW/HAN/EN on a quarter-step grid. **Retuned to the best allocation for every race** (upper bound; respec cost ignored). Pool sizes 10/20/30% (placeholder). Available from the second R2 crew (`DEBT_CLEAR_AFTER` = (2, 1)) and in the finale.
- **Oracle (share-aware):** off-balance builds change deck weights, so clash-count banks were generated on a share grid (`grid.py`/`gen.py`: 244 points, step 0.025, shares 0.15–0.65). Each grid point is 3 districts × seeds 20261113/14/15 × 10/20/30 turns, N = 4,000, q_read 0.6, using the official seed formula. Off-grid builds are interpolated barycentrically. POW/EN payoff multipliers and HAN's QTE effect are applied analytically (`model.py`).
- **Validation (`validate.json`):** the balanced grid point reproduces the official Wangan and Street banks bit-for-bit. Interpolation vs exact banks at 4 off-grid builds × r 1.0355/1.05 × 3 profiles: ≤ **0.20 pp** on the 9-bank mean and ≤ 1.01 pp on a single bank.
- **Statistical bar (same as asked):** N = 4,000 per bank, seeds 20261113–15 × 10/20/30 turns = **9 paired banks**.
  - **dominant / dominated:** mean Δ ≥ +5 pp / ≤ −5 pp, with the same sign in all 9 banks.
  - **even:** |mean| < 1.5 pp.
  - Otherwise lean+ / lean−.
  - "No-brainer" means dominant.
- **Clear test:** official, pooled mid ≥ 50, where mid = (min + max)/2 of the 9 bank win rates (`prog.py`).
- **Key cells (`cells.py`):** mature #2 skipped, boss skipped and boss at target for all 9 crews, scored on the crew's own district, plus Myth #2 and Summit skipped. That's 29 cells × 3 splits × 3 profiles = 261 (`results.json`).
- **Profiles:** weak / average / strong σ are placeholders.

## Recommendation

1. **Keep Austin's 2/2/2 layout.** It is what stops the real no-brainer: with free category choice, stacking POW or EN is dominant in 62 of 87 average cells and HAN is never part of the best stack (Q3).
2. **The secondary split barely matters.** Grind counts are identical under all three splits (Q2). Use 100/0/0 or 80/10/10 for clarity. 70/20/10 adds a small sidegrade choice (≤ 3.9 pp) but lifts the Summit to 49.17 for average players, which lets aero ≥ 20% clear it (Q5).
3. **Window +75% / 1.15 cap / max one: keep it, but it breaks the grind wall** at two average opener bosses (49.14 → 50.30). The smallest fix found: lower `KNOT_WINDOW_105`'s r = 1.00 knot from **0.68 to 0.67**. That clears the violation and leaves every balanced grind count unchanged (141/153/121) (Q7).
4. **Aero: cap the free pool at 10% (placeholder).** Aero is never dominant, but it is never worse than the mod it replaces, so price it above a regular mod. At 30% (100/0/0) it still clears R3 Street's boss after the knot fix, and at 20–30% (70/20/10) it clears the Summit.
5. **Prices: use the grind-matched shape (P2)** so weak and average players can't pre-buy, and decide what to do about strong players' 34 money races (Q6).
6. **Open violation for Austin:** for strong players, the newly unlocked mod alone clears R1 Wangan and R2 Touge mature #2 (49.02 → 53.11 / 53.10). The knot fix doesn't remove it (Q5).

## Key numbers

| Item | Value | File |
|---|---|---|
| Max total over all loadouts, every story point | 105% at all 63 points (max deviation 2.2e−14 pp) | `check105.json` |
| Exhaustive loadouts checked per point | 12,500 – 262,144; 0 over 105%; max = best-per-slot | `check105.json` |
| Grind races, balanced 2/2/2 (weak / avg / strong) | 141 / 153 / 121, all 3 splits | `results_grind.json` |
| + window (+75%, 1.15 cap) | 141 / **140** / 121 (avg clears R2 Wangan and R3 Street bosses at 50.30) | `results_grind.json` |
| + aero 10/20/30% without a window | 141 / 153 / 121 for every pool and split | `results_grind.json` |
| + aero with a window | 141 / 140 / 121 (R3 Street boss 50.54 / 50.68 / 51.14 at 10/20/30%, 100/0/0) | `results_grind.json` |
| Aero vs the mod it replaces (all 51 eligible cells per profile) | +0.03 … +2.85 pp, never negative, never dominant | `results.json` |
| Window best vs best fixed | weak −5.52 … +4.10; avg −35.18 … +2.99; strong −24.13 … −3.46; never dominant | `results.json` |
| Fix: knot 0.68 → 0.67 | balanced 141/153/121 unchanged; window avg 153 (boss 49.07); aero30 avg (100/0/0) 146 | `results_parity*.json`, `results_aero_knot.json` |
| Dead wins (no stat tier possible) | 9 (1 per crew); removing them all costs ≥ +28 avg grind | `results_alloc.json` |
| Price P2 (grind-matched), per purchase | 1.73–1.91 race-units (round openers), 3.17–3.67 (others) | `results_price.json` |

## Q1. Is the max over all loadouts ≤ 105%, and does it only just reach it?

**Yes.** Source: `check105.py` → `check105.json`.

- **Exhaustive check.** I checked 5 story points: R1 Street boss, R2 Wangan kid, R2 Street boss, R3 Street mature #2 and R3 Wangan boss.
  - Each was run under all 3 splits, with aero added where it's unlocked.
  - The catalog was each slot's newest 6 tiers (×2 sidegrade variants under 70/20/10), plus the window mod (0 stats) and the aero part (total = the tier).
  - That is 12,500 to 262,144 loadouts per point. Every point has max total = **105.000000%**, `over_105` = 0, and `reaches_105` = true.
  - Stat shares stay within 0.2737–0.4012, so 0 loadouts fall outside the 25–50% build limits.
- **Austin's 36-mod example (6 stat mods per slot, no window or aero).** I checked 6⁶ = **46,656** loadouts at R2 Touge kid #1 (the first point where every slot has 6 tiers) and at R3 Wangan boss, under 100/0/0 and 80/10/10. Max is 105.0% and 0 loadouts are over.
- **Every story point (63).** The best-per-slot total equals 105% to within 2.2e−14 pp.
- **Why best-per-slot is the max:**
  - Total % = (SP + Σ over slots of the mod's stat total) / reference.
  - Each slot is chosen independently from its own catalog, and the sum has no cross-slot terms (no set bonuses, no clamps).
  - So the max of the sum is the sum of the per-slot maxes. The brute force confirms it at every checked point: `max_total_pct` = `separable_best_per_slot_pct`.
  - The secondary split moves points between stats, not the total. A window mod has 0 stats, and an aero pool redistributes the tier's points without adding any. Neither can beat the top stat tier.
  - I also tried a non-additive variant (stat above the 50% share doesn't count). It gives the same 105% because no loadout gets near 50%.
  - **This proof breaks if mods ever get set bonuses, negative stats, or a clamp that binds.** The exhaustive check is kept for that case.

## Q2. Secondary split (placeholder 100/0/0, 80/10/10, 70/20/10)

- **Grind is identical under every split** for each policy. Balanced is 141/153/121, window 141/140/121, aero without a window 141/153/121, aero with a window 141/140/121 (`results_grind.json`).
- **Within the 2/2/2 layout:**
  - 100/0/0 and 80/10/10 each allow exactly one stat loadout (spread 0).
  - 70/20/10's sidegrade choice is worth at most **3.88 pp** (best vs worst variant). It is never dominant (86 even, 1 lean+ of 87 best-variant verdicts).
  - The 70/20/10 "layout" policy (free sidegrade choice) gives 141/153/121, the same as balanced.
- **Where it matters:** at Summit skipped, the best 70/20/10 variant lifts the average player to **49.17** vs 46.97 (100/0/0 and 80/10/10). That margin is what aero ≥ 20% crosses (Q5).

## Q3. Category mix: no-brainer, dead category, HAN stacking?

- **Austin's layout fixes the mix (2/2/2),** so there is no mix choice to be a no-brainer. The only choices are the 70/20/10 sidegrade (≤ 3.88 pp), the window slot and the aero slot.
- **Window slot:** the best slot to give up is EN or HAN, never POW, for average players (EN 47, HAN 40 of 87) and strong players (EN 51, HAN 36). Weak players pick POW 6 times. So POW slots are worth the most per point and EN/HAN the least, but every category stays in use.
- **Counterfactual: any category in any slot** (`free_mix`, not Austin's layout):
  - **Stacking is a no-brainer.** The best free mix is dominant over 2/2/2 in **62 of 87** average cells (11 weak, 16 strong). It is mostly 6 POW (51 average cells) or 6 EN / 1P-5E (30). Best-mix gains are up to +19.97 pp for average players.
  - **HAN is the dead category.** It is never in the best stack under 80/10/10 or 70/20/10. Under 100/0/0 it's at most 1 slot (19 of that split's 87 cells, all profiles together).
  - **Stacking HAN does not dominate.** 6 HAN is never the best mix. It is the worst mix in 30 of 87 cells per profile, ranging −21.58 … +2.43 pp for average players.
  - **Conclusion:** the fixed 2/2/2 layout is what keeps HAN alive and stops POW/EN stacking.

## Q4. Window and aero

**Window (+75%, any slot, max one, 1.15 × w0 cap):** never dominant for any profile in any of the 261 cells.

| Profile | Verdict counts (87 cells) | Δ vs best fixed |
|---|---|---|
| Weak | lean+ 51, even 30, lean− 5, dominated 1 | −5.52 … +4.10 |
| Average | even 36, lean− 42, lean+ 3, dominated 6 | −35.18 … +2.99 |
| Strong | lean− 53, dominated 34 | −24.13 … −3.46 |

In the finale it is dominated for average and strong players: Myth #2 25.6 vs 44.7, Summit 15.1 vs 47.0 (average, 100/0/0). It stays a skill-dependent choice: it helps weak players, sits even/lean− for average, and costs strong players. **But** it is decisive at two average walls (Q5).

**Aero, retuned to the best allocation every race:** **not a no-brainer by the bar, but a free upgrade.** Across the 51 eligible cells per profile, aero vs the fixed mod it replaces is:

| Pool | Weak | Average | Strong |
|---|---|---|---|
| 10% | +0.03 … +0.56 (even 51) | +0.11 … +1.01 (even 51) | +0.06 … +0.32 (even 51) |
| 20% | +0.06 … +0.70 (even 51) | +0.23 … +2.03 (even 49, lean+ 2) | +0.13 … +0.66 (even 51) |
| 30% | +0.12 … +0.90 (even 51) | +0.35 … +2.85 (even 43, lean+ 8) | +0.18 … +1.09 (even 51) |

- **Never negative and never dominant.** Since it can't be worse, it is always worth fitting. design/07's "higher price or a slightly smaller total" is therefore needed.
- **The best retune is almost always all-POW** (the `pool->P1.00` labels in `results_grind.json`). It is a POW top-up, not a counter-build tool.
- **Aero plus a window** behaves like the window alone: the same verdict pattern, and strong players are always lean−/dominated.

## Q5. Grind wall: does a newly unlocked mod, with no grinding, clear a wall?

Official pooled test. Mid with the newest tier equipped at the skip state (`results_econ.json`, `results_econ_cleared*.json`).

**Balanced 2/2/2, no window or aero.** No wall is cleared by the new mod for weak or average players.

| Profile | Walls that force grind | Mid with new mod | Margin to 50 |
|---|---|---|---|
| Weak | every mature #2 / boss | 9.64 – 20.02 | 29.98 – 40.36 |
| Average | mature #2 (9 crews) | 46.93 – 47.14 | 2.86 – 3.07 |
| Average | crew bosses (9 crews) | 48.99 – 49.14 | **0.86 – 1.01** |
| Strong | R1 Wangan, R2 Wangan, R2 Touge old heads | 39.80 – 44.48 | 5.52 – 10.20 |
| Strong | R3 Touge mature #2 | 49.02 | **0.98** |

**Violations:**

| # | Who | Wall | Cause | Before → after | File |
|---|---|---|---|---|---|
| V1 | strong, balanced | R1 Wangan mature #2 | newest tier alone | 49.02 → **53.11** | `results_econ_cleared.json` |
| V2 | strong, balanced | R2 Touge mature #2 | newest tier alone | 49.02 → **53.10** | same |
| V3 | average, window +75% (all splits) | R2 Wangan boss | window@HAN | 49.14 → **50.30** (70/20/10: 50.57) | `results_grind.json` |
| V4 | average, window +75% (all splits) | R3 Street boss | window@HAN (aero+window up to 51.14) | 49.14 → **50.30** | same |
| V5 | average, 70/20/10, aero 20/30% | Summit skipped | aero | 49.17 → **50.53 / 51.11** | `results.json` |

- **V3/V4 move the grind, they don't remove it.** The next crew's mature #2 grows from 7 to 9 and from 8 to 10, so the net is −13 (153 → 140).
- **V1/V2 survive the knot fix:** 47.86 → 52.49 and 47.84 → 52.67 (`results_econ_cleared_knot067.json`). Candidate fixes, none of them run: P2 prices (Q6) so the tier can't be afforded before mature #2, a `TIER_LEVEL_FLOOR` on that tier, or unlocking that tier after mature #2.
- **Pre-existing, not caused by mods:**
  - Strong players clear the finale at the skipped state with balanced mods (Myth #2 82.43, Summit 83.12). The finale isn't wall-tested because official policy always grinds to the cap (86/14). This is the existing "finale above r 1.05" item.
- **District sensitivity (not the official test):** scored on the crew's own district, average boss-skipped walls already sit at the line with balanced mods: R2 Wangan 50.37, R3 Wangan 49.95–50.02. Window or aero lifts the R1/R2/R3 Touge bosses to 50.0–51.3 (`results.json`).
- **Margins under 0.3 pp** (50.14, 50.30, 49.96) are within about 1.5× the 0.20 pp interpolation error. Treat them as "at the line".

## Q6. Economy: prices that can't be paid on unlock and that overlap the XP grind

**Payouts are TBD** (design/07 §5.1), so money is counted in **race-income units: every race pays 1 unit** (placeholder; boss purses will be bigger).

Inputs come from `results_econ.json` (default crew order, balanced 2/2/2, average-player schedule):
- every crew has 7 story wins and 1 dead win;
- the round-opening crews (R1 Touge, R2 Wangan, R3 Street) make 11 purchases (a 6-mod restock plus 5 singles), and the other crews make 6;
- forced XP grind per crew (weak / average / strong) is R1 Touge 12/13/0, R1 Wangan 12/13/19, R1 Street 13/13/0, R2 Wangan 12/16/28, R2 Street 14/14/0, R2 Touge 14/14/22, R3 Street 14/18/0, R3 Touge 15/16/18, R3 Wangan 15/16/0.

The constraints:
- **Floor:** a single tier must cost > 1 unit, so the win that unlocks it can't pay for it alone.
- **Overlap:** a crew's spend must be ≤ its forced races (7 + grind).
  - Weak/average players have 1.73–3.83 units per purchase.
  - **Strong players have only 0.64 (round-opening crews) or 1.17 (others) in the 5 crews where they never XP-grind.**
  - **No single price satisfies both rules for all profiles.**

Two placeholder curves (`price_curve.py` → `results_price.json`; the wallet carries over between crews):

| | P1 "strong-safe" | P2 "grind-matched" (recommended shape) |
|---|---|---|
| Price | single tier 1.1 units; restock 0.25 per mod | per crew = min(weak, average) forced income ÷ purchases: **1.73** (R1 Touge, R2 Wangan), **1.91** (R3 Street), **3.17** (R1 Wangan), **3.33** (R1 Street), **3.5** (R2 Street, R2 Touge), **3.67** (R3 Touge, R3 Wangan) |
| Races of income per purchase | 1.1 | 1.73 – 3.67 |
| Spend per crew | 6.6 – 7.0 | 19 – 22 |
| Extra money races (weak / avg / strong) | 0 / 0 / 0 | 0 / 0 / **34** |
| Wallet left after R3 (weak / avg / strong) | 123.4 / 135.4 / 89.4 | 0 / 12 / 0 |
| Can't buy on unlock? | Only for strong. Weak/avg bank 12–18 units per crew, so they buy everything the moment it unlocks | Yes for weak/avg (the wallet tracks the grind); strong runs short |

As a curve, P2 is about 1.7–1.9 units per purchase in round-opening crews (the restock spreads the cost) and 3.2–3.7 in the rest. It rises gently with the round because forced grind rises: R1 19–20 → R3 21–22 units per crew. **Austin's call:** either accept 34 money-only races for strong players (their XP grind is 121, the lowest), or use P1 and gate unlocks with `TIER_LEVEL_FLOOR` / a restock delay instead of price. Per-race purse sizes (boss vs grind) and the 9 dead wins are not modelled.

## Q7. Which constant breaks, and what is the smallest fix?

**What breaks:** the window rule (+75%, 1.15 × w0 cap) combined with the zone curve `KNOT_WINDOW_105` (live knots (1.00, 0.68), (1.05, 1.00)). At the opener-boss skip state (r 1.0374), the cap doesn't bind. The widened zone outweighs the lost slot and lifts average players from 49.14 to 50.30 (V3/V4).

Sweeps, all in-process (`results_breaks.json`, `results_breaks2.json`, `results_window_margin.json`, `results_parity.json`):

| Knob | Values tried | Result for average (boss mid / grind) |
|---|---|---|
| `ZONE_CAP` | 1.15, 1.10, 1.05, 1.04, 1.03, 1.02 | both bosses still clear (grind 140; boss 50.30 at 1.15) |
| `ZONE_CAP` | 1.01 | 49.96 / 153. That is 0.04 pp below the line, which is fragile |
| `ZONE_CAP` | 1.00 | the window is never chosen (49.14 / 153) |
| `WINDOW` size | 0.70, 0.65, 0.60, 0.55, 0.50, 0.25 | grind 153 at every size. At 0.70/0.60/0.50 the window isn't chosen at those bosses (49.14), so it becomes dead content there |
| `KNOT_WINDOW_105` r = 1.00 knot | **0.67** | window 49.07 / 153; balanced 141/153/121 **unchanged** |
| same | 0.66, 0.65 | fixes it, but strong grind changes 121 → 112 |

**Proposed smallest fix (draft, not applied): r = 1.00 knot 0.68 → 0.67** (`results_parity_after.json`).

| r | 0.95 | 1.00 | 1.0004 | 1.02 | 1.037 | 1.05 |
|---|---|---|---|---|---|---|
| Zone width before (×w0) | 0.3448 | 0.5802 | 0.5829 | 0.7243 | 0.8687 | 1.0 |
| Zone width after (×w0) | 0.3448 | 0.5698 | 0.5725 | 0.7170 | 0.8649 | 1.0 |

Grind after the fix, all three splits:
- balanced, window and aero 30% without a window: 141/153/121;
- aero 30% with a window: 141/153/121 under 80/10/10 and 70/20/10, but **146** for average under 100/0/0, because R3 Street boss is still cleared at 50.14 (`results_aero_knot.json`);
- aero 10% and 20% (100/0/0, average): 153.

At the finale after the fix (`results_finale_knot.json`), 70/20/10 aero 20/30% still clears the Summit (50.41 / 50.97), and aero 10% doesn't (49.39). Under 100/0/0 and 80/10/10, aero ≤ 30% stays below 50 (max 49.65). So the full fix is **knot 0.67 plus an aero pool ≤ 10%**. Alternatively, keep 20% and drop 70/20/10.

**Difficulty curve / dead wins (`results_alloc.json`):**
- Removing the 9 dead wins means changing `CAP_ALLOC_CREW` / `CAP_ALLOC_ROUND_OPEN` so neither has a zero entry.
- The cheapest zero-dead option, e.g. CREW (2,2,3,2,1,1,1) with RO (12,3,3,3,0.5,0.5,0.5) or (18,4,4,4,1,1,1), gives 150/181/121, i.e. **+28 average grind**.
- Every zero-free option costs at least +28 average grind (181–210 vs 153). Options with 2 dead wins left cost +26 (179).
- **Recommendation:** keep the live allocation and give the 9 dead wins window, aero or sidegrade unlocks instead.

## Placeholder caveats

- σ for each profile, the window size and cap, the aero pool, the secondary splits and every payout are placeholders. Re-run after playtest.
- The aero retune is free and optimal before every race (upper bound). With `RESPEC_COST` it's weaker.
- Economy uses 1 unit per race, crew-level wallet timing, and the default crew order (free order reshuffles which crews strong players skip).
- Cells use the average player's official progression state for every profile (as in slots-v1). Grind counts use each profile's own progression.
- The slots-v1 opener-boss numbers (48.85 → 50.06) came from the balanced-deck oracle. v2's share-aware oracle gives 49.14 → 50.30.

## Reproduce

From this folder. It needs numpy, `../slots-v1/` (schedule and oracle), `/workspace/barry-drafts/lines-v1` (`lib.py` and the official banks) and the repo sim at `/workspace/midnight-apex/sim`. `counts/` (≈ 44 MB, 244 `.npz` files) is not committed. Rebuild it with `python3 grid.py` (≈ 25 min on 8 cores).

```
python3 grid.py && python3 validate.py
python3 check105.py; python3 cells.py; python3 prog.py; python3 econ.py; python3 econ_cleared.py; python3 econ_cleared.py --knot067
python3 breaks.py; python3 breaks2.py; python3 alloc_sweep.py; python3 parity_sweep.py; python3 parity_after.py
python3 aero_knot_check.py; python3 finale_knot_check.py; python3 price_curve.py
```

`results_window_margin.json` has no generating script. It was written by the interrupted run, and its rows match `results_breaks*.json` / `results_parity.json`.
