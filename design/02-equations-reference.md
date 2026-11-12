# Midnight Apex — Equations Reference

Every formula in the combat engine. All are pure functions in `sim/velocity_shift/equations.py`. All game-rule constants are module-level names — tunable in one place, never per-encounter.

---

## Decision sheet (2026-11-04, for Austin to lock)

> Author: Barry (Chief of Systems). Status: **decision list**, not applied. Prefixed here so you can lock math before more Godot work. Nothing committed. Raw runs: `/workspace/parity/decision-sheet/`. Economy sims still wait on your criteria.

### Top decisions (in order)

1. **How hard should parity feel?** Today 0.9/0.9 wins **100%** vs Lt/Boss. Your yardstick is ~**60%** in Round 2+ on raw stats. Only **AI skill** moves that (not clash stakes / battle bonus / rubber band).
2. **Lock the AI-skill lever** that hits ~60% at 0.9/0.9: recommend **AI read 0.40 + AI QTE 10**. Needs a real engine hook + matching tells (Desmond).
3. **Fix encounter scaling** (doc vs code mismatch; double-count today). Tiers should set **AI skill** (and maybe a small r), not double-scale level × QTE.
4. **HP_PER_LEVEL**: code **180**, stale §1 says **120**. Recommend keep **180** and fix the doc.
5. ~~Third-stance naming~~ **Resolved 2026-11-12: POW / EN / HAN everywhere** (Austin; canon block in 01, map in §6.0).
6. **Straight window**: 8s (06) vs 12s (Godot guide). Pick one for Godot.
7. **Economy numbers** (debt race, DEBT_SHARE, wholesale, respec, betting stakes/odds/shell rate): list only; **no season runs** until you give success criteria.
8. Accept or mark up the **§0 target curves** (q_read / q_time form, equal weights, coefficients).
9. **Wild ramp (proposed 2026-11-04, Integration room):** in each district, Wild races get harder and longer as the PC beats that district's lieutenants. Early Wild races stay short pushovers for EXP; later ones approach lieutenant AI skill and race length, so the climb to lieutenants isn't a cliff. Wild and lieutenant races differ by AI skill (read, QTE timing, tell lie rate, deck lean), not stats; both stay near stat parity. Story reason: reputation (each lieutenant beaten spreads the PC's name and draws better locals). Open: should lieutenants also read the PC's past stance habits against them (makes post-loss retries harder, which conflicts with the same-difficulty-retry rule), or only after wins? Lie rates go through Desmond and Nathaniel. Next step after sign-off: sim AI skill × race length along the ramp so each step is a small, real jump.

### Yardstick (your meta) vs today's sim

| Your feel | Today's parity sim | What moves it |
|---|---|---|
| Every race scales with player level | Opponent level = `round(player × ENCOUNTER_RATIOS)`; leveling barely changes relative power | Pending scaling fix: season opponents from a table, not player×ratio |
| Skill/leveling capped at **0.8×** top unlocked boss | Not in sim yet | Skill-point / season systems (07) |
| Wild = pushovers (EXP farm) | **game_wild** unlosable (q50 0, 99.9% at q=0); **parity_wild** still easy (0.9/0.9 = 100%) | Keep wild AI skill low; do **not** give wild the same AI read/QTE as bosses |
| Betting > wild, slightly < lieutenant | No betting in sim | 07 §7.5 + canon 26 |
| Lt/Boss at r 0.8–1.2, **0.9/0.9 → ~60%** raw in R2+ | **0.9/0.9 → 100%** (Lt & Boss) | AI read + AI QTE (below) |
| Races 1–3 are scripted raw-stat tutorials that a new player can win; mods unlock when the PC wins race 3, and the rest of R1 is still a challenge (proposal: at 0.8 cap, ~0.8 play ≈ 50% vs Lt, ~0.9 vs R1 boss) | No R1/cap sim yet | After AI lever + skill-point format |

**Spot-check just run** (L50, parity, N=1000/cell → `/workspace/parity/decision-sheet/spot_check.txt`):

| Config | Lt 0.9/0.9 | Boss 0.9/0.9 | Lt 0.25/0.25 | Boss 0.25/0.25 | Lt 1.0/0.6 |
|---|---|---|---|---|---|
| Current (AI QTE 7, no AI read) | **100%** | **100%** | 54.7% | 48.3% | 100% |
| **AI read 0.40 + QTE 10** | **53.3%** | **49.7%** | 0.0% | 0.1% | 24.7% |

Grid2d (existing, `/workspace/parity/grid2d.txt`, N=4000): current 0.9/0.9 = 100% Lt & Boss; 0.25/0.25 = 56.9% Lt / 45.2% Boss. Matches the "far too easy" read.

Validate re-run today (`decision-sheet/val_r40q10.txt`, seeds 40): AI read 0.40 + QTE 10 → q50 **0.874–0.916** across Wild/Lt/Boss × L10–80; at q=0.9 win% ≈ **48–59%**. Closest cheap hit to your ~60%.

**Levers that barely move q50** (08 §5, parity_lieutenant L50): CLASH_STAKES 0.20/0.60 → 0.264/0.195; BATTLE_BONUS 0.20 → 0.224; RUBBER_BAND 0.05/0.50 → 0.231/0.228. **Do not use these to fix difficulty.**

---

### Core equations / rules

#### 1. Clash resolution (RPS + stakes)

| | |
|---|---|
| **Current sim** | `resolve_stance`: POW > HAN > EN > POW; same → DRAW (`equations.py`, `resolve_stance`). `clash_mult = 1 + CLASH_STAKES × outcome`, **CLASH_STAKES = 0.35** (`equations.py:16`, `:54-61`). Battle margin: `battle_mult = 1 + BATTLE_BONUS × \|sum\|`, **BATTLE_BONUS = 0.05** (`equations.py:17`; applied in `combat.py`). |
| **Recommend** | Keep RPS and **0.35 / 0.05**. They don't set difficulty (08 §5). Difficulty goes through AI skill. |
| **Alts** | Raise stakes (0.45–0.60) for spicier swings (q50 moves ~0.03). Cut stakes for flatter races. |
| **Evidence** | 08 §5: stakes/bonus barely move q50. |
| **Decision needed:** | Keep clash math as-is and push difficulty into AI skill? Y/N |

#### 2. Damage / HP (incl. HP per level)

| | |
|---|---|
| **Current sim** | `DP = POW × qte_factor × clash_mult × battle_mult` (`equations.py:64-74`). Mitigation: `max(MITIGATION_FLOOR, 1 − (EN/1000)×MITIGATION_PER_1000×qte_factor)` with **MITIGATION_PER_1000=0.4**, **FLOOR=0.1** (`equations.py:18-19`, `:77-84`). **HP_PER_LEVEL = 180** (`equations.py:20`). Stale §1 still says 120. |
| **Recommend** | Keep **180**; fix §1 to match. Keep damage/mitigation chain. |
| **Alts** | HP 120 (old doc) shortens races; 200+ lengthens. Touching mitigation changes EN's value a lot. |
| **Evidence** | Code/Godot use 180 (`04:58` text already says 180). No HP-sweep this turn. |
| **Decision needed:** | Lock HP_PER_LEVEL = **180**? Y/N |

#### 3. Energy (EN / Endurance)

| | |
|---|---|
| **Current sim** | EN only mitigates incoming DP (formula above) and weights EN cards in the deck. UI label **EN**. No separate "energy resource" / mana. |
| **Recommend** | Keep EN as mitigation + EN card weight. No new resource meter in v1. |
| **Alts** | A spent resource (per-turn energy) would be a new system — out of scope for this lock. |
| **Evidence** | `01-system-overview.md:83`; no energy pool in `sim/`. |
| **Decision needed:** | Confirm EN stays mitigation-only (no AP/mana) for v1? Y/N |

#### 4. Deck size / composition

| | |
|---|---|
| **Current sim** | **DECK_SIZE = 192** (`deck.py:19`). Draw 6/turn. Weights: α=0.85 blend of POW/EN/HAN stat shares → POW/EN/HAN cards (`deck.py:29-44`; `03:7-24`). Player: no reshuffle (discard grows). Opponent: reshuffle every turn. Boss max 30 turns → at most 180 cards used → **player deck never empties**. |
| **Recommend** | Keep 192 / draw 6. Note the "never empties" property is intentional for bosses. |
| **Alts** | Smaller deck (e.g. 96) would force late-race thinning; needs a design reason. |
| **Evidence** | 08 §7 known limitation; 03 §deck management. |
| **Decision needed:** | Keep 192 / no player reshuffle? Y/N |

#### 5. Straight window (pick timer)

| | |
|---|---|
| **Current** | **Conflict.** `06-pattern-read.md:204` = **8 seconds**. `godot-build-guide.md:64,271` = **STRAIGHT_DURATION 12.0** (tunable 8–12 at `:956`). Sim has no real-time timer. |
| **Recommend** | Lock **10s** as a middle ground for first Godot pass, or pick 8 if you want sharper reads. |
| **Alts** | 8 (doc 06) / 12 (guide default). |
| **Evidence** | Docs only; no playtest timing data. |
| **Decision needed:** | Straight window = 8 / 10 / 12 s? |

#### 6. Gauntlet PASS rule

| | |
|---|---|
| **Current** | `balance_gauntlet.py`: (a) algebraic predict vs measured winner must match (ties auto-pass); (b) **archetype balance = each arch has ≥1 win and ≥1 loss** across the matrix (`:401-407`). Header warns: read win/loss counts, not just PASS (`:7-8`). Rubber band in gauntlet uses a **hard-coded 0.15** (`:96`, `:146`), not `RUBBER_BAND_FRACTION`. |
| **Recommend** | Keep the soft archetype rule for now, but treat it as a **smoke test**, not balance proof. Import `RUBBER_BAND_FRACTION` instead of 0.15. |
| **Alts** | Stricter band (e.g. win rate 30–70% per arch); or drop archetype PASS entirely until matchups are reworked (08 §6.3). |
| **Evidence** | Parity pair spread q50 **0.01–0.48** (08 §3.1) — Aggressive is over-tuned; gauntlet PASS can still light green. |
| **Decision needed:** | Keep "≥1 win and ≥1 loss" as the only archetype gate, or raise the bar? |

#### 7. Stance naming

| | |
|---|---|
| **History** | The third stance had two names (one in code, one on UI buttons); resolved 2026-11-11 to one name, then superseded. |
| **Resolved (2026-11-12, Austin):** | Stances and stats are **POW / EN / HAN** everywhere, code included (`Stance.POW` / `Stance.EN` / `Stance.HAN`). Old → new map in §6.0. |

#### 8. Encounter ratios + opponent QTE

| | |
|---|---|
| **Current code** | `ENCOUNTER_RATIOS`: wild **0.75**, lieutenant **1.1**, boss **1.2** (`ai.py:17-21`). Opp level = `round(player × ratio)` (`cli.py:305`). Opp QTE = `TYPICAL_QTE(7.0) × same ratio` (`ai.py:36`, `:301-305`) → **double-counted**. |
| **Current docs** | `04:58-62`: **0.35 / 0.75 / 1.15**. Opp QTE doc: `4.0 + level × 0.025` (`04:148`). |
| **Recommend** | **One job each:** tier → AI skill (read rate + QTE skill); stats/r from a season table (or small level gap). Retire double-scale. Sync 04 to code after the fix. Proposed AI skill from §0 / 08: Boss ≈ read 0.40 + QTE 10; Lt a step down; Wild much lower so it stays a farm. |
| **Alts** | Keep code ratios but stop multiplying QTE; or adopt doc 0.35/0.75/1.15 as level-only. |
| **Evidence** | 08 §3.2: game_wild unlosable; game_boss q50 ≈ 0.81–0.83 from the double scale. 02 §0.1. |
| **Decision needed:** | Approve "tiers = AI skill (+ small r), no double-scale"? Y/N |

#### 9. RUBBER_BAND_FRACTION

| | |
|---|---|
| **Current** | **0.15** in `equations.py:23`; used in `match.py:65`. Gauntlet duplicates **0.15** (`balance_gauntlet.py:96,146`). |
| **Recommend** | Keep **0.15**. Point gauntlet at the constant. |
| **Alts** | 0.10 / 0.25 (guide tunable range). |
| **Evidence** | 08 §5: 0.05→0.50 changes q50 by ~0.003. Cosmetic for parity feel. |
| **Decision needed:** | Keep 0.15? Y/N |

#### 10. Play quality model (q_read / q_time) + §0 targets

| | |
|---|---|
| **Current sim** | Opt-in `player_read` / `player_timing` (or `player_quality` for both). q_read = P(counter AI pick); q_time = P(perfect-10 QTE) (`equations.py:25-38`; `simulation.py`). |
| **§0 proposed targets** | `s = (q_read+q_time)/2`; logistic with equal weights; Boss s0 **0.86**, a **16** → 0.9/0.9 ≈ **65%**, perfect ≈ **90%** at parity. |
| **Recommend** | Keep the two-axis model. Use **AI read 0.40 + QTE 10** as the first candidate to chase §0 (spot-check ≈ 50–53% at 0.9/0.9 — a bit under 65%; fine-tune read 0.35–0.38 or soften QTE after). Equal style weights stay the goal (today timing is worth ~1.16–1.20× reading on the current easy curve). |
| **Alts** | Single-q only; specialist-bonus interaction (§0 Q2); different s0 (0.9 → 50% instead of 65%). |
| **Evidence** | grid2d + spot_check + val_r40q10; §0.3–0.6. |
| **Decision needed:** | (a) Keep two-axis q_read/q_time? (b) Boss at 0.9/0.9 → ~60–65% OK? (c) Approve AI read 0.40 + QTE 10 as first candidate? |

#### 11. Other unlocked / TBD

| Item | Status | Recommend |
|---|---|---|
| Tell / lie rates (06) | Cap what q_read is worth in-game | Set with Desmond alongside AI read |
| Archetype matchup spread | q50 0.01–0.48 at parity | Separate pass after AI lever |
| Skill-point value / 0.8× boss cap | **In sim (2026-11-09):** `SP_CAP_FRACTION`, level curve and level cap in `equations.py`; model in `progression.py` | See "Story ladder + XP progression" below |
| Wild ramp (top decision 9) | Proposed, awaiting sign-off | Sim AI skill × race length per ramp step |
| Constants location (C10) | Ratios/turns live in ai.py/cli.py | Move into `equations.py` with the scaling fix |

---

### Story ladder + XP progression (locked by Austin 2026-11-09; numbers are stand-ins pending playtest)

All values live in `sim/velocity_shift/equations.py` (section "Story race-balance + XP/level progression model"); the model is `sim/velocity_shift/progression.py`; run `python scripts/run_progression.py` from `sim/` (checked by `sim/tests/test_progression.py`).

| Item | Constant(s) | Rule |
|---|---|---|
| Race-balance combat settings (final-v1 + qte-v1) | `QTE_ZONE_BASE_MS`, `QTE_ZONE_WIDTH_105`, `QTE_SKILL_SIGMA_OVER_A0`, `QTE_SKILL_TARGET_E`, `QTE_PHASES`, `PHASE_QTE_UNPLAYED`, `QTE_SCORE_DECIMALS`, `KAPPA_BY_LENGTH`, `LINE_SET_C`, `LINE_ADHERENCE`, `LINE_ALT_WEIGHTS`, `OPPONENT_QTE` | Visible QTE zone width by stat ratio r (`qte_zone_width`, plus `MatchConfig.qte_window_mod`), PLACEHOLDER skill σ (`expected_hit_quality`, `raw_qte_score`), stat-gap leverage by race length, district line set C (2026-11-10: Street N90 and Wangan IR/SW mains revised, lines-v1), uniform opponent QTE, and the Phi/tau clash payoff (`W0`, `T_MAX`, `L_MAX`, `TAU_BETA`, `TAU_P_TOP`, `MU`, `ETA`, `DECK_ALPHA`, `HAND_SIZE`). The playable engine in `combat.py` / `match.py` uses this model: one categorical line pick per corner, v4 read + `assign_hand` when `q_read` is set, progress `g = V · Φ(outcome, q_eff) · M` with `V = r**kappa`; `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)` with no `knot_window` factor; HAN scales both sides. The player's raw score comes from the visible zone at the race's fixed r (it does not change with mid-race position). A turn may also take three phase scores (Entry, Apex, Exit) via `mean_phase_qte` / `phase_raw_qte` (`TurnState.player_qte_phases` or a 3-tuple from `get_player_qte`); the turn's `raw_qte` is their mean, and an unplayed phase is `PHASE_QTE_UNPLAYED`. 2026-11-12 (Austin approved via Desmond): every QTE phase score is rounded to `QTE_SCORE_DECIMALS` by `round_qte_score` where it is computed (`raw_qte_score`, `phase_raw_qte`), before `mean_phase_qte`, `q_eff`, clash or progress math, so 1-ULP libm differences between platforms cannot change gameplay (rule below). The `q_eff` formula is unchanged. `KNOT_WINDOW_105` / `knot_window` are legacy (winrate_n4000.json / progression oracle, and the generator of the zone table). 2026-11-11 (slots-v2, Austin approved): the r = 1.00 knot is 0.67 (was 0.68), so `qte_zone_width` is 0.5698 at r 1.00 (was 0.5802) and 0.7170 at r 1.02 (was 0.7243); r ≥ 1.05 and r ≤ 0.95 are unchanged. `winrate_n4000.json` was rebuilt with it; official progression stays 153 grind / 162 levels in all 216 orders. The older HP/DP path is `resolve_turn_legacy` (`MatchConfig.legacy_hp_dp`). |
| Caps and mods | `SP_CAP_FRACTION`, `MOD_CAP_FRACTION`, `MOD_SHARE_OF_REF`, `REFERENCE_RULE`, `MOD_TIMING`, `AERO_FREE_POOL_MAX_FRACTION`, `AERO_MAX_EQUIPPED`, `AERO_COUNTS_IN_MOD_CAP` | SP cap 80 % of reference (= level cap); SP + mods to 105 %; mods bought only, unlocked progressively (timing c). Aero (Austin approved 2026-11-11, slots-v2): any slot, at most one equipped, its full stat total counts inside the 105 % cap, and its free wind-tunnel pool is at most 10 % of the part's total (`aero_free_pool_max`; per-tier `AERO_FREE_POINTS` still TBD). |
| Mod tier level floor | `MOD_TIER_LEVEL_FLOOR`, `MOD_TIER_FLOOR_RUNG`, `MOD_TIER_FLOOR_MARGIN` | Austin approved 2026-11-12 (slots-v2 fix b3). Each crew's mature #2 mod tier can't be fitted below a per-(round, play position) level. The floor is the crew-local level after story XP alone + the margin, generated by `progression.derive_mod_tier_floors` and checked with `mod_tier_available`. Below the floor, the skip state keeps the previous rung's mods. See design/07 §6.4. |
| Ladder | `LADDER_RUNGS`, `LADDER_R`, `SCRIPTED_BUDGETS`, `SABINE_BUDGET` | Target r per rung at its level cap. |
| Budgets | `OPTION_A_CREW_STEP`, `OPTION_A_ROUND_STEP`, `DISTRICTS`, `DEFAULT_CREW_ORDER`, `FINALE` | Step by play position (free crew order); the first crew challenged in R2/R3 gets the round step. `DEFAULT_CREW_ORDER` is an example order for reports/tests. |
| Unlock points | `DEBT_CLEAR_AFTER`, `BETTING_UNLOCK_AFTER`, `FINALE_UNLOCK_AFTER` | (round, crews beaten in that round): debt/aero after the first R2 crew, betting after R2, finale after R3. |
| Level curve | `SP_START`, `SP_GROWTH_PER_12_LEVELS`, `XP_BASE`, `XP_SP_EXPONENT` | `sp_per_level(L)`, `xp_to_next(L)`: SP per level grows, XP per level grows faster. |
| Cap raises | `CAP_ALLOC_CREW`, `CAP_ALLOC_ROUND_OPEN` | Front-loaded levels per win. |
| Story XP | `STORY_XP_LT`, `STORY_XP_LT_ROUND_OPEN`, `STORY_XP_LT_FLOOR`, `STORY_XP_BOSS` | Every win pays visible XP; boss pays the levels it unlocks, immediately. |
| Grind taper | `TAPER_F0`, `TAPER_RUNG`, `TAPER_LEVEL_TAU`, `TAPER_FINALE_RUNG` | `grind_payout_fraction(L, j)`: per-crew taper T2. |
| Finale | `FINALE_MOD_SHARE`, `FINALE_GRIND_SHARE` | Caps lifted; finale stat rise mostly mods. |
| Build bounds | `BUILD_STAT_MIN_SHARE`, `BUILD_STAT_MAX_SHARE` | Each stat 25–50 % of total. |

Open items: see 07 §8.

### Economy (from 07 — numbers only; **no season runs**)

Evidence for all rows: **no run (awaiting criteria)**.

| Item | Current proposal | Alternatives | Decision needed |
|---|---|---|---|
| **DEBT_AMOUNT** | Solved by season sim so median clear = target R2 race | Hand-picked flat number | After Q1 + criteria |
| **DEBT_SHARE** | **B Allowance** `< 1.0` from Prologue (A Strict ruled out) | C boss-money-free; D Reiko cuts remaining debt; Desmond trickle-from-bonuses | Pick B vs C/D layer? |
| **Which R2 race clears debt (Q1)** | **Hard target** (aero unlocks at debt = 0). Still open which race | Mid-R2 Wangan crew / Wangan boss / debt=0 floating | Name the race |
| **WHOLESALE_DISCOUNT** | TBD fraction off after end of R1 | — | Pick a fraction (e.g. 0.15–0.25)? |
| **RESPEC_POINTS_PER_VISIT** + **RESPEC_COST_PER_POINT** (Q18) | Cap points moved per Jesse/tunnel visit; cost per point; same values for skill + aero? | Separate aero vs skill prices | Set both numbers |
| **Betting unlock** | **Locked:** end of Round 2 (canon 21/26) | — | No decision (done) |
| **Betting stakes / odds / prompt / shell win rate** | Canon 26 locked *rules*: shells & liveries cosmetic; crew bosses' signature shells come from crew boss betting races at promoter's subsea Wangan home base (standout substories add a small oddball shell pool, canon 28); PC never stakes own; shells kept forever at garage; any wild can prompt into a betting race (no shells); unlock end R2. **Numbers TBD:** `BET_MIN`, `BET_MAX_FRACTION`, `BET_MAX[round]`, `HOUSE_EDGE`, handicap bonus, shell drop rate, wild-prompt chance | Flat odds vs sim-derived line | After criteria: set stakes, house edge, shell rate, prompt rate |
| **Substories + story-race shop unlocks (canon 28)** | **Locked rules:** substories open after race 3 and award cash (runs through `DEBT_SHARE` while debt is open), a free skewed-sidegrade mod to garage stash (≤ tier net budget, real penalty, never aero), a shell-specific livery (R1–R2 target starter/owned substory shell), or a standout shell (mesh count TBD w/ Desmond & Arthur); lieutenant wins expand horizontal shop stock while crew bosses gate rare mods. **Numbers TBD:** `SUBSTORY_CASH_PAYOUT[round]`, `SUBSTORY_FREE_PARTS_MAX[round]`, sidegrade penalty floor, lieutenant stock count | — | After criteria: set payout, sidegrade budget & R1–R2 count |

**Blocker (07):** encounter-scaling fix before any debt/payout numbers.

---

### Tests

`cd sim && uv run --with pytest pytest -q` → **25 passed** (2026-11-04, `/workspace/parity/decision-sheet/pytest.txt`). No `equations.py` changes this turn.

---

## 0. Target curves (PROPOSED: the spec the core equations must hit)

> Author: Barry (Chief of Systems), 2026-11-03. Status: **PROPOSAL for Austin to mark up**, not measured. Placed here on Austin's call; the older sections below are not yet reconciled with it (cleanup later).
> Every number labeled **measured** comes from `design/08-skill-parity.md` (2026-11-02) or from `python3 scripts/parity_sweep.py grid2d --seeds 40` (2026-11-03, raw output in `/workspace/parity/grid2d.txt` and `grid2d.json`). Everything else is a **target or proposal**, computed from the chosen coefficients with plain math.
> 2026-11-03 revision (Austin): play quality is now **two independent skills**, q_read and q_time, and the targets must keep three play styles viable. This replaces the single-q targets from earlier the same day.

### 0.1 Purpose

Clean-sheet redesign: set the target curves first, then design the smallest set of core equations (clash resolution, QTE, AI skill) that hits them, with each constant doing one job. The targets below become the acceptance test that every candidate model gets swept against before anything goes into Godot.

Why start over (measured, 08 §5, parity_lieutenant L50, N = 2000 per q): the current levers mostly do nothing.
- CLASH_STAKES 0.20 / 0.35 / 0.60 → q50 0.264 / 0.230 / 0.195.
- BATTLE_BONUS 0.05 → 0.20 → q50 0.230 → 0.224.
- RUBBER_BAND_FRACTION 0.05 / 0.15 / 0.50 → q50 0.231 / 0.230 / 0.228.
- Only AI skill moves it: AI QTE 10 → 0.521; AI read 0.80 → 0.898; AI read 0.40 + AI QTE 10 → 0.893.
- Encounter ratios (`ai.py` ENCOUNTER_RATIOS: wild 0.75, lieutenant 1.1, boss 1.2) are **double-counted**: `cli.py:305` scales opponent level by the ratio, and `get_ai_qte` scales AI QTE by the same ratio. Measured result (08 §3.2): Wild is unlosable (q50 0, 99.9% win at q = 0), Lieutenant q50 ≈ 0.51–0.53, Boss q50 ≈ 0.81–0.83.

Proposed principle for the new model: **one input, one job.**
- Tier (wild / lieutenant / boss) sets **AI skill**, which moves s0 (where the curve sits).
- Stats (level, skill points, mods) set **r**, which moves the curve via b.
- Race length sets the slope a (measured: a rises with length, 8.83 → 10.49 → 10.68 in 08 §4).
- The two player skills are weighted equally, so no play style is the "right" one.
- No constant scales two of these at once.

### 0.2 Inputs: two skill axes

Play quality is split into two independent skills, both 0–1 (sim: `MatchConfig.player_read` / `player_timing`; `player_quality = q` is shorthand for both = q, exactly the old single q of 08 §2):

- **q_read**: each clash, the chance the player reads the AI's real pick and plays its counter (else a tie card, else any card). Otherwise the pick is random from hand.
- **q_time**: each turn, the chance of a perfect-10 QTE. Otherwise the QTE is uniform 1–10.
- **r** = opponent level / player level (later: opponent stat total / player effective stat total, including skill points and mods).
- **Tier**: wild, lieutenant, boss. **Round**: scripted races 1–3 on skill points only; mods unlock when the PC wins race 3; wholesale at the end of R1; aero when the debt hits zero (mid R2); betting at the end of R2, so R3 is capped betting and expensive mods.

Three play styles the targets must keep viable:
- **(A) Reader:** strong q_read, sloppy q_time (e.g. 1.0 / 0.6).
- **(B) Timer:** sloppy q_read, sharp q_time (e.g. 0.6 / 1.0).
- **(C) Balanced:** equal (e.g. 0.8 / 0.8, or 0.9 / 0.9).

"Total skill" below means q_read + q_time.

### 0.3 Measured: today's model on the (q_read, q_time) grid (diagnostic only)

Stat parity, AI QTE ratio 1.0, pooled over all 25 archetype pairs × levels L10/30/50/80, **N = 4000 per cell** (1000 per level). Win %, rows q_read, columns q_time.

**Lieutenant length (20 turns)**

| q_read \ q_time | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 0 | 6.0 | 22.9 | 58.3 | 86.1 | 94.2 | 97.0 |
| 0.25 | 21.0 | 56.9 | 84.5 | 96.1 | 98.3 | 98.9 |
| 0.5 | 51.8 | 82.2 | 94.9 | 98.6 | 99.3 | 99.6 |
| 0.75 | 74.5 | 93.4 | 98.3 | 99.6 | 100.0 | 100.0 |
| 0.9 | 85.8 | 95.8 | 99.0 | 99.9 | 100.0 | 100.0 |
| 1.0 | 91.1 | 97.2 | 99.4 | 100.0 | 100.0 | 100.0 |

**Boss length (30 turns)**

| q_read \ q_time | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 0 | 3.8 | 14.6 | 44.2 | 80.3 | 91.3 | 95.5 |
| 0.25 | 13.9 | 45.2 | 79.7 | 94.8 | 98.0 | 98.9 |
| 0.5 | 39.0 | 78.5 | 94.9 | 98.4 | 99.2 | 99.5 |
| 0.75 | 69.3 | 91.8 | 98.0 | 99.5 | 99.8 | 100.0 |
| 0.9 | 82.5 | 96.0 | 98.9 | 99.9 | 100.0 | 100.0 |
| 1.0 | 88.1 | 96.8 | 99.3 | 99.9 | 100.0 | 100.0 |

Logistic fits on these 36 pooled cells (measured):

| Length | additive: z = c + a_r·q_read + a_t·q_time | rms / max error | + interaction term a_rt·q_read·q_time | log-lik gain |
|---|---|---|---|---|
| Lieutenant | c −2.56, a_r 4.94, a_t 5.92 | 1.1 / 4.0 pts | a_rt +0.21 | 1.2 |
| Boss | c −3.19, a_r 5.38, a_t 6.22 | 1.3 / 4.4 pts | a_rt +0.68 | 13.3 |

**Finding: read and timing are substitutes, not complements.**
- Their effects **add** on the log-odds scale. The interaction term is near zero (Lieutenant +0.21, no real gain in fit; Boss +0.68, a small complement effect against main effects of 5–6). Either skill can replace the other.
- **Either skill alone wins today.** Perfect reading with random timing (1.0 / 0) wins 91.1% (Lt) and 88.1% (Boss). Perfect timing with random reading (0 / 1.0) wins 97.0% and 95.5%. Half of each (0.5 / 0.5) wins 94.9% at both lengths.
- **Timing is worth about 15–20% more than reading per unit** (a_t / a_r = 1.20 Lt, 1.16 Boss). At equal total skill the timer leads: 1.0 / 0 vs 0 / 1.0 is 91.1 vs 97.0 (Lt) and 88.1 vs 95.5 (Boss); 0.75 / 0.25 vs 0.25 / 0.75 is 93.4 vs 96.1 and 91.8 vs 94.8.
- The specialist gap widens with level: at L80, 1.0 / 0 wins 78.4% (Lt) and 74.9% (Boss) vs 90.8% and 88.1% for 0 / 1.0.
- Today's game is far too easy on both axes (08 §3), so these gaps sit in the saturated 90–100% region; near 50% they would matter more.

### 0.4 PROPOSED target form

One skill index, the plain mean of the two axes, inside the same logistic as 08 §4:

    s      = (q_read + q_time) / 2
    P(win) = 1 / (1 + exp( -( a·(s - s0) - b·ln r ) ))
           = logistic( a_r·q_read + a_t·q_time - a·s0 - b·ln r ),   a_r = a_t = a/2
    s50(r) = s0 + (b/a)·ln r

Why this form:
- **Additive, no interaction.** That's what the measured engine already does (0.3), so a candidate model doesn't have to fight its own structure. It fits with `parity_sweep.fit_features` using features [1, q_read, q_time, −ln r].
- **Equal weights (a_r = a_t)** make the styles balanced by construction: at equal total skill, Reader, Timer and Balanced all have the same target. Today timing is worth 1.16–1.20× reading, so the new model has to close that gap.
- **The balanced player keeps the old meaning of q**: q_read = q_time = q gives s = q.
- An interaction term was considered. A negative one (a specialist bonus) would let 1.0 / 0.6 match 0.9 / 0.9, but then 1.0 / 0 also wins easily, and perfect play barely beats 0.9 / 0.9. Left as open question 2.

### 0.5 PROPOSED coefficients

| Tier | a | a_r = a_t | s0 (= parity s50) | b | s50 shift per +10% r | slope: P(s50+0.1) − P(s50−0.1) |
|---|---|---|---|---|---|---|
| Wild | **12** | 6 | **0.58** | **12.59** | +0.10 | 54 pts |
| Lieutenant | **14** | 7 | **0.72** | **14.69** | +0.10 | 60 pts |
| Boss | **16** | 8 | **0.86** | **16.79** | +0.10 | 66 pts |

For contrast, today's single-q fits (**measured**, 08 §4): Wild a 8.83 q0 0.217 b 18.30; Lt a 10.49 q0 0.214 b 26.18; Boss a 10.68 q0 0.236 b 29.30 (q50 shift per +10% r: 0.20 / 0.24 / 0.26).

Reasoning:
- **Boss.** A balanced 0.9 / 0.9 player wins 65% at parity, close to Austin's "win if you play about 90% right". Perfect play wins 90%. A specialist with 1.0 in one skill and 0.6 in the other wins 28% at parity, which climbs to 69% with a 10% stat edge (r 0.9). That's winnable, and it gives mods a clear job for specialists. Compared with the earlier single-q draft (a 22, q0 0.90), the slope is flatter and s0 slightly lower. That's the price of making 1.0 / 0.6 viable: with a 22 it would win only 10%.
- **Lieutenant and Wild** step down by 0.14 in s0, with a flatter slope each tier down (measured: shorter races are more random). 0.9 / 0.9 wins 93% of lieutenants and 98% of wilds. Either specialist (1.0 / 0.6) wins 75% and 93%.
- **One-trick play loses.** 1.0 / 0 wins 28% (Wild), 4.4% (Lt) and 0.3% (Boss). Today it wins 88–91% (measured, 0.3), and that's the main thing the redesign changes.
- **Random play (0 / 0) wins about 0%** in every tier (Wild 0.1%). A logistic has no floor; see open question 5.
- **One stat exchange rate: +10% opponent stats ≈ +0.10 of s**, i.e. 0.2 of total skill. Today it's 0.20–0.26 of q, so a 10% stat gap swamps skill.

### 0.6 PROPOSED target tables

#### 0.6.1 Play styles, P(win) %, at r 0.9 / 1.0 / 1.1

Same total skill per block, so A, B and C are equal by design.

| Style (q_read / q_time) | Total | Wild r 0.9 / 1.0 / 1.1 | Lieutenant r 0.9 / 1.0 / 1.1 | Boss r 0.9 / 1.0 / 1.1 |
|---|---|---|---|---|
| A Reader 1.0 / 0.6 | 1.6 | 98.1 / 93.3 / 80.8 | 93.5 / 75.4 / 43.0 | 69.2 / 27.7 / 7.2 |
| B Timer 0.6 / 1.0 | 1.6 | 98.1 / 93.3 / 80.8 | 93.5 / 75.4 / 43.0 | 69.2 / 27.7 / 7.2 |
| C Balanced 0.8 / 0.8 | 1.6 | 98.1 / 93.3 / 80.8 | 93.5 / 75.4 / 43.0 | 69.2 / 27.7 / 7.2 |
| A Reader 0.9 / 0.5 | 1.4 | 94.1 / 80.8 / 56.0 | 78.0 / 43.0 / 15.7 | 31.2 / 7.2 / 1.5 |
| B Timer 0.5 / 0.9 | 1.4 | 94.1 / 80.8 / 56.0 | 78.0 / 43.0 / 15.7 | 31.2 / 7.2 / 1.5 |
| C Balanced 0.7 / 0.7 | 1.4 | 94.1 / 80.8 / 56.0 | 78.0 / 43.0 / 15.7 | 31.2 / 7.2 / 1.5 |
| C Balanced 0.9 / 0.9 | 1.8 | 99.4 / 97.9 / 93.3 | 98.3 / 92.6 / 75.4 | 91.7 / 65.5 / 27.7 |
| Perfect 1.0 / 1.0 | 2.0 | 99.8 / 99.4 / 97.9 | 99.6 / 98.1 / 92.6 | 98.2 / 90.4 / 65.5 |

#### 0.6.2 Full grid at parity (r = 1.0), P(win) %, rows q_read, columns q_time

Same grid as the measurement in 0.3, so the acceptance test lines up cell by cell. The grid is symmetric because the weights are equal.

**Wild** (a 12, s0 0.58, b 12.59)

| q_read \ q_time | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 0 | 0.1 | 0.4 | 1.9 | 7.9 | 17.4 | 27.7 |
| 0.25 | 0.4 | 1.9 | 7.9 | 27.7 | 48.5 | 63.2 |
| 0.5 | 1.9 | 7.9 | 27.7 | 63.2 | 80.8 | 88.5 |
| 0.75 | 7.9 | 27.7 | 63.2 | 88.5 | 95.0 | 97.2 |
| 0.9 | 17.4 | 48.5 | 80.8 | 95.0 | 97.9 | 98.8 |
| 1.0 | 27.7 | 63.2 | 88.5 | 97.2 | 98.8 | 99.4 |

**Lieutenant** (a 14, s0 0.72, b 14.69)

| q_read \ q_time | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0.0 | 0.1 | 0.8 | 2.2 | 4.4 |
| 0.25 | 0.0 | 0.1 | 0.8 | 4.4 | 11.6 | 20.9 |
| 0.5 | 0.1 | 0.8 | 4.4 | 20.9 | 43.0 | 60.3 |
| 0.75 | 0.8 | 4.4 | 20.9 | 60.3 | 81.3 | 89.8 |
| 0.9 | 2.2 | 11.6 | 43.0 | 81.3 | 92.6 | 96.2 |
| 1.0 | 4.4 | 20.9 | 60.3 | 89.8 | 96.2 | 98.1 |

**Boss** (a 16, s0 0.86, b 16.79)

| q_read \ q_time | 0 | 0.25 | 0.5 | 0.75 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 | 0.3 |
| 0.25 | 0.0 | 0.0 | 0.0 | 0.3 | 1.0 | 2.3 |
| 0.5 | 0.0 | 0.0 | 0.3 | 2.3 | 7.2 | 14.7 |
| 0.75 | 0.0 | 0.3 | 2.3 | 14.7 | 36.4 | 56.0 |
| 0.9 | 0.1 | 1.0 | 7.2 | 36.4 | 65.5 | 80.8 |
| 1.0 | 0.3 | 2.3 | 14.7 | 56.0 | 80.8 | 90.4 |

#### 0.6.3 Stat-gap sensitivity (PROPOSED)

| Tier | s50 at r 0.9 / 1.0 / 1.1 | Unwinnable (perfect play < 50%) at r > | Gimme (0.5 / 0.5 wins ≥ 90%) at r < |
|---|---|---|---|
| Wild | 0.47 / 0.58 / 0.68 | 1.49 | 0.78 |
| Lieutenant | 0.61 / 0.72 / 0.82 | 1.31 | 0.70 |
| Boss | 0.75 / 0.86 / 0.96 | 1.14 | 0.62 |

Implication: a boss above r ≈ 1.14 is a wall. Bosses should get their difficulty from AI skill at r ≈ 1.0, not from a stat bonus.

### 0.7 Rounds: how parts and skill points shift effective r (qualitative only)

No economy runs; those stay forbidden until Austin's economy and mods spec is approved.

- **R1, skill points only.** Skill points are the only way to move r below 1. Small, steady drops in r: the player feels themselves getting better. Bosses should still feel like 90%-right fights unless the player has really grinded.
- **R2, Reiko plus mods.** Mods are a bigger, lumpier drop in r. Encounter opponent levels need to rise to keep effective r near 1 for bosses, otherwise the R2 boss becomes a gimme. Under these targets a 10% stat edge is what turns a specialist (1.0 / 0.6) from 28% to 69% against a boss, so mods are how specialists keep up. The R2 Wangan boss is the natural check on whether mods are priced right.
- **R3, betting plus expensive mods.** Betting lets a skilled player buy r below 1 faster. Bet caps exist to stop r collapsing to a gimme (r < 0.62 for boss under these targets). The felt curve should be a sawtooth: each round starts near r ≈ 1 against new opponents, and the player buys it down over the round.
- **Open caveat from 08 §4:** the fit moved level (stats plus HP together). A stats-only bonus may be worth a different amount of r; that needs its own sweep once the skill-point and mod formats exist. Skill points that buy *skill* (e.g. a wider QTE window, a clearer tell) would move q_time or q_read instead of r; that's a design choice for the skill-point spec.

### 0.8 Acceptance criteria for a candidate model (PROPOSED)

Sweep grid: 3 tiers × q_read {0, 0.25, 0.5, 0.75, 0.9, 1.0} × q_time {same} × r {0.9, 1.0, 1.1} = **324 cells**, N ≥ 1000 per cell (about ±3.1 pts at 50%, 95% CI), pooled over archetype pairs and levels L10/30/50/80 (`parity_sweep.py grid2d`, extended to r ≠ 1).

1. **Fit to target:** max abs error ≤ 6 pts and RMS ≤ 3 pts vs the 0.4 / 0.5 targets over all 324 cells.
2. **Perfect play at parity (1.0 / 1.0, r 1.0) wins ≥ 85% in every tier** (target 90% boss, ≈ 98–99% lieutenant and wild). For reference, the current best single-q lever combo (AI read 0.40 + AI QTE 10) gives 63–87% at q = 1 (measured, 08 §6), so it would fail this.
3. **Style balance:** at equal total skill, no style beats another by more than **X = 5 pts**. Checked on every grid pair mirrored across the diagonal ((q_read, q_time) vs (q_time, q_read)), and on each off-diagonal cell vs a balanced player with the same total (interpolated from the diagonal). Every tier, r 0.9 / 1.0 / 1.1. Today, at parity, 1.0 / 0 trails 0 / 1.0 by 5.9 pts (Lt) and 7.4 pts (Boss) (measured, 0.3), so it would fail this, even in the saturated region.
4. **Weight check:** a fitted additive model on the candidate's grid has a_t / a_r within 0.9–1.1 (today 1.16–1.20, measured).
5. **Level stability:** parity s50 for the balanced diagonal within ±0.03 of target at every level L10–L80 (today q50 drifts 0.21 → 0.27 with level, and the specialist gap widens with level; measured).
6. **Monotonic:** win rate rises with q_read and with q_time and falls with r in every cell.
7. Secondary, tracked but not gating yet: archetype-pair spread at parity (today q50 0.01–0.48, measured, 08 §3.1).

### 0.9 Open questions for Austin (oldest first)

1. **Is a boss at 0.9 / 0.9 → 65%, perfect → 90% the right feel?** The earlier single-q draft had 0.9 → 50%, but then a 1.0 / 0.6 specialist won only 10%.
2. **Equal styles or a specialist bonus?** Equal weights (proposed) make A, B and C identical at equal total skill. A specialist bonus would let 1.0 / 0.6 match 0.9 / 0.9, at the cost of 1.0 / 0 also winning a lot.
3. **Is 28% for a 1.0 / 0.6 specialist against a parity boss "reasonably winnable"**, given it rises to 69% with a 10% stat edge?
4. **One exchange rate, 10% stats ≈ 0.10 of s, for all tiers?** It makes a boss above r ≈ 1.14 unwinnable.
5. **Should random play ever win?** Targets give about 0% at 0 / 0. A floor (e.g. 2–5%) needs an extra term.
6. **Tiers = AI skill only** (bosses at r ≈ 1.0, no stat bonus)? That routes difficulty through AI read and lie rates, which needs **Desmond**.

### 0.10 Flags for Desmond

- **The read axis depends on the tells.** In the game, q_read is how often the player correctly reads the AI's real pick from faces, car motion and the hand. The lie rates in `design/06-pattern-read.md` (0–50% by tier, e.g. Top Boss 50% on all clashes) directly cap what q_read can be worth. If a face lies half the time and the player can't spot the bluff, even a perfect reader can't reach q_read 1.0. So the tell rules and the target weights here have to be set together.
- Tier difficulty via AI skill (an AI read rate, AI QTE or lie rate) changes what the tells must show and needs matching Godot rules.
- Equal weighting may need a timing change too (e.g. how the QTE is scored in Godot), since today timing is worth 1.16–1.20× reading in the sim.
- Retiring the double-scaled ENCOUNTER_RATIOS changes how Godot picks opponent level and AI QTE.

---

# Stale; do not reference unless explicitly asked to

## 1. Hit Points (HP)

```
max_hp = level × HP_PER_LEVEL (120)
```

| Variable | Range | Notes |
|----------|-------|-------|
| level | 1+ | Combatant's level (from cars.py archetype progression) |

**Intent:** HP scales linearly with level. Used to compute position (damage ratio) at match end.

---

## 2. Playable turn scoring (final-v1 Phi/tau)

**Files:** `sim/velocity_shift/equations.py` — `timing_value()`, `clash_payoff()`, `clash_progress()`; `combat.py` — `resolve_turn()`.

The playable match no longer uses HP or DP. Each clash adds progress

```
g = V × Phi(outcome, q_eff) × M
V = r ** kappa                  # kappa from KAPPA_BY_LENGTH for MatchConfig.max_turns (the planned race length, not the lap)
q_eff = clip(raw_qte × (1 + ETA × (HAN_share − 1/3)), 0, 1)
```

There is no `knot_window` factor on `q_eff`. The stat gap lives in the visible zone: `qte_zone_width(r, window_mod)` (from `QTE_ZONE_WIDTH_105`, plus `MatchConfig.qte_window_mod`). A simulated player's raw score is `raw_qte_score` / `expected_hit_quality` at that zone for a PLACEHOLDER skill profile (`QTE_SKILL_SIGMA_OVER_A0`) or an explicit `player_timing` (expected hit quality at the default zone, evaluated at the race's fixed r). The zone does not change with mid-race position. A live player's entered QTE is already the raw score at the visible zone (CLI). The CLI asks for Entry, Apex, and Exit; `mean_phase_qte` averages them into the turn's single `raw_qte` (unplayed / None = `PHASE_QTE_UNPLAYED`). **QTE score rounding (2026-11-12, Austin approved via Desmond):** `raw_qte_score` and each `phase_raw_qte` return `round_qte_score(x) = floor(x · 10^QTE_SCORE_DECIMALS + 0.5) / 10^QTE_SCORE_DECIMALS` (half-up on the scaled double, then an exact-integer division; non-finite values pass through). Only correctly rounded IEEE `*`, `+`, `/` and `floor` are used, so the bits are identical on every platform; `expected_hit_quality` itself stays unrounded (it is also used to invert the zone table). The rule is not Python `round()` (half-even on the exact binary value: e.g. 0.0045 → 0.004 there, 0.005 here) and not Godot `snappedf(x, 0.001)` (divides and multiplies by the inexact 0.001; differs in the last bit on ~14% of inputs). Godot mirrors it as `floor(x * 1000.0 + 0.5) / 1000.0` and sums the three rounded phases in Entry, Apex, Exit order before `/ 3.0`. The `q_eff` formula and `clash_progress` are unchanged. HAN still scales `q_eff` on both sides. The opponent's raw score is `OPPONENT_QTE` (1.0), with HAN, unchanged. `Phi` is the tau-shaped payoff (`W0`, `T_MAX`, `L_MAX`, `TAU_BETA`, `TAU_P_TOP`). `M` raises a win by POW share and a tie/loss by EN share (`MU`). The race is the sum of all clash progress; the higher total wins, ties allowed. There is no knockout, rubber-band, battle bonus, or mitigation.

