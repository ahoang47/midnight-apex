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
enum Stance { POW, EN, HAN }
enum StanceOutcome { WIN = 1, DRAW = 0, LOSS = -1 }
enum EncounterType { WILD, LIEUTENANT, BOSS }
enum PhaseType { AGGRESSIVE, REACTIVE, UNPREDICTABLE }
enum QteType { MASH, TIMING }
```

**Combat constants** (copied from `sim/velocity_shift/equations.py` by name and never retuned in Godot; the values live only in the sim, Barry's source of truth):

| Name | Notes |
|------|-------|
| `QTE_ZONE_BASE_MS` | Presentation unit for the visible QTE zone. Godot `QTE_TIMING_WINDOW_BASE_MS` is this constant, not a separately tuned value (`equations.py:130–133`) |
| `QTE_ZONE_WIDTH_105` | `(r, width/w0)` knots for the visible zone; used by `qte_zone_width(r, window_mod)` (`equations.py:137`, function at `:338`) |
| `QTE_SKILL_SIGMA_OVER_A0` | PLACEHOLDER skill σ (units of the default half-width a0) until playtest; used by `expected_hit_quality` / `raw_qte_score` (`equations.py:149`, marked PLACEHOLDER) |
| `QTE_SKILL_TARGET_E` | Target E[s] at the default zone for the named placeholder profiles (`equations.py:148`) |
| `KNOT_WINDOW_105` | LEGACY `(r, W)` knots for `knot_window(r)`: `winrate_n4000.json` / progression oracle, and the generator of the zone table. Not used by `clash_progress` / `resolve_turn` (`equations.py:125`, `knot_window` at `:256`) |
| `KAPPA_BY_LENGTH`, `KAPPA_HEAT_MULT` | Stat-gap leverage `V = r^kappa`, kappa = `kappa_for_length(T)` = `KAPPA_BY_LENGTH[T] × KAPPA_HEAT_MULT[T]` (heat system, 2026-11-13) |
| `RACE_LENGTHS` | Race lengths that have a `KAPPA_BY_LENGTH` entry |
| `OPPONENT_QTE` | Opponent raw timing; unchanged (HAN still applies; no visible-zone width) (`equations.py:129`, `combat.py:75`) |
| `W0`, `T_MAX`, `L_MAX` | Phi payoff: win at q = 0, tie at q = 1, loss at q = 1 |
| `TAU_BETA`, `TAU_P_TOP`, `TAU_GAMMA` | tau(q): top-bonus share, top-bonus sharpness, body shape |
| ~~`MU`~~, ~~`ETA`~~ | **Removed 2026-11-13.** Replaced by `STAT_M_W` (payoff × (1 + `STAT_M_W` × (share of the stance played − 1/3)), all three stats); no HAN timing modifier |
| `QTE_NORMALIZER` | QTE score (1–10) → `q_time`, the same conversion as `qte_factor()` |
| ~~`DECK_ALPHA`~~, ~~`HAND_SIZE`~~ | **Removed 2026-11-13** with the card draw. Port the heat section instead: `HEAT_ORDER`, `CORNER_HEAT_COST`, `CORNER_HEAT_PASSIVE`, `HEAT_*`, `OVERRUN_*`, `LIMP_MULT`, `STAT_M_W`, `BOSS_HEAT_*`, `MOD_CAP_FRACTION`, and the derived calibration `heat.avg_heat_demand()` / `heat.track_wear()` (see `design/02-equations-reference.md`, heat/load section) |
| `LINE_SET_C`, `LINE_ADHERENCE`, `LINE_ALT_WEIGHTS` | Opponent line tables and line-pick weights (§8.1) |

**Godot-only constants** (prototype UX, tuned in Godot):

| Name | Value | Notes |
|------|-------|-------|
| `PICKS_PER_TURN` | 3 | stances selected per turn |
| `STRAIGHT_DURATION` | 12.0 | seconds for all 3 picks |
| `PHASE_DURATION` | 4.0 | seconds per individual pick |

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
@export var qte_window_mod: float = 0.0  # multiplicative bonus on qte_zone_width(r); models.py:152
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
│   │       ├── PowButton (Button)
│   │       ├── EnButton (Button)
│   │       └── HanButton (Button)
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

> **SUPERSEDED 2026-11-13 (Barry):** the card draw was deleted from the sim; Austin approved the heat/load resource system (resources-v4b G2). There is no hand: each clash the player picks any stance whose gauge is not locked. The sim reference is `sim/velocity_shift/heat.py` (`HeatGauges`, `boss_stance`, `track_wear`) and `match.py`; rules in `design/02-equations-reference.md` (heat/load section). This section is left for Gordon to replace.

**Goal:** A fresh stat-weighted hand each turn. GDScript port of `deck_weights()` in `sim/velocity_shift/equations.py` and `draw_weighted_hand()` in `sim/velocity_shift/combat.py`.

### 3.1 `Deck.gd`

**🤖 MCP creates** `scripts/Deck.gd` — all static, no deck state:

```gdscript
class_name Deck

static func deck_weights(pow: float, en: float, han: float) -> Array
    # Returns [w_pow, w_han, w_en], §3.2

static func draw_hand(pow: float, en: float, han: float,
                      rng: RandomNumberGenerator, n: int = HAND_SIZE) -> Array
    # n cards drawn i.i.d. (with replacement) from deck_weights(), one rng.rand_weighted() per card
    # Returns Array[Stance]

static func hand_stance_counts(hand: Array) -> Dictionary  # {POW: N, EN: N, HAN: N}
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

> **Prototype timer, not the locked tell.** Austin locked the read on 2026-11-06 in `design/06-pattern-read.md`: the player locks all 3 cards up front, before corner playback, and the car tell is the Entry lane, which shows the Entry stance (on-screen lane-to-stat map: `design/02-equations-reference.md` §6.0) and can bluff by improper placement. Apex and Exit are inferred, with no explicit tell and no extra bluff layer. Shared Touge, Wangan, and Street tendencies are the intended inference, and the precise mapping is still TBD. The Aggressive, Defensive, and Precise rows in that doc are not that map. The steps below match the scripts that are already in the repo. They were not rewritten, and this decision did not pick 12s over the old 8s sentence in that doc.

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
    PowButton.text = "POW (x" + str(counts[POW]) + ")"
    EnButton.text = "EN (x" + str(counts[EN]) + ")"
    HanButton.text = "HAN (x" + str(counts[HAN]) + ")"
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

**Goal:** Pure functions, a 1:1 port of the playable engine in `sim/velocity_shift/combat.py` (`resolve_turn`) and the Phi/tau functions in `sim/velocity_shift/equations.py` (4cb5401, including the approved qte-v1 visible QTE zone). A race is scored by progress: every clash adds progress to both cars, and the higher total at the end of the race wins. There are no HP or DP bars, knockouts, EN mitigation, rubber-banding or battle bonus.

### 5.1 `CombatResolver.gd`

**🤖 MCP creates** `scripts/CombatResolver.gd` — all static:

