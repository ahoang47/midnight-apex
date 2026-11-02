# Velocity Shift — Godot Prototype

> Build a playable Godot prototype using only colored cubes. Tune gameplay constants,
> then replace cubes with real art — gameplay comes first.
>
> The Python code in `sim/velocity_shift/` is reference/prototype only — this is a
> full GDScript rewrite.

## How this works

| Icon | Who | What they do |
|------|-----|-------------|
| 🤖 | **MCP** | Creates scenes, scripts, and project settings using Godot tools |

---

## 1. Project Bootstrap

**Goal:** `project.godot` configured, global singletons registered, resource types defined.

### 1.1 Project settings

**🤖 MCP configures:**

| Setting | Value |
|---------|-------|
| Display width | 640 |
| Display height | 480 |
| Stretch mode | `viewport` |
| Aspect | `keep` |
| Input map `qte_mash` | Space / X |
| Input map `qte_timing` | Enter / Z |
| Input map `ui_accept` | Enter / Space |
| Input map `ui_cancel` | Escape |

### 1.2 `globals.gd` (autoload)

**🤖 MCP creates** `scripts/globals.gd` — enums, constants, and lockout lookup.

```gdscript
enum Stance { ATTACK, DEFEND, NEUTRAL }
enum StanceOutcome { WIN = 1, NEUTRAL = 0, LOSS = -1 }
enum EncounterType { WILD, LIEUTENANT, BOSS }
enum PhaseType { AGGRESSIVE, REACTIVE, UNPREDICTABLE }
enum QteType { MASH, TIMING }
```

**Balance constants** (match `sim/velocity_shift/equations.py` exactly):

| Name | Value | Notes |
|------|-------|-------|
| `CLASH_STAKES` | 0.35 | clash_mult = 1 ± CLASH_STAKES |
| `BATTLE_BONUS` | 0.05 | battle_mult bonus per win-margin point |
| `MITIGATION_PER_1000` | 0.40 | EN reduction per 1000 EN |
| `MITIGATION_FLOOR` | 0.10 | minimum damage fraction |
| `HP_PER_LEVEL` | 180 | max_hp = level × HP_PER_LEVEL |
| `QTE_NORMALIZER` | 10.0 | qte_factor = score / QTE_NORMALIZER |
| `HAN_QTE_WEIGHT` | 0.50 | HAN modifier for both sides |
| `DECK_SIZE` | 192 | cards per deck |
| `DECK_ALPHA` | 0.85 | smoothing term for deck weights |
| `DECK_HAND_SIZE` | 6 | cards drawn per turn |
| `PICKS_PER_TURN` | 3 | stances selected per turn |
| `RUBBER_BAND_PCT` | 0.15 | % of avg max HP for full rubber-band |
| `STRAIGHT_DURATION` | 12.0 | seconds for all 3 picks |
| `PHASE_DURATION` | 4.0 | seconds per individual pick |
| `EXIT_LOCKOUT_ENABLED` | true | toggle exit→entry lockout on/off |
| `QTE_TIMING_WINDOW_BASE_MS` | 800 | base width of timing target zone |
| `QTE_TIMING_WINDOW_PER_GAP` | 50 | ms shrunk per level of opponent advantage |
| `QTE_TIMING_WINDOW_MIN_MS` | 200 | floor for timing target zone |
| `QTE_MASH_SPEED_PER_GAP` | 0.10 | press-rate multiplier per level gap |

**Lockout lookup** (add after constants):

```gdscript
static func get_locked_out(exit_stance: int, from_type: int, to_type: int) -> Array:
    if not EXIT_LOCKOUT_ENABLED: return []
    var table = {
        "3|0|5": [Stance.NEUTRAL],
    }
    return table.get(str(from_type) + "|" + str(exit_stance) + "|" + str(to_type), [])
```

### 1.3 `SignalBus.gd` (autoload)

**🤖 MCP creates** `scripts/SignalBus.gd` — central event bus.

```gdscript
signal match_started(cfg)
signal straight_started(turn, turn_type, stances, bluff_flags)
signal phase_pick(phase_index, phase_name)
signal card_selected(stance)
signal phase_pick_timeout(phase_index)
signal corner_started(player_stances, opponent_stances)
signal clash_resolved(position, player_stance, opponent_stance, outcome)
signal corner_ended(qte_score)
signal damage_batch_done(player_dp, opponent_dp, cum_p, cum_o, battle_mult)
signal turn_ended(turn)
signal lap_began(phase, total)
signal match_ended(winner, player_name, opponent_name)
```

### 1.4 Resource scripts

**🤖 MCP creates** `scripts/CombatantStats.gd` and `scripts/MatchConfig.gd`:

```gdscript
# CombatantStats.gd
extends Resource; class_name CombatantStats
@export var name: String
@export var pow: float
@export var en: float
@export var han: float
@export var level: int
```

```gdscript
# MatchConfig.gd
extends Resource; class_name MatchConfig
@export var player_stats: CombatantStats
@export var opponent_stats: CombatantStats
@export var max_turns: int = 99
@export var seed: int
@export var deterministic: bool = true
@export var rival_personality: String
@export var encounter_type: String
```

---

## 2. Battle Scene

**Goal:** A 3D scene with two colored cubes on a ground plane, full UI overlay.

### 2.1 Scene hierarchy

**🤖 MCP creates** `scenes/Battle.tscn`:

```
Battle (Node)                                   ← TurnManager.gd attached
├── World3D (SubViewport)                       ← 3D viewport (640×480, transparent)
│   ├── WorldEnvironment                        ← sky, ambient, fog
│   ├── DirectionalLight3D                     ← shadows off for simplicity
│   ├── Camera3D                               ← chase cam (see Step 12)
│   ├── StraightRoad (Node3D)
│   │   └── MeshInstance3D                     ← BoxMesh, gray ~4×0.1×30
│   ├── CornerRoad (Node3D)
│   │   └── MeshInstance3D                     ← curved plane (placeholder, hidden during straight)
│   ├── PlayerCube (MeshInstance3D)            ← BoxMesh 1×1×1, white material
│   ├── OpponentCube (MeshInstance3D)          ← BoxMesh 1×1×1, white material
│   └── CarAnimators (Node)
│       ├── PlayerCarAnimator (Node)           ← CarAnimator.gd
│       └── OpponentCarAnimator (Node)         ← CarAnimator.gd
│
├── CanvasLayer (2D UI — 640×480)
│   ├── TopBar (HBoxContainer)
│   │   ├── PositionLabel (Label)             ← "1st" / "2nd"
│   │   ├── PhaseLabel (Label)                ← "LAP 1/3"
│   │   ├── TurnTypeLabel (Label)             ← "Hairpin L"
│   │   └── CornerTimerBar (TextureProgress)  ← 12s countdown
│   │
│   ├── CenterContent (HBoxContainer)
│   │   ├── OpponentPanel (VBox, 160px)
│   │   │   ├── FaceStack (Control 120×160)
│   │   │   │   ├── FaceATK (TextureRect)
│   │   │   │   ├── FaceDEF (TextureRect)
│   │   │   │   ├── FaceNEU (TextureRect)
│   │   │   │   └── TellOverlay (TextureRect)
│   │   │   ├── OpponentNameLabel (Label)
│   │   │   └── DPBarOpponent (TextureProgress)
│   │   │
│   │   ├── CenterGap (Control)               ← 3D viewport shows through
│   │   │
│   │   └── CardPanel (VBox, 180px)
│   │       ├── PhasePromptLabel (Label)      ← "ENTRY — Pick your stance"
│   │       ├── StraightTimerBar (TextureProgress)
│   │       ├── AttackButton (Button)
│   │       ├── DefendButton (Button)
│   │       └── SteadyButton (Button)
│   │
│   ├── BottomBar (HBoxContainer)
│   │   ├── PhaseColumn (VBox)
│   │   │   ├── EntryLabel (Label, "ENTRY")
│   │   │   ├── ApexLabel (Label, "APEX")
│   │   │   └── ExitLabel (Label, "EXIT")
│   │   ├── PlayerColumn (VBox)
│   │   │   ├── P1Panel (Panel)               ← colored bg per stance
│   │   │   │   └── P1Label (Label, stance name)
│   │   │   ├── P2Panel (Panel)               ← colored bg per stance
│   │   │   │   └── P2Label (Label, stance name)
│   │   │   └── P3Panel (Panel)               ← colored bg per stance
│   │   │       └── P3Label (Label, stance name)
│   │   ├── OpponentColumn (VBox)
│   │   │   ├── O1Panel (Panel)               ← colored bg per stance
│   │   │   │   └── O1Label (Label, stance name)
│   │   │   ├── O2Panel (Panel)               ← colored bg per stance
│   │   │   │   └── O2Label (Label, stance name)
│   │   │   └── O3Panel (Panel)               ← colored bg per stance
│   │   │       └── O3Label (Label, stance name)
│   │   └── DPBarPlayer (TextureProgress)
│   │
│   └── QTEOverlay (CenterContainer, hidden)
│       ├── QTEPromptLabel (Label)
│       ├── MashIndicator (TextureProgress)
│       └── TimingIndicator (Control)
│           ├── QteTarget (TextureRect)      ← target zone
│           └── QteMarker (TextureRect)      ← moving marker
│
└── TurnManager (Node)                          ← TurnManager.gd
```

---

## 3. Deck

**Goal:** 192-card stat-proportional deck. GDScript port of `sim/velocity_shift/deck.py`.

### 3.1 `Deck.gd`

**🤖 MCP creates** `scripts/Deck.gd`:

```gdscript
class_name Deck

const DECK_SIZE = 192
const ALPHA = 0.85

static func build(pow: float, en: float, han: float,
                  reshuffle_on_end: bool = false,
                  rng: RandomNumberGenerator = null) -> Deck
    # Compute weights using ALPHA smoothing (matching deck.py):
    #   total = pow + en + han
    #   w_atk = (pow / total) * (1 - ALPHA) + ALPHA / 3
    #   w_def = (en / total) * (1 - ALPHA) + ALPHA / 3
    #   w_neu = (han / total) * (1 - ALPHA) + ALPHA / 3
    # Fill DECK_SIZE cards proportionally, shuffle, return Deck instance

func draw(n: int = 6) -> Array                  # Draw up to n cards, return Array[Stance]
func prepare_turn_hand(requirements: Dictionary = {}) -> Array   # AI draw with retry
func end_turn(played: Array, unpicked: Array)   # Discard or reshuffle
func hand_stance_counts(hand: Array) -> Dictionary  # {ATTACK: N, DEFEND: N, NEUTRAL: N}
```

**Key rules:**
- Opponent deck: `reshuffle_on_end = true` (all 6 back, reshuffled each turn)
- Player deck: `reshuffle_on_end = false` (played + unpicked → discard pile)
- If draw pile < 6, return remaining cards (no auto-reshuffle)
- Deck weights use the same ALPHA smoothing as the Python prototype

### 3.2 Deck weights reference

```
total = pow + en + han
w_atk = (pow / total) × (1 - ALPHA) + ALPHA / 3
w_def = (en / total) × (1 - ALPHA) + ALPHA / 3
w_neu = (han / total) × (1 - ALPHA) + ALPHA / 3
```

---

## 4. Straight Timer + Card Selection

**Goal:** 12s countdown, 3 sequential phases (entry/apex/exit), auto-pick on timeout. Exit→Entry lockout enforced on phase 0.

### 4.1 `StraightTimer.gd`

**🤖 MCP creates** `scripts/StraightTimer.gd`:

```gdscript
extends TextureProgress

var total_time: float = 12.0
var phase_times: Array[float] = [4.0, 4.0, 4.0]
var current_phase: int = 0

signal phase_timeout(phase_index)
signal straight_complete

func start():
    # 12s countdown, emit phase_timeout at 4s, 8s, 12s
    # Update TextureProgress.value 0 → max over 12s
    # Phase prompt changes: ENTRY → APEX → EXIT
```

**Timeline:**

```
 0.0s  StraightTimer.start()
       → phase_pick(0) — CardHandUI enables, prompt: "ENTRY"
 4.0s  → phase_timeout(0) or player picks → phase_pick(1) — prompt: "APEX"
 8.0s  → phase_timeout(1) or player picks → phase_pick(2) — prompt: "EXIT"
 12.0s → straight_complete
```

### 4.2 `CardHandUI.gd`

**🤖 MCP creates** `scripts/CardHandUI.gd`:

```gdscript
func on_hand_dealt(hand: Array):
    counts = Deck.hand_stance_counts(hand)
    AttackButton.text = "ATTACK (x" + str(counts[ATTACK]) + ")"
    DefendButton.text = "DEFEND (x" + str(counts[DEFEND]) + ")"
    SteadyButton.text = "STEADY (x" + str(counts[NEUTRAL]) + ")"
    disable all buttons initially

func on_phase_pick(phase_index):
    enable all buttons with count > 0
    if phase_index == 0:
        blocked = TurnManager.locked_out_stances
        for stance in blocked:
            disable button for that stance

func on_card_selected(stance):
    decrement count for that stance
    update button text
    if count == 0: disable button
    emit card_selected(stance)
    disable all buttons until next phase_pick

func on_pick_timeout(phase_index):
    auto-pick the stance with the highest remaining count (skip blocked if phase_index == 0)
    (fallback: worst expected value)
```

---

## 5. Combat Math

**Goal:** Pure functions, 1:1 port from `sim/velocity_shift/equations.py` + `combat.py`.

### 5.1 `CombatResolver.gd`

