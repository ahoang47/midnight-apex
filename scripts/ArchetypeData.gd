class_name ArchetypeData

static func get_meta_archetype(archetype: String) -> String:
	match archetype:
		"Aggressive":
			return "POW"
		"Defensive", "Balanced":
			return "EN"
		"Precise", "Adaptive":
			return "HAN"
		_:
			return "HAN"

static func get_face_type(archetype: String) -> String:
	match archetype:
		"Aggressive":
			return "Scowling"
		"Defensive", "Balanced":
			return "Grinning"
		"Precise", "Adaptive":
			return "Focused"
		_:
			return "Focused"

static func is_comfortable_turn(archetype: String, turn_type: String) -> bool:
	var comfortable = _comfortable_zones(archetype)
	return turn_type in comfortable

static func is_weak_turn(archetype: String, turn_type: String) -> bool:
	var weak = _weak_zones(archetype)
	return turn_type in weak

static func _comfortable_zones(archetype: String) -> Array:
	match archetype:
		"Aggressive":
			return ["Sweeper", "Increasing Radius"]
		"Defensive", "Balanced":
			return ["Constant Radius", "Sweeper"]
		"Precise", "Adaptive":
			return ["Chicane", "Esses"]
		_:
			return []

static func _weak_zones(archetype: String) -> Array:
	match archetype:
		"Aggressive":
			return ["Hairpin", "Decreasing Radius"]
		"Defensive", "Balanced":
			return ["Chicane", "Esses"]
		"Precise", "Adaptive":
			return ["Sweeper", "Hairpin"]
		_:
			return []
