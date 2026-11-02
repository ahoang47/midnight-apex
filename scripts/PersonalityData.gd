class_name PersonalityData

static func get_personality(name: String) -> Dictionary:
	var map = {
		"Aggressive": _aggressive(),
		"Defensive": _defensive(),
		"Precise": _precise(),
		"Balanced": _balanced(),
		"Adaptive": _adaptive(),
	}
	return map.get(name, _aggressive())

static func _aggressive() -> Dictionary:
	return {
		"name": "Aggressive",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 3, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 1}, "hand_requirements": {Globals.Stance.ATTACK: 2}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _defensive() -> Dictionary:
	return {
		"name": "Defensive",
		"phases": [
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 3, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 1}, "hand_requirements": {Globals.Stance.ATTACK: 2}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _precise() -> Dictionary:
	return {
		"name": "Precise",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "behavior_override": "highest_ev", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _balanced() -> Dictionary:
	return {
		"name": "Balanced",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "behavior_override": "alternate", "hand_requirements": {Globals.Stance.ATTACK: 2, Globals.Stance.DEFEND: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "repeat_win", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
		]
	}

static func _adaptive() -> Dictionary:
	return {
		"name": "Adaptive",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "behavior_override": "third_highest_ev", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "second_highest_ev", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func get_encounter_phases(encounter_type: String) -> int:
	match encounter_type:
		"wild": return 1
		"lieutenant": return 2
		"boss": return 3
		_: return 1

static func get_phase_for_turn(turn: int, encounter_type: String) -> int:
	match encounter_type:
		"wild": return 0
		_: return (turn - 1) / 10
