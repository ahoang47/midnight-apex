class_name TurnTypeData

const TURN_TYPES = ["Hairpin", "Constant Radius", "Decreasing Radius",
	"Increasing Radius", "90-Degree", "Chicane", "Esses", "Sweeper"]

static func get_stance_sequence(turn_type: String, archetype: String) -> Array:
	var base = _get_base_archetype(archetype)
	var table = _stances_by_archetype(base)
	return table.get(turn_type, [Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL])

static func get_qte_type(turn_type: String, stance: int) -> int:
	var table = {
		"Hairpin": {Globals.Stance.ATTACK: Globals.QteType.MASH, Globals.Stance.DEFEND: Globals.QteType.TIMING, Globals.Stance.NEUTRAL: Globals.QteType.TIMING},
		"Constant Radius": {Globals.Stance.ATTACK: Globals.QteType.TIMING, Globals.Stance.DEFEND: Globals.QteType.MASH, Globals.Stance.NEUTRAL: Globals.QteType.MASH},
		"Decreasing Radius": {Globals.Stance.ATTACK: Globals.QteType.MASH, Globals.Stance.DEFEND: Globals.QteType.TIMING, Globals.Stance.NEUTRAL: Globals.QteType.MASH},
		"Increasing Radius": {Globals.Stance.ATTACK: Globals.QteType.TIMING, Globals.Stance.DEFEND: Globals.QteType.MASH, Globals.Stance.NEUTRAL: Globals.QteType.TIMING},
		"90-Degree": {Globals.Stance.ATTACK: Globals.QteType.MASH, Globals.Stance.DEFEND: Globals.QteType.TIMING, Globals.Stance.NEUTRAL: Globals.QteType.MASH},
		"Chicane": {Globals.Stance.ATTACK: Globals.QteType.TIMING, Globals.Stance.DEFEND: Globals.QteType.MASH, Globals.Stance.NEUTRAL: Globals.QteType.MASH},
		"Esses": {Globals.Stance.ATTACK: Globals.QteType.MASH, Globals.Stance.DEFEND: Globals.QteType.TIMING, Globals.Stance.NEUTRAL: Globals.QteType.TIMING},
		"Sweeper": {Globals.Stance.ATTACK: Globals.QteType.TIMING, Globals.Stance.DEFEND: Globals.QteType.MASH, Globals.Stance.NEUTRAL: Globals.QteType.TIMING},
	}
	return table.get(turn_type, {}).get(stance, Globals.QteType.MASH)

static func get_bluff_stance(turn_type: String, archetype: String, position: int) -> int:
	var base = _get_base_archetype(archetype)
	var bluff_table = _bluffs_by_archetype(base)
	var bluffs = bluff_table.get(turn_type, [Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL])
	return bluffs[position] if position < bluffs.size() else Globals.Stance.NEUTRAL

static func _get_base_archetype(archetype: String) -> String:
	match archetype:
		"AR P": return "Bruiser"
		"AR E": return "Endurance"
		"AR H": return "Swift"
		_: return archetype

static func _stances_by_archetype(archetype: String) -> Dictionary:
	match archetype:
		"Bruiser":
			return {
				"Hairpin": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Constant Radius": [Globals.Stance.DEFEND, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"Decreasing Radius": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Increasing Radius": [Globals.Stance.DEFEND, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"90-Degree": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Chicane": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Esses": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Sweeper": [Globals.Stance.DEFEND, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
			}
		"Endurance":
			return {
				"Hairpin": [Globals.Stance.NEUTRAL, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"Constant Radius": [Globals.Stance.NEUTRAL, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Decreasing Radius": [Globals.Stance.NEUTRAL, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Increasing Radius": [Globals.Stance.NEUTRAL, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"90-Degree": [Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Chicane": [Globals.Stance.NEUTRAL, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Esses": [Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
				"Sweeper": [Globals.Stance.NEUTRAL, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
			}
		"Swift":
			return {
				"Hairpin": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Constant Radius": [Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Decreasing Radius": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Increasing Radius": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"90-Degree": [Globals.Stance.DEFEND, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"Chicane": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Esses": [Globals.Stance.NEUTRAL, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"Sweeper": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
			}
	return {}

static func _bluffs_by_archetype(archetype: String) -> Dictionary:
	match archetype:
		"Bruiser":
			return {
				"Hairpin": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Constant Radius": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
				"Decreasing Radius": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.DEFEND],
				"Increasing Radius": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
				"90-Degree": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Chicane": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Esses": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.NEUTRAL],
				"Sweeper": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
			}
		"Endurance":
			return {
				"Hairpin": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.DEFEND],
				"Constant Radius": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
				"Decreasing Radius": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Increasing Radius": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.DEFEND],
				"90-Degree": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.DEFEND],
				"Chicane": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.ATTACK],
				"Esses": [Globals.Stance.ATTACK, Globals.Stance.ATTACK, Globals.Stance.ATTACK],
				"Sweeper": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.ATTACK],
			}
		"Swift":
			return {
				"Hairpin": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Constant Radius": [Globals.Stance.DEFEND, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Decreasing Radius": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Increasing Radius": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"90-Degree": [Globals.Stance.ATTACK, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
				"Chicane": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
				"Esses": [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL, Globals.Stance.NEUTRAL],
				"Sweeper": [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.NEUTRAL],
			}
	return {}