**🤖 MCP creates** `scripts/CombatResolver.gd` — all static:

```gdscript
static func resolve_stance(a: Stance, b: Stance) -> StanceOutcome
    # Attack > Neutral > Defend > Attack

static func clash_mult(outcome: StanceOutcome) -> float
    # WIN → 1.35, LOSS → 0.65, NEUTRAL → 1.0

static func compute_damage(pow: float, qte_factor: float, clash_mult: float, battle_mult: float) -> float
    # pow × qte_factor × clash_mult × battle_mult

static func damage_mitigation(en: float, qte_factor: float) -> float
    # max(MITIGATION_FLOOR, 1 - (en/1000) × MITIGATION_PER_1000 × qte_factor)

static func qte_factor(score: float) -> float
    # score / QTE_NORMALIZER

static func apply_han_qte_mod(score: float, han_pct: float) -> float
    # score × (1 + HAN_QTE_WEIGHT × (han_pct - 1/3))

static func battle_winner(outcomes: Array) -> String
    # sum(outcome.values) — positive → "Player", negative → "Opponent", zero → "Tie"

static func battle_multiplier(outcome_sum: int) -> float
    # 1 + BATTLE_BONUS × abs(outcome_sum)

static func qte_rubber_band(player_gap: float, threshold: float, p_qte: float, o_qte: float) -> Dictionary
    # Returns { p_damage_qte, p_mitigation_qte, o_damage_qte, o_mitigation_qte }
    # Proportional blend: leader's disadvantaged stat erodes toward 1.0 as gap widens
```

Reference: `sim/velocity_shift/equations.py` — every formula is there.

---

## 6. Turn Manager

**Goal:** One state machine orchestrates the whole game loop.

### 6.1 `TurnManager.gd`

**🤖 MCP creates** `scripts/TurnManager.gd` — attached to Battle root.

```
States:
┌──────────────────────────────────────────────────────────────────────┐
│  START         → load config, build decks, init visuals              │
│       ↓                                                             │
│  STRAIGHT      → 12s timer with 3 sub-phases:                       │
│       │            [0-4s]  PICK_ENTRY                               │
│       │            [4-8s]  PICK_APEX                                │
│       │            [8-12s] PICK_EXIT                                │
│       ↓ (all 3 picks locked in)                                    │
│                                                                      │
│  CORNER_PLAYBACK → auto-resolve 3 clashes in sequence               │
│       │             + QTE runs simultaneously                        │
│       ↓ (QTE captured + all outcomes known)                         │
│                                                                      │
│  DAMAGE_BATCH   → compute DP, update bars, tween car positions      │
│       ↓ (tweens done)                                               │
│                                                                      │
│  END_TURN       → deck cycle, store exit for lockout, lap check     │
│       ↓ (more turns)                    ↓ (max turns)              │
│  → STRAIGHT                           MATCH_COMPLETE               │
└──────────────────────────────────────────────────────────────────────┘
```

**State fields:**

```gdscript
var last_exit_stance: int = -1
var last_turn_type: int = -1
var locked_out_stances: Array = []
```

**Lockout lookup:**

```gdscript
static func get_locked_out(exit_stance: int, from_turn_type: int, to_turn_type: int) -> Array:
    var table = {
        "3|0|5": [Stance.NEUTRAL],
    }
    return table.get(str(from_turn_type) + "|" + str(exit_stance) + "|" + str(to_turn_type), [])
```

**State transition triggers:**

| State | Entered by | Exited by |
|-------|-----------|-----------|
| START | Scene loaded | Setup complete |
| STRAIGHT | Previous END_TURN (or START) | All 3 picks stored |
| CORNER_PLAYBACK | All 3 picks locked | QTE complete + 3 clashes resolved |
| DAMAGE_BATCH | Corner end | Tween animations done |
| END_TURN | Damage displayed | Deck cycled |
| MATCH_COMPLETE | Max turns reached | — |

---

## 7. QTE

**Goal:** Runs during the corner phase. Type depends on turn_type × player stance.

### 7.1 `QTEController.gd`

**🤖 MCP creates** `scripts/QTEController.gd`:

```gdscript
func start(qte_type: QteType, difficulty: Dictionary):
    # Show QTEOverlay
    # Mash: count presses against speed_multiplier requirement
    #   Fills MashIndicator TextureProgress over ~3-4s
    #   difficulty.speed_multiplier adjusts how fast fill depletes between presses
    #   At 1.5x, you must press 50% faster to maintain the same fill rate
    # Timing: moving marker across target zone
    #   difficulty.timing_window_ms sets the width of the target zone
    #   Multiple successful presses increase score
    # Read QTE type from TurnTypeData.get_qte_type(turn_type, player_stance)
    # Runs ~3-4s (concurrent with clash resolution)

func stop() -> float:
    # Mash: final score = fill% × 10, normalized 1.0–10.0
    # Timing: final score = (successful_presses / total_opportunities) × 10
    # Return final score (1.0–10.0)
```

**Difficulty:**

```gdscript
static func qte_difficulty(player_level: int, opponent_level: int) -> Dictionary:
    var gap = opponent_level - player_level
    return {
        timing_window_ms: max(QTE_TIMING_WINDOW_MIN_MS,
            QTE_TIMING_WINDOW_BASE_MS - gap * QTE_TIMING_WINDOW_PER_GAP),
        speed_multiplier: 1.0 + max(0, gap) * QTE_MASH_SPEED_PER_GAP,
    }
```

| gap | timing_window_ms | speed_multiplier | feel |
|-----|-----------------|-----------------|------|
| -10 | 800 (capped) | 1.0 | Player dominates — no bonus |
| 0 | 800 | 1.0 | Even match — base difficulty |
| +3 | 650 | 1.30 | Opponent fav — tighter timing |
| +6 | 500 | 1.60 | Tough — zone shrinks, mash races |
| +10 | 300 | 2.00 | Max before soft floor at 200ms |

### 7.2 QTE Type lookup

One continuous QTE per corner. Type determined by `(turn_type × stance)`:

| Turn Type | ATTACK | DEFEND | STEADY |
|-----------|--------|--------|--------|
| Hairpin | MASH | TIMING | TIMING |
| Constant Radius | TIMING | MASH | MASH |
| Decreasing Radius | MASH | TIMING | MASH |
| Increasing Radius | TIMING | MASH | TIMING |
| 90-Degree | MASH | TIMING | MASH |
| Chicane | TIMING | MASH | MASH |
| Esses | MASH | TIMING | TIMING |
| Sweeper | TIMING | MASH | TIMING |

---

## 8. AI Layer

**Goal:** Opponent card selection, QTE generation, data resources.

### 8.1 Data resources

**🤖 MCP creates** static data classes:

**`TurnTypeData.gd`** — 8 turn types × 3 meta-archetype stance sequences (matching `06-pattern-read.md` tables):

