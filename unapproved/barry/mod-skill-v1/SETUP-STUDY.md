# mod_skill SETUP STUDY: structures × mandatory count × non-mandatory cap, judged against Austin's goals (Barry DRAFT, 2026-11-19)

> **Scope (Austin, direct, 2026-11-19 4:21 PM PT):** compare setups against his written goals G1-G5 instead of a single
> climb recommendation. **Unapproved and nothing live. Nothing in `sim/` changed.** Fixed: 7 story races per crew (2 kid,
> 2 mature, 2 old head, 1 boss), crews stat-locked with FLOORS (earned points count, assigned or not), no underdog bonus,
> 0.80 random AI QTE, AI heat rules, fixed mod layout.

## 0. REVISION 2026-11-19 (later): strong story player at 65-70 % on the boss (Barry DRAFT, unapproved)
> **Austin (direct, 2026-11-19, after reading this study):** "Think we can get a strong story player to 65-70%?"
> **G1a revised: 80/80 boss win at the floor (mandatory build) 65-70 % every round** (was 40-65). Every other threshold in
> section 1 is unchanged. Code: `boss_lever.py` → `boss_lever.json` (levers), `boss65_probe.py` → `boss65_probe.json`,
> `climb65.py` → `climb65.json` (scorecard), `journey_shop.py` → `journey_shop.json` (journeys with mod purchases).
> Nothing live; `sim/` untouched.

### 0.1 Levers tried (engine n = 6,000, target 66 % so the boss stays ≤ oh2 + 1 for G3a)
| Lever | Values (Street / Wangan / Touge) | 80/80 at floor | 80/80 at max (G5 ≤ 95) | 60/60 at max | Verdict |
|---|---|---|---|---|---|
| **(b) raise the boss floor** (story XP in the oh2 → boss gap) | floor 3,346 → **3,392 (+46)**, 3,865 → **3,904 (+39)**, 4,424 → **4,467 (+43)**; boss budgets unchanged | 66.9 / 66.1 / 67.7 | **94.5 / 89.6 / 94.8** (unchanged) | 32.6 / 35.9 / 38.6 (unchanged) | **chosen: cheapest, breaks nothing** |
| (a) lower the boss budget at the old floor | 332.58 → 328.07, 390.35 → 386.46, 437.06 → 432.96 | ≈ 66 (same floor r) | **95.98** / 93.85 / **98.08** | 40.2 / 50.2 / 56.4 | fails G5; 60/60 too easy |
| (c) soften the boss AI QTE | mean 0.80 → 0.685 / 0.65 / 0.68 | 69.7 / 66.4 / 66.7 | **96.7** / 92.3 / **96.9** | 49.0 / 48.1 / 53.7 | fails G5; 60/60 too easy; per-character AI skill (Desmond) |

- (a) and (c) lift the full build as much as the floor; (b) only closes the floor-to-max gap, so G5 and G2a don't move.
- **(b) in numbers (M13r, one wild encounter per gap):** pre-boss story XP R1 42×5 + **104** (oh2 was 58), R2 70×5 + **90**
  (was 85), R3 74×5 + **109** (was 91); the boss sits at 73.7 % / 72.7 % / 72.4 % of the round's mod XP (was 65 %).
  Full build from the boss floor needs 11 / 12 / 12 non-mandatory wins (was 15 / 15 / 15); cap 15 unchanged.
- **Knock-on:** the higher R1/R2 boss floor raises the next round's entry (+46 into R2, +39 into R3). To hold kid1-oh2, the
  R2/R3 rung budgets are rescaled to keep each rung's r: R2 318.65 / 340.56 / 348.93 / 362.05 / 373.74 / 384.44, R3 354.33 /
  383.85 / 393.80 / 404.82 / 416.82 / 426.72 (kid1 … oh2; the R2 kid1 and R3 kid1/oh2 values include the G3a repair below).
