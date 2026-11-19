# mod_skill boss gate ("gym gate"): mandatory wild encounters, Barry DRAFT, 2026-11-19

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
