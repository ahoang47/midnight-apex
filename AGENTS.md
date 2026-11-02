# Midnight Apex — AGENTS.md

One file for the whole repo. Read it before touching anything.

## Repo rules (all agents)

- **Never `git push`.** Not without an explicit instruction from the lead for that push.
- **Commit only when explicitly asked.**
- **Read `CHANGELOG.md` before planning or executing a change**, to avoid repeating past mistakes.
- **Log every change in `CHANGELOG.md`** with what changed and the reasoning. Newest entry at the top. Tag the entry with the area (`[sim]`, `[design]`, `[story]`, `[art]`, `[godot]`, `[repo]`) and the owner bot.
- **`sim/` code is the source of truth for numbers.** Docs in `design/` (and anywhere else) reference the constant by name and file (e.g. `HP_PER_LEVEL` in `sim/velocity_shift/equations.py`) instead of copying values. If a doc and the code disagree, the code wins until the systems owner changes it on purpose.
- **Stay in your folder.** Changes outside the folders you own go through the owner (or Desmond).

## Folder map and owners

| Path | What lives there | Owner |
|------|------------------|-------|
| `project.godot`, `scenes/`, `scripts/`, `icon.*` | Godot project (root) | Lead (playtests); Barry ports tuned values from `sim/` |
| `sim/` | Python math model: the text-based prototype, tests, balance scripts, presets | **Barry** (Systems & Balance) |
| `design/` | Systems docs `01`–`06`, `godot-build-guide.md`, `sample_battle_screen.html`, `notes/` (lead's notes + mod notes) | **Barry** (Systems & Balance) |
| `design/art/` | Art direction guide (`art_direction.md`) | **Arthur** (Art Director) |
| `assets/` | Game-ready art for Godot: `cars/`, `characters/`, `env/`, `faces/`, `ui/`, `fonts/` | **Arthur** (Art Director) |
| `art/` | Source art (Blender builds, blueprints, mood scenes) | **Arthur** (Art Director) |
| `story/` | `pitch.md`, `plot.md`, `barks.md`, `characters/` (index, Sabine, Myth Drivers) | **Nathaniel** (Narrative), guided by the lead |
| `AGENTS.md`, `CHANGELOG.md`, cross-folder work | Coordination | **Desmond** (Chief of Design) |

Nathaniel flags anything that touches mechanics (archetype, lie rate, turn-type preferences) to Barry. Barry flags any stance/UI naming that affects art to Arthur.

`sim/`, `design/` and `story/` each contain an empty `.gdignore` so Godot does not import them.

## Godot project

- Godot 4.6.3, Mobile renderer, Jolt Physics 3D, Direct3D 12 on Windows. GDScript only (no Mono/C#).
- Git: `proto-build` is the working branch; remote `github.com/ahoang47/midnight-apex.git`.
- `.gitignore` covers `.godot/` and `/android/`.
- 27 scripts + 1 scene (`scenes/Battle.tscn`): the full prototype built per `design/godot-build-guide.md` (15-step guide: bootstrap → deck → combat → AI → tells → animation → tuning).
- The GDScript is a port of the Python model in `sim/velocity_shift/`. Tune in `sim/` first, then port the settled values to `scripts/globals.gd` and friends.
- User handoffs: register `globals.gd` and `SignalBus.gd` as autoloads in Project Settings; colour cubes, position camera, arrange UI in the editor.
- No Godot tests, CI, or lint config yet.

## Sim (`sim/`) — Python math model

**No dependencies.** Pure Python 3.10+ stdlib. Run everything **from `sim/`** (scripts use `sys.path.insert(0, ".")` and `config/...` relative paths).

```bash
cd sim
python -c "
import sys; sys.path.insert(0, '.')
import tests.test_equations as e, tests.test_systems as s, tests.test_cars as c
for m in (e, s, c):
    for n, f in vars(m).items():
        if n.startswith('test_') and callable(f): f(); print('PASS', n)
"
```

Tests are plain functions with `assert` statements (or install pytest; `pyproject.toml` points it at `tests/`):
- `tests/test_equations.py` — 9 unit tests for the equation modules
- `tests/test_systems.py` — 5 integration tests for combat/match flow
- `tests/test_cars.py` — 8 tests for archetype progression

Other entry points (from `sim/`): `python main.py` (interactive CLI), `python scripts/balance_gauntlet.py`, `python scripts/design_opponent.py --help`, `python scripts/generate_build_matrix.py` (**overwrites** `config/sample_builds.json`).

### Architecture

```
sim/
  main.py
  velocity_shift/
    cli.py          — Interactive match setup, prompts, display, run_cli
    models.py       — Data classes: Stance, CombatantStats, TurnState, MatchConfig, etc.
    equations.py    — Pure math + ALL game-rule constants (module-level names)
    deck.py         — Deck construction, draw/reset (DECK_SIZE = 192, stat-proportional)
    combat.py       — resolve_turn, resolve_battle, battle_winner
    match.py        — run_match, multi-turn loop, position-based decision
    ai.py           — Opponent card selection strategies + QTE generation
    trace.py        — Execution trace logger
    simulation.py   — Headless batch runner for statistical analysis
    cars.py         — Archetype stat progression
  config/sample_builds.json — Preset player builds (opponents generated at runtime)
  tests/, scripts/
```

All game-rule constants are module-level names in `equations.py` (deck size/alpha in `deck.py`) — tunable in one place, never per-encounter.

### Gotchas

- No pytest installed by default; `python -c` is the primary runner. No CI, lint, or typecheck.
- `config/sample_builds.json` holds player builds only; opponents are generated from archetype + level.
- Stats (POW, EN, HAN) have no upper bound; floor is 0.
- Mods infrastructure was removed in a prior simplification.
- Card type is `Stance` (enum), not a `Card` class. `Deck.draw()` returns `list[Card]`.
- `DECK_SIZE = 192` (not 36), built from stat proportions with smoothing alpha = 0.85.
- Win condition: after `max_turns`, the higher position wins (opponent DP / player_max_hp vs player DP / opponent_max_hp). Tie = opponent wins.
- Difficulty is driven only by the level gap (Wild 0.35×, Lieutenant 0.75×, Boss 1.15×).
- 6 AI personalities, each with 3 phase-indexed behaviours (up to 156 unique opponents).
