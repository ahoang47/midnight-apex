# Changelog

> Session journal tracking changes, decisions, and reversions. Read before making architectural changes to avoid repeating past mistakes.

---

## 2026-07-07 — Initial setup

- Created `AGENTS.md` combining midnight-apex project context with velocity-shift reference. Key directives: no auto-push, changelog maintenance, velocity-shift as prototype reference.
- Created `overview/changelog.md` for change tracking.

## 2026-07-07 — velocity-shift copied into repo as reference

- Copied entire `velocity-shift/` project into midnight-apex root (minus `.git/` and `__pycache__/`) so all prototype reference material is local.
- Updated `AGENTS.md` intro path from absolute `C:\...` to relative `velocity-shift/`.

## 2026-07-07 — Full 15-step Godot prototype build

Built the complete Godot prototype per `velocity-shift/overview/godot_prototype.md`. 27 scripts + 1 scene + project config.

**Project config:**
- Display: 640×480, viewport stretch, keep aspect
- Input maps: `qte_mash` (Space/X), `qte_timing` (Enter/Z), `ui_accept`, `ui_cancel`

**Phase 1 — Foundation (Steps 1–4):**
- `scripts/globals.gd` — enums, constants (CLASH_STAKES=0.35, DECK_SIZE=192, etc.), lockout lookup
- `scripts/SignalBus.gd` — 12 signals
- `scripts/CombatantStats.gd` — Resource: name, pow, en, han, level
- `scripts/MatchConfig.gd` — Resource: player/opponent stats, max_turns, seed, etc.
- `scenes/Battle.tscn` — Full hierarchy: SubViewport (World3D), CanvasLayer (UI), TurnManager
- `scripts/Deck.gd` — 192-card stat-proportional deck with ALPHA=0.85 smoothing
- `scripts/StraightTimer.gd` — 12s countdown, 3×4s phases, signal on timeout
- `scripts/CardHandUI.gd` — 3 stance buttons, count display, lockout, auto-pick

**Phase 2 — Core Combat Loop (Steps 5–7):**
- `scripts/CombatResolver.gd` — All pure combat math: resolve_stance, clash_mult, compute_damage, mitigation, qte_factor, HAN mod, rubber-band split
- `scripts/TurnManager.gd` — State machine: START→STRAIGHT→CORNER_PLAYBACK→DAMAGE_BATCH→END_TURN→MATCH_COMPLETE, full data flow
- `scripts/QTEController.gd` — Mash (fill bar with depletion) + Timing (oscillating marker) QTE modes, difficulty scaling

**Phase 3 — AI + Tell System (Steps 8–9):**
- `scripts/AIPicker.gd` — EV-scoring card selection, 6 behavior overrides (highest_ev, counter, alternate, repeat_win, etc.)
- `scripts/AIQTE.gd` — Opponent QTE generation with encounter ratio scaling
- `scripts/TurnTypeData.gd` — 8 turn types × 3 archetypes stance sequence tables + QTE type lookup + bluff tables
- `scripts/ArchetypeData.gd` — Meta-archetype mapping, face type, comfort/weak turn zones
- `scripts/PersonalityData.gd` — 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) with 3 phases each
- `scripts/TrackData.gd` — 3 preset circuit layouts (10-turn sequences)
- `scripts/TellGenerator.gd` — Deception flow: lie rate, position weighting, intensity, comfort/weak scaling
- `scripts/FaceController.gd` — Face display with alpha crossfade, tell overlay

**Phase 4 — Display + Animation (Steps 10–12):**
- `scripts/PositionTracker.gd` — Cumulative DP, gap, rubber-band threshold
- `scripts/DamageDisplay.gd` — DP bar tweens
- `scripts/ClashDisplay.gd` — 2×3 stance grid with color-coded panels
- `scripts/PhaseAnnouncer.gd` — Lap boundary overlay
- `scripts/CarAnimator.gd` — Z-offset by DP gap, surge/drop, corner path blank
- `scripts/AnimationTreeBlendManager.gd` — Stance blend schedule (0-4-8-12s)
- `scripts/BattleCamera.gd` — Chase cam, corner transitions, overtake swing

**Phase 5 — Scene Management (Steps 13–14):**
- `scripts/StageManager.gd` — Scene loading (Battle.tscn) with auto-MatchConfig wiring
- `scripts/RoadScroller.gd` — UV-offset parallax shader material

