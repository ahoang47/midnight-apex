# Round-ladder v1 — 3-crew ceiling × 1.07 (draft)

Barry / 2026-11-13. Study only, under `unapproved/barry/round-ladder-v1/`. No `sim/` or `design/` edits. No commit.

Austin approved (2026-11-13) one district per round, R1 Street / R2 Wangan / R3 Touge, **one crew per district, raced once, no rematches**, plus a new round-to-round ladder: each round's opponent power (stats + mods) = previous round's ceiling × the parity cap. Live `MOD_CAP_FRACTION` is 1.07 (Austin: "110% or whatever you decided"); **1.07 is primary, 1.10 is a variant**. XP / economy refit stays deferred. Live constants are not changed.

Canon/story/docs used here are **origin/proto-build `c826ffd`** (Desmond, 2026-11-13): debt/aero at the end of R1 with wholesale, one Myth sighting per district, canon 12 retired, Mentor Confrontation after the Touge round before Myth #1. This worktree stays on `9a17baa`; live files were not checked out or edited. Proposed numbers are draft only in this folder (`proposed_constants.json`).

## Sources

Combat is live **G2_slant_m10** on the **touge-lines-v1 draft track set**, one fixed tune per district (Street 50/25/25, Wangan 25/30/45, Touge 40/30/30), gravity on, no line edits. New r-sweep: `results_r_sweep.npz`, 9×1000, seeds 20261112–20261120, 28 values of r from 0.88 to 1.333, measures 60/60 (`q_read` 0.6 + average QTE profile + `PACE_Q` 0.6 at the trial r) and 80/80. At r = 1.07 the district-mean win rates match touge-lines-v1 exactly (Street 74.7 / 67.8 / 57.4, Wangan 68.8 / 70.6 / 67.6, Touge 65.2 / 53.5 / 40.9 at 10 / 20 / 30).

Encounter lengths stay official (`cli.py`): wild / grind = 10, lieutenants (kids, mature, old heads) = 20, crew boss = 30. Within a round the crew ladder is still 2 kids → 2 mature → 2 old heads → boss (`LADDER_RUNGS`). Lieutenant at-cap target r stays `LADDER_R[:6]` = 1.13, 1.11, 1.10, 1.08, 1.07, 1.06. Boss at-cap r uses the **live** cap 1.07, not the stale `LADDER_R[6] = 1.05`.

`progression.py` is still stale (v8c XP, `PROGRESSION_MOD_CAP_FRACTION` 1.05, card-draw oracle, 9-crew `check_order`). **Not refit.** Grind counts and finale *level caps* below are from that curve and are flagged. Combat r at cap uses a live 1.07 fill (`player total = 1.07 × ref`). The shop still only funds a 0.25 share, which reaches 1.05; the extra 0.02 has no economy source until the deferred refit.

## Ladder rule

Let k = 1.07 (primary) or 1.10 (variant). Power means SP + mods.

1. R1 Street boss is anchored at today's first campaign crew: `SABINE_BUDGET × OPTION_A_CREW_STEP` = 330, snapped to the nearest level (already exact).
2. Player ceiling at the end of a round, C = `player_cap_frac ×` that round's snapped boss budget. Primary `player_cap_frac` = live 1.07.
3. Next round's intended boss budget = previous C × k, then snapped to the nearest level.
4. Lieutenant budgets at each rung are set so that a player at that rung's cap has r = `LADDER_R[j]`.
5. Every opponent / player-ceiling ratio is checked against the 0.8–1.2 stat+mod parity band in `design/01`.
6. Level-cap raises use `CAP_ALLOC_CREW` weights on the actual level delta of that crew. The old 33-level `CAP_ALLOC_ROUND_OPEN` is **not** used (see § opener step).

A budget step does **not** change at-cap combat r if the player cap still tracks 1.07 × the current boss. The 1.07 vs 1.10 *step* only changes how big the cap jump (and the grind) is. A 1.10 *player cap* would change at-cap boss r to 1.10 and ease every district at once.

Nearest-level snap makes R2 / R3 boss ÷ previous ceiling 1.0697 rather than 1.0700 on the primary walk. Immaterial.

## Per-round opponent power (primary, k = 1.07, cap = 1.07)