- **G3a repair (the boss drop broke it):** at boss ≈ 66-68 the kid1 → boss drop was 29.1 (Wangan) and 25.3 (Touge), and the
  Touge boss (67.9; the engine curve steps from 64.9 to 67.8 between r 1.0219 and 1.0220) sat above oh2 + 1 (66.8 + 1).
  Fixes: Wangan kid1 r 1.046 → 1.0645 (80/80 95.0 → 97.1), Touge kid1 r 1.0636 → 1.1018 (93.3 → 98.7), Touge oh2 r 1.0125 →
  1.018 (66.8 → 70.7). Story/art impact: none (stats only).

### 0.2 Scorecard, S1 M13r cap 15 + lever (b) (engine: n = 2,000 non-boss, 6,000 boss; `climb65.json`)
| Criterion | Threshold | Street / Wangan / Touge | Pass |
|---|---|---|---|
| G1a (revised) strong boss at floor | 65-70 | **66.87 / 66.05 / 67.65** | + |
| G1b strong story losses per round | 1.5-4.0 | 1.80 / 2.02 / 1.79 | + |
| G2a min 60/60 at max build | ≥ 30 | 32.63 (Street boss) | + |
| G2b weak improving, R1 | ≤ 60 att, 0 stuck | 32.3 attempts, 6.1 NM wins, 0 stuck | + |
| G3a climb monotone, drop | drop ≥ 30 | yes; 31.18 / 31.0 / 31.0 | + |
| G3b boss read gap (80/80 floor − 60/60 max) | ≥ +10 | +34.2 / +30.2 / +29.1 | + |
| G4a min 80/80 at floor | ≥ 40 | 65.9 (Wangan oh2) | + |
| G4b 60/60 boss at floor | ≤ 10 | 2.28 / 1.53 / 2.93 | + |
| G5 cap set, 80/80 boss at max | ≤ 95 | 94.5 / 89.6 / 94.77 | + |

**9/9.** Boss per round: strong at floor 66.9 / 66.1 / 67.7, strong at max 94.5 / 89.6 / 94.8, 60/60 at floor 2.3 / 1.5 / 2.9,
60/60 at max 32.6 / 35.9 / 38.6. Climb (80/80 at floor, kid1 … boss): Street 98.1 / 91.8 / 87.2 / 81.7 / 75.9 / 66.2 / 66.9;
Wangan 97.1 / 89.9 / 85.6 / 78.9 / 70.8 / 65.9 / 66.1; Touge 98.7 / 90.7 / 85.6 / 80.0 / 73.2 / 70.7 / 67.7.
- **Nothing broke** against the thresholds. 60/60 doesn't get easier (floor ≤ 2.9, max unchanged at 32.6-38.6).
- **Watch:** in Street and Wangan the boss (66.9 / 66.1) now equals oh2 (66.2 / 65.9) for a strong player at the floor: G3a passes
  on its +1 tolerance, but the top of the climb is flat. If Austin wants the boss to feel harder than oh2, lower oh2 to ~70-72
  (budget only); not run.
- G5 and the cap need no change: the max build is untouched by (b).

### 0.3 Mod tiers in the journeys (answer)
- **The earlier journeys (`journey.py`, `journey_setups.py`) assumed the needed tier was owned:** no purchase, no cash deducted,
  no debt. (The engine scorecards are stat-only and don't need it; the campaign walk `walk.py` does buy, but one tier per round
  at round open at Mk1 list $150 / $700 / $1,200, not the mods-v1 Mk2/Mk3 unlocks.)
- **Fixed in `journey_shop.py`:** R1 starts at $0 with the $16,000 debt, 65 % of each purse to the debt; mods-v1 R1 prices and
  unlocks: Mk1 $150 at round open, Mk2 $500 after the mat1 win, Mk3 $1,000 after the mat2 win, 4 slots; earned-point ceiling
  per slot Mk1 115 / Mk2 124 / Mk3 133 (scaled from mods-v1 points above stock 63 / 68 / 73 to mod_skill's 133; Barry
  mapping, draft). XP with no room is lost from the car but counts toward the floor ledger. Myth tiers are arc-only (not R1).
