# slots-v1 — mod slot schemes with window-only mods competing for slots (NOT approved)

Barry, 2026-11-11 (run 5:55–6:05 PM PT). **Draft for Austin's review, not approved.** Base: `proto-build` @ `4cb5401` (live visible-QTE model: `qte_zone_width`, `raw_qte_score`, `expected_hit_quality`, `QTE_SKILL_SIGMA_OVER_A0`; progression @ free crew order, 153 grind races / 162 levels). Nothing in `sim/` was changed.

Every number below comes from `results.json`, `results_sizes.json`, `results_grind.json` or `results_cap.json` (printed by `summarize.py` into `summary.txt`). Placeholder caveats are listed at the end.

## Setup

- **Oracle:** the official clash-count banks, the same ones behind `sim/config/winrate_n4000.json` and qte-v1 (`wr_shortcut.py`, copied unchanged from `design/notes/qte-v1/`):
  - Banks: Touge from `final-v1/counts_n4000.npz` masked to Touge tracks; Street from lines-v1 `SSA`; Wangan from lines-v1 `AAD`.
  - Sampling: q_read 0.6, **N = 4,000 races per bank**, **seeds 20261113/14/15 × 10/20/30 turns** = 9 banks per district (36,000 races per district cell, 108,000 for pooled).
  - Settings: `KAPPA_BY_LENGTH`, opponent QTE 1.0.
  - The player's q_eff is `expected_hit_quality(σ_profile, qte_zone_width(r, window_mod))`, using the live 4cb5401 functions with balanced HAN.
- **Precision:**
  - One bank's 95% half-width is ≤ 1.55 pp at 50%.
  - The 9-bank mean used for every verdict is ≤ 0.52 pp.
  - All trade comparisons are *paired*: the same banks are used with and without the window mod, so the differences are tighter than either rate.
- **Profiles (placeholder σ):** weak, average, strong (`QTE_SKILL_SIGMA_OVER_A0`; E[s] = 0.4 / 0.6 / 0.8 at the default zone).
- **Cells:** taken at the official progression state (average player, forced grind, all stat mods; reproduced here at 153 races).
  - Mature #2 skipped and boss skipped use r at the story level.
  - Boss at target uses r = 1.05.
  - Finale cells: Myth #2 skipped (r 1.0336) and Summit skipped (r 1.0359).
  - Each campaign cell is evaluated for all 9 crews, scored on that crew's district. Finale cells are scored on their own district.
- **Window mod:** multiplies the zone, `MatchConfig.qte_window_mod` semantics. The QTE is a function of the race's fixed r and the equipped mods only; it never reads mid-race position (rule 4).
- **Trade:** equipping one window mod removes the **smallest** equipped stat mod (the cheapest slot to give up), so r drops by that mod's value divided by the opponent budget. Loadouts with up to 3 window mods (capped at n−1) were also searched; stacking was never the best loadout in any run.
- **Verdict per cell:** based on the paired Δ = window-loadout win rate − all-stat win rate.
  - **dominant**: mean Δ ≥ +5 pp and Δ > 0 in all 9 banks.
  - **dominated**: mean Δ ≤ −5 pp and Δ < 0 in all 9 banks.
  - **even**: |mean| < 1.5 pp.
  - Otherwise **lean+ / lean−**.
  - "No-brainer" means dominant or dominated.

## Stat-mod schedules (rule 1: never spare slots, never above 105%)

The model already sets mods available at a rung to exactly `MOD_SHARE_OF_REF × ref`, so SP cap + mods = `MOD_CAP_FRACTION × ref` (105%). Each scheme therefore splits the same total across n slot lines, with these rules:

- Mods unlock at race 4 (after the race-3 win) with every line at T/n.
- Each later story win unlocks **one** new tier in the currently smallest line, raised by the whole increment, so the equipped tiers sum to exactly T (one purchase per win).
- When the increment is larger than 25% of an average line (the R2/R3 round openings), the win is a **restock** instead: the smallest lines are raised toward a common level (B: 3 purchases, C: 6).
- A slot added mid-campaign (scheme A) starts empty. It takes the opening increment and then later increments until it catches up. It cannot start full without breaking rule 1.
- Finale (cap-exempt, 86/14 kept): each finale rung's mods (base + finale mods) are split evenly over the slots.