`KNOT_WINDOW_105` / `knot_window` are legacy: they still generate the zone table (average `E[s]` equals `AVERAGE_PLAY_Q × knot_window(r)`) and back the `winrate_n4000.json` / progression oracle. Knots: (0.80, 0.41), (0.85, 0.41), (0.90, 0.41), (0.95, 0.43), (1.00, **0.67**, was 0.68 before 2026-11-11), (1.05, 1.00). They are not used in `clash_progress` or `resolve_turn`. Slot competition and the 105%-all-slots rule for window mods belong to the upcoming slot sim and are not applied here.

The CLI still asks for a 1–10 QTE on each of Entry, Apex, and Exit and divides by 10; a blank / unplayed phase is 0, and the three scores are averaged into the turn's `raw_qte`. `q_read` drives the equations_v4 line-read model (correct Entry tell commits to the most likely same-Entry line; a misread aims at a tie vs the actual card with probability `q_read`, else a loss), then `assign_hand` from a 6-card stat-weighted draw.

### Legacy HP/DP (not the playable engine)

**File:** `sim/velocity_shift/equations.py` — `compute_damage()`; `combat.py` — `resolve_turn_legacy()` (`MatchConfig.legacy_hp_dp=True`).

```
DP_i = POW × QTE_factor × clash_mult_i × battle_mult
```