```gdscript
static func resolve_stance(a: Stance, b: Stance) -> StanceOutcome
    # POW > HAN > EN > POW; same stance → DRAW

static func battle_winner(outcomes: Array) -> String
    # sum(outcome.values) — positive → "Player", negative → "Opponent", zero → "Tie"
    # Display only (ClashDisplay, turn log). It does not feed progress.

static func stat_shares(pow: float, en: float, han: float) -> Array
    # [total, pow / total, en / total, han / total]; [0, 1/3, 1/3, 1/3] when total <= 0

static func knot_window(r: float) -> float
    # LEGACY hidden W(r): piecewise-linear through the KNOT_WINDOW_105 knots,
    # flat below the first knot and above the last, capped at 1.
    # Not used by clash_progress / resolve_turn. Kept only to match the
    # sim: winrate_n4000.json / progression oracle, and as the generator
    # of qte_zone_width() (equations.py:256–268).

static func expected_hit_quality(sigma_over_a0: float, width_over_w0: float) -> float
    # E[s] for one timing press at a zone width (fraction of QTE_ZONE_BASE_MS).
    # Skill σ values are PLACEHOLDER until playtest (QTE_SKILL_SIGMA_OVER_A0).
    # equations.py:271

static func qte_zone_width(r: float, window_mod: float = 0.0) -> float
    # Visible zone width as a fraction of QTE_ZONE_BASE_MS, at the race's
    # FIXED r (no mid-race change). window_mod is MatchConfig.qte_window_mod,
    # a multiplicative bonus (0.10 = +10% of the current zone). Slot
    # competition and the 105%-all-slots rule are not applied (upcoming
    # slot sim). equations.py:338

static func raw_qte_score(r: float, profile, q_time, window_mod: float = 0.0) -> float
    # Expected raw QTE score at the race's fixed r (no HAN, no knot_window).
    # A named PLACEHOLDER profile (MatchConfig.player_qte_profile) or an
    # explicit player_timing is evaluated at qte_zone_width(r, window_mod).
    # A live player's entered QTE is already the raw score at the visible
    # zone (CLI). equations.py:361; match.py:180–196; models.py:145–152

static func kappa_for_length(race_length: int) -> float
    # KAPPA_BY_LENGTH[race_length]; any other length uses the closest key (no interpolation)

static func timing_value(q: float) -> float
    # tau(q), q clamped to [0, 1]:
    #   body = 1 - (1 - q)^2 if TAU_GAMMA <= 0 else q^TAU_GAMMA
    #   tau  = (1 - TAU_BETA) × body + TAU_BETA × q^TAU_P_TOP

static func clash_payoff(outcome: StanceOutcome, q: float) -> float
    # Phi(outcome, q), with t = timing_value(q):
    #   WIN     → W0 + (1 - W0) × t
    #   DRAW    → T_MAX × t
    #   LOSS    → L_MAX × t

static func clash_progress(outcome: StanceOutcome, q_time: float,
                           pow: float, en: float, han: float,
                           boss_total: float, kappa: float) -> float
    # [total, pow_s, en_s, han_s] = stat_shares(pow, en, han)
    # r     = total / boss_total            (1.0 if boss_total == 0)
    # V     = r^kappa
    # q_eff = clamp(q_time × (1 + ETA × (han_s - 1/3)), 0, 1)
    #         no knot_window factor (equations.py:426–433)
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
    #   player_clash_progress[i]   = clash_progress(outcome,  player_q_time,   player stats,   boss_total, kappa)
    #   opponent_clash_progress[i] = clash_progress(-outcome, opponent_q_time, opponent stats, boss_total, kappa)
    # player_progress / opponent_progress = sum of the 3 clashes (not an average)
    # Returns { outcomes, battle_winner, player_clash_progress, opponent_clash_progress,
    #           player_progress, opponent_progress }
```

**Inputs, as `match.py` feeds them:**
- `player_q_time` is the turn's single corner-long raw QTE score from `QTEController.stop()` divided by `QTE_NORMALIZER` (the same conversion as `cli.prompt_qte()` → `qte_factor()`), so it lies in [0, 1]. The same value is used for all 3 clashes. It is already the raw score at the visible zone for the race's fixed r (and any `qte_window_mod`); don't pre-apply HAN. `clash_progress` applies only the HAN term (`combat.py:71–75`, `equations.py:426–428`). A simulated player uses `raw_qte_score` at that same fixed r (`match.py:180–196`).
- `opponent_q_time` is always `OPPONENT_QTE` (`AIQTE.opponent_q_time()`, §8.3). The opponent is unchanged: no visible-zone width, HAN still applies (`combat.py:75`, `equations.py:163–164`).
- Both sides use the same effective timing, `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)`, with no `knot_window` factor (`equations.py:160`, `:426–433`). For the player, `raw_qte` is `player_q_time`. For the opponent, `raw_qte` is `OPPONENT_QTE`. The opponent's HAN share still scales its timing.
- The stat gap lives in the visible zone width `qte_zone_width(r, window_mod)` (`equations.py:338`), evaluated at the race's FIXED r (it does not change mid-race). `MatchConfig.qte_window_mod` (`models.py:152`) widens that zone. `KNOT_WINDOW_105` / `knot_window` are legacy for the oracle only (and as the generator of the zone table); they are not used in `clash_progress` or `resolve_turn` (`equations.py:115–116`, `:256–260`).
- Every clash pays both cars: a win pays at least `W0`, while a tie and a loss pay `T_MAX` and `L_MAX` scaled by timing.

**Result** (`TurnManager._determine_winner()`, after `max_turns`): the higher of `player_cum_progress` and `opponent_cum_progress` wins, and equal totals are a `"Tie"`. Display shares are `pos_p = cum_p / (cum_p + cum_o)` (0.5 when both are 0), as `MatchResult.player_position` in `match.py`.

Reference: `sim/velocity_shift/equations.py` (`stat_shares`, `qte_zone_width` `:338`, `raw_qte_score` `:361`, `expected_hit_quality` `:271`, `kappa_for_length`, `timing_value`, `clash_payoff`, `clash_progress` `:415`; legacy `knot_window` `:256`) and `combat.py` `resolve_turn` (`:71–75`, `:122–131`). The sim keeps the old HP/DP path as `resolve_turn_legacy` behind `MatchConfig.legacy_hp_dp` for frozen checks; Godot does not port it.

> **Resolved (Austin, 2026-11-11, 8:48 PM PT):** "Yeah QTE difficulty is scaled through the visibile zone. I don't see double dipping there." QTE difficulty is scaled only through the visible zone width `qte_zone_width(r, window_mod)` at the race's fixed r, plus `MatchConfig.qte_window_mod`. The old level-gap `qte_difficulty()` scaling is dropped; see §7.

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
func start(qte_type: QteType, zone_width_over_w0: float):
    # Show QTEOverlay
    # zone_width_over_w0 comes from qte_zone_width(r, MatchConfig.qte_window_mod)
    # at the race's FIXED r (equations.py:338). No mid-race change, and no
    # extra level-gap shrink or mash-speed scale.
    # Timing target width in ms = zone_width_over_w0 × QTE_ZONE_BASE_MS
    #   (equations.py:130–133; Godot presentation name QTE_TIMING_WINDOW_BASE_MS).
    # Mash: count presses; fills MashIndicator TextureProgress over ~3-4s
    # Timing: moving marker across that target zone
    #   Multiple successful presses increase score
    # Read QTE type from TurnTypeData.get_qte_type(turn_type, player_stance)
    # Runs ~3-4s (concurrent with clash resolution)

func stop() -> float:
    # Mash: final score = fill% × 10, normalized 1.0–10.0
    # Timing: final score = (successful_presses / total_opportunities) × 10
    # Return final score (1.0–10.0)
