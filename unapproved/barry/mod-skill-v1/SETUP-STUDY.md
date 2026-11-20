# mod_skill SETUP STUDY: structures × mandatory count × non-mandatory cap, judged against Austin's goals (Barry DRAFT, 2026-11-19)

> **Scope (Austin, direct, 2026-11-19 4:21 PM PT):** compare setups against his written goals G1-G5 instead of a single
> climb recommendation. **Unapproved and nothing live. Nothing in `sim/` changed.** Fixed: 7 story races per crew (2 kid,
> 2 mature, 2 old head, 1 boss), crews stat-locked with FLOORS (earned points count, assigned or not), no underdog bonus,
> 0.80 random AI QTE, AI heat rules, fixed mod layout.

## 1. Criteria (written and fixed at 16:23 PT, BEFORE any setup run; not tuned afterwards)
Players: **strong** = 80/80 (read = timing = pacing 0.80) throughout. **Weak (fixed)** = 60/60. **Weak improving** = skill
q(a) = min(0.80, 0.50 + 0.30·a/40), a = race attempts made so far in the round (wins and losses), i.e. linear from 50/50 to
80/80 over 40 attempts. Losses are free retries. "Mandatory build" = car points on arrival with mandatory wins only (= the floor).
"Max build" = mandatory build + the non-mandatory cap's XP (capped by the round's mod ceiling; prior rounds' max carried).

| ID | Goal | Measure | Pass threshold | Why this number |
|---|---|---|---|---|
| G1a | Strong player challenged, mandatory only | 80/80 boss win % at the mandatory build, worst and best round | **40-65 %** every round | A coin-flip-ish boss (~1-2.5 attempts) is a challenge; > 65 is routine, < 40 is a wall for the target player |
| G1b | … | 80/80 expected losses over the 7 story races, per round (Σ 1/p − 1) | **1.5-4.0** every round | At least one or two lost story races per round; more than 4 starts to feel like a grind for a strong player |
| G2a | Weak can grind to win | 60/60 win % at the MAX (capped) build, worst story rung over 3 rounds | **≥ 30 %** | Same floor as the approved boss rule (60/60 ≥ 30) applied to every story rung |
| G2b | … | Weak improving, R1 Street, mandatory + capped non-mandatory (grind until the next story race is ≥ 50 % or the cap is hit): mean attempts in the round; players stuck (≥ 400 attempts on a race) | **≤ 60 attempts, 0 stuck** | 60 ≈ 3× the current 20 mandatory; beyond that the round is a slog |
| G3a | Rising climb | 80/80 at the mandatory build kid1 → boss: every step down (tolerance +1.0 for noise) and total drop | **monotone, drop ≥ 30** every round | A felt climb needs each crew member harder than the last and a clear gap kid → boss |
| G3b | Reading matters (learn the lines) | boss: 80/80 at mandatory build − 60/60 at max build | **≥ +10 pts** every round | A good reader without grinding must beat a poor reader who maxed the car |
| G4a | Challenge before full stats | min over story rungs of 80/80 at the floor (no non-mandatory XP) | **≥ 40 %** every round | A strong reader at the floor should be able to take every rung with a realistic chance |
| G4b | Brutal for weak readers | 60/60 boss win % at the floor | **≤ 10 %** every round | Weak readers must grind; at the floor the boss is near-closed to them |
| G5 | Non-mandatory cap | an explicit cap exists AND 80/80 boss win at the max build | **cap set, ≤ 95 %** every round | The cap must keep the boss a skill check (approved 80/80 ≤ 95) |

## 2. Setups simulated (live SimulationRunner, seeded; code `setup_study.py` → `setup_study.json`, `journey_setups.py` → `journey_setups.json`, scoring `setup_score.py` → `setup_score.json`)
- **Common model.** Crews are stat-locked at the climb-draft budgets (V0 rungs from `climb_eval.json`; bosses Street 332.58
  with kappa × 0.5 on that race only, Wangan 390.35, Touge 437.06). Race XP is fixed per race: story 29×5 + 32 / 58×5 + 73 /
  60×5 + 77 (the boss win pays cash, no XP); wild encounters and non-mandatory wins pay 13 / 12 / 14. Round ceilings
  3,532 / 4,044 / 4,628. Floors = the mandatory build at each rung. Engine cells: n = 2,000 (non-boss), 6,000 (boss), hard
  track, 3 boss styles, ties half. G2b journeys: 10,000 Monte Carlo players on `journey_grid.json` (engine, n = 1,500 per cell,
  R1 Street only).