```gdscript
static func get_stance_sequence(turn_type: String, archetype: String) -> Array[Stance]
    # Returns [entry_stance, apex_stance, exit_stance]

static func get_qte_type(turn_type: String, stance: Stance) -> QteType
    # Returns MASH or TIMING
```

**`ArchetypeData.gd`** — comfortable/weak turn zones per archetype:

```gdscript
static func get_meta_archetype(archetype: String) -> String    # "POW" / "EN" / "HAN"
static func get_face_type(archetype: String) -> String         # "Scowling" / "Grinning" / "Focused"
static func is_comfortable_turn(archetype: String, turn_type: String) -> bool
static func is_weak_turn(archetype: String, turn_type: String) -> bool
```

**`PersonalityData.gd`** — 5 personality configs (Aggressive, Defensive, Precise, Balanced, Adaptive) with 3 phases each. They mirror `PERSONALITY_MAP` in `sim/velocity_shift/ai.py`, which is the source of truth for each phase's type, weights, behavior override and hand requirements; see the phase table in `design/04-difficulty-tuning.md`. Wild races use phase 0 only, Lieutenants phases 0–1, Bosses all three.

**`TrackData.gd`** — predetermined 10-turn sequence per circuit:

```gdscript
static func get_track_layout(circuit_id: String) -> Array[String]
static func get_turn_type(turn: int, circuit_id: String) -> String
```

### 8.2 `AIPicker.gd`

**🤖 MCP creates** `scripts/AIPicker.gd`:

```gdscript
static func pick_card(hand: Array, opponent_hand: Array,
                      phase_index: int, personality: PersonalityConfig,
                      clash_index: int, previous_clashes: Array,
                      turn_number: int,
                      player_stance_history: Array[Stance],
                      rng: RandomNumberGenerator) -> Stance
    # MoveScore = EVWeight + PhaseWeight + PersonalityWeight + Randomness
    # Behavior overrides: counter, alternate, highest_ev, repeat_win
    # Unpredictable phase: 70% EV / 30% random
    # Lockout: aware of blocked stances — skips them if possible
```

### 8.3 `AIQTE.gd`

**🤖 MCP creates** `scripts/AIQTE.gd`:

```gdscript
static func generate_qte(level: int, encounter_type: String,
                          rng: RandomNumberGenerator,
                          deterministic: bool,
                          han_pct: float) -> float
    # Baseline = 7.0 × level_ratio (Wild=0.35, Lieutenant=0.75, Boss=1.15)
    # Modified by HAN proportion via apply_han_qte_mod
    # Noise range shrinks as opponent level increases
```

---

## 9. Tell System

**Goal:** Opponent face display with deception and bluff tells, crossfade schedule.

### 9.1 `TellGenerator.gd`

**🤖 MCP creates** `scripts/TellGenerator.gd` — implements the deception flow from `06-pattern-read.md`:

```gdscript
static func generate_tells(turn: int, archetype: String,
                           turn_type: String, encounter_type: String,
                           rng: RandomNumberGenerator) -> Array[Dictionary]
    # 1. Look up true stance sequence from TurnTypeData
    # 2. Check comfort/weak zones
    # 3. Apply lie rate per clash position
    # 4. Apply clash-position weighting
    # 5. Apply reverse psychology (top tier)
    # Returns Array of 3 { stance: Stance, is_bluff: bool, expression_key: String }
```

### 9.2 Face types

Each archetype maps to one face type with 3 expressions:

| Face Type | ATK expression | ATK tell | DEF expression | DEF tell | NEU expression | NEU tell |
|-----------|---------------|----------|----------------|----------|----------------|----------|
| A — Scowling (POW) | Bared teeth, furrowed brow | Mouth closes over bared teeth briefly | Tight jaw, narrowed eyes | Eyes flick wide then narrow back | Flat stare, relaxed brow | Brow drops and returns |
| B — Grinning (EN) | Wide smile, raised brows | Raised brows drop flat | Thin smile, watchful eyes | Eyes shift to the side | Half-smirk, steady gaze | Half-smirk goes straight |
| F — Focused (HAN) | Intense stare, sharp focus | Intense gaze loses focus, drifts | Cocky smirk, raised brow | Raised brow drops flat | Relaxed half-smile | Half-smile vanishes |

### 9.3 `FaceController.gd`

**🤖 MCP creates** `scripts/FaceController.gd`:

```gdscript
func set_face_sequence(expressions: Array[Dictionary], face_type: String)
    # Called at straight start with 3 (stance, is_bluff) tuples
    # Load the correct ATK/DEF/NEU textures for this face_type
    # Set tell overlay textures per stance
    # AnimationTreeBlendManager handles the alpha crossfade timing

func set_tell_alpha(intensity: float, is_deceptive: bool)
    # TellOverlay.modulate.a = intensity × (1.0 if is_deceptive else 0.0)
```

**Face crossfade mechanism:**

```
FaceStack (Control)
├── FaceATK (TextureRect)   ← modulate.a driven by stance_blend schedule
├── FaceDEF (TextureRect)   ← modulate.a driven by stance_blend schedule
├── FaceNEU (TextureRect)   ← modulate.a driven by stance_blend schedule
└── TellOverlay (TextureRect) ← modulate.a = intensity × is_deceptive
```

At any moment exactly one face texture has `a = 1.0` during a phase, with smooth 0.5s crossfade between phases. The tell overlay sits on top at reduced alpha.

**Face reveal schedule:**

```
 0s-4s:   ENTRY face shown + tell (if deceptive)
 4s-8s:   Crossfade to APEX expression
 8s-12s:  Crossfade to EXIT expression
```

---

## 10. Position & Damage Display

**Goal:** Track cumulative damage, update DP bars, show clash results.

### 10.1 `PositionTracker.gd`

**🤖 MCP creates** `scripts/PositionTracker.gd`:

```gdscript
var player_total_dp: float = 0.0
var opponent_total_dp: float = 0.0

func add_turn_damage(player_dp: float, opponent_dp: float)
    # Accumulate
    # Update DPBarPlayer.value and DPBarOpponent.value
    # Compute and emit position label (1st/2nd)

func get_player_gap() -> float
    # return player_total_dp - opponent_total_dp

func get_rubber_band_threshold(avg_max_hp: float) -> float
    # return avg_max_hp * RUBBER_BAND_PCT
```

### 10.2 `DamageDisplay.gd`

**🤖 MCP creates** `scripts/DamageDisplay.gd`:

```gdscript
func animate_bars(player_new_total: float, opponent_new_total: float,
                  player_max_hp: float, opponent_max_hp: float)
    # Tween DPBarPlayer.value and DPBarOpponent.value from current to new
    # Duration: 0.8s
    # Flash "1st" / "2nd" label update
```

### 10.3 `ClashDisplay.gd`

**🤖 MCP creates** `scripts/ClashDisplay.gd`:

```gdscript
const COLORS = {
    ATTACK:  Color("#dc2626"),
    DEFEND:  Color("#16a34a"),
    NEUTRAL: Color("#d97706"),
}

func display_summary(player_stances: Array[int], opponent_stances: Array[int])
    # 2 rows × 3 cols: PhaseColumn | PlayerColumn | OpponentColumn
    # Color panels per stance

func reveal_phase(phase_index: int)
    # Brief scale-pulse fade-in for this row
```

### 10.4 `PhaseAnnouncer.gd`

**🤖 MCP creates** `scripts/PhaseAnnouncer.gd`:

```gdscript
func announce_lap(phase: int, total: int)
    # Show overlay: "LAP 2/3" with fade-in, hold 1.5s, fade-out
```

---

## 11. Car Animation

**Goal:** Each car has straight Z-offset (DP gap) and corner path traversal. AnimationTree blends stance body language.

### 11.1 `CarAnimator.gd`

**🤖 MCP creates** `scripts/CarAnimator.gd` — one per car:

```gdscript
# ─── Straight phase ───────────────────────────────────────────────

var straight_base_z: float = 0.0

func snap_to_gap(gap: float, max_gap: float)
    # global_position.z = straight_base_z + lerp(-5.0, 5.0, clamp(gap / max_gap, -1.0, 1.0))
    # Tween over 0.5s

func play_surge()
    # Brief forward burst (clash win)

func play_drop()
    # Brief backward fall (clash loss)

# ─── Corner phase ─────────────────────────────────────────────────

var corner_path: Curve3D
var corner_progress: float = 0.0
var progress_offset: float = 0.0

func begin_corner_traversal(path: Curve3D, duration: float = 3.5)
    # Store Path3D curve from CornerRoad
    # Read current DP gap from PositionTracker
    # Set progress_offset = dp_gap / max_gap × 0.1 (10% path offset per full gap)
    # Tween corner_progress from 0.0 → 1.0 over duration

func _on_corner_progress_updated(progress: float)
    # position = corner_path.sample_baked(clamp(progress + progress_offset, 0.0, 1.0))
    # Align car rotation to path tangent

func play_overtake()
    # 0.5-1s pass animation — car moves from behind to ahead along corner path

func end_corner_traversal()
    # Reset to straight positioning
```

### 11.2 Animation Tree structure

**Car AnimationTree:**

```
AnimationTree
├── AnimationNodeBlend3 (root)
│   ├── Animation (corner_left)        ← base (blend via corner_blend param)
│   ├── Animation (corner_right)       ← base (blend via corner_blend param)
│   └── AnimationNodeBlend3 (stance blend)
│       ├── Animation (pose_attack)    ← blended via stance_blend param
│       ├── Animation (pose_defend)
│       └── Animation (pose_steady)
```

### 11.3 `AnimationTreeBlendManager.gd`

**🤖 MCP creates** `scripts/AnimationTreeBlendManager.gd` — drives both car AnimationTree and face crossfade:

```gdscript
func start_blend_cycle(entry_stance: Stance, apex_stance: Stance,
                       exit_stance: Stance, corner_direction: String)
    # Set corner_blend on both car AnimationTrees (left=0.0, right=1.0)
    # Begin 12s stance_blend schedule:
    #   0s-4s:   stance_blend → entry_stance weight 1.0
    #   4s-8s:   crossfade → apex_stance weight 1.0
    #   8s-12s:  crossfade → exit_stance weight 1.0
    # Same schedule drives FaceStack alpha

func update_blend(delta: float)
    # Called each frame during STRAIGHT state
    # Interpolates stance_blend parameter

func set_tell_alpha(intensity: float, is_deceptive: bool)
    # TellOverlay.modulate.a = intensity × (1.0 if is_deceptive else 0.0)
```

### 11.4 Connected signals

- `turn_state_changed(STRAIGHT)`: `snap_to_gap(...)` with current DP
- `turn_state_changed(CORNER_PLAYBACK)`: `begin_corner_traversal(...)`
- `clash_resolved(position, ...)`: `play_surge()` on winner / `play_drop()` on loser
- `lead_changed`: `play_overtake()` on overtaking car
- `turn_state_changed(DAMAGE_BATCH)`: `end_corner_traversal()`

---

## 12. Camera

**Goal:** Chase cam that follows the cars through straight and corner phases.

### 12.1 `BattleCamera.gd`

**🤖 MCP creates** `scripts/BattleCamera.gd` — attached to Camera3D:

```gdscript
# During STRAIGHT:
#   - Behind both cars, looking down the straight road
#   - FOV ~65°, slight vertical tilt for speed feel
# During CORNER_PLAYBACK:
#   - Rotate ~15° around Y axis into corner direction
#   - FOV ~55°, closer to cars
#   - Subtle X roll to follow road camber
# During DAMAGE_BATCH:
#   - Hold same position as corner

func transition_to_corner(corner_direction: String)
    # If "left":  target_pos = origin + Vector3(-3, 0.5, 1)
    # If "right": target_pos = origin + Vector3(3, 0.5, 1)
    # Tween over 1.0s (ease-in-out)

func transition_to_straight()
    # Tween back to default chase cam position over 1.0s

func swing_overtake()
    # Brief camera shift (0.3s) to emphasize overtake during exit
```

---

## 13. Corner Cinematic

**Goal:** Turn the abstract clash into a visual corner playback with segment-based rendering.

### 13.1 Segment-based rendering

No continuous track. Each turn is a self-contained straight approach + corner segment. Previous segment unloaded, next segment loaded between turns (Initial D: Another Stage style).

| Game state | Visible road | Car positioning | Camera |
|---|---|---|---|
| LOAD_SEGMENT | (loading) | — | — |
| STRAIGHT | StraightRoad | Static Z-offset for DP gap | Chase cam behind |
| CORNER_PLAYBACK | CornerRoad | Pathing along Curve3D | Authored camera path |
| DAMAGE_BATCH | CornerRoad | Static at corner exit | Same as corner |
| END_TURN | (unload) | Snap back to straight Z | Swing back to chase cam |

### 13.2 Corner playback flow

```
1. Load corner segment (straight + corner meshes + camera path + car Path3D)
2. emit corner_started(player_stances, opponent_stances)
3. QTEController.start(qte_type)         ← runs through all 3 phases
4. RESOLVE_ENTRY → clash anim (~1.5s, QTE active) + CarAnimator.surge/drop
5. RESOLVE_APEX  → clash anim (~1.5s, QTE active) + CarAnimator.surge/drop
6. RESOLVE_EXIT  → position-based exit anim (~1.5s, QTE active) + CarAnimator.surge/drop
7. QTEController.stop() → qte_score
8. Damage computed from all 3 phases → DP gap resolved
9. Lead change check:
   a. If leader changed → play overtake animation (0.5-1s) + camera.swing_overtake()
   b. If unchanged → skip
10. emit corner_ended(qte_score)
11. Unload corner segment
```

