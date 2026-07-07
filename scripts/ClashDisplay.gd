extends Node

const COLORS = {
	Globals.Stance.ATTACK: Color("#dc2626"),
	Globals.Stance.DEFEND: Color("#16a34a"),
	Globals.Stance.NEUTRAL: Color("#d97706"),
}

@onready var p1_panel: Panel = $CanvasLayer/BottomBar/PlayerColumn/P1Panel
@onready var p2_panel: Panel = $CanvasLayer/BottomBar/PlayerColumn/P2Panel
@onready var p3_panel: Panel = $CanvasLayer/BottomBar/PlayerColumn/P3Panel
@onready var o1_panel: Panel = $CanvasLayer/BottomBar/OpponentColumn/O1Panel
@onready var o2_panel: Panel = $CanvasLayer/BottomBar/OpponentColumn/O2Panel
@onready var o3_panel: Panel = $CanvasLayer/BottomBar/OpponentColumn/O3Panel

@onready var p1_label: Label = $CanvasLayer/BottomBar/PlayerColumn/P1Panel/P1Label
@onready var p2_label: Label = $CanvasLayer/BottomBar/PlayerColumn/P2Panel/P2Label
@onready var p3_label: Label = $CanvasLayer/BottomBar/PlayerColumn/P3Panel/P3Label
@onready var o1_label: Label = $CanvasLayer/BottomBar/OpponentColumn/O1Panel/O1Label
@onready var o2_label: Label = $CanvasLayer/BottomBar/OpponentColumn/O2Panel/O2Label
@onready var o3_label: Label = $CanvasLayer/BottomBar/OpponentColumn/O3Panel/O3Label

func display_summary(player_stances: Array, opponent_stances: Array) -> void:
	var panels = [p1_panel, p2_panel, p3_panel]
	var labels = [p1_label, p2_label, p3_label]
	var stance_names = {Globals.Stance.ATTACK: "ATK", Globals.Stance.DEFEND: "DEF", Globals.Stance.NEUTRAL: "NEU"}

	for i in range(3):
		var ps = player_stances[i] if i < player_stances.size() else Globals.Stance.NEUTRAL
		var os = opponent_stances[i] if i < opponent_stances.size() else Globals.Stance.NEUTRAL

		panels[i].color = COLORS[ps]
		labels[i].text = stance_names[ps]

	var o_panels = [o1_panel, o2_panel, o3_panel]
	var o_labels = [o1_label, o2_label, o3_label]
	for i in range(3):
		var os = opponent_stances[i] if i < opponent_stances.size() else Globals.Stance.NEUTRAL
		o_panels[i].color = COLORS[os]
		o_labels[i].text = stance_names[os]

func reveal_phase(phase_index: int) -> void:
	var panels = [p1_panel, p2_panel, p3_panel]
	if phase_index < panels.size():
		var tween = create_tween()
		tween.tween_property(panels[phase_index], "scale", Vector2(1.1, 1.1), 0.15)
		tween.tween_property(panels[phase_index], "scale", Vector2(1.0, 1.0), 0.15)