## 2026-07-07 — Fixed Battle.tscn loading error + missing class_names

- `scenes/Battle.tscn` — Fixed `load_steps=2` → `load_steps=6` in scene header. The value was too low (2 instead of 6: 1 scene + 2 ext_resources + 3 sub_resources), causing Godot's parser to choke when encountering all 5 resource entries before node data.
- `scripts/StraightTimer.gd` — Added `class_name StraightTimer` so GDScript can resolve the type in `TurnManager.gd:32` (`straight_timer: StraightTimer`).
- `scripts/CardHandUI.gd` — Added `class_name CardHandUI` so GDScript can resolve the type in `TurnManager.gd:33` (`card_hand_ui: CardHandUI`).
- `scripts/FaceController.gd` — Added `class_name FaceController` so GDScript can resolve the type hint.
- `scenes/Battle.tscn` — Added `FaceController` node (`res://scripts/FaceController.gd`) as child of root `Battle` node.
- `scripts/TurnManager.gd` — Changed static call `FaceController.set_face_sequence(...)` to instance call via `@onready var face_controller: FaceController = $FaceController`.
- `scenes/Battle.tscn` — Added `uid=` fields to `ext_resource` lines (needed in Godot 4.4+). Attached `StraightTimer.gd` to `CornerTimerBar` and `CardHandUI.gd` to `CanvasLayer` so their `@onready` paths resolve. Updated `load_steps` to 9.
- `scripts/RoadScroller.gd` — Changed `extends ShaderMaterial` → `extends Node` with `@export var material: ShaderMaterial`. `ShaderMaterial` (a `Resource`) has no `_process` or `get_tree()` — both are `Node` methods.

**User handoffs (still needed):**
- Register `globals.gd` and `SignalBus.gd` as autoloads in Project Settings
- Color PlayerCube (blue) and OpponentCube (red) materials in editor
- Position Camera3D at (0, 5, 8) looking at (0, 0, -5) — verify after scene import
- Resize ground plane to look like a narrow road lane
- Arrange UI panels so they don't obscure the 3D viewport
- Tune constants in `globals.gd` via playtesting (Step 15)

## 2026-10-31 — Art direction guide + S2000 reference car restored after art-box data loss (Arthur, Art Director)

- `velocity-shift/overview/art_direction.md` — **restored (reconstructed)** v2 draft of the game-wide art guide. Part A is the binding vehicle standard; Part B is [VIBE]/[PROPOSAL] scene guidance; Part C has naming, open questions Q1–Q9 and doc conflicts K1–K7; Appendix W is the S2000 worked example.
- `art/` — new source-art tree. `art/vehicles/s2000/` holds the S2000 reference car (build scripts, textures, `.glb/.blend/.obj/.fbx`, blueprint refs, IoU overlays, key renders, README). `art/mood/tokyo_v2/` holds the Tokyo v2 vibe-check scene scripts and small previews (generated files git-ignored).

**Reasoning:** the original guide (written 2026-10-30/31, never committed) and all S2000 work lived only on the art box's `/workspace`, which was wiped when the box moved to a fresh instance (2026-10-31 ~11:31 AM PT; restore step reported "store empty; first boot"). The lead asked to restore the S2000 and the rules and to push finished art to the repo so it can't be lost again.

**Recovery detail:**
- S2000: recovered **verbatim** from the last zip sent in chat (scripts, textures, exports, references). Re-running the scripts reproduces it pixel-identically (4,354 tris; IoU side .961 / top .992 / front .925 / rear .944). Hard-coded `/workspace/s2000` paths were made relative for the repo copy.
- Art guide: **reconstructed** from the approved skill text, the chat record and the surviving style-reference sheet; structure and every binding rule match v2, wording and the Touge/Wangan palette/fog numbers are re-proposed. Two rules from the BRZ build were added and flagged as pending lead review (photo check of window/roof/hood/wheel lines beyond IoU; clay-stage shape sign-off).
- Tokyo v2 scene: scripts **rebuilt** from the recipe (originals lost); the approved original frames survive at `art/mood/tokyo_v2/renders/original_800/`.

**Earlier entries lost with the box (summarised):** 2026-10-31 — first art guide written (general, not S2000-specific, after context from Desmond); later the same day reorganised so the car rules are the only binding standard and all scene content is mood reference ("The key rules are for the cars only. The scene will likely not make it to the game.").