| Variable | Source | Range | Notes |
|----------|--------|-------|-------|
| POW | CombatantStats | 0+ | Attacker's power |
| QTE_factor | derived | 0.1–1.0 | QTE_score / QTE_NORMALIZER (10) |
| clash_mult_i | derived | 0.65–1.35 | Per-clash outcome |
| battle_mult | derived | 1.0+ | 1 + BATTLE_BONUS × \|sum\| |

**Intent:** Pure multiplicative chain. No gates, no interaction terms, no sigmoid.

### Turn DP (after mitigation)

```
DP_turn_effective = average(DP_1, DP_2, DP_3) × opponent_mitigation_mult
```

Where mitigation comes from the *opponent's* EN (it mitigates your damage):

```
opponent_mitigation_mult = max(MITIGATION_FLOOR, 1 - (opponent_EN / 1000) × MITIGATION_PER_1000 × opponent_QTE_factor)
```

---

## 3. QTE Effectiveness

**File:** `sim/velocity_shift/equations.py` — `qte_factor()`

```
QTE_factor = QTE_score / QTE_NORMALIZER (10)
```

| Variable | Range | Notes |
|----------|-------|-------|
| QTE_score | 1–10 | Execution rating per turn |

**Intent:** Linear normalization. A QTE_score of 7 yields a 0.7 multiplier on all damage for that turn.