### 13.3 Per turn-type camera choreography

Each turn type has an authored camera motion path — a Path3D the camera follows:

| Turn Type | Camera feel |
|-----------|-------------|
| Hairpin | Tight inside-line view |
| Sweeper | Wide tracking shot |
| Chicane | Side-angle for S-motion |
| Esses | Flowing follow-cam |
| 90-Degree | Sharp cut to apex |

---

## 14. Scene Management + Road FX

### 14.1 `StageManager.gd` (autoload)

**🤖 MCP creates** `scripts/StageManager.gd`:

```gdscript
func load_battle(config: MatchConfig)
    # Transition to Battle.tscn, pass config

func load_menu()
    # For future: load Menu scene

func load_results(result: MatchResult)
    # For future: show results overlay or scene
```

For v1: `load_battle()` is the primary entry point.

### 14.2 `RoadScroller.gd`

**🤖 MCP creates** `scripts/RoadScroller.gd` — UV-offset parallax to simulate speed.

```gdscript
extends ShaderMaterial

var scroll_speed: float = 0.05

func start_scrolling()
    # Begin incrementing UV offset each frame

func stop_scrolling()
    # Pause UV offset

func set_speed(factor: float)
    # Adjust for drama: faster during straight, slower during corner

func _process(delta):
    # uv_offset += scroll_speed × delta
    # Apply to road mesh material

func transition_to_corner()
    # Brief speed burst + decel as cars approach the bend
    set_speed(1.5) → wait 0.5s → set_speed(0.6)
```

Applied as `ShaderMaterial` on both road segments. The same UV-offset drives both straight and corner textures.

### 14.3 Corner segment lifecycle

```
1. END_TURN: unload previous corner segment
2. Load next corner segment (straight + corner + cam path + car path)
3. STRAIGHT: show straight mesh, cars at starting Z positions
4. CORNER_PLAYBACK: hide straight, show corner mesh, cars traverse Path3D
5. All 3 phases resolve → damage computed → overtake if applicable
6. Unload corner segment, loop
```

---

## 15. Tuning Loop

**Goal:** Play matches → adjust constants → play again. This is the whole point.

### 15.1 How to run

1. Open `Battle.tscn` in Godot, press **F5**
2. Match starts automatically (uses a default `MatchConfig`)
3. Pick 3 stances across 3 phases (entry → apex → exit)
4. Complete the QTE (mash or timing)
5. Watch DP bars + cubes update
6. Match ends at `max_turns` → winner displayed
7. Edit constants in `globals.gd` → **F5** to rerun

### 15.2 Quick-tune constants

| Constant | Effect | Recommended range |
|----------|--------|-------------------|
| `CLASH_STAKES` | How much each clash win/loss matters | 0.25 – 0.45 |
| `BATTLE_BONUS` | How much winning the battle amplifies damage | 0.03 – 0.10 |
| `MITIGATION_PER_1000` | How effective EN is per 1000 | 0.30 – 0.50 |
| `MITIGATION_FLOOR` | Minimum damage always dealt | 0.05 – 0.20 |
| `HP_PER_LEVEL` | HP per level (turns length) | 150 – 200 |
| `STRAIGHT_DURATION` | Seconds to pick 3 stances | 8.0 – 12.0 |
| `QTE_TIMING_WINDOW_BASE_MS` | Base timing target width | 600 – 1000 |
| `DECK_ALPHA` | Deck smoothing (higher = more even) | 0.70 – 0.95 |
| `RUBBER_BAND_PCT` | QTE comeback threshold | 0.10 – 0.25 |
| `EXIT_LOCKOUT_ENABLED` | Toggle lockout on/off | true / false |

### 15.3 Tuning flow

1. **Run vs Wild** (level gap favors you) — should feel dominant but not boring
2. **Run vs Lieutenant** (near parity) — should feel tense, each pick matters
3. **Run vs Boss** (level gap favors them) — should feel like an uphill fight
4. **Adjust** any constant that makes a matchup feel wrong
5. **Rerun** — no restart needed, just F5

### 15.4 Adding real art later

When gameplay is tuned to your liking:

1. Replace `PlayerCube` / `OpponentCube` BoxMesh with imported car `.glb`
2. Replace ground plane with road meshes (straight + corner variants)
3. Replace `TextureProgress` bars and `Button` textures with styled assets
4. Add corner cinematic (Path3D traversal, camera choreography)
5. Import face textures and wire into FaceStack TextureRects
6. The gameplay scripts (`Deck.gd`, `CombatResolver.gd`, `TurnManager.gd`, etc.) need zero changes

### 15.5 Edge cases

- **Tiebreaker:** opponent wins on equal position (enforced in TurnManager)
- **Empty deck:** player deck runs out of cards mid-match → draw returns fewer
- **Rapid clicking:** CardHandUI disables buttons between phases
- **Timer precision:** StraightTimer uses `delta` accumulation, not frame count

### 15.6 Deferred

- Sound / music — design signal hooks for future audio integration
- Skill trees — not in v1
- Mods system — separate design doc
- Menu → Overworld → Race flow — StageManager stubs exist
- Full face texture assets — placeholders until art pass

---

## Appendix A: File Manifest

**🤖 MCP creates:**

```
project.godot

scripts/
  globals.gd               — enums + constants + lockout lookup
  SignalBus.gd             — 12 signals
  CombatantStats.gd        — resource
  MatchConfig.gd           — resource
  Deck.gd                  — 192-card stat-proportional
  StraightTimer.gd         — 12s, 3 phases
  CardHandUI.gd            — 3 buttons + counts + lockout
  CombatResolver.gd        — pure math
  TurnManager.gd           — state machine
  QTEController.gd         — mash + timing
  AIPicker.gd              — EV scoring
  AIQTE.gd                 — opponent QTE generation
  TurnTypeData.gd          — stance sequences + QTE type
  ArchetypeData.gd         — comfort/weak zones
  PersonalityData.gd       — 5 personalities, 3 phases each
  TrackData.gd             — circuit layouts
  TellGenerator.gd         — deception flow
  FaceController.gd        — face display + tell overlay
  PositionTracker.gd       — cumulative DP
  DamageDisplay.gd         — DP bar tweens
  ClashDisplay.gd          — 2×3 stance grid
  PhaseAnnouncer.gd        — lap boundaries
  CarAnimator.gd           — Z-offset + path traversal
  AnimationTreeBlendManager.gd — stance blend + face crossfade
  BattleCamera.gd          — chase cam + transitions
  StageManager.gd          — scene loading (autoload)
  RoadScroller.gd          — UV-offset parallax

scenes/
  Battle.tscn              — full node hierarchy
```

Total: **24 script files + 1 scene file**

---

## Appendix B: Turn Flow Reference

