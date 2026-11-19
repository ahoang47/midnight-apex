## rear-view mirror frame (post_lsc.py:46-48); the image itself is composited by the post shader
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	draw_rect(Rect2(221.5, 13.5, 197, 69), Color8(110, 127, 151), false, 1.0); draw_rect(Rect2(222.5, 14.5, 195, 67), Color8(15, 20, 30), false, 1.0)
	t2(291, 84, "REAR VIEW", 9, L_DIM)
