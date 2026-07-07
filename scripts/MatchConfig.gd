extends Resource
class_name MatchConfig
@export var player_stats: CombatantStats
@export var opponent_stats: CombatantStats
@export var max_turns: int = 99
@export var seed: int
@export var deterministic: bool = true
@export var rival_personality: String
@export var encounter_type: String
