# Velocity Shift — AGENTS.md

> **Git directive:** Do NOT automatically push to git. Only commit when explicitly asked. Never use `git push`.

> **Changelog directive:** Whenever a change is requested and executed, the change + reasoning must be added to `overview/changelog.md`. Before planning or executing a change, read `overview/changelog.md` to avoid repeating past mistakes.

## Quick start

```bash
python -c "
import sys; sys.path.insert(0, '.')
from tests.test_equations import *; from tests.test_systems import *
"
```

**No dependencies.** Pure Python 3.10+ stdlib only.

## Running tests

Tests are plain functions with `assert` statements:
- `tests/test_equations.py` — 9 unit tests for all equation modules
- `tests/test_systems.py` — 5 integration tests for combat/match flow
- `tests/test_cars.py` — 8 tests for archetype progression

Run via `python -c` calling each `test_*()` function, or install pytest.

## Key architecture

```
main.py
  └─> velocity_shift/
        ├─> cli.py          — Interactive match setup, prompts, display, run_cli
        ├─> models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
        ├─> equations.py    — Pure math: qte, clash, damage, mitigation, stance resolution
        ├─> deck.py         — Deck construction, draw/reset (192-card stat-proportional)
        ├─> combat.py       — resolve_turn, resolve_battle, battle_winner
        ├─> match.py        — run_match, multi-turn loop, position-based decision
        ├─> ai.py           — Opponent card selection strategies + QTE generation
        ├─> trace.py        — Execution trace logger
        ├─> simulation.py   — Headless batch runner for statistical analysis
        └─> cars.py         — Archetype stat progression
  └─> config/
        └─> sample_builds.json  — Preset player builds (opponents generated at runtime)
  └─> overview/                 — Design docs (keep in sync if variables change)
```

All game-rule constants are module-level names in `equations.py` — tunable in one place, never per-encounter.

## Gotchas

- **No pytest installed** by default. Tests are assertion-based with no framework imports.
- **No CI, lint, or typecheck.** `python -c` is the primary test runner.
- **`config/sample_builds.json`** contains player builds only; opponents are generated at runtime from archetype + level.
- **Stats (POW, EN, HAN) have no upper bound**, floor is 0.
- **Mods infrastructure was removed** in a prior simplification.
- **Card type is `Stance`** (enum), not a `Card` class. `Deck.draw()` returns `list[Card]`.
- **DECK_SIZE = 192** (not 36), built from stat proportions with smoothing alpha=0.85.
- **Win condition:** after `max_turns`, winner is higher position (opponent DP / player_max_hp vs player DP / opponent_max_hp). Tie = opponent wins.
- **Difficulty** is driven only by the level gap (Wild=0.35x, Lieutenant=0.75x, Boss=1.15x).
- **6 AI personalities**, each with 3 phase-indexed behavior phases (up to 156 unique opponents).
