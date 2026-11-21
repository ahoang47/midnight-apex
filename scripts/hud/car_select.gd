## TOUGE (Gordon, touge-race): car select. All five cars in assets/cars (Austin 2026-11-19). Car choice is visual / model only
## (Austin t102u: every car statted alike, within parity, no mods, no retune). The stats line shows the block in use and the
## parity check against the 1.07 cap; touch buttons (touch_buttons.gd) sit on the arrows and START.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var c = st.get("carsel")
	if c == null: return
	var x0 := 120.0; var x1 := 520.0; var y0 := 236.0; var y1 := 474.0
	lpanel(x0, y0, x1, y1, L_EDGE_L)
	t2(320, y0 + 6, "CHOOSE CARS", 16, L_AMBER, false, "m", true, false, true)
	var rows: Array = c.rows
	for i in rows.size():
		var r: Dictionary = rows[i]; var ry := 270.0 + i * 52.0
		var sel: bool = int(c.sel) == i
		if sel: outline(cut_panel(204, ry, 436, ry + 40, 5.0), L_AMBER)
		t2(320, ry + 3, String(r.label), 10, L_DIM, false, "m", true, false, true)
		t2(320, ry + 15, String(r.car), 18, L_WHITE if sel else L_EDGE_L, false, "m", true, false, true)
	t2(320, 376, String(c.stats), 10, SUB, false, "m", true, false, true)
	t2(320, 390, String(c.parity), 10, CHECK_GREEN if bool(c.ok) else Color8(232, 40, 44), false, "m", true, false, true)
	t2(320, 404, String(c.source), 9, L_DIMMER, false, "m", true, false, false)
