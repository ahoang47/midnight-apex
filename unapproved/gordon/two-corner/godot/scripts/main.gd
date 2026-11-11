## Two-corner test, Godot presentation. Builds everything in code. Logic lives in race_core.gd.
## User args (after --): --script-inputs <file> --shots <dir> --seed N --no-menu   (single look: 640x480, RGB555 + Bayer; no CRT/low-res)
## Main menu (Austin 2026-11-10) unless --script-inputs or --no-menu; --seed N prefills the seed field. headless_run.gd never shows it.
extends Control

const RaceCore = preload("res://scripts/race_core.gd")
const Track = preload("res://scripts/track.gd")
const C = preload("res://scripts/sim_constants.gd")
const Combat = preload("res://scripts/combat.gd")  # display uses the pure resolve_stance only (no RNG)
const CAR_SH = preload("res://shaders/car.gdshader")
const ENV_SH = preload("res://shaders/env.gdshader")
const POST_SH = preload("res://shaders/post.gdshader")
const SCROLL_SH = preload("res://shaders/scroll.gdshader")
const RoadScroller = preload("res://scripts/road_scroller.gd")
const GLOW_SH = preload("res://shaders/glow.gdshader")
const SKY_SH = preload("res://shaders/sky.gdshader")
const FX_SH = preload("res://shaders/fx.gdshader")
const Hud = preload("res://scripts/hud.gd")
const TAG := "640"

var cfg: Dictionary
var disp: Dictionary
var script_in = null
var shots_dir := ""
var core
var world_vp: SubViewport
var mirror_vp: SubViewport
var glow_vp: SubViewport  # glow-only pass for bloom (art_direction.md@55b9063 B.2a: bloom 0.22, 0 threshold; mockup post: glow pass, Gaussian r 3)
var glow_cam: Camera3D
var PAL: Dictionary
var cam: Camera3D
var mirror_cam: Camera3D
var post_rect: TextureRect
var post_mat: ShaderMaterial
var hud
var env_mat: ShaderMaterial
var car_mats: Array[ShaderMaterial] = []
var player_car: Node3D
var rival_car: Node3D
var path
var phase_t := 0.0
var s_player := 8.0
var rival_offset := 0.0
var rival_offset_target := 0.0
var rival_lane_d := 0.0
var qte_t := 0.0
var qte_stopped = null
var reveal := 0
var busy := false
var script_timing := 1.0
var fog_color := Color(0.043, 0.051, 0.102)
# ── scrolling straight / corner camera (display only) ──
var RS: Dictionary
var CC: Dictionary
var scroller
var scroll_mats: Array[ShaderMaterial] = []
var straight_path
var road_W := 5.5
var wheel_nodes := {}
var wheel_angle := 0.0
var clock := 0.0
var rig := "BCH"
var cam_pos := Vector3.ZERO
var cam_look := Vector3.ZERO
var cam_fov := 56.7
var cam_path: Path3D
var cam_follow: PathFollow3D
var cam_curve_built := false
var back_from = null
var back_t := 99.0
var first_corner := true
var pending_snap := false
var leader_changed := false
var result_t := 0.0
var meta := {}
# ── main menu / finish options (display only; START / RESTART always build a fresh RaceCore) ──
var races: Array = []
var mode := "RACE"
var menu := {"items": ["START RACE", "SEED"], "sel": 0, "seed_text": "", "blink": false, "commit": ""}
var fin := {"items": ["RESTART SAME SEED", "NEW RACE", "MAIN MENU"], "sel": 0}
var next_random_seed = null  # test harness preset for NEW RACE / RANDOM
var shot_pre := ""
# ── PLAN THE LINE selection (display/input only; every pick still goes through core.pick(hand index)) ──
const PLAN_ORDER := ["A", "S", "D"]   # rows: Attack / Neutral / Defend = OUT / MID / IN
var plan_sel := 0
# ── B.5b camera stops (display only): stop 0 = Entry (chase, rival visible), 1 = Apex, 2 = Exit (corner geometry, no cars) ──
var SC: Dictionary
var last_stop := 0
var stop_t := 99.0
var stop_from = null
var lock_hold_t := 99.0
var lock_from = null

func _arg(k: String, def = null):
	var a := OS.get_cmdline_user_args()
	var i := a.find(k)
	return a[i + 1] if i >= 0 and i + 1 < a.size() else def

func _json(p: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(p))

func _ready() -> void:
	cfg = _json("res://spec/race_config.json")
	disp = _json("res://spec/display.json")
	RS = disp.road_scroller; CC = disp.corner_cams; SC = disp.select_cam
	scroller = RoadScroller.new(RS)
	road_W = float(disp.lane_width_m) * 1.5 + 1.0
	if _arg("--script-inputs") != null:
		script_in = _json(_arg("--script-inputs"))
	shots_dir = _arg("--shots", "")
	if shots_dir != "": DirAccess.make_dir_recursive_absolute(shots_dir)
	if script_in != null: races = script_in.races if script_in.has("races") else [script_in]
	var seed_v: int = int(races[0].seed) if script_in != null else int(_arg("--seed", "20261113"))
	mode = "RACE" if (script_in != null or OS.get_cmdline_user_args().has("--no-menu")) else "MENU"
	menu.seed_text = _arg("--seed", ""); menu.commit = C.PIN_COMMIT.substr(0, 7)
	if not OS.has_feature("web"): menu.items.append("QUIT")  # Quit: Godot desktop only
	DIST = disp.districts; CS = disp.car_shading; PAL = disp.palette
	_build_viewports()
	straight_path = Track.straight(100000.0)
	player_car = _load_car("res://assets/cars/car_mx5.glb", "res://assets/cars/mx5_env.png", "mx5")
	rival_car = _load_car("res://assets/cars/car_s2000.glb", "res://assets/cars/s2000_env.png", "s2000")
	core = RaceCore.new()
	core.setup(cfg, seed_v)
	_setup_corner()
	if script_in != null:
		_run_script()
	elif OS.get_cmdline_user_args().has("--plan-key-test"):
		_plan_key_test()

## Plan the Line key test: random Up/Down/Left/Right/Enter/Backspace over many seeds; every pick must be an unused hand index of the
## highlighted stance, the cursor never rests on a 'none drawn' stance, and the 3rd Enter locks exactly the chosen stances.
func _plan_key_test() -> void:
	var keys := [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER, KEY_BACKSPACE]
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	var n_lock := 0
	for sd in range(1, 201):
		start_race(sd)
		var chosen := ""
		for step in 60:
			if core.phase != "SELECT": break
			assert(int(_plan_avail()[PLAN_ORDER[plan_sel]]) > 0)
			if _sel_stop() != mini(core.picks.size(), 2): push_error("seed %d: camera stop %d != picks %d" % [sd, _sel_stop(), core.picks.size()]); get_tree().quit(1); return
			var k: int = keys[rng.randi() % keys.size()]
			var before: Array = core.picks.duplicate(); var want: String = PLAN_ORDER[plan_sel]
			handle_key(k)
			if k == KEY_ENTER:
				if core.picks.size() != before.size() + 1 or core.hand[core.picks[-1]] != want:
					push_error("seed %d: Enter picked wrong (%s -> %s, want %s)" % [sd, str(before), str(core.picks), want]); get_tree().quit(1); return
				chosen += want
			elif k == KEY_BACKSPACE:
				if before.size() > 0: chosen = chosen.left(-1)
				if core.picks.size() != maxi(0, before.size() - 1): push_error("seed %d: Backspace" % sd); get_tree().quit(1); return
			elif core.picks != before:
				push_error("seed %d: arrow changed picks" % sd); get_tree().quit(1); return
		if core.phase == "TIMING":
			n_lock += 1
			if core.player_line() != chosen or core.autofilled: push_error("seed %d: locked %s, chose %s" % [sd, core.player_line(), chosen]); get_tree().quit(1); return
			var shown := []   # B.5a panel results (shown during playback) must equal the sim's outcomes
			for i in 3: shown.append(Combat.resolve_stance(core.player_line()[i], core.line[i]))
			core.submit_timing(5.0)
			if str(shown) != str(core.result.outcomes): push_error("seed %d: panel %s != sim %s" % [sd, str(shown), str(core.result.outcomes)]); get_tree().quit(1); return
	print("PLAN KEY TEST PASS: 200 seeds, %d locked by keys; camera stop == picks every step; B.5a panel results == sim outcomes" % n_lock)
	get_tree().quit(0)

