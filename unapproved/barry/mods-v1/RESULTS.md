# mods-v1: mod count and points per mod (draft, Barry, 2026-11-14)

**Draft only. Nothing in sim/ changed, nothing committed.** All points are on the new 10× skill-point scale (2,400 points at L0, 19–48 per level). Every win % below comes from the files in this folder. The baseline is live proto-build c877a19 (skill-points-v1: band, lock, 20% retune).

## Live mod model (what a scheme has to match)
- The live code (equations.py and progression.py) does not model individual mods. Combat power is min(ceiling, 1.07 × P(L)) with P = SP / 0.8, so mods are assumed to fill the gap.
  - On the 10× scale, the car's points are skill_points(L) + mod points, capped at 1.3375 × skill_points(L) and at the round or finale ceiling.
- There are 6 slots (`MOD_SLOTS`), tiers T1–T4, and floors at T1 L0, T2 L13, T3 L30, T4 L47 (T4 also needs the P1 win).
- Aero: at most one equipped. It occupies a slot and counts inside the 1.07 cap. Its free pool is ≤ 10% of the part's total.
- A full set of the newest tier must fill this gap (mod points needed at each cap):

| Cap | R1 L12 | R2 L29 | R3 L46 | F1 L64 | F2 L79 | F3 L94 | F4 L115 | worst level (L114) |
|---|---|---|---|---|---|---|---|---|
| Mod points needed | 891.0 | 1019.9 | 1167.1 | 1329.1 | 1496.5 | 1703.2 | 1992.4 | 2003.1 |

- **What this means:** if a full set always meets the need (the overflow is clipped by the 1.07 cap, as in the live code), total power is identical to live at every level. Only the car's POW/HAN/EN split can move balance. A tier is sized by the last cap it has to fill: T1 for R1, T2 for R2, T3 for R3, and T4 for L114/L115. `check_fill()` in `mod_schemes.py` verifies every level from 0 to 115 with the tier available at that level.

