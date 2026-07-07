class_name TellGenerator

static func generate_tells(turn: int, archetype: String,
		turn_type: String, encounter_type: String,
		rng: RandomNumberGenerator) -> Array:
	var true_sequence = TurnTypeData.get_stance_sequence(turn_type, archetype)
	var bluff_sequence = []
	var intensity = _get_intensity(encounter_type)
	var lie_rate = _get_lie_rate(encounter_type)

	if ArchetypeData.is_weak_turn(archetype, turn_type):
		lie_rate = 0.0
	elif ArchetypeData.is_comfortable_turn(archetype, turn_type):
		lie_rate = min(1.0, lie_rate * 2.0)

	var position_lie = _get_position_lie_weights(encounter_type)

	for i in range(3):
		var is_bluff = false
		var shown_stance = true_sequence[i]

		if rng.randf() < lie_rate and position_lie[i]:
			is_bluff = true
			shown_stance = TurnTypeData.get_bluff_stance(turn_type, archetype, i)

		bluff_sequence.append({
			"stance": shown_stance,
			"is_bluff": is_bluff,
			"expression_key": ArchetypeData.get_face_type(archetype),
		})

	return bluff_sequence

static func _get_intensity(encounter_type: String) -> int:
	match encounter_type:
		"wild": return 5
		"lieutenant": return 3
		"boss": return 2
		_: return 3

static func _get_lie_rate(encounter_type: String) -> float:
	match encounter_type:
		"wild": return 0.0
		"lieutenant": return 0.15
		"boss": return 0.25
		_: return 0.0

static func _get_position_lie_weights(encounter_type: String) -> Array:
	match encounter_type:
		"wild": return [false, false, false]
		"lieutenant": return [true, false, false]
		"boss": return [true, true, false]
		_: return [false, false, false]
