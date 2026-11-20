## TOUGE turnout parking lot (Austin t114u / t121 item 13): a drop-in scene for Arthur's lot art.
## Node path in the running game: WorldVP/Dressing/CourseDressing/TurnoutLot  (scene: res://scenes/turnout_lot.tscn)
## Children (replaceable): Floor, Curbs, StallLines, WheelStops, BackWall, HillTop, Lamps, Props, LotArt.
##   - touge_dressing.gd fills a container procedurally ONLY when it is empty, so instanced glb children under a slot
##     in turnout_lot.tscn replace that layer (Arthur's 16 m two-row kit, 2026-11-19).
##   - Floor / Curbs / StallLines / WheelStops / BackWall / HillTop / Lamps / Props placeholders are built in course
##     coordinates (TurnoutLot itself stays at the identity transform).
##   - LotArt is moved onto the lot frame at build time: origin = road edge at the entrance (course s0), +X = away from the road
##     into the lot, +Z = along travel, +Y = up, pitched to the course grade. Arthur's glbs are authored in that LotArt
##     frame, so touge_dressing.gd copies LotArt.transform onto every slot that already has art (README drop-in note).
##   - Lamps: lamp posts are nodes named Lamp* (placeholder) or lot_lamp* (Arthur's kit); used by the camera guard
##     (post at the node origin, arm toward local -X / the road).
## Art lives at res://assets/env/turnout_lot/*.glb (copied from art/kits/turnout_lot/glb/; art/.gdignore hides the source).
@tool
extends Node3D
class_name TurnoutLot

## container to fill procedurally, or null when the scene already authors it
func slot(nm: String) -> Node3D:
	var c := get_node_or_null(nm) as Node3D
	if c == null:
		c = Node3D.new(); c.name = nm; add_child(c)
	return c if c.get_child_count() == 0 else null

func lamps() -> Array:
	var c := get_node_or_null("Lamps")
	if c == null: return []
	var posts: Array = []
	_find_lamp_posts(c, posts)
	return posts if not posts.is_empty() else c.get_children()

func _find_lamp_posts(n: Node, out: Array) -> void:
	var nm := String(n.name)
	if n is Node3D and (nm.begins_with("lot_lamp") or nm.begins_with("Lamp")):
		out.append(n)
	for ch in n.get_children():
		_find_lamp_posts(ch, out)