# ── viewports, post, HUD ──
func _build_viewports() -> void:
	world_vp = SubViewport.new()
	world_vp.world_3d = World3D.new()  # shared with the mirror viewport (own_world_3d would ignore it)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = fog_color
	world_vp.world_3d.environment = env
	world_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	world_vp.msaa_3d = Viewport.MSAA_DISABLED
	world_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(world_vp)
	cam = Camera3D.new(); cam.fov = disp.camera.fov; cam.near = 0.1; cam.far = 400.0
	world_vp.add_child(cam); cam.current = true
	mirror_vp = SubViewport.new()
	mirror_vp.world_3d = world_vp.world_3d
	mirror_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(mirror_vp)
	mirror_cam = Camera3D.new(); mirror_cam.fov = disp.mirror.fov; mirror_cam.near = float(disp.mirror.near); mirror_cam.far = 300.0
	mirror_vp.add_child(mirror_cam); mirror_cam.current = true
	env_mat = ShaderMaterial.new(); env_mat.shader = ENV_SH
	cam_path = Path3D.new(); world_vp.add_child(cam_path)  # authored corner camera path (§13.3)
	cam_follow = PathFollow3D.new(); cam_follow.loop = false; cam_follow.rotation_mode = PathFollow3D.ROTATION_NONE
	cam_path.add_child(cam_follow)
	post_mat = ShaderMaterial.new(); post_mat.shader = POST_SH
	post_mat.set_shader_parameter("mirror_rect", Vector4(disp.mirror.x, disp.mirror.y, disp.mirror.w, disp.mirror.h))
	post_rect = TextureRect.new(); post_rect.size = Vector2(640, 480); post_rect.stretch_mode = TextureRect.STRETCH_SCALE
	post_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	post_rect.texture = world_vp.get_texture(); post_rect.material = post_mat
	add_child(post_rect)
	hud = Hud.new(); add_child(hud)
	hud.setup(load("res://art/font_6x9.png"), _json("res://art/font.json"), load("res://art/panel9.png"), load("res://art/logo_v3.png"))
	var IW: int = int(disp.render.internal_w); var IH: int = int(disp.render.internal_h)
	world_vp.size = Vector2i(IW, IH)
	mirror_vp.size = Vector2i(int(disp.mirror.w), int(disp.mirror.h))
	post_mat.set_shader_parameter("res", Vector2(IW, IH))
	post_mat.set_shader_parameter("scene_tex", world_vp.get_texture())
	post_mat.set_shader_parameter("mirror_tex", mirror_vp.get_texture())
	glow_vp = SubViewport.new(); glow_vp.world_3d = world_vp.world_3d; glow_vp.size = Vector2i(IW, IH)
	glow_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS; glow_vp.msaa_3d = Viewport.MSAA_DISABLED
	add_child(glow_vp)
	glow_cam = Camera3D.new(); glow_cam.fov = disp.camera.fov; glow_cam.near = 0.1; glow_cam.far = 400.0; glow_cam.cull_mask = 2
	var genv := Environment.new(); genv.background_mode = Environment.BG_COLOR; genv.background_color = Color.BLACK; glow_cam.environment = genv
	glow_vp.add_child(glow_cam); glow_cam.current = true
	post_mat.set_shader_parameter("glow_tex", glow_vp.get_texture())
	post_mat.set_shader_parameter("bloom_k", float(PAL.bloom[0])); post_mat.set_shader_parameter("sat", float(PAL.sat))
	env_mat.set_shader_parameter("snap_res", Vector2(IW, IH))
	_build_sky()

# ── cars ──
## game-ready .glb from assets/cars; A.4/A.8 faked shine with per-car values (README); lamp glow, blob shadow, headlight throw
func _load_car(glb: String, env_png: String, id: String) -> Node3D:
	var holder := Node3D.new()
	var inst: Node3D = (load(glb) as PackedScene).instantiate()
	holder.add_child(inst)
	var env_tex: Texture2D = load(env_png)
	_freeze_and_shade(inst, env_tex, CS[id])
	holder.set_meta("root", inst)
	holder.set_meta("wheels", _pivot_wheels(inst))
	holder.add_child(_decal("blob_shadow", 2.1, 4.6, 0.0, false, 1.0))                                          # A.4.4 blob shadow
	holder.add_child(_decal("headlight_throw", 4.0, 9.0, 2.2 + 4.5, true, float(CS.headlight_throw_strength)))  # A.4.4 reduced strength
	if CS[id].glow_node == null:  # S2000 lean has no glow FX in its .glb: stand-in head/tail glow billboards (A.4.3)
		for x in [-0.58, 0.58]:
			var t := _glow_sprite("glow_tail", Color.WHITE, 0.7, 0.9); t.position = Vector3(x, 0.80, -2.06); holder.add_child(t)
			var h := _glow_sprite("glow_head", Color.WHITE, 0.9, 0.8); h.position = Vector3(x, 0.66, 2.08); holder.add_child(h)
	world_vp.add_child(holder)
	return holder

