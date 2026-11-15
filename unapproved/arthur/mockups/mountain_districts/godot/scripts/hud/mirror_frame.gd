## rear-view mirror frame (post_lsc.py:46-48); the image itself is composited by the post shader.
## District mockup copy: st.inset = {"rect": [x, y, w, h], "label": "REAR VIEW" | "AHEAD"} moves / resizes the inset
## (mouse options A and B). Without it the frame is drawn exactly as before.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	if not st.has("inset"):
		draw_rect(Rect2(221.5, 13.5, 197, 69), Color8(110, 127, 151), false, 1.0); draw_rect(Rect2(222.5, 14.5, 195, 67), Color8(15, 20, 30), false, 1.0)
		t2(291, 84, "REAR VIEW", 9, L_DIM)
		return
	var r: Array = st.inset.rect
	var x := float(r[0]); var y := float(r[1]); var w := float(r[2]); var h := float(r[3])
	draw_rect(Rect2(x - 2.5, y - 2.5, w + 5, h + 5), Color8(110, 127, 151), false, 1.0); draw_rect(Rect2(x - 1.5, y - 1.5, w + 3, h + 3), Color8(15, 20, 30), false, 1.0)
	var lab := String(st.inset.get("label", "REAR VIEW"))
	t2(x + w * 0.5 - sw(lab, 9) * 0.5, y + h + 4.0, lab, 9, L_DIM)
