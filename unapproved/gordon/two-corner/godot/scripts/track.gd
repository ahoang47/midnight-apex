## Display-only corner path + lane + visual-gap + camera helpers (mirror of threejs/src/track.js).
extends RefCounted
var S: float; var R: float; var A: float; var E: float; var sgn: float; var length: float

## road.by_code[code] = {corner_radius_m, corner_angle_deg} (display PLACEHOLDERS, spec/display.json)
static func for_corner(dir: String, road: Dictionary, code: String):
	var g: Dictionary = road.by_code.get(code, {"corner_radius_m": 20.0, "corner_angle_deg": 90.0})
	return new(dir, road.straight_m, g.corner_radius_m, deg_to_rad(g.corner_angle_deg), road.exit_m)

## StraightRoad (§13.1): one long straight
static func straight(len: float):
	return new("L", len, 1.0, 0.0, 0.0)

func _init(dir: String, s_: float, r_: float, a_: float, e_: float) -> void:
	S = s_; R = r_; A = a_; E = e_
	sgn = 1.0 if dir == "L" else -1.0
	length = S + R * A + E

## {x, z, tx, tz}; forward is -Z (guide §0.1)
func at(s: float) -> Dictionary:
	if s <= S:
		return {"x": 0.0, "z": -s, "tx": 0.0, "tz": -1.0}
	if s <= S + R * A:
		var th := (s - S) / R
		return {"x": sgn * (-R + R * cos(th)), "z": -S - R * sin(th), "tx": -sgn * sin(th), "tz": -cos(th)}
	var e := at(S + R * A)
	var u := s - S - R * A
	return {"x": e.x + e.tx * u, "z": e.z + e.tz * u, "tx": e.tx, "tz": e.tz}

## lateral d: right = tangent x up (guide §0.1); s < 0 continues the entry straight behind
func point(s: float, d: float) -> Dictionary:
	if s < 0.0:
		return {"x": d, "z": -s, "tx": 0.0, "tz": -1.0}
	var p := at(s)
	return {"x": p.x - p.tz * d, "z": p.z + p.tx * d, "tx": p.tx, "tz": p.tz}

static func inside_sign(dir: String) -> float:
	return -1.0 if dir == "L" else 1.0

static func lane_offset(lane: String, dir: String, w: float) -> float:
	if lane == "center": return 0.0
	return (inside_sign(dir) if lane == "inside" else -inside_sign(dir)) * w

## asymmetric visual gap (display only; PLACEHOLDER constants in spec/display.json)
static func rival_draw_offset(lead: float, vg: Dictionary) -> float:
	if lead <= 0.0:
		return minf(maxf(vg.min_spacing_m, -lead * vg.gap_scale_m_per_lead), vg.lead_cap_ahead_m)
	return -maxf(vg.min_spacing_m, lead * vg.gap_scale_m_per_lead)

## authored corner-camera control points (guide §13.3; keyframes are PLACEHOLDERS)
func corner_cam_points(dir: String, cc: Dictionary) -> Array:
	var out := []
	for k in cc.points:
		var p := point(S + R * A * float(k.a), float(k.d_in) * inside_sign(dir))
		out.append(Vector3(p.x, k.h, p.z))
	return out

static func smooth(k: float) -> float:
	k = clampf(k, 0.0, 1.0)
	return k * k * (3.0 - 2.0 * k)