- **Mandatory count M per round:** 7 (story only), 10, 13, 20 = 7 story + 0 / 3 / 6 / 13 required wild encounters in the gaps
  before kid2, mat1, mat2, oh1, oh2, boss (0 | 0,1,0,1,0,1 | 1 each | 2,2,2,2,2,3).
  - **Fixed race XP (M7, M10, M13, M20):** fewer mandatory races means a lower floor build.
  - **Retuned (M7r, M13r):** story XP absorbs the dropped wild encounters' XP so the floors equal M20's (R1 story 55×5 + 71
    for M7r, 42×5 + 58 for M13r; R2/R3 scaled the same way: +(13 − M + 7)/… i.e. each story win also pays the XP of the
    wild encounters removed from the gap after it). Same stats as M20, fewer races.
- **Non-mandatory cap c:** none (round ceiling only), 8, 12, 15 XP-paying non-mandatory wins per round.
- **Structure S2 (every crew each round), pruned on one engine pass.** Mapping by tier (7 story races per round):
  R1 = kid1 + kid2 of Street, Wangan, Touge + Street mat1; R2 = Wangan mat1, Touge mat1, mat2 ×3, Street oh1, Wangan oh1;
  R3 = Touge oh1, oh2 ×3, boss ×3. With crews stat-locked at their stats (what "stat-locked" means), 80/80 at the M20 floor:
  R1 Street kid1 97.2, **Wangan kid1 34.5, Touge kid1 0.0, Touge kid2 0.0**, Street mat1 99.9; R2 Touge mat1 0.0, Street mat2
  100, Touge mat2 0.0; R3 Street boss 100, Wangan boss 99.5, Touge boss 55.1. **S2 fails G3a (no climb: Touge kids are
  walls, the Street boss is a free win) and G1a in R1/R2 (no boss).** Making it work needs every crew re-statted per
  round, so a Touge kid is weaker than a Street old head; that is a story change (crew hierarchy), **flag Desmond**. S2 was not
  carried into the grid.

## 3. Scorecard (S1; worst round shown unless 3 values; + pass, − fail)
| Setup | G1a boss 80/80 at floor (40-65) | G1b story losses 80/80 (1.5-4) | G2a min 60/60 at max build (≥30) | G2b weak-improving attempts / stuck (≤60, 0) | G3a climb, drop (≥30) | G3b boss read gap (≥+10) | G4a min 80/80 at floor (≥40) | G4b boss 60/60 at floor (≤10) | G5 cap, boss 80/80 at max (≤95) | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| M7 none | − 2.9 / 0.3 / 0.0 | − 41.7 / 502 / 32,415 | + 32.6 | + 37.5 / 0 | + 37.9 | − −29.7 / −35.6 / −38.6 | − 0.0 | + 0.0 | − no cap (94.8) | 4 |
| M7 8 / 12 / 15 | − same | − same | − 0.0 / 0.1 / 1.1 | + 38.9 / 35.9 / 36.3 | + 37.9 | − ≤ 2.9 | − 0.0 | + 0.0 | + 28.6 / 50.1 / 76.6 | 4 |
| M10 none | − 8.0 / 1.7 / 0.0 | − 16.7 / 116 / 7,504 | + 32.6 | + 37.5 / 0 | + 62.5 | − −24.6 / −34.2 / −38.6 | − 0.0 | + 0.0 | − no cap | 4 |
| M10 8 / 12 / 15 | − same | − same | − 0.0 / 1.1 / 4.1 | + 37.0 / 36.4 / 37.5 | + 62.5 | − | − 0.0 | + 0.0 | + ≤ 94.4 | 4 |
| M13 none | − 18.5 / 5.5 / 0.4 | − 7.4 / 34.1 / 351 | + 32.6 | + 37.5 / 0 | + 79.6 | − −14.2 / −30.4 / −38.2 | − 0.4 | + 0.0 | − no cap | 4 |
| M13 8 / 12 / 15 | − same | − same | − 0.6 / 4.1 / 11.2 | + 36.3 / 37.4 / 37.5 | + 79.6 | − | − 0.4 | + 0.0 | + ≤ 94.8 | 4 |
| **M20 none** | + 53.6 / 56.8 / 54.1 | + 2.17 / 2.29 / 2.29 | + 32.6 (Street boss) | + 38.0 / 0 | + 38.0 | + 21.0 / 20.9 / 15.5 | + 53.6 | + 0.3 / 0.3 / 0.8 | − no cap (94.5 / 89.6 / 94.8) | 8 |
| M20 8 | + | + | − 11.2 | + 38.0 / 0 | + | + | + | + | + 85.9 / 89.6 / 94.8 | 8 |
| M20 12 | + | + | − 26.4 | + 38.0 / 0 | + | + | + | + | + 92.3 / 89.6 / 94.8 | 8 |
| **M20 15** | + 53.6 / 56.8 / 54.1 | + 2.17-2.29 | + 32.6 | + 38.0 / 0 (4.8 NM wins) | + 38.0 | + 15.5-21.0 | + 53.6 | + ≤ 0.8 | + 94.5 / 89.6 / 94.8 | **9** |
| M13r 8 / 12 | + (= M20) | + | − 11.2 / 26.4 | + 33.0 / 0 | + | + | + | + | + | 8 |
| **M13r 15** | + 53.6 / 56.8 / 54.1 | + 2.17-2.29 | + 32.6 | + **33.0** / 0 (6.7 NM wins) | + 38.0 | + 15.5-21.0 | + 53.6 | + ≤ 0.8 | + ≤ 94.8 | **9** |
| M7r 8 / 12 | + (= M20) | + | − 11.2 / 26.4 | + 28.6 / 29.4 | + | + | + | + | + | 8 |
| **M7r 15** | + 53.6 / 56.8 / 54.1 | + 2.17-2.29 | + 32.6 | + **29.4** / 0 (9.1 NM wins) | + 38.0 | + 15.5-21.0 | + 53.6 | + ≤ 0.8 | + ≤ 94.8 | **9** |
| S2 (any M) | − R1/R2 have no boss | − | n/a | n/a | − Touge kids 0.0, Street boss 100 | − | − 0.0 | n/a | n/a | pruned |

- "none" and "15" give the same builds (15 wins ≈ the round ceiling gap 186 / 179 / 204); "none" fails G5 only because no
  explicit cap exists. 12 is too tight for G2a (the 60/60 Street boss tops out at 26.4); 8 is far too tight.
- **Pruned early:** S2 (one pass, above). Fixed-XP M7 / M10 / M13 fail G1a / G1b / G3b / G4a in every cap: without the
  required wild-encounter XP the strong player meets the stat-locked crew under-built (boss 0-18 %), and grinding to fix it
  makes the 60/60 grinder out-race the 80/80 reader (G3b negative).

## 4. Player journeys, R1 Street, top setups (cap 15; Monte Carlo 10,000; journey grid = engine; grid interpolation reads the boss ~2 pts low vs the n = 6,000 cell, 51.8 vs 54.1)
Weak = 50/50 → 80/80 linear over 40 attempts. Run 1 = mandatory only; run 2 = + non-mandatory, grinding until the next story race is ≥ 50 % (cap 15). Per story race: skill on arrival, points (floor), first-try win %, mean attempts, cumulative cash.

**M13r (7 story + 6 required wild encounters):**
| Race | Weak run 1 | Weak run 2 | Strong run 1 (= run 2: never needs to grind) |
|---|---|---|---|
| kid1 | 0.50, 3,000 (3,000), 12.1 %, 5.18 att | 0.58, 3,040, 57.6 %, 1.69 (3.1 NM wins before) | 97.4 %, 1.03 |
| kid2 | 0.56, 3,055 (3,055), 9.4 %, 6.51 | 0.62, 3,121, 55.1 %, 1.76 (2.0) | 90.5 %, 1.10 |
| mat1 | 0.61, 3,110, 17.8 %, 4.58 | 0.64, 3,177, 56.8 %, 1.70 | 84.7 %, 1.18 |
| mat2 | 0.66, 3,165, 21.0 %, 4.05 | 0.67, 3,238, 54.6 %, 1.76 | 78.0 %, 1.27 |
| oh1 | 0.69, 3,220, 26.6 %, 3.35 | 0.69, 3,298, 55.5 %, 1.75 | 70.6 %, 1.42 |
| oh2 | 0.73, 3,275, 30.1 %, 3.02 | 0.71, 3,355, 55.6 %, 1.74 | 63.2 %, 1.57 |
| boss | 0.76, 3,346 (3,346), 31.9 %, 2.91 | 0.74, 3,433, 54.7 %, 1.76 | 51.8 %, 1.91 |
| Round | 37.2 attempts, $23,300; skill walls at kid1-mat2 (first try < 25 %), no floor wall | 33.0 attempts, 6.7 NM wins, $26,971; no wall | 15.5 attempts, $23,300 |

**M7r (story only, story XP 55×5 + 71):** weak run 1: 35.1 attempts, kid2 6.4 % first try (7.84 att), boss 0.74 skill, 23.9 %,
3.65 att, $20,000. Weak run 2: 29.4 attempts, 9.1 NM wins, boss 0.71 skill, 53.7 %, $25,008. Strong: 9.5 attempts, boss 51.8 %,
1.94 att, $20,000.

**M20 (current, `journey.py`, 20,000 players):** weak run 1 40.9 attempts (kid1 12.1 %, kid2 12.8 %, boss 44.7 % at skill 0.785),
$27,150; weak run 2 38.0 attempts, 4.8 NM wins, boss 60.5 %, $29,808.

- Floors never wall a player who plays in story order; they only block skipping ahead (or skipping required wild encounters).
- Free retries are themselves practice: the improving weak player clears even mandatory-only, at the cost of skill walls early.

## 5. Recommendation and the main tradeoff
- **Recommended: S1, M13r, non-mandatory cap 15 XP-paying wins per round** (7 story + 6 required wild encounters, one before
  each rung after kid1; story XP raised so the floors match the climb). Passes 9/9: strong mandatory-only boss 53.6 / 56.8 /
  54.1 %, 2.2-2.3 story losses per round, climb 97 → 54, read gap +15.5 to +21.0, 60/60 boss 32.6 at the cap and ≤ 0.8 at
  the floor, 80/80 at the cap ≤ 94.8; weak-improving R1 in 33.0 attempts (6.7 non-mandatory wins), 0 stuck.
- **Tradeoff: race count vs practice.** M7r, M13r and M20 have identical stats (same floors), so the choice is length. M7r is the
  shortest (strong 9.5 attempts per round, weak 29.4) but the weak player reaches the boss at skill 0.71 instead of 0.74
  (M13r) / 0.77 (M20) and leans on 9.1 grind wins; M20 gives the most district practice but strong players face 20 races, 13
  of them near-certain wild encounters (99-100 %). M13r keeps one wild encounter per rung as line practice at about two thirds
  of M20's length.
- **Cap 15** is the smallest tested cap that passes G2a (12 gives 26.4 at the Street boss); it equals the ceiling gap, so it
  also stops XP farming past full build.

## 6. Stat-lock floors, grind cost, live-sim check (from `climb_floor.py` → `climb_floor.json`, engine n = 6,000)
- **Floors (earned car points; M20 / M13r / M7r, all equal):** Street 3,000 / 3,055 / 3,110 / 3,165 / 3,220 / 3,275 / 3,346;
  Wangan 3,346 / 3,428 / 3,510 / 3,592 / 3,674 / 3,756 / 3,865; Touge 3,865 / 3,953 / 4,041 / 4,129 / 4,217 / 4,305 / 4,424
  (kid1 … boss). In mod_skill, race XP goes straight into equipped mods up to the bought tier's ceiling, re-assignable for free,
  so there are no "unassigned" points; XP that doesn't fit is lost. **The floor should check an earned-XP ledger (all race XP,
  including lost overflow)** so an unbought tier never walls the player.
- **Brutal grind cost, 60/60 to reach 30 % (non-mandatory wins on top of the mandatory path, cash at $550 / $632.50 / $742.50):**
  Street mat1 4 ($2,200), mat2 6 ($3,300), oh1 8 ($4,400), oh2 10 ($5,500), boss 14 ($7,700); Wangan 2 ($1,265), 7 ($4,427.50),
  10 ($6,325), 12 ($7,590), 14 ($8,855); Touge 2 ($1,485), 4 ($2,970), 7 ($5,197.50), 10 ($7,425), 12 ($8,910).
- **Live sim: crews are already stat-locked.** `sim/velocity_shift/equations.py:923` `opponent_budget(rnd, rung)` =
  `C_ROUND[rnd] / LADDER_TARGET_R[district][rung]`, a constant per round and rung; `progression.py:435` reads that B and
  `progression.py:454` sets r = player power / B. Nothing scales with the player. There is **no floor or challenge gate**: walks
  grind by policy (`grind_until`, `progression.py:428`). **Godot does not model progression:** `scripts/race_core.gd:34-38`
  `stats_from_config` makes the opponent a fixed `opp_total / 3` per stat and derives the PLAYER as `opp_total × LADDER_R[rung]`
  (`scripts/sim_constants.gd:58`, stale values 1.13 … 1.05).
- **Gordon would need:** player stats from save data (base + earned mod points); per-character fixed opponent stats and shape;
  an earned-XP ledger and a floor check before a challenge; a per-race kappa multiplier (Street boss × 0.5); a per-round
  non-mandatory XP counter (cap 15).

## 7. Flags for Desmond
- S2 (every crew every round) only works if crews are re-statted per round (a Touge kid weaker than a Street old head).
- Floors need an in-world reason ("the crew won't race a car below X") and a UI readout.
- Raising story XP (M13r / M7r) changes nothing in story, but the six required wild encounters become story beats.
- The Street boss's kappa × 0.5 has no story hook yet.
