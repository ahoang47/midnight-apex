class_name AIPicker

static func pick_card(hand: Array, opponent_hand: Array, phase_index: int,
		personality_name: String, clash_index: int,
		previous_clashes: Array, turn_number: int,
		player_stance_history: Array,
		rng: RandomNumberGenerator) -> int:
	var personality = PersonalityData.get_personality(personality_name)
	var phase = personality["phases"][phase_index]
	var override = phase.get("behavior_override", "")

	if override != "":
		return _apply_override(override, hand, opponent_hand, clash_index,
			previous_clashes, turn_number, player_stance_history, rng)

	var phase_type = phase.get("phase_type", Globals.PhaseType.AGGRESSIVE)
	if phase_type == Globals.PhaseType.UNPREDICTABLE:
		if rng.randf() < 0.3:
			return hand[rng.randi_range(0, hand.size() - 1)]
		return _highest_ev(hand, opponent_hand)

	var scores = {}
	var weights = phase.get("weights", {})
	for card in hand:
		var ev = _ev_weight(card, opponent_hand)
		var pw = weights.get(card, 0.0) if clash_index != 2 else 0.0
		var rand_val = rng.randf_range(-0.5, 0.5)
		scores[card] = ev + pw + rand_val

	return _max_score_key(scores)

static func _ev_weight(card: int, opponent_hand: Array) -> float:
	if opponent_hand.is_empty():
		return 0.0
	var total = 0.0
	for oc in opponent_hand:
		total += CombatResolver.resolve_stance(card, oc)
	return total / opponent_hand.size()

static func _highest_ev(hand: Array, opponent_hand: Array) -> int:
	var best = hand[0]
	var best_score = _ev_weight(best, opponent_hand)
	for card in hand:
		var score = _ev_weight(card, opponent_hand)
		if score > best_score:
			best_score = score
			best = card
	return best

static func _apply_override(override: String, hand: Array, opponent_hand: Array,
		clash_index: int, previous_clashes: Array, turn_number: int,
		player_stance_history: Array, rng: RandomNumberGenerator) -> int:
	match override:
		"highest_ev":
			return _highest_ev(hand, opponent_hand)
		"second_highest_ev":
			var sorted_cards = _sort_by_ev(hand, opponent_hand)
			return sorted_cards[1] if sorted_cards.size() > 1 else sorted_cards[0]
		"third_highest_ev":
			var sorted_cards = _sort_by_ev(hand, opponent_hand)
			return sorted_cards[2] if sorted_cards.size() > 2 else sorted_cards[-1]
		"alternate":
			var pattern = [Globals.Stance.ATTACK, Globals.Stance.DEFEND, Globals.Stance.ATTACK]
			if turn_number % 2 == 0:
				pattern = [Globals.Stance.DEFEND, Globals.Stance.ATTACK, Globals.Stance.DEFEND]
			var preferred = pattern[clash_index]
			for c in hand:
				if c == preferred:
					return c
			return _highest_ev(hand, opponent_hand)
		"counter":
			if player_stance_history.is_empty():
				return _highest_ev(hand, opponent_hand)
			var most_common = _most_common_stance(player_stance_history)
			var counters = {
				Globals.Stance.ATTACK: Globals.Stance.DEFEND,
				Globals.Stance.DEFEND: Globals.Stance.NEUTRAL,
				Globals.Stance.NEUTRAL: Globals.Stance.ATTACK,
			}
			var target = counters.get(most_common, Globals.Stance.NEUTRAL)
			for c in hand:
				if c == target:
					return c
			return _highest_ev(hand, opponent_hand)
		"repeat_win":
			var winning = []
			for cr in previous_clashes:
				if cr.get("outcome", 0) == Globals.StanceOutcome.WIN:
					winning.append(cr.get("opponent_card", Globals.Stance.NEUTRAL))
			if winning.is_empty():
				return _highest_ev(hand, opponent_hand)
			var target = winning[-1]
			for c in hand:
				if c == target:
					return c
			return _highest_ev(hand, opponent_hand)
		_:
			return _highest_ev(hand, opponent_hand)

static func _sort_by_ev(hand: Array, opponent_hand: Array) -> Array:
	var scored = []
	for card in hand:
		scored.append({"card": card, "ev": _ev_weight(card, opponent_hand)})
	scored.sort_custom(func(a, b): return a["ev"] > b["ev"])
	var result = []
	for s in scored:
		result.append(s["card"])
	return result

static func _max_score_key(scores: Dictionary) -> int:
	var best_card = scores.keys()[0]
	var best_score = scores[best_card]
	for card in scores:
		if scores[card] > best_score:
			best_score = scores[card]
			best_card = card
	return best_card

static func _most_common_stance(history: Array) -> int:
	var counts = {}
	for s in history:
		counts[s] = counts.get(s, 0) + 1
	var best = Globals.Stance.ATTACK
	var best_count = 0
	for s in counts:
		if counts[s] > best_count:
			best_count = counts[s]
			best = s
	return best
