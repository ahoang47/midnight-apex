# Changelog

> Session journal tracking overview doc updates. Add entries chronologically.

---

## 2026-10-31 — `art_direction.md` restored after data loss (reconstructed v2)

`overview/art_direction.md` re-added. The v2 draft was never committed and was lost when the art box was wiped (2026-10-31 ~11:31 AM PT). Rebuilt from the approved skill text, the chat record and the surviving Tokyo v2 style-reference sheet.

- **Part A — Vehicle standard [MUST]:** blueprint build + IoU gate (side/top ≥ 0.95, front/rear ≥ 0.92), ≤ 5k tris, painted 1024² body with baked AO, vector panel lines, 256² parts atlas, 512² fabric, RGB555 + Bayer textures, faked shine (ambient + one key + Blinn + painted env map, env ≤ 0.45), opaque cool-tinted glass, no interior/brakes/engine, made-up brands, review in the 640×480 reference frame, checklist, Godot shader sketch (untested).
- **Part B — [VIBE]/[PROPOSAL]:** what made Tokyo v2 work, its palette, district proposals, cameras, portraits/UI, engine notes, advisory scene checklist.
- **Part C:** naming and `art/` layout, open questions Q1–Q9, doc conflicts K1–K7. **Appendix W:** S2000 worked example.
- **New since v2 (flagged pending review):** A.1.3 photo check of window/roof/hood/wheel lines (IoU alone missed a too-tall BRZ body), A.1.4 clay-stage shape sign-off.
- Touge/Wangan palette and fog numbers are re-proposed (originals lost) and still need sign-off (Q2).

**Reasoning:** lead asked to restore the rules from the chat session and push finished art so it isn't lost again.

**Lost entries (summarised):** 2026-10-31 — `art_direction.md` created as the general game art guide (after context from Desmond); then reorganised so car rules come first and are the only binding standard, with all scene content relabelled [VIBE]/[PROPOSAL] and nothing deleted.

---

## 2026-07-07 — Human-centric tasks stripped from prototype doc

All 16 `🧑 You:` sections removed from `overview/godot_prototype.md` — autoload registration, editor setup, constant tuning, verification steps, and placeholder notes. The doc is now MCP-only; no tasks require manual editor intervention.

**Reasoning:** The `globals.gd`/`SignalBus.gd` autoload registration that was previously a human step is now handled by MCP via `project.godot`. Remaining tuning/verification steps are development workflow notes, not document-level tasks. Removing them keeps the doc focused on what MCP produces.

---

## 2026-07-06 — Godot docs merged into single prototype document

`overview/godot_outline.md` + `overview/godot_cube_prototype.md` → `overview/godot_prototype.md`

Merged the comprehensive reference outline and the step-by-step cube tutorial into a single 15-step linear document (1400+ lines). Old files deleted.

**Structural changes:**
- 15 sequential steps replace the previous 8-section outline / 10-step tutorial split
- Steps 1–4: Bootstrap, scene, deck, timer + card selection
- Steps 5–7: Combat math, turn manager, QTE
- Steps 8–9: AI layer, tell system (expanded from simplified tells to full face controller)
- Steps 10–14: Display, car animation, camera, corner cinematic, scene management
- Step 15: Tuning loop + deferred items
- Appendices A–H: file manifest, turn flow reference, signals, data flow, art checklist, QTE lookup/difficulty, AI stance lookup, gotchas

**🧑/🤖 split preserved** throughout. All detail from both sources carried forward (lockout, AnimationTree blend, FaceStack, BattleCamera, corner cinematic, RoadScroller, StageManager).

---

## 2026-07-06 — Exit→Entry lockout mechanic

`overview/03-deckbuilding-clash.md` — added Exit→Entry lockout section with 3 placeholder matrices (Attack / Defend / Steady exit), 8×8 turn-type cross-reference (all TBD except Chicane→Hairpin / Attack→Steady). Narrative justification for the Chicane→Hairpin example.

`overview/01-system-overview.md` — added key design property #9.

`overview/06-pattern-read.md` — updated exit paragraph to reference lockout.

`overview/godot_prototype.md` — lockout in CardHandUI (Step 4), TurnManager fields + static lookup (Step 6), Appendix D data flow.

**Reasoning:** Creates inter-turn sequencing decisions — the optimal exit for this corner may lock you out of an important entry for the next corner, forcing players to think ahead across turn boundaries. Turn-type-dependent lockout means the same exit stance carries different risk depending on what corner comes next.

