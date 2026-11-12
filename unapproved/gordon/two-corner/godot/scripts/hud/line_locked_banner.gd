## B.5b frame 4 (post_lsc.py:120-130): LINE LOCKED banner over the Entry chase camera, then the QTEs and playback run
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var x0 := 176.0; var y0 := 112.0; var x1 := 404.0; var y1 := 150.0
	semi(cut_panel(x0 - 6, y0 - 4, x1 + 6, y1 + 22, 9), PANEL)
	var slab := P([x0 + 10, y0, x1, y0, x1 - 10, y1, x0, y1])
	var sh := PackedVector2Array()
	for v in slab: sh.append(v + Vector2(2, 3))
	solid(sh, L_AMBER_D); solid(slab, L_AMBER); outline(slab, L_INK)
	draw_line(Vector2(x0 + 12, y0 + 3), Vector2(x1 - 4, y0 + 3), Color8(255, 236, 170), 1.0)
	t2((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 1, "LINE LOCKED", 26, L_INK, true, "m", false, true)
	var ln: String = st.line if String(st.line).length() == 3 else ""
	for k in ln.length():
		var cx := x0 + 22 + k * 70; lchip(cx, y1 + 5, ln[k])
		if k < 2: t2(cx + 57, y1 + 5, ">", 12, L_DIM)
