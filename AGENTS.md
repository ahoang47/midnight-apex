# Midnight Apex — AGENTS.md

One file for the whole repo. Read it before touching anything.

## Repo rules (all agents)

- **Never `git push`.** Not without an explicit instruction from the lead for that push.
- **Commit only when explicitly asked.**
- **Read `CHANGELOG.md` before planning or executing a change**, to avoid repeating past mistakes.
- **Log every change in `CHANGELOG.md`** with what changed and the reasoning. Newest entry at the top. Tag the entry with the area (`[sim]`, `[design]`, `[story]`, `[art]`, `[godot]`, `[repo]`) and the owner bot.
- **`sim/` code is the source of truth for numbers.** Docs in `design/` (and anywhere else) reference the constant by name and file (e.g. `HP_PER_LEVEL` in `sim/velocity_shift/equations.py`) instead of copying values. If a doc and the code disagree, the code wins until the systems owner changes it on purpose.
- **Everything in the game world is an authored asset, not generated in code** (Austin 2026-11-20). Terrain, hillsides, cliff and cut faces, lots, galleries, buildings and roadside dressing are built as assets (Arthur, `art/` -> `assets/`) and placed in scenes. Godot scripts load and place assets and run gameplay; they don't build world geometry procedurally. The one exception is the road surface, which stays generated in code from the course spec; assets are modelled against Gordon's road export. Keep anything generated in code to the bare minimum: generated geometry is harder to see and fix, and it costs frame time. If something seems to need generated geometry, raise it with Austin and Arthur first.
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

- Godot 4.6.3, **GL Compatibility** renderer (switched from Mobile 2026-11-19 for the mobile web export), Jolt Physics 3D, Direct3D 12 on Windows. GDScript only (no Mono/C#). Blender import is off (`filesystem/import/blender/enabled=false`) so the `.blend` sources in `art/` don't block a headless import.
- Git: `touge-race` is the working branch for all new commits (Austin 2026-11-14: build a full 10-turn Touge race end to end, no mods, stats in the parity range, focused on art and player experience). `master` holds the merged history (`proto-build` merged and deleted). Pull with rebase, never force-push; remote `github.com/ahoang47/midnight-apex.git`.
- `.gitignore` covers `.godot/`, `/android/`, `/.pin/` (pinned sim checkout for the parity tools) and `/.out/` (tool output and the web export).
- The root project is Gordon's two-corner engine test, promoted from `unapproved/gordon/two-corner/godot/` on 2026-11-19 (Austin). Main scene `scenes/main.tscn` (menu → two Touge corners → finish screen), drawn at 640×480 internal and upscaled to a 1280×960 window.
  - `scenes/`: `main.tscn` plus sub-scenes `camera_rig`, `car`, `hud`, `sky`, `track`, `touge_dressing`.
  - `scripts/`: `race_core.gd` (race state, RNG, TC3 state token), `combat.gd` and `sim_constants.gd` (generated from the pinned sim; do not hand-edit), `py_random.gd` (exact CPython MT19937 port), `main.gd` (flow, cameras, input), `hud.gd` + `hud/` (one script per HUD widget), track/road/sky/dressing/car scripts, `headless_run.gd` (headless parity runner).
  - `shaders/` (car, env, sky, glow, post, chevron, scroll, fx), `fonts/` (HUD fonts + licences), `spec/` (`race_config.json`, display-only `display.json`, `constants.json`, `build.json`, scripted test inputs), `export_presets.cfg` (Web).
  - Stand-in textures live at `assets/tex/` (`kit/` HUD/env stand-ins, `cars/` env maps, road/verge/barrier). Cars are Arthur's `assets/cars/<car>/car_<car>.glb`.
  - Tests: `tools/two_corner/run_parity.sh` (QTE function bits, Godot vs pinned sim, dump/load, restart test, key test) needs a sim checkout at the pin in `.pin/` (or `TWO_CORNER_PIN=`). Details: `design/godot-build-guide.md` Appendix I.
- The GDScript ports the Python model in `sim/velocity_shift/`. Tune in `sim/` first, then regenerate `scripts/sim_constants.gd` with `tools/two_corner/gen_constants.py` from the pinned sim.
- No Godot CI job yet (Gordon adds one when the Touge race build lands); no lint config.

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
    heat.py         — Heat/load gauges (POW engine, HAN suspension, EN brakes), calibration, boss heat rule
    combat.py       — resolve_turn, resolve_battle, battle_winner
    match.py        — run_match, multi-turn loop under heat gauges, progress-total decision
    ai.py           — Encounter laps/phases (+ legacy AI QTE)
    trace.py        — Execution trace logger
    simulation.py   — Headless batch runner for statistical analysis
    cars.py         — Archetype stat progression
  config/sample_builds.json — Preset player builds (opponents generated at runtime)
  tests/, scripts/
```

All game-rule constants are module-level names in `equations.py` — tunable in one place, never per-encounter. The card draw was removed 2026-11-13 (heat/load system).

### Gotchas

- No pytest installed by default; `python -c` is the primary runner. No CI, lint, or typecheck.
- `config/sample_builds.json` holds player builds only; opponents are generated from archetype + level.
- Stats (POW, EN, HAN) have no upper bound; floor is 0.
- Mods infrastructure was removed in a prior simplification.
- Stances are the `Stance` enum; there is no `Card` class or deck (removed 2026-11-13). Each clash the player picks a stance whose heat gauge is not locked (`heat.HeatGauges`).
- Win condition: after `max_turns`, the higher Phi/tau progress total wins (exact tie recorded as "Tie").
- Difficulty: stat ratio r (`LADDER_R`), race length (`kappa_for_length`) and the heat gauges; targets checked by `scripts/balance_gauntlet.py`.
- Opponents play their district line (`LINE_SET_C`) under the boss heat rule; the personality card AI was removed 2026-11-13.