func _decal(n: String, w: float, l: float, z: float, additive: bool, strength: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(w, l); mi.mesh = pm
	var m := StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.albedo_texture = _tex(n)
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(1, 1, 1, strength); m.disable_fog = true; m.render_priority = 1
	if additive: m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m; mi.position = Vector3(0, 0.03, z)
	return mi

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

func _freeze_and_shade(n: Node, env_tex: Texture2D, cs: Dictionary) -> void:
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
				car_mats.append(m)
	for ch in n.get_children(): _freeze_and_shade(ch, env_tex, cs)

# ── art: stand-in textures from spec/gen_art.py (art_direction Part B recipes, RGB555 + Bayer, lossless import) ──
var DIST: Dictionary
var CS: Dictionary
var tex_cache := {}
var card_mats := {}
var straight_d = null
var corner_d = null
var sky_root: Node3D
var sky_mat: ShaderMaterial
var band_mat: ShaderMaterial
var LAMP_MESH: ArrayMesh
var GLOW_QUAD: QuadMesh

func _tex(n: String) -> Texture2D:
	if not tex_cache.has(n): tex_cache[n] = load("res://art/%s.png" % n)
	return tex_cache[n]

func _fogify(m: ShaderMaterial) -> ShaderMaterial:
	scroll_mats.append(m); m.set_shader_parameter("snap_res", Vector2(disp.render.internal_w, disp.render.internal_h))
	return m

## strip material: v = (metres along + scroll) / tile -> scrolls with the RoadScroller (§14.2)
func _strip_mat(n: String, tile: float) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = SCROLL_SH
	m.set_shader_parameter("tex", _tex(n)); m.set_shader_parameter("tile", tile)
	m.set_meta("scrolls", true)
	return _fogify(m)

## cut-out card material (static UVs)
func _card_mat(n: String) -> ShaderMaterial:
	if not card_mats.has(n):
		var m := ShaderMaterial.new(); m.shader = SCROLL_SH
		m.set_shader_parameter("tex", _tex(n)); m.set_shader_parameter("tile", 1.0); m.set_shader_parameter("scroll_m", 0.0)
		card_mats[n] = _fogify(m)
	return card_mats[n]

func _glow_sprite(n: String, col: Color, size: float, strength: float) -> MeshInstance3D:
	if GLOW_QUAD == null: GLOW_QUAD = QuadMesh.new(); GLOW_QUAD.size = Vector2(1, 1)
	var m := ShaderMaterial.new(); m.shader = GLOW_SH
	m.set_shader_parameter("tex", _tex(n)); m.set_shader_parameter("color", Vector3(col.r, col.g, col.b))
	m.set_shader_parameter("strength", strength); m.set_shader_parameter("size", Vector2(size, size))
	m.set_shader_parameter("snap_res", Vector2(disp.render.internal_w, disp.render.internal_h)); m.render_priority = 5
	glow_mats.append(m)
	var mi := MeshInstance3D.new(); mi.mesh = GLOW_QUAD; mi.material_override = m; mi.extra_cull_margin = 16384.0
	mi.layers = 3  # main view + glow-only bloom pass
	return mi
var glow_mats: Array[ShaderMaterial] = []

## one strip along pth, tessellated across/up (keeps affine warping readable); UV.x 0..1 across/up, UV.y = metres along
func _strip(pth, s0: float, s1: float, d0: float, d1: float, mat: ShaderMaterial, wall := 0.0, y := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nc: int = maxi(1, ceili((wall if wall > 0.0 else absf(d1 - d0)) / 3.0))
	var rows: Array = []
	var s := s0
	while s <= s1 + 1e-6:
		var row: Array = []
		for j in nc + 1:
			var u := float(j) / nc
			var p: Vector3 = _pp(pth, s, d0, y + wall * u) if wall > 0.0 else _pp(pth, s, d0 + (d1 - d0) * u, y)
			row.append([p, Vector2(u, s)])
		rows.append(row); s += 2.0
	for i in range(1, rows.size()):
		for j in nc:
			var q := [rows[i - 1][j], rows[i][j], rows[i - 1][j + 1], rows[i - 1][j + 1], rows[i][j], rows[i][j + 1]]
			for v in q:
				st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	return mi

## card: w x h quad standing on y (plane = across/up, facing along the road). Godot UV v runs top-down.
func _card(n: String, w: float, h: float, y := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var v := [[Vector3(-w / 2, y, 0), Vector2(0, 1)], [Vector3(w / 2, y, 0), Vector2(1, 1)], [Vector3(-w / 2, y + h, 0), Vector2(0, 0)], [Vector3(w / 2, y + h, 0), Vector2(1, 0)]]
	for i in [0, 2, 1, 1, 2, 3]:
		st.set_uv(v[i][1]); st.add_vertex(v[i][0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = _card_mat(n); mi.extra_cull_margin = 16384.0
	return mi

func _cross_card(n: String, w: float, h: float) -> Node3D:
	var g := Node3D.new(); var a := _card(n, w, h); var b := _card(n, w, h); b.rotation.y = PI / 2
	g.add_child(a); g.add_child(b); return g

## lamp: post + arm + head, unlit vertex colour (B.1); same numbers as Three.js lampGeo
func _lamp_mesh() -> ArrayMesh:
	if LAMP_MESH != null: return LAMP_MESH
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var h := 6.5; var pc := Color(0.16, 0.16, 0.18)
	_quad(st, Vector3(-0.1, 0, 0), Vector3(0.1, 0, 0), Vector3(-0.1, h, 0), Vector3(0.1, h, 0), pc)
	_quad(st, Vector3(0, h - 0.1, 0), Vector3(-1.4, h - 0.1, 0), Vector3(0, h + 0.05, 0), Vector3(-1.4, h + 0.05, 0), pc)
	_quad(st, Vector3(-1.0, h - 0.25, 0), Vector3(-1.6, h - 0.25, 0), Vector3(-1.0, h, 0), Vector3(-1.6, h, 0), Color(PAL.lamp))  # emissive head: B.2a #F0C894
	LAMP_MESH = st.commit()
	return LAMP_MESH

## display-only pattern, not the sim RNG (identical to track.js hash)
func _hash(k: float) -> float:
	var x := sin(k * 127.1 + 311.7) * 43758.5453
	return x - floor(x)

## district dressing along a path. Props stream with the scroller so they stay on the pools painted into the road texture.
func _build_district(pth, s0: float, s1: float, dk: String) -> Dictionary:
	var D: Dictionary = DIST[dk]; var per: float = D.lamp_period_m; var W := road_W
	var g := Node3D.new(); var items: Array = []
	var a0 := floorf(s0 / per) * per; var rng: float = ceilf((s1 - a0) / per) * per
	g.add_child(_strip(pth, a0, a0 + rng, -W, W, _strip_mat(dk + "_road", per)))
	var add := func(obj: Node3D, base: float, d: float) -> void:
		g.add_child(obj); items.append({"obj": obj, "base": base, "d": d})
	for n in int(rng / per):
		for L in D.lamps:
			var side: float = L[1]
			var lamp := Node3D.new()
			var post := MeshInstance3D.new(); post.mesh = _lamp_mesh(); post.material_override = env_mat; post.extra_cull_margin = 16384.0; lamp.add_child(post)
			var gl := _glow_sprite("glow_lamp", Color(1, 1, 1), 1.5, 0.9)  # tinted texture (make_tone_tex.py per-lamp), 1.5 m billboard at 0.9 (build_v5.py:276)
			gl.position = Vector3(-1.3, 6.3, 0); lamp.add_child(gl)   # (Phase 5 fix: Phase 4 had this line swallowed by the comment above, so lamp heads had no glow)
			lamp.scale.x = side  # arm reaches over the road on either side
			add.call(lamp, a0 + n * per + float(L[0]), side * (float(D.lamp_post_d_m) if D.has("lamp_post_d_m") else W + 0.6))
	if dk == "touge":
		for sd in [-1.0, 1.0]:
			g.add_child(_strip(pth, a0, a0 + rng, sd * W, sd * (W + float(D.verge_w_m)), _strip_mat("touge_verge", 6.0)))
			g.add_child(_strip(pth, a0, a0 + rng, sd * (W + float(D.wall_d_m)), 0.0, _strip_mat("touge_rail", 4.0), float(D.wall_h_m)))
		var k := 0; var sp: float = D.cedar_spacing_m; var out: float = D.outside_side
		while k * sp < rng:   # B.5b frames (build_lsc.py:221-234): 2 outside cedars + an inside one (p .8) per step
			var trees := []
			for j in 2: trees.append([out * lerpf(D.cedar_out_d_m[0], D.cedar_out_d_m[1], _hash(k * 5 + j)), lerpf(D.cedar_h_m[0], D.cedar_h_m[1], _hash(k * 2 + j + 0.5))])
			if _hash(k * 7 + 0.3) < float(D.cedar_in_p): trees.append([-out * lerpf(D.cedar_in_d_m[0], D.cedar_in_d_m[1], _hash(k * 9 + 0.7)), lerpf(D.cedar_in_h_m[0], D.cedar_in_h_m[1], _hash(k * 4 + 0.9))])
			for ti in trees.size():
				var tr: Array = trees[ti]; var h: float = tr[1]
				var c := _cross_card("touge_cedar_a" if _hash(k + ti * 7) < 0.5 else "touge_cedar_b", h * float(D.cedar_w_ratio), h)
				add.call(c, a0 + k * sp + (_hash(k * 3 + ti) - 0.5) * 4.0, tr[0])
			k += 1
	else:
		var sw: float = D.sidewalk_w_m
		for sd in [-1.0, 1.0]:
			g.add_child(_strip(pth, a0, a0 + rng, sd * W, sd * (W + sw), _strip_mat("street_walk", 4.0), 0.0, 0.02))
			g.add_child(_strip(pth, a0, a0 + rng, sd * (W + sw), 0.0, _strip_mat("street_facade", float(D.facade_tile_m)), float(D.facade_h_m)))
		var k := 0
		while k * 12 < rng:
			var sd := 1.0 if k % 2 else -1.0; var i: int = k % D.neon.size()
			var sign := Node3D.new(); var y := 3.5 + _hash(k) * 3.0
			sign.add_child(_card("street_neon_%d" % i, 0.6, 2.4, y))
			var gl := _glow_sprite("glow_white", Color(D.neon[i]), 3.2, 0.45); gl.position = Vector3(0, y + 1.2, 0); sign.add_child(gl)
			add.call(sign, a0 + k * 12 + 5, sd * (W + sw - 0.7))
			k += 1
		var KINDS := [["street_cut_cone", 0.5, 0.7], ["street_cut_bike", 1.6, 1.1], ["street_cut_plant", 0.9, 1.0], ["street_cut_vending", 1.0, 1.9]]
		k = 0
		while k * float(D.prop_spacing_m) < rng:
			for sd in [-1, 1]:
				if _hash(k * 11 + sd) < 0.35: continue
				var kd: Array = KINDS[int(floor(_hash(k * 13 + sd) * 4))]
				add.call(_card(kd[0], kd[1], kd[2]), a0 + k * float(D.prop_spacing_m) + 2, sd * (W + 1.0 + _hash(k * 17 + sd) * (sw - 1.6)))
			k += 1
	return {"group": g, "items": items, "a0": a0, "range": rng, "pth": pth}

func _stream_district(dd: Dictionary, scroll_m: float) -> void:
	for it in dd.items:
		var s: float = dd.a0 + fposmod(float(it.base) - scroll_m - dd.a0, dd.range)
		var p: Dictionary = dd.pth.point(s, it.d)
		(it.obj as Node3D).position = Vector3(p.x, 0, p.z); (it.obj as Node3D).rotation.y = atan2(p.tx, p.tz)

## painted sky cylinder + skyline/ridge band (B.1); fog colour-matched at the horizon
func _cylinder(r: float, y0: float, y1: float, rep: float) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 48
	for i in n:
		var a0 := TAU * i / n; var a1 := TAU * (i + 1) / n
		var u0 := rep * i / n; var u1 := rep * (i + 1) / n
		var v := [[Vector3(r * sin(a0), y0, r * cos(a0)), Vector2(u0, 1)], [Vector3(r * sin(a1), y0, r * cos(a1)), Vector2(u1, 1)],
			[Vector3(r * sin(a0), y1, r * cos(a0)), Vector2(u0, 0)], [Vector3(r * sin(a1), y1, r * cos(a1)), Vector2(u1, 0)]]
		for k in [0, 2, 1, 1, 2, 3]:
			st.set_uv(v[k][1]); st.add_vertex(v[k][0])
	return st.commit()

func _build_sky() -> void:
	sky_root = Node3D.new(); world_vp.add_child(sky_root)
	sky_mat = ShaderMaterial.new(); sky_mat.shader = SKY_SH
	band_mat = sky_mat  # skyline/ridge band composited in sky.gdshader (r 240, y -3..22, rep 5, as Three.js)
	var sm := MeshInstance3D.new(); sm.mesh = _cylinder(250.0, -125.0, 125.0, 1.0); sm.material_override = sky_mat; sm.extra_cull_margin = 16384.0
	sky_root.add_child(sm)

func _apply_district(dk: String) -> void:
	var D: Dictionary = DIST[dk]; var fc := Color(D.fog)
	var fv := Vector3(fc.r, fc.g, fc.b)
	for m in scroll_mats + car_mats + [env_mat]:
		m.set_shader_parameter("fog_color", fv); m.set_shader_parameter("fog_near", float(D.fog_near)); m.set_shader_parameter("fog_far", float(D.fog_far))
	for m in glow_mats:
		m.set_shader_parameter("fog_near", float(D.fog_near)); m.set_shader_parameter("fog_far", float(D.fog_far))
	world_vp.world_3d.environment.background_color = fc
	sky_mat.set_shader_parameter("tex", _tex(dk + "_sky"))
	band_mat.set_shader_parameter("band_tex", _tex("street_skyline" if dk == "street" else "touge_ridge"))

## StraightRoad + CornerRoad (§13.1), dressed for the upcoming corner's district
func _build_road(dk: String) -> void:
	for d in [straight_d, corner_d]:
		if d != null: d.group.queue_free()
	scroll_mats = scroll_mats.filter(func(m): return card_mats.values().has(m))
	glow_mats.clear()
	straight_d = _build_district(straight_path, RS.straight_from_m, RS.straight_to_m, dk)
	corner_d = _build_district(path, -10.0, path.length, dk)
	world_vp.add_child(straight_d.group); world_vp.add_child(corner_d.group)
	for c in [player_car, rival_car]:  # car head/tail glow sprites keep their fog uniforms in step
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is ShaderMaterial and ((ch as MeshInstance3D).material_override as ShaderMaterial).shader == GLOW_SH:
				glow_mats.append((ch as MeshInstance3D).material_override)
	_apply_district(dk)

func _pp(pth, s: float, d: float, y: float = 0.0) -> Vector3:
	var q: Dictionary = pth.point(s, d)
	return Vector3(q.x, y, q.z)

func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color) -> void:
	for v in [a, c, b, b, c, d]:
		st.set_color(col); st.add_vertex(v)

# ── game flow ──
func _setup_corner() -> void:
	var c: Dictionary = core.corner()
	path = Track.for_corner(c.dir, disp.road, c.corner)
	_build_road(c.district)
	s_player = 8.0; phase_t = 0.0; qte_t = 0.0; qte_stopped = null; reveal = 0; cam_curve_built = false; leader_changed = false
	plan_sel = 0; _plan_fix_sel(0)
	last_stop = 0; stop_t = 99.0; stop_from = null; lock_hold_t = 99.0; lock_from = null
	rival_lane_d = Track.lane_offset(core.entry_tell().lane, c.dir, disp.lane_width_m)
	rival_offset_target = Track.rival_draw_offset(core.lead(), disp.visual_gap)
	scroller.transition_to_straight()
	if first_corner:
		rival_offset = rival_offset_target; back_t = 99.0
	else:
		_return_to_chase()
	first_corner = false

## Full reset for START / RESTART / NEW RACE: a fresh RaceCore (fresh MT19937 seeded from s) and every display-side race variable.
func start_race(s: int) -> void:
	core = RaceCore.new(); core.setup(cfg, s); mode = "RACE"
	scroller = RoadScroller.new(RS); clock = 0.0; wheel_angle = 0.0; back_from = null; back_t = 99.0; pending_snap = false
	leader_changed = false; rival_offset = 0.0; result_t = 0.0; fin.sel = 0; first_corner = true
	_setup_corner()

func to_menu() -> void:
	menu.sel = 0; start_race(core.seed_value); mode = "MENU"  # backdrop only

func _random_seed() -> int:  # display-side RNG, never the sim's
	if next_random_seed != null:
		var s: int = next_random_seed; next_random_seed = null; return s
	return 1 + randi() % 999999999

func _menu_key(k: int) -> void:
	var n: int = (menu.items as Array).size(); var item: String = menu.items[menu.sel]
	if k == KEY_UP: menu.sel = (int(menu.sel) + n - 1) % n
	elif k == KEY_DOWN: menu.sel = (int(menu.sel) + 1) % n
	elif item == "SEED" and k >= KEY_0 and k <= KEY_9 and String(menu.seed_text).length() < 15: menu.seed_text += str(k - KEY_0)
	elif item == "SEED" and k == KEY_BACKSPACE: menu.seed_text = String(menu.seed_text).left(-1)
	elif k == KEY_ENTER or k == KEY_KP_ENTER:
		if item == "START RACE": start_race(String(menu.seed_text).to_int() if menu.seed_text != "" else _random_seed())
		elif item == "SEED": menu.sel = 0
		elif item == "QUIT": get_tree().quit()

func _finish_choose(i: int) -> void:
	if i == 0: start_race(core.seed_value)
	elif i == 1: start_race(_random_seed())
	else: to_menu()

func _finish_key(k: int) -> void:
	if k >= KEY_1 and k <= KEY_3: _finish_choose(k - KEY_1)
	elif k == KEY_LEFT or k == KEY_UP: fin.sel = (int(fin.sel) + 2) % 3
	elif k == KEY_RIGHT or k == KEY_DOWN: fin.sel = (int(fin.sel) + 1) % 3
	elif k == KEY_ENTER or k == KEY_KP_ENTER: _finish_choose(int(fin.sel))

## shared by the keyboard and the restart test harness
func handle_key(k: int) -> void:
	if mode == "MENU": _menu_key(k); return
	if core.phase == "FINISHED": _finish_key(k); return
	if core.phase == "SELECT":
		if k >= KEY_1 and k <= KEY_6: core.pick(k - KEY_1); _plan_fix_sel(0)   # legacy direct hand-index pick (hidden; kept for old scripts)
		elif k == KEY_UP or (k == KEY_LEFT and core.picks.size() == 0): _plan_fix_sel(-1)
		elif k == KEY_DOWN or (k == KEY_RIGHT and core.picks.size() == 0): _plan_fix_sel(1)
		elif k == KEY_BACKSPACE: core.unpick(); _plan_fix_sel(0)
		elif k == KEY_ENTER or k == KEY_KP_ENTER:
			if core.picks.size() >= 3: _do_lock()
			else:
				var idx := _plan_hand_index(PLAN_ORDER[plan_sel])
				if idx >= 0:
					core.pick(idx)
					if core.picks.size() >= 3: _do_lock()   # Enter on EXIT locks the line
					else: _plan_fix_sel(0)
	elif core.phase == "TIMING" and k == KEY_SPACE and qte_stopped == null and lock_hold_t >= float(SC.lock_hold_s):
		qte_stopped = sin(TAU * qte_t / float(disp.qte.period_s))
	elif core.phase == "RESULT" and (k == KEY_ENTER or k == KEY_KP_ENTER) and reveal >= 3:
		core.next()
		if core.phase != "FINISHED": _setup_corner()
		else: _return_to_chase()

## corner plate title: turn type + direction (frames: 'HAIRPIN R'; N90 label from display.json corner_cams / guide §13.3)
func _corner_name(c: Dictionary) -> String:
	var n := {"HP": "HAIRPIN", "N90": "90-DEGREE"}
	return "%s %s" % [n.get(String(c.corner), String(c.corner)), c.dir]

## corner plate map: the corner path squeezed into the plate (forward = up), with the E / A / X stop marks
func _plate_icon() -> Dictionary:
	var pts := []; var arc: float = path.R * path.A
	var s0: float = path.S - 14.0; var s1: float = path.S + arc + 14.0
	for i in 25:
		var q: Dictionary = path.point(lerpf(s0, s1, i / 24.0), 0.0); pts.append(Vector2(q.x, q.z))
	var st := []
	for sv in [path.S - 6.0, path.S + arc * 0.5, path.S + arc + 6.0]:
		var q: Dictionary = path.point(sv, 0.0); st.append(Vector2(q.x, q.z))
	return {"pts": pts, "stops": st}

## stance availability = copies in the hand minus picks already used
func _plan_avail(skip_first := false) -> Dictionary:
	var a := {"A": 0, "S": 0, "D": 0}
	for h in core.hand: a[h] += 1
	for j in core.picks.size():
		if skip_first and j == 0: continue
		a[core.hand[core.picks[j]]] -= 1
	return a

## first unused hand index holding stance k (-1 = none drawn)
func _plan_hand_index(k: String) -> int:
	for i in core.hand.size():
		if core.hand[i] == k and not core.picks.has(i): return i
	return -1

## move the row cursor by dir, skipping stances with none drawn (dir 0 = just make the current row valid)
func _plan_fix_sel(dir: int) -> void:
	var a := _plan_avail()
	for n in 4:
		if n > 0 or dir != 0: plan_sel = (plan_sel + (dir if dir != 0 else 1) + 3) % 3
		if int(a[PLAN_ORDER[plan_sel]]) > 0: return

## END_TURN: swing back to the chase cam (§12.2 transition_to_straight). AUSTIN OVERRIDE (guide §13.2 step 9a): no swing_overtake;
## cars hold their pre-corner spacing through the corner camera and snap to the visual-gap positions when the chase lock is reached.
func _return_to_chase() -> void:
	back_from = {"pos": cam_pos, "look": cam_look}; back_t = 0.0; pending_snap = true

func _maybe_snap() -> void:
	if pending_snap and back_t >= float(CC.transition_to_straight_s):
		rival_offset = rival_offset_target; pending_snap = false

func _in_straight() -> bool: return core.phase == "SELECT" and _sel_stop() == 0  # Apex/Exit stops show the corner geometry (B.5b)

func _place(car: Node3D, pth, s: float, d: float) -> Dictionary:
	var p: Dictionary = pth.point(s, d)
	car.position = Vector3(p.x, 0, p.z)
	car.rotation.y = atan2(p.tx, p.tz)
	(car.get_meta("root") as Node3D).position.y = float(RS.bob_amp_m) * sin(TAU * float(RS.bob_hz) * clock + (1.7 if car == rival_car else 0.0))  # identical bob, no pitch/roll
	for w in car.get_meta("wheels"): (w as Node3D).rotation.x = wheel_angle
	return p

func _qte_score(pos: float) -> float:
	return clampf(roundf(10.0 - 9.0 * absf(pos)), 1.0, 10.0)

func _do_lock() -> void:
	lock_from = {"pos": cam_pos, "look": cam_look, "fov": cam_fov}; lock_hold_t = 0.0
	core.lock(); phase_t = 0.0; scroller.transition_to_corner()  # §13.2/§14.2 transition_to_corner
	await _shot("%slock%d" % [shot_pre, core.corner_index])

func _shot(name: String) -> void:
	if shots_dir == "": return
	busy = true
	_render_hud(); _update_scene()
	meta[name] = {"phase": core.phase, "rig": rig, "uv_offset": scroller.uv_offset, "scroll_m": scroller.scroll_m(), "speed_factor": scroller.factor,
		"cam": [snappedf(cam_pos.x, 0.001), snappedf(cam_pos.y, 0.001), snappedf(cam_pos.z, 0.001)], "s_player": s_player,
		"rival_offset": snappedf(rival_offset, 0.001), "rival_offset_target": snappedf(rival_offset_target, 0.001), "leader_changed": leader_changed}
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(shots_dir.path_join("%s_%s.png" % [name, TAG]))
	busy = false

func dump_state() -> String:
	var tok := RaceCore.encode_token(core.dump())
	print("TC1 token ", tok)
	DisplayServer.clipboard_set(tok)
	var f := FileAccess.open("user://last_state.tc1", FileAccess.WRITE); f.store_string(tok)
	return tok

func load_state(tok: String) -> void:
	var n = RaceCore.new(); n.load_state(cfg, RaceCore.decode_token(tok)); core = n
	first_corner = true
	_setup_corner()
	if core.phase == "RESULT": reveal = 3

func _unhandled_input(e: InputEvent) -> void:
	if script_in != null or not (e is InputEventKey) or not e.pressed or e.echo: return
	var k: int = (e as InputEventKey).keycode
	if mode == "RACE" and k == KEY_F9: dump_state()
	elif mode == "RACE" and k == KEY_F10:
		var t := DisplayServer.clipboard_get()
		if t.begins_with("TC1:"): load_state(t)
	else: handle_key(k)

const SEQ_SELECT_N := 6
const SEQ_SELECT_DT := 0.2
const SEQ_CORNER_N := 8

## frame sequences are timed on the game clock (paused while a shot is taken)
func _wait_game(pred: Callable) -> void:
	while not pred.call(): await get_tree().process_frame

func _run_script() -> void:
	var results := []
	for ri in races.size():
		var nxt: Dictionary = races[ri]
		if ri > 0:  # restart through the same paths the keys use (finish options / main menu)
			var how: String = script_in.restart[ri - 1]
			if how == "same":
				assert(int(nxt.seed) == core.seed_value); handle_key(KEY_1)
			elif how == "new":
				next_random_seed = int(nxt.seed); handle_key(KEY_2)
			else:
				handle_key(KEY_3)
				await _wait_game(func(): return clock > 0.3)
				await _shot("menu_r%d_empty" % ri)
				handle_key(KEY_DOWN)
				for ch in str(int(nxt.seed)): handle_key(KEY_0 + int(ch))
				await _wait_game(func(): return clock > 0.8)
				await _shot("menu_r%d_seed" % ri)
				handle_key(KEY_UP); handle_key(KEY_ENTER)
			var fresh = RaceCore.new(); fresh.setup(cfg, int(nxt.seed))  # restarted state must equal a cold start
			if core.seed_value != int(nxt.seed) or core.rng.draws != fresh.rng.draws or core.line != fresh.line or str(core.hand) != str(fresh.hand) \
					or core.history.size() > 0 or core.cum_p != 0.0 or core.cum_o != 0.0 or core.corner_index != 0:
				push_error("restart %s: dirty state" % how); get_tree().quit(1); return
		await _run_one_race(nxt, "" if ri == 0 else "r%d_" % ri)
		results.append({"engine": "godot-4.6.3(windowed)", "commit": C.PIN_COMMIT, "seed": core.seed_value, "provisional_w1": true,
			"corners": core.history, "player_total": core.cum_p, "opponent_total": core.cum_o, "winner": core.winner(), "rng_draws": core.rng.draws,
			"restart": null if ri == 0 else script_in.restart[ri - 1]})
	var out = results[0] if results.size() == 1 else {"races": results}
	if shots_dir != "":
		var tag: String = TAG
		FileAccess.open(shots_dir.path_join("result_%s.json" % tag), FileAccess.WRITE).store_string(JSON.stringify(out, " ", false, true))
		FileAccess.open(shots_dir.path_join("frames_%s.json" % tag), FileAccess.WRITE).store_string(JSON.stringify({"meta": meta}, " ", false, true))
	get_tree().quit()

func _run_one_race(race: Dictionary, pre: String) -> void:
	var seqs := pre == ""  # full frame sequences for the first race only
	shot_pre = pre
	var lc_last := false
	while core.phase != "FINISHED":
		var ci: int = core.corner_index
		var inp: Dictionary = race.corners[ci]
		if seqs:
			for i in SEQ_SELECT_N:
				await _wait_game(func(): return phase_t >= 0.3 + i * SEQ_SELECT_DT)
				await _shot("seq_select%d_%d" % [ci, i])
		var pk: Array = inp.get("pick", [])
		for j in pk.size():
			if seqs and j > 0:   # B.5b camera stops: Apex / Exit pick shots once the camera has arrived (picks are the scripted hand indices, unchanged)
				_plan_fix_sel(0)
				await _wait_game(func(): return stop_t >= float(SC.move_s) + 0.1)
				await _shot("plan_%s%d" % ["apex" if j == 1 else "exit", ci])
			core.pick(int(pk[j]))
			if seqs and j < 2 and j + 1 < pk.size():
				for m in 3:   # camera-move frames between stops
					await _wait_game(func(): return stop_t >= (m + 1) * float(SC.move_s) / 4.0)
					await _shot("seq_move%d_%d_%d" % [ci, j, m])
		await _do_lock()
		if seqs:
			for m in 3:   # camera back to Entry + LINE LOCKED banner (B.5b frame 4)
				await _wait_game(func(): return lock_hold_t >= (m + 1) * float(SC.lock_hold_s) / 3.2)
				await _shot("seq_lock%d_%d" % [ci, m])
		script_timing = float(inp.timing); qte_stopped = 0.0
		for i in (SEQ_CORNER_N if seqs else 0):
			await _wait_game(func(): return core.phase != "TIMING" or qte_t >= (i + 0.5) / SEQ_CORNER_N * float(disp.playback_s))
			if core.phase != "TIMING": break
			await _shot("seq_corner%d_%d" % [ci, i])
		await _wait_game(func(): return core.phase == "RESULT" and reveal >= 3 and result_t > 0.4)
		await _shot("%sresult%d" % [pre, ci])
		lc_last = leader_changed
		core.next()
		if core.phase != "FINISHED": _setup_corner()
		else: _return_to_chase()
		if seqs and lc_last:
			for i in 6:
				await _wait_game(func(): return back_t >= i * 0.25)
				await _shot("seq_snap%d_%d" % [ci, i])
	await _wait_game(func(): return back_t > float(CC.transition_to_straight_s) + 0.2)
	await _shot("%sfinish" % pre)

func _process(dt: float) -> void:
	dt = minf(dt, 0.05)
	if busy: return
	phase_t += dt; clock += dt; back_t += dt; stop_t += dt
	if core.phase == "SELECT":
		var stp := _sel_stop()
		if stp != last_stop:
			stop_from = {"pos": cam_pos, "look": cam_look, "fov": cam_fov}; stop_t = 0.0; last_stop = stp
	if core.phase == "TIMING": lock_hold_t += dt
	if not (core.phase == "SELECT" and _sel_stop() > 0):   # the straight keeps scrolling at the Entry stop; Apex/Exit stops are still frames of the corner
		scroller.update(dt)
	var v: float = scroller.speed_ms()
	if mode == "MENU": phase_t = 0.0  # backdrop: the straight scrolls, the selection timer never runs
	if core.phase == "SELECT" and phase_t >= RaceCore.STRAIGHT_DURATION and script_in == null:
		_do_lock()  # timer expiry -> auto-fill (guide §4.2)
	if core.phase == "TIMING" and lock_hold_t >= float(SC.lock_hold_s):
		qte_t += dt
		var travel: float = path.S + path.R * path.A + 10.0 - 8.0
		s_player = 8.0 + travel * minf(1.0, qte_t / float(disp.playback_s)); v += travel / float(disp.playback_s)
		if qte_t >= float(disp.playback_s):
			var score: float = script_timing if script_in != null else (C.PLAYER_QTE_MIN if qte_stopped == null else _qte_score(qte_stopped))
			var before: float = core.lead()
			core.submit_timing(score); reveal = 0; phase_t = 0.0; result_t = 0.0
			var after: float = core.lead()
			leader_changed = before != 0.0 and after != 0.0 and signf(before) != signf(after)
			rival_offset_target = Track.rival_draw_offset(after, disp.visual_gap)  # applied at the chase lock (Austin override)
	if core.phase == "RESULT":
		result_t += dt
		reveal = mini(3, int(floor(phase_t / 0.6)) + 1)
	wheel_angle += minf(float(RS.wheel_spin_cap_rad_s), v / 0.31) * dt
	_render_hud(); _update_scene()

## fixed chase camera (B.5b frames: build_lsc.py:245, see display.json camera)
func _chase_pose(pp: Dictionary) -> Array:
	var t := Vector3(pp.tx, 0, pp.tz); var p := Vector3(pp.x, 0, pp.z); var rt := Vector3(-pp.tz, 0, pp.tx)
	var k := 1.0; var cm: Dictionary = disp.camera   # 'fixed' chase camera: frame offsets as given, not mirrored per corner
	return [p - t * float(cm.back) + rt * (k * float(cm.side)) + Vector3(0, cm.height, 0),
		p + t * float(cm.look_ahead) + rt * (k * float(cm.look_side)) + Vector3(0, cm.look_y, 0)]

func _sel_stop() -> int: return mini(core.picks.size(), 2) if core.phase == "SELECT" and mode == "RACE" else 0

## B.5b Apex / Exit stop poses on the corner path: [pos, look, fov]
func _stop_pose(stop: int) -> Array:
	var c: Dictionary = core.corner(); var k: float = Track.inside_sign(String(c.dir)); var arc: float = path.R * path.A
	var q: Dictionary = SC.apex if stop == 1 else SC.exit
	var out_m: float = float(q.cam_out_m)
	var D: Dictionary = DIST[String(c.district)]
	if D.has("sidewalk_w_m"): out_m = minf(out_m, road_W + float(D.sidewalk_w_m) - 0.5)   # Street: stay in front of the facade wall (no Street frame exists; DERIVED)
	var cp: Dictionary = path.point(path.S + arc * float(q.cam_arc), -k * out_m)
	var ts: float = path.S + arc * float(q.tgt_arc) if stop == 1 else path.S + arc + float(q.tgt_after_m)
	var tp: Dictionary = path.point(ts, k * float(q.tgt_in_m))
	return [Vector3(cp.x, q.cam_h, cp.z), Vector3(tp.x, q.tgt_y, tp.z), float(q.fov)]

## camera rig: chase (BCH) / authored corner Path3D (BCL/BCR, §13.3) / swing back to chase. No swing_overtake (Austin override).
func _update_camera(pp: Dictionary) -> void:
	var ch := _chase_pose(pp)
	var c: Dictionary = core.corner()
	var cc = CC.get(c.corner)
	cam_fov = float(disp.camera.fov)
	var stp := _sel_stop()
	if core.phase == "SELECT" and (stp > 0 or (stop_from != null and stop_t < float(SC.move_s))):
		var tgt: Array = _stop_pose(stp) if stp > 0 else [ch[0], ch[1], float(disp.camera.fov)]
		rig = ["BCH", "STA", "STX"][stp]
		if stop_from != null and stop_t < float(SC.move_s):
			var kk := Track.smooth(stop_t / float(SC.move_s))
			cam_pos = (stop_from.pos as Vector3).lerp(tgt[0], kk); cam_look = (stop_from.look as Vector3).lerp(tgt[1], kk); cam_fov = lerpf(float(stop_from.fov), tgt[2], kk)
		else:
			cam_pos = tgt[0]; cam_look = tgt[1]; cam_fov = tgt[2]
		return
	if core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s):   # B.5b: camera returns to Entry, LINE LOCKED, then playback
		rig = "BCH"
		if lock_from != null and lock_hold_t < float(SC.move_s):
			var kk := Track.smooth(lock_hold_t / float(SC.move_s))
			cam_pos = (lock_from.pos as Vector3).lerp(ch[0], kk); cam_look = (lock_from.look as Vector3).lerp(ch[1], kk); cam_fov = lerpf(float(lock_from.fov), cam_fov, kk)
		else:
			cam_pos = ch[0]; cam_look = ch[1]
		return
	if _in_straight() or core.phase == "FINISHED":
		rig = "BCH"
		if back_from != null and back_t < float(CC.transition_to_straight_s):
			var k := Track.smooth(back_t / float(CC.transition_to_straight_s))
			cam_pos = (back_from.pos as Vector3).lerp(ch[0], k); cam_look = (back_from.look as Vector3).lerp(ch[1], k)
		else:
			cam_pos = ch[0]; cam_look = ch[1]; _maybe_snap()
		return
	rig = "BCL" if c.dir == "L" else "BCR"
	var u: float = qte_t / float(disp.playback_s) if core.phase == "TIMING" else 1.0
	var tgt := Vector3(pp.x, 0.8, pp.z)
	if cc == null or u < float(cc.start_t):  # §12.2 transition_to_corner: chase + side offset, 1.0 s ease
		var o: Array = CC.transition_to_corner_offset
		var side := -1.0 if c.dir == "L" else 1.0
		var k := Track.smooth(qte_t / float(CC.transition_s))
		var right := Vector3(-pp.tz, 0, pp.tx); var fwd := Vector3(pp.tx, 0, pp.tz)
		cam_pos = ch[0] + right * (side * float(o[0]) * k) + Vector3.UP * (float(o[1]) * k) - fwd * (float(o[2]) * k)
		cam_look = (ch[1] as Vector3).lerp(tgt, k)
	else:
		if not cam_curve_built:  # authored path (PLACEHOLDER keyframes); continuous from the current pose unless the turn type is a cut
			var pts: Array = path.corner_cam_points(c.dir, cc)
			if not bool(cc.cut): pts.push_front(cam_pos)
			cam_path.curve = _catmull_curve(pts); cam_curve_built = true
		cam_follow.progress_ratio = Track.smooth((u - float(cc.start_t)) / (1.0 - float(cc.start_t)))
		cam_pos = cam_follow.position
		cam_look = tgt

## Curve3D through pts with Catmull-Rom tangents as Bezier handles (centripetal-free uniform form, like THREE 'catmullrom' 0.5)
func _catmull_curve(pts: Array) -> Curve3D:
	var cv := Curve3D.new(); cv.bake_interval = 0.1
	var n := pts.size()
	for i in n:
		var p0: Vector3 = pts[maxi(i - 1, 0)]; var p2: Vector3 = pts[mini(i + 1, n - 1)]
		var tan := (p2 - p0) * 0.5 / 3.0
		cv.add_point(pts[i], -tan if i > 0 else Vector3.ZERO, tan if i < n - 1 else Vector3.ZERO)
	return cv

func _update_scene() -> void:
	var st := _in_straight()
	straight_d.group.visible = st; corner_d.group.visible = not st
	for m in scroll_mats:
		if m.has_meta("scrolls"): m.set_shader_parameter("scroll_m", scroller.scroll_m())
	_stream_district(straight_d if st else corner_d, scroller.scroll_m())
	var at_stop: bool = core.phase == "SELECT" and mode == "RACE" and _sel_stop() > 0
	for it in corner_d.items:   # keep props out of the stop lens (build_lsc.py:254 drops cedars within 5.5 m of a camera)
		var o: Node3D = it.obj
		o.visible = not (at_stop and Vector2(o.position.x - cam_pos.x, o.position.z - cam_pos.z).length() < 5.5)
	var pth = straight_path if st else path
	var pp := _place(player_car, pth, s_player, 0.0)
	_place(rival_car, pth, s_player + rival_offset, rival_lane_d)
	_update_camera(pp)
	cam.position = cam_pos
	cam.look_at(cam_look)
	cam.fov = cam_fov; glow_cam.fov = cam_fov
	glow_cam.global_transform = cam.global_transform
	var cars_on: bool = not (core.phase == "SELECT" and mode == "RACE" and _sel_stop() > 0 and bool(SC.hide_cars_at_stops))
	player_car.visible = cars_on; rival_car.visible = cars_on
	post_mat.set_shader_parameter("mirror_on", 1.0 if _mirror_on() else 0.0)
	sky_root.position = cam_pos  # painted sky follows the camera
	var t := Vector3(pp.tx, 0, pp.tz); var p := Vector3(pp.x, 0, pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)  # build_lsc.py:246
	mirror_cam.look_at(p - t * float(disp.mirror.look_back) + Vector3(0, float(disp.mirror.look_y), 0))

## rear-view mirror only on the chase camera (B.5b frames 1 and 4); none during corner playback (B.5a frames) or at the Apex/Exit stops
func _mirror_on() -> bool:
	if mode == "MENU": return false   # the menu logo sits where the mirror goes
	if core.phase == "SELECT": return _sel_stop() == 0 and not (stop_from != null and stop_t < float(SC.move_s))
	if core.phase == "TIMING": return lock_hold_t < float(SC.lock_hold_s)
	return core.phase == "FINISHED" and back_t >= float(CC.transition_to_straight_s)

func _render_hud() -> void:
	if mode == "MENU":
		menu.blink = int(floor(clock * 2.0)) % 2 == 0
		hud.show_state({"menu": menu}); return
	var c: Dictionary = core.corner()
	var r = core.result if core.phase == "RESULT" else (core.history[-1] if core.history.size() > 0 else {})
	var slots := []
	for i in 3: slots.append(core.hand[core.picks[i]] if i < core.picks.size() else null)
	var left: float = maxf(0.0, RaceCore.STRAIGHT_DURATION - phase_t)
	var turn_m: float = left * scroller.speed_ms()   # display: distance to turn-in at the current scroll speed
	var plan := {"phase": core.picks.size(), "sel": plan_sel, "avail": _plan_avail(), "avail_entry": _plan_avail(true),
		"entry": core.hand[core.picks[0]] if core.picks.size() > 0 else ""}
	var lanes = null
	if core.phase == "SELECT" and mode == "RACE":   # player lane chevrons over the road ahead (post_v5.py:66); never a rival-lane marker (B.4)
		lanes = {}
		var ahead: float = s_player + clampf(turn_m, 14.0, 40.0)
		var ln := {"A": "outside", "S": "center", "D": "inside"}
		for k in ln:
			var wp := _pp(straight_path, ahead, Track.lane_offset(ln[k], c.dir, disp.lane_width_m), 0.05)
			lanes[k] = null if cam.is_position_behind(wp) else cam.unproject_position(wp)
	var pline: String = core.player_line() if core.phase == "TIMING" else (String((r as Dictionary).get("player_line", "")) if core.phase != "SELECT" else "")
	var play_phase: int = mini(2, int(floor(3.0 * qte_t / float(disp.playback_s))))
	# B.5a: both full lines face up from the start of playback; RESULT per phase from the sim's own resolve_stance (pure, no RNG)
	var rline: String = core.line if core.phase == "TIMING" else (String((r as Dictionary).get("line", "")) if core.phase != "SELECT" else "")
	var outs := []
	if pline.length() == 3 and rline.length() == 3:
		for i in 3: outs.append(Combat.resolve_stance(pline[i], rline[i]))
	var plate := {"name": _corner_name(c), "icon": _plate_icon(), "mode": "VIEW", "stop": _sel_stop(), "done": core.picks.size()}
	if core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s): plate.mode = "LOCK"
	elif core.phase == "TIMING": plate.mode = "PLAY"; plate.stop = play_phase
	elif core.phase != "SELECT": plate.mode = "DONE"
	hud.show_state({"phase": core.phase, "title": "CORNER %d/%d %s %s (%s)" % [core.corner_index + 1, cfg.corners.size(), String(c.district).to_upper(), c.corner, c.dir],
		"sub": "seed %d %s %s %dm/s" % [core.seed_value, C.PIN_COMMIT.substr(0, 7), rig, roundi(scroller.speed_ms())], "lead": core.lead(), "gap": core.gap(),
		"left": left, "total": RaceCore.STRAIGHT_DURATION, "slots": slots, "hand": core.hand, "used": core.picks,
		"needle": qte_stopped if qte_stopped != null else sin(TAU * qte_t / float(disp.qte.period_s)), "line": pline, "rline": rline, "outs": outs, "plate": plate, "locked_hold": core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s), "mirror": _mirror_on(), "play_phase": play_phase, "plan": plan, "turn_m": turn_m, "dir": c.dir, "lanes": lanes,
		"result": r, "reveal": reveal, "leader_changed": leader_changed, "winner": core.winner() if core.phase == "FINISHED" else "", "cum_p": core.cum_p, "cum_o": core.cum_o,
		"last_corner": core.corner_index + 1 >= cfg.corners.size(), "fin": fin if core.phase == "FINISHED" else null})