```

**Zone width** (this is the QTE difficulty):

```gdscript
# CombatResolver.qte_zone_width(r, window_mod)  — equations.py:338
# timing_window_ms = qte_zone_width(r, window_mod) × QTE_ZONE_BASE_MS
#   (equations.py:130–133)
```

> **Resolved (Austin, 2026-11-11, 8:48 PM PT):** "Yeah QTE difficulty is scaled through the visibile zone. I don't see double dipping there." Difficulty is scaled only through this visible zone, plus `MatchConfig.qte_window_mod`. The old level-gap `qte_difficulty()` (and its ms table) is dropped.

### 7.2 QTE Type lookup

One continuous QTE per corner. Type determined by `(turn_type × stance)`:

| Turn Type | POW | EN | HAN |
|-----------|-----|----|-----|
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

**`TurnTypeData.gd`** — per-district line tables. Mirrors `LINE_SET_C` in `sim/velocity_shift/equations.py` exactly (copied into `scripts/globals.gd` like every other sim constant, never retuned here): district (`touge`, `wangan`, `street`) → corner code (`HP`, `CR`, `DR`, `IR`, `N90`, `CH`, `ES`, `SW`) → `[main, alt1, alt2]`, each an Entry/Apex/Exit string of `P` (`Stance.POW`), `E` (`Stance.EN`) and `H` (`Stance.HAN`); letters renamed from A/D/S on 2026-11-12 (map: `design/02-equations-reference.md` §6.0). The alternates share main's Entry: `alt1` switches Apex+Exit, `alt2` switches Exit only. Once per corner (each turn), the opponent draws one whole line with a single weighted pick over `[main, alt1, alt2]` with weights `[LINE_ADHERENCE, (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt1"], (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt2"]]`. It's one draw, not an adherence roll followed by an alternate roll. It plays the chosen line exactly, and its hand never blocks it. When `equations.py` changes a line (for example the 6fc87d5 Street `N90` and Wangan `IR`/`SW` edits), only the mirrored table changes:

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
    # Returns OPPONENT_QTE (match.py:200). Opponent unchanged: fixed, not
    # rolled; no level ratio, no noise, no visible-zone width, and no RNG
    # draw. HAN is applied later inside CombatResolver.clash_progress(),
    # the same as for the player (equations.py:163–164, combat.py:75).
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

| Face Type | POW expression | POW tell | EN expression | EN tell | HAN expression | HAN tell |
|-----------|---------------|----------|----------------|----------|----------------|----------|
| A — Scowling (POW) | Bared teeth, furrowed brow | Mouth closes over bared teeth briefly | Tight jaw, narrowed eyes | Eyes flick wide then narrow back | Flat stare, relaxed brow | Brow drops and returns |
| B — Grinning (EN) | Wide smile, raised brows | Raised brows drop flat | Thin smile, watchful eyes | Eyes shift to the side | Half-smirk, steady gaze | Half-smirk goes straight |
| F — Focused (HAN) | Intense stare, sharp focus | Intense gaze loses focus, drifts | Cocky smirk, raised brow | Raised brow drops flat | Relaxed half-smile | Half-smile vanishes |

### 9.3 `FaceController.gd`

**🤖 MCP creates** `scripts/FaceController.gd`:

```gdscript
func set_face_sequence(expressions: Array[Dictionary], face_type: String)
    # Called at straight start with 3 (stance, is_bluff) tuples
    # Load the correct POW/EN/HAN textures for this face_type
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
    POW:     Color("#2CB84A"),  # green — art_direction.md:252 (B.5)
    EN:      Color("#E8282C"),  # red — art_direction.md:252 (B.5)
    HAN:     Color("#F0C828"),  # yellow, dark text — art_direction.md:252 (B.5)
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
- **Player behind:** cap how far ahead the rival is drawn so that rival's lane and Entry stance stay readable. No distance number is approved. The cap is draw distance only. It is not a real-gap cap, and not a scoring or AI change. Visible spacing does not show the exact size of a large real lead.
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
| `QTE_ZONE_BASE_MS`, `QTE_ZONE_WIDTH_105` | Visible QTE zone width at the race's fixed r (`qte_zone_width`). Godot `QTE_TIMING_WINDOW_BASE_MS` is the presentation name for `QTE_ZONE_BASE_MS` (`equations.py:130–133`), not a separately tuned range |
| `QTE_SKILL_SIGMA_OVER_A0` | PLACEHOLDER skill σ for `expected_hit_quality` / `raw_qte_score` until playtest |
| `KNOT_WINDOW_105` | LEGACY only: winrate oracle and generator of the zone table; not used in `clash_progress` |
| `KAPPA_BY_LENGTH` | How strongly the stat ratio scales progress, per race length |
| `OPPONENT_QTE` | How well the opponent times (unchanged; HAN still applies) |
| `W0`, `T_MAX`, `L_MAX` | Progress for a win, tie and loss relative to a perfect win |
| `TAU_BETA`, `TAU_P_TOP`, `TAU_GAMMA` | Shape of the timing curve tau(q) |
| `MU` | How much POW share boosts wins and EN share boosts ties/losses |
| `ETA` | How much HAN share boosts effective timing |
| `DECK_ALPHA` | Deck smoothing (higher = more even) |

Godot-only feel constants, tuned here:

| Constant | Effect | Recommended range |
|----------|--------|-------------------|
| `STRAIGHT_DURATION` | Seconds to pick 3 stances | 8.0 – 12.0 |

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
     → visible zone = qte_zone_width(r, MatchConfig.qte_window_mod) at the race's fixed r
       (equations.py:338). This is the QTE difficulty (Austin, 2026-11-11, 8:48 PM PT:
       scaled only through the visible zone; no level-gap qte_difficulty() on top).
     → emit corner_started(player_stances, opponent_stances)
      → QTEController.start(qte_type, qte_zone_width(r, qte_window_mod))
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
       (q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1) on both sides,
        no knot_window; player raw_qte is the entered QTE at the visible zone;
        opponent raw_qte = OPPONENT_QTE; HAN still applies; kappa from max_turns)
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
| Button idle/pressed (POW, EN, HAN) | 6 |
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

| Turn Type | POW | EN | HAN |
|-----------|-----|----|-----|
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
- No separate mash-speed difficulty scale.

### Timing mode (continuous)
- Moving marker oscillates across a target zone
- Timer ticks down; multiple successful presses increase score
- Final score = (successful_presses / total_opportunities × 10)

### Zone width (QTE difficulty)

**Resolved (Austin, 2026-11-11, 8:48 PM PT):** "Yeah QTE difficulty is scaled through the visibile zone. I don't see double dipping there." Difficulty is scaled only through the visible zone; the old level-gap `qte_difficulty()` formula and its ms table are dropped.

```
zone_width_over_w0 = qte_zone_width(r, MatchConfig.qte_window_mod)   # equations.py:338
timing_window_ms   = zone_width_over_w0 × QTE_ZONE_BASE_MS           # equations.py:130–133
```

`r` is the race's fixed stat ratio (no mid-race change). `qte_window_mod` is a multiplicative bonus on the current zone (`models.py:152`). Values live in the sim; do not retune them in Godot.

---

## Appendix G: AI Stance Lookup

For each corner, the opponent's 3 stances come from the district line table, `LINE_SET_C[district][corner]` in `sim/velocity_shift/equations.py` (mirrored in `scripts/globals.gd`, read through `TurnTypeData.pick_line()`). The district is the race's `district_id`, and the corner code comes from `TrackData`. The locked car tell is lane Entry only (`design/06-pattern-read.md`), which is why every alternate shares main's Entry.

```
# Street race, corner N90:
lines  = LINE_SET_C["street"]["N90"]      # [main, alt1, alt2]
a       = LINE_ADHERENCE
weights = [a, (1 - a) * LINE_ALT_WEIGHTS["alt1"], (1 - a) * LINE_ALT_WEIGHTS["alt2"]]
line    = lines[rng.rand_weighted(weights)]   # one draw per corner, played exactly
stances = [line[0], line[1], line[2]]     # Entry, Apex, Exit (P/E/H)
```

Make the draw from the match `RandomNumberGenerator` so a playtest dump's Block C seed and RNG state reproduce the opponent's picks in Godot. Godot's generator isn't Python's, so this matches the sim's line rates, not its exact rolls.

## Appendix H: Notes / Gotchas