---

## 2026-07-03 — Cube prototype tutorial added

`overview/godot_cube_prototype.md` — new file alongside the existing `godot_outline.md`:

- Simplified tutorial-style document focused on getting the combat loop running with colored cubes as placeholder 3D assets
- 10 sequential steps with clear 🤖 MCP / 🧑 Developer split
- 8s straight timer (matching `06-pattern-read.md`), 3 sequential pick phases
- Includes simplified tells (text/color HUD-based, matching `06-pattern-read.md` deception flow)
- Deferred: corner cinematic, car animations, face textures, segment loading, road shader
- Referenced from: `overview/06-pattern-read.md` (stance tables), `velocity_shift/equations.py` (math), `velocity_shift/ai.py` (personalities), `velocity_shift/deck.py` (deck weights)

**Reasoning:** The full `godot_outline.md` is comprehensive but overwhelming for initial prototyping. The cube prototype lets the developer tune gameplay constants before investing in 3D art assets, with a clear tutorial path that distinguishes what MCP automates vs what the developer configures.

---

## 2026-07-03 — Level-gap QTE difficulty scaling

`overview/godot_outline.md` — QTE timing/mash difficulty is now driven by level gap:

- **§4.1 QTEController.gd** — added `qte_difficulty()` static function: `timing_window_ms` shrinks and `speed_multiplier` increases as `opponent_level - player_level` grows
- **§1.2 globals.gd** — added 4 QTE difficulty constants (`QTE_TIMING_WINDOW_BASE_MS`, `QTE_TIMING_WINDOW_PER_GAP`, `QTE_MASH_SPEED_PER_GAP`, `QTE_TIMING_WINDOW_MIN_MS`)
- **§3.3 AIQTE.gd** — added note that level gap also feeds into AI consistency (shrinking noise range)
- **Appendix E** — added difficulty scaling descriptions for both mash & timing modes, with formula, constants, and example table (gap -10 → +10)
- **Appendix C** — updated data flow step 6 to compute and pass `qte_difficulty` to `QTEController.start()`

**Reasoning:** Higher-level opponents should feel mechanically sharper — your timing windows tighten and your mash rate must increase. The gap-based formula (`gap = opponent_level - player_level`) keeps even matches at base difficulty and only penalizes the player when outmatched.

---

## 2026-07-02 — Decision window updated: 8s real-time + corner cinematic scene

`overview/06-pattern-read.md` — updated Decision window:
- Removed slo-mo framing; 4s → 8s real-time straightaway approach to select all 3 cards
- Timeout auto-selects unselected positions (semi-random)
- Added corner cinematic scene: camera attached to turn type, car animation driven by selected stances

`overview/godot_outline.md` — timing flow updated to reflect cinematic corner scene after card selection

**Reasoning:** The slo-mo framing added unnecessary complexity (no gameplay need for it) and 4s was too tight to read both car animation channels and pick 3 cards. 8s real-time keeps tension through the straightaway approach. The cinematic corner scene gives visual payoff for the card selections and makes the turn feel like an actual driving moment rather than an abstract clash.

---

## 2026-07-02 — Corner cinematic system + segment-based rendering

`overview/godot_outline.md` — added corner cinematic system (§4.4):
- Segment-based rendering (Initial D: Another Stage style) — each turn loads/unloads its own straight + corner segment
- Per turn-type authored camera paths (not static camera)
- Stance-driven car traversal along corner Path3D
- QTE runs all 3 phases; damage computed after exit
- Overtake detection: if lead changed, short overtake animation (0.5-1s) + camera swing plays after exit
- Updated §4.1 (QTE runs all 3 phases), §4.2 (corner playback flow with overtake check), §6.1 (segment lifecycle), §6.2 (overtake animation), §6.4 (CarAnimator.play_overtake), §6.5 (BattleCamera.swing_overtake), Appendix A (revised corner flow)

`overview/06-pattern-read.md` — updated exit note:
- Exit reflects position (leading car pulls away, trailing car struggles)
- Overtake as separate short animation after DP resolution if lead changed

**Reasoning:** Segment-based rendering avoids maintaining a full continuous track while keeping each corner visually distinct. Overtake as a post-resolution extra animation gives clear visual payoff for lead changes without complicating the 3-phase stance system.

---

## 2026-07-02 — Merged remote godot_outline.md (1093-line full Godot implementation outline)

