## car.tscn: wraps a game-ready .glb from assets/cars (Part A binding) with the A.4/A.8 faked-shine shading (per-car values from
## display.json car_shading.<car_id>), wheel hub pivots, blob shadow, headlight throw and the S2000 stand-in lamp glows.
## Moved verbatim from main.gd _load_car (scene refactor 2026-11-12). main.tscn has two instances: PlayerCar (MX5) and RivalCar (S2000).
## @tool: the model shows in the editor (unshaded preview of the .glb); the shading is applied at runtime by setup().
@tool
extends Node3D
const CAR_SH = preload("res://shaders/car.gdshader")
const FX_SH = preload("res://shaders/fx.gdshader")
@export var model: PackedScene:
	set(v): model = v; if is_inside_tree(): _spawn_model()
@export var env_texture: Texture2D
## key into display.json car_shading ("mx5" / "s2000")
@export var car_id := "mx5"
var mats: Array[ShaderMaterial] = []

func _ready() -> void:
	_spawn_model()

func _spawn_model() -> void:
	var old := get_node_or_null("Model")
	if old != null: remove_child(old); old.queue_free()
	if model == null: return
	var inst: Node3D = model.instantiate(); inst.name = "Model"
	add_child(inst); move_child(inst, 0)

## runtime only: shade the model and add the decals / glows. Sets meta "root" (the model) and "wheels" (hub pivots).
func setup(art, CS: Dictionary) -> void:
	var inst: Node3D = $Model
	_freeze_and_shade(inst, env_texture, CS[car_id], art.disp, CS)
	set_meta("root", inst)
	set_meta("wheels", _pivot_wheels(inst))
	add_child(art.decal("blob_shadow", 2.1, 4.6, 0.0, false, 1.0))                                          # A.4.4 blob shadow
	add_child(art.decal("headlight_throw", 4.0, 9.0, 2.2 + 4.5, true, float(CS.headlight_throw_strength)))  # A.4.4 reduced strength
	if CS[car_id].glow_node == null:  # S2000 lean has no glow FX in its .glb: stand-in head/tail glow billboards (A.4.3)
		for x in [-0.58, 0.58]:
			var t: MeshInstance3D = art.glow_sprite("glow_tail", Color.WHITE, 0.7, 0.9); t.position = Vector3(x, 0.80, -2.06); add_child(t)
			var h: MeshInstance3D = art.glow_sprite("glow_head", Color.WHITE, 0.9, 0.8); h.position = Vector3(x, 0.66, 2.08); add_child(h)

## wheel meshes are authored at the car origin: wrap each in a pivot at its hub (AABB centre) so it spins in place
func _pivot_wheels(root: Node) -> Array:
	var found: Array = []
	_find_wheels(root, found)
	var pivots: Array = []
	for mi in found:
		var m := mi as MeshInstance3D
		var c: Vector3 = m.transform * m.get_aabb().get_center()
		var par := m.get_parent()
		var pv := Node3D.new(); pv.name = String(m.name) + "_pivot"
		par.add_child(pv); pv.position = c
		m.owner = null; par.remove_child(m); pv.add_child(m)
		m.position -= c
		pivots.append(pv)
	return pivots

func _find_wheels(n: Node, out: Array) -> void:
	if n is MeshInstance3D and RegEx.create_from_string("_Wheel_(FL|FR|RL|RR)$").search(String(n.name)) != null:
		out.append(n)
	for ch in n.get_children(): _find_wheels(ch, out)

func _freeze_and_shade(n: Node, env_tex: Texture2D, cs: Dictionary, disp: Dictionary, CS: Dictionary) -> void:
	if n is RigidBody3D:
		(n as RigidBody3D).freeze = true
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.name.contains("FX_LampGlow"):  # MX5_FX_LampGlow: the car's own glow quads (hidden by default in the .glb), additive unshaded
			var src0 := mi.get_active_material(0)
			var fx := ShaderMaterial.new(); fx.shader = FX_SH
			fx.set_shader_parameter("tex", (src0 as BaseMaterial3D).albedo_texture if src0 is BaseMaterial3D else null)
			fx.render_priority = 6
			for si in mi.mesh.get_surface_count(): mi.set_surface_override_material(si, fx)
			mi.visible = true; mi.layers = 3  # also in the glow-only bloom pass
		elif mi.mesh != null:
			for si in mi.mesh.get_surface_count():
				var src := mi.get_active_material(si)
				var nm: String = src.resource_name if src != null else ""
				var m := ShaderMaterial.new(); m.shader = CAR_SH
				var tex: Texture2D = (src as BaseMaterial3D).albedo_texture if src is BaseMaterial3D else null
				m.set_shader_parameter("albedo_tex", tex); m.set_shader_parameter("has_tex", tex != null)
				m.set_shader_parameter("env_equirect", env_tex)
				var kind := "glass" if nm.contains("Glass") else ("paint" if nm.contains("Paint_Body") else ("softtop" if nm.contains("SoftTop") else "default"))
				var mp: Dictionary = cs.get(kind, cs.default)
				var tint: Array = mp.get("tint", [1, 1, 1]); var et: Array = mp.get("env_tint", tint)
				m.set_shader_parameter("tint", Vector3(tint[0], tint[1], tint[2]))
				m.set_shader_parameter("env_tint", Vector3(et[0], et[1], et[2]))
				var bc: Color = (src as BaseMaterial3D).albedo_color if src is BaseMaterial3D else Color(0.6, 0.6, 0.6)
				m.set_shader_parameter("base_col", Vector3(bc.r, bc.g, bc.b))
				m.set_shader_parameter("spec_scale", float(mp.spec)); m.set_shader_parameter("env_strength", float(mp.env))
				m.set_shader_parameter("ambient", float(CS.ambient)); m.set_shader_parameter("spec_power", float(CS.spec_power))
				m.set_shader_parameter("key_dir", Vector3(CS.key_dir[0], CS.key_dir[1], CS.key_dir[2]))
				m.set_shader_parameter("emissive", nm.contains("Lamp"))
				m.set_shader_parameter("snap_res", Vector2(disp.render.internal_w, disp.render.internal_h))
				mi.set_surface_override_material(si, m)
				mats.append(m)
	for ch in n.get_children(): _freeze_and_shade(ch, env_tex, cs, disp, CS)