---

## 4. Clash Multiplier

**File:** `sim/velocity_shift/equations.py` — `clash_mult()`

```
clash_mult = 1 + CLASH_STAKES (0.35) × outcome_value
```

| Variable | Range | Notes |
|----------|-------|-------|
| outcome_value | {-1, 0, +1} | LOSS / DRAW / WIN |

| Outcome | Bonus | Mult |
|---------|-------|------|
| WIN | +0.35 | 1.35× |
| DRAW | 0 | 1.00× |
| LOSS | -0.35 | 0.65× |

**Intent:** Single-parameter outcome modifier. 0.35 is the fixed game-wide clash stakes.

---

## 5. Battle Multiplier

**File:** `sim/velocity_shift/combat.py` — (inline in `resolve_turn()`)

```
battle_mult = 1 + BATTLE_BONUS (0.05) × |sum(outcome_values)|
```

| Variable | Range | Notes |
|----------|-------|-------|
| outcome_sum | -3 to +3 | Sum of 3 per-clash outcome values (±1 each) |

| Result | Margin | Mult |
|--------|--------|------|
| Tie | 0 | 1.00× |
| 2-1 win | 1 | 1.05× |
| 3-0 sweep | 3 | 1.15× |

**Intent:** Winning a battle should feel impactful. Each point of win margin gives a small flat boost to all damage that turn.