`overview/godot_outline.md` — replaced the 27-line placeholder with the full implementation outline from the remote branch, covering:
- Sections 1–8: Foundation, Engine Core, AI Layer, Corner + QTE, Position + Blend System, 3D Visuals, Art Integration, Wrap
- Appendices A–G: Turn Flow, Signals, Data Flow, Art Checklist, QTE Lookup, AI Stance Lookup, Notes/Gotchas
- My only local edit (timing flow step 3) was already superseded by the remote's more detailed TurnManager state machine and Appendix A corner playback description

`overview/06-pattern-read.md` — preserved local changes (positioning-based car motion, 8s decision window, cinematic corner scene); remote changes to this file (12s, sequential face reveals) were conflicting and discarded per user direction.

---

## 2026-07-02 — Stance projection changed to positioning-based car motion system

`overview/06-pattern-read.md` — replaced the entire **Car motion types** section:
- **Channel 1 (entry):** track position — outside bias = ATK, center bias = NEU, full-width weaving = DEF
- **Channel 2 (apex):** suspension loading — rear squat = ATK, front dive = DEF, flat = NEU
- Both channels play simultaneously on the straightaway approach before corner entry
- Bluffs use position/suspension that reads opposite the true stance, with secondary cues leaking the truth
- Removed old "in front / behind" framing
- Exit (pos 2) has no dedicated visual channel

`overview/godot_outline.md` — created with implementation outline for TrackPositionController, SuspensionAnimationController, StanceVisualConfig resource, and timing flow.