- **Stance naming:** stances are `Stance.POW` / `Stance.EN` / `Stance.HAN` (string values `"POW"` / `"EN"` / `"HAN"`) and the same-stance clash result is `StanceOutcome.DRAW`, matching the sim. Old → new map: `design/02-equations-reference.md` §6.0. Lane words belong only to on-screen lane labels and art.
- **Hands:** a fresh `HAND_SIZE` hand each turn, drawn i.i.d. from `deck_weights()`; pick 3, the rest is dropped. No persistent deck, no piles.
- **Opponent cards:** the picked line, played exactly; no opponent hand.
- **No DNF / knockout** — match always runs to max_turns, then the higher progress total wins.
- **Race length sets kappa:** `max_turns` (default 10) is the planned race length, one of `RACE_LENGTHS`; kappa = `kappa_for_length(max_turns)`, never the lap's corner count. Any other length snaps to the nearest `KAPPA_BY_LENGTH` key.
- **Visible QTE zone, not knot_window:** player `q_eff = clip(raw_qte × (1 + ETA × (han_share − 1/3)), 0, 1)` with no `knot_window`. QTE difficulty is scaled only through `qte_zone_width(r, window_mod)` at the race's fixed r (`equations.py:338`), plus `MatchConfig.qte_window_mod` (Austin, 2026-11-11, 8:48 PM PT). `KNOT_WINDOW_105` / `knot_window` are legacy for the oracle only. The old level-gap `qte_difficulty()` is dropped.
- **Ties:** equal progress totals are a tie; no opponent tiebreaker.
- **Car position in 3D:** drawn spacing only. Cumulative progress, position, and the win condition stay on the real gap (`design/06-pattern-read.md`, Lane Entry and visual gap). A capped lead ahead of the player is not the exact large-lead magnitude. The trailer is not given a matching cap. `CarAnimator.gd` still uses a symmetric Z lerp; that code was not updated with the rule.
- **AnimationTree blend:** 7 animations + 3-way blend node = smooth stance transitions for any 3-stance sequence. No per-combination baking.
- **Face crossfade:** 3 stacked TextureRects with alpha driven by same blend schedule as the car. 4th overlay layer for bluff tell.
- **Meta-archetypes:** 3 face types (Scowling/Grinning/Focused) shared by hard+soft pairs. 9 face textures + 9 tell overlays total.
- **Future screens:** Menu → Isometric Overworld → Race → Battle → Results → Overworld. Design scene loading (StageManager) with this in mind.
- **Skill points are in v1** (see 08); the tree layout is still undecided. Mods system design is separate.
- **Sound/music:** deferred. Design signal hooks for future audio integration.

---

## Appendix I: Root Godot project (two-corner engine test, promoted 2026-11-19)

