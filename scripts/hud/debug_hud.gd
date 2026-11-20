## debug readout (seed / pin / rig / keys), kept small and out of the approved panels. hud.gd moves it to y 64 (selection,
## lock, QTE) or y 106 (under the LINE LOCKED panel during playback / result).
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var x: float = origin().x; var y: float = origin().y
	box(x, y, 178, 36); text(x + 5, y + 4, st.title); text(x + 5, y + 14, st.sub)
	var nt: bool = bool(st.get("no_timer", false))   # TOUGE debug (Austin t119u): F6 toggles the planning / continue timers
	text(x + 5, y + 24, "F9 dump F10 load F6 timer", Color("#ADADC8"))
	if nt:
		box(x, y + 38, 178, 14); text(x + 5, y + 41, "DEBUG: TIMER OFF (F6)", Color("#FFB040"))