| Round | District | Intended B | Snapped B | Player ceiling C | Cap L | Levels in the crew | Alloc (7 rungs) | Boss r at cap | Opp / C (in band?) |
|---|---|---:|---:|---:|---:|---:|---|---:|---|
| 1 | Street | 330.00 | 330.00 | 353.10 | 12 | +12 | 2,2,3,3,1,0,1 | 1.070 | 0.935, yes |
| 2 | Wangan | 377.82 | 377.71 | 404.15 | 29 | +17 | 3,3,4,4,2,0,1 | 1.070 | 0.935, yes |
| 3 | Touge | 432.44 | 432.31 | 462.57 | 46 | +17 | 3,3,4,4,2,0,1 | 1.070 | 0.935, yes |

Boss budget grows ×1.145 per round (1.07², because C_n = 1.07 B_n and B_{n+1} = 1.07 C_n). All at-cap rungs sit inside the 0.8–1.2 band (kids 0.885 through old head #2 0.943, boss 0.935).

### 1.10 variants (same R1)

| Variant | R2 B (snap) | R2 cap L | R3 B (snap) | R3 cap L | At-cap boss r |
|---|---:|---:|---:|---:|---:|
| Step 1.10, player cap stays 1.07 | 389.90 | 33 | 460.67 | 54 | **1.070** (combat same as primary) |
| Step 1.10 and player cap 1.10 | 399.30 | 36 | 483.15 | 60 | **1.100** (every boss easier) |

## At-cap win rates, 60/60 and 80/80

Because at-cap boss r is 1.07 on the primary ladder (and on the 1.10-step / 1.07-cap variant), the district-mean rates are the touge-lines-v1 cells, now assigned to whole rounds.

### 60/60, official lengths, district-fixed tune, r at the rung's cap

| Round | District | Grind 10 at r=1.07 | Lt 20 at each `LADDER_R` (kid, kid, mat, mat, OH, OH) | Boss 30 at r=1.07 |
|---|---|---:|---|---:|
| 1 | Street | 74.7 | 95.9, 90.5, 87.2, 76.3, 67.8, **58.6** | 57.4 |
| 2 | Wangan | 68.8 | 94.6, 89.8, 86.1, 76.9, 70.6, 62.0 | **67.6** |
| 3 | Touge | 65.2 | 86.8, 78.5, 71.7, 59.7, **53.5**, **46.0** | **40.9** |

80/80 at the same r: Street lieutenants 99.9–96.9, boss 98.4; Wangan 99.9–94.4, boss 97.6; Touge 99.5–91.7, boss **92.2**. Strong players are fine everywhere. The walls below are 60/60 problems.

Wild / grind 10-turn: if wild opponents stay on the pending `ENCOUNTER_RATIOS['wild'] = 0.75` placeholder (r ≈ 1.333), 60/60 is 100.0 in every district in this sweep. That ratio is still the old CLI double-count and is not a G2 final. 10-turn at the crew's at-cap r=1.07 (a conservative stand-in) is the 74.7 / 68.8 / 65.2 column above.

If the player cap is also 1.10 (third variant), bosses at r=1.10 are Street 83.2, Wangan 86.2, Touge 63.8 at 30 turns, 60/60. That fixes Touge by making R1 and R2 very easy. Not recommended as a global cap change; use a Touge-only offset instead (§ offset).

## Walls and dips (60/60, at cap unless noted)

- **R3 Touge crew boss, 30-turn, r=1.07: 40.9%**, uphill 37.4, downhill 44.4, limp 27.1% of clashes (vs Street 16.9, Wangan 19.2). This is the same cell as touge-lines-v1; the new ladder does not soften it at cap. It is now the *entire* last chapter, then (per c826ffd) a Touge #1 challenge, the Mentor Confrontation, and Myth #1 on Touge.
- **R3 Touge old head #2, 20-turn, r=1.06: 46.0%**, already a wall at cap, before the boss. Street / Wangan old head #2 are 58.6 / 62.0.
- **R1 Street crew boss is not uniform.** District mean 57.4 hides **S1 Shibuya Grid 48.5 CW / 50.5 CCW** at 30 turns, limp ~22.6. S3 Shinjuku is 65.7 / 64.7, limp ~11. If the R1 boss runs on S1, it is an early wall for a 60/60 player. 80/80 on S1 is 97.3–97.5.
- **Wangan R2 is the most comfortable chapter** (boss 67.6). The soft layout is W3 CW 56.9 at 30, still well above Touge.
- **Skip-grind falls off a cliff under G2.** Design/07's "average play at a skipped wall wins roughly 40–55%" is the stale card-draw oracle and is false here. At r ≤ 0.98, 60/60 bosses are ~0%. Never-grind arrival at the R3 boss (stale XP walk, r_skip = 0.920) is un-winnable for 60/60 and 5.1% for 80/80. Even arriving at r=1.00 is 0.1 / 1.5 / 0.4 at Street / Wangan / Touge 30-turn. After grinding the mature #2 wall, stale-XP arrival at the boss is r ≈ 1.053: Street 35.5, Wangan 50.9, Touge 26.0, then 6–8 more grind races to cap. Average players must be at (or extremely near) cap. Do not ship a "skip the grind" reading from the old oracle.

## Grind needed to reach each round's cap

**Flag: stale v8c XP curve, not a refit.** Counts use existing `grind_payout_fraction` and `STORY_XP_*` with `CAP_ALLOC_CREW` on the new level deltas. `STORY_XP_LT_ROUND_OPEN` was applied to R2/R3 as the only crew in the walk; that is not a recommendation. `MOD_TIER_LEVEL_FLOOR` was **not** applied (the 9-crew table has R3 floor L111, above the new L46 cap; it would lock R2/R3 mature #2 mods and must be re-derived after the XP refit).

Walls policy (grind to cap only at mature #2 and the crew boss), primary 1.07 ladder:

| Round | Cap L | Arrive at mature #2 / grind there | Arrive at boss (r_skip) / grind there | Total grind to finish the round at cap |
|---|---:|---|---|---:|
| 1 Street | 12 | 7 races | L10, r=1.053 / 6 races | 13 |
| 2 Wangan | 29 | 7 | L27, r=1.053 / 8 | 15 |
| 3 Touge | 46 | 7 | L44, r=1.053 / 8 | 15 |

That is the same shape as today's per-crew walls (about 6–8 races at the boss after a mature #2 grind), not the inflated "always-to-cap from a never-grind start" sums. Variant step 1.10 / cap 1.07: R2 18, R3 19. Variant 1.10 / 1.10: R2 19, R3 21. Never-grind leaves the player at L4 / L15 / L27 on the primary walk (r_skip at the three bosses 1.004 / 0.957 / 0.920) and is not viable under G2.

## Open questions, with numbers

**Does the campaign cap go 150 → ~78?** No, not under the approved ceiling × 1.07 rule. 150 is the current 9-crew end cap. **78 is what you get if you keep `OPTION_A_ROUND_STEP` 1.30 on a 3-crew walk** (R1 L12, R2 L45, R3 L78). The primary 1.07 ladder ends the campaign at **L46** (1.10-step / 1.07-cap: L54; 1.10 / 1.10: L60). You cannot keep L150 with three crews and a ~1.07–1.30 step on the current GEO curve (SP grows 10% per 12 levels; two 1.145 budget steps are a 31% rise, not the old 9-crew 3× rise). Stretching the cap back to 150 would mean a different step or a different SP curve — that is an XP refit, deferred. Combat at cap depends on *r*, not on the absolute cap, so L46 vs L150 does not by itself change the 40.9% Touge boss.

**Do finale caps go 154–162 → ~100–112?** The 100–112 figure is also an artifact: it is the stale `FINALE_GRIND_SHARE` formula applied to the **old absolute finale budgets** (1086.8 … 1446.5) after a 1.30 3-crew end at L78. Those finale budgets were scaled off a last campaign boss near 988 and do not belong on a 3-crew season that ends at 432. Under the primary rule, recommended finale *budgets* continue ceiling × 1.07:

| Race | District | Proposed B (snapped) | Stale grind-share cap (flag, not a refit) |
|---|---|---:|---:|
| Myth #1 | Touge | 494.8 | 51 |
| Myth #2 | Wangan | 566.3 | 55 |
| Myth #3 | Street | 648.2 | 59 |
| Summit | Touge | 741.9 | 63 |

Lstep (last boss pays a 12-level finale story step, current formula) = 48. These Lf numbers are XP-dependent and must not be treated as shipping caps. A legacy ×1.10-from-last-B alternative would be 475.5 / 523.1 / 575.4 / 632.9 with stale Lf 50 / 53 / 55 / 58. I recommend the ceiling × 1.07 continuation so finale uses the same step as the campaign. Absolute power is much lower than 1086–1446; **at-cap r can stay 1.07**, so the win-rate problem is still the district (Myth #1 and Summit are Touge) rather than the raw budget.

**R3 all-Touge bosses ~41% and 27% limp at 30 turns?** Yes, at cap, r=1.07: **40.9% win, 27.1% limp**. Uphill 37.4, downhill 44.4. 80/80 is 92.2%. This is real G2 on the draft tracks, and the new ladder does not change it unless R3 gets a target-r offset (next section). Touge old head #2 at r=1.06 is already 46.0% at cap.

**R1 Street boss 48–50% on Shibuya S1?** Yes, at cap, r=1.07, 30-turn: **S1 CW 48.5, CCW 50.5**, limp 22.8 / 22.5. S3 is 65.7 / 64.7. 80/80 on S1 is 97.3–97.5. Prefer S3 for the R1 boss layout. If S1 must be the boss track, a **+0.01 Street-boss-only** target (r=1.08) lifts S1 to 57.5 / 60.2 at 30 turns (measured, not interpolated). Do not raise the whole Street ladder.

## How to keep R3 Touge from being a wall (numbers only; live constants unchanged)

A smaller R3 *budget step* does not help at cap if the player cap still tracks 1.07 × B3: r stays 1.07 and the 40.9% cell stays. The offset has to **decouple R3 opponent power from the player ceiling**.

**Proposal (draft):** keep C3 = 1.07 × (R2 ceiling step), i.e. the player still gets the normal 1.07 ceiling rise from R2, but set every R3 opponent budget so the at-cap target r is **+0.03** vs the live ladder (boss 1.07 → **1.10**; lieutenants `LADDER_R[j] × 1.10/1.07`). That is a 2.7% opponent-budget cut: B3 = C3 / 1.10 = 420.5 vs 432.3. Opp / player = 0.909, still inside 0.8–1.2.

Measured at r=1.10, Touge 60/60: 10 / 20 / 30 = 76.4 / 71.7 / **63.8** (uphill 60.3, downhill 67.4), limp 20.0 at 30 turns. 80/80 boss 97.3. This clears the current-mix 55.3 and the Street boss 57.4, and is within a few points of Wangan 67.6. Old head #2 would move from r=1.06 toward ~1.09 (not on the grid; at r=1.08 20-turn Touge is already 59.7, at 1.10 it is 71.7).

If the aim is to *match* Wangan's 67.6 including the uphill cell, use **+0.04** (boss r=1.11): Touge 30-turn 73.0 (uphill 69.8), limp 17.0. Linear interpolation between 1.08 and 1.11 (not resimulated) puts Street-parity 57.4 near r≈1.092 and Wangan-parity 67.6 near r≈1.104; I would not ship an interpolated value — pick 1.10 or 1.11 from the measured grid.

Do **not** raise global `MOD_CAP_FRACTION` to 1.10 to fix this. That would also push R1 Street and R2 Wangan bosses to 83.2 / 86.2 at 30 turns.

Line edits remain the wrong tool (touge-lines-v1: one tune already covers both directions; 8/10 corners are signature).

## Proposed structural constants (draft only)

Full draft: `proposed_constants.json`. Not for `sim/` until Austin signs off.

```
DEFAULT_CREW_ORDER = {1: ("Street",), 2: ("Wangan",), 3: ("Touge",)}
DEBT_CLEAR_AFTER    = (1, 1)   # Street crew boss, same moment as wholesale (c826ffd)
BETTING_UNLOCK_AFTER = (2, 1)  # Wangan crew boss
FINALE_UNLOCK_AFTER  = (3, 1)  # Touge crew boss; Mentor Confrontation then Myth #1
```

`check_order`: each round has exactly one crew, matching that locked order. Retire the permutation test. `all_orders()` yields the single order (the 216-order enumerator goes away).

**×1.30 opener step: do not apply.** There is no "which crew opens the round." `OPTION_A_ROUND_STEP = 1.30` and `CAP_ALLOC_ROUND_OPEN` (the 33-level raise) should be retired. The new inter-round step is ceiling × 1.07 (or the 1.10 variant, which still should not use 1.30). `OPTION_A_CREW_STEP = 1.10` stays only as the prologue → R1 anchor (330).

**Opening-crew cap raise:** use `CAP_ALLOC_CREW` weights on the actual dL (12 / 17 / 17 on the primary walk), not `CAP_ALLOC_ROUND_OPEN`.

**FINALE budgets (primary, ceiling × 1.07):** 494.8, 566.3, 648.2, 741.9 for Myth #1 / #2 / #3 / Summit. Stale grind-share caps 51 / 55 / 59 / 63 are XP-dependent and not part of this structural proposal.

XP-dependent items **not** proposed as a refit: grind payout, story XP lambdas, `MOD_TIER_LEVEL_FLOOR`, `DEBT_AMOUNT` (must be retargeted to the end of R1, economy deferred), finale level caps.

Tests that would need rewriting once this lands (not run this pass): `test_default_order_reproduction`, `test_round_opening_by_position`, `test_free_order_position_keyed`, `test_first_crew_gets_round_step_and_unlocks`, `test_order_must_be_a_permutation`, and `test_mod_floor`'s 9-crew table.

## What stale `progression.py` blocks

It cannot accept the approved 3-crew order (`check_order` requires a permutation of all three districts each round). Unlock markers are still `(2,1)` / `(2,3)` / `(3,3)`, so debt/aero would fire on a non-existent mid-R2 crew and betting / finale would never fire. `DEFAULT_CREW_ORDER` still starts on Touge and lists nine slots. `OPTION_A_ROUND_STEP` / `CAP_ALLOC_ROUND_OPEN` still inject a 1.30 / 33-level opener. Finale budgets are still 1086–1446. The win-rate oracle is card-draw at a 1.05 cap; `run()`'s "clear" test and any quoted skip-grind win rates from that module are not G2. The mod-tier floor table is unusable at the new caps. **None of that was silently refit.** The structural draft above is what a later refit should install; the XP curve stays deferred.

## Wording fixes for the c826ffd notes

Desmond's stale banners are in the right spirit (sim still models the 9-crew ladder until a refit). These leftovers should be cleaned up when the draft constants land, and some should be fixed sooner because they now describe the wrong structure or the wrong study.

**`sim/velocity_shift/equations.py` (comment above `DEFAULT_CREW_ORDER`):**
- The stale note points at `unapproved/barry/round-order-v1`, reading B. Point it at **`unapproved/barry/round-ladder-v1`** once this study is the source.
- Immediately after saying the campaign is one district per round, the next sentences still say "Crew order is FREE within a round" and that everything is "keyed by PLAY POSITION." That is the retired 2026-11-10 rule. Split "what the constants still do" from "what canon is now," or readers will take free order as current.
- `OPTION_A_ROUND_STEP` is still glossed "whichever crew OPENS Round 2 / Round 3." Mark that gloss retired.

**`sim/velocity_shift/progression.py` docstring:**
- The new "STALE vs canon since 2026-11-13" blurb is good, but the very next paragraph still says "any permutation of DISTRICTS per round … 9 crews × 7 rungs" and the rules list still describe Option A steps by play position and `CAP_ALLOC_ROUND_OPEN` as if they were live design. Same split: stale behaviour vs new structure.

**`design/02-equations-reference.md`:**
- Budgets and unlock rows are correctly marked stale and already have the new canon timing. Good.
- **Cap raises** (`CAP_ALLOC_CREW`, `CAP_ALLOC_ROUND_OPEN`) and **Story XP** (`STORY_XP_LT_ROUND_OPEN`) are not marked stale; `CAP_ALLOC_ROUND_OPEN` should be, for the same reason as the 1.30 step.
- Caps row still says "SP + mods to 105 %." Live `MOD_CAP_FRACTION` is 1.07 (pre-existing vs the G2 commit; worth fixing in the same pass).
- The 02 table still cites "official progression stays 153 grind / 162 levels in all 216 orders" (race-balance row). That is the old 9-crew reproduction, not canon.

**`design/07-economy-and-mods.md` §1, §7, §8, test plan:**
- §1 season runner and §2.1 structure rows are already updated. Good.
- §6.3 evidence still says a large aero pool "let average players clear **R3 Street's crew boss**." That study is historical (slots-v2, 9-crew, Street was the default last R3 crew) and should be labeled as such; R3 is Touge now.
- §6.4: "N is per crew, keyed by (round, play position) … the same in all 216 play orders" — the stale caveat is present, but after a 3-crew refit this becomes one floor per round, keyed by district/round, not 216 orders.
- §8.0 still teaches `CAP_ALLOC_ROUND_OPEN`, "the boss before a round-opening crew pays its large opening step," and free-order budget steps (the stale caveat is only on the budgets bullet). Update or banner the opener-step sentences.
- §8 **open items (2) and (3)** are out of date and should not be quoted as current: "(2) Street is the thinnest district … **Round 3 old head #2** clears at only 55–57% with the grind skipped" and "(3) skipped walls dip on Wangan's tracks (to 33–37%) and at Finale Myth #2 (36–46% pooled)." Those are card-draw 9-crew figures. Under this G2 3-crew assignment, Street is R1, the thin 20/30 cells are **Touge**, and skip-grind at even r=1.00 is ~0% for 60/60 bosses, not 40–55%.
- §8 also still says "105 % cap" and "the finale window is extrapolated above r 1.05."
- §9.5 test plan already notes that live `progression` tests use the old `DEFAULT_CREW_ORDER`. Keep that until the tests are rewritten; then drop the "until Barry's refit" clause.
- Q3 is correctly marked resolved (Street crew boss, end of R1).

**`design/01`:** the new Round structure entry and the "Sim gap" sentence are accurate. After this study, the gap can point at `round-ladder-v1` rather than an open refit with no numbers. The canon block still says "3 tracks per district" (already flagged in touge-lines-v1; Austin 2026-11-12) and still says 105% in places.

**`design/08`:** context line was updated for wholesale + aero at end of R1. No further 3-crew issue.

## Recommendation

1. Install the structural draft (locked 3-crew order, unlocks `(1,1)` / `(2,1)` / `(3,1)`, retire 1.30 and `CAP_ALLOC_ROUND_OPEN`, R1 anchor 330, inter-round step = previous ceiling × 1.07, finale budgets 494.8 / 566.3 / 648.2 / 741.9). Do not install an XP refit, new grind counts, or new `MOD_TIER_LEVEL_FLOOR` values.
2. Do **not** use the ~78 / 100–112 figures; they assume the retired 1.30 opener plus the old absolute finale budgets. Primary campaign cap is **L46**.
3. Keep at-cap r = 1.07 for Street and Wangan. For R3 Touge, apply the **+0.03 target-r offset** (boss r=1.10 → 63.8% at 30 turns, 60/60, limp 20.0) without raising the global cap. Prefer **+0.04 (r=1.11)** only if the bar is "match Wangan, including uphill."
4. Prefer S3 for the R1 Street boss. If S1 is required, a +0.01 boss-only offset (r=1.08) is enough (48.5–50.5 → 57.5–60.2).
5. Treat grind-to-cap as mandatory for 60/60 under G2; do not quote the old 40–55% skip-wall line.
6. Desmond can apply the wording fixes above; Gordon wires order / unlocks / UI once Austin signs the draft constants; Nathaniel's c826ffd story pass already matches this structure (debt at end of R1, one sighting, no rematches, confrontation before Myth #1). Arthur: no track-art demand from this study. Barry: XP/economy refit still deferred; a later pass must rebuild floors, debt amount, and finale level caps on G2, not the card-draw oracle.

## Files

- `unapproved/barry/round-ladder-v1/RESULTS.md` (this writeup)
- `proposed_constants.json` (structural draft)
- `ladder.json` / `ladder_model.py` (3-crew walks, including flagged grind)
- `run_sweep.py`, `results_r_sweep.npz`, `sweep_meta.json`, `analysis.json`
- Combat tracks and tunes: `unapproved/barry/touge-lines-v1/`

## Austin's picks (2026-11-13)

- R3 Touge: +0.03 target-r offset (boss r=1.10 at cap; 60/60 30-turn 63.8%, limp 20.0). Not the +0.04 variant.
- R1 Street boss: stays on Shibuya S1 with a +0.01 boss-only offset (r=1.08; 57.5 / 60.2 at 30 turns). S3 not swapped in.
- Status: chosen for the draft; not yet approved to go live in sim/.
