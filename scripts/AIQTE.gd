class_name AIQTE

const TYPICAL_QTE: float = 7.0

static func generate_qte(level: int, encounter_type: String,
		rng: RandomNumberGenerator,
		deterministic: bool,
		han_pct: float) -> float:
	var ratio = _encounter_ratio(encounter_type)
	var raw = TYPICAL_QTE * ratio
	if not deterministic:
		raw += rng.randf_range(-0.3, 0.3)
	return CombatResolver.apply_han_qte_mod(raw, han_pct)

static func _encounter_ratio(encounter_type: String) -> float:
	match encounter_type:
		"wild":
			return 0.75
		"lieutenant":
			return 1.1
		"boss":
			return 1.2
		_:
			return 1.0