```
[STRAIGHT — 12s REAL TIME]
  Car drives toward the corner. Opponent car projects the racing line.
  Three opponent faces reveal SEQUENTIALLY with smooth crossfade:
    0s-4s:   ENTRY face shown + tell (if deceptive)
             Player picks entry stance (lockout applied)
    4s-8s:   Face crossfades to APEX expression
             Player picks apex stance
    8s-12s:  Face crossfades to EXIT expression
             Player picks exit stance
  Each pick has 4s window; auto-pick on expire.

[CARS ENTER CORNER — SEGMENT-BASED CINEMATIC]
  All 3 stances locked in. Corner segment plays out:
    1. RESOLVE_ENTRY → clash anim (~1.5s, QTE active)
    2. RESOLVE_APEX  → clash anim (~1.5s, QTE active)
    3. RESOLVE_EXIT  → position-based anim (~1.5s, QTE active)

  [CONTINUOUS QTE runs through all 3 phases]

[CORNER EXIT]
  QTE stops. Damage computed from all 3 phases → DP gap resolved
  Lead change check:
    - If changed → overtake animation (0.5-1s) + camera swing
    - If unchanged → skip
  DP bars update → position label updates
  Car positions tween to reflect new gap
  → Unload corner segment
  → DECK DISCARD / DRAW for next turn
  → Load next corner segment
  → Loop back to STRAIGHT (next corner)
```

### Mapping to Python reference

| Phase | Python equivalent |
|-------|-------------------|
| Straight (12s) | No equivalent — pure Godot UX |
| 3× CARD_PICK | `match.py` sequential pick loop (on straight) |
| 3× CLASH resolve | `equations.resolve_stance()` (in corner, batched) |
| 1× QTE (corner-long) | `cli.prompt_qte()` → `combat.py` QTE split |
| DAMAGE batch | `combat.resolve_turn()` (all 3 averaged) |
| DECK draw/discard | `deck.py` draw + end_turn |

---

## Appendix C: Signals Reference

All signals on `SignalBus` autoload singleton.

| Signal | Payload | Emitter | Fires When |
|--------|---------|---------|------------|
| `match_started(cfg: MatchConfig)` | `MatchConfig` | StageManager | Battle scene ready |
| `straight_started(turn, turn_type, entry_stance, apex_stance, exit_stance, is_deceptive)` | `int, String, int×3, Array[bool]` | TurnManager | Straight begins |
| `phase_pick(phase_index, phase_name)` | `int, String` | TurnManager | 0/entry, 1/apex, 2/exit |
| `card_selected(stance: int)` | `Stance` | CardHandUI | Player clicks stance button |
| `phase_pick_timeout(phase_index)` | `int` | StraightTimer | Per-pick sub-timer expired |
| `corner_started(player_stances, opponent_stances)` | `Array[int]×2` | TurnManager | Corner playback begins, QTE starts |
| `clash_resolved(position, player_stance, opponent_stance, outcome)` | `int×4` | TurnManager | Per-clash resolution done |
| `corner_ended(qte_score)` | `float` | TurnManager | All 3 clashes + QTE complete |
| `damage_batch_done(player_dp, opponent_dp, cum_player, cum_opponent, battle_mult)` | `float×5` | TurnManager | Damage computed, bars start animating |
| `turn_ended(turn)` | `int` | TurnManager | Deck cycled, ready for next straight |
| `lap_began(phase, total)` | `int, int` | TurnManager | Phase boundary crossed |
| `match_ended(winner, player_name, opponent_name)` | `String×3` | TurnManager | Max turns reached |

---

## Appendix D: Full Data Flow

```
BEFORE TURN: TurnManager reads TrackData for current turn_type
  → Set TurnTypeLabel
  → Set corner_blend (left/right) on AnimationTreeBlendManager
  → Look up opponent's entry/apex/exit stances from TurnTypeData
  → TellGenerator: deception check per position → 3 (stance, is_bluff) tuples
  → FaceController: load target textures for all 3 positions

1. TurnManager: state = STRAIGHT (12s)
     → Deck: draw 6, compute stance counts → CardHandUI: update button labels
     → StraightTimer: start 12s countdown
     → emit straight_started(...)
     → AnimationTreeBlendManager: begin stance_blend cycle
       (0-4s: entry_weight, 4-8s: apex_weight, 8-12s: exit_weight)
     → FaceStack: alpha crossfade follows same schedule

2. PICK_ENTRY (0-4s)
     → compute locked_out_stances = get_locked_out(last_exit_stance, last_turn_type, current_turn_type)
     → emit phase_pick(0, "ENTRY")
     → CardHandUI: enable buttons with count > 0 (minus lockout-blocked stances)
     a. Player clicks → emit card_selected(stance) → store
     b. OR 4s expires → emit phase_pick_timeout(0) → auto-pick (skip blocked) → store
     → CardHandUI: disable, grey out consumed count
     → PhasePromptLabel: "APEX — Pick your stance"

3. PICK_APEX (4-8s)
     → same flow as ENTRY (no lockout)

4. PICK_EXIT (8-12s)
     → same flow as ENTRY (no lockout)

5. StraightTimer emits straight_complete
     → AIPicker: select opponent's 3 cards

6. TurnManager: state = CORNER_PLAYBACK
     → compute qte_difficulty = QTEController.qte_difficulty(player.level, opponent.level)
     → emit corner_started(player_stances, opponent_stances)
      → QTEController.start(qte_type, qte_difficulty)
      → ClashDisplay.display_summary(player_stances, opponent_stances)
      → Loop through 3 positions:
          CombatResolver.resolve_stance(player, opponent)
          → emit clash_resolved(...)
          → ClashDisplay.reveal_phase(position)
          → CarAnimator.play_surge() or play_drop()
     → QTEController.stop() → qte_score
     → emit corner_ended(qte_score)

7. TurnManager: state = DAMAGE_BATCH
     → CombatResolver: compute 3× DP, average, mitigate, battle_mult
     → HAN modifier applied to QTE scores
     → Rubber-band QTE split applied
     → PositionTracker: accumulate
     → CarAnimator: tween Z offsets to new gap
     → DamageDisplay: animate bars
     → emit damage_batch_done(...)

8. TurnManager: state = END_TURN
     → Deck.end_turn(played, unpicked)
     → Store last_exit_stance = played[2] (exit stance) for lockout next turn
     → Store last_turn_type = current_turn_type
     → Check lap boundary → emit lap_began(...)
     → If turns < max_turns → STRAIGHT
     → If turns >= max_turns → emit match_ended(...)
```

---

## Appendix E: Art Asset Checklist

### 3D Assets (human — Blender)