## Schemes tested
All mods are single-stat (all of a mod's points go to one stat). Aero has the same total as the regular mod of its tier. Its base is total − pool in one stat, and its pool is floor(10% × total), placed freely.

| Scheme | Slots | T1 | T2 | T3 | T4 | Aero pool T1–T4 | Stat per slot |
|---|---|---|---|---|---|---|---|
| A | 6 | 149 | 171 | 196 | 334 | 14 / 17 / 19 / 33 | fixed 2 POW, 2 HAN, 2 EN (slots-v2 layout) |
| B | 6 | 149 | 171 | 196 | 334 | 14 / 17 / 19 / 33 | free: pick the stat when fitting |
| **C** | **4** | **223** | **256** | **293** | **501** | **22 / 25 / 29 / 50** | free |
| D | 8 | 112 | 128 | 147 | 251 | 11 / 12 / 14 / 25 | free |

The full-set margin at the tightest level is +0.9 points for A, B and C and +4.1 for D.

**Player policy (`mod_schemes.walk`):**
- For each segment (R1–R3, then finale steps F1–F4 with the district change before P1, M11, M21, M31), pick the mod stats whose car split at the segment cap is closest to the district tune.
- Skill points follow the live rules: 25–50% band, spent points lock, 20% retune. They are placed to make up for the mods.
- The car split must also stay inside 25–50%.

## Car split reached (POW / HAN / EN %, at each segment cap)

| Segment (tune) | A 6 fixed | B 6 free | C 4 free | D 8 free |
|---|---|---|---|---|
| R1 Street (50/25/25) | 45.8 / 27.1 / 27.1 | 45.8 / 27.1 / 27.1 | **50.0 / 25.0 / 25.0** (PPHE) | 50.0 / 25.0 / 25.0 |
| R2 Wangan (25/25/50) | 28.0 / 27.1 / 44.9 | 28.0 / 27.1 / 44.9 | 25.9 / 25.0 / 49.1 (PHEE) | 25.9 / 25.0 / 49.1 |
| R3 Touge (45/25/30) | 44.0 / 27.1 / 28.9 | 44.2 / 27.1 / 28.7 | 45.0 / 25.0 / 30.0 | 45.0 / 25.0 / 30.0 |
| F1 Touge | 44.0 / 27.1 / 28.9 | 43.7 / 27.1 / 29.2 | 45.0 / 25.0 / 30.0 | 45.0 / 25.0 / 30.0 |
| F2 Wangan | 27.1 / 27.1 / 45.8 | 27.1 / 27.1 / 45.8 | 25.0 / 25.0 / 50.0 | 25.0 / 25.0 / 50.0 |
| F3 Street | 44.6 / 27.1 / 28.3 | 44.6 / 27.1 / 28.3 | 50.0 / 25.0 / 25.0 | 50.0 / 25.0 / 25.0 |
| F4 Touge | 44.0 / 27.1 / 28.9 | 43.7 / 27.1 / 29.2 | 45.0 / 25.0 / 30.0 | 45.0 / 25.0 / 30.0 |

- **Why 6 slots miss the tune:**
  - Every tune is 2:1:1 in some order (HAN always 25%), and 6 single-stat slots can't split 2:1:1.
  - A HAN share of at least 25% on the car needs 2 HAN mods, because skill-point HAN can't make up the gap once R1's L0 build is locked at 50/25/25. That pulls the car toward an even split.
  - 4 slots (2-1-1) and 8 slots (4-2-2) hit every tune.

## Balance vs live (hardest track; 80/80 = strong, 60/60 = weak; mixed = 60/80 and 80/60)
Live is the skill-points-v1 baseline: the R2 car is at 26.2% POW and every other segment is on the tune.

| | Live | A 6 fixed | B 6 free | **C 4 free** | D 8 free |
|---|---|---|---|---|---|
| 80/80 story-only bosses | 53.0 / 57.7 / 55.8 | 53.7 / **70.8** / **51.1** | 53.7 / **70.8** / **48.4** | 52.9 / 57.7 / 55.8 | 52.9 / 57.7 / 55.8 |
| 80/80 lowest story race (≥50) | 53.0 / 54.4 / 50.5 | 53.7 / 61.7 / **43.8** | 53.7 / 61.7 / **41.9** | 52.9 / 54.3 / 50.5 | 52.9 / 54.3 / 50.5 |
| Mixed grinds (wall + to cap) | 3+10 / 3+10 / 4+8 | same | same | same | same |
| 60/60 grinds per round | 13 / 15 / 18 | 13 / 15 / **22** | 13 / 15 / 18 | 13 / 15 / 18 | 13 / 15 / 18 |
| At-cap boss, 60/60 | 31.6 / 40.1 / 30.3 | 30.1 / 44.9 / **29.2** | 30.1 / 44.9 / **28.9** | 31.6 / 39.9 / 30.3 | 31.6 / 39.9 / 30.3 |
| At-cap boss, 80/80 | 94.9 / 91.6 / 92.9 | 95.1 / 94.9 / 95.0 | 95.1 / 94.9 / 94.1 | 94.9 / 91.4 / 92.9 | 94.9 / 91.4 / 92.9 |
| At-cap boss, 60/80 · 80/60 (R2) | 64.1 · 81.4 | 68.5 · 86.6 | 68.5 · 86.6 | 63.7 · 81.2 | 63.7 · 81.2 |
| Finale billed, 80/80 | 81.7 / 82.7 / 78.6 / 81.7 | 82.4 / **89.5** / 76.2 / 82.4 | 81.0 / **89.5** / 76.2 / 81.0 | 81.7 / 82.7 / 79.3 / 81.7 | 81.7 / 82.7 / 79.3 / 81.7 |
| Finale billed, 60/60 | 34.7 / 41.7 / 30.3 / 34.7 | 32.2 / 49.0 / 30.6 / 32.2 | 31.2 / 49.0 / 30.6 / 31.2 | 34.7 / 41.7 / 31.6 / 34.7 | 34.7 / 41.7 / 31.6 / 34.7 |
| Arc grinds 60/60 | 11 / 7 / 7 / 9 | **13** / 7 / 7 / **13** | **13** / 7 / 7 / 11 | 11 / 7 / 7 / 9 | 11 / 7 / 7 / 9 |
| Arc grinds 60/80 · 80/60 | 7/6/6/7 · 6/6/6/7 | same | same | same | same |

- **C and D match live within 0.4 points everywhere except F3.** R2 moves −0.1 to −0.4 because the car reaches 25.9% POW instead of the skill-point 26.2%. F3 gains +0.7 to +1.3 because the car is back on the Street tune: 80/80 79.3, 60/60 31.6, 60/80 · 80/60 72.4 · 71.0. Grinds are identical.
- **A and B break targets:**
  - R3 80/80 story minimum: 43.8 / 41.9, below 50.
  - R3 60/60 at cap: 29.2 / 28.9, below 30.
  - A adds 4 60/60 grinds in R3 and 2–4 per arc step.
  - Both lift the R2 and F2 Wangan fights by 7–13 points (extra HAN helps on the hardest Wangan track).

**If T4 parts keep their stat for the whole arc** (bought once at P1, no re-pick; the "T4-locked" runs):
- C and D: F2 80/80 is 83.8 (+1.1), F3 is 78.8, 60/60 F2 is 40.7, and 60/60 grinds before F2 are 9 (+2). Everything else is unchanged.
- B locked would put F3 at 23.8% EN, outside the band, so it was not run.

## Aero (one part, any slot, same total, 10% free pool)
- **Measured:** aero against the regular set it replaces, at every boss and billed finale fight at its cap r on the hardest track (`aero_check`, policy: get as close to the tune as possible).
  - **C / D:** the gain is 0.0 everywhere except R2: −0.3 to −0.7 (C) and −0.2 to −0.3 (D). The regular 2-1-1 / 4-2-2 set already lands on the tune, so the pool has nothing to fix.
  - **A / B:** −4.5 to +2.9 points. The pool moves the car by ≤0.4 points of share, and the sign follows the hardest track's shape rather than the distance to the tune.
- **Why aero can't be a no-brainer in any scheme:**
  - The 1.07 cap clips total power, so aero's extra value can only come through the split.
  - The pool is 10% of one part: about 0.4–0.6% of the car.
  - Even an ideal pool placement moves win % by about 1 point (the off-tune slope is about 1 point of win per 1% of POW share on the hardest Wangan track).
  - At 1.75× the price, aero in C/D is a cosmetic or fine-tune buy, not a must-have. If Austin wants aero to matter more, the lever is its own stat or a different effect, not more points; extra points are clipped by the cap.

## Mod unlocks over the season (live unlock schedule)
**The sim's schedule:**
- A tier opens all at once when the player reaches its level floor (`MOD_TIER_LEVEL_FLOOR`): T1 at L0, T2 at L13, T3 at L30, T4 at L47. T4 also needs the P1 win (`T4_UNLOCK_RACE`).
- When a tier opens, every stat version of it is in stock (POW, HAN, EN) plus its aero part. Aero is available only after the R1 boss (`AERO_UNLOCK_AFTER` 1), and at most one can be equipped.
- There is no per-race stock schedule in the sim. The design/07 rule that mods unlock after the Prologue's race 3 is not in the campaign walk.

**When each tier opens.** Levels are the live walk's arrival levels (`unlocks.txt`, `purchase_sequence.json`).

| Stage | Tier that opens | When it opens (story-only 80/80 · mixed · 60/60) |
|---|---|---|
| R1 Street (cap L12) | **T1** at L0 | R1 kid1 is the stock car at L0, so mods apply from kid2 (L1) on. All profiles get the same. |
| End of R1 | **Aero** (one, at the current tier) | Available from the start of R2 |
| R2 Wangan (cap L29) | **T2** at L13 | kid1 is raced at L12 on the R1 T1 set; T2 from kid2 (L14) · same · 60/60 grinds to L14 before kid1, so T2 is there for all of R2 |
| R3 Touge (cap L46) | **T3** at L30 | kid1 at L29 on the R2 T2 set; T3 from kid2 (L31) · same · 60/60 grinds to L33 before kid1 |
| Pre-finale arc (caps L64 / 79 / 94 / 115) | **T4** at L47 + the P1 win | P1 is raced at L43 (story-only) or L46 (others) on the T3 set. After P1 the player is at L49–50, so T4 is available from P2 on. No new tier after that. |
| Finale F1–F4 | none | The T4 set is rebalanced by buying at the M11 / M21 / M31 district changes (before F2 / F3 / F4) |

**Mods bought per tier, per scheme** (bought mods keep their stat; P = power, H = handling, E = endurance):

| Scheme (slots) | R1: T1 | R2: T2 | R3: T3 | Arc step 1 (F1): T4 | Before F2 (M11) | Before F3 (M21) | Before F4 (M31) | **Total T4** | Season total |
|---|---|---|---|---|---|---|---|---|---|
| A (6 fixed) | 6: PPHHEE | 6: PPHHEE | 6: PPHHEE | 6: PPHHEE | 0 | 0 | 0 | **6** | 24 |
| B (6 free) | 6: PPHHEE | 6: PPHHEE | 6: PPPPHH | 6: PPPPHH | +2 E | 0 | 0 | **8** | 26 |
| **C (4 free)** | **4: PPHE** | **4: PHEE** | **4: PPHE** | **4: PPHE** | **+1 E** | **+1 P** | **0** | **6** | **18** |
| D (8 free) | 8: PPPPHHEE | 8: PPHHEEEE | 8: PPPHHEEE | 8: PPPPHHEE | +2 E | +1 P | +1 P | **12** | 36 |

- **Equipped T4 sets for C:** F1 PPHE, F2 PHEE, F3 PPPH, F4 PPPH.
- **Equipped T4 sets for D:** F1 PPPPHHEE, F2 PPHHEEEE, F3 PPPPPHHE, F4 PPPPPPHH.
- **Aero is optional.** Each scheme can add one aero per tier from R2 on. It isn't in the counts because it adds 0 to −0.7 points in C and D.
- **For comparison:** the live draft economy (6 slots) buys 5 regular T4 + 1 aero over the arc. The story-only 80/80 player can only afford them gradually: 1 after P1, 3 by P4, 5 by M12, and the aero by M21. Mixed and 60/60 players have 4–5 after P1 and the aero by P3–P4.

**Races before a new tier opens** (R2 kid1 at L12, R3 kid1 at L29). They carry the previous round's set into the new district. Two options were checked for C and D:
- **(a) Keep the old set.** C: R2 kid1 car 35.1 / 25.0 / 40.0, R3 kid1 38.7 / 25.0 / 36.3. kid1 still clears for 60/80 and 80/60 at 53–62% and for 80/80 at 86–87%. Bosses, story minimums and every grind count are unchanged from the C and D rows above.
- **(b) Buy extra old-tier mods** to rebalance for that one race. C needs +1 T1 E and +1 T2 P; D needs +3 T1 E and +1 T2 P. It changes nothing measurable (kid1 moves ±2–5 points, and grinds are unchanged), so (a) is the recommendation and no extra old-tier mods are needed.

## Recommendation
- **Scheme C: 4 mod slots, single-stat mods, the stat picked when fitted.**
  - Points per mod: **T1 223, T2 256, T3 293, T4 501**.
  - Aero: same total, free pool **22 / 25 / 29 / 50**, base = total − pool.
  - Every district tune is one 2-1-1 pattern: Street PPHE, Wangan PHEE, Touge PPHE plus skill points. Balance is within 0.4 points of live (F3 +0.7 to +1.3, back on the tune), grinds are identical, the car stays inside 25–50%, and aero is never dominant.
  - The full T4 set becomes 3 regular + 1 aero, against 5 + 1 today.
- **Alternative: scheme D, 8 slots of 112 / 128 / 147 / 251** (pool 11 / 12 / 14 / 25). The balance is the same, with finer choices (4-2-2 patterns), but twice as many purchases.
- **Not recommended: 6 slots** (A or B). The car can't reach the 2:1:1 tunes, and R3 breaks the 50% story floor and the 30% 60/60 floor.
- **Rebalancing is by buying (Austin):** a bought mod keeps its stat, and the player buys and swaps in new ones. For scheme C that means 2 extra T4 mods over the arc (6 T4 mods for 4 slots). If the player skips them and keeps one T4 set, 60/60 grinds 2 more before F2.

## Assumptions and flags
1. **Constant split per segment.** Each segment uses its car split at the segment cap for every race in it. Splits inside a round drift a little as the 1.07 clip scales mods (mods are scaled proportionally when they overfill). The 80/80 story-only player arrives below cap and is given the cap split.
2. **Off-tune win rates are deltas against the rt1 tune.** Splits with HAN ≠ 25% were swept fresh (`sweep_splits.py`, N=150 per style on the same seeds as rt1, so the deltas are paired). An exact replay of the Street tune reproduced rt1 with 0.0 difference. HAN = 25% splits use the rt1 interpolation, as live does. Noise is about ±2 points (skill-points-v1 rt2 replicate).
3. **Rebalancing by buying (confirmed by Austin, 2026-11-14).** A bought mod keeps its stat. The player rebalances by buying new mods of the stat they need and swapping them in. Owned mods can be re-equipped at no cost. The equipped sets in the tables above are exactly what this rule produces, so the C and D numbers stand. The cost is the extra purchases listed in "Mod unlocks over the season" below. The "T4-locked" runs show what happens if the player buys only one T4 set.
4. **The policy minimises distance to the tune.** That is not the win-maximising split on the hardest tracks: Wangan W3 likes extra HAN, which is why A/B lift F2. A smarter player could do slightly better in any scheme.
5. **Economy not re-run.** The campaign walk banks cash and assumes full mods, as live does. The arc's draft T4 shop still prices a 6-slot set. Keeping the same total spend would need per-mod prices ×1.5 for 4 slots or ×0.75 for 8 slots, with `T4_PACKAGE` at 3+1 or 7+1. This needs an econ re-check before going live; prices were not changed here.
6. **The arc uses the draft econ-v1 walker** (live table plus deltas). The live baseline in the first column is the skill-points-v1 `verify_live` path.
7. **The car band 25–50% is applied to the whole car (skill points + mods) as well as to skill points.** With HAN at 25% in every tune, the HAN floor is the binding constraint.

Files: `unlocks.py` → `unlocks.txt` / `unlocks.json` / `purchase_sequence.json`; `mod_schemes.py` (schemes, fill check, split walk) → `mod_schemes.txt`; `sweep_splits.py` → `splits.json` (+ logs); `mods_eval.py` → `mods_eval.txt` / `mods_eval.json`.
