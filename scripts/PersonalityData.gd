class_name PersonalityData

static func get_personality(name: String) -> Dictionary:
	var map = {
		"Bruiser": _bruiser(),
		"Endurance": _endurance(),
		"Swift": _swift(),
		"AR P": _ar_p(),
		"AR E": _ar_e(),
		"AR H": _ar_h(),
	}
	return map.get(name, _bruiser())

static func _bruiser() -> Dictionary:
	return {
		"name": "Bruiser",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 3, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 1}, "hand_requirements": {Globals.Stance.ATTACK: 2}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _endurance() -> Dictionary:
	return {
		"name": "Endurance",
		"phases": [
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 3, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 1}, "hand_requirements": {Globals.Stance.ATTACK: 2}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _swift() -> Dictionary:
	return {
		"name": "Swift",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "behavior_override": "highest_ev", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.UNPREDICTABLE},
		]
	}

static func _ar_p() -> Dictionary:
	return {
		"name": "AR P",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 4, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 0}, "hand_requirements": {Globals.Stance.ATTACK: 2}},
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 0, Globals.Stance.DEFEND: 4, Globals.Stance.NEUTRAL: 0}, "hand_requirements": {Globals.Stance.DEFEND: 2}},
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "weights": {Globals.Stance.ATTACK: 0, Globals.Stance.DEFEND: 0, Globals.Stance.NEUTRAL: 4}, "hand_requirements": {Globals.Stance.NEUTRAL: 2}},
		]
	}

static func _ar_e() -> Dictionary:
	return {
		"name": "AR E",
		"phases": [
			{"phase_type": Globals.PhaseType.AGGRESSIVE, "behavior_override": "alternate", "hand_requirements": {Globals.Stance.ATTACK: 2, Globals.Stance.DEFEND: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "counter", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
			{"phase_type": Globals.PhaseType.REACTIVE, "behavior_override": "repeat_win", "hand_requirements": {Globals.Stance.ATTACK: 1, Globals.Stance.DEFEND: 1, Globals.Stance.NEUTRAL: 1}},
		]
	}

static func _ar_h() -> Dictionary:
	return {
		"name": "AR H",
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
