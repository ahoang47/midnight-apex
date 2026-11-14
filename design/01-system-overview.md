# Midnight Apex — System Overview

> **Design canon: locked terms and decisions (2026-11-04; designated design canon by Austin 2026-11-12).** This block is the source of truth for Austin's mechanical and scope decisions; if any other design/ file disagrees, this block wins. Add a decision here only once Austin has approved it, with its date; unapproved proposals go in `unapproved/<owner>/`. Use these terms everywhere in design/. The game is **Midnight Apex**; the sim lives in `sim/` (Python package `sim/velocity_shift/`, named after the engine's old working title).
> - **Race tiers:** **wild race** (open-world pushover for EXP farming; code `wild`), **betting race** (any wild race turned into a bet through a prompt, harder than wild and a bit easier than lieutenants; never awards shells), **lieutenant** (crew members; code `lieutenant`), **crew boss** (the crew's chief; code `boss`), **Myth Driver race** (Finale story races; like wild races, no loss persistence). "Lackey", "crew chief", "Lieutenant Challenge" and "encounter" are informal synonyms; prefer the terms above.
> - **Crew ladder:** each district has one crew, raced once from start to finish: kids, then mature members, then old heads (all lieutenants), then the crew boss. There are no rematches (Finale training sessions with former crew members, 2026-11-13, aren't rematches), and the boss no longer levels up the crew between rounds.
> - **Round structure (Austin, 2026-11-13):** one district per round: Round 1 is Street, Round 2 is Wangan, Round 3 is Touge. Each round covers its own district's incident, consequences and distortion from start to finish (this replaces the old per-round themes). Free crew order (2026-11-10) and canon 12 are retired. Each Myth Driver gets one sighting: #3 after the Street round, #2 after Wangan, #1 after Touge (as a challenge only, with no race yet). After the Touge round come the Mentor Confrontation and the rift, and then the PC goes back up the mountain to race #1, which opens the rest of the Finale. **Sim:** the 3-crew ladder is live in `sim/` (econ-v1, Barry, 0af2715).
> - **Reputation:** the in-world reason crews take you on. It's lore only, not a tracked stat, and it's never called "street cred" or "rep".
> - **Persistence:** loss persistence applies only to crew members (lieutenants) and crew bosses: if you lose to one of them, that driver remembers it in later barks and retries (canon 27). Wild races and Myth Driver races don't have loss persistence. Scripted race 3 still has its own win gate to unlock mods (canon 19), and losing to a crew boss means a retry.
> - **Stats:** **POW** (Attack), **EN** (Defend), **HAN** (the third stance). The third stance is **Neutral** everywhere, player-facing too (`NEUTRAL` in code; resolved 2026-11-11, art Q6 in `design/art/art_direction.md`, 55b9063).
> - **Naming (Austin, 2026-11-12):** stats, stances and line choices are written **POW / EN / HAN** everywhere behind the screen: code, data, sim, specs, line tables (e.g. `story/corner_lines.md`) and docs about the math. Attack / Steady / Neutral / Defend and the A/S/D letters are retired. **OUT / MID / IN** is for visuals only (on-screen lane labels, art, lane placement, camera), shown with the stat it calls for: OUT (POW), MID (HAN), IN (EN). A lane is read relative to the corner's direction, so OUT on a left turn and OUT on a right turn are the same POW line. The line-choice rules themselves are unchanged.
> - **Play quality:** two skills, **read** (`q_read`, countering the AI's real pick) and **timing** (`q_time`, the **QTE**). `player_quality` sets both. **Phase QTE (Austin, 2026-11-11, f0efecf):** each turn has an entry, apex and exit QTE; the sim scores each phase 0 to 1, the three are averaged into the turn's one raw QTE with no other math changed (`QTE_PHASES`, `mean_phase_qte`, `phase_raw_qte`), and an unplayed phase scores `PHASE_QTE_UNPLAYED` (0). The CLI's 1–10 entry is only an input format. **QTE rounding (Austin, 2026-11-12, c3ffc41):** each phase score is rounded to 3 decimals (`QTE_SCORE_DECIMALS`); the mean of the three isn't rounded again.
> - **Stat parity:** the ratio of opponent stats to player stats; 0.8–1.2 counts as parity. The story caps the player at 0.8 of the top unlocked crew boss's stats.
> - **Combat scoring (final-v1; Austin 2026-11-09, playable engine 2026-11-10, 0dd376a):** a turn is 3 clashes (entry, apex, exit); each adds progress `g = V × Φ(outcome, q_eff) × M` with `V = r**kappa` (`KAPPA_BY_LENGTH`, `kappa_for_length(max_turns)`), and the higher progress total wins. There is no HP/DP; that path is legacy only (`resolve_turn_legacy`, `MatchConfig.legacy_hp_dp`). Opponents pick one whole line per corner from `LINE_SET_C` (`LINE_ADHERENCE`, `LINE_ALT_WEIGHTS`; Street N90 and Wangan IR/SW mains approved 2026-11-10, 6fc87d5). Equations: 02.
> - **Visible QTE zone (qte-v1; Austin 2026-11-11, 4cb5401):** the stat gap r sets the width of the visible QTE zone (`qte_zone_width`, `QTE_ZONE_WIDTH_105`, `QTE_ZONE_BASE_MS`); there is no hidden `knot_window` factor on the player's timing (`clash_progress`: `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)`). The skill σ values (`QTE_SKILL_SIGMA_OVER_A0`) are placeholders until playtest.
> - **Parity knot and aero cap (Austin 2026-11-11, 5e5d902):** the r = 1.00 knot in `KNOT_WINDOW_105` is 0.67 (was 0.68), which sets `QTE_ZONE_WIDTH_105`. Aero goes in any slot, at most `AERO_MAX_EQUIPPED` (1) equipped, counts inside the 105 % cap (`AERO_COUNTS_IN_MOD_CAP`), and its free wind-tunnel pool is at most `AERO_FREE_POOL_MAX_FRACTION` (10 %) of the part's total.
> - **Mod slots (Austin 2026-11-11):** 6 slots in 3 categories × 2 (primarily POW, primarily EN, primarily HAN). A window mod and an aero part can each go in any slot, at most one of each equipped. Available stat mods only just reach the 105 % cap (`MOD_CAP_FRACTION`) when every slot is filled, never above. Not yet in sim constants; window size, prices and secondary splits are unapproved (`unapproved/barry/slots-v2/`).
> - **New mods never skip a wall (Austin 2026-11-11):** a newly unlocked mod must not make the next wall beatable on its own, and grind stays mandatory. **Mod tier level floor (Austin 2026-11-12, 29f8431):** each crew's mature #2 mod tier needs a minimum car level before it can be fitted (`MOD_TIER_LEVEL_FLOOR`, `MOD_TIER_FLOOR_RUNG`, `MOD_TIER_FLOOR_MARGIN`; `mod_tier_available`). 07 §6.4.
> - **Progression unlocks:** the first 3 races are scripted. **Mods** (parts bought once from Reiko at full price) unlock when the PC **wins race 3**, which also opens the world and **substories** (canon 19, 28). Beating story races up each crew's ladder (**lieutenants** as well as **crew bosses**) expands Reiko's paid shop stock, with crew bosses gating rare tier-jump mods (canon 28). **⚠ CONFLICT, pending Desmond's rewording of canon 28:** Austin decided on 2026-11-09 that mods are **bought only**; boss wins pay XP (levels, so some SP), money, a shell and a graphic, not rare mods. Canon 28 is not rewritten here; see 07 §5.2 and §8. **Wholesale** (Reiko's discount) unlocks at the end of Round 1. **Aero** (base boost plus a free point pool, tuned at the speakeasy's **wind tunnel**) unlocks when the **debt** to Sabine hits zero, which happens when the PC beats the Street crew boss at the end of Round 1, the same moment as wholesale (Austin, 2026-11-13; `DEBT_CLEAR_AFTER` in the sim). **Betting** unlocks at the end of Round 2, after the Wangan crew boss (`BETTING_UNLOCK_AFTER`); the finale opens after Round 3, the Touge round (`FINALE_UNLOCK_AFTER`). **Shells** (car bodies) and shell-specific **graphics/liveries** are cosmetic only: crew bosses' signature shells come only from crew boss betting races at the promoter's subsea Wangan parking-area home base, while **substories** each award cash (through Sabine's normal debt cut while open), a free skewed-sidegrade mod straight to the garage stash (never aero), a shell-specific livery (Round 1–2 liveries target the starter shell or an already earned substory shell; later ones can tease locked shells), or—for a few standout substories—an oddball shell (canon 26, 28).
> - **XP → levels → skill points (2026-11-09):** skill points come only from car levels; levels come from XP earned in story wins and **grind races** (repeatable races between story characters). The **level cap** equals the 80 % SP cap (`SP_CAP_FRACTION`) and rises with each story win; XP past the cap is lost. SP per level rises as levels go up, and each level costs more XP (`sp_per_level`, `xp_to_next`). Grind-race XP pays proportionally less further up each crew's ladder and at higher levels (per-crew taper: `grind_payout_fraction`, `TAPER_*`). Crew boss wins pay XP (so SP), money, a shell and a graphic; mods are bought only (see the canon 28 conflict above). Model: grind v8c (0c90c9c). See 07 §8 and `sim/velocity_shift/progression.py`.
> - **Respec:** moving locked skill points (Jesse) or retuning aero (the tunnel) costs money and is capped per visit. **After the rift (Austin, 2026-11-11; canon in story/):** after the Mentor Confrontation Jesse stops respecs and tuning for the PC; both move to the speakeasy with Malo.
> - **Pre-finale training arc (Austin, 2026-11-13):** after the rift, Round 1–3 crew members hear what the PC is doing, respect it, and come back to train the PC. These are **training sessions, not rematches**, so the no-rematch rule above still holds. Shape: four Touge races before the #1 race (10, 20, 20 wall, 30 gate), then two before each later finale race (a 10, then a 20 wall). Cast: the Touge kid, mature member, phone-call old head and crew boss before #1; a Wangan lieutenant and the Wangan boss before #2; a Street lieutenant and the Street boss before #3; and, as the crews come up the mountain, a Wangan or Street old head and the other Touge old head before the summit. On some corners a trainer drives the next Myth Driver's line and bluff. Crew loss persistence applies. The **summit (F4) is the final race against Sabine** (canon 4); the story reason she's there is still open with Austin. Proposal and sim: `design/notes/finale-arc-cast-v1.md`, Barry's econ-v1 (live 2026-11-13).
> - **Shop after the rift (Austin, 2026-11-11):** Wholesale ends at the Mentor Confrontation; Reiko returns to full price but keeps selling through the Finale. **Big mods (Austin, 2026-11-10; unlock moved 2026-11-13):** the big Finale mods (the T4 tier) unlock when the PC wins the first training race after the rift (P1), bought from Reiko at full price.
> - **DAQ log (Austin, 2026-11-11):** Jesse's logger keeps only the last race and plays it back as a per-corner list of the PC's and the opponent's lines; after the rift the PC pulls it up alone. UI is Gordon's.
> - **Finale order (Austin, 2026-11-12):** Myth Driver races run in fixed order: Touge #1, Wangan #2, Street #3.
> - **Tracks (Austin, 2026-11-12):** 3 tracks per district, 9 in total. Every track is exactly 10 turns per lap. 20- and 30-turn races are 2 and 3 laps of the same track. Each district has a few signature corners where every racer in the district runs the same standard line and bluff; on other corners wild racers share one line and bluff and each named character has their own style (which corners and lines: pending, sim paused on Austin's call).
> - **Art (Arthur):** locked art rules live in `design/art/art_direction.md` (approved items marked MUST/APPROVED with dates).
> - **Build (Godot), approved by Austin:** development is **Godot 4.6.3 only**, with no Three.js build (2026-11-11). **Combat freeze (2026-11-10):** no Godot combat work except the two-corner engine test, which uses provisional numbers and lives in `unapproved/gordon/two-corner/`. **Exit→Entry lockout** rule deleted (2026-11-08). **Render (2026-11-11):** the 3D scene is 640×480 with no antialiasing, scaled up by whole numbers with nearest-neighbour; HUD text is drawn sharp on a 1280×960 grid (art rule B.5c in `design/art/art_direction.md`). **QTE (2026-11-11):** difficulty scales only through the visible zone width (`qte_zone_width` at the race's fixed r in `sim/`); the old level-gap `qte_difficulty()` scaling is dropped. Each turn has three QTEs (Entry, Apex, Exit); an unplayed QTE scores 0, and the three scores are averaged into one score that every clash in the turn uses (final, Austin 2026-11-11; sim f0efecf, build matches). **Turn flow (2026-11-11, 2026-11-12):** line select and playback never pause; the only pause is a timed Enter-to-continue after a turn completes. The player picks Entry, then Apex and Exit at static camera stops; the three QTEs play during playback, each on its own timer, with the cars held in that phase and the road scrolling while it runs. Passes are shown during play, but the car order only changes after the Exit QTE finishes, for both cars, even when the outcome is already certain (2026-11-12): if both cars share the exit lane, the passer moves to an open lane for the pass, with no clipping. **Public demo:** Austin updates nodestar.tech himself.
> - **Places:** Jesse (the Tuner) and Reiko (parts) work out of **Sabine's garage**; the **speakeasy** is the barkeep Malo's bar (named 2026-11-11) with the hidden wind tunnel.
> - **Level bands** in 04 (Starter … Legend) are stat-budget labels, not race tiers.

A turn-based racing combat engine. Two combatants race a 10-turn lap (1–3 laps). Each turn the player picks a 3-stance line (entry, apex, exit) from any stance whose heat gauge is not locked (heat/load system, Austin approved 2026-11-13; the card draw is gone), the opponent draws a whole district line, and each of the 3 clashes adds Phi/tau progress; the higher progress total wins. The locked rules are in the canon block above; equations and constants are in `design/02-equations-reference.md` and `sim/velocity_shift/equations.py`.

---

## Architecture

```
sim/main.py
  └─> velocity_shift/
        ├─> cli.py          — Interactive match setup, prompts, display, run_cli
        ├─> models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
        ├─> equations.py    — Pure math and all constants: QTE zone, clash progress, kappa, line sets, progression
        ├─> heat.py         — Heat/load gauges (POW engine, HAN suspension, EN brakes), load calibration, boss heat rule
        ├─> combat.py       — resolve_turn (Phi/tau progress), pick_line, resolve_turn_legacy
        ├─> match.py        — run_match, multi-turn loop, progress-total winner
        ├─> ai.py           — Encounter laps/phases (+ legacy AI QTE)
        ├─> trace.py        — Structured execution logger
        ├─> simulation.py   — Batch runner + simulated player (read model, heat pacing)
        ├─> progression.py  — Story ladder + XP/level/SP progression model (grind v8c)
        └─> config.py       — build_from_archetype factory
  └─> config/
        └─> sample_builds.json  — Preset player builds
  └─> ../design/               — Design docs at repo root (keep in sync if variables change)
```

### Package boundaries

| File | Role |
|------|------|
| `sim/velocity_shift/models.py` | All data classes and enums — no logic |
| `sim/velocity_shift/equations.py` | Pure functions — no state, no side effects. All game constants as module-level names in equations.py — tunable in one place |
| `sim/velocity_shift/heat.py` | Heat/load gauges: `HeatGauges` (cost, overrun, lock, release, limp), `track_wear` / `avg_heat_demand` calibration, `boss_stance` |
| `sim/velocity_shift/combat.py` | Turn resolution orchestration + clash/battle logic |
| `sim/velocity_shift/match.py` | Multi-turn match loop with callbacks |
| `sim/velocity_shift/ai.py` | Encounter laps/phases; legacy AI QTE (HP/DP only) |
| `sim/velocity_shift/trace.py` | Structured execution logger |
| `sim/velocity_shift/simulation.py` | Headless batch runner, simulated player (read model + reserve pacing), result export |
| `sim/velocity_shift/progression.py` | Story ladder (budgets, level caps, story/grind XP, walls) over the econ-v1 heat-system win-rate table `sim/config/winrate_g2_econ_v1.json`; report via `sim/scripts/run_progression.py` |
| `sim/velocity_shift/cli.py` | Interactive frontend (setup, prompts, display, entry point) |
| `sim/velocity_shift/config.py` | Factory function for archetype-based builds |

---

## Live combat model (one turn)

Superseded text removed 2026-11-12: the HP/DP data flow, `HP_PER_LEVEL` / `QTE_NORMALIZER` normalization, level-gap difficulty ratios, the persistent 192-card deck loop and the position (DP / max HP) win decision described the legacy path (`resolve_turn_legacy`, `MatchConfig.legacy_hp_dp`), not the live sim. The canon block wins; this is a map, not a second spec.

```
Track: district + lap → heat.track_wear (HEAT_DEMAND_SLANT, normalised total); gauges sized by
        heat_capacity (HEAT_CAP_TURNS, HEAT_RECOVERY, HEAT_SHARE_EXP, HEAT_R_EXP) from heat.avg_heat_demand
        │
Opponent: pick_line from LINE_SET_C[district][corner] (LINE_ADHERENCE, LINE_ALT_WEIGHTS)
        │      plays it under the boss heat rule (heat.boss_stance, BOSS_HEAT_*)
Player: per clash, any stance whose gauge is not locked; each adds CORNER_HEAT_COST × wear ×
        │      (1 + HEAT_REPEAT_SURCHARGE × earlier uses this turn); overrun pays overrun_mult
        │      (OVERRUN_SLOPE, OVERRUN_FLOOR); a full gauge locks until load < HEAT_RELEASE × cap;
        │      all three locked = limp (LIMP_MULT). End of turn: CORNER_HEAT_PASSIVE, recovery, release.
Player QTE: entry/apex/exit phases → mean_phase_qte (unplayed = PHASE_QTE_UNPLAYED)
        │      zone width = qte_zone_width(r, qte_window_mod); opponent uses OPPONENT_QTE
        ▼
clash_progress x3: g = V × Φ(outcome, q) × stat_payoff_mult(share of the stance played) × heat mult
        │      V = r**kappa_for_length(max_turns)  (KAPPA_BY_LENGTH × KAPPA_HEAT_MULT); STAT_M_W
        ▼
progress totals accumulate; after max_turns the higher total wins
(an exact tie is recorded as "Tie"; how a tie reads in game is not decided)
```

- **Stats:** POW / EN / HAN set each gauge's capacity and recovery (stat share) and weight the payoff of the stance played (`STAT_M_W`); the stat gap is the ratio r (player / opponent), which sets `V`, gauge size and the visible QTE zone. The SP + mods cap is `MOD_CAP_FRACTION`.
- **Heat:** POW = engine heat, HAN = suspension load, EN = brake/tire heat; all three recover during the race. Rules and values: `sim/velocity_shift/equations.py` ("Heat / load resource system") and `heat.py`; study: `unapproved/barry/resources-v4/RESULTS.md` (v4b, G2_slant_m10). Boss heat behaviour and the district tuned splits are open for Desmond / Nathaniel.
- **Difficulty:** set by r per rung (`LADDER_TARGET_R`, the target r at each rung's level cap) and by race length (`kappa_for_length`), not by level-gap ratios or per-encounter knobs. Targets the heat system was fitted to: perfect play at 80 % stats wins 10–25 % on 20/30-turn races, perfect play at 100 % ≥ 85 %, average play at the cap 60–75 % (check: `sim/scripts/balance_gauntlet.py`).
- **Progression:** levels, caps, grind walls and the mod tier floor live in `sim/velocity_shift/progression.py`; see 07 §6 and §8. Live since econ-v1 (Austin go-ahead 2026-11-13): the 3-round ladder (`CAP_LEVEL` 12 / 29 / 46, finale caps `FINALE_CAP_LEVEL` 63 / 76 / 95 / 114) on the heat-system oracle `sim/config/winrate_g2_econ_v1.json`.
- **Global knobs:** every game constant is a named module-level value in `sim/velocity_shift/equations.py`; docs cite names, not copied values. Seeded RNG keeps runs reproducible.
