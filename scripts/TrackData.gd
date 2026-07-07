class_name TrackData

const TURN_TYPES = ["Hairpin", "Constant Radius", "Decreasing Radius",
	"Increasing Radius", "90-Degree", "Chicane", "Esses", "Sweeper"]

const _CIRCUITS = {
	"default": ["Hairpin", "Sweeper", "Chicane", "Constant Radius", "90-Degree",
		"Esses", "Increasing Radius", "Decreasing Radius", "Chicane", "Sweeper"],
	"highway": ["Constant Radius", "Sweeper", "Sweeper", "90-Degree", "Chicane",
		"Decreasing Radius", "Esses", "Increasing Radius", "Hairpin", "90-Degree"],
	"technical": ["Chicane", "Esses", "90-Degree", "Hairpin", "Decreasing Radius",
		"Esses", "Chicane", "90-Degree", "Hairpin", "Increasing Radius"],
}

static func get_track_layout(circuit_id: String) -> Array:
	return _CIRCUITS.get(circuit_id, _CIRCUITS["default"])

static func get_turn_type(turn: int, circuit_id: String) -> String:
	var layout = get_track_layout(circuit_id)
	return layout[(turn - 1) % layout.size()]