> Promoted out of `unapproved/gordon/two-corner/` into the repo root on `touge-race` (Austin 2026-11-19, via Arthur's chat: "Yes, Gordon can promote the two-corner test into the root Godot project, remove the unapproved copy, log it and push."). The numbers inside are still the provisional two-corner ones; the 10-turn Touge race builds on top of this project.

**Where things live now** (old two-corner path → root path):

| Was (`unapproved/gordon/two-corner/…`) | Now |
|---|---|
| `godot/project.godot` | merged into `project.godot` (name, icon, Jolt, `[input]` kept; main scene, display and GL Compatibility renderer taken from the test) |
| `godot/scenes/`, `godot/scripts/`, `godot/shaders/`, `godot/fonts/`, `godot/export_presets.cfg` | `scenes/`, `scripts/`, `shaders/`, `fonts/`, `export_presets.cfg` |
| `godot/spec/` + `spec/inputs/`, `spec/race_config.json`, `spec/display.json` (identical copies), `spec/constants.json` | `spec/` (one copy; scripted inputs sit next to the configs) |
| `godot/art/` (stand-in HUD/env textures; root `art/` is Arthur's source art) | `assets/tex/kit/` (`res://assets/tex/kit/…`) |
| `godot/assets/tex/` | `assets/tex/` |
| `godot/assets/cars/mx5_env.png`, `s2000_env.png` | `assets/tex/cars/` |
| `godot/assets/cars/car_mx5.glb`, `car_s2000.glb` (byte-identical to Arthur's) | reuse Arthur's `assets/cars/mx5/car_mx5.glb`, `assets/cars/s2000/car_s2000.glb` |
| `tools/`, `spec/gen_*.py` | `tools/two_corner/` (run from anywhere; they `cd` to the repo root) |
| `out/` (kept playtest shots/reports) | `unapproved/gordon/two-corner-media/` |
| `_pin/` (sim checkout at the pin) | `.pin/` at the repo root (`git worktree add .pin <pin sha>`), or set `TWO_CORNER_PIN=/path/to/checkout`. Gitignored, hidden from Godot |
| fresh tool output (`out/…`) | `.out/two_corner/` (gitignored, hidden from Godot); web export goes to `.out/godot_web/` |

Renderer: the root switched from Mobile to **GL Compatibility** (needed for the mobile web export; the test was built and shot on it). Run commands below assume the repo root: `/workspace/tools/godot --path .` (add `--rendering-driver opengl3` on the box). In the history notes below, `out/…` means `unapproved/gordon/two-corner-media/…` for kept shots and `.out/two_corner/…` for new runs; mentions of "this directory" mean the repo root.

> **UNAPPROVED.** This is the two-corner engine test, with provisional numbers. Phase 5 UI/camera follows AD B.5a/B.5b at **ab1c4a1**. It is the one exception to the combat freeze. The sim is pinned at **50928ed** (`50928ed0e268277e50f97a68c7d71151078e976e`, newest proto-build containing Barry's 53267c5 POW/EN/HAN rename and the c3ffc41 QTE rounding; Austin's 2026-11-12 naming rule: backend is POW/EN/HAN, IN/MID/OUT is visual only). The palette is Arthur's B.2a, committed at **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`).

> **2026-11-11: Three.js dropped (Austin).** The Godot build is the only one worked on and tested; parity is Godot vs the pinned sim.
> Notes below that mention `threejs/` are historical; that tree is not in this copy.

Before 2026-11-19 the working copy was `/workspace/prototypes/two-corner/` (with `_pin/`, the historical `threejs/` tree and local `out/`) and the repo mirror was `unapproved/gordon/two-corner/`; the repo root is now the only copy.

Tools that import the pinned sim (`tools/two_corner/sim_parity.py`, `tools/two_corner/check_driver_vs_run_match.py`, `tools/two_corner/gen_constants.py`) look for `.pin/sim`. To re-run them, point those tools at a checkout of `50928ed` (`git worktree add .pin 50928ed`); do not use this branch's live `sim/`, which may move on. sim/ is unchanged after 53267c5. `tools/two_corner/gen_art.py` also reads the logo from `.pin/art/logo/final/`. `tools/two_corner/gen_constants.py` no longer writes the Three.js constants file (shots10).

### Layout
- `tools/two_corner/gen_constants.py` imports the pinned `equations.py` and writes `scripts/sim_constants.gd`, citing `equations.py:<line>`
  above every constant. No value is typed by hand. Long floats are written as an exact mantissa / 2^k (Godot's decimal parser is not
  correctly rounded); `headless_run.gd` self-checks the IEEE-754 bits of every float.
- `spec/race_config.json`: corners (Touge HP L, Touge N90 R; corner 2 was Street N90 R until shots9 — one continuous Touge road, Austin 2026-11-11) and stats by constant name (Balanced builds from
  `simulate_win_rate`, opp_total = `SABINE_BUDGET`, r = `LADDER_R[6]` crew boss = 1.05, so 105/105/105 vs 100/100/100).
  Base stats only: no mods, parts or loadouts.
- `spec/display.json`: DISPLAY-ONLY placeholders (visual-gap cap, road, camera, mirror, QTE sweep).
- `spec/*.json`: scripted inputs `{seed, corners:[{pick:[hand idx...], qte:[entry, apex, exit]}]}`. Each phase score is null
  (unplayed = 0), a number in [0, 1], or `"0x<16 hex>"` IEEE-754 bits. Fewer than 3 picks means the timer ran out, and the line is auto-filled.
- `tools/two_corner/sim_parity.py`: the real pinned sim functions (`pick_line`, `draw_weighted_hand`, `resolve_turn`) in `run_match` draw order.
  `tools/two_corner/check_driver_vs_run_match.py` proves the order matches `run_match`. `tools/two_corner/compare.py` and `tools/two_corner/run_parity.sh` check the engines against the sim.
- RNG: CPython's `random.Random` (MT19937, `random()`, `choices` bisect) is ported exactly to JS and GDScript, so there is no pre-drawn stream.
- Godot scenes (since shots11): `scenes/` holds `main.tscn` plus six sub-scenes; see **Editor workflow** below.

### Run
- Parity (qte-v1 function bits, Godot vs sim, dump/load, restart test, Plan the Line + QTE key test vs sim): `tools/two_corner/run_parity.sh`
- Restart test (Godot game loop): `tools/two_corner/run_restart_test.sh`
- Screenshots + frame sequences (Godot): `tools/two_corner/run_shots.sh [inputs-name] [outroot=.out/two_corner/shots5]`
- Live check of the web export on :5176: `node tools/two_corner/live_check_godot.mjs` (writes `out/shots5/live/` relative to this directory). The web export and the Playwright install from `threejs/node_modules` are not in this copy, so this script is noted only.
- Godot, play (from the repo root): `/workspace/tools/godot --path .`
  - add `--rendering-driver opengl3` on the box
  - user args: `-- --seed N` (prefills the menu seed), `--no-menu`, `--script-inputs res://spec/X.json --shots DIR` (skips the menu)
- Godot, headless: `/workspace/tools/godot --headless --path . --script res://scripts/headless_run.gd -- $PWD/spec/X.json --out f.json [--dump-after 0 --dump-to s.tc2 | --load s.tc2]`
- Godot web export: `.out/godot_web/` (served at http://127.0.0.1:5176/)
- Three.js dev server: `cd threejs && npm run dev`, which serves http://127.0.0.1:5174/
  - query params: `?seed=N` (prefills the menu seed), `?menu=0` (straight into a race), `?script=X.json` (harness; skips the menu)
  - production build: `threejs/dist/` (`npm run build`), served by `npm run preview` at :5175
- Three.js headless: `cd threejs && node headless/run_race.mjs ../spec/X.json [--out f] [--dump-after 0 --dump-to s.tc1 | --load s.tc1]`
- Keys:
  - Main menu: Up/Down select, Enter confirm; on SEED, 0-9 type and Backspace delete (empty = random seed). QUIT is Godot desktop only
  - Finish screen: 1 restart same seed, 2 new race (random seed), 3 main menu (or Left/Right + Enter)
  - Plan the Line (selection, at the B.5b camera stops): Up/Down choose the option for the current phase (on ENTRY, Left/Right move the lane the way the road shows it: a left corner has IN on the left, a right corner OUT; no wrap), Enter sets it and moves to
    the next phase (Enter on EXIT locks the line), Backspace goes back one phase. After each turn: 'Press Enter to continue' with a countdown that auto-continues (playback_flow.continue_s, PLACEHOLDER).
    (Hidden legacy: 1-6 still pick a hand index directly.)
  - QTE (after LINE LOCKED, at the Entry, Apex and Exit camera stops): Space when the cursor is in the amber zone; no press before
    the cursor passes the zone's far edge = unplayed = 0
  - F9 dumps a TC3 token (clipboard + console / user://last_state.tc1, file name unchanged), F10 loads one from the clipboard

### State token
Since this pass: `TC3:<sim7>:<build10>:<base64url(json)>:<CRC-16/CCITT-FALSE>`, spec in `unapproved/gordon/playtest-state-spec.md` §0.5.
It records the sim pin and the build id (`tools/two_corner/stamp_build.py` -> `spec/build.json`), the seed, and every completed turn's picks and
exact phase scores (IEEE-754 bits). Load replays them through the core and checks rng draws and total bits ("replay desync" otherwise).
`python3 tools/two_corner/decode_token.py '<token>'` decodes TC3, and flags older TC2/TC1 as outdated tokens. TC2 (A/S/D letters) and TC1 (sim 212eaab) must be replayed on the build that made them.
Stance letters in `line`, `hand` and `player_line`: `P` = POW, `E` = EN, `H` = HAN. On screen the lane is written **OUT (POW)**, **MID (HAN)**, **IN (EN)**.

### Phase 2 (display only, parity unchanged): scrolling straight + authored corner camera
- STRAIGHT (whole selection timer): StraightRoad strip mesh (road/verge/barrier textures from tools/two_corner/gen_textures.py) scrolled by UV offset
  via the guide §14.2 RoadScroller (`scroll_speed` 0.05, transition_to_corner 1.5 for 0.5 s then 0.6 — GUIDE values in display.json road_scroller).
  Metres-per-UV (road_uv_length_m 500 → 25 m/s), tiles, lamp spacing, wheel cap, bob are PLACEHOLDERS. Lamps stream past; wheels spin; identical body bob.
- Corner: same scroller on the CornerRoad. Camera: §12.2 side-offset transition, then an authored path per turn type (Godot Path3D/PathFollow3D,
  Three.js CatmullRomCurve3): HP tight inside line, N90 hard cut to the apex. Rig modes BCH / BCL / BCR shown in the HUD. Keyframes are PLACEHOLDERS (display.json corner_cams).
- Overtakes (since shots9, Austin 2026-11-11 ~10 PM PT, replaces the hold-then-snap rule; timing updated shots12, Austin 2026-11-12:
  "Order only changes after exit QTE"): "if a pass occurs, it is visually shown during the dynamic play... if the exit lane is the same for
  both cars and one goes for a pass, then the passing car should go to an open lane for the pass animation, and then move into the position
  it needs to play for the next turn." The gap holds until the Exit QTE finishes, then eases over `pass_after_exit_s`. See the shots9 section below.
- Frame sequences: scripted runs write seq_select*/seq_corner*/seq_snap* PNGs + frames_640.json; `python3 tools/two_corner/frame_compare.py out/shots3` makes GIFs and numbers.
- Live check: `URL=... TAG=... node threejs/headless/live_check.mjs`.

### Phase 3 (display/art only, parity unchanged): Arthur's art direction
Sources (pin 212eaab): `design/art/art_direction.md` (Part A binding for cars, Part B [VIBE]/[PROPOSAL]), the psx-night-street-art-direction skill,
`art/README.md`, `art/mood/*`, game-ready `assets/cars/*`. Nathaniel's story/world files were NOT read or applied (Austin's scope change).
- ONE look only: 640x480 internal (A.5), RGB555 + 4x4 Bayer dither, nearest upscale to 1280x960. CRT filter, the low-res mode and the C/R toggles were removed (Austin).
  PSX vertex snapping and affine texturing stay.
- `tools/two_corner/gen_art.py` writes every stand-in texture to `assets/tex/kit/` (copied to `threejs/public/art/`, `assets/tex/kit/`): district road strips with the
  stepped 4-band sodium pools painted in (B.1), verge, guardrail, cedar cards, ridge/skyline bands, painted sky strips (fog-matched horizon),
  facades (pre-lit windows, no lettering), blank neon panels, cut-out props, glow sprites, blob shadow, headlight throw, 6x9 bitmap font, 9-slice panel.
  `assets/env`, `assets/ui`, `assets/fonts` are empty at the pin, so ALL environment/HUD art is a stand-in.
- `spec/display.json` `districts` (B.3 Touge / Urban Street palettes, fog ranges, lamp spacing) and `car_shading` (A.4/A.8 + per-car README values).
  Each value carries `_source`; PLACEHOLDER marks anything the doc does not give.
- Cars: A.8 faked-shine shader per material (paint/softtop/glass values from the MX5 README; S2000 uses A.8 defaults), MX5 FX_LampGlow quads shown
  additively, S2000 stand-in lamp glows, blob shadow + headlight-throw decals.
- HUD: drawn at 640x480 with the bitmap font and 9-slice panels (Three.js `src/hud.js`, Godot `scripts/hud.gd`).
- Composites: `python3 tools/two_corner/art_composites.py out/before_art_shots out/shots3 .pin out/art_composites`. Those source trees are not in this copy.

### Main menu + restart (Austin 2026-11-10, display/flow only)
- Main menu: approved V3 logo (`art/logo/final/v3_white_on_black.png`, downsampled to 384 px with hard 1-bit alpha by `tools/two_corner/gen_art.py` -> `logo_v3.png`),
  START RACE, SEED (typed, or RANDOM), QUIT (Godot desktop only). The scrolling Touge straight is the backdrop; its timer never runs.
- Finish screen: RESTART SAME SEED / NEW RACE / MAIN MENU. Every start builds a fresh RaceCore (fresh MT19937 from the seed) and resets every display-side race variable.
  Random seeds come from Math.random / randi (display side), never the sim RNG.
- Restart test: `spec/restart_test.json` = 4 races chained by `restart: [same, new, menu]`, driven through the same key handler the player uses.
  Each restart asserts state == cold start, and all 4 races are compared with the pinned sim (`tools/two_corner/run_restart_test.sh`).
- Headless runners (`headless_run.gd`, `run_race.mjs`) and scripted shots never show the menu.

### Phase 4 (2026-11-11, display/art/UI only, parity unchanged): Arthur's palette + Plan the Line
- Palette: art_direction.md **B.2a**, committed at origin **55b9063** (`55b90630ce777fa8f9fffac7c243dd341d158725`), values copied from
  `/workspace/mockups/tones/work/tones.py` preset `blend50` into `spec/display.json` `palette` (fog #0B172B, zenith #010408, no city glow,
  ambient #5575A0 x0.8, every lamp #F0C894 x0.85, 3-step pools x0.09, bloom 0.22 / threshold 0 as a glow-only pass, saturation 1.05).
  `palette.calib` holds display calibration gains (not doc values) that scale the mockup light terms onto our stand-in textures.
- Stance UI colours (Austin, swapped 2026-11-11; names as of 2026-11-12): POW #2CB84A (green), EN #E8282C (red), HAN #F0C828 (yellow) with dark text on yellow (`display.json` `stance_ui`).
- Backend, data, tokens and docs name stances by stat only (POW / EN / HAN, letters P / E / H). IN / MID / OUT is the on-screen lane (OUT = POW, MID = HAN, IN = EN), written **OUT (POW)** on the HUD.
- Filtering (Q4): world textures smooth (linear; the car albedo uses mipmaps per the A.8 shader sketch), no other mips. HUD stays crisp:
  NimbusSansNarrow Bold / BoldOblique at 1-bit (the mockups' fonts, `fonts/README.md`), 640x480 nearest upscale (A.5).
- Plan the Line (Arthur's `/workspace/mockups/lane_chain/v5`): the 6-card hand is hidden and only decides which options are available.
  PLAN THE LINE panel (breadcrumb ENTRY > APEX > EXIT, options '<Stance> <phase>' with POW/EN/HAN chips, '<TAG> · none drawn' greying),
  ENTRY strip (OUT (POW), MID (HAN), IN (EN)), turn-in plate + 16-segment timer under the mirror,
  player lane chevrons over the road, 'Line locks at turn-in'. Corner playback: LINE LOCKED strip with the current phase in amber,
  then per-clash results in the same strip. Gap meter moved to the top right. Scripted inputs are unchanged (`pick` = hand indices).
- Shots: `out/shots4/`; composites (`python3 tools/two_corner/phase4_composites.py`, paths are relative to this directory): `out/shots4/composites/`. Those Phase 4 composites were removed from this copy in Phase 5 (superseded; see git history).

### Phase 5 (2026-11-11, display/UI/camera only, parity unchanged): B.5b camera stops + B.5a line vs line
Sources: `design/art/art_direction.md` at **ab1c4a1** (`ab1c4a12f69b23ccd74cd8982629b73a4865a127`) B.5b (lines 255-263) and B.5a (265-270), both approved by Austin
2026-11-11; reference frames `art/ui/line_select_cam/` (with `build_lsc.py`, `post_lsc.py`, `make_tex.py`) and `art/ui/line_vs_line/` (built by
`unapproved/arthur/mockups/line_clash/post_clash.py`, option A). Full source table: `out/PHASE5_REPORT.md`.
- **Selection walks the corner (B.5b).** Entry: the fixed chase camera (frame values, build_lsc.py:245) on the scrolling straight, rival in its Entry lane,
  rear-view mirror on. Apex: the camera moves to a raised view from the corner's outside (build_lsc.py:247-249). Exit: the camera moves to the exit
  (build_lsc.py:250-252). At the Apex and Exit stops the corner is shown with no cars and no mirror, and the straight stops scrolling. Backspace walks
  back a stop. When the line locks (Enter on Exit, or the 12 s timer auto-fills), the camera returns to Entry with the LINE LOCKED banner (frame 4),
  then playback runs. The B.5b timer (17 segments) sits top left; the corner plate (top right) marks the stop E / A / X.
- **Playback (B.5a).** The Phase 4 LINE LOCKED strip is replaced by the line-vs-line panel: YOU and RIVAL rows, both full lines face up from the start
  (no flips), amber outline on the column being played, RESULT (WIN / LOSS / TIE) filling in per phase. No pause or clash beats. The corner plate shows
  the phase being played. RESULT is computed with the sim's own pure `resolve_stance` (no RNG), and the key test checks it equals the sim's outcomes.
- **Kept:** Plan the Line option labels ('<Stance> <phase>'), POW/EN/HAN chips, 'none drawn' greying, the navy/teal palette, 640x480 without CRT,
  menu and restart, the overtake rule (cars hold through the corner camera and snap when it returns to rear chase), the provisional W=1 hook, the sim pin
  and the parity harness. The playback camera is still the guide §13.3 authored path.
- **Touge dressing** now comes from the approved B.5b Touge frames (road paint, guardrail, cedars, ridge, lamps, fog 9-78 m); see the report.
- Shots: `out/shots5/` on the box prototype (GIFs `corner1_touge_HP_full.gif`, `corner2_street_N90_full.gif`). This copy keeps only `out/shots5/composites/` (`vs_line_select_cam.png`, `vs_line_vs_line.png`, `before_after_phase4.png`, palette-quantised to fit the size budget); `python3 tools/two_corner/phase5_composites.py` needs the full frame sets.

### B.5d line preview (2026-11-12, display only, parity unchanged)

Austin approved Arthur's line-preview mockup (relayed by Arthur, commit **9a83828**) as the build reference. Purely visual; no gameplay or sim change.

- Flat chevrons on the road along the chained Entry → Apex → Exit line, pointing in the direction of travel, no glow. Colours are the stance UI set: POW `#2CB84A`, EN `#E8282C`, HAN `#F0C828`. Hovered segment at full strength; follow-on segments solid at 0.66 brightness and slightly thinner (Arthur pass 4 measures, `spec/display.json` `line_preview`, marked PLACEHOLDER). Scripts `scripts/line_chevrons.gd` and the chevron shader/art are copied from Arthur's mockup and adapted here (credit in the script).
- Bend mapping is Arthur's, recorded as PLACEHOLDER: POW holds the outer line (−1 × lane width), HAN mid-lane (0), EN cuts to the inner line (+1 × full lane width, corner-relative via `track.gd`). Implied follow-on is Apex EN, Exit POW. Each segment starts where the previous one ends. Entry stays in the chosen Entry lane.
- One combined PLAN THE LINE panel at the bottom right (narrower so it clears the car). Lane chips read `OUT · POW`, `MID · HAN`, `IN · EN`. The race split bar sits under the rear-view mirror. Entry camera, Entry select framing, and Exit camera are unchanged.
- Known leftover: from the Entry chase cam the follow-on line vanishes over the crest (`_in_straight()` hides the hook mesh). Left as-is; same gap is in the mockup.
- Shots: `out/shots14/` (Entry / Apex / Exit × each stance hover, 640 and 1280; `compare_arthur_vs_gordon.png`). Shot harness: `--line-preview-shots <dir>` (seed 20261114 so every stance can be hovered at Exit).

### HUD look (2026-11-12, display only, parity unchanged)

Austin (12:55 PM PT): "I like his HUD look." Plate grain, bevel and heavier titles are ported from Arthur's line-preview `hud_panel.gd` (`plate_finish`) and fonts. Grain is drawn only on HUD plates, on the 1280×960 HUD layer after the 640×480 dither pass — never on the 3D or the road. Fonts: Nimbus Sans Narrow Bold / Bold Oblique, Nimbus Sans Bold (URW++ base35, AGPL-3 with Font exception), and Archivo Black (SIL OFL 1.1); licenses sit next to the files in `fonts/`. Text is pixel-hard (no AA, hinting off, nearest). Colours unchanged. Every PLAN THE LINE row uses unframed OUT / MID / IN over a small framed POW / HAN / EN stat box (Austin via Arthur, 769f073). `entry_strip.gd` inlines those labels so Arthur's `run.sh` can symlink it onto his `hud_panel.gd`. Debug box keeps the 6x9 bitmap so F9/F10 and the seed stay readable. Cameras and gameplay unchanged. Shots: `out/shots15/`.


### shots9 (display/flow only, scoring/RNG/pin unchanged): Austin's playtest, 2026-11-11 ~9:58-10:22 PM PT
- **After-turn pause:** once the RESULT row fills in, 'Press Enter to continue  N' counts down and auto-continues ("That should have a time limit").
  No pause was added to selection or playback (B.5a). Length `playback_flow.continue_s` = 6 s, PLACEHOLDER awaiting Desmond/Austin.
- **Entry lane with Left/Right:** on-screen direction (left corner: IN MID OUT left to right; right corner: OUT MID IN). The bottom-left ENTRY strip
  lists the lanes in that same on-screen order, so it is mirrored on left corners (post_v5.py:98 draws OUT MID IN). The player car eases into
  the highlighted lane while you choose.
- **Cars drive their lines:** both cars go Entry lane -> Apex lane (mid-arc) -> Exit lane, smoothly (`playback_flow.blend_*`, PLACEHOLDER).
  Apex/Exit lanes use the Entry lane rule (A outside, S centre, D inside), as the B.5b frames' labels do; no Apex/Exit lane mapping is approved.
  The chase camera stays on the road centre line (B.5b framing), so the car visibly moves across lanes.
- **Infinite scroll at every stop:** the road also scrolls at the Apex and Exit stops (Phase 5 kept it to Entry only). `hold_stop` in main.gd is a
  hook to hold the Apex stop pose with the road scrolling while a QTE plays later (not used by the flow yet).
- **Passes after the Exit QTE (shots12, Austin 2026-11-12: "Order only changes after exit QTE"):** the visual gap holds the pre-turn value
  until the Exit QTE finishes, then moves to the post-turn value over `playback_flow.pass_after_exit_s` (PLACEHOLDER 2.5 s, the same length as the
  old `pass_u0..pass_u1` window). Leftover playback after the Exit hold is only ~0.16 s (HP) / ~0.23 s (N90), too short to read, so the animation
  continues into the RESULT / Enter-to-continue phase (Enter and auto-continue wait until the lerp finishes). `pass_u0` / `pass_u1` are unused.
  Lead/gap still from the sim: `_preview_lead` calls the same pure `Combat.resolve_turn` the core uses, and that value equals `core.submit_qte`.
  If the drawn order flips and the lines share a lane while the cars overlap, the passer takes the open lane, overtakes, and settles back onto its
  line (the open-lane plan is sampled on this same post-Exit window). No-clip check: the scripted run prints `MIN_SEP_OVERLAP` (lateral gap while
  the cars are within `car_len_m` along the road).
- **One continuous Touge road:** straight 45, corner 1 (HP L), join 47 (= 10 + 45 - 8, so corner 1's playback ends exactly where corner 2's selection
  starts), corner 2 (N90 R), exit 30 (`scripts/course.gd`). Radius/angle stay the `road.by_code` PLACEHOLDERS. Corner 2 now uses the sim's Touge N90
  line set (`LINE_SET_C.touge.N90` DSA/DDS/DSS instead of Street's SSA/SDS/SSS), so the rival's corner-2 lines differ from before for the same seed.
  The Touge dressing is one-sided (cedars/lamps on the right of travel), so on corner 2 (a right turn) they sit on its inside, unlike the B.5b frames.
- **HUD on a 2x pixel grid (Austin 22:21: "now the text is really sharp and uncharacteristic of the vibe"; he chose "Draw HUD text pixel-hard on a
  2x grid (1280x960)"):** the HUD (640x480 design units) is drawn into a 1280x960 SubViewport at x2. Text is rasterised at size x2, 1-bit (no AA,
  no subpixel), with a 2 px shadow, and the 6x9 bitmap font and panels go up x2 nearest. The project base is 1280x960 with the game at x2. When
  the window fits 1280x960 or more, everything scales by a whole number of that (HUD nearest, world 640x480 at twice that). Below 1280x960 the
  scale is fractional and the HUD layer is shown linear. **Departs from art_direction.md:115/:141/:242 (integer nearest upscale of one 640x480 frame,
  viewport stretch) and the mockups' 1-bit 640x480 text (post_lsc.py:34) for the UI only, at Austin's request; flag for Arthur.**
- Placeholders: all of display.json `playback_flow` (continue_s 6, lane_ease_s 0.35, blend 6/8 m, pass_after_exit_s 2.5, overlap 5.5/9 m, min_sep 2.6 m; pass_u0/pass_u1 unused since shots12).
- Demo input `spec/shots9_pass.json` (seed 3): both corners share the Exit lane and the drawn order flips in both. Shots in `out/shots9/`.


### shots10 (2026-11-11): re-pin to f0efecf + three timing QTEs per turn (Austin approved 10:56 PM PT: "Yes.")
- **Pin:** `.pin` is now `f0efecfbc18b495a0ba9df3bf956d8e89acc3477` (sim/ is unchanged at origin/proto-build 59f7e6d). Ported to GDScript:
  qte-v1 zone (`qte_zone_width`, `expected_hit_quality` with a bit-exact port of glibc's `erf`, `raw_qte_score`, `qte_sigma_over_a0`
  and the two bisections), `phase_raw_qte`, `mean_phase_qte` (with CPython 3.12+ `sum()` Neumaier compensation so the mean is
  bit-identical), `clash_progress` without the knot window, and `resolve_turn` with `player_qte_phases`. The PROVISIONAL W=1 hook is
  retired: its hidden window no longer exists in clash math. Constants cite `equations.py:<line>` in `sim_constants.gd`.
- **Game:** after LINE LOCKED, one timing QTE at each B.5b camera stop (Entry chase, Apex stop, Exit stop) over the scrolling road, then
  the camera returns to Entry and playback (B.5a) runs. Zone = `qte_zone_width(r, qte_window_mod)` x `QTE_ZONE_BASE_MS`, the same for
  all three. At this race's r = 1.05 that is 1.0 x 800 ms. Press score = max(0, 1 - |e| / (zone/2)) (the s in `expected_hit_quality`'s
  docstring). The cursor passing the far edge = unplayed = 0. The three scores go to `core.submit_qte()`, and `resolve_turn` averages them.
- **Placeholders** (display.json `qte_sweep`): lead_ms 700, tail_ms 200, ready_s 0.5, result_hold_s 0.6, key SPACE. The QTE panel
  layout, labels and the plate's 'QTE' / 'TIMING' words have no Arthur frame.
- **Parity:** `tools/two_corner/qte_fn_test.py` checks 5,757 values bit for bit. Inputs are per-phase. fuzz300 mixes null / 0 / 1 / decimals /
  k/1024 / raw bits. The 200-seed key test now plays the three QTEs by Space through the real input path and sends the same picks and
  scores to the sim. Shots: `out/shots10/`.

### Editor workflow (shots11, 2026-11-12, UNAPPROVED)
Austin: "I think this is a good chance to work on your workflow for the editor with the two corner scene." The test used to build
everything in code under one Control. It is now split into scenes that open in the Godot 4.6.3 editor and show what the game draws.
No number, rule or sim value changed in the split. Values still come from `sim_constants.gd` (generated from the pinned sim) and
`spec/*.json` (display placeholders), and the split alone was pixel-identical on all 73 shots and 611 GIF frames (fixed-step A/B, `out/shots11/entry_pixel_diff.txt`).

**Open the project:** `godot --editor --path .` (Godot 4.6.3; on the box run it from the repo root; it needs `--rendering-driver opengl3`;
the editor runs on the Compatibility renderer like the game). F5 runs `main.tscn`. A scene path after the project opens that scene directly,
e.g. `... res://scenes/track.tscn`. To validate every scene headless: `godot --headless --editor --path . res://scenes/<name>.tscn --quit-after 120`
and check the output for `ERROR`.

**Which scene to edit for what**

| Scene | Script | Purpose / edit it for |
|---|---|---|
| `scenes/main.tscn` | `scripts/main.gd` | Composition: WorldVP (640x480 3D SubViewport) with CameraRig, Sky, PlayerCar, RivalCar, Track, Dressing; MirrorVP; Post (RGB555 + Bayer, 2x nearest); HudVP (1280x960) + HudRect; GlowVP. Game flow, cameras, passes and the QTE flow stay in `main.gd`. Child order matters (GlowVP stays last, so the post pass reads last frame's glow as before). |
| `scenes/track.tscn` | `scripts/track_road.gd` (@tool) | The Touge road surface: one continuous course (straight 45, hairpin L, join 47, N90 R, exit 30) plus each corner's scroll straight at runtime. Geometry comes from `display.json` `road` / `lane_width_m` / `districts.<dk>.lamp_period_m`, shown read-only in the inspector under "Spec values". |
| `scenes/touge_dressing.tscn` | `scripts/touge_dressing.gd` (@tool) | Lamps, verge, guardrail, cedar cards (B.5b Touge frames); the Street branch is kept for a Street corner. Props stream with the road scroll at runtime. |
| `scenes/sky.tscn` | `scripts/sky.gd` (@tool) | Painted sky cylinder + ridge band (`SkyCylinder` node); follows the camera at runtime. |
| `scenes/car.tscn` | `scripts/car.gd` (@tool) | Wraps a `.glb` from `assets/cars` (exports `model`, `env_texture`, `car_id` = key into `display.json` `car_shading`). `main.tscn` has PlayerCar (MX5) and RivalCar (S2000, overridden exports). The A.8 shading, wheel pivots, decals and glows are added at runtime. |
| `scenes/camera_rig.tscn` | `scripts/camera_rig.gd` | `Cam` (main camera) and `CornerPath/Follow` (the §13.3 authored playback path). Poses are still computed in `main.gd` `_update_camera`, unchanged. **The Entry camera and Entry selection screen are final (Austin 2026-11-12): don't change their placement, framing, motion or timing.** |
| `scenes/hud.tscn` | `scripts/hud.gd` + `scripts/hud/*.gd` | One Control per panel: MirrorFrame, CornerPlate, GapMeter, LineLockTimer, DebugHud, LineSelect (Lanes, EntryStrip, PlanPanel), LineLockedBanner, QtePanel, LineVsLine, ContinuePrompt (result line + Enter-to-continue countdown), FinishPanel, MainMenu. `hud.gd` picks which panels show; each panel script draws its part. Shared palette and helpers: `scripts/hud/hud_panel.gd`. |
| (no scene) | `scripts/art_kit.gd` | Shared mesh / material builders used by the scenes above and by `main.gd`, so the editor and the game build the same thing. |

**How @tool regeneration works**
- Generated geometry (road strips, dressing, sky mesh, car model) is built in `_ready()` when `Engine.is_editor_hint()` is true, as children with
  no owner, so it shows in the viewport but is **never saved into the .tscn**. At runtime the same functions run from `main.gd` (per corner, with
  the corner's district and scroll straight), and the editor-only build does nothing.
- To see a spec change: edit `spec/display.json` (or `race_config.json`), copy it to `spec/`, then press **Rebuild road** / **Rebuild dressing**
  in the inspector (or reopen the scene). `district`, `preview_in_editor` and `preview_fog` (fog off by default so a top view stays readable) are
  editor-preview settings only.
- The HUD preview: pick a state in `Hud` > **Editor Preview** (select / lock / qte / play / result / finish / menu). The samples are display stand-ins,
  never used by the game. Text is rasterised for the 2x grid, so view the HUD at 200 % zoom to see it as the game shows it.
- Moving a HUD panel node in the editor only moves its selection box. Each panel still draws at the coordinates of the approved frames
  (post_lsc.py / post_clash.py / post_v5.py), so a layout change is a code change in that panel's script, not a drag.
- Placement in a .tscn that the runtime overwrites from the spec (viewport sizes, camera fov / near / far) is only an editor default; `main.gd`
  still sets it from `display.json` at start.
- The build id (`tools/two_corner/stamp_build.py`) now also hashes `scripts/hud/*.gd` and `scenes/*.tscn`.
- Editor screenshots: `out/shots11/editor_track_tscn.png` (top view of the road, Track inspector), `editor_touge_dressing_tscn.png`, `editor_hud_tscn.png`.

### shots11 (2026-11-12): QTEs during playback, static Apex / Exit stops (UNAPPROVED)
Austin 2026-11-12: line select is Entry, then a static Apex stop, then a static Exit stop. The QTEs play during playback (entry, apex, exit),
each with a timer, and while a QTE runs the cars stay at that phase with the road scrolling until the timer runs out. The Entry camera and
Entry selection screen stay exactly as they were.
- **Selection:** Entry is unchanged, and corner 1 Entry select frames are pixel-identical to shots10. At the Apex and Exit stops the road and props are now static:
  the drawn scroll freezes while the scroller keeps running underneath, so the return to Entry (LINE LOCKED) is pixel-identical too.
- **Playback:** after LINE LOCKED the car drives its line, holds at the Entry point (turn-in - 6 m), the Apex point (mid-arc) and the Exit point
  (arc end + 6 m), the same E / A / X marks as the corner plate, and runs that phase's QTE there with the road still scrolling. Phase timer =
  lead_ms + QTE_ZONE_BASE_MS + tail_ms (1.7 s), and at least result_hold_s after the score goes up. The sweep, zone, score
  (max(0, 1 - |e| / (zone/2))) and unplayed = 0 are unchanged. The B.5a panel shows the phase being played, and the QTE panel sits under it with
  the timer. The three scores go to `core.submit_qte()` at the end of playback, and `resolve_turn` averages them as before.
- `qte_sweep.ready_s` is no longer used. Layout, timer text and hold points are PLACEHOLDERS (no Arthur frame).
- **Shots:** `out/shots11/`. Full-turn GIF `turn1_full_qte_in_playback.gif` (640 px, 10 fps), with a repo copy `turn1_full_qte_in_playback_400.gif`;
  `side_by_side_shots10_vs_shots11.png`; `entry_pixel_diff.txt`; `parity.txt`.
