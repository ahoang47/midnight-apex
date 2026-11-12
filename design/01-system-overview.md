# Midnight Apex — System Overview

> **Design canon: locked terms and decisions (2026-11-04; designated design canon by Austin 2026-11-12).** This block is the source of truth for Austin's mechanical and scope decisions; if any other design/ file disagrees, this block wins. Add a decision here only once Austin has approved it, with its date; unapproved proposals go in `unapproved/<owner>/`. Use these terms everywhere in design/. The game is **Midnight Apex**; the sim lives in `sim/` (Python package `sim/velocity_shift/`, named after the engine's old working title).
> - **Race tiers:** **wild race** (open-world pushover for EXP farming; code `wild`), **betting race** (any wild race turned into a bet through a prompt, harder than wild and a bit easier than lieutenants; never awards shells), **lieutenant** (crew members; code `lieutenant`), **crew boss** (the crew's chief; code `boss`), **Myth Driver race** (Finale story races; like wild races, no loss persistence). "Lackey", "crew chief", "Lieutenant Challenge" and "encounter" are informal synonyms; prefer the terms above.
> - **Crew ladder:** every round the PC runs each whole crew in order: kids, then mature members, then old heads (all lieutenants), then the crew boss. Between rounds the boss levels up the whole crew. **Crew order is free (Austin, 2026-11-10):** within a round the PC may challenge the three district crews in any order, but is locked into a crew once started until its boss is beaten; rounds stay gated (all three bosses before the next round). Budgets and cap raises are keyed by **play position**, not district: the first crew the PC challenges in Round 2 / Round 3 is the **round-opening crew** (`OPTION_A_ROUND_STEP`, `CAP_ALLOC_ROUND_OPEN`), the rest step by `OPTION_A_CREW_STEP` (`DISTRICTS`, `DEFAULT_CREW_ORDER` in `sim/velocity_shift/equations.py`; the default order is only an example for reports and tests). All 216 legal orders give the same walls and totals (`python scripts/run_progression.py --all-orders`).
> - **Reputation:** the in-world reason crews take you on. It's lore only, not a tracked stat, and it's never called "street cred" or "rep".
> - **Persistence:** loss persistence applies only to crew members (lieutenants) and crew bosses: if you lose to one of them, that driver remembers it in later barks and rematches (canon 27). Wild races and Myth Driver races don't have loss persistence. Scripted race 3 still has its own win gate to unlock mods (canon 19), and losing to a crew boss means a retry.
> - **Stats:** **POW** (Attack), **EN** (Defend), **HAN** (the third stance). The third stance is **Neutral** everywhere, player-facing too (`NEUTRAL` in code; resolved 2026-11-11, art Q6 in `design/art/art_direction.md`, 55b9063).
> - **Naming (Austin, 2026-11-12):** stats and stances are always written **POW / EN / HAN**; this replaces Attack / Steady / Neutral / Defend in docs, UI and story (code identifiers can be renamed by their owners). Line choice is always **OUT / MID / IN**, with a short note of the stat it calls for: **OUT (POW)**, **MID (HAN)**, **IN (EN)**. Line choice is read relative to the corner's direction, so OUT on a left turn and OUT on a right turn are the same line and the same stat even though the car sits on opposite sides of the road. The line-choice rules themselves are unchanged. **Backend vs visual (Austin, 2026-11-12):** everything behind the screen (code, data, sim, specs, line tables like `story/corner_lines.md`, and docs about the math) refers to lines and stances only by stat: POW / EN / HAN. OUT / MID / IN is used only for visual reference: on-screen lane labels, art, lane placement and the camera.
> - **Play quality:** two skills, **read** (`q_read`, countering the AI's real pick) and **timing** (`q_time`, the **QTE**). `player_quality` sets both. **Phase QTE (Austin, 2026-11-11, f0efecf):** each turn has an entry, apex and exit QTE; the sim scores each phase 0 to 1, the three are averaged into the turn's one raw QTE with no other math changed (`QTE_PHASES`, `mean_phase_qte`, `phase_raw_qte`), and an unplayed phase scores `PHASE_QTE_UNPLAYED` (0). The CLI's 1–10 entry is only an input format.
> - **Stat parity:** the ratio of opponent stats to player stats; 0.8–1.2 counts as parity. The story caps the player at 0.8 of the top unlocked crew boss's stats.
> - **Combat scoring (final-v1; Austin 2026-11-09, playable engine 2026-11-10, 0dd376a):** a turn is 3 clashes (entry, apex, exit); each adds progress `g = V × Φ(outcome, q_eff) × M` with `V = r**kappa` (`KAPPA_BY_LENGTH`, `kappa_for_length(max_turns)`), and the higher progress total wins. There is no HP/DP; that path is legacy only (`resolve_turn_legacy`, `MatchConfig.legacy_hp_dp`). Opponents pick one whole line per corner from `LINE_SET_C` (`LINE_ADHERENCE`, `LINE_ALT_WEIGHTS`; Street N90 and Wangan IR/SW mains approved 2026-11-10, 6fc87d5). Equations: 02.
> - **Visible QTE zone (qte-v1; Austin 2026-11-11, 4cb5401):** the stat gap r sets the width of the visible QTE zone (`qte_zone_width`, `QTE_ZONE_WIDTH_105`, `QTE_ZONE_BASE_MS`); there is no hidden `knot_window` factor on the player's timing (`clash_progress`: `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)`). The skill σ values (`QTE_SKILL_SIGMA_OVER_A0`) are placeholders until playtest.
> - **Parity knot and aero cap (Austin 2026-11-11, 5e5d902):** the r = 1.00 knot in `KNOT_WINDOW_105` is 0.67 (was 0.68), which sets `QTE_ZONE_WIDTH_105`. Aero goes in any slot, at most `AERO_MAX_EQUIPPED` (1) equipped, counts inside the 105 % cap (`AERO_COUNTS_IN_MOD_CAP`), and its free wind-tunnel pool is at most `AERO_FREE_POOL_MAX_FRACTION` (10 %) of the part's total.
> - **Mod slots (Austin 2026-11-11):** 6 slots in 3 categories × 2 (primarily POW, primarily EN, primarily HAN). A window mod and an aero part can each go in any slot, at most one of each equipped. Available stat mods only just reach the 105 % cap (`MOD_CAP_FRACTION`) when every slot is filled, never above. Not yet in sim constants; window size, prices and secondary splits are unapproved (`unapproved/barry/slots-v2/`).
> - **New mods never skip a wall (Austin 2026-11-11):** a newly unlocked mod must not make the next wall beatable on its own, and grind stays mandatory. **Mod tier level floor (Austin 2026-11-12, 29f8431):** each crew's mature #2 mod tier needs a minimum car level before it can be fitted (`MOD_TIER_LEVEL_FLOOR`, `MOD_TIER_FLOOR_RUNG`, `MOD_TIER_FLOOR_MARGIN`; `mod_tier_available`). 07 §6.4.
> - **Progression unlocks:** the first 3 races are scripted. **Mods** (parts bought once from Reiko at full price) unlock when the PC **wins race 3**, which also opens the world and **substories** (canon 19, 28). Beating story races up each crew's ladder (**lieutenants** as well as **crew bosses**) expands Reiko's paid shop stock, with crew bosses gating rare tier-jump mods (canon 28). **⚠ CONFLICT, pending Desmond's rewording of canon 28:** Austin decided on 2026-11-09 that mods are **bought only**; boss wins pay XP (levels, so some SP), money, a shell and a graphic, not rare mods. Canon 28 is not rewritten here; see 07 §5.2 and §8. **Wholesale** (Reiko's discount) unlocks at the end of Round 1. **Aero** (base boost plus a free point pool, tuned at the speakeasy's **wind tunnel**) unlocks when the **debt** to Sabine hits zero, early in Round 2 after the PC beats the first crew of the round (`DEBT_CLEAR_AFTER`; Austin, 2026-11-10). **Betting** unlocks at the end of Round 2 (`BETTING_UNLOCK_AFTER`); the finale opens after Round 3 (`FINALE_UNLOCK_AFTER`). **Shells** (car bodies) and shell-specific **graphics/liveries** are cosmetic only: crew bosses' signature shells come only from crew boss betting races at the promoter's subsea Wangan parking-area home base, while **substories** each award cash (through Sabine's normal debt cut while open), a free skewed-sidegrade mod straight to the garage stash (never aero), a shell-specific livery (Round 1–2 liveries target the starter shell or an already earned substory shell; later ones can tease locked shells), or—for a few standout substories—an oddball shell (canon 26, 28).
> - **XP → levels → skill points (2026-11-09):** skill points come only from car levels; levels come from XP earned in story wins and **grind races** (repeatable races between story characters). The **level cap** equals the 80 % SP cap (`SP_CAP_FRACTION`) and rises with each story win; XP past the cap is lost. SP per level rises as levels go up, and each level costs more XP (`sp_per_level`, `xp_to_next`). Grind-race XP pays proportionally less further up each crew's ladder and at higher levels (per-crew taper: `grind_payout_fraction`, `TAPER_*`). Crew boss wins pay XP (so SP), money, a shell and a graphic; mods are bought only (see the canon 28 conflict above). Model: grind v8c (0c90c9c). See 07 §8 and `sim/velocity_shift/progression.py`.
> - **Respec:** moving locked skill points (Jesse) or retuning aero (the tunnel) costs money and is capped per visit. **After the rift (Austin, 2026-11-11; canon in story/):** after the Mentor Confrontation Jesse stops respecs and tuning for the PC; both move to the speakeasy with Malo.
> - **Shop after the rift (Austin, 2026-11-11):** Wholesale ends at the Mentor Confrontation; Reiko returns to full price but keeps selling through the Finale. **Big mods (Austin, 2026-11-10):** finishing Round 3 unlocks the big Finale mods, bought from Reiko at full price.
> - **DAQ log (Austin, 2026-11-11):** Jesse's logger keeps only the last race and plays it back as a per-corner list of the PC's and the opponent's lines; after the rift the PC pulls it up alone. UI is Gordon's.
> - **Finale order (Austin, 2026-11-12):** Myth Driver races run in fixed order: Touge #1, Wangan #2, Street #3.
> - **Tracks (Austin, 2026-11-12):** 3 tracks per district, 9 in total. Every track is exactly 10 turns per lap. 20- and 30-turn races are 2 and 3 laps of the same track. Each district has a few signature corners where every racer in the district runs the same standard line and bluff; on other corners wild racers share one line and bluff and each named character has their own style (which corners and lines: pending, sim paused on Austin's call).
> - **Art (Arthur):** locked art rules live in `design/art/art_direction.md` (approved items marked MUST/APPROVED with dates).
> - **Build (Godot), approved by Austin:** development is **Godot 4.6.3 only**, with no Three.js build (2026-11-11). **Combat freeze (2026-11-10):** no Godot combat work except the two-corner engine test, which uses provisional numbers and lives in `unapproved/gordon/two-corner/`. **Exit→Entry lockout** rule deleted (2026-11-08). **Render (2026-11-11):** the 3D scene is 640×480 with no antialiasing, scaled up by whole numbers with nearest-neighbour; HUD text is drawn sharp on a 1280×960 grid (art rule B.5c in `design/art/art_direction.md`). **QTE (2026-11-11):** difficulty scales only through the visible zone width (`qte_zone_width` at the race's fixed r in `sim/`); the old level-gap `qte_difficulty()` scaling is dropped. Each turn has three QTEs (Entry, Apex, Exit); an unplayed QTE scores 0. **⚠ Open:** Austin asked for each QTE to feed its own clash, but the sim (f0efecf) averages the three into one score that every clash uses, and so does the build; this needs Austin's call. **Turn flow (2026-11-11, 2026-11-12):** line select and playback never pause; the only pause is a timed Enter-to-continue after a turn completes. The player picks Entry, then Apex and Exit at static camera stops; the three QTEs play during playback, each on its own timer, with the cars held in that phase and the road scrolling while it runs. Passes are shown during play: if both cars share the exit lane, the passer moves to an open lane for the pass, with no clipping. **Public demo:** Austin updates nodestar.tech himself.
> - **Places:** Jesse (the Tuner) and Reiko (parts) work out of **Sabine's garage**; the **speakeasy** is the barkeep Malo's bar (named 2026-11-11) with the hidden wind tunnel.
> - **Level bands** in 04 (Starter … Legend) are stat-budget labels, not race tiers.

A turn-based racing combat engine. Two combatants race a 10-turn lap (1–3 laps). Each turn the player picks a 3-stance line (entry, apex, exit) from a stat-weighted hand, the opponent draws a whole district line, and each of the 3 clashes adds Phi/tau progress; the higher progress total wins. The locked rules are in the canon block above; equations and constants are in `design/02-equations-reference.md` and `sim/velocity_shift/equations.py`.

---

## Architecture

```
sim/main.py
  └─> velocity_shift/
        ├─> cli.py          — Interactive match setup, prompts, display, run_cli
        ├─> models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
        ├─> equations.py    — Pure math and all constants: QTE zone, clash progress, kappa, line sets, progression
        ├─> deck.py         — 192-card shoe (legacy HP/DP path only; live hands are drawn per turn)
        ├─> combat.py       — resolve_turn (Phi/tau progress), pick_line, resolve_turn_legacy
        ├─> match.py        — run_match, multi-turn loop, progress-total winner
        ├─> ai.py           — Opponent card selection strategies + QTE generation
        ├─> trace.py        — Structured execution logger
        ├─> simulation.py   — Batch runner for statistical analysis
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
| `sim/velocity_shift/deck.py` | Deck class — construction, draw, discard lifecycle (legacy HP/DP path; the live engine uses `combat.draw_weighted_hand`) |
| `sim/velocity_shift/combat.py` | Turn resolution orchestration + clash/battle logic |
| `sim/velocity_shift/match.py` | Multi-turn match loop with callbacks |
| `sim/velocity_shift/ai.py` | AI card selection strategies + QTE generation |
| `sim/velocity_shift/trace.py` | Structured execution logger |
| `sim/velocity_shift/simulation.py` | Headless batch runner + result export |
| `sim/velocity_shift/progression.py` | Story ladder (budgets, level caps, story/grind XP, walls) over the N=4000 win-rate table `sim/config/winrate_n4000.json`; report via `sim/scripts/run_progression.py` |
| `sim/velocity_shift/cli.py` | Interactive frontend (setup, prompts, display, entry point) |
| `sim/velocity_shift/config.py` | Factory function for archetype-based builds |

---

## Live combat model (one turn)

Superseded text removed 2026-11-12: the HP/DP data flow, `HP_PER_LEVEL` / `QTE_NORMALIZER` normalization, level-gap difficulty ratios, the persistent 192-card deck loop and the position (DP / max HP) win decision described the legacy path (`resolve_turn_legacy`, `MatchConfig.legacy_hp_dp`), not the live sim. The canon block wins; this is a map, not a second spec.

```
draw_weighted_hand (HAND_SIZE, DECK_ALPHA; fresh each turn)
        │
Player locks a line: entry / apex / exit stances
Opponent: pick_line from LINE_SET_C[district][corner] (LINE_ADHERENCE, LINE_ALT_WEIGHTS)
Player QTE: entry/apex/exit phases → mean_phase_qte (unplayed = PHASE_QTE_UNPLAYED)
        │      zone width = qte_zone_width(r, qte_window_mod); opponent uses OPPONENT_QTE
        ▼
clash_progress x3: g = V × Φ(outcome, q_eff) × M,  V = r**kappa_for_length(max_turns)
        │      q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)
        ▼
progress totals accumulate; after max_turns the higher total wins
(an exact tie is recorded as "Tie"; how a tie reads in game is not decided)
```

- **Stats:** POW / EN / HAN set the hand's stance weights; the stat gap is the ratio r (opponent / player), which sets both `V` and the visible QTE zone.
- **Difficulty:** set by r per rung (`LADDER_R`, the target r at each rung's level cap) and by race length (`KAPPA_BY_LENGTH`), not by level-gap ratios or per-encounter knobs.
- **Progression:** levels, caps, grind walls and the mod tier floor live in `sim/velocity_shift/progression.py`; see 07 §6 and §8.
- **Global knobs:** every game constant is a named module-level value in `sim/velocity_shift/equations.py`; docs cite names, not copied values. Seeded RNG keeps runs reproducible.