| Asset | Count | Notes |
|-------|-------|-------|
| Car body mesh | 1 | Low-poly PS1-style, shared by both cars |
| Player livery material | 1 | `.tres` + `.png` texture |
| Opponent livery material | 1 | `.tres` + `.png` texture |
| `corner_right` animation | 1 | glTF |
| `corner_left` animation | 1 | glTF |
| `pose_attack` animation | 1 | glTF |
| `pose_defend` animation | 1 | glTF |
| `pose_steady` animation | 1 | glTF |
| `surge_ahead` animation | 1 | glTF (0.3s) |
| `drop_back` animation | 1 | glTF (0.3s) |
| `road_straight` mesh | 1 | Long straight plane with lane markings (~30 units) |
| `road_corner_left` mesh | 1 | Curved plane arc left, same lane layout |
| `road_corner_right` mesh | 1 | Curved plane arc right, mirror of left |
| `barrier_straight` mesh | 2 | Road-edge barrier wall segment (straight) |
| `barrier_corner_left` mesh | 2 | Road-edge barrier wall following left curve |
| `barrier_corner_right` mesh | 2 | Road-edge barrier wall following right curve |
| Track texture | 1 | `.png` tiling road surface (shared UV across all segments) |
| Skybox | 1 cubemap | 6× `.png` or 1 equirect |

### Face Assets (human — Aseprite/Photoshop)

9 face portraits + 9 tell overlays (see Step 9 for expression reference):

| File | Subject |
|------|---------|
| `face_scowling_atk.png`, `face_scowling_def.png`, `face_scowling_neu.png` | Aggressive expressions |
| `face_grinning_atk.png`, `face_grinning_def.png`, `face_grinning_neu.png` | Defensive and Balanced expressions |
| `face_focused_atk.png`, `face_focused_def.png`, `face_focused_neu.png` | Precise and Adaptive expressions |
| `tell_scowling_atk.png`, `tell_scowling_def.png`, `tell_scowling_neu.png` | Aggressive tells |
| `tell_grinning_atk.png`, `tell_grinning_def.png`, `tell_grinning_neu.png` | Defensive and Balanced tells |
| `tell_focused_atk.png`, `tell_focused_def.png`, `tell_focused_neu.png` | Precise and Adaptive tells |

### UI Assets (human — Aseprite/Photoshop)

| Files | Count |
|-------|-------|
| Button idle/pressed (ATK, DEF, STEADY) | 6 |
| Panel backgrounds (9-slice) | 4 |
| Timer bar fills (straight, QTE mash) | 2 |
| QTE indicator (timing marker, timing target) | 2 |
| Outcome icons (WIN, LOSS, TIE) | 3 |
| Position icons (1st, 2nd) | 2 |
| DP bar fills (player, opponent) | 2 |
| Font | 1 `.ttf`/`.otf` |

---

## Appendix F: QTE Type Lookup + Difficulty Formula

One continuous QTE per corner. Type determined by `(turn_type × player stance)`.

| Turn Type | ATTACK | DEFEND | STEADY |
|-----------|--------|--------|--------|
| Hairpin | MASH | TIMING | TIMING |
| Constant Radius | TIMING | MASH | MASH |
| Decreasing Radius | MASH | TIMING | MASH |
| Increasing Radius | TIMING | MASH | TIMING |
| 90-Degree | MASH | TIMING | MASH |
| Chicane | TIMING | MASH | MASH |
| Esses | MASH | TIMING | TIMING |
| Sweeper | TIMING | MASH | TIMING |

### Mash mode (continuous)
- Rapid button press (input map: `qte_mash`)
- Fill bar builds during corner playback (~3-4s)
- Final score = fill % × 10, normalized 1–10
- **Difficulty scaling:** `speed_multiplier` adjusts how fast the fill bar depletes between presses — at 1.5×, you must press 50% faster to maintain the same fill rate.

### Timing mode (continuous)
- Moving marker oscillates across a target zone
- Timer ticks down; multiple successful presses increase score
- Final score = (successful_presses / total_opportunities × 10)
- **Difficulty scaling:** `timing_window_ms` sets the width of the target zone — at 800ms the zone is generous, at 200ms you must nail the frame. Both the window size and the marker oscillation speed scale with the gap.

### Difficulty formula

```gdscript
gap = opponent_level - player_level
timing_window_ms = max(QTE_TIMING_WINDOW_MIN_MS,
                       QTE_TIMING_WINDOW_BASE_MS - gap × QTE_TIMING_WINDOW_PER_GAP)
speed_multiplier = 1.0 + max(0, gap) × QTE_MASH_SPEED_PER_GAP
```

| gap | timing_window_ms | speed_multiplier | feel |
|-----|-----------------|-----------------|------|
| -10 | 800 (capped) | 1.0 | Player dominates — no bonus |
| 0 | 800 | 1.0 | Even match — base difficulty |
| +3 | 650 | 1.30 | Opponent fav — tighter timing |
| +6 | 500 | 1.60 | Tough — zone shrinks, mash races |
| +10 | 300 | 2.00 | Max before soft floor at 200ms |

---

## Appendix G: AI Stance Lookup

For each corner, the opponent's 3 "true" stance picks come from the turn-type table per their archetype. TellGenerator may swap some based on deception.

```
# TurnTypeData lookup for Aggressive on Hairpin:
entry_stance = DEFEND
apex_stance  = DEFEND
exit_stance  = ATTACK

# Deception check per position:
# 0: show DEFEND, tell if deceptive
# 1: show DEFEND, tell if deceptive
# 2: show ATTACK, tell if deceptive
```

Tables in `06-pattern-read.md` — sections: Aggressive, Defensive, Precise. Balanced shares Defensive's sequences and Adaptive shares Precise's.

---

## Appendix H: Notes / Gotchas

- **Stance naming:** UI displays "STEADY" but the enum is `Stance.NEUTRAL`. Button label and all UI text uses "STEADY"; all logic uses NEUTRAL.
- **Deck size:** 192 cards. Draw 6, pick 3, discard 3.
- **Opponent deck:** reshuffles each turn (player deck uses discard pile).
- **HP_PER_LEVEL = 180**, not 120.
- **No DNF / knockout** — match always runs to max_turns, then position decides.
- **Tiebreaker:** opponent wins on equal position.
- **Rubber-band threshold:** 15% of average max HP.
- **Car position in 3D:** purely a visualization of DP gap. DP = position.
- **AnimationTree blend:** 7 animations + 3-way blend node = smooth stance transitions for any 3-stance sequence. No per-combination baking.
- **Face crossfade:** 3 stacked TextureRects with alpha driven by same blend schedule as the car. 4th overlay layer for bluff tell.
- **Meta-archetypes:** 3 face types (Scowling/Grinning/Focused) shared by hard+soft pairs. 9 face textures + 9 tell overlays total.
- **Future screens:** Menu → Isometric Overworld → Race → Battle → Results → Overworld. Design scene loading (StageManager) with this in mind.
- **No skill trees** in v1 (deferred). Mods system design is separate.
- **Sound/music:** deferred. Design signal hooks for future audio integration.
