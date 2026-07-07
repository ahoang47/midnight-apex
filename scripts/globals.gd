extends Node

enum Stance { ATTACK, DEFEND, NEUTRAL }
enum StanceOutcome { WIN = 1, NEUTRAL = 0, LOSS = -1 }
enum EncounterType { WILD, LIEUTENANT, BOSS }
enum PhaseType { AGGRESSIVE, REACTIVE, UNPREDICTABLE }
enum QteType { MASH, TIMING }

const CLASH_STAKES: float = 0.35
const BATTLE_BONUS: float = 0.05
const MITIGATION_PER_1000: float = 0.40
const MITIGATION_FLOOR: float = 0.10
const HP_PER_LEVEL: int = 180
const QTE_NORMALIZER: float = 10.0
const HAN_QTE_WEIGHT: float = 0.50
const DECK_SIZE: int = 192
const DECK_ALPHA: float = 0.85
const DECK_HAND_SIZE: int = 6
const PICKS_PER_TURN: int = 3
const RUBBER_BAND_PCT: float = 0.15
const STRAIGHT_DURATION: float = 12.0
const PHASE_DURATION: float = 4.0
const EXIT_LOCKOUT_ENABLED: bool = true
const QTE_TIMING_WINDOW_BASE_MS: int = 800
const QTE_TIMING_WINDOW_PER_GAP: int = 50
const QTE_TIMING_WINDOW_MIN_MS: int = 200
const QTE_MASH_SPEED_PER_GAP: float = 0.10

static func get_locked_out(exit_stance: int, from_type: int, to_type: int) -> Array:
	if not EXIT_LOCKOUT_ENABLED:
		return []
	var table = {
		"3|0|5": [Stance.NEUTRAL],
	}
	return table.get(str(from_type) + "|" + str(exit_stance) + "|" + str(to_type), [])