**Reasoning:** The old front/behind framing was ambiguous (who's in front changes mid-turn) and didn't give a clear visual read under time pressure. Position-based telegraphing maps directly to racing intuition — a car weaving wide is attacking, a car covering the full track is defending, a car holding center is steady. Suspension loading adds a second readable axis for apex intent, and playing both on the straightaway gives the player two simultaneous cross-referencing tells to decode deception.

---

## 2026-06-30 — Decision window added to pattern-read doc

`overview/06-pattern-read.md` — added a **Decision window** section at the end explaining that time slows to a crawl before each turn, giving the player 4 seconds to read the opponent's face and select a card. Passing on timeout is equivalent to playing a neutral with zero effect.

**Reasoning:** Formalizes the real-time pressure that makes the telegraphing system meaningful — players must read bluff tells under time constraint, not with unlimited analysis. The 4-second window creates a tension rhythm (observe → decide → execute) that matches the racing theme.

---

## 2026-06-26 — Character sheets restructured with pattern-read fields

### Split into per-character files

`story/character_sheets.md` → index; each character moved to their own file (`story/sabine.md`, `story/myth_driver_{1..4}.md`). All 5 sheets now include Myth Driver #4 (was accidentally truncated in the monolithic write). Each containing:
- **Narrative Identity** — role, backstory, conflict, resolution (preserved from old content)
- **Battle Identity** — archetype, face type, comfortable/weak turn types (TODO)
- **Deception Profile** — lie rate, clash-position weighting, intensity, reverse psychology (TODO; hand bluffs excluded per future rework)
- **Progression / Tier** — tier, difficulty class, level range (TODO)
- **Stance Preferences** — notes that strong/weak turns are fixed by archetype per pattern-read tables; other turn types have a per-character per-position preference (TODO)

**Reasoning:** Each character needs mechanical attributes that plug into the pattern-read system (face expressions, bluff behavior, turn-type proficiency) so their in-match behavior is consistent with their narrative identity. The TODO fields are intentionally left blank for the author to assign meaningful values.

## 2026-06-26 — Track layout randomization removed from pattern-read doc

`Notes/06-pattern-read.md` — removed all references to randomized track layout generation:
- **Line 45**: "randomized 10 turn sequence" → "predetermined 10-turn sequence"
- **Lines 46-47**: Removed incomplete "Each match shall include at least" sentence and "Seeded from MatchConfig" line
- **Line 7**: Added narrative framing bullet — tracks are fixed per circuit, archetype cornering habits remain consistent, but bluffing behavior is per-character (driven by lie rate and personality)

**Reasoning:** Player pattern memorization was a concern for fixed layouts, but since the game is narrative-driven, each character has their own bluffing habits defined by lie rate, personality, and the archetype comfort/weak zone system. The track itself becomes authored scenery rather than RNG.

## 2026-06-26 — Fixed preset builds format

`config/sample_builds.json` used the old stat system (`pow`/`def`/`eff` with no `archetype`/`level`), causing `KeyError: 'archetype'` when selecting a preset build. Replaced with builds keyed by archetype + level, matching the current `cars.build_stats()` API. 36 presets (6 archetypes × 6 tier levels).

## 2026-06-26 — Deckbuilding & Clash Docs Rewrite

### Fully rewritten: `overview/03-deckbuilding-clash.md`

The doc was highly out of date vs the codebase. Changes:

- **DECK_SIZE 36 → 192** — all card counts, formulas, composition table ("~12" → "~64"), and strategic cycle math (6 turns → 32 turns) updated
- **Selection phase** — rewritten from batch pick-3-and-arrange to sequential per-position picks with immediate clash resolution (lead → middle → anchor, one card at a time)
- **QTE rubber-band** — replaced the simplified binary split with the actual proportional blend system (threshold = 15% avg max_hp, `blend = min(1.0, abs(gap)/threshold)`)
- **HAN → QTE modifier** — added section documenting `apply_han_qte_mod` / `HAN_QTE_WEIGHT = 0.5`
- **Draw phase / deck reshuffle** — corrected to reflect player discard vs opponent `reshuffle_on_end` (no universal auto-reshuffle)
- **Flowchart** — updated to show sequential clash flow instead of batch arrangement
- **Played cards → discard** — noted opponent cards return to draw pile reshuffled

## 2026-06-23 — Unused Code Cleanup

### Removed dead code across the codebase

**Deleted:**
- `velocity_shift/config.py` — entire module; `build_from_archetype` had zero call sites (CLI calls `cars.build_stats()` directly)

**Production modules (`velocity_shift/`):**
- `velocity_shift/ai.py` — removed `ENCOUNTER_CEILINGS` dict (defined but never read); removed unused `rng` param from `_apply_override` signature and call site
- `velocity_shift/models.py` — removed `TurnResult.phase` field (written at `match.py:155` but never read by any code path)
- `velocity_shift/match.py` — removed write to `turn_result.phase`
- `velocity_shift/cli.py` — removed unused `get_phase` import
- `velocity_shift/simulation.py` — removed unused `get_phase` import

**Tests:**
- `tests/test_systems.py` — removed unused `Card`, `ClashResult` imports

**Scripts:**
- `scripts/balance_gauntlet.py` — **rewritten** to use current `resolve_turn` API directly (previously called `run_match` with an incompatible signature and referenced a nonexistent `opponent_ai_mode` field on `MatchConfig`)
- `scripts/generate_build_matrix.py` — removed legacy `MODS_MAP` dict; removed `opponent_builds` from JSON output (unconsumed by the game)
- `scripts/design_racers.py` — fixed two Python 3.11-incompatible f-string backslash expressions (`\u2500` inside `{}`) which also prevented `generate_build_matrix.py` from running

**Config:**
- `config/sample_builds.json` — regenerated without `opponent_builds` key

**Docs:**
- `AGENTS.md` — rewritten for concision: fixed stale test counts (5→9, 6→5, 7→8) and `DECK_SIZE` (36→192); pruned low-signal sections (stats table, damage formula, HP/DNF, encounter table); preserved git/changelog directives and high-signal gotchas; updated `python3`→`python` command

---

## 2026-06-21 — DNF State Removed

### Removed knockout / early-exit mechanic

**Removed** the DNF (Did Not Finish) rule where a combatant would lose when cumulative damage received ≥ max_hp. The match always runs all `max_turns`, then decides by position.

**Files touched:**
- `velocity_shift/match.py` — stripped early-exit check from turn loop; cleaned up stale `knockout` logic
- `velocity_shift/models.py` — removed dead DNF-related fields
- `velocity_shift/cli.py` — removed DNF display wiring
- `velocity_shift/ai.py` — removed DNF-related context from AI callbacks
- `velocity_shift/simulation.py` — removed DNF handling from batch runner
- `testing/test_systems.py` — removed knockout-specific test cases
- `scripts/balance_gauntlet.py` — removed DNF scenario
- `AGENTS.md`, `overview/*.md` — updated docs to reflect position-only win condition

**Reasoning:** DNF created a snowball problem — once a combatant fell behind, their max_hp deficit made recovery impossible. Removing it made races competitive for longer and pushed the decision to the full race distance, where skill (card selection) matters more than early luck.

---

## 2026-06-20 — HAN Stat Use

### Unified HAN → QTE modifier for both sides

**Replaced** the divergent HAN implementations with a single shared formula in `velocity_shift/equations.py`:

- Added `apply_han_qte_mod(qte_score, han_pct)` — same function used for both player and opponent
- Added `HAN_QTE_WEIGHT = 0.5` constant (moved from `ai.py`)
- Added `TYPICAL_QTE = 7.0` — AI QTE baseline, no longer derived from player QTE

**File changes by module:**
- `velocity_shift/ai.py` — `get_ai_qte` simplified: dropped `player_qte` and `ceiling` params, uses `TYPICAL_QTE × ratio` then `apply_han_qte_mod`. Removed local `HAN_QTE_WEIGHT`.
- `velocity_shift/match.py` — `apply_han_qte_mod` applied to both sides' raw QTE after callbacks. Opponent callback type changed to `Callable[[int], float]`.
- `velocity_shift/cli.py` — `get_opponent_qte` simplified to single-param. Removed `ENCOUNTER_CEILINGS` import.
- `velocity_shift/simulation.py` — same simplification. Removed `ENCOUNTER_CEILINGS` import.
- `tests/test_systems.py` — four opponent QTE lambdas updated to `lambda t:` signature.
- `tests/test_equations.py` — added 4 tests for `apply_han_qte_mod`.

**Intent:** HAN now affects QTE score (raw QTE × HAN modifier) for both sides through the same formula. Neutral point at han_pct = 1/3. Swift-like (55% HAN) gets +10.8%, Bruiser-like (25%) gets −4.2%. No double-dipping — HAN modifies the QTE score once, the existing pipeline (qte_factor → compute_damage → damage_mitigation) handles everything else.

---

## 2026-06-17 — Mod System Redesign

### Rewritten: `Notes/mod_notes.md`

**Replaced** the entire mod system design:
- Removed roguelite layer (car loss on boss defeat → narrative gating)
- Single assigned car, chosen from 2–3 chassis archetypes at new game
- Chassis has fixed stat ratio from L1, scales linearly — no convergence
- Mods are shop-bought equipment with trade-offs and unique effects (no drops)
- Loadout slots start at ~3, grow with car level
- Tree/mod categories deferred (TBD)

### Updated: `overview/05-skill-trees.md`

- Stripped speculative per-archetype tree tables
- Replaced "RunMods" references with current Mods system
- Flagged tree design as deferred with link to `Notes/mod_notes.md`
- Kept additive-only principle and system interactions as design guardrails

## 2026-06-10 — AI Personality Documentation + HP_PER_LEVEL Fixes

### Updated: `overview/04-difficulty-tuning.md`

**Replaced** the stale `## AI Difficulty (opponent behavior)` section (lines 116–125), which listed long-removed strategy names (`deterministic_attack`, `deterministic_defend`, `deterministic_neutral`, `random`) with an up-to-date section documenting the current phase-based personality system:

- **Personalities table** — all 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) mapped to their 3 phase-indexed behaviors (AGGRESSIVE / REACTIVE / UNPREDICTABLE with weights and overrides)
- **Phases per encounter table** — Wild (1), Lieutenant (2), Boss (3) with active personality indices
- **Unique opponents table** — ordered permutations per encounter:
  - Wild: 6
  - Lieutenant: 30
  - Boss: 120
  - **Total: 156 unique opponents**

