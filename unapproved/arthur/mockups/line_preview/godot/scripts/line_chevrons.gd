## B.5d racing-line preview: a row of flat chevrons on the road, stance-coloured per segment.
extends Node3D
const SPACING := 2.6
const WIDTH := 1.9
const LENGTH := 2.3
const Y := 0.05
const COL := {
	"A": Color8(44, 184, 74),
	"D": Color8(232, 40, 44),
	"S": Color8(240, 200, 40)
}

var mat_cache: Array[ShaderMaterial] = []

func clear() -> void:
	for ch in get_children():
		remove_child(ch)
		ch.queue_free()
	mat_cache.clear()

## segs: array of {s0, s1, d0, d1, stance, hovered}
func build(pth, segs: Array, fog: Color, fog_near: float, fog_far: float) -> void:
	clear()
	var tex: Texture2D = load("res://art/line_chevron.png")
	for seg in segs:
		var s0: float = seg.s0
		var s1: float = seg.s1
		if s1 - s0 < 0.5:
			continue
		var col: Color = COL[String(seg.stance)]
		var hovered: bool = bool(seg.hovered)
		var s := s0 + LENGTH * 0.5
		var i := 0
		while s <= s1 - LENGTH * 0.35:
			# hovered: lighter + slightly gapped (every other chevron a touch dimmer) so it reads as a live variant
			var t := clampf((s - s0) / maxf(0.001, s1 - s0), 0.0, 1.0)
			var ramp := lerpf(0.88, 1.14, t)
			var pulse := 1.22 if hovered else 1.0
			if hovered and i % 2 == 1:
				pulse = 0.72
			var tint := Color(col.r * ramp * pulse, col.g * ramp * pulse, col.b * ramp * pulse)
			tint.r = minf(1.0, tint.r); tint.g = minf(1.0, tint.g); tint.b = minf(1.0, tint.b)
			var d := lerpf(float(seg.d0), float(seg.d1), _smooth(t))
			var q: Dictionary = pth.point(s, d)
			add_child(_chevron(tex, Vector3(q.x, Y, q.z), Vector3(q.tx, 0, q.tz), tint, fog, fog_near, fog_far, hovered))
			s += SPACING
			i += 1

func _smooth(k: float) -> float:
	k = clampf(k, 0.0, 1.0)
	return k * k * (3.0 - 2.0 * k)

func _chevron(tex: Texture2D, pos: Vector3, fwd: Vector3, tint: Color, fog: Color, fog_near: float, fog_far: float, hovered: bool) -> MeshInstance3D:
	fwd = fwd.normalized()
	var right := Vector3.UP.cross(fwd).normalized()
	# Texture tip is at V=1 (bottom of line_chevron.png). Put that tip at +fwd
	# so the point faces the direction of travel, not back at the player.
	var hl := LENGTH * 0.5
	var hw := WIDTH * (0.58 if not hovered else 0.62)
	var v := [
		pos - right * hw - fwd * hl, pos + right * hw - fwd * hl,
		pos + right * hw + fwd * hl, pos - right * hw + fwd * hl
	]
	var uv := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for idx in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uv[idx])
		st.add_vertex(v[idx])
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/chevron.gdshader")
	m.set_shader_parameter("tex", tex)
	m.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	m.set_shader_parameter("gain", 1.0)
	m.set_shader_parameter("fog_color", Vector3(fog.r, fog.g, fog.b))
	m.set_shader_parameter("fog_near", fog_near)
	m.set_shader_parameter("fog_far", fog_far)
	m.render_priority = 2
	mat_cache.append(m)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = m
	mi.extra_cull_margin = 16384.0
	mi.layers = 1  # not in the glow pass
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi
