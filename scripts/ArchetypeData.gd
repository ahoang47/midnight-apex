class_name ArchetypeData

static func get_meta_archetype(archetype: String) -> String:
	match archetype:
		"Bruiser", "AR P":
			return "POW"
		"Endurance", "AR E":
			return "EN"
		"Swift", "AR H":
			return "HAN"
		_:
			return "HAN"

static func get_face_type(archetype: String) -> String:
	match archetype:
		"Bruiser", "AR P":
			return "Scowling"
		"Endurance", "AR E":
			return "Grinning"
		"Swift", "AR H":
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
		"Bruiser", "AR P":
			return ["Sweeper", "Increasing Radius"]
		"Endurance", "AR E":
			return ["Constant Radius", "Sweeper"]
		"Swift", "AR H":
			return ["Chicane", "Esses"]
		_:
			return []

static func _weak_zones(archetype: String) -> Array:
	match archetype:
		"Bruiser", "AR P":
			return ["Hairpin", "Decreasing Radius"]
		"Endurance", "AR E":
			return ["Chicane", "Esses"]
		"Swift", "AR H":
			return ["Sweeper", "Hairpin"]
		_:
			return []