---

## 6. Stance Resolution

### 6.0 Naming map (Austin, 2026-11-12)

Stances are named by the stat that feeds them. Everything behind the screen (sim code, data, line tables, specs and these docs) uses **POW / EN / HAN** only. This table is the one place the old names appear; other docs refer here.

| Stat / stance | Old stance names (retired) | Old code (retired) | New code (`sim/velocity_shift/models.py`) | Line-table letter (`LINE_SET_C`), old → new |
|---|---|---|---|---|
| **POW** | Attack, ATK | `Stance.ATTACK = "attack"` | `Stance.POW = "POW"` | A → **P** |
| **EN** | Defend, DEF | `Stance.DEFEND = "defend"` | `Stance.EN = "EN"` | D → **E** |
| **HAN** | Neutral, Steady, NEU | `Stance.NEUTRAL = "neutral"` | `Stance.HAN = "HAN"` | S → **H** |

- The clash outcome for the same stance on both sides was `StanceOutcome.NEUTRAL`; it is now **`StanceOutcome.DRAW`** (value 0, unchanged).
- Line tables are written as stat sequences, Entry-Apex-Exit: e.g. Touge hairpin main line `EHP` = EN-HAN-POW (was `DSA`).
- **On screen only** (art, lane labels, camera): POW is drawn on the OUT lane, HAN on MID, EN on IN, relative to the corner, so OUT on a left turn and OUT on a right turn are the same stance. Backend docs don't use the lane words.
- The rename changed names only; every number is identical (CHANGELOG 2026-11-12).

