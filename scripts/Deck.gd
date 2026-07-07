class_name Deck

var _draw: Array
var _discard: Array
var _rng: RandomNumberGenerator
var reshuffle_on_end: bool

func _init(draw_pile: Array, rng: RandomNumberGenerator, p_reshuffle_on_end: bool = false) -> void:
	_draw = draw_pile
	_discard = []
	_rng = rng
	reshuffle_on_end = p_reshuffle_on_end

static func _deck_weights(pow_stat: float, en_stat: float, han_stat: float) -> Dictionary:
	var total = pow_stat + en_stat + han_stat
	if total == 0:
		return {"atk": 1.0 / 3.0, "def": 1.0 / 3.0, "neu": 1.0 / 3.0}
	var alpha = 0.85
	var beta = 1.0 - alpha
	var wp = alpha * pow_stat / total + beta / 3.0
	var wd = alpha * en_stat / total + beta / 3.0
	var wn = alpha * han_stat / total + beta / 3.0
	var tw = wp + wd + wn
	return {"atk": wp / tw, "def": wd / tw, "neu": wn / tw}

static func build(pow_stat: float, en_stat: float, han_stat: float,
		reshuffle_on_end: bool = false,
		rng: RandomNumberGenerator = null) -> Deck:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	var w = _deck_weights(pow_stat, en_stat, han_stat)
	var a = roundi(192 * w["atk"])
	var d = roundi(192 * w["def"])
	var n = 192 - a - d
	var raw: Array = []
	for _i in range(a):
		raw.append(Globals.Stance.ATTACK)
	for _i in range(d):
		raw.append(Globals.Stance.DEFEND)
	for _i in range(n):
		raw.append(Globals.Stance.NEUTRAL)
	rng.shuffle(raw)
	return Deck.new(raw, rng, reshuffle_on_end)

func draw(n: int = 6) -> Array:
	var available = min(n, _draw.size())
	var hand = _draw.slice(0, available)
	_draw = _draw.slice(available)
	return hand

func prepare_turn_hand(requirements: Dictionary = {}) -> Array:
	var hand = draw(6)
	if requirements.is_empty():
		return hand
	var retries = 0
	while not _hand_satisfies(hand, requirements) and retries < 10:
		_draw.append_array(hand)
		_rng.shuffle(_draw)
		hand = draw(6)
		retries += 1
	return hand

func end_turn(played: Array, unpicked: Array) -> void:
	if reshuffle_on_end:
		_draw.append_array(played)
		_draw.append_array(unpicked)
		_rng.shuffle(_draw)
	else:
		_discard.append_array(played)
		_discard.append_array(unpicked)

static func _hand_satisfies(hand: Array, requirements: Dictionary) -> bool:
	for stance in requirements:
		var min_count = requirements[stance]
		var count = 0
		for c in hand:
			if c == stance:
				count += 1
		if count < min_count:
			return false
	return true

static func hand_stance_counts(hand: Array) -> Dictionary:
	var counts = {}
	counts[Globals.Stance.ATTACK] = 0
	counts[Globals.Stance.DEFEND] = 0
	counts[Globals.Stance.NEUTRAL] = 0
	for c in hand:
		counts[c] = counts.get(c, 0) + 1
	return counts

func remaining() -> int:
	return _draw.size()
