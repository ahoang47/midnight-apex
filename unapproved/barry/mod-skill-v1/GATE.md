# mod_skill: SETUP STUDY replaces the climb recommendation (Austin 2026-11-19 4:21 PM PT), Barry DRAFT

> **LIVE 2026-11-19 (Austin, direct, 6:39 PM PT: "Approved for all").** The setup study (commit 203e3b6 values: S1, M13r, raised
> boss floor / story XP for a 66-68 % boss, the oh1/oh2 changes for G3c, cap 15, ledger floors, no underdog, Mk 115/124/133) is
> ported into the live sim: `sim/velocity_shift/mod_skill.py`, `equations.py` "mod_skill progression", `MatchConfig.kappa_mult`,
> `sim/config/mod_skill_climb_v1.json`, `sim/tests/test_mod_skill.py`; design/07 top. This folder is now the study record.

> **See [SETUP-STUDY.md](SETUP-STUDY.md)** (criteria G1-G5 fixed before runs, scorecard, journeys, floors, live-sim lock check).
> Austin's decisions on the climb draft (2026-11-19): **no underdog bonus** (C5 below REJECTED); keep it brutal for 60/60; crews
> stat-locked with floors on earned points. The single recommendation in C3 below is **superseded** by the setup study
> (recommended there: S1, 13 mandatory with story XP retuned, non-mandatory cap 15). Unapproved; nothing live.

---

# mod_skill: THE CLIMB (Austin 2026-11-19), Barry DRAFT

> **Direction (Austin, direct, 2026-11-19):** "Hmm, that seems cheap. The boss needs to be a difficult build up, and you've taken
> the easiest way to the top. The gameplay feel should be the player learning how to read the lines of the district, the
> lieutenants and bosses need to feel like a climb, and the player should be encouraged to fight them even without full stats."
> **This rejects the mandatory-20 "no retune" finding below (042a725)**, which is kept and marked rejected. Kept from it: 20
> mandatory races per round (7 story + 13 required wild encounters), 0.80 random AI QTE, AI heat rules, the fixed mod layout.
> **Unapproved and nothing live. Nothing in `sim/` changed.** Code: `climb_grid.py` → `climb_grid.json` (engine grid, n 600/cell),
> `climb_eval.py` → `climb_eval.json` (rung budgets), `climb_verify.py` → `climb_verify.json` (V0) and `climb_verify_K50.json`
> (K50), `climb_boss_fix.py` → `climb_boss_fix.json` and `climb_street_check.py` → `climb_street_check.json` (boss searches).
> All numbers marked "engine" are the live SimulationRunner at n = 6,000 (2,000 per boss style, hard track, ties = half).

## C1. Why the old answer was cheap, and the design model
- In 042a725 the mandatory 20 alone reach the round cap at every boss, so the boss is met fully built and the ladder before it
  is a walk (lowest non-boss 60/60 was 23-38). Stats, not reading, carried the player.
- **New model ("expected build"):** the mandatory path lands at **65 % of the round's mod XP at the boss** (F = 0.65), not the cap.
  Points rise linearly over the 20 mandatory slots; rungs sit at slots 1, 4, 7, 10, 13, 16, 20. Round entry = previous cap −
  0.35 × previous room (a player who did no optionals). **Full build = the round cap, reached only with ~15 optional wild-encounter
  wins per round.**
- **XP retune this needs (draft):** mandatory XP per round = **346 / 519 / 559** points (3,000→3,346, 3,346→3,865, 3,865→4,424).
  Keep wild-encounter XP 13 / 12 / 14 (13 required wins = 169 / 156 / 182), so **pre-boss story XP drops to ≈177 / 363 / 377**.
  The catch-up rule must be off or folded into these numbers. Gap to full build: 186 / 179 / 204 points = **15 / 15 / 15
  optional wins** at 13 / 12 / 14 XP.
- **Rung budgets** (budget = points / 10 / r) are set so 80/80 at the expected build falls along a climb:
  **kid1 95, kid2 90, mat1 84, mat2 78, oh1 70, oh2 62, boss ~50**. The boss is then placed by its **full-build** r under the
  boss window (full 80/80 ≤ 95, full 60/60 ≥ 30).

## C2. Options (per-rung win %, 60/60 / 80/80 at the expected build; engine n = 6,000 unless marked grid)
**Option A, "build climb": live combat (V0), only XP and budgets change.** Engine (`climb_verify.json`, boss from `climb_boss_fix.json`).

| Rung | Street (R1) | Wangan (R2) | Touge (R3) |
|---|---|---|---|
| kid1 | 47.5 / 97.4 | 62.3 / 95.0 | 56.3 / 92.4 |
| kid2 | 16.6 / 90.1 | 31.5 / 89.2 | 38.7 / 88.0 |
| mat1 | 9.9 / 85.3 | 19.3 / 85.4 | 20.8 / 83.6 |
| mat2 | 4.3 / 79.5 | 5.6 / 78.3 | 14.6 / 79.1 |
| oh1 | 1.8 / 74.7 | 1.8 / 70.9 | 6.9 / 71.3 |
| oh2 | 0.4 / 64.2 | 0.9 / 65.5 | 2.7 / 66.1 |
| boss, expected (65 %) | 0.05 / 37.2 | ≈0 / 56.1 | 0.75 / 53.6 |
| boss 80/80 at 60 % / 70 % | 25.0 / 49.5 | 49.4 / 61.9 | 41.7 / 60.1 |
| **boss full build** | 36.8 / 94.3 (r 1.050) | 33.2 / 88.6 (r 1.036) | 37.6 / 94.0 (r 1.0589) |

- Rung r (kid1 … oh2): Street 1.0205 / 0.9977 / 1.0058 / 0.9968 / 0.99 / 0.9831; Wangan 1.046 / 1.02 / 1.019 / 1.0048 /
  0.9952 / 0.9888; Touge 1.0635 / 1.04 / 1.0361 / 1.0297 / 1.0212 / 1.0127.
- **Street problem:** its EN-heavy boss curve is steep. The full-build ceiling caps r at 1.050 (engine: r 1.052 gives 95.07),
  which leaves an under-built strong reader only 25-49 %. Relaxing Street to r 1.058 (full 80/80 96.5) gets ≈37 / 56.

**Option B, "reader's climb": kappa × 0.5 on all story races (K50)** (less stat weight per point, so lines decide more).
Engine (`climb_verify_K50.json`); boss full r Street 1.062, Wangan 1.045, Touge 1.068.

| Rung | Street | Wangan | Touge |
|---|---|---|---|
| kid1 | 46.0 / 96.2 | 61.9 / 95.3 | 55.4 / 95.3 |
| kid2 | 16.2 / 89.9 | 28.8 / 88.5 | 40.0 / 87.0 |
| mat1 | 9.5 / 85.1 | 16.8 / 84.2 | 18.4 / 82.3 |
| mat2 | 4.2 / 79.4 | 5.2 / 77.8 | 11.5 / 77.7 |
| oh1 | 1.8 / 74.9 | 1.8 / 70.7 | 6.3 / 70.0 |
| oh2 | 0.5 / 64.3 | 0.7 / 63.9 | 2.5 / 64.4 |
| boss, expected | 0.4 / 52.3 | 1.2 / **64.0** | 1.9 / 58.7 |
| boss 80/80 at 60 % / 70 % | 43.2 / 60.5 | 58.5 / 70.2 | 53.2 / 68.4 |
| **boss full build** | 31.8 / 93.4 | 37.8 / 90.4 | 35.8 / 94.6 |

- Fixes Street, but **flattens the top in Wangan and Touge**: the Wangan boss (64.0) is no harder than oh2 (63.9) for a good
  reader, and both exceed 60 at 70 %. Lowering their boss r runs into the full 60/60 ≥ 30 floor (grid: r 1.039 / 1.062 sit at
  30.0), so the boss stays ≈ 59-60. B is a global combat-tuning change (`KAPPA_BY_LENGTH`).

**Option C, "driver climb": AI QTE rises per rung (kid 0.70 / mat 0.76 / oh 0.82 / boss 0.86)**, alone (Q) or with kappa × 0.7
(K70Q). **Grid only (n 600/cell, interpolated, not engine-verified).** Rung r at the expected build barely moves, except kids get
easier r (Q kid1 1.006 / 1.036 / 1.053 vs V0 1.021 / 1.046 / 1.064). Boss 80/80 at 60 % / 70 %: Q 40.7 / 59.5, 42.9 / 58.0,
41.4 / 58.6; K70Q 41.3 / 58.8, 51.4 / 64.3, 42.0 / 58.1. It reads as "the bosses drive better", which is **per-character AI skill:
story/character territory, flag for Desmond.** Plain K70 (grid) behaves like a milder B.

## C3. Recommendation: Option A, plus kappa × 0.5 on the Street boss race only (SUPERSEDED by SETUP-STUDY.md)
- **Everything is engine-verified at n = 6,000.** Live combat for every rung and for the Wangan and Touge bosses (Option A
  table), and **K50 only for the Street boss** at full r **1.062** (`climb_street_check.json`):

| Boss | full 60/60 / 80/80 | 80/80 at 60 % / 65 % / 70 % | 60/60 at 65 % | budget (full r) | live budget |
|---|---|---|---|---|---|
| Street (K50) | **31.8 / 93.35** | **43.2 / 52.3 / 60.5** | 0.4 | 332.58 (1.062) | 337.57 |
| Wangan (V0) | **33.2 / 88.57** | **49.4 / 56.1 / 61.9** | ≈0 | 390.35 (1.036) | 388.72 |
| Touge (V0) | **37.6 / 93.98** | **41.7 / 53.6 / 60.1** | 0.75 | 437.05 (1.0589) | 440.80 |

- **(a) Climb:** 80/80 at the expected build falls kid1 → boss 97 → 52 (Street), 95 → 56 (Wangan), 92 → 54 (Touge), every step
  down. 60/60 at the expected build falls to ≈0-3 by oh2: a weak reader has to build (optionals) to pass the lieutenants.
- **(b) Reading beats stats:** an 80/80 reader at 60-70 % of the round's XP wins **42-62 %**; a 60/60 driver at full build wins
  **32-38 %**. Full-build 80/80 stays ≤ 95 (88.6-94.0).
- **Why not B everywhere:** it softens the Wangan/Touge tops (C2). **Why Street:** its boss window is the only one too narrow in
  V0. Street kappa × 0.5 is a per-race combat setting (no story or art); if Austin prefers one global rule, take B and accept a
  boss ≈ oh2 in Wangan.
- **Weak spot:** full 60/60 ≈0 → 32-38 between 65 % and 100 % build means a weak reader must do most of the ~15 optionals.
  That is the "difficult build-up", by design.

## C4. Targets (proposed, replacing "boss only" pass/fail)
- Keep: **full 80/80 ≤ 95, full 60/60 ≥ 30.**
- Add: **under-built 80/80 (60-70 % of round XP) 40-60** (met: 41.7-61.9, the 70 % ends are 0.1-1.9 over); **full 60/60 30-50**
  (met: 31.8-37.6); **climb**: expected-build 80/80 strictly falling kid1 → boss (met).
- Reasoning: the boss is a skill check, not a stat check. The top two targets separate readers from builders, and the climb
  target stops a boss from being easier than its lieutenants.

## C5. ~~Reward for fighting early: "underdog" bonus (draft)~~ REJECTED by Austin 2026-11-19 (no underdog bonus)
- **Underdog purse: +25 % of the rung purse** for beating a lieutenant (mat1, mat2, oh1, oh2) or the boss below the round cap.
  Lieutenant purses 2,500 / 2,875 / 3,375 ×4 plus boss 8,000 / 9,200 / 10,800 give at most **+$4,500 / +$5,175 / +$6,075 per round** (R1 story
  purses total $20,000, so ≤ +22.5 %). +50 % would be $9,000 / $10,350 / $12,150 (too rich, R1 +45 %).
- **Underdog XP:** each such win also pays one wild encounter's XP (13 / 12 / 14), at most 5 per round (65 / 60 / 70 points),
  saving ~5 of the ~15 optional wins. It never raises the boss, because the round ceiling binds.
- **Free retries:** keep the retry fee at 0 (live), so failed early attempts cost only time.
- **Not proposed by me:** a unique trophy mod, decal, or barks. That needs Desmond (story) and Arthur (art).

## C6. For Austin / Desmond
1. Austin: pick A + Street-boss K50 (recommended), A with Street relaxed to full 80/80 ≈ 96.5, or B everywhere.
2. Austin: approve the XP retune (mandatory path → 65 %, pre-boss story XP ≈ 177 / 363 / 377, catch-up off) and the new targets.
3. Austin: underdog bonus at +25 % purse and +1 wild encounter of XP per lieutenant/boss win below cap.
4. **Desmond flags:** Option C's per-rung AI QTE is per-character driving skill; any underdog trophy mod, decal, or barks. The
   Street-boss kappa change has no story hook, but Desmond may want one ("the Street boss's race is all lines").

---

# mod_skill: MANDATORY 20 RACES PER ROUND (Austin 2026-11-19), Barry DRAFT

> **REJECTED by Austin (2026-11-19): "Hmm, that seems cheap … you've taken the easiest way to the top."** The "no retune"
> finding below is kept for reference; the 20 mandatory races stay, and the climb draft above replaces the rest.

> **Direction (Austin, direct, 2026-11-19):** "I want a mandatory 20 races per round." Mandatory = story races plus required
> wild-encounter wins (story beats). This supersedes the N = 5 story-beat recommendation below (kept, marked superseded).
> **Unapproved and nothing live. Nothing in `sim/` changed.** Code: `mandatory20.py` → `mandatory20.json`. `walk.py`
> `beats` mode now also accepts a per-round N.

## M1. Counts
- **Story races per round (live ladder `E.LADDER_RUNGS`): 7** in every round. That's kid1 and kid2 (10 turns each),
  mat1 and mat2 (20), oh1 and oh2 (20), and the boss (30).
- **Required wild-encounter wins: N = 20 − 7 = 13 per round**, spread before kid2 … boss (2 before each rung, 3 before the boss).
- **Interpretation:** "20 races" = **20 required wins (race slots)**. A loss is a retry and is not counted, so the
  20 are fixed for every player.
  - **Alternative ("20 attempts including losses"):** this can't be a fixed rule, because attempts depend on skill. For
    reference, the mandatory path takes 20.3 / 20.6 / 20.8 expected attempts at 80/80 (so the two readings almost match for a
    good player) and 28.2 / 29.0 / 35.8 at 60/60.
  - **The Prologue's 3 scripted races come before Round 1 and are not counted.** If they counted toward R1, R1 would get
    N = 10: the boss would be met at 3,497 points, 15.8 / 87.8, which fails 60/60 ≥ 30. Keep N = 13.

## M2. Mandatory path (7 story + 13 wild encounters), live sim, live boss r (R1 / R2 / R3)
| | R1 Street | R2 Wangan | R3 Touge |
|---|---|---|---|
| Car points at boss / cap | 3,532 / 3,532 (at cap) | 4,044 / 4,044 (at cap) | 4,628 / 4,628 (at cap) |
| Boss r (live) | 1.046 | 1.0398 | 1.0492 |
| Boss win 60/60 / 80/80, table | 31.2 / 93.9 | 40.5 / 92.4 | 31.2 / 91.4 |
| **Boss win, engine (6,000 races)** | **32.02 / 93.78** | **40.73 / 92.22** | **30.75 / 91.77** |
| Lowest non-boss race 60/60 | 35.8 (mat2) | 38.3 (mat2) | 23.2 (mat2) |
| Expected races (retry on loss), 60/60 / 80/80 | 28.2 / 20.3 | 29.0 / 20.6 | 35.8 / 20.8 |
| Cash after the round (cumulative) | $10,550 (debt paid) | $39,532 | $72,345 |

- **Engine source:** `gate_engine_check.json`. The live SimulationRunner was run at exactly these boss r with on-tune builds
  and is deterministic, so the inputs are identical.
- **All three bosses pass** 60/60 ≥ 30 and 80/80 ≤ 95 at the **live** boss r, so **no boss retune is needed**. Touge 60/60
  has only 0.75 points of headroom (about 1.25 SE).
- **Comparison:**
  - N = 5 path at the live boss budgets: 2.9 / 5.1 / 6.8 at 60/60, which is why that draft needed a retune.
  - No wild encounters: 0.1 / 0.8 / 0.5.
  - Lowest non-boss 60/60 rises from 11.8 / 14.6 / 9.4 (N = 5) to 35.8 / 38.3 / 23.2.

## M3. Cap and overshoot finding
- **The mandatory path reaches the cap at every boss**, so the ceilings bind. Extra optional wins add no XP headroom, and
  **the full-build overshoot from the N = 5 draft disappears**.
  - Checked: with 16 or 20 wild-encounter wins per round, the boss row is identical: 3,532 / 4,044 / 4,628 points, r 1.046 /
    1.0398 / 1.0492, 31.2 / 93.9, 40.5 / 92.4, 31.2 / 91.4.
  - Optional wins still pay cash, and they reach the cap earlier inside a round, which makes the lieutenant races easier.
    They never change the boss.
- **Wins needed to cap (prior rounds at N = 13): 13 / 13 / 12.**
  - R1 and R2 cap on the 13th win (it is partly used: 9 of 13 points in R1, 11 of 12 in R2).
  - In R3 **one mandatory win is cash only**: the 13th, whose 14 XP is lost.
  - The current XP 13 / 12 / 14 therefore already lands the cap at the boss in R1 and R2.
- **Optional XP tweak (draft): R3 wild-encounter XP 14 → 12** (the lowest value in 0.1 steps that still caps with 13 wins). The
  cap then lands on the 13th win in every round, with no cash-only mandatory win. The boss is unchanged (31.2 / 91.4), and R3's
  lowest non-boss 60/60 goes 23.2 → 20.4.
  - Leaving 14 in place is also fine: it just makes the last R3 beat cash only.
  - R1 and R2 can't go lower: 12.5 in R1 gives 3,529 at the boss, and 11.5 in R2 gives 4,038, both short of the cap.

## M4. For Austin
1. Confirm the reading: 7 story races + 13 required wild-encounter wins = 20 mandatory wins per round; losses are retries; the
   Prologue is not counted.
2. Boss r stays live (no retune), and the full-build overshoot is gone.
3. R3 wild-encounter XP: keep 14 (one cash-only beat) or lower it to 12 (cap lands on the 13th beat).
4. Still open: the finale r retune.

---

# ~~mod_skill boss gate: STORY-BEAT wild encounters (Austin 2026-11-19), Barry DRAFT~~ SUPERSEDED by the mandatory-20 section above (Austin 2026-11-19)

> **SUPERSEDED (Austin 2026-11-19, "I want a mandatory 20 races per round"):** the N = 5 recommendation, its boss retune and
> the optional-XP cap below no longer apply. Kept for the record.
>
> **Direction (Austin, direct, 2026-11-19):** "Make a few wild-encounter wins required story beats each round, no build check
> at the boss." This section is the draft of that direction. **It is unapproved and nothing here is live.** Nothing in `sim/`
> changed. ~~Gate A (boss locked until all four mods are full)~~ was reconsidered by Austin on 2026-11-19 (bosses behind a
> maxed car feel bad); its study is kept further down for the record.

## S1. Model
- Each round has **N required wild-encounter wins**, placed as story beats between story races. Extra wild encounters stay
  optional (non-mandatory races). There is **no build check at the boss**.
- The beats are spread evenly over the six slots before kid2 … boss, with the remainder going to later slots
  (`walk.py` mode `beats`). With **N = 5** there is **one beat before each lieutenant race (mat1, mat2, oh1, oh2) and one
  before the boss**.
- Setup:
  - Live sim at 5cc6b97: 0.80 random AI QTE, boss r 1.046 / 1.040 / 1.050, Street boss 25/25/50, v2 tables.
  - Fixed layout P/E/E flex. Ceilings 133 / 261 / 407 (caps 3,532 / 4,044 / 4,628). Wild-encounter XP 13 / 12 / 14 (code
    `grind_xp`). Approved story table from `fixed_layout.json`, with the walk_boss_flag fix applied.
- The "min-path player" wins exactly the N beats and no optional wild encounters.
- Code: `beats.py` → `beats.json`, `beats_engine_check.py` → `beats_engine_check.json`.

## S2. Sweep N = 2..8 at the LIVE boss budgets (min-path player; R1 / R2 / R3)
| N | Car points at boss (cap 3,532 / 4,044 / 4,628) | Boss r at live budget | Boss win 60/60 / 80/80 | Lowest non-boss 60/60 | Exp. races 60/60 | Exp. races 80/80 | Cash after round (cumulative) |
|---|---|---|---|---|---|---|---|
| 0 (ref: no wild encounters) | 3,367 / 3,853 / 4,446 | 0.997 / 0.991 / 1.009 | 0.1/40.6; 0.8/58.4; 0.5/48.1 | 5.2 / 5.5 / 2.6 | 1058.5 / 203.1 / 314.8 | 9.1 / 9.6 / 10.4 | $6,400 / $24,160 / $47,320 |
| 2 | 3,393 / 3,884 / 4,482 | 1.005 / 0.999 / 1.017 | 0.4/49.7; 2.0/65.8; 1.5/58.3 | 7.7 / 7.1 / 4.9 | 293.2 / 108.0 / 135.9 | 10.6 / 11.1 / 11.6 | $6,785 / $26,525 / $51,170 |
| 3 | 3,406 / 3,899 / 4,499 | 1.009 / 1.003 / 1.021 | 0.7/53.7; 2.9/69.4; 2.4/63.3 | 7.7 / 10.1 / 5.6 | 180.2 / 80.9 / 98.1 | 11.4 / 11.8 / 12.3 | $6,978 / $27,708 / $53,095 |
| 4 | 3,419 / 3,914 / 4,517 | 1.013 / 1.007 / 1.025 | 1.6/60.0; 3.8/72.9; 4.6/68.2 | 11.8 / 11.2 / 8.1 | 94.6 / 66.7 / 68.4 | 12.2 / 12.6 / 13.0 | $7,170 / $28,890 / $55,020 |
| **5** | 3,432 / 3,930 / 4,535 | 1.017 / 1.011 / 1.029 | 2.9/67.2; 5.1/76.0; 6.8/73.1 | 11.8 / 14.6 / 9.4 | 64.7 / 55.5 / 55.4 | 12.9 / 13.4 / 13.7 | $7,362 / $30,072 / $56,945 |
| 6 | 3,445 / 3,945 / 4,553 | 1.020 / 1.015 / 1.033 | 4.2/74.1; 7.3/77.9; 9.9/77.5 | 16.0 / 19.0 / 13.0 | 49.8 / 44.5 / 44.5 | 13.7 / 14.3 / 14.4 | $7,555 / $31,255 / $58,870 |
| 7 | 3,458 / 3,960 / 4,570 | 1.024 / 1.019 / 1.037 | 5.8/77.7; 9.5/79.7; 13.2/81.5 | 16.0 / 20.1 / 13.6 | 44.3 / 40.7 / 41.8 | 14.7 / 15.2 / 15.3 | $7,748 / $32,438 / $60,795 |
| 8 | 3,471 / 3,975 / 4,584 | 1.028 / 1.023 / 1.040 | 7.5/81.4; 13.8/82.5; 15.9/84.7 | 22.1 / 25.2 / 16.7 | 38.3 / 35.1 / 38.7 | 15.5 / 16.0 / 16.2 | $7,940 / $33,620 / $62,720 |
| ref: full build (all mods maxed) | 3,532 / 4,044 / 4,628 | 1.046 / 1.040 / 1.049 | 31.2/93.9; 40.5/92.4; 31.2/91.4 | 16.0 / 16.6 / 22.4 | 41.7 / 39.6 / 38.5 | 20.5 / 21.0 / 20.0 | $10,550 / $39,532 / $71,602 |

- **Expected races** = Σ 100 / win % over the 7 story races plus the N beats; a loss means retry.
- **At the live boss budgets, no N from 2 to 8 passes the boss check**: the best is N = 8, at 60/60 7.5 / 13.8 / 15.9. The live
  boss r is tuned to the full build. With N = 2-8, the min-path car sits 1-4 % below cap power, but the boss band (60/60 ≥ 30
  to 80/80 ≤ 95) is only about 0.3-1.4 % wide in r. So bosses must be retuned to the min-path build (S3).
- **Debt** after R1 for the min-path player: $2,285 (N 2) … $140 (N 8); $1,212 at N 5. It is paid off early in R2.
- **The mid-ladder stays hard for 60/60 at any N ≤ 8**: lowest non-boss race 5-25 %. Rung budgets are unchanged in this draft.

## S3. Recommendation: N = 5, boss retuned to the min-path build
- **Why N = 5:** it's the top of Austin's "a few" (3-5), and it gives one beat before each lieutenant race and the boss.
  It has the best 60/60 mid-ladder and the fewest expected races of N 3-5. Cost at 80/80 is about 12.9-13.7 races per round,
  versus 11.4-12.3 at N 3.
- **Retuned boss** (the smallest r where min-path 60/60 ≥ 30, rounded up to 0.001; boss table, hard track):

| Round | Min-path boss r (new) | Boss budget new / live | Same boss vs a full build: r | Min-path 60/60 / 80/80 (table) | **Engine, min path (6,000 races)** | Full build (table) | **Engine, full build** |
|---|---|---|---|---|---|---|---|
| R1 Street | 1.046 | 328.07 / 337.56 | 1.0763 | 31.2 / 93.9 | **32.02 / 93.78** | 64.0 / 98.3 | **65.80 / 98.98** |
| R2 Wangan | 1.034 | 380.04 / 388.72 | 1.0635 | 30.5 / 90.0 | **31.98 / 89.30** | 66.0 / 98.4 | **68.82 / 98.00** |
| R3 Touge | 1.049 | 432.33 / 440.81 | 1.0698 | 30.8 / 91.2 | **30.25 / 91.80** | 55.3 / 97.8 | **58.30 / 97.97** |

- **In live terms:** each boss budget drops 2.8 / 2.2 / 1.9 %. As `BOSS_TARGET_R` (cap power ÷ budget), that is 1.0763 / 1.0635 /
  1.0698. N = 3 and N = 4 retune to the same min-path r, with budgets 325.58 / 377.09 / 428.93 and 326.83 / 378.56 / 430.63.
  Their full build gets 99.0 / 99.2 / 99.0 and 98.6 / 98.9 / 98.4 at 80/80.
- **Engine SE** is about 0.6 at 60/60 and 0.13-0.4 at 80/80. Touge min-path 60/60 at 30.25 is only about 0.4 SE above 30.
- **Flag: a full build goes to 98-99 % at 80/80** (60/60 58-69 %) against the retuned boss. The boss band is very narrow:
  - min-path 60/60 ≥ 30 needs r ≥ 1.0455 / 1.034 / 1.049;
  - 80/80 ≤ 95 needs r ≤ 1.049 / 1.0485 / 1.0615.
  - That leaves about 0.3 % / 1.4 % / 1.2 % of headroom. In Street, a single optional win (13 points) already gives 95.3.

## S4. Mitigation options for the full-build overshoot (N = 5, numbers from `beats.json`)
1. **Recommended: cap the XP from optional wild encounters at K extra wins per round (cash always pays).**
   K is the largest number of extra wins that keeps 80/80 ≤ 95 against the retuned boss: **0 / 3 / 3**.
   - Street: optional wins are cash-only.
   - Wangan and Touge: the first 3 optional wins also pay XP.
   - Engine at K = 3: Wangan 48.72 / 93.77, Touge 39.53 / 94.33. Street at K = 3 would be 45.43 / 96.72, which is why
     Street gets K = 0.
   - Table at K = 1 / 2 / 3, 80/80: Street 95.3 / 95.8 / 96.3, Wangan 91.7 / 93.1 / 94.2, Touge 92.7 / 93.7 / 94.6.
   - If Austin accepts Street up to about 96-97 as the reward for optional play, Street can take K = 3 like the others.
   - With this cap, ceilings and caps stay as they are (133 / 261 / 407), but a car only fills to the cap through story XP plus
     beats plus K.
2. **Not recommended: lower each round's ceiling.** Lowering so a full build sits at 80/80 = 95 against the retuned boss
   (re-walked and iterated round by round) gives ceilings **110 / 227 / 364** (caps 3,440 / 3,908 / 4,456).
   - A full build then needs 6 / 10 / 9 wild-encounter wins and meets the boss at 33.9 / 94.8, 51.2 / 94.7, 38.1 / 94.7.
   - But a lower R1 and R2 cap means less catch-up XP and a weaker car going into the next round, while the story-race budgets
     are unchanged. The min-path player's lowest non-boss 60/60 falls to 11.8 / 3.7 / 0.1, and expected 60/60 races to
     64.7 / 215 / 3,185.
   - That only works if every rung budget is rescaled too, which is a full ladder retune.
3. **Diminishing XP** for optional wins only slows the climb. Every optional win still adds power, so on its own it doesn't
   bound the full-build 80/80. It is option 1 with a soft edge instead of a hard K.
4. **Accept the overshoot:** full build at 98.3 / 98.4 / 97.8 (engine 98.98 / 98.00 / 97.97) as the reward for optional play.
   No rule needed.

## S5. Effects and open items
- **Story-only is retired** (Austin 2026-11-19): the N beats are part of the story, so the min-path player is the story path.
- **Time and cash (N = 5, min path, cumulative):**
  - Cash $7,362 / $30,072 / $56,945, versus $6,400 / $24,160 / $47,320 with no wild encounters and $10,550 / $39,532 /
    $71,602 for a full build.
  - Expected 80/80 races per round 12.9 / 13.4 / 13.7, versus about 20 for a full build.
- **Mid-ladder:** for 60/60 at the min path, the lowest non-boss race is 11.8 / 14.6 / 9.4 % (55-65 expected races per round).
  Weak readers will likely race optional wild encounters there too. That's fine under S4 option 1, because those wins still
  pay cash and the first K pay XP. A separate rung retune is outside this draft.
- **Finale:** not walked (mod_skill has no finale walk). The finale r retune is still open and is unaffected by this draft.
- **For Austin:** N (recommended 5); the boss retune (the S3 budgets); the overshoot option (recommended: optional-win XP cap
  K = 0 / 3 / 3, or accept up to about 96-97 in Street with K = 3); and the finale retune (still open).

---

# (Earlier) mod_skill boss gate ("gym gate"): Gate A study, Barry DRAFT, 2026-11-19

> **2026-11-19 (later): Gate A RECONSIDERED by Austin, gate design reopened.** Locking a boss behind a maxed car feels
> bad. Gate A ("boss locked until all four mods are full") is **not decided and not live**; it stays below as a studied
> option with its numbers. Gate B was rejected earlier the same day and stays marked rejected. No gate is chosen.
> mod_skill itself is still an unapproved draft. Nothing in `sim/` changed.
>
> ~~**DECISION (Austin, direct, 2026-11-19): Gate A.** Each round's crew boss stays locked until all four mods are full
> (car points 3,532 / 4,044 / 4,628). For a story-only player that means 13 / 13 / 12 wild-encounter wins. Austin accepted
> about 20 races per round for an 80/80 player.~~ (Reconsidered, see above.) **Gate B is rejected** (kept below, marked, for the record).
>
> **DECIDED (Austin, direct, 2026-11-19): story-only retired.** "Story only is updated via the mandatory races, those are
> part of the story." Wild encounters are mandatory races, so there is no separate story-only player type. **The story-only
> boss win criterion is retired, not replaced.** The proposed replacement ("80/80 ≥ 50 on every non-boss race") is **moot**.
> Recorded in design/07 (top) and the design/01 "Race terms" bullet. The "story-only" columns below are kept as the
> pre-decision comparison only.
>
> **Terms (Austin approved, 2026-11-19; glossary in design/01 canon, "Race terms"):**
> - **Mandatory race:** a Pokemon-style wild encounter or a story race.
> - **Non-mandatory race:** a substory or a race the player picks a fight in.
> - "Grind race" is retired. This file now says "wild encounter" where it used to say "grind". Code names (`grind_xp`,
>   `grind1`, `total_grind`, the `"grind"` JSON keys) are unchanged. Quotes from older sources keep their original wording.
>
> **Still OPEN (not decided):**
> 1. The boss-gate design (reopened 2026-11-19).
> 2. The finale r retune (§4).
>
> ~~Whether to replace the story-only criterion with "80/80 ≥ 50 on every non-boss race"~~: moot, the criterion is retired.


**Status: DRAFT, unapproved. Nothing here is live.** Austin, direct, 2026-11-19: port the Pokemon-style required grinding from
skill_tree into mod_skill (Austin's wording before the 2026-11-19 terms). Code: `gate.py` → `gate.json`, `gate_engine_check.py` → `gate_engine_check.json`, and a new `gate`
mode in `walk.py`. All numbers come from the LIVE sim at 2fe7cf8: 0.80 random AI QTE, boss r 1.046 / 1.040 / 1.050, Street
boss 25/25/50, v2 tables. They use the fixed layout (POW/HAN/EN + flex P/E/E) and the approved calibration from
`fixed_layout.json` (ceilings 133 / 261 / 407, caps 3,532 / 4,044 / 4,628, wild-encounter XP 13 / 12 / 14 (code `grind_xp`), story table with R1 boss
26.5). `walk.py` now carries the boss-cell fix from `../ai-heat-qte-v1/econ_rewalk/walk_boss_flag.patch`: boss rows read the
boss-shape cells, so the Street boss is 25/25/50.

## 1. What skill_tree actually did (sources)
- **Where:** `unapproved/barry/skill-tree-v1/` (shelved in e5b8a14 and deleted in 1fa6915). Read it with
  `git show e5b8a14:unapproved/barry/skill-tree-v1/README.md` §8 and `.../SIM_RESULTS.md` §3, sim `.../sim/run3_gyms.py`.
  The direction was recorded in 7e0febe.
- **Gate type: a WIN gate on mandatory races, not an XP or win-count threshold.**
  - README §8 (Austin 2026-11-18): "Pokemon-style rounds: multiple crews per round = gyms; each crew boss = gym leader,
    lieutenants = trainers. Mandatory road races between crews." Also: "Losing a mandatory race: **blocks progress**", and
    "Optional grind races: **stay optional**".
  - run3_gyms.py (lines 1-12): you retry until you win, and "losses give no XP [PH]". Expected attempts = 100 / win %.
- **Thresholds:** none in XP terms. The sim swept k crews × m mandatory roads. SIM_RESULTS §3 recommended **k2 m1**: 2 crews
  per round with 1 mandatory road between them, 9 mandatory races per round. That was the only layout whose story XP landed on
  the caps without wild encounters (landing 1.22 / 1.04 / 1.03, with R1 trimmed about 18% [PH]).
- **Finding:** "mandatory loss blocks + no grinds" (skill_tree's wording) **failed** under today's budgets. The crew-1 boss sat at r about 0.97-1.01,
  where 60/60 wins 0% and 80/80 wins 18-34%, so expected attempts were unbounded. It only worked with **matched budgets**
  (opponents scaled to the car's expected power): about 12 attempts per round at 60/60.
- **So there was no concrete "win N wild encounters / reach X XP" gate in skill_tree.** The real mechanism was *more mandatory races
  plus loss-blocks*, with wild encounters left optional. The closest mod_skill equivalent is below. mod_skill has one crew per round,
  and its opponent budgets are already set to the cap build, so the gate goes on the car's mod points rather than on new races.

## 2. The gate
- **Gate A (~~DECIDED~~ RECONSIDERED by Austin 2026-11-19, gate design reopened; not live): the round boss is locked until all four mods are full for the round.** In car points that is
  **3,532 / 4,044 / 4,628**: each mod at 133 / 261 / 407 earned points, with the tier bought.
  - This is the exact build the boss targets assume. Boss r and the 60/60 ≥ 30 / 80/80 ≤ 95 checks are tuned at the cap.
  - In the UI it reads as "max your mods to challenge <boss>". Wild encounters are the only XP source left once the story rungs
    run out, so for a story-only player the gate makes them mandatory races.
  - Equivalent wild-encounter wins at the gate are 13 / 13 / 12 for a story-only player (table below). Points are the rule, not wins,
    because story XP and spill vary a little.
- ~~**Gate B (optional, closer to skill_tree's "two gyms"):**~~ **REJECTED (Austin 2026-11-19).** Gate A plus a mid-round lock on mat2, the first crew lieutenant.
  It opens at **3,327 / 3,793 / 4,382 car points**. These are not picked numbers: they are the points the mixed walk has when its
  wall wild encounters stop (the 60/80 and 80/60 players clear 50%).
  - Wild encounters split 3 + 10 / 2 + 11 / 6 + 6. Gate B reproduces today's mixed path exactly for everyone.
- **Minimum gate checked (rejected):** "just enough for boss 60/60 ≥ 30". R1 needs the full cap anyway (n = 13). R2 can stop
  2 wild encounters early (4,021 points: 31.1 / 90.2) and R3 1 wild encounter early (4,626: 31.2 / 91.4). That saves about 3 wins in total for a
  rule that is harder to explain, so I don't recommend it.

## 3. Numbers (live sim, `gate.json`; boss checks at 60/60 ≥ 30, 80/80 ≤ 95)
Columns are R1 / R2 / R3. "Today story" = the optional path with no wild encounters. "Today mixed" = the optional path most players take.

| | Today story | Today mixed | Gate A (reconsidered) | Gate B (rejected) |
|---|---|---|---|---|
| Required wild-encounter wins | 0 / 0 / 0 (optional) | 13 / 13 / 12 (optional) | **13 / 13 / 12** | 3+10 / 2+11 / 6+6 (rejected) |
| Points at the boss | 3,367 / 3,853 / 4,446 | 3,532 / 4,044 / 4,628 | 3,532 / 4,044 / 4,628 | 3,532 / 4,044 / 4,628 |
| Boss r | 0.997 / 0.991 / 1.009 | 1.046 / 1.040 / 1.049 | 1.046 / 1.040 / 1.049 | same |
| Boss win 60/60 (table) | 0.1 / 0.8 / 0.5 | 31.2 / 40.5 / 31.2 | **31.2 / 40.5 / 31.2** | same |
| Boss win 80/80 (table) | 40.6 / 58.4 / 48.1 | 93.9 / 92.4 / 91.4 | **93.9 / 92.4 / 91.4** | same |
| Boss win, engine (6,000 races, SE about 0.6 / 0.35) | | | **32.0 / 93.8; 40.7 / 92.2; 30.8 / 91.8** | same |
| Lowest non-boss rung 60/60 | 5.2 / 5.5 / 2.6 | 16.0 / 16.6 / 22.4 | 5.2 / 10.8 / 5.4 | 16.0 / 16.6 / 22.4 |
| Lowest non-boss rung 80/80 | 84.1 / 70.9 / 64.8 | 89.6 / 81.5 / 85.8 | 84.1 / 77.6 / 69.3 | 89.6 / 81.5 / 85.8 |
| Expected races, 60/60 (retry on loss) | 1,059 / 203 / 315 | 41.7 / 39.6 / 38.5 | 74.8 / 47.7 / 70.8 | 41.7 / 39.6 / 38.5 |
| Expected races, 80/80 | 9.1 / 9.6 / 10.4 | 20.5 / 21.0 / 20.0 | 20.7 / 21.2 / 20.7 | 20.5 / 21.0 / 20.0 |
| Expected turns, 80/80 | 187 / 185 / 203 | 271 / 280 / 268 | 275 / 283 / 282 | 271 / 280 / 268 |
| Cash after the round (cumulative) | $6,400 / $24,160 / $47,320 | $10,550 / $39,532 / $71,602 | same as mixed | same as mixed |
| Debt left after R1 | $3,000 | $0 | $0 | $0 |
| Mod spend (cumulative) | $600 / $2,840 / $6,680 | same | same | same |

Notes:
- **Engine check** (`gate_engine_check.py`): live SimulationRunner at the exact boss r the gated player arrives with (cap power
  ÷ boss budget), on-tune, same seeds as `../ai-heat-qte-v1/verify_boss_live.py`.
  - Street 32.02 / 93.78, Wangan 40.73 / 92.22, Touge 30.75 / 91.77. All pass.
  - Touge 60/60 has only 0.75 points of headroom, about 1.25 SE. That is the same thin margin as today's mixed path at the cap.
- **Expected races** = Σ 100 / win % over the 7 rungs plus every wild encounter; a loss means retry. Story 60/60 is effectively a wall
  today (the R1 boss at 0.1% means about 1,000 tries). Wild-encounter wins are nearly certain: about 13.1 attempts for 13 wins at 60/60.
- **Time vs today's optional path:** the gate adds nothing for mixed or hard players. They already race wild encounters to the cap before
  the boss (mixed 13 / 13 / 12; hard 13 / 13 / 14, identical boss rows). It adds **13 / 13 / 12 wild-encounter wins** (about +11.6 / +11.6 /
  +10.3 races, +88 / +98 / +79 turns at 80/80) only for the story-only player. That player gets +$4,150 by the end of R1, and
  by R3 is $24,282 ahead on the cumulative wallet: the wild-encounter purses pay the R1 debt off in R1.

## 4. Effects on open issues
- **Story-only criterion (80/80 ≥ 50 at the boss on story XP only):** **RETIRED (Austin 2026-11-19)**, independent of any gate: wild encounters are mandatory races and part of the story. Under Gate A it would also have disappeared. Nobody can reach a boss on story XP
  alone, so every boss is fought at the cap: 80/80 is 93.9 / 92.4 / 91.4 and 60/60 is 31.2 / 40.5 / 31.2. This settles today's
  R1 / R3 fails (40.6 / 48.1) by design. If a story-side check is still wanted, the natural replacement is "80/80 ≥ 50 on every
  non-boss race". ~~OPEN~~ **Moot: the story-only criterion is retired, not replaced (Austin 2026-11-19).**
  - Gate A passes it: lowest 84.1 / 77.6 / 69.3.
  - Gate B (rejected) would pass it: lowest 89.6 / 81.5 / 85.8.
- **Finale out of band: still there, and the gate doesn't change it.** The gate only decides how the player arrives at each
  round boss, and gated players arrive at the same cap build the finale check already used. Live F1-F4 at 80/80 are
  97.5-98.6 and need their own r retune. **OPEN, not decided (Austin 2026-11-19).** mod_skill has no finale walk (README Limits), so I did not re-walk the finale.
- **Gate A vs B tradeoff** (B rejected 2026-11-19; A later reconsidered, gate design reopened; kept for the record):
  - A is one simple rule ("max your mods"). It keeps the mid-round lieutenant walls as they are for weak readers: 60/60 wins
    5-11% at mat2 to oh2 for story-only players, so they would likely race wild encounters there anyway.
  - B is closer to skill_tree's two gyms per round and removes that mid-round wall: lowest 60/60 is 16 / 17 / 22. It costs the
    same total wild encounters, but it is a second gate to explain and a second number per round.
- **Wild encounters become mandatory races for the story-only path.** That goes against skill_tree's "optional grind races
  stay optional" decision, but it matches design/01's standing rule "grind stays mandatory" (Austin 2026-11-11).
- **Catch-up XP stops firing** (no one enters a round below the previous cap). It can stay in code as a no-op or be cut.

## 5. Decisions for Austin
1. **OPEN (reopened 2026-11-19):** the boss-gate design. Gate B rejected; Gate A reconsidered by Austin (locking a boss
   behind a maxed car feels bad). ~~DECIDED: Gate A.~~
2. **DECIDED (Austin 2026-11-19):** wild encounters are mandatory races and part of the story (no story-only path). The
   13 / 13 / 12 wins and about 20 races per round at 80/80 were Gate A numbers; with Gate A reconsidered they are not a decision.
3. **DECIDED (Austin 2026-11-19):** the story-only criterion is retired, not replaced. The "80/80 ≥ 50 on every non-boss race" proposal is moot.
4. **OPEN:** separately, and unchanged by this, the finale r retune.

## Reproduce
`python3 gate.py && python3 gate_engine_check.py`. gate.py takes under a second; the engine check takes about 21 s on 8 cores.
Older outputs in this folder (`fixed_layout.json`, `results.json`, `tables.md`) were made on the pre-go-live sim and before the
boss-cell fix, so they are not rerun here.
