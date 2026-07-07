class_name CardHandUI
extends CanvasLayer

@onready var attack_button: Button = $CenterContent/CardPanel/AttackButton
@onready var defend_button: Button = $CenterContent/CardPanel/DefendButton
@onready var steady_button: Button = $CenterContent/CardPanel/SteadyButton
@onready var phase_prompt_label: Label = $CenterContent/CardPanel/PhasePromptLabel

var _counts: Dictionary = {}
var _locked_out: Array = []
var _phase_active: bool = false

signal card_selected(stance)

func on_hand_dealt(hand: Array) -> void:
	_counts = Deck.hand_stance_counts(hand)
	attack_button.text = "ATTACK (x" + str(_counts[Globals.Stance.ATTACK]) + ")"
	defend_button.text = "DEFEND (x" + str(_counts[Globals.Stance.DEFEND]) + ")"
	steady_button.text = "STEADY (x" + str(_counts[Globals.Stance.NEUTRAL]) + ")"
	_disable_all_buttons()

func on_phase_pick(phase_index: int) -> void:
	_phase_active = true
	if phase_index == 0:
		if Globals.EXIT_LOCKOUT_ENABLED:
			_update_button_states()
		else:
			_enable_all_with_counts()
	else:
		_enable_all_with_counts()

func on_card_selected_ui(stance: int) -> void:
	_counts[stance] -= 1
	_update_button_labels()
	_disable_all_buttons()
	_phase_active = false
	emit_signal("card_selected", stance)

func on_pick_timeout(phase_index: int) -> void:
	if not _phase_active:
		return
	var best = _highest_count_stance(phase_index)
	_counts[best] -= 1
	_update_button_labels()
	_disable_all_buttons()
	_phase_active = false
	emit_signal("card_selected", best)

func _enable_all_with_counts() -> void:
	attack_button.disabled = _counts[Globals.Stance.ATTACK] <= 0
	defend_button.disabled = _counts[Globals.Stance.DEFEND] <= 0
	steady_button.disabled = _counts[Globals.Stance.NEUTRAL] <= 0

func _update_button_states() -> void:
	attack_button.disabled = _counts[Globals.Stance.ATTACK] <= 0 or Globals.Stance.ATTACK in _locked_out
	defend_button.disabled = _counts[Globals.Stance.DEFEND] <= 0 or Globals.Stance.DEFEND in _locked_out
	steady_button.disabled = _counts[Globals.Stance.NEUTRAL] <= 0 or Globals.Stance.NEUTRAL in _locked_out

func _update_button_labels() -> void:
	attack_button.text = "ATTACK (x" + str(max(0, _counts[Globals.Stance.ATTACK])) + ")"
	defend_button.text = "DEFEND (x" + str(max(0, _counts[Globals.Stance.DEFEND])) + ")"
	steady_button.text = "STEADY (x" + str(max(0, _counts[Globals.Stance.NEUTRAL])) + ")"

func _disable_all_buttons() -> void:
	attack_button.disabled = true
	defend_button.disabled = true
	steady_button.disabled = true

func _highest_count_stance(phase_index: int) -> int:
	var best = Globals.Stance.ATTACK
	var best_count = _counts[best]
	for s in [Globals.Stance.DEFEND, Globals.Stance.NEUTRAL]:
		if _counts[s] > best_count and not (s in _locked_out and phase_index == 0):
			best = s
			best_count = _counts[s]
	return best

func set_locked_out(stances: Array) -> void:
	_locked_out = stances