- **Result:** every player owns 4 × Mk3 by the boss (100 % of runs), spends $6,600, and loses 0 XP; the ceilings never bind
  before the boss, so the R1 journeys are unchanged within noise (old M13r: strong 15.6 attempts, weak 37.2, weak + NM 33.0).

### 0.4 Round 1 journey, M13r + lever (b), with purchases (10,000 players; journey grid = engine, reads ~1.5 pts low at the boss)
| Race | Strong (80/80), mandatory only | Weak (50 → 80), mandatory only | Weak + non-mandatory (cap 15) |
|---|---|---|---|
| kid1 | 97.4 %, 1.0 att | skill 0.50, 12.1 %, 5.0 att | 0.58, 3,040 pts, 57.6 %, 1.7 att (3.1 NM wins) |
| kid2 | 90.5 %, 1.1 | 0.56, 9.2 %, 6.6 | 0.62, 3,121, 55.1 %, 1.8 (2.0) |
| mat1 | 84.7 %, 1.2 | 0.61, 17.8 %, 4.6 | 0.64, 3,177, 56.8 %, 1.7 |
| mat2 | 78.0 %, 1.3 | 0.66, 21.1 %, 4.1 | 0.67, 3,238, 54.6 %, 1.8 |
| oh1 | 70.6 %, 1.4 | 0.69, 26.8 %, 3.4 | 0.69, 3,298, 55.5 %, 1.8 |
| oh2 | 63.2 %, 1.6 | 0.73, 30.4 %, 3.0 | 0.71, 3,355, 55.6 %, 1.7 |
| boss | 3,392 pts, **65.3 %**, 1.5 | 0.76, 3,392, 47.3 %, 2.1 | 0.73, 3,472, **67.3 %**, 1.5 |
| Round | 15.2 attempts; cash $1,555, debt $855 left | 36.4 attempts; same cash/debt | 32.3 attempts, 6.1 NM wins; $4,079, debt cleared |

All runs: $6,600 on mods (4 × Mk1-Mk3), 0 XP lost, 0 stuck. Floors never wall a player in story order.

---

## 1. Criteria (written and fixed at 16:23 PT, BEFORE any setup run; not tuned afterwards)
Players: **strong** = 80/80 (read = timing = pacing 0.80) throughout. **Weak (fixed)** = 60/60. **Weak improving** = skill
q(a) = min(0.80, 0.50 + 0.30·a/40), a = race attempts made so far in the round (wins and losses), i.e. linear from 50/50 to
80/80 over 40 attempts. Losses are free retries. "Mandatory build" = car points on arrival with mandatory wins only (= the floor).
"Max build" = mandatory build + the non-mandatory cap's XP (capped by the round's mod ceiling; prior rounds' max carried).

| ID | Goal | Measure | Pass threshold | Why this number |
|---|---|---|---|---|
| G1a | Strong player challenged, mandatory only | 80/80 boss win % at the mandatory build, worst and best round | **40-65 %** every round (REVISED 2026-11-19 by Austin to **65-70 %**, see section 0) | A coin-flip-ish boss (~1-2.5 attempts) is a challenge; > 65 is routine, < 40 is a wall for the target player |
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
  - **Retuned (M7r, M13r):** each story win also pays the XP of the wild encounters removed from the gap after it, so the
    floors equal M20's. Story XP kid1 … oh2: M7r 55×5 + 71 / 82×5 + 109 / 88×5 + 119; M13r 42×5 + 58 / 70×5 + 85 / 74×5 + 91
    (R1 / R2 / R3). Same stats as M20, fewer races.
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

## 5. ~~Recommendation and the main tradeoff~~ (STALE 2026-11-19: G1a revised to 65-70 % by Austin; superseded by section 0, which keeps S1 M13r cap 15 and adds lever (b))
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
