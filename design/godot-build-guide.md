# Midnight Apex — Godot Prototype

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

## 0. Playtest-to-Troubleshooting Spec (PROPOSED)

Moved to `unapproved/gordon/playtest-state-spec.md` (unapproved; awaiting Austin).

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

**🤖 MCP creates** `scripts/globals.gd` — enums and constants.

```gdscript
enum Stance { ATTACK, DEFEND, NEUTRAL }
enum StanceOutcome { WIN = 1, NEUTRAL = 0, LOSS = -1 }
enum EncounterType { WILD, LIEUTENANT, BOSS }
enum PhaseType { AGGRESSIVE, REACTIVE, UNPREDICTABLE }
enum QteType { MASH, TIMING }
```

**Combat constants** (copied from `sim/velocity_shift/equations.py` by name and never retuned in Godot; the values live only in the sim, Barry's source of truth):

| Name | Notes |
|------|-------|
| `KNOT_WINDOW_105` | `(r, W)` knots for `knot_window(r)`, the player-only QTE window |
| `KAPPA_BY_LENGTH` | Stat-gap leverage `V = r^kappa`, keyed by race length in turns |
| `RACE_LENGTHS` | Race lengths that have a `KAPPA_BY_LENGTH` entry |
| `OPPONENT_QTE` | Opponent timing skill `q`; its window is `W = 1`, and HAN still applies |
| `W0`, `T_MAX`, `L_MAX` | Phi payoff: win at q = 0, tie at q = 1, loss at q = 1 |
| `TAU_BETA`, `TAU_P_TOP`, `TAU_GAMMA` | tau(q): top-bonus share, top-bonus sharpness, body shape |
| `MU` | POW share raises the win payoff; EN share raises the tie/loss payoff |
| `ETA` | HAN share raises effective timing (both sides) |
| `QTE_NORMALIZER` | QTE score (1–10) → `q_time`, the same conversion as `qte_factor()` |
| `DECK_ALPHA` | Deck-weight smoothing in `deck_weights()` |
| `HAND_SIZE` | Cards in each turn's fresh hand |
| `LINE_SET_C`, `LINE_ADHERENCE`, `LINE_ALT_WEIGHTS` | Opponent line tables and line-pick weights (§8.1) |

**Godot-only constants** (prototype UX, tuned in Godot):

| Name | Value | Notes |
|------|-------|-------|
| `PICKS_PER_TURN` | 3 | stances selected per turn |
| `STRAIGHT_DURATION` | 12.0 | seconds for all 3 picks |
| `PHASE_DURATION` | 4.0 | seconds per individual pick |
| `QTE_TIMING_WINDOW_BASE_MS` | 800 | base width of timing target zone |
| `QTE_TIMING_WINDOW_PER_GAP` | 50 | ms shrunk per level of opponent advantage |
| `QTE_TIMING_WINDOW_MIN_MS` | 200 | floor for timing target zone |
| `QTE_MASH_SPEED_PER_GAP` | 0.10 | press-rate multiplier per level gap |

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
signal progress_batch_done(player_progress, opponent_progress, cum_p, cum_o)
signal turn_ended(turn)
signal lap_began(phase, total)
signal match_ended(winner, player_name, opponent_name)   # winner may be "Tie"
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
@export var max_turns: int = 10         # planned race length in turns, one of RACE_LENGTHS; kappa = kappa_for_length(max_turns), not a lap's corner count
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
│   │   ├── PositionLabel (Label)             ← "1st" / "2nd" / "TIE"
│   │   ├── ProgressGapMeter (Control)        ← race progress gap (§10.2)
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
│   │   │   └── OpponentNameLabel (Label)
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
│   │   └── OpponentColumn (VBox)
│   │       ├── O1Panel (Panel)               ← colored bg per stance
│   │       │   └── O1Label (Label, stance name)
│   │       ├── O2Panel (Panel)               ← colored bg per stance
│   │       │   └── O2Label (Label, stance name)
│   │       └── O3Panel (Panel)               ← colored bg per stance
│   │           └── O3Label (Label, stance name)
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

**Goal:** A fresh stat-weighted hand each turn. GDScript port of `deck_weights()` in `sim/velocity_shift/equations.py` and `draw_weighted_hand()` in `sim/velocity_shift/combat.py`.

### 3.1 `Deck.gd`

**🤖 MCP creates** `scripts/Deck.gd` — all static, no deck state:

```gdscript
class_name Deck

static func deck_weights(pow: float, en: float, han: float) -> Array
    # Returns [w_atk, w_neu, w_def] (Attack = POW, Steady = HAN, Defend = EN), §3.2

static func draw_hand(pow: float, en: float, han: float,
                      rng: RandomNumberGenerator, n: int = HAND_SIZE) -> Array
    # n cards drawn i.i.d. (with replacement) from deck_weights(), one rng.rand_weighted() per card
    # Returns Array[Stance]

static func hand_stance_counts(hand: Array) -> Dictionary  # {ATTACK: N, DEFEND: N, NEUTRAL: N}
```

**Key rules:**
- The player gets a fresh `HAND_SIZE` hand every turn, plays 3 and the rest is dropped. Nothing carries over and nothing runs out.
- The opponent has no hand. It plays the line from `TurnTypeData.pick_line()` (§8.1).
- Turn RNG order, as in `match.py`: line pick first, then the player's hand, both from the match RNG.

### 3.2 Deck weights reference

```
total   = pow + en + han                     (shares are 1/3 each if total <= 0)
raw_atk = DECK_ALPHA × (pow / total) + (1 - DECK_ALPHA) / 3
raw_neu = DECK_ALPHA × (han / total) + (1 - DECK_ALPHA) / 3
raw_def = DECK_ALPHA × (en  / total) + (1 - DECK_ALPHA) / 3
w_x     = raw_x / (raw_atk + raw_neu + raw_def)
```

---

## 4. Straight Timer + Card Selection

**Goal:** 12s countdown, 3 sequential phases (entry/apex/exit), auto-pick on timeout.

> **Prototype timer, not the locked tell.** Austin locked the read on 2026-11-06 in `design/06-pattern-read.md`: the player locks all 3 cards up front, before corner playback, and the car tell is lane Entry (outside = Attack, center = Steady, inside = Defend), which can bluff by improper placement. Apex and Exit are inferred, with no explicit tell and no extra bluff layer. Shared Touge, Wangan, and Street tendencies are the intended inference, and the precise mapping is still TBD. The Aggressive, Defensive, and Precise rows in that doc are not that map. The steps below match the scripts that are already in the repo. They were not rewritten, and this decision did not pick 12s over the old 8s sentence in that doc.

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

func on_card_selected(stance):
    decrement count for that stance
    update button text
    if count == 0: disable button
    emit card_selected(stance)
    disable all buttons until next phase_pick

func on_pick_timeout(phase_index):
    auto-pick the stance with the highest remaining count
    (fallback: worst expected value)
```

---

## 5. Combat Math

**Goal:** Pure functions, a 1:1 port of the playable engine in `sim/velocity_shift/combat.py` (`resolve_turn`) and the Phi/tau functions in `sim/velocity_shift/equations.py` (0dd376a). A race is scored by progress: every clash adds progress to both cars, and the higher total at the end of the race wins. There are no HP or DP bars, knockouts, EN mitigation, rubber-banding or battle bonus.

### 5.1 `CombatResolver.gd`

**🤖 MCP creates** `scripts/CombatResolver.gd` — all static:

```gdscript
static func resolve_stance(a: Stance, b: Stance) -> StanceOutcome
    # Attack > Neutral > Defend > Attack

static func battle_winner(outcomes: Array) -> String
    # sum(outcome.values) — positive → "Player", negative → "Opponent", zero → "Tie"
    # Display only (ClashDisplay, turn log). It does not feed progress.

static func stat_shares(pow: float, en: float, han: float) -> Array
    # [total, pow / total, en / total, han / total]; [0, 1/3, 1/3, 1/3] when total <= 0

static func knot_window(r: float) -> float
    # W(r): piecewise-linear through the KNOT_WINDOW_105 knots,
    # flat below the first knot and above the last, capped at 1

static func kappa_for_length(race_length: int) -> float
    # KAPPA_BY_LENGTH[race_length]; any other length uses the closest key (no interpolation)

static func timing_value(q: float) -> float
    # tau(q), q clamped to [0, 1]:
    #   body = 1 - (1 - q)^2 if TAU_GAMMA <= 0 else q^TAU_GAMMA
    #   tau  = (1 - TAU_BETA) × body + TAU_BETA × q^TAU_P_TOP

static func clash_payoff(outcome: StanceOutcome, q: float) -> float
    # Phi(outcome, q), with t = timing_value(q):
    #   WIN     → W0 + (1 - W0) × t
    #   NEUTRAL → T_MAX × t
    #   LOSS    → L_MAX × t

static func clash_progress(outcome: StanceOutcome, q_time: float,
                           pow: float, en: float, han: float,
                           boss_total: float, kappa: float, scale_window: bool) -> float
    # [total, pow_s, en_s, han_s] = stat_shares(pow, en, han)
    # r     = total / boss_total            (1.0 if boss_total == 0)
    # V     = r^kappa
    # w     = knot_window(r) if scale_window else 1.0
    # q_eff = clamp(q_time × w × (1 + ETA × (han_s - 1/3)), 0, 1)
    # M     = 1 + MU × (pow_s - 1/3) on a WIN, else 1 + MU × (en_s - 1/3)
    # return V × clash_payoff(outcome, q_eff) × M

static func resolve_turn(player_stances: Array, opponent_stances: Array,
                         player: CombatantStats, opponent: CombatantStats,
                         player_q_time: float, opponent_q_time: float,
                         race_length: int) -> Dictionary
    # outcomes   = resolve_stance(p, o) per position (player's view); opponent's outcome = -outcome
    # boss_total = opponent.pow + opponent.en + opponent.han  → opponent V = 1, player V = r^kappa
    # kappa      = kappa_for_length(race_length)              (race_length = MatchConfig.max_turns, the planned race length, not the lap's corner count)
    # per clash i:
    #   player_clash_progress[i]   = clash_progress(outcome,  player_q_time,   player stats,   boss_total, kappa, true)
    #   opponent_clash_progress[i] = clash_progress(-outcome, opponent_q_time, opponent stats, boss_total, kappa, false)
    # player_progress / opponent_progress = sum of the 3 clashes (not an average)
    # Returns { outcomes, battle_winner, player_clash_progress, opponent_clash_progress,
    #           player_progress, opponent_progress }
```

**Inputs, as `match.py` feeds them:**
- `player_q_time` is the turn's single corner-long QTE score from `QTEController.stop()` divided by `QTE_NORMALIZER` (the same conversion as `cli.prompt_qte()` → `qte_factor()`), so it lies in [0, 1]. The same value is used for all 3 clashes. Don't pre-apply HAN or the window; `clash_progress` applies both.
- `opponent_q_time` is always `OPPONENT_QTE` (`AIQTE.opponent_q_time()`, §8.3).
- Both sides use the same effective timing, `q_eff = clamp(q × W × (1 + ETA × (han_share - 1/3)), 0, 1)`. For the player, `q = player_q_time` and `W = knot_window(r)`. For the opponent, `q = OPPONENT_QTE` and `W = 1` (`scale_window = false`). The opponent's HAN share still scales its timing.
- Every clash pays both cars: a win pays at least `W0`, while a tie and a loss pay `T_MAX` and `L_MAX` scaled by timing.

**Result** (`TurnManager._determine_winner()`, after `max_turns`): the higher of `player_cum_progress` and `opponent_cum_progress` wins, and equal totals are a `"Tie"`. Display shares are `pos_p = cum_p / (cum_p + cum_o)` (0.5 when both are 0), as `MatchResult.player_position` in `match.py`.

Reference: `sim/velocity_shift/equations.py` (`stat_shares`, `knot_window`, `kappa_for_length`, `timing_value`, `clash_payoff`, `clash_progress`) and `combat.py` `resolve_turn`. The sim keeps the old HP/DP path as `resolve_turn_legacy` behind `MatchConfig.legacy_hp_dp` for frozen checks; Godot does not port it.

> **Open question for Austin:** §7's level-gap QTE difficulty (`qte_difficulty()`) shrinks the timing zone and speeds up the mash when the opponent is stronger, while `knot_window(r)` already scales the player's timing by the stat ratio in the math. Keeping both would count the stat gap twice. §7 stays as written until you decide.

---

## 6. Turn Manager

**Goal:** One state machine orchestrates the whole game loop.

### 6.1 `TurnManager.gd`

**🤖 MCP creates** `scripts/TurnManager.gd` — attached to Battle root.

```
States:
┌──────────────────────────────────────────────────────────────────────┐
│  START         → load config, seed RNG, init visuals                 │
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
│  PROGRESS_BATCH → add progress, update gap meter, tween cars        │
│       ↓ (tweens done)                                               │
│                                                                      │
│  END_TURN       → lap check                                         │
│       ↓ (more turns)                    ↓ (max turns)              │
│  → STRAIGHT                           MATCH_COMPLETE               │
└──────────────────────────────────────────────────────────────────────┘
```

**State transition triggers:**

| State | Entered by | Exited by |
|-------|-----------|-----------|
| START | Scene loaded | Setup complete |
| STRAIGHT | Previous END_TURN (or START) | All 3 picks stored |
| CORNER_PLAYBACK | All 3 picks locked | QTE complete + 3 clashes resolved |
| PROGRESS_BATCH | Corner end | Tween animations done |
| END_TURN | Progress displayed | Lap check done |
| MATCH_COMPLETE | Max turns reached (higher progress total wins; equal = Tie) | — |

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

> **Open question for Austin:** this level-gap difficulty and `knot_window(r)` both penalize a stat gap (see §5.1).

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

**`TurnTypeData.gd`** — per-district line tables. Mirrors `LINE_SET_C` in `sim/velocity_shift/equations.py` exactly (copied into `scripts/globals.gd` like every other sim constant, never retuned here): district (`touge`, `wangan`, `street`) → corner code (`HP`, `CR`, `DR`, `IR`, `N90`, `CH`, `ES`, `SW`) → `[main, alt1, alt2]`, each an Entry/Apex/Exit string of `D` (Defend), `S` (Steady = `Stance.NEUTRAL`) and `A` (Attack). The alternates share main's Entry: `alt1` switches Apex+Exit, `alt2` switches Exit only. Once per corner (each turn), the opponent draws one whole line with a single weighted pick over `[main, alt1, alt2]` with weights `[LINE_ADHERENCE, (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt1"], (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt2"]]`. It's one draw, not an adherence roll followed by an alternate roll. It plays the chosen line exactly, and its hand never blocks it. When `equations.py` changes a line (for example the 6fc87d5 Street `N90` and Wangan `IR`/`SW` edits), only the mirrored table changes:

```gdscript
static func get_lines(district: String, corner: String) -> Array[String]
    # Returns LINE_SET_C[district][corner] = [main, alt1, alt2]

static func pick_line(district: String, corner: String, rng: RandomNumberGenerator) -> Array[Stance]
    # One weighted pick over [main, alt1, alt2] (weights above), once per corner;
    # one rng draw (rng.rand_weighted(weights)); hand never blocks the line
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
```

### 8.3 `AIQTE.gd`

**🤖 MCP creates** `scripts/AIQTE.gd`:

```gdscript
static func opponent_q_time() -> float
    # Returns OPPONENT_QTE (match.py). Fixed, not rolled: no level ratio, no noise,
    # no knot window, and no RNG draw. HAN is applied later inside
    # CombatResolver.clash_progress(), the same as for the player.
```

---

## 9. Tell System

**Goal:** Opponent face display with deception and bluff tells, crossfade schedule.

> **Prototype face draft, not the locked tell.** The locked car tell is lane Entry under the visual-gap rule in `design/06-pattern-read.md`. Apex and Exit are inferred, and the Touge, Wangan, and Street mapping for that inference is still TBD. This section documents the face scripts already in the repo. It does not adopt the Aggressive, Defensive, and Precise rows as that mapping, and it does not add an Apex/Exit tell, an extra bluff layer, or a probability for bluffing Entry by improper placement.

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

## 10. Position & Progress Display

**Goal:** Track cumulative race progress, show the progress gap on the race HUD, and show clash results. Austin, 2026-11-10: the race HUD shows the progress gap instead of HP bars.

### 10.1 `PositionTracker.gd`

**🤖 MCP creates** `scripts/PositionTracker.gd`:

```gdscript
var player_total_progress: float = 0.0
var opponent_total_progress: float = 0.0

func add_turn_progress(player_progress: float, opponent_progress: float)
    # Accumulate (match.py: result.player_total_progress += turn progress)
    # Emit position label: "1st" / "2nd", or "TIE" on equal totals

func get_progress_gap() -> float
    # return player_total_progress - opponent_total_progress

func get_lead() -> float
    # total = player_total_progress + opponent_total_progress
    # return 0.0 if total == 0 else (player_total_progress - opponent_total_progress) / total
    # = pos_p - pos_o (`unapproved/gordon/playtest-state-spec.md` §0.1), always in [-1, 1]
```

### 10.2 `ProgressGapDisplay.gd`

**🤖 MCP creates** `scripts/ProgressGapDisplay.gd`, driving `TopBar/ProgressGapMeter`:

```gdscript
func animate_gap(new_lead: float)
    # Tween ProgressGapMeter from the previous lead to new_lead (PositionTracker.get_lead())
    # Centre = level; the fill grows toward the player's side when ahead, the rival's side when behind
    # Duration: 0.8s
    # Flash the "1st" / "2nd" / "TIE" label update
```

The meter is scaled to the normalized lead `(cum_p - cum_o) / (cum_p + cum_o)`, the same shares as `MatchResult.player_position` in `match.py`, so it needs no full-scale value and can't overflow. The drawn car spacing (§11) takes the same `lead`.

> **Open question for Austin:** whether the race HUD prints a number (the debug HUD prints `lead`) and how a tie reads.

### 10.3 `ClashDisplay.gd`

**🤖 MCP creates** `scripts/ClashDisplay.gd`:

```gdscript
const COLORS = {
    ATTACK:  Color("#16a34a"),
    DEFEND:  Color("#dc2626"),
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

**Goal:** Each car has a straight Z-offset and corner path traversal. AnimationTree blends stance body language.

> **Drawn spacing is not the progress gap.** `snap_to_gap` in `scripts/CarAnimator.gd` still lerps a symmetric Z range from the gap fraction (`lerp(-5.0, 5.0, …)`). That script was not changed. The locked presentation rule is in `design/06-pattern-read.md`: when the player is behind, the rival is drawn only as far ahead as keeps lane and Entry readable from the fixed rear third-person player camera (no distance number approved); when the player is ahead, the trailer recedes in the top-center mirror with no matching rear cap. Actual cumulative progress is unchanged. Do not read a large lead's exact size off the visible spacing.

### 11.1 `CarAnimator.gd`

**🤖 MCP creates** `scripts/CarAnimator.gd` — one per car:

```gdscript
# ─── Straight phase ───────────────────────────────────────────────

var straight_base_z: float = 0.0

func snap_to_gap(gap: float, max_gap: float)
    # Input: gap = PositionTracker.get_lead(), max_gap = 1.0 (the lead is already normalized, §10.2)
    # PROTOTYPE ONLY (still what CarAnimator.gd does). Not the locked visual gap.
    # The symmetric ±5 range caps the trailer the same way as the leader; the
    # locked rule caps only how far ahead of the player the rival is drawn.
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
    # PROTOTYPE ONLY. The 10% path offset is not an approved draw distance.
    # Locked spacing is the visual-gap rule in design/06-pattern-read.md (no number).
    # Read the current lead from PositionTracker.get_lead()
    # Set progress_offset = lead × 0.1 (10% path offset per full lead)
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
    # PROTOTYPE face/stance crossfade. Not an explicit Apex/Exit tell.
    # Locked tell is lane Entry (design/06-pattern-read.md).
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

- `turn_state_changed(STRAIGHT)`: `snap_to_gap(...)` with `PositionTracker.get_lead()`
- `turn_state_changed(CORNER_PLAYBACK)`: `begin_corner_traversal(...)`
- `clash_resolved(position, ...)`: `play_surge()` on winner / `play_drop()` on loser
- `lead_changed`: `play_overtake()` on overtaking car
- `turn_state_changed(PROGRESS_BATCH)`: `end_corner_traversal()`

---

## 12. Camera

**Goal:** Fixed rear third-person camera on the player. The rival's drawn gap is asymmetric so Entry stays readable when the player is behind, and gets harder to read in the mirror when the player is ahead. Rule: `design/06-pattern-read.md` (Lane Entry and visual gap). Actual progress, position, and the win condition do not follow the drawn spacing.

### 12.1 Locked view (2026-11-06)

- The race view used to read Entry is a fixed rear third-person camera on the **player**. It is not placed behind both cars, and it does not pull back to keep an uncapped leader in shot.
- **Player behind:** cap how far ahead the rival is drawn so that rival's lane and Entry (outside = Attack, center = Steady, inside = Defend, relative to the next corner) stay readable. No distance number is approved. The cap is draw distance only. It is not a real-gap cap, and not a scoring or AI change. Visible spacing does not show the exact size of a large real lead.
- **Player ahead:** the trailing rival recedes in the top-center rear-view mirror. Do not cap that recession to match the forward cap. Headlights and lane get harder to read with distance. That loss of Entry information is intentional. Do not add a HUD lane marker or enlarge the lamps to undo it.
- Corner-playback camera paths later in this guide are the cinematic after the line is locked. They do not replace this view as the one Entry is read from, and they do not authorize a symmetrical rear cap.
- Display settings are unchanged: 640×480, viewport stretch, keep aspect, as in §1.1 and `project.godot`. A higher-resolution / CRT trial was an experiment only.

### 12.2 `BattleCamera.gd`

**🤖 MCP creates** `scripts/BattleCamera.gd` — attached to Camera3D.

The sketch below is the prototype chase cam. "Behind both cars" is not the locked view; §12.1 is.

```gdscript
# During STRAIGHT (prototype sketch — locked view is §12.1, fixed on the player):
#   - Rear third-person on the player, looking down the straight
#   - FOV ~65°, slight vertical tilt for speed feel
# During CORNER_PLAYBACK:
#   - Rotate ~15° around Y axis into corner direction
#   - FOV ~55°, closer to cars
#   - Subtle X roll to follow road camber
# During PROGRESS_BATCH:
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
| STRAIGHT | StraightRoad | Drawn spacing follows the visual-gap rule in 06 (not a 1:1 progress offset; prototype `snap_to_gap` is still symmetric) | Fixed rear third-person on the player |
| CORNER_PLAYBACK | CornerRoad | Pathing along Curve3D | Authored camera path |
| PROGRESS_BATCH | CornerRoad | Static at corner exit | Same as corner |
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
8. Progress computed for all 3 clashes (both cars) → progress gap updated
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
5. All 3 phases resolve → progress added → overtake if applicable
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
5. Watch the progress gap meter + cubes update
6. Match ends at `max_turns` → winner displayed
7. Edit Godot-only constants in `globals.gd` → **F5** to rerun. Combat constants are mirrored from `sim/velocity_shift/equations.py` and change only there (§15.2)

### 15.2 Quick-tune constants

Combat constants are tuned in Barry's sim, not in Godot. Austin and Barry sign off on the numbers there, and Godot copies them into `globals.gd` by name:

| Constant (`equations.py`) | Effect |
|----------|--------|
| `KNOT_WINDOW_105` | How much of the player's timing lands at each stat ratio `r` |
| `KAPPA_BY_LENGTH` | How strongly the stat ratio scales progress, per race length |
| `OPPONENT_QTE` | How well the opponent times |
| `W0`, `T_MAX`, `L_MAX` | Progress for a win, tie and loss relative to a perfect win |
| `TAU_BETA`, `TAU_P_TOP`, `TAU_GAMMA` | Shape of the timing curve tau(q) |
| `MU` | How much POW share boosts wins and EN share boosts ties/losses |
| `ETA` | How much HAN share boosts effective timing |
| `DECK_ALPHA` | Deck smoothing (higher = more even) |

Godot-only feel constants, tuned here:

| Constant | Effect | Recommended range |
|----------|--------|-------------------|
| `STRAIGHT_DURATION` | Seconds to pick 3 stances | 8.0 – 12.0 |
| `QTE_TIMING_WINDOW_BASE_MS` | Base timing target width | 600 – 1000 |

### 15.3 Tuning flow

1. **Run vs Wild** (level gap favors you) — should feel dominant but not boring
2. **Run vs Lieutenant** (near parity) — should feel tense, each pick matters
3. **Run vs Boss** (level gap favors them) — should feel like an uphill fight
4. **Adjust** a Godot-only constant, or report a combat number that feels wrong to Barry
5. **Rerun** — no restart needed, just F5

### 15.4 Adding real art later

When gameplay is tuned to your liking:

1. Replace `PlayerCube` / `OpponentCube` BoxMesh with imported car `.glb`
2. Replace ground plane with road meshes (straight + corner variants)
3. Replace the progress gap meter, timer bars and `Button` textures with styled assets
4. Add corner cinematic (Path3D traversal, camera choreography)
5. Import face textures and wire into FaceStack TextureRects
6. The gameplay scripts (`Deck.gd`, `CombatResolver.gd`, `TurnManager.gd`, etc.) need zero changes

### 15.5 Edge cases

- **Ties:** equal progress totals are a tie (`"Tie"`), as in `match.py`; there is no opponent tiebreaker
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
  globals.gd               — enums + constants
  SignalBus.gd             — 12 signals
  CombatantStats.gd        — resource
  MatchConfig.gd           — resource
  Deck.gd                  — fresh i.i.d. hand from deck_weights()
  StraightTimer.gd         — 12s, 3 phases
  CardHandUI.gd            — 3 buttons + counts
  CombatResolver.gd        — Phi/tau progress math
  TurnManager.gd           — state machine
  QTEController.gd         — mash + timing
  AIPicker.gd              — EV scoring
  AIQTE.gd                 — opponent q_time (OPPONENT_QTE)
  TurnTypeData.gd          — stance sequences + QTE type
  ArchetypeData.gd         — comfort/weak zones
  PersonalityData.gd       — 5 personalities, 3 phases each
  TrackData.gd             — circuit layouts
  TellGenerator.gd         — deception flow
  FaceController.gd        — face display + tell overlay
  PositionTracker.gd       — cumulative progress + lead
  ProgressGapDisplay.gd    — progress gap meter tween
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
  Prototype flow (scripts unchanged). Locked tell is lane Entry under the
  visual-gap rule in design/06-pattern-read.md: 3 cards lock up front,
  Apex/Exit are inferred (Touge/Wangan/Street map still TBD; the old
  archetype rows are not that map), and a rival ahead of the player is drawn only as
  far as that lane stays readable. A rival behind recedes in the mirror.
  Car drives toward the corner. The rival shows lane Entry (not a separate Apex or Exit tell).
  Three opponent faces reveal SEQUENTIALLY with smooth crossfade
  (earlier face draft, not an Apex/Exit tell):
    0s-4s:   ENTRY face shown + tell (if deceptive)
             Player picks entry stance
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
  QTE stops. Progress computed for all 3 clashes (both cars) → progress gap updated
  Lead change check:
    - If changed → overtake animation (0.5-1s) + camera swing
    - If unchanged → skip
  Progress gap meter updates → position label updates
  Car positions tween. Drawn spacing follows the visual-gap rule, not the raw progress magnitude
  → Unload corner segment
  → Next turn: line pick, then a fresh hand
  → Load next corner segment
  → Loop back to STRAIGHT (next corner)
```

### Mapping to Python reference

| Phase | Python equivalent |
|-------|-------------------|
| Straight (12s) | No equivalent — pure Godot UX |
| 3× CARD_PICK | `match.py` sequential pick loop (on straight) |
| 3× CLASH resolve | `equations.resolve_stance()` (in corner, batched) |
| 1× QTE (corner-long) | `cli.prompt_qte()` (score / `QTE_NORMALIZER` = player `q_time`); opponent uses `OPPONENT_QTE` |
| PROGRESS batch | `combat.resolve_turn()` (Phi/tau progress per clash, 3 summed) + `match.py` running totals |
| Hand draw | `combat.draw_weighted_hand()` (`deck_weights()`, `HAND_SIZE`), after `combat.pick_line()` |

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
| `progress_batch_done(player_progress, opponent_progress, cum_player, cum_opponent)` | `float×4` | TurnManager | Turn progress computed, gap meter starts animating |
| `turn_ended(turn)` | `int` | TurnManager | Turn complete, ready for next straight |
| `lap_began(phase, total)` | `int, int` | TurnManager | Phase boundary crossed |
| `match_ended(winner, player_name, opponent_name)` | `String×3` | TurnManager | Max turns reached; `winner` has the higher progress total, or is `"Tie"` |

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
     → TurnTypeData.pick_line() first, then Deck.draw_hand(player stats, _rng): fresh HAND_SIZE hand
       → compute stance counts → CardHandUI: update button labels
     → StraightTimer: start 12s countdown
     → emit straight_started(...)
     → AnimationTreeBlendManager: begin stance_blend cycle
       (0-4s: entry_weight, 4-8s: apex_weight, 8-12s: exit_weight)
     → FaceStack: alpha crossfade follows same schedule

2. PICK_ENTRY (0-4s)
     → emit phase_pick(0, "ENTRY")
     → CardHandUI: enable buttons with count > 0
     a. Player clicks → emit card_selected(stance) → store
     b. OR 4s expires → emit phase_pick_timeout(0) → auto-pick → store
     → CardHandUI: disable, grey out consumed count
     → PhasePromptLabel: "APEX — Pick your stance"

3. PICK_APEX (4-8s)
     → same flow as ENTRY

4. PICK_EXIT (8-12s)
     → same flow as ENTRY

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

7. TurnManager: state = PROGRESS_BATCH
     → player_q_time = qte_score / QTE_NORMALIZER; opponent_q_time = AIQTE.opponent_q_time()
     → CombatResolver.resolve_turn(...): clash_progress for each car on all 3 clashes, summed
       (q_eff = clamp(q × W × HAN term, 0, 1) on both sides: player W = knot_window(r);
        opponent q = OPPONENT_QTE, W = 1; kappa from max_turns)
     → PositionTracker: accumulate progress
     → CarAnimator: tween Z offsets to the new lead
     → ProgressGapDisplay: animate gap meter
     → emit progress_batch_done(...)

8. TurnManager: state = END_TURN
     → Check lap boundary → emit lap_began(...)
     → If turns < max_turns → STRAIGHT
     → If turns >= max_turns → emit match_ended(...) (higher progress total wins; equal = "Tie")
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
| Progress gap meter (frame, fill) | 2 |
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

For each corner, the opponent's 3 stances come from the district line table, `LINE_SET_C[district][corner]` in `sim/velocity_shift/equations.py` (mirrored in `scripts/globals.gd`, read through `TurnTypeData.pick_line()`). The district is the race's `district_id`, and the corner code comes from `TrackData`. The locked car tell is lane Entry only (`design/06-pattern-read.md`), which is why every alternate shares main's Entry.

```
# Street race, corner N90:
lines  = LINE_SET_C["street"]["N90"]      # [main, alt1, alt2]
a       = LINE_ADHERENCE
weights = [a, (1 - a) * LINE_ALT_WEIGHTS["alt1"], (1 - a) * LINE_ALT_WEIGHTS["alt2"]]
line    = lines[rng.rand_weighted(weights)]   # one draw per corner, played exactly
stances = [line[0], line[1], line[2]]     # Entry, Apex, Exit (D/S/A)
```

Make the draw from the match `RandomNumberGenerator` so a playtest dump's Block C seed and RNG state reproduce the opponent's picks in Godot. Godot's generator isn't Python's, so this matches the sim's line rates, not its exact rolls.

## Appendix H: Notes / Gotchas

- **Stance naming:** UI displays "STEADY" but the enum is `Stance.NEUTRAL`. Button label and all UI text uses "STEADY"; all logic uses NEUTRAL.
- **Hands:** a fresh `HAND_SIZE` hand each turn, drawn i.i.d. from `deck_weights()`; pick 3, the rest is dropped. No persistent deck, no piles.
- **Opponent cards:** the picked line, played exactly; no opponent hand.
- **No DNF / knockout** — match always runs to max_turns, then the higher progress total wins.
- **Race length sets kappa:** `max_turns` (default 10) is the planned race length, one of `RACE_LENGTHS`; kappa = `kappa_for_length(max_turns)`, never the lap's corner count. Any other length snaps to the nearest `KAPPA_BY_LENGTH` key.
- **Ties:** equal progress totals are a tie; no opponent tiebreaker.
- **Car position in 3D:** drawn spacing only. Cumulative progress, position, and the win condition stay on the real gap (`design/06-pattern-read.md`, Lane Entry and visual gap). A capped lead ahead of the player is not the exact large-lead magnitude. The trailer is not given a matching cap. `CarAnimator.gd` still uses a symmetric Z lerp; that code was not updated with the rule.
- **AnimationTree blend:** 7 animations + 3-way blend node = smooth stance transitions for any 3-stance sequence. No per-combination baking.
- **Face crossfade:** 3 stacked TextureRects with alpha driven by same blend schedule as the car. 4th overlay layer for bluff tell.
- **Meta-archetypes:** 3 face types (Scowling/Grinning/Focused) shared by hard+soft pairs. 9 face textures + 9 tell overlays total.
- **Future screens:** Menu → Isometric Overworld → Race → Battle → Results → Overworld. Design scene loading (StageManager) with this in mind.
- **Skill points are in v1** (see 08); the tree layout is still undecided. Mods system design is separate.
- **Sound/music:** deferred. Design signal hooks for future audio integration.
