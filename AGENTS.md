# Midnight Apex

Godot 4.6.3 Mobile project. Jolt Physics 3D, mobile renderer, Direct3D 12 on Windows.

- **Scripting:** GDScript (no Mono/C#)
- **Git:** `proto-build` branch, remote origin at `github.com/ahoang47/midnight-apex.git`  
  → Do NOT automatically push. Only commit when explicitly asked. Never `git push` without explicit instruction.
- **.gitignore** already covers `.godot/` and `/android/` — no need to update
- **No tests, CI, or lint config** exist yet
- **27 scripts + 1 scene** exist — full prototype build per `velocity-shift/overview/godot_prototype.md`
- **User handoffs:** Register `globals.gd` and `SignalBus.gd` as autoloads in Project Settings; color cubes, position camera, arrange UI in editor

## Reference: velocity-shift (prototype)

Game logic is prototyped in `velocity-shift/`. This project is a GDScript rewrite of that Python prototype.

- **Build plan:** `velocity-shift/overview/godot_prototype.md` — 15-step linear guide (bootstrap → deck → combat → AI → tells → animation → tuning)
- **Design docs:** `velocity-shift/overview/` — equations, deck/clash mechanics, difficulty tuning, skill trees, pattern read
- **Reference code:** `velocity-shift/velocity_shift/` — Python implementation of all game rules (equations, deck, combat, match, AI)
- **Tests:** `velocity-shift/tests/` — run via `python -c` to verify equation outputs

## Changelog directive

Whenever a change is requested and executed, the change + reasoning must be added to `overview/changelog.md`. Before planning or executing a change, read `overview/changelog.md` to avoid repeating past mistakes. If `overview/changelog.md` doesn't exist yet, create it.