| | A (3 → 6) | B (fixed 3) | C (fixed 6) |
|---|---|---|---|
| Slots R1 / R2 / R3 / Finale | 3 / 4 / 5 / 6 (+1 at each round opening and at the finale unlock) | 3 | 6 |
| Smallest slot / mean slot, SP: R1 kid #1 · R2 opener kid #1 · R3 opener kid #1 · R3 last boss · Myth #1 | 25.4/25.8 · **19.1/29.7** · **30.0/37.4** · 47.7/49.4 · 54.3 | 25.4/25.8 · 38.4/39.6 · 60.4/62.3 · 80.7/82.3 · 108.6 | 12.7/12.9 · 19.2/19.8 · 30.2/31.2 · 39.8/41.1 · 54.3 |
| r cost of one slot at walls (mature #2 / bosses) | 0.048–0.084 (R1 like B, R3 ≈ 0.048) | 0.082–0.086 | **0.037–0.041** |
| Rungs with a slot < 90% of the mean slot | 8 (min 0.53 at the R2 opener, 0.67 at the R3 opener) | 0 | 6 (all 0.89) |
| Campaign purchases R1–R3 (62 story wins) | 56 | 60 | 69 |
| Wins with no new stat tier (0-level win, rule 1 forbids one) | 9 | 9 | 9 |
| Upgrade per purchase vs the replaced mod, median (p10–p90) | 7.3% (2.5–17.3) | 4.9% (2.4–9.7) | **10.4% (5.0–19.4)** |
| Spend in stat-point units (price ∝ stat value) R1 / R2 / R3 | 585 / 583 / 776 | 585 / 916 / 1,440 | **336 / 523 / 822** |
| Finale spend | 1,928 | 1,928 | 1,928 |

## Q1. Is trading a stat slot for a window slot ever a no-brainer?

### Asked sizes (+10/20/30% of w(r))

Mean paired Δ for one window mod, range across the 9 crews (pp). The verdict letter gives counts across crews: X = dominated, − = lean−, = = even, + = lean+, D = dominant.

| Scheme | Cell | Weak +30% | Average +10% / +20% / +30% | Strong +30% |
|---|---|---|---|---|
| A | mature #2 skipped | −5.4..−4.4 (−7 X2) | −47.2..−40.6 / −46.9..−37.6 / −46.4..−33.7 (X9 each) | −55.7..−20.8 X9 |
| A | boss skipped | −6.0..−4.8 (−2 X7) | −49.0..−41.6 / −48.5..−38.1 / −47.9..−33.4 X9 | −52.3..−19.1 X9 |
| A | boss at target | −14.3..−11.6 X9 | −63.4..−49.3 / −62.4..−43.8 / −61.0..−37.4 X9 | −43.6..−15.7 X9 |
| B | mature #2 skipped | −5.4..−4.9 (−6 X3) | −47.2..−45.8 / −46.9..−45.5 / −46.4..−45.0 X9 | −58.0..−54.0 X9 |
| B | boss skipped | −6.0..−5.4 X9 | −49.0..−47.5 / −48.5..−47.1 / −47.9..−46.5 X9 | −52.7..−50.1 X9 |
| B | boss at target | −14.3..−13.2 X9 | −63.4..−62.0 / −62.4..−60.9 / −61.0..−59.4 X9 | −44.0..−41.6 X9 |
| C | mature #2 skipped | −4.3..−3.7 (−9) | −37.2..−35.5 / −32.7..−30.7 / −27.3..−24.9 X9 | −15.4..−13.9 X9 |
| C | boss skipped | −4.6..−4.0 (−9) | −38.2..−35.0 / −32.9..−29.6 / −27.2..−23.5 X9 | −14.3..−12.8 X9 |
| C | boss at target | −10.9..−9.3 X9 | −42.3..−38.1 / −34.7..−30.6 / −27.7..−23.3 X9 | −11.2..−9.9 X9 |
| A, C | Myth #2 skipped (6 slots) | −4.1 (−) | −41.4 / −39.7 / −37.4 X | −29.4 X |
| B | Myth #2 skipped (3 slots) | −4.2 (−) | −43.7 / −43.6 / −43.5 X | −67.0 X |
| A, C | Summit skipped | −5.6 X | −46.8 / −46.0 / −45.1 X | −44.0 X |
| B | Summit skipped | −5.6 X | −47.7 / −47.6 / −47.6 X | −73.3 X |

All-stat baselines (mid, range across crews):

| Cell | Weak | Average | Strong |
|---|---|---|---|
| Mature #2 skipped | 5.8–6.2 | 46.2–48.0 | 81.8–83.6 |
| Boss skipped | 6.3–6.9 | 48.2–50.1 | 81.9–83.7 |
| Boss at target | 14.4–15.2 | 63.2–65.6 | 86.7–88.3 |
| Myth #2 skipped | 5.3 | 44.7 | 82.4 |
| Summit skipped | 6.6 | 47.0 | 83.6 |

**Verdict at +10/20/30%: yes, a no-brainer in every scheme. The window mod is clearly dominated at every key cell for the average and strong player.** For the weak player it is dominated or lean− (they sit near the floor, so they have little to lose).

The cause is that one slot costs Δr 0.037–0.086, and below r = 1.05 that costs twice: V = r^κ falls *and* the visible zone shrinks (w(1.0097) = 0.647 w0). A +30% widening cannot buy that back.

The only places a +10–30% window wins are the **easy rungs above r = 1.05**, where the zone has already plateaued at w0 so the lost stat only costs V. At kid #1 at target:
- C, weak player: dominant from +20% (+8.2..+9.7 at +20%, +17.5..+18.6 at +30%).
- A: the same right after each slot unlock, because the new slot is undersized.
- B: needs +50%.

### Break-even window size (one window mod; mean Δ = 0)

| Scheme | Cell | Weak | Average | Strong |
|---|---|---|---|---|
| A | mature #2 skipped | +88% – +204% | +103% – +260% | +234% – >300% |
| A | boss at target | +92% – +199% | +117% – +297% | +283% – >300% |
| B | mature #2 skipped | +195% – +209% | +250% – +269% | >300% |
| B | boss at target | +194% – +201% | +288% – +299% | >300% |
| C | mature #2 skipped | +66% – +70% | +76% – +81% | +150% – +163% |
| C | boss skipped | +62% – +70% | +72% – +81% | +135% – +155% |
| C | boss at target | +64% – +73% | +78% – +89% | +159% – +189% |
| A, C | Myth #2 / Summit skipped | +112% / +163% | +131% / +204% | +294% / >300% |
| B | Myth #2 / Summit skipped | +243% / >300% | >300% / >300% | >300% |

A's ranges span its rounds: R1 behaves like B, and R3 (5 slots) comes down to about +100–120% for the average player.

Only fixed 6 has a break-even size that separates the profiles: weak < average < strong, at roughly +65 / +80 / +150%. That spread is what makes a choice meaningful.

### Larger sizes (one window mod, mean Δ range across crews; full grid in `results_sizes.json`)

**Scheme C at the walls:**

| Cell | Profile | +50% | +75% | +100% |
|---|---|---|---|---|
| Mature #2 skipped | weak | −2.7..−2.0 (−9) | +0.6..+1.4 (=9) | +5.9..+7.5 **D9** |
| Mature #2 skipped | average | −15.7..−13.7 X9 | −3.4..−1.1 (−7 =2) | +6.3..+8.8 **D9** |
| Mature #2 skipped | strong | −10.7..−8.6 X9 | −6.5..−5.8 X9 | −5.2..−2.8 (−8 X1) |
| Boss at target | weak | −6.8..−4.6 (−2 X7) | +1.2..+4.4 (+3 =6) | +10.9..+15.5 **D9** |
| Boss at target | average | −15.2..−11.6 X9 | −4.3..−1.6 (−9) | +3.3..+5.8 (+7 D2) |
| Boss at target | strong | −6.8..−6.0 X9 | −5.1..−4.0 (−5 X4) | −4.2..−1.5 (−9) |

**Schemes A and B at +100%:** the walls stay dominated or lean− for every profile.

**Finale, all schemes:** dominated at every size up to +100%. A finale slot holds 1/n of the big finale mods; at 6 slots that is Δr 0.059 at Myth #2 and 0.075 at Summit.

### Recommended size, with the qte-v1 total-width cap kept

The candidate is **scheme C, one window mod of +75% of w(r), plus qte-v1's total-zone cap of 1.15 × w0** (`results_cap.json`). The cap never binds at the walls: there w(r − Δr) × 1.75 ≈ 0.98–1.13 w0. It only binds on easy rungs above r ≈ 1.03, where it removes the kid-rung no-brainer.

| Cell | Weak | Average | Strong |
|---|---|---|---|
| Kid #1 at target | +4.2..+5.9 (lean+ 7, D 2) | −2.5..−2.2 lean− | −2.1..−1.9 lean− |
| Mature #2 skipped | +0.6..+1.4 even | −3.4..−1.1 (lean− 7, even 2) | −6.5..−5.8 dominated |
| Boss skipped | +0.9..+2.8 (lean+ 3, even 6) | −2.6..+1.4 (lean− 6, even 3) | −5.8..−5.3 dominated |
| Boss at target | +1.2..+3.0 (lean+ 3, even 6) | −4.3..−2.6 lean− | −5.1..−4.4 (lean− 5, X 4) |
| Myth #2 / Summit skipped | −2.9 / −5.2 | −20.6 / −36.4 dominated | −15.7 / −27.6 dominated |

Without the cap, the same mod is **dominant** at kid #1 at target: weak +43.8..+45.7, average +7.1..+7.8. Across all 126 campaign cells (63 rungs × target/skip):
- **With the cap:** dominant 0 times for average and strong, and 4 times for weak (all kid #1). Verdict counts: average lean− 117, even 9; strong lean− 95, dominated 31; weak lean+ 101, even 21, dominant 4.
- **Without the cap:** average 73 dominant, weak 93 dominant.

So slot competition does **not** replace the 1.15 × w0 width cap. The two are needed together.

## Q2. Grind counts (forced policy; at each rung the player takes the best loadout at the skip state; clear = pooled mid ≥ 50)

| Window option | A weak / avg / strong | B weak / avg / strong | C weak / avg / strong |
|---|---|---|---|
| No window (baseline) | 141 / 153 / 121 | 141 / 153 / 121 | 141 / 153 / 121 |
| +10%, +20%, +30% | 141 / 153 / 121 | 141 / 153 / 121 | 141 / 153 / 121 |
| +50% | 141 / 153 / 121 | 141 / 153 / 121 | 137 / 153 / 121 |
| +75% | 139 / 153 / 121 | 141 / 153 / 121 | 137 / **140** / 121 |
| +75% + 1.15 w0 cap (C only) | — | — | 141 / **140** / 121 |
| +100% | 137 / 153 / 121 | 141 / 153 / 121 | 139 / **109** / 127 |

All runs reach 162 levels. Allowing up to 3 window mods gives identical counts.

- **Asked sizes:** windows of +10–30% change no grind count in any scheme. Only rule 1 decides the stat totals, and it is the same in all three schemes.
- **C at +75% (−13 races for average):** the window lifts the R2 and R3 opener boss walls from 48.85 to 50.06 mid, so they clear with 0 grind instead of 8 and 9. The next crew's mature #2 then costs 9 and 10 instead of 7 and 8. That clear sits at the 50 line, inside the noise, so treat −13 as fragile.
- **C at +100% (109 for average):** windows start replacing grind at 12 walls, which breaks the spirit of rule 3. Don't go that big.
- **Weak below average:** the weak player's 141 is lower than the average 153 because they clear nothing. They grind to the cap at every rung, where the taper pays more per race, and they still lose most walls (5–15% mid).

## Q3. Progression feel

- **B (fixed 3):**
  - The smallest felt upgrades (median +4.9% per purchase).
  - The highest spend: 2,941 units over R1–R3, 1.75× C.
  - Window mods are dead at every wall for every size tested up to +100%.
  - No choices beyond "buy the next tier".
- **A (3 → 6):**
  - Three slot-unlock moments read well on paper, but each new slot starts at 53–67% of a full slot. Rule 1 forbids starting it full.
  - The first wins after an unlock are therefore the "almost spare slot" Austin wanted to avoid. Average players take a +30% window at 6 kid rungs in R2/R3. Four of them are the opener kids right after an unlock (R2 Wangan, R3 Street kid #1/#2), where the new slot holds little stat; the other two are R3 Touge and R3 Wangan kid #1.
  - R1 plays like B.
- **C (fixed 6):**
  - The largest felt upgrade per purchase: median +10.4%, p10 5.0%.
  - The lowest spend (1,681 units R1–R3).
  - Evenly filled slots (worst 0.89 of the mean).
  - The only scheme where a window mod is a real, skill-dependent choice at the walls: weak lean+, average close, strong lean−/dominated.
- **All schemes:** 9 story wins per campaign (the 0-level old-head #1 wins and the zero step in the round-opening cap) can't unlock a stat tier without breaking rule 1. A window mod is a natural thing to unlock on those wins, so no win is empty. That is a proposal, not run.

## Recommendation

Use **scheme C (fixed 6 slots)** with:
- the water-filling stat schedule above (one tier per win, restock at round openings);
- one window-only mod size of **+75% of w(r)**, at most one equipped;
- qte-v1's total-zone cap of **1.15 × w0** kept.

This setup gives:
- no no-brainer at any key cell for the average or strong player;
- a mild edge for weak players at walls (+0.6 to +3.0) and kid rungs (+4.2 to +5.9);
- strong players lose 4–6.5 pp;
- grind 140 for average (fragile −13, see Q2), 141 for weak, 121 for strong;
- the finale unaffected (windows dominated there, so the 86/14 split stands).

If Austin wants to keep window sizes at +10/20/30%, they are dead content at every wall in every scheme: only kid rungs use them. Then pick C or B on economy and feel alone, and C still wins.

## Placeholder caveats

- **Skill model is a placeholder:** σ for weak/average/strong (`QTE_SKILL_SIGMA_OVER_A0`, E[s] 0.4/0.6/0.8) and the linear-falloff press model. The break-even sizes scale directly with these, so **re-run after playtest**.
- **Mod lines and costs are modelled, not designed:** slots are generic stat lines with no per-stat split. Builds are balanced, so a slot's value is its total. Prices are "∝ stat value" because every payout and price constant in design/07 is TBD. Money is reported as stat-point units, and payouts (`BASE_PAYOUT_*`, wholesale discount, betting) are not modelled. The finale spend assumes every slot is replaced on each finale rung.
- **Restock threshold:** the 25%-of-a-line restock rule and the smallest-line purchase order are my design choices.
- **Clear rule and cells:** clears use the official pooled-mid ≥ 50 rule. Cells use the average player's official progression state for every profile.
- **Some grind changes are within noise:** the +75% opener-boss clears are 1.2 pp over the line.

## Reproduce

```
cd design/unapproved/slots-v1 && ./run_all.sh && python3 summarize.py > summary.txt
```

Needs numpy, the count banks under `/workspace/barry-drafts/{final-v1,lines-v1}`, and the repo sim at `/workspace/midnight-apex/sim`. Files:
- `slots_model.py`: schemes, schedules, oracle, and a progression copy with the loadout-aware clear test.
- `run.py`: key cells, +10/20/30%, break-even, feel.
- `run_sizes.py`: +10…+100% on every rung.
- `run_grind.py`: grind counts.
- `run_cap.py`: C at +75% with and without the 1.15 × w0 cap.
- `wr_shortcut.py`: oracle, unchanged from qte-v1.