Also **fixed** `HP_PER_LEVEL` value from 120 → 180 to match `velocity_shift/equations.py:20`.

### Updated: `overview/01-system-overview.md`

**Fixed** `HP_PER_LEVEL` value from 120 → 180 in the Normalization section to match `velocity_shift/equations.py:20`.

### Updated: `overview/03-deckbuilding-clash.md`

**Fixed** stale line 72: replaced "configurable strategy (attack-bias, defend-bias, random, etc.)" with a reference to the current phase-based personality system.

---

### Fully expanded: `Notes/06-pattern-read.md`

Replaced the original bullet list with a full spec covering:
- **4 deception mechanics** — lie rate, hand-dependent bluffing, clash-position weighting, reverse psychology tell
- **Turn type system** — 8 turn types (Hairpin, Straight, Chicane, Banked, S-Curve, Technical, Esses, Tunnel) with archetype-turn stance preference table (6×8 grid)
- **Track layout generation** — random per match, seeded, wraps if needed
- **Face types** — 6 cohesive expression palettes (one per archetype), 3 expressions each (ATK/DEF/NEU)
- **Expression intensity** — scale 1–5, gated by tier and encounter type
- **Bluff tell** mechanics — per-face-type betrayal signals, perceptibility tied to intensity
- **Tell generation flow** — step-by-step how a face is determined each turn
- **Combined deception axis** table including intensity values
