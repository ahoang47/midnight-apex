# Midnight Apex — System Overview

> **Design canon: locked terms and decisions (2026-11-04; designated design canon by Austin 2026-11-12).** This block is the source of truth for Austin's mechanical and scope decisions; if any other design/ file disagrees, this block wins. Add a decision here only once Austin has approved it, with its date; unapproved proposals go in `unapproved/<owner>/`. Use these terms everywhere in design/. The game is **Midnight Apex**; the sim lives in `sim/` (Python package `sim/velocity_shift/`, named after the engine's old working title).
> - **Race tiers:** **wild race** (open-world pushover for EXP farming; code `wild`), **betting race** (any wild race turned into a bet through a prompt, harder than wild and a bit easier than lieutenants; never awards shells), **lieutenant** (crew members; code `lieutenant`), **crew boss** (the crew's chief; code `boss`), **Myth Driver race** (Finale story races; like wild races, no loss persistence). "Lackey", "crew chief", "Lieutenant Challenge" and "encounter" are informal synonyms; prefer the terms above.
> - **Crew ladder:** every round the PC runs each whole crew in order: kids, then mature members, then old heads (all lieutenants), then the crew boss. Between rounds the boss levels up the whole crew. **Crew order is free (Austin, 2026-11-10):** within a round the PC may challenge the three district crews in any order, but is locked into a crew once started until its boss is beaten; rounds stay gated (all three bosses before the next round). Budgets and cap raises are keyed by **play position**, not district: the first crew the PC challenges in Round 2 / Round 3 is the **round-opening crew** (`OPTION_A_ROUND_STEP`, `CAP_ALLOC_ROUND_OPEN`), the rest step by `OPTION_A_CREW_STEP` (`DISTRICTS`, `DEFAULT_CREW_ORDER` in `sim/velocity_shift/equations.py`; the default order is only an example for reports and tests). All 216 legal orders give the same walls and totals (`python scripts/run_progression.py --all-orders`).
> - **Reputation:** the in-world reason crews take you on. It's lore only, not a tracked stat, and it's never called "street cred" or "rep".
> - **Persistence:** loss persistence applies only to crew members (lieutenants) and crew bosses: if you lose to one of them, that driver remembers it in later barks and rematches (canon 27). Wild races and Myth Driver races don't have loss persistence. Scripted race 3 still has its own win gate to unlock mods (canon 19), and losing to a crew boss means a retry.
> - **Stats:** **POW** (Attack), **EN** (Defend), **HAN** (the third stance). The third stance is `NEUTRAL` in code; the player-facing name ("Steady" vs "Neutral") is still open (decision sheet, 02).
> - **Play quality:** two skills, **read** (`q_read`, countering the AI's real pick) and **timing** (`q_time`, hitting a perfect-10 **QTE**, the 1–10 timing input). `player_quality` sets both.
> - **Stat parity:** the ratio of opponent stats to player stats; 0.8–1.2 counts as parity. The story caps the player at 0.8 of the top unlocked crew boss's stats.
> - **Progression unlocks:** the first 3 races are scripted. **Mods** (parts bought once from Reiko at full price) unlock when the PC **wins race 3**, which also opens the world and **substories** (canon 19, 28). Beating story races up each crew's ladder (**lieutenants** as well as **crew bosses**) expands Reiko's paid shop stock, with crew bosses gating rare tier-jump mods (canon 28). **⚠ CONFLICT, pending Desmond's rewording of canon 28:** Austin decided on 2026-11-09 that mods are **bought only**; boss wins pay XP (levels, so some SP), money, a shell and a graphic, not rare mods. Canon 28 is not rewritten here; see 07 §5.2 and §8. **Wholesale** (Reiko's discount) unlocks at the end of Round 1. **Aero** (base boost plus a free point pool, tuned at the speakeasy's **wind tunnel**) unlocks when the **debt** to Sabine hits zero, early in Round 2 after the PC beats the first crew of the round (`DEBT_CLEAR_AFTER`). **Betting** unlocks at the end of Round 2 (`BETTING_UNLOCK_AFTER`); the finale opens after Round 3 (`FINALE_UNLOCK_AFTER`). **Shells** (car bodies) and shell-specific **graphics/liveries** are cosmetic only: crew bosses' signature shells come only from crew boss betting races at the promoter's subsea Wangan parking-area home base, while **substories** each award cash (through Sabine's normal debt cut while open), a free skewed-sidegrade mod straight to the garage stash (never aero), a shell-specific livery (Round 1–2 liveries target the starter shell or an already earned substory shell; later ones can tease locked shells), or—for a few standout substories—an oddball shell (canon 26, 28).
> - **XP → levels → skill points (2026-11-09):** skill points come only from car levels; levels come from XP earned in story wins and **grind races** (repeatable races between story characters). The **level cap** equals the 80 % SP cap and rises with each story win; XP past the cap is lost. See 07 §8 and `sim/velocity_shift/progression.py`.
> - **Respec:** moving locked skill points (Jesse) or retuning aero (the tunnel) costs money and is capped per visit. **After the rift (Austin, 2026-11-11; canon in story/):** after the Mentor Confrontation Jesse stops respecs and tuning for the PC; both move to the speakeasy with Malo.
> - **Shop after the rift (Austin, 2026-11-11):** Wholesale ends at the Mentor Confrontation; Reiko returns to full price but keeps selling through the Finale. **Big mods (Austin, 2026-11-10):** finishing Round 3 unlocks the big Finale mods, bought from Reiko at full price.
> - **DAQ log (Austin, 2026-11-11):** Jesse's logger keeps only the last race and plays it back as a per-corner list of the PC's and the opponent's lines; after the rift the PC pulls it up alone. UI is Gordon's.
> - **Finale order (Austin, 2026-11-12):** Myth Driver races run in fixed order: Touge #1, Wangan #2, Street #3.
> - **Tracks (Austin, 2026-11-12):** 3 tracks per district, 9 in total. Every track is exactly 10 turns per lap. 20- and 30-turn races are 2 and 3 laps of the same track. Each district has a few signature corners where every racer in the district runs the same standard line and bluff; on other corners wild racers share one line and bluff and each named character has their own style (which corners and lines: pending, sim paused on Austin's call).
> - **Art (Arthur):** locked art rules live in `design/art/art_direction.md` (approved items marked MUST/APPROVED with dates), incl. B.5c: 3D at 640×480 no AA → RGB555 + Bayer → 2× nearest; UI pixel-hard at 1280×960 (2026-11-11).
> - **Build (Godot), approved by Austin:** development is **Godot 4.6.3 only**, with no Three.js build (2026-11-11). **Combat freeze (2026-11-10):** no Godot combat work except the two-corner engine test, which uses provisional numbers and lives in `unapproved/gordon/two-corner/`. **Exit→Entry lockout** rule deleted (2026-11-08). **Render (2026-11-11):** the 3D scene is 640×480 with no antialiasing, scaled up by whole numbers with nearest-neighbour; HUD text is drawn sharp on a 1280×960 grid (art rule B.5c in `design/art/art_direction.md`). **QTE (2026-11-11):** difficulty scales only through the visible zone width (`qte_zone_width` at the race's fixed r in `sim/`); the old level-gap `qte_difficulty()` scaling is dropped. Each turn has three QTEs (Entry, Apex, Exit), each feeding its own clash; an unplayed QTE scores 0. **Turn flow (2026-11-11, 2026-11-12):** line select and playback never pause; the only pause is a timed Enter-to-continue after a turn completes. The player picks Entry, then Apex and Exit at static camera stops; the three QTEs play during playback, each on its own timer, with the cars held in that phase and the road scrolling while it runs. Passes are shown during play: if both cars share the exit lane, the passer moves to an open lane for the pass, with no clipping. **Public demo:** Austin updates nodestar.tech himself.
> - **Places:** Jesse (the Tuner) and Reiko (parts) work out of **Sabine's garage**; the **speakeasy** is the barkeep Malo's bar (named 2026-11-11) with the hidden wind tunnel.
> - **Level bands** in 04 (Starter … Legend) are stat-budget labels, not race tiers.

A turn-based racing combat engine. Two combatants race. Each turn they select cards from a stat-proportional deck, resolve 3 rock-paper-scissors clashes, compute damage from a pure multiplicative formula, and track cumulative damage for position.

---

## Architecture

```
sim/main.py
  └─> velocity_shift/
        ├─> cli.py          — Interactive match setup, prompts, display, run_cli
        ├─> models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
        ├─> equations.py    — Pure math: qte, clash, damage, mitigation, stance resolution
        ├─> deck.py         — Deck construction, draw/reset (192-card stat-proportional)
        ├─> combat.py       — resolve_turn, resolve_battle, battle_winner
        ├─> match.py        — run_match, multi-turn loop, position decision
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
| `sim/velocity_shift/deck.py` | Deck class — construction, draw, discard lifecycle |
| `sim/velocity_shift/combat.py` | Turn resolution orchestration + clash/battle logic |
| `sim/velocity_shift/match.py` | Multi-turn match loop with callbacks |
| `sim/velocity_shift/ai.py` | AI card selection strategies + QTE generation |
| `sim/velocity_shift/trace.py` | Structured execution logger |
| `sim/velocity_shift/simulation.py` | Headless batch runner + result export |
| `sim/velocity_shift/progression.py` | Story ladder (budgets, level caps, story/grind XP, walls) over the N=4000 win-rate table `sim/config/winrate_n4000.json`; report via `sim/scripts/run_progression.py` |
| `sim/velocity_shift/cli.py` | Interactive frontend (setup, prompts, display, entry point) |
| `sim/velocity_shift/config.py` | Factory function for archetype-based builds |

---

## Data Flow (one turn)

```
Deck.draw(6) ──> Card[6] hand
                      │
            Player picks 3 in order (lead / middle / anchor)
            Opponent AI picks 3
            Each gets a QTE score (1–10)
                      │
                      ▼
         resolve_stance() x3 ──> StanceOutcome[3]
                      │
                      ├──> battle_winner() ──> string label
                      ├──> sum(outcome_values) ──> battle_mult = 1 + BATTLE_BONUS × |sum|
                      │
                      ▼
         QTE rubber-band — who is leading?
           gap > 0  → leader: QTE→offense / trailer: QTE→defense
           gap < 0  → trailer: QTE→offense / leader: QTE→defense
           gap == 0 → both use QTE on offense & defense (symmetric)
                      │
                      ▼
          compute_damage() x3 ──> DP per clash
         (POW × damage_QTE_factor × clash_mult × battle_mult)
                      │
                      ├──> damage_mitigation() ──> mitigation_mult per side
                      │    (EN/1000 × MITIGATION_PER_1000 × defense_QTE_factor)
                      │
                      ▼
          DP_turn = average(DP_1, DP_2, DP_3) × opponent_mitigation_mult
```

---

## Core Combat Stats (0+, no upper bound)

| Stat | Role | Effect |
|------|------|--------|
| POW | Offensive power | Directly scales damage output |
| EN | Endurance | Mitigates incoming damage |
| HAN | Handling | Drives Neutral card weight in deck composition |
| QTE_score | Execution quality | Multiplier on damage and mitigation (1–10 scale) |

### Normalization

- `QTE_score / QTE_NORMALIZER (10)` → `QTE_factor` (0.1–1.0)
- `level × HP_PER_LEVEL (180)` → max_hp for each combatant

---

## Difficulty

Difficulty is driven entirely by the **level gap** between combatants.
There are no encounter tuning parameters.

| Encounter type | Opponent level ratio | ~Turns vs equal stats | Feel |
|---|---|---|---|
| Wild | 0.35× player | 3–5 | Dominate — opponent stat-poor |
| Lieutenant | 0.75× player | 10–12 | Pressure — near parity |
| Boss | 1.15× player | 12+ | Heat — opponent marginally stronger |

---

## Deck System

- **192 cards** per combatant, built proportionally from POW, EN, HAN
- POW → Attack card weight, EN → Defend card weight, HAN → Neutral card weight
- Smoothing term (`alpha=0.85`) prevents any single stance from overwhelming the deck
- **Draw 6** per turn, pick 3, discard 3
- **Infinite deck loop**: when draw pile < 6, reshuffle discard back in

---

## Win Condition

- **Decision:** after max_turns, the winner is the combatant with the higher position (opponent DP / player_max_hp vs player DP / opponent_max_hp)
- **Tie:** if positions are equal after max_turns, the opponent wins (the player needed to be ahead to win)

---

## Key Design Properties

1. **Pure multiplicative damage** — no gates, no interaction terms, no sigmoids
2. **Multi-clash per turn** — 3 independent RPS resolutions, averaged
3. **Battle bonus** — winning the battle amplifies all clash damage (`battle_mult = 1 + BATTLE_BONUS × |sum|`)
4. **EN-based mitigation** — higher EN reduces incoming damage, gated by QTE execution
5. **Position-based decision** — after max_turns, higher cumulative DP ratio wins
6. **Deterministic core** — seeded RNG, reproducible results
7. **Stat-to-stance mapping** — POW/EN/HAN directly drive deck card type proportions
8. **Global knobs** — all game constants are named module-level values in equations.py, never per-encounter
