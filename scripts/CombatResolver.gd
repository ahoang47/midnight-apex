class_name CombatResolver

static func resolve_stance(a: int, b: int) -> int:
	if a == b:
		return Globals.StanceOutcome.NEUTRAL
	if (a == Globals.Stance.ATTACK and b == Globals.Stance.NEUTRAL) or \
	   (a == Globals.Stance.NEUTRAL and b == Globals.Stance.DEFEND) or \
	   (a == Globals.Stance.DEFEND and b == Globals.Stance.ATTACK):
		return Globals.StanceOutcome.WIN
	return Globals.StanceOutcome.LOSS

static func clash_mult(outcome: int) -> float:
	return 1.0 + Globals.CLASH_STAKES * outcome

static func compute_damage(pow_stat: float, qte_factor_val: float, clash_mult_val: float, battle_mult_val: float) -> float:
	return max(0.0, pow_stat * qte_factor_val * clash_mult_val * battle_mult_val)

static func damage_mitigation(en_stat: float, qte_factor_val: float) -> float:
	var reduction = (en_stat / 1000.0) * Globals.MITIGATION_PER_1000 * qte_factor_val
	return max(Globals.MITIGATION_FLOOR, 1.0 - reduction)

static func qte_factor_val(score: float) -> float:
	return score / Globals.QTE_NORMALIZER

static func apply_han_qte_mod(qte_score: float, han_pct: float) -> float:
	return qte_score * (1.0 + Globals.HAN_QTE_WEIGHT * (han_pct - 1.0 / 3.0))

static func resolve_battle(player_cards: Array, opponent_cards: Array) -> Array:
	var outcomes: Array = []
	for i in range(player_cards.size()):
		outcomes.append(resolve_stance(player_cards[i], opponent_cards[i]))
	return outcomes

static func battle_winner(outcomes: Array) -> String:
	var score = 0
	for o in outcomes:
		score += o
	if score > 0:
		return "Player"
	elif score < 0:
		return "Opponent"
	else:
		return "Tie"

static func battle_multiplier(outcome_sum: int) -> float:
	return 1.0 + Globals.BATTLE_BONUS * abs(outcome_sum)

static func qte_rubber_band(player_gap: float, threshold: float,
		p_qte: float, o_qte: float) -> Dictionary:
	var result = {}
	var blend = 0.0
	if threshold > 0:
		blend = min(1.0, abs(player_gap) / threshold)
	else:
		blend = 1.0 if player_gap != 0 else 0.0

	if player_gap > 0:
		result["p_damage_qte"] = p_qte
		result["p_mitigation_qte"] = p_qte + (1.0 - p_qte) * blend
		result["o_damage_qte"] = o_qte + (1.0 - o_qte) * blend
		result["o_mitigation_qte"] = o_qte
	elif player_gap < 0:
		result["p_damage_qte"] = p_qte + (1.0 - p_qte) * blend
		result["p_mitigation_qte"] = p_qte
		result["o_damage_qte"] = o_qte
		result["o_mitigation_qte"] = o_qte + (1.0 - o_qte) * blend
	else:
		result["p_damage_qte"] = p_qte
		result["p_mitigation_qte"] = p_qte
		result["o_damage_qte"] = o_qte
		result["o_mitigation_qte"] = o_qte

	return result