**File:** `sim/velocity_shift/equations.py` — `resolve_stance()`

```
POW vs POW → DRAW
POW vs HAN → WIN      (POW beats HAN)
POW vs EN  → LOSS     (EN beats POW)
HAN vs HAN → DRAW
HAN vs EN  → WIN      (HAN beats EN)
HAN vs POW → LOSS     (POW beats HAN)
EN  vs EN  → DRAW
EN  vs POW → WIN      (EN beats POW)
EN  vs HAN → LOSS     (HAN beats EN)
```

RPS cycle: **POW > HAN > EN > POW**

---

## 7. Battle Winner

**File:** `sim/velocity_shift/combat.py` — `battle_winner()`

```
outcome_values = [outcome_value_1, outcome_value_2, outcome_value_3]
winner = sign(sum(outcome_values))
battle_mult = 1 + 0.05 × |sum|
```

| Sum | Result | battle_mult |
|-----|--------|-------------|
| > 0 | Player wins clashes | 1.05 (2-1) or 1.15 (3-0) |
| < 0 | Opponent wins clashes | 1.05 or 1.15 for opponent |
| = 0 | Tie | 1.00 |

---

## 8. Damage Mitigation

**File:** `sim/velocity_shift/equations.py` — `damage_mitigation()`

```
mitigation_mult = max(MITIGATION_FLOOR, 1 - (EN / 1000) × MITIGATION_PER_1000 × QTE_factor)
```

Applied per turn: each combatant's EN reduces the opponent's effective DP.

| Variable | Range | Notes |
|----------|-------|-------|
| EN | 0+ | Defender's Endurance stat |
| QTE_factor | 0.1–1.0 | Defender's execution quality that turn |

| Scenario | Mitigation mult | Damage taken |
|----------|----------------|--------------|
| EN=0 | 1.0 | 100% |
| EN=500, QTE=0.7 | 0.86 | 86% |
| EN=1000, QTE=0.7 | 0.72 | 72% |
| EN=1000, QTE=1.0 | 0.60 | 60% |
| EN=1650, QTE=1.0 | 0.34 | 34% |

**Intent:** Higher EN makes you tougher, but only if you're driving well (QTE). Good execution rewards both offense and defense. The 10% floor prevents total immunity.
