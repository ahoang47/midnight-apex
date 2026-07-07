# Velocity Shift — System Overview

A turn-based racing combat engine. Two combatants race. Each turn they select cards from a stat-proportional deck, resolve 3 rock-paper-scissors clashes, compute damage from a pure multiplicative formula, and track cumulative damage for position.

---

## Architecture

```
main.py
  └─> velocity_shift/
        ├─> cli.py          — Interactive match setup, prompts, display, run_cli
        ├─> models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
        ├─> equations.py    — Pure math: qte, clash, damage, mitigation, stance resolution
        ├─> deck.py         — Deck construction, draw/reset (36-card stat-proportional)
        ├─> combat.py       — resolve_turn, resolve_battle, battle_winner
        ├─> match.py        — run_match, multi-turn loop, position decision
        ├─> ai.py           — Opponent card selection strategies + QTE generation
        ├─> trace.py        — Structured execution logger
        ├─> simulation.py   — Batch runner for statistical analysis
        └─> config.py       — build_from_archetype factory
  └─> config/
        └─> sample_builds.json  — Preset player builds
  └─> overview/                — Design docs (keep in sync if variables change)
```

### Package boundaries

| File | Role |
|------|------|
| `velocity_shift/models.py` | All data classes and enums — no logic |
| `velocity_shift/equations.py` | Pure functions — no state, no side effects. All game constants as module-level names in equations.py — tunable in one place |
| `velocity_shift/deck.py` | Deck class — construction, draw, discard lifecycle |
| `velocity_shift/combat.py` | Turn resolution orchestration + clash/battle logic |
| `velocity_shift/match.py` | Multi-turn match loop with callbacks |
| `velocity_shift/ai.py` | AI card selection strategies + QTE generation |
| `velocity_shift/trace.py` | Structured execution logger |
| `velocity_shift/simulation.py` | Headless batch runner + result export |
| `velocity_shift/cli.py` | Interactive frontend (setup, prompts, display, entry point) |
| `velocity_shift/config.py` | Factory function for archetype-based builds |

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

- **36 cards** per combatant, built proportionally from POW, EN, HAN
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
9. **Exit→Entry lockout** — The exit stance in turn N can block specific entry stances in turn N+1 based on the turn-type pair. Both sides are affected cross-turn only.
