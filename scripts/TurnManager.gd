extends Node

enum State { START, STRAIGHT, CORNER_PLAYBACK, DAMAGE_BATCH, END_TURN, MATCH_COMPLETE }

var state: int = State.START
var turn_number: int = 0
var current_turn_type: String = ""
var last_exit_stance: int = -1
var last_turn_type: int = -1
var locked_out_stances: Array = []

var player_stats: CombatantStats
var opponent_stats: CombatantStats
var match_config: MatchConfig

var player_deck: Deck
var opponent_deck: Deck

var player_hand: Array = []
var opponent_hand: Array = []

var player_picks: Array = []
var opponent_picks: Array = []

var player_cum_dp: float = 0.0
var opponent_cum_dp: float = 0.0
var player_max_hp: float = 0.0
var opponent_max_hp: float = 0.0

var _rng: RandomNumberGenerator

@onready var straight_timer: StraightTimer = $CanvasLayer/TopBar/CornerTimerBar
@onready var card_hand_ui: CardHandUI = $CanvasLayer
@onready var face_controller: FaceController = $FaceController
@onready var signal_bus: Node = get_node("/root/SignalBus")

func _ready() -> void:
	_rng = RandomNumberGenerator.new()
	_rng.randomize()
	signal_bus.connect("card_selected", Callable(self, "_on_card_selected"))
	signal_bus.connect("phase_pick_timeout", Callable(self, "_on_phase_pick_timeout"))
	straight_timer.connect("phase_timeout", Callable(self, "_on_timer_phase_timeout"))
	straight_timer.connect("straight_complete", Callable(self, "_on_straight_complete"))

func start_match(cfg: MatchConfig) -> void:
	match_config = cfg
	player_stats = cfg.player_stats
	opponent_stats = cfg.opponent_stats
	player_max_hp = player_stats.level * Globals.HP_PER_LEVEL
	opponent_max_hp = opponent_stats.level * Globals.HP_PER_LEVEL

	if cfg.deterministic and cfg.seed != 0:
		_rng.seed = cfg.seed

	player_deck = Deck.build(player_stats.pow, player_stats.en, player_stats.han, false, _rng)
	opponent_deck = Deck.build(opponent_stats.pow, opponent_stats.en, opponent_stats.han, true, _rng)

	turn_number = 0
	state = State.START
	_begin_straight()

func _begin_straight() -> void:
	turn_number += 1
	state = State.STRAIGHT
	current_turn_type = TrackData.get_turn_type(turn_number, "")

	player_hand = player_deck.draw(6)
	opponent_hand = opponent_deck.prepare_turn_hand()

	signal_bus.emit_signal("straight_started", turn_number, current_turn_type, [], [])

	card_hand_ui.on_hand_dealt(player_hand)
	straight_timer.start()

	var entry = ArchetypeData.get_meta_archetype(opponent_stats.name)
	var entry_stance = TurnTypeData.get_stance_sequence(current_turn_type, entry)[0]
	var apex_stance = TurnTypeData.get_stance_sequence(current_turn_type, entry)[1]
	var exit_stance = TurnTypeData.get_stance_sequence(current_turn_type, entry)[2]
	face_controller.set_face_sequence([entry_stance, apex_stance, exit_stance])

	locked_out_stances = Globals.get_locked_out(last_exit_stance, last_turn_type, track_type_to_int(current_turn_type))
	card_hand_ui.set_locked_out(locked_out_stances)

	signal_bus.emit_signal("phase_pick", 0, "ENTRY")
	card_hand_ui.on_phase_pick(0)

func _on_card_selected(stance: int) -> void:
	var phase = _get_current_pick_index()
	player_picks.append(stance)
	var opp_stance = AIPicker.pick_card(
		opponent_hand, player_hand, phase, opponent_stats.name,
		player_picks.size() - 1, [], turn_number, player_picks, _rng
	)
	opponent_picks.append(opp_stance)

	if player_picks.size() >= Globals.PICKS_PER_TURN:
		_on_all_picks_done()
	else:
		var next_phase = _get_current_pick_index()
		var phase_names = ["ENTRY", "APEX", "EXIT"]
		signal_bus.emit_signal("phase_pick", next_phase, phase_names[next_phase])
		card_hand_ui.on_phase_pick(next_phase)

func _on_phase_pick_timeout(phase_index: int) -> void:
	card_hand_ui.on_pick_timeout(phase_index)

func _on_timer_phase_timeout(phase_index: int) -> void:
	if player_picks.size() <= phase_index:
		card_hand_ui.on_pick_timeout(phase_index)

func _get_current_pick_index() -> int:
	return player_picks.size()

func _on_all_picks_done() -> void:
	straight_timer.stop()
	state = State.CORNER_PLAYBACK

	signal_bus.emit_signal("corner_started", player_picks, opponent_picks)

	var outcomes = CombatResolver.resolve_battle(player_picks, opponent_picks)
	for i in range(outcomes.size()):
		signal_bus.emit_signal("clash_resolved", i, player_picks[i], opponent_picks[i], outcomes[i])

	_compute_damage()

