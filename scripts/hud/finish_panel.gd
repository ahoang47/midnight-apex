## finish: winner + options (keys 1-3, or arrows + Enter), centre panel above the strip
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var wn: String = st.winner
	var pl := cut_panel(170, 300, 470, 398, 8); semi(pl, PANEL); outline(pl, EDGE)
	t2(320, 306, "%s  %.4f vs %.4f" % ["TIE" if wn == "Tie" else ("YOU WIN" if wn == "Player" else "RIVAL WINS"), st.cum_p, st.cum_o], 13, Color("#FFF2CC"), false, "m")
	if st.get("fin") != null:
		var fin: Dictionary = st.fin
		for i in (fin.items as Array).size():
			var sel: bool = i == int(fin.sel); var y := 328.0 + i * 18
			if sel: semi(P([182, y - 2, 458, y - 2, 454, y + 14, 178, y + 14]), AMBER, 200 / 255.0)
			t2(192, y, "%d  %s" % [i + 1, fin.items[i]], 12, INK if sel else EDGE, false, "l", not sel)
		t2(320, 384, "1-3 or Up/Down + Enter", 10, SUB, true, "m")