func _compute_damage() -> void:
	state = State.DAMAGE_BATCH

	var outcome_sum = 0
	var outcomes = []
	for i in range(player_picks.size()):
		var o = CombatResolver.resolve_stance(player_picks[i], opponent_picks[i])
		outcomes.append(o)
		outcome_sum += o

	var battle_mult = CombatResolver.battle_multiplier(outcome_sum)
	var p_qte_val = 7.0
	var o_qte_val = 5.0

	var p_han_pct = player_stats.han / (player_stats.pow + player_stats.en + player_stats.han) if (player_stats.pow + player_stats.en + player_stats.han) > 0 else 1.0 / 3.0
	var o_han_pct = opponent_stats.han / (opponent_stats.pow + opponent_stats.en + opponent_stats.han) if (opponent_stats.pow + opponent_stats.en + opponent_stats.han) > 0 else 1.0 / 3.0
	p_qte_val = CombatResolver.apply_han_qte_mod(p_qte_val, p_han_pct)
	o_qte_val = CombatResolver.apply_han_qte_mod(o_qte_val, o_han_pct)

	var p_qte_factor = CombatResolver.qte_factor_val(p_qte_val)
	var o_qte_factor = CombatResolver.qte_factor_val(o_qte_val)
	p_qte_factor = clamp(p_qte_factor, 0.0, 1.0)
	o_qte_factor = clamp(o_qte_factor, 0.0, 1.0)

	var avg_hp = (player_max_hp + opponent_max_hp) / 2.0
	var threshold = avg_hp * Globals.RUBBER_BAND_PCT
	var gap = player_cum_dp - opponent_cum_dp
	var rb = CombatResolver.qte_rubber_band(gap, threshold, p_qte_factor, o_qte_factor)

	var p_total_dp = 0.0
	var o_total_dp = 0.0

	for i in range(outcomes.size()):
		var p_cm = CombatResolver.clash_mult(outcomes[i])
		var o_outcome = -outcomes[i]
		var o_cm = CombatResolver.clash_mult(o_outcome)

		var p_dp = CombatResolver.compute_damage(player_stats.pow, rb["p_damage_qte"], p_cm, battle_mult)
		var o_dp = CombatResolver.compute_damage(opponent_stats.pow, rb["o_damage_qte"], o_cm, battle_mult)

		p_total_dp += p_dp
		o_total_dp += o_dp

	var p_avg = p_total_dp / outcomes.size()
	var o_avg = o_total_dp / outcomes.size()

	var p_mit = CombatResolver.damage_mitigation(player_stats.en, rb["p_mitigation_qte"])
	var o_mit = CombatResolver.damage_mitigation(opponent_stats.en, rb["o_mitigation_qte"])

	var player_turn_dp = o_avg * p_mit
	var opponent_turn_dp = p_avg * o_mit

	player_cum_dp += player_turn_dp
	opponent_cum_dp += opponent_turn_dp

	signal_bus.emit_signal("damage_batch_done", player_turn_dp, opponent_turn_dp, player_cum_dp, opponent_cum_dp, battle_mult)

	_end_turn()

func _end_turn() -> void:
	state = State.END_TURN

	player_deck.end_turn(player_picks, _get_unpicked())
	opponent_deck.end_turn(opponent_picks, _get_unpicked_opponent())

	last_exit_stance = player_picks[2] if player_picks.size() > 2 else -1
	last_turn_type = track_type_to_int(current_turn_type)
	player_picks = []
	opponent_picks = []

	signal_bus.emit_signal("turn_ended", turn_number)

	if turn_number >= match_config.max_turns:
		state = State.MATCH_COMPLETE
		var winner = _determine_winner()
		signal_bus.emit_signal("match_ended", winner, player_stats.name, opponent_stats.name)
	else:
		_begin_straight()

func _get_unpicked() -> Array:
	var picked_set = {}
	for s in player_picks:
		picked_set[s] = picked_set.get(s, 0) + 1
	var unpicked: Array = []
	for s in player_hand:
		if picked_set.get(s, 0) > 0:
			picked_set[s] -= 1
		else:
			unpicked.append(s)
	return unpicked

func _get_unpicked_opponent() -> Array:
	var picked_set = {}
	for s in opponent_picks:
		picked_set[s] = picked_set.get(s, 0) + 1
	var unpicked: Array = []
	for s in opponent_hand:
		if picked_set.get(s, 0) > 0:
			picked_set[s] -= 1
		else:
			unpicked.append(s)
	return unpicked

func _determine_winner() -> String:
	var player_pos = player_cum_dp / opponent_max_hp if opponent_max_hp > 0 else 0.0
	var opponent_pos = opponent_cum_dp / player_max_hp if player_max_hp > 0 else 0.0
	if player_pos > opponent_pos:
		return player_stats.name
	return opponent_stats.name

func track_type_to_int(type_name: String) -> int:
	var types = TrackData.TURN_TYPES
	for i in range(types.size()):
		if types[i] == type_name:
			return i
	return -1
