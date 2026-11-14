# ARTHUR CEL A PORT (unapproved experiment): copy of Gordon's two-corner main.gd. Every change is marked `# CEL:`.
## Two-corner test, Godot presentation. Logic lives in race_core.gd. Scene refactor (2026-11-12): the nodes live in scenes
## (main.tscn composes track.tscn, touge_dressing.tscn, sky.tscn, car.tscn x2, camera_rig.tscn, hud.tscn; see the README
## 'Editor workflow'); this script wires them up and runs the game flow, cameras and passes exactly as before.
## User args (after --): --script-inputs <file> --shots <dir> --seed N --no-menu --line-preview-shots <dir>   (single look: 640x480, RGB555 + Bayer; no CRT/low-res)
## Main menu (Austin 2026-11-10) unless --script-inputs or --no-menu; --seed N prefills the seed field. headless_run.gd never shows it.
extends Control

const RaceCore = preload("res://scripts/race_core.gd")
const Track = preload("res://scripts/track.gd")
const C = preload("res://scripts/sim_constants.gd")
const Combat = preload("res://scripts/combat.gd")  # display uses the pure resolve_stance only (no RNG)
const POST_SH = preload("res://shaders/post.gdshader")
const RoadScroller = preload("res://scripts/road_scroller.gd")
const GLOW_SH = preload("res://shaders/glow.gdshader")
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Dressing = preload("res://scripts/touge_dressing.gd")
const LineChevrons = preload("res://scripts/line_chevrons.gd")
const TAG := "640"

var cfg: Dictionary
var disp: Dictionary
var script_in = null
var shots_dir := ""
var shot_dual := false  # also write 640 (3D+post) and 1280 (final composite) siblings
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
var hud_vp: SubViewport
var hud_rect: TextureRect
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
var reveal := 0
var busy := false
var script_qte: Array = []    # scripted runs: the exact phase scores to submit (parity); presses are placed to show them
var fog_color := Color(0.043, 0.051, 0.102)
# ── scrolling straight / corner camera (display only) ──
var RS: Dictionary
var CC: Dictionary
var scroller
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
const PLAN_ORDER := ["P", "H", "E"]   # rows: POW / HAN / EN; on-screen lanes OUT / MID / IN
var plan_sel := 0
# ── B.5b camera stops (display only): stop 0 = Entry (chase, rival visible), 1 = Apex, 2 = Exit (corner geometry, no cars) ──
var SC: Dictionary
var last_stop := 0
var stop_t := 99.0
var stop_from = null
var lock_hold_t := 99.0
var lock_from = null
# ── shots9 (Austin playtest 2026-11-11 ~10 PM PT), display only ──
var PB: Dictionary            # display.json "playback_flow" (PLACEHOLDERS)
var course                    # one continuous Touge road: straight, corner 1, straight, corner 2, straight
var views: Array = []         # per-corner local view of the course (local 0 = 45 m before turn-in)
var straights: Array = []     # per-corner infinite-scroll straight, anchored where that corner's approach starts
var lat_p := 0.0; var lat_r := 0.0; var err_p := 0.0; var err_r := 0.0; var tgt_p = null; var tgt_r = null
var off0 := 0.0; var off1 := 0.0; var off1_score = null; var pass_plan := {}
var pass_t := 0.0             # seconds since the Exit QTE finished; the pass eases over PB.pass_after_exit_s
var cont_t := 0.0             # after-turn pause (RESULT), auto-continues at PB.continue_s
var cont_pending := false     # Enter / auto-continue waited until the pass lerp finished
# ── shots10: three timing QTEs per turn (Entry / Apex / Exit camera stops), sim pin f0efecf (Austin approved 10:56 PM PT) ──
var QS: Dictionary            # display.json "qte_sweep" (PLACEHOLDERS)
# shots11 (Austin 2026-11-12): the three QTEs play DURING playback. The car drives the corner, holds at the Entry / Apex / Exit
# point while that phase's QTE timer runs (the road keeps scrolling), then drives on. Apex / Exit selection stops are static.
var qte_i := 0                # next / current phase QTE during playback: 0..2, 3 = all three done
var qte_seg := ""             # "" (driving) | "sweep" (cursor running) | "show" (score up until the phase timer ends)
var qte_show_t := 0.0         # qte_seg_t when the score went up
var pb_started := false       # playback has started for this corner (off0 captured)
var scroll_shown := 0.0       # road scroll drawn this frame: frozen at the Apex / Exit selection stops (static), else the scroller's
var qte_seg_t := 0.0
var qte_res: Array = [null, null, null]       # phase scores: float in [0, 1], or null = unplayed (0)
var qte_press_ms: Array = [null, null, null]  # where the cursor stopped (display)
var qte_from = null           # camera pose at the start of a move
var zone_ms := 800.0          # qte_zone_width(r, mod) x QTE_ZONE_BASE_MS for this race (core.zone_ms())
var min_sep_overlap := 99.0   # smallest lateral gap seen while the cars overlap longitudinally (no-clip check)
var gif_dir := ""; var gif_dt := 0.1; var gif_next := 0.0; var gif_n := 0
var chevrons: Node3D  # B.5d road chevrons (SELECT only, purely visual)
# CEL: Cel A port. Toggle = project setting cel/enabled, overridden by user arg --cel 0|1, live key F7.
const CEL_BIT_N := 1 << 18   # layer 19: view-normal pass (CEL_GB = 1)
const CEL_BIT_D := 1 << 19   # layer 20: linear-depth pass (CEL_GB = 2)
const CEL_BIT_DECAL := 1 << 17   # layer 18: car decals (blob shadow, headlight throw); seen by the colour cameras, not the G-buffer
var cel_enabled := true
var cel_vps: Array = []      # [main normal, main depth, mirror normal, mirror depth]
var cel_cams: Array = []
var perf_on := false; var perf_dts: PackedFloat64Array = PackedFloat64Array(); var perf_last := 0; var perf_skip := 0

func _arg(k: String, def = null):
	var a := OS.get_cmdline_user_args()
	var i := a.find(k)
	return a[i + 1] if i >= 0 and i + 1 < a.size() else def

func _json(p: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(p))

## Window scale (shots7/8/9). The game is laid out in 640x480 design units under a x2 node scale on a 1280x960 project base,
## and the HUD is a 1280x960 layer (2x pixel grid, Austin 2026-11-11 22:21). When the window fits 1280x960 or more the
## frame scales by a whole number of that base (1x at 1920x1080 and 2560x1440, 2x at 2560x1920): the HUD layer goes up
## nearest by a whole number and the 640x480 world by twice that (art_direction.md:115/:141 integer nearest for the world).
## Below 1280x960 the scale is fractional and the HUD layer is shown LINEAR (nearest downscaling would drop rows of 1-bit text).
func _fit_scale() -> void:
	var w := get_window()
	var s := minf(w.size.x / 1280.0, w.size.y / 960.0)
	w.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_INTEGER if s >= 1.0 else Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	if hud_rect != null: hud_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if s >= 1.0 else CanvasItem.TEXTURE_FILTER_LINEAR

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
	menu.seed_text = _arg("--seed", ""); menu.commit = "%s build %s" % [C.PIN_COMMIT.substr(0, 7), String(RaceCore.build_info().build)]
	if not OS.has_feature("web"): menu.items.append("QUIT")  # Quit: Godot desktop only
	DIST = disp.districts; CS = disp.car_shading; PAL = disp.palette; PB = disp.playback_flow; QS = disp.qte_sweep
	gif_dir = _arg("--gif", ""); gif_dt = float(_arg("--gif-dt", "0.1"))
	if gif_dir != "": DirAccess.make_dir_recursive_absolute(gif_dir)
	_build_viewports()
	scale = Vector2(2, 2)   # 640x480 design units on the 1280x960 base
	_fit_scale(); get_window().size_changed.connect(_fit_scale)
	_build_course()
	player_car = _load_car($WorldVP/PlayerCar)   # car.tscn: car_mx5.glb, mx5_env.png, car_shading.mx5
	rival_car = _load_car($WorldVP/RivalCar)     # car.tscn: car_s2000.glb, s2000_env.png, car_shading.s2000
	for c in [player_car, rival_car]:   # CEL: decals (StandardMaterial3D planes) stay out of the G-buffer, so they never get inked
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is StandardMaterial3D: (ch as MeshInstance3D).layers = CEL_BIT_DECAL
	chevrons = LineChevrons.new()
	chevrons.cfg = disp.get("line_preview", {})
	$WorldVP.add_child(chevrons)
	core = RaceCore.new()
	core.setup(cfg, seed_v)
	_setup_corner()
	if script_in != null:
		_run_script()
	elif OS.get_cmdline_user_args().has("--plan-key-test"):
		_plan_key_test()
	elif _arg("--line-preview-shots") != null:
		shots_dir = _arg("--line-preview-shots")
		DirAccess.make_dir_recursive_absolute(shots_dir)
		await _run_line_preview_shots()

## Plan the Line key test: random Up/Down/Left/Right/Enter/Backspace over many seeds; every pick must be an unused hand index of the
## highlighted stance, the cursor never rests on a 'none drawn' stance, and the 3rd Enter locks exactly the chosen stances.
func _plan_key_test() -> void:
	var keys := [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER, KEY_BACKSPACE]
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	var n_lock := 0; var n_unplayed := 0
	var kt_inputs := []; var kt_out := []
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
			# the three QTEs through the real input path: SPACE at a random point of each sweep, or no press (unplayed)
			lock_hold_t = float(SC.lock_hold_s)
			var want_ms := []
			for i in 3: want_ms.append(-1.0 if rng.randf() < 0.25 else rng.randf_range(0.0, float(QS.lead_ms) + zone_ms))
			var guard := 0   # playback with the QTE holds, stepped at 60 Hz through the same code as _process
			while core.phase == "TIMING" and guard < 4000:
				guard += 1
				if qte_i <= 2 and qte_seg == "sweep" and float(want_ms[qte_i]) >= 0.0 and _qte_ms() >= float(want_ms[qte_i]): handle_key(KEY_SPACE)
				_step_play(1.0 / 60.0)
				_ease_gap(1.0 / 60.0)
				if qte_i < 3 and (rival_offset != off0 or (off0 != 0.0 and rival_offset != 0.0 and signf(rival_offset) != signf(off0))):
					push_error("seed %d: order/gap changed before Exit QTE (qte_i=%d off0=%s off=%s)" % [sd, qte_i, str(off0), str(rival_offset)]); get_tree().quit(1); return
			if core.phase == "TIMING" or qte_i != 3: push_error("seed %d: playback never ended" % sd); get_tree().quit(1); return
			# finish the pass into RESULT and confirm the drawn gap equals the resolved lead (no snap)
			var want_off: float = Track.rival_draw_offset(core.lead(), disp.visual_gap)
			if absf(off1 - want_off) > 0.001:
				push_error("seed %d: preview off1 %s != resolved %s" % [sd, str(off1), str(want_off)]); get_tree().quit(1); return
			while pass_t < float(PB.pass_after_exit_s) and guard < 8000:
				guard += 1; _ease_gap(1.0 / 60.0)
			if absf(rival_offset - want_off) > 0.001:
				push_error("seed %d: RESULT gap %s != resolved %s (snap?)" % [sd, str(rival_offset), str(want_off)]); get_tree().quit(1); return
			for i in 3:
				var z := _qte_zone()
				var ok: bool = qte_res[i] == null if float(want_ms[i]) < 0.0 else (qte_res[i] != null and float(qte_res[i]) == Combat.round_qte_score(Combat.hit_quality(float(qte_press_ms[i]) - (z.x + z.y) / 2.0, zone_ms)) and float(qte_res[i]) >= 0.0 and float(qte_res[i]) <= 1.0)
				if not ok: push_error("seed %d: QTE %d press %s -> %s" % [sd, i, str(want_ms[i]), str(qte_res[i])]); get_tree().quit(1); return
				if qte_res[i] == null: n_unplayed += 1
			var q := []   # (_step_play submitted qte_res at the end of playback)
			for v in qte_res: q.append(null if v == null else RaceCore.fhex(float(v)))
			kt_inputs.append({"seed": sd, "corners": [{"pick": core.picks.duplicate(), "qte": q}]})
			kt_out.append({"seed": sd, "corners": core.history.duplicate(true), "player_total": core.cum_p, "opponent_total": core.cum_o, "winner": core.winner()})
			if str(shown) != str(core.result.outcomes): push_error("seed %d: panel %s != sim %s" % [sd, str(shown), str(core.result.outcomes)]); get_tree().quit(1); return
	var od := ProjectSettings.globalize_path("res://").path_join("../out")
	FileAccess.open(od.path_join("key_test_inputs.json"), FileAccess.WRITE).store_string(JSON.stringify({"races": kt_inputs}))
	FileAccess.open(od.path_join("key_test_godot.json"), FileAccess.WRITE).store_string(JSON.stringify({"races": kt_out}, " ", false, true))
	print("PLAN KEY TEST PASS: 200 seeds, %d locked by keys; camera stop == picks every step; 3 QTEs by SPACE per locked turn (%d unplayed) score = hit_quality(press); B.5a panel results == sim outcomes (sim compare: out/key_test_*.json)" % [n_lock, n_unplayed])
	get_tree().quit(0)

# ── viewports, post, HUD ──
func _build_viewports() -> void:
	art = ArtKit.new(disp)
	world_vp = $WorldVP
	world_vp.world_3d = World3D.new()  # shared with the mirror viewport (own_world_3d would ignore it)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = fog_color
	world_vp.world_3d.environment = env
	world_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	world_vp.msaa_3d = Viewport.MSAA_DISABLED
	world_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	cam_rig = $WorldVP/CameraRig
	cam = cam_rig.cam; cam.fov = disp.camera.fov; cam.near = 0.1; cam.far = 400.0
	cam.current = true
	mirror_vp = $MirrorVP
	mirror_vp.world_3d = world_vp.world_3d
	mirror_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	mirror_cam = $MirrorVP/MirrorCam; mirror_cam.fov = disp.mirror.fov; mirror_cam.near = float(disp.mirror.near); mirror_cam.far = 300.0
	mirror_cam.current = true
	env_mat = art.env_mat
	cam_path = cam_rig.path  # authored corner camera path (§13.3)
	cam_follow = cam_rig.follow; cam_follow.loop = false; cam_follow.rotation_mode = PathFollow3D.ROTATION_NONE
	post_mat = ShaderMaterial.new(); post_mat.shader = POST_SH
	post_mat.set_shader_parameter("mirror_rect", Vector4(disp.mirror.x, disp.mirror.y, disp.mirror.w, disp.mirror.h))
	post_rect = $Post; post_rect.size = Vector2(640, 480); post_rect.stretch_mode = TextureRect.STRETCH_SCALE
	post_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	post_rect.texture = world_vp.get_texture(); post_rect.material = post_mat
	# HUD on a 2x pixel grid (Austin 2026-11-11 22:21): drawn into a 1280x960 SubViewport at scale 2, shown nearest over the world
	hud_vp = $HudVP; hud_vp.size = Vector2i(1280, 960); hud_vp.transparent_bg = true; hud_vp.disable_3d = true
	hud_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	hud_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	hud_rect = $HudRect; hud_rect.size = Vector2(640, 480); hud_rect.stretch_mode = TextureRect.STRETCH_SCALE
	hud_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; hud_rect.texture = hud_vp.get_texture(); hud_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	hud = $HudVP/Hud; hud.scale = Vector2(2, 2)
	hud.setup(load("res://art/font_6x9.png"), _json("res://art/font.json"), load("res://art/panel9.png"), load("res://art/logo_v3.png"))
	var IW: int = int(disp.render.internal_w); var IH: int = int(disp.render.internal_h)
	world_vp.size = Vector2i(IW, IH)
	mirror_vp.size = Vector2i(int(disp.mirror.w), int(disp.mirror.h))
	post_mat.set_shader_parameter("res", Vector2(IW, IH))
	post_mat.set_shader_parameter("scene_tex", world_vp.get_texture())
	post_mat.set_shader_parameter("mirror_tex", mirror_vp.get_texture())
	glow_vp = $GlowVP; glow_vp.world_3d = world_vp.world_3d; glow_vp.size = Vector2i(IW, IH)
	glow_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS; glow_vp.msaa_3d = Viewport.MSAA_DISABLED
	glow_cam = $GlowVP/GlowCam; glow_cam.fov = disp.camera.fov; glow_cam.near = 0.1; glow_cam.far = 400.0; glow_cam.cull_mask = 2
	var genv := Environment.new(); genv.background_mode = Environment.BG_COLOR; genv.background_color = Color.BLACK; glow_cam.environment = genv
	glow_cam.current = true
	post_mat.set_shader_parameter("glow_tex", glow_vp.get_texture())
	post_mat.set_shader_parameter("bloom_k", float(PAL.bloom[0])); post_mat.set_shader_parameter("sat", float(PAL.sat))
	_build_sky()
	_build_cel()   # CEL:

# ── cars (car.tscn instances PlayerCar / RivalCar) ──
## game-ready .glb from assets/cars; A.4/A.8 faked shine with per-car values (README); lamp glow, blob shadow, headlight throw
func _load_car(car: Node3D) -> Node3D:
	car.setup(art, CS)
	car_mats.append_array(car.mats)
	return car

# ── art: stand-in textures from spec/gen_art.py (art_direction Part B recipes, RGB555 + Bayer, lossless import) ──
var DIST: Dictionary
var CS: Dictionary
var art                      # art_kit.gd: shared builders + material lists (scroll / glow / card)
var cam_rig                  # camera_rig.tscn
var straight_d = null        # {road, group, items, a0, range, pth}: road from track.tscn, props from touge_dressing.tscn
var corner_d = null
var sky_root: Node3D
var sky_mat: ShaderMaterial
var band_mat: ShaderMaterial

func _tex(n: String) -> Texture2D: return art.tex(n)

func _stream_district(dd: Dictionary, scroll_m: float) -> void: Dressing.stream(dd, scroll_m)

## sky.tscn (B.1): the painted cylinder follows the camera
func _build_sky() -> void:
	sky_root = $WorldVP/Sky
	sky_mat = sky_root.build()
	band_mat = sky_mat  # skyline/ridge band composited in sky.gdshader (r 240, y -3..22, rep 5, as Three.js)

func _apply_district(dk: String) -> void:
	var D: Dictionary = DIST[dk]; var fc := Color(D.fog)
	art.apply_fog(dk, car_mats)
	world_vp.world_3d.environment.background_color = fc
	sky_mat.set_shader_parameter("tex", _tex(dk + "_sky"))
	band_mat.set_shader_parameter("band_tex", _tex("street_skyline" if dk == "street" else "touge_ridge"))
	# CEL: ink fades into this district's fog
	post_mat.set_shader_parameter("fog_color", Vector3(fc.r, fc.g, fc.b))
	var fn = D.get("fog_near", D.get("fog_near_m", 9.0)); var ff = D.get("fog_far", D.get("fog_far_m", 78.0))
	post_mat.set_shader_parameter("fog_near", float(fn)); post_mat.set_shader_parameter("fog_far", float(ff))
	# CEL: road strips flatten wider (Cel A: 6 texels) and posterise in 9 sqrt-luma steps instead of 10. The touge asphalt
	# sits at luma 0.092 / 0.124 and 0.124 is exactly a 10-step boundary, which broke it into speckles that crawled as the road scrolled.
	for m in art.scroll_mats:
		var t = (m as ShaderMaterial).get_shader_parameter("tex")
		if t == _tex("touge_road") or t == _tex("street_road"):
			m.set_shader_parameter("flat_radius", 6.0); m.set_shader_parameter("poster", 9.0)

## StraightRoad + CornerRoad (§13.1), dressed for the upcoming corner's district: road strips in track.tscn, props in touge_dressing.tscn
func _build_road(dk: String) -> void:
	var track = $WorldVP/Track; var dressing = $WorldVP/Dressing
	track.clear(); dressing.clear()
	art.reset_for_rebuild()
	var sr = track.build_strip(art, straight_path, RS.straight_from_m, RS.straight_to_m, dk, "StraightRoad")
	straight_d = dressing.build(art, straight_path, RS.straight_from_m, RS.straight_to_m, dk, "StraightDressing"); straight_d.road = sr
	var cr = track.build_strip(art, course, -60.0, course.length + 60.0, dk, "CourseRoad")   # the whole continuous course (both corners)
	corner_d = dressing.build(art, course, -60.0, course.length + 60.0, dk, "CourseDressing"); corner_d.road = cr
	for c in [player_car, rival_car]:  # car head/tail glow sprites keep their fog uniforms in step
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is ShaderMaterial and ((ch as MeshInstance3D).material_override as ShaderMaterial).shader == GLOW_SH:
				art.glow_mats.append((ch as MeshInstance3D).material_override)
	_apply_district(dk)

func _pp(pth, s: float, d: float, y: float = 0.0) -> Vector3: return ArtKit.pp(pth, s, d, y)

# ── game flow ──
func _setup_corner() -> void:
	var c: Dictionary = core.corner()
	path = views[core.corner_index]; straight_path = straights[core.corner_index]
	_build_road(c.district)
	s_player = 8.0; phase_t = 0.0; qte_t = 0.0; reveal = 0; cam_curve_built = false; leader_changed = false
	cont_t = 0.0; pass_plan = {}; off1_score = null; pass_t = 0.0; cont_pending = false
	qte_i = 0; qte_seg = ""; qte_seg_t = 0.0; qte_show_t = 0.0; pb_started = false; qte_res = [null, null, null]; qte_press_ms = [null, null, null]; qte_from = null
	zone_ms = core.zone_ms()
	plan_sel = 0; _plan_fix_sel(0)
	last_stop = 0; stop_t = 99.0; stop_from = null; lock_hold_t = 99.0; lock_from = null
	rival_lane_d = Track.lane_offset_for_stance(core.entry_tell().stance, c.dir, disp.lane_width_m)
	rival_offset_target = Track.rival_draw_offset(core.lead(), disp.visual_gap)
	scroller.transition_to_straight()
	if first_corner:
		rival_offset = rival_offset_target; back_t = 99.0
		tgt_p = null; tgt_r = null; err_p = 0.0; err_r = 0.0
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
		elif k == KEY_UP: _plan_fix_sel(-1)
		elif k == KEY_DOWN: _plan_fix_sel(1)
		elif (k == KEY_LEFT or k == KEY_RIGHT) and core.picks.size() == 0: _plan_lane_step(-1 if k == KEY_LEFT else 1)
		elif k == KEY_BACKSPACE: core.unpick(); _plan_fix_sel(0)
		elif k == KEY_ENTER or k == KEY_KP_ENTER:
			if core.picks.size() >= 3: _do_lock()
			else:
				var idx := _plan_hand_index(PLAN_ORDER[plan_sel])
				if idx >= 0:
					core.pick(idx)
					if core.picks.size() >= 3: _do_lock()   # Enter on EXIT locks the line
					else: _plan_fix_sel(0)
	elif core.phase == "TIMING" and k == KEY_SPACE and qte_i <= 2 and qte_seg == "sweep" and script_in == null:
		_qte_press()
	elif core.phase == "RESULT" and (k == KEY_ENTER or k == KEY_KP_ENTER) and reveal >= 3:
		_continue()

## after-turn pause ends (Enter, or the countdown runs out): next corner, or the finish
func _continue() -> void:
	if pb_started and pass_t < float(PB.pass_after_exit_s):
		cont_pending = true; return
	cont_pending = false
	core.next()
	if core.phase != "FINISHED": _setup_corner()
	else: _return_to_chase()

## Entry lane with Left / Right (Austin 2026-11-11: "left and right don't scroll left and right when selecting an entry lane").
## Moves to the next drawn lane in that on-screen direction: a left corner has IN on the left, a right corner has OUT on the left.
## No wrap; lanes with none drawn are skipped.
func _screen_lanes() -> Array: return ["E", "H", "P"] if String(core.corner().dir) == "L" else ["P", "H", "E"]
func _plan_lane_step(dir: int) -> void:
	var order := _screen_lanes(); var a := _plan_avail()
	var j: int = order.find(PLAN_ORDER[plan_sel]) + dir
	while j >= 0 and j < 3:
		if int(a[order[j]]) > 0: plan_sel = PLAN_ORDER.find(order[j]); return
		j += dir

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
	var a := {"P": 0, "H": 0, "E": 0}
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

## END_TURN: swing back to the chase cam (§12.2 transition_to_straight). The pass is animated after the Exit QTE
## (Austin 2026-11-12: 'Order only changes after exit QTE'), into RESULT if needed, so nothing snaps here.
func _return_to_chase() -> void:
	back_from = {"pos": cam_pos, "look": cam_look}; back_t = 0.0; pending_snap = false

func _in_straight() -> bool: return core.phase == "SELECT" and _sel_stop() == 0  # Apex/Exit stops show the corner geometry (B.5b)

func _place(car: Node3D, pth, s: float, d: float) -> Dictionary:
	var p: Dictionary = pth.point(s, d)
	car.position = Vector3(p.x, 0, p.z)
	car.rotation.y = atan2(p.tx, p.tz)
	(car.get_meta("root") as Node3D).position.y = float(RS.bob_amp_m) * sin(TAU * float(RS.bob_hz) * clock + (1.7 if car == rival_car else 0.0))  # identical bob, no pitch/roll
	for w in car.get_meta("wheels"): (w as Node3D).rotation.x = wheel_angle
	return p

# ── per-phase QTE during playback (display + input; the scores go to core.submit_qte, which resolves the turn with the sim's averaging) ──
## timeline of one sweep in ms: cursor starts at 0, zone = [lead, lead + zone_ms], sweep ends at the zone's far edge
func _qte_zone() -> Vector2: return Vector2(float(QS.lead_ms), float(QS.lead_ms) + zone_ms)
func _qte_ms() -> float: return qte_seg_t * 1000.0
## the phase timer (s): the cars hold for the whole QTE bar (lead + zone + tail, display.json qte_sweep PLACEHOLDERS), and at
## least result_hold_s after the score goes up
func _qte_timer_s() -> float: return maxf(float(QS.lead_ms) + float(C.QTE_ZONE_BASE_MS), _qte_zone().y) / 1000.0 + float(QS.tail_ms) / 1000.0
func _qte_press() -> void:
	var ms := _qte_ms(); var z := _qte_zone()
	qte_press_ms[qte_i] = ms
	qte_res[qte_i] = Combat.round_qte_score(Combat.hit_quality(ms - (z.x + z.y) / 2.0, zone_ms))  # rounded phase score (pin c3ffc41); HUD + token use this
	qte_seg = "show"; qte_show_t = qte_seg_t
func _qte_timeout() -> void:
	qte_res[qte_i] = null; qte_press_ms[qte_i] = null   # unplayed = PHASE_QTE_UNPLAYED (0), Austin
	qte_seg = "show"; qte_show_t = qte_seg_t
## scripted runs submit the exact scripted value; the cursor stops where that score sits (early side of the centre)
func _script_press_ms(v) -> float:
	var z := _qte_zone(); return (z.x + z.y) / 2.0 - (1.0 - float(v)) * zone_ms / 2.0
func _step_qte(dt: float) -> void:
	qte_seg_t += dt
	if qte_seg == "sweep":
		var ms := _qte_ms()
		if script_in != null and script_qte.size() == 3 and script_qte[qte_i] != null and ms >= _script_press_ms(script_qte[qte_i]):
			qte_press_ms[qte_i] = ms; qte_res[qte_i] = Combat.phase_raw_qte(script_qte[qte_i]); qte_seg = "show"; qte_show_t = qte_seg_t
		elif ms > _qte_zone().y:
			_qte_timeout()
	if qte_seg == "show" and qte_seg_t >= _qte_timer_s() and qte_seg_t - qte_show_t >= float(QS.result_hold_s):
		qte_i += 1; qte_seg = ""; qte_seg_t = 0.0

## playback distance and the three hold points: the corner plate's E / A / X marks (_plate_icon: turn-in - 6 m, mid-arc,
## arc end + 6 m), as playback-clock times
func _travel() -> float: return path.S + path.R * path.A + 10.0 - 8.0
func _hold_t(i: int) -> float:
	var arc: float = path.R * path.A
	var sv: float = [path.S - 6.0, path.S + arc * 0.5, path.S + arc + 6.0][i]
	return float(disp.playback_s) * (sv - 8.0) / _travel()

## one playback step: drive to the next hold point, hold there while that phase's QTE runs (road keeps scrolling), drive on;
## at the end submit the three scores (resolve_turn averages them). Returns the extra speed for the wheels.
func _step_play(dt: float) -> float:
	if not pb_started:
		pb_started = true; qte_t = 0.0; off0 = rival_offset; off1_score = null; pass_plan = {}; pass_t = 0.0
	var dv := 0.0
	if qte_seg != "":
		_step_qte(dt)
	elif qte_i < 3 and qte_t + dt >= _hold_t(qte_i):
		qte_t = _hold_t(qte_i); qte_seg = "sweep"; qte_seg_t = 0.0; qte_show_t = 0.0
	else:
		qte_t += dt; dv = _travel() / float(disp.playback_s)
	s_player = 8.0 + _travel() * minf(1.0, qte_t / float(disp.playback_s))
	_update_pass_target()
	if qte_t >= float(disp.playback_s) and qte_seg == "" and qte_i >= 3:
		var before: float = core.lead()
		core.submit_qte(qte_res.duplicate()); reveal = 0; phase_t = 0.0; result_t = 0.0
		var after: float = core.lead()
		leader_changed = before != 0.0 and after != 0.0 and signf(before) != signf(after)
		rival_offset_target = Track.rival_draw_offset(after, disp.visual_gap)  # = off1 (same resolve_turn); the pass may still be easing into RESULT
		cont_t = 0.0
	return dv

func _do_lock() -> void:
	lock_from = {"pos": cam_pos, "look": cam_look, "fov": cam_fov}; lock_hold_t = 0.0
	core.lock(); phase_t = 0.0; scroller.transition_to_corner()  # §13.2/§14.2 transition_to_corner
	off0 = rival_offset; off1_score = null; pass_plan = {}; pass_t = 0.0
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
	if shot_dual:
		await _save_shot_resolutions(name)
	busy = false


## 640 = post-processed 3D (B.5c native); 1280 = 2× nearest + HUD composite (final judged frame).
func _save_shot_resolutions(name: String) -> void:
	var post_img := await _bake_post_640()
	if post_img != null:
		post_img.save_png(shots_dir.path_join("%s_640.png" % name))
		var hi := Image.new(); hi.copy_from(post_img)
		if hi.get_format() != Image.FORMAT_RGBA8:
			hi.convert(Image.FORMAT_RGBA8)
		hi.resize(1280, 960, Image.INTERPOLATE_NEAREST)
		var hud_img := hud_vp.get_texture().get_image()
		if hud_img.get_format() != Image.FORMAT_RGBA8:
			hud_img.convert(Image.FORMAT_RGBA8)
		hi.blend_rect(hud_img, Rect2i(0, 0, 1280, 960), Vector2i.ZERO)
		hi.convert(Image.FORMAT_RGB8)
		hi.save_png(shots_dir.path_join("%s_1280.png" % name))

func _bake_post_640() -> Image:
	# Re-use the on-screen Post TextureRect's material on a 640 bake viewport.
	var bake := SubViewport.new()
	bake.size = Vector2i(640, 480)
	bake.transparent_bg = false
	bake.disable_3d = true
	bake.render_target_update_mode = SubViewport.UPDATE_ONCE
	bake.msaa_2d = Viewport.MSAA_DISABLED
	bake.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(bake)
	var cr := TextureRect.new()
	cr.size = Vector2(640, 480)
	cr.stretch_mode = TextureRect.STRETCH_SCALE
	cr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cr.texture = world_vp.get_texture()
	cr.material = post_mat
	bake.add_child(cr)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := bake.get_texture().get_image()
	bake.queue_free()
	return img

## B.5d line preview during SELECT only. Entry stays in the chosen lane; Apex/Exit use Arthur's PLACEHOLDER bend map.
func _update_line_preview() -> void:
	if chevrons == null:
		return
	if mode != "RACE" or core.phase != "SELECT":
		chevrons.clear()
		return
	var lpv: Dictionary = disp.get("line_preview", {})
	chevrons.cfg = lpv
	var c: Dictionary = core.corner()
	var dir := String(c.dir)
	var w := float(disp.lane_width_m)
	var entry: String = core.hand[core.picks[0]] if core.picks.size() > 0 else PLAN_ORDER[plan_sel]
	var hover: int = core.picks.size()  # 0 Entry, 1 Apex, 2 Exit
	var follow_ap: String = String(lpv.get("follow_on_apex", "E"))
	var follow_ex: String = String(lpv.get("follow_on_exit", "P"))
	var ap: String = core.hand[core.picks[1]] if core.picks.size() > 1 else (PLAN_ORDER[plan_sel] if hover == 1 else follow_ap)
	var ex: String = core.hand[core.picks[2]] if core.picks.size() > 2 else (PLAN_ORDER[plan_sel] if hover == 2 else follow_ex)
	var apex_pending: bool = core.picks.size() < 2 and hover < 1
	var exit_pending: bool = core.picks.size() < 3 and hover < 2
	var d0 := _lane_d(entry)           # Entry segment stays in the chosen Entry lane
	var d1 := d0
	var d2 := _bend_d(ap, dir, w)
	var d3 := _bend_d(ex, dir, w)
	var s_e0 := s_player + 3.0
	var s_e1 := float(path.S)
	var s_a1 := float(path.S) + float(path.R) * float(path.A)
	var s_x1 := s_a1 + minf(float(path.E), 24.0)
	var segs: Array = []
	segs.append({"s0": s_e0, "s1": s_e1, "d0": d0, "d1": d1, "stance": entry, "hovered": hover == 0, "pending": false})
	segs.append({"s0": s_e1, "s1": s_a1, "d0": d1, "d1": d2, "stance": ap, "hovered": hover == 1, "pending": apex_pending})
	segs.append({"s0": s_a1, "s1": s_x1, "d0": d2, "d1": d3, "stance": ex, "hovered": hover == 2, "pending": exit_pending})
	var D: Dictionary = DIST[String(c.district)]
	chevrons.build(path, segs, Color(D.fog), float(D.fog_near), float(D.fog_far))

## PLACEHOLDER bend (display.json line_preview.bend, Arthur pass 4): multiple of lane width, inside-positive.
func _bend_d(stance: String, dir: String, w: float) -> float:
	var lpv: Dictionary = disp.get("line_preview", {})
	var b: Dictionary = lpv.get("bend", {"P": -1.0, "H": 0.0, "E": 1.0})
	return float(b.get(stance, 0.0)) * Track.inside_sign(dir) * w

func _run_line_preview_shots() -> void:
	shot_dual = true
	mode = "RACE"
	# 20261114 opening hand is P/H/E x2 (20261113 has only one EN, so Exit EN hover would be skipped).
	# First corner is still the left Touge hairpin.
	start_race(20261114)
	await _wait_game(func(): return core.phase == "SELECT" and clock > 0.4)
	var names := {"P": "pow", "H": "han", "E": "en"}
	for k in PLAN_ORDER:
		plan_sel = PLAN_ORDER.find(k)
		_plan_fix_sel(0)
		# if none drawn of k, skip
		if PLAN_ORDER[plan_sel] != k:
			continue
		await get_tree().process_frame
		await _shot("entry_%s" % names[k])
	# Lock Entry OUT/POW (P), then hover each Apex, then lock Apex EN, then hover each Exit.
	plan_sel = PLAN_ORDER.find("P")
	if _plan_hand_index("P") >= 0:
		handle_key(KEY_ENTER)
		await get_tree().process_frame
		await get_tree().process_frame
		await _wait_game(func(): return _sel_stop() == 1 and stop_t >= float(SC.move_s) + 0.25)
		for k in PLAN_ORDER:
			plan_sel = PLAN_ORDER.find(k)
			_plan_fix_sel(0)
			if PLAN_ORDER[plan_sel] != k:
				continue
			await get_tree().process_frame
			await _shot("apex_%s" % names[k])
		plan_sel = PLAN_ORDER.find("E")
		if _plan_hand_index("E") < 0:
			# any remaining EN-less: pick whatever is selected
			pass
		else:
			plan_sel = PLAN_ORDER.find("E")
		handle_key(KEY_ENTER)
		await get_tree().process_frame
		await get_tree().process_frame
		await _wait_game(func(): return _sel_stop() == 2 and stop_t >= float(SC.move_s) + 0.25)
		for k in PLAN_ORDER:
			plan_sel = PLAN_ORDER.find(k)
			_plan_fix_sel(0)
			if PLAN_ORDER[plan_sel] != k:
				continue
			await get_tree().process_frame
			await _shot("exit_%s" % names[k])
		# Lock Exit POW (canonical follow-on), then capture the Exit QTE and the RESULT panel.
		plan_sel = PLAN_ORDER.find("P")
		if _plan_hand_index("P") < 0:
			_plan_fix_sel(0)
		else:
			plan_sel = PLAN_ORDER.find("P")
		handle_key(KEY_ENTER)
		await _wait_game(func(): return core.phase == "TIMING" and qte_i == 2 and qte_seg == "sweep" and _qte_ms() >= 40.0)
		await get_tree().process_frame
		await _shot("exit_qte")
		await _wait_game(func(): return core.phase == "RESULT" and reveal >= 3 and result_t > 0.4)
		await get_tree().process_frame
		await _shot("result")
	print("LINE_PREVIEW_SHOTS_OK ", shots_dir)
	get_tree().quit()

func dump_state() -> String:
	var tok := RaceCore.encode_token(core.dump())
	print("TC3 token ", tok)
	DisplayServer.clipboard_set(tok)
	var f := FileAccess.open("user://last_state.tc1", FileAccess.WRITE); f.store_string(tok)
	return tok

func load_state(tok: String) -> void:
	var d := RaceCore.decode_token(tok)
	if d.is_empty(): return   # outdated TC1/TC2: refused with a message, replay it on its own build
	var n = RaceCore.new(); n.load_state(cfg, d); core = n
	first_corner = true
	_setup_corner()
	if core.phase == "RESULT": reveal = 3

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_F7:   # CEL: live toggle
		set_cel(not cel_enabled); print("CEL ", "ON" if cel_enabled else "OFF"); return
	if script_in != null or not (e is InputEventKey) or not e.pressed or e.echo: return
	var k: int = (e as InputEventKey).keycode
	if mode == "RACE" and k == KEY_F9: dump_state()
	elif mode == "RACE" and k == KEY_F10:
		var t := DisplayServer.clipboard_get()
		if t.begins_with("TC1:") or t.begins_with("TC2:") or t.begins_with("TC3:"): load_state(t)
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
		results.append({"engine": "godot-4.6.3(windowed)", "commit": C.PIN_COMMIT, "seed": core.seed_value, "build": RaceCore.build_info().build, "zone_width": core.zone_width(),
			"corners": core.history, "player_total": core.cum_p, "opponent_total": core.cum_o, "winner": core.winner(), "rng_draws": core.rng.draws,
			"restart": null if ri == 0 else script_in.restart[ri - 1]})
	var out = results[0] if results.size() == 1 else {"races": results}
	print("MIN_SEP_OVERLAP %.3f m (lateral gap while within %.1f m along the road; 99 = never overlapped)" % [min_sep_overlap, float(PB.car_len_m)])
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
		var dm: Dictionary = script_in.get("demo", {})
		if not dm.is_empty() and pk.size() > 0:   # shots9 demo: Left / Right over the Entry lanes, ending on the scripted Entry stance
			var keys: Array = dm.get("arrows%d" % ci, [])
			var want: String = core.hand[int(pk[0])]
			for key in keys:
				var t0 := clock
				await _wait_game(func(): return clock >= t0 + float(dm.get("key_gap_s", 0.6)))
				handle_key(KEY_LEFT if key == "LEFT" else KEY_RIGHT)
			while PLAN_ORDER[plan_sel] != want:
				var t1 := clock
				await _wait_game(func(): return clock >= t1 + float(dm.get("key_gap_s", 0.6)))
				handle_key(KEY_LEFT if _screen_lanes().find(want) < _screen_lanes().find(PLAN_ORDER[plan_sel]) else KEY_RIGHT)
			var t2 := clock
			await _wait_game(func(): return clock >= t2 + 0.8)
		for j in pk.size():
			if not dm.is_empty() and j > 0:   # hold at the Apex / Exit stop so the road scroll shows
				await _wait_game(func(): return stop_t >= float(SC.move_s) + float(dm.get("stop_hold_s", 1.5)))
			if seqs and j > 0:   # B.5b camera stops: Apex / Exit pick shots once the camera has arrived (picks are the scripted hand indices, unchanged)
				_plan_fix_sel(0)
				await _wait_game(func(): return stop_t >= float(SC.move_s) + 0.1)
				await _shot("plan_%s%d" % ["apex" if j == 1 else "exit", ci])
			core.pick(int(pk[j]))
			await get_tree().process_frame; await get_tree().process_frame   # let _process start the camera move (stop_t = 0) before timing on it
			if seqs and j < 2 and j + 1 < pk.size():
				for m in 3:   # camera-move frames between stops
					await _wait_game(func(): return stop_t >= (m + 1) * float(SC.move_s) / 4.0)
					await _shot("seq_move%d_%d_%d" % [ci, j, m])
		await _do_lock()
		if seqs:
			for m in 3:   # camera back to Entry + LINE LOCKED banner (B.5b frame 4)
				await _wait_game(func(): return lock_hold_t >= (m + 1) * float(SC.lock_hold_s) / 3.2)
				await _shot("seq_lock%d_%d" % [ci, m])
		script_qte = []
		for v in inp.qte:
			var s = RaceCore.fdec(v)
			script_qte.append(null if s == null else Combat.round_qte_score(float(s)))
		if seqs: _qte_shots(ci)   # runs alongside the playback frames below (the game clock is frozen during a shot)
		for i in (SEQ_CORNER_N if seqs else 0):
			await _wait_game(func(): return core.phase != "TIMING" or qte_t >= (i + 0.5) / SEQ_CORNER_N * float(disp.playback_s))
			if core.phase != "TIMING": break
			await _shot("seq_corner%d_%d" % [ci, i])
		await _wait_game(func(): return core.phase == "RESULT" and reveal >= 3 and result_t > 0.4)
		await _shot("%sresult%d" % [pre, ci])
		lc_last = leader_changed
		if bool(script_in.get("demo", {}).get("auto_continue", false)):   # let the after-turn countdown run out on its own
			await _wait_game(func(): return core.phase == "FINISHED" or core.corner_index != ci)
		else:
			await _wait_game(func(): return (not pb_started) or pass_t >= float(PB.pass_after_exit_s))
			_continue()
		if seqs and lc_last:
			for i in 6:
				await _wait_game(func(): return back_t >= i * 0.25)
				await _shot("seq_snap%d_%d" % [ci, i])
	await _wait_game(func(): return back_t > float(CC.transition_to_straight_s) + 0.2)
	await _shot("%sfinish" % pre)

## each phase QTE during playback: cursor mid-sweep, then the score (cars held at that phase's point)
func _qte_shots(ci: int) -> void:
	for i in 3:
		await _wait_game(func(): return core.phase != "TIMING" or qte_i > i or (qte_i == i and qte_seg == "sweep" and _qte_ms() >= float(QS.lead_ms) * 0.8))
		if core.phase == "TIMING" and qte_i == i and qte_seg == "sweep": await _shot("seq_qte%d_%d_sweep" % [ci, i])
		await _wait_game(func(): return core.phase != "TIMING" or qte_i > i or (qte_i == i and qte_seg == "show" and qte_seg_t - qte_show_t >= 0.15))
		if core.phase == "TIMING" and qte_i == i and qte_seg == "show": await _shot("seq_qte%d_%d_score" % [ci, i])

func _process(dt: float) -> void:
	if perf_on:   # CEL: wall-clock frame time (process + render of every viewport), shots/gif frames excluded
		var now := Time.get_ticks_usec()
		if perf_last > 0 and not busy and gif_dir == "" and perf_skip <= 0: perf_dts.append(float(now - perf_last) / 1000.0)
		perf_skip -= 1; perf_last = now
	dt = minf(dt, 0.05)
	if busy: return
	phase_t += dt; clock += dt; back_t += dt; stop_t += dt
	if core.phase == "SELECT":
		var stp := _sel_stop()
		if stp != last_stop:
			stop_from = {"pos": cam_pos, "look": cam_look, "fov": cam_fov}; stop_t = 0.0; last_stop = stp
	if core.phase == "TIMING": lock_hold_t += dt
	scroller.update(dt)   # infinite scroll on the Entry straight and during playback (incl. the QTE holds)
	if not (core.phase == "SELECT" and _sel_stop() > 0): scroll_shown = scroller.scroll_m()   # Apex / Exit selection stops are static (Austin 2026-11-12)
	var v: float = scroller.speed_ms()
	if mode == "MENU": phase_t = 0.0  # backdrop: the straight scrolls, the selection timer never runs
	if core.phase == "SELECT" and phase_t >= RaceCore.STRAIGHT_DURATION and script_in == null:
		_do_lock()  # timer expiry -> auto-fill (guide §4.2)
	if _playing(): v += _step_play(dt)
	_ease_gap(dt)
	if core.phase == "RESULT":
		result_t += dt
		reveal = mini(3, int(floor(phase_t / 0.6)) + 1)
		if reveal >= 3: cont_t += dt
		var auto: bool = script_in == null or bool(script_in.get("demo", {}).get("auto_continue", false))
		if auto and mode == "RACE" and cont_t >= float(PB.continue_s): _continue()
		if cont_pending: _continue()
	wheel_angle += minf(float(RS.wheel_spin_cap_rad_s), v / 0.31) * dt
	_step_lanes(dt)
	_render_hud(); _update_scene()
	if gif_dir != "" and clock >= gif_next:
		gif_next += gif_dt; _gif_frame()

func _gif_frame() -> void:
	busy = true
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(gif_dir.path_join("f%05d.png" % gif_n)); gif_n += 1
	busy = false

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
func _update_camera(pc: Dictionary, pp: Dictionary) -> void:
	var ch := _chase_pose(pc)   # B.5b fixed chase camera on the road centre line (the car moves across its lanes in front of it)
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
			cam_pos = ch[0]; cam_look = ch[1]
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
	straight_d.group.visible = st; corner_d.group.visible = not st; straight_d.road.visible = st; corner_d.road.visible = not st
	for m in art.scroll_mats:
		if m.has_meta("scrolls"): m.set_shader_parameter("scroll_m", scroll_shown)
	_stream_district(straight_d if st else corner_d, scroll_shown)
	for it in corner_d.items:   # keep props out of every camera lens (build_lsc.py:254 drops cedars within 5.5 m of a camera)
		var o: Node3D = it.obj
		o.visible = Vector2(o.position.x - cam_pos.x, o.position.z - cam_pos.z).length() >= 5.5
	var pth = straight_path if st else path
	var lp := _pass_lanes()
	var pp := _place(player_car, pth, s_player, lp.x)
	_place(rival_car, pth, s_player + rival_offset, lp.y)
	if absf(rival_offset) < float(PB.car_len_m) and player_car.visible: min_sep_overlap = minf(min_sep_overlap, absf(lp.x - lp.y))
	_update_camera(pth.point(s_player, 0.0), pp)
	cam.position = cam_pos
	cam.look_at(cam_look)
	cam.fov = cam_fov; glow_cam.fov = cam_fov
	glow_cam.global_transform = cam.global_transform
	var cars_on: bool = not (((core.phase == "SELECT" and mode == "RACE" and _sel_stop() > 0)) and bool(SC.hide_cars_at_stops))
	player_car.visible = cars_on; rival_car.visible = cars_on
	post_mat.set_shader_parameter("mirror_on", 1.0 if _mirror_on() else 0.0)
	sky_root.position = cam_pos  # painted sky follows the camera
	var t := Vector3(pp.tx, 0, pp.tz); var p := Vector3(pp.x, 0, pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)  # build_lsc.py:246
	mirror_cam.look_at(p - t * float(disp.mirror.look_back) + Vector3(0, float(disp.mirror.look_y), 0))
	_update_line_preview()
	_sync_cel()   # CEL:

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
		var ln := Track.LANE_FOR
		for k in ln:
			var wp := _pp(straight_path, ahead, Track.lane_offset(ln[k], c.dir, disp.lane_width_m), 0.05)
			lanes[k] = null if cam.is_position_behind(wp) else cam.unproject_position(wp)
	var pline: String = core.player_line() if core.phase == "TIMING" else (String((r as Dictionary).get("player_line", "")) if core.phase != "SELECT" else "")
	var play_phase: int = mini(2, qte_i)   # the phase being driven / held for its QTE
	# B.5a: both full lines face up from the start of playback; RESULT per phase from the sim's own resolve_stance (pure, no RNG)
	var rline: String = core.line if core.phase == "TIMING" else (String((r as Dictionary).get("line", "")) if core.phase != "SELECT" else "")
	var outs := []
	if pline.length() == 3 and rline.length() == 3:
		for i in 3: outs.append(Combat.resolve_stance(pline[i], rline[i]))
	var plate := {"name": _corner_name(c), "icon": _plate_icon(), "mode": "VIEW", "stop": _sel_stop(), "done": core.picks.size()}
	if core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s): plate.mode = "LOCK"
	elif _qte_active(): plate.mode = "QTE"; plate.stop = qte_i
	elif core.phase == "TIMING": plate.mode = "PLAY"; plate.stop = play_phase
	elif core.phase != "SELECT": plate.mode = "DONE"
	var lpv: Dictionary = disp.get("line_preview", {})
	hud.show_state({"phase": core.phase, "title": "CORNER %d/%d %s %s (%s)" % [core.corner_index + 1, cfg.corners.size(), String(c.district).to_upper(), c.corner, c.dir],
		"sub": "seed %d %s %s %dm/s" % [core.seed_value, C.PIN_COMMIT.substr(0, 7), rig, roundi(scroller.speed_ms())], "build": String(RaceCore.build_info().build), "lead": core.lead(), "gap": core.gap(),
		"left": left, "total": RaceCore.STRAIGHT_DURATION, "slots": slots, "hand": core.hand, "used": core.picks,
		"qte": _qte_hud(), "line": pline, "rline": rline, "outs": outs, "plate": plate, "locked_hold": core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s), "mirror": _mirror_on(), "play_phase": play_phase, "plan": plan, "turn_m": turn_m, "dir": c.dir, "lanes": lanes,
		"preview_panel": lpv.get("panel", [424, 372, 636, 479]), "gap_pos": lpv.get("gap_pos", [220, 98]),
		"result": r, "reveal": reveal, "cont_left": maxf(0.0, float(PB.continue_s) - cont_t), "leader_changed": leader_changed, "winner": core.winner() if core.phase == "FINISHED" else "", "cum_p": core.cum_p, "cum_o": core.cum_o,
		"last_corner": core.corner_index + 1 >= cfg.corners.size(), "fin": fin if core.phase == "FINISHED" else null})

## QTE panel state (hud.gd _qte_panel); null outside the QTE stage
func _qte_hud():
	if not _qte_active(): return null
	var z := _qte_zone()
	return {"i": qte_i, "seg": qte_seg, "ms": minf(_qte_ms(), z.y) if qte_seg == "sweep" else 0.0, "zone": [z.x, z.y], "zone_w": core.zone_width(),
		"bar_ms": float(QS.lead_ms) + float(C.QTE_ZONE_BASE_MS) + float(QS.tail_ms), "res": qte_res.duplicate(), "press": qte_press_ms.duplicate(),
		"line": core.player_line(), "key": String(QS.key), "t_left": maxf(0.0, _qte_timer_s() - qte_seg_t), "t_total": _qte_timer_s()}

# ── shots9: continuous course, lines, passes (display only; lead / gap always from the sim) ──
## straight S, corner 1, join, corner 2, exit as ONE road (track_road.gd build_course, shared with the editor preview)
func _build_course() -> void:
	var tr: Dictionary = TrackRoad.build_course(disp, cfg)
	course = tr.course; views = tr.views; straights = tr.straights

func _lane_d(stance: String) -> float:
	return Track.lane_offset_for_stance(stance, String(core.corner().dir), disp.lane_width_m)

## the car drives its line: Entry lane up to turn-in, Apex lane at mid-arc, Exit lane past the arc (lane/stance = the Entry rule,
## borrowed for Apex / Exit as in the B.5b frames' labels). Blend distances are PLACEHOLDERS (display.json playback_flow).
func _line_d(line: String, s: float) -> float:
	if line.length() < 3: return 0.0
	var arc: float = path.R * path.A; var sa: float = path.S + arc * 0.5
	var b0: float = path.S - float(PB.blend_before_m); var b1: float = path.S + arc + float(PB.blend_after_m)
	var e := _lane_d(line[0]); var a := _lane_d(line[1]); var x := _lane_d(line[2])
	if s <= b0: return e
	if s <= sa: return lerpf(e, a, Track.smooth((s - b0) / (sa - b0)))
	if s <= b1: return lerpf(a, x, Track.smooth((s - sa) / (b1 - sa)))
	return x

## TIMING after the LINE LOCKED hold (camera back at Entry) = playback, with the three QTE holds inside it
func _playing() -> bool: return core.phase == "TIMING" and lock_hold_t >= float(SC.lock_hold_s)
## a phase QTE is running (the cars are held at that phase's point)
func _qte_active() -> bool: return _playing() and qte_seg != "" and qte_i <= 2

## lateral targets per phase; a target that jumps (new highlight, next corner) is eased out, a line followed smoothly is exact
func _step_lanes(dt: float) -> void:
	var tp = tgt_p; var tr = tgt_r
	if mode == "RACE" and core.phase == "SELECT":
		tp = _lane_d(core.hand[core.picks[0]] if core.picks.size() > 0 else PLAN_ORDER[plan_sel])
		tr = _lane_d(core.line[0])
	elif core.phase == "TIMING" and not _playing():
		tp = _lane_d(core.player_line()[0]); tr = _lane_d(core.line[0])
	elif core.phase == "TIMING" or core.phase == "RESULT":
		var pl: String = core.player_line(); var rl: String = core.line
		tp = _line_d(pl, s_player); tr = _line_d(rl, s_player + rival_offset)
	if tp == null: tp = 0.0
	if tr == null: tr = 0.0
	var k := exp(-dt / float(PB.lane_ease_s))
	if tgt_p != null and absf(float(tp) - float(tgt_p)) > 1.2: err_p += float(tgt_p) - float(tp)
	if tgt_r != null and absf(float(tr) - float(tgt_r)) > 1.2: err_r += float(tgt_r) - float(tr)
	err_p *= k; err_r *= k; tgt_p = tp; tgt_r = tr
	lat_p = float(tp) + err_p; lat_r = float(tr) + err_r

## what the lead will be once this playback resolves: the same Combat.resolve_turn the core calls in submit_qte (pure, no RNG)
func _preview_lead(phases: Array) -> float:
	var pc := []; var oc := []
	for i in core.picks: pc.append(core.hand[i])
	for ch in core.line: oc.append(ch)
	var res := Combat.resolve_turn(pc, oc, core.player, core.opponent, Combat.mean_phase_qte(phases), C.OPPONENT_QTE, int(cfg.max_turns), phases)
	var cp: float = core.cum_p + res.player_progress; var co: float = core.cum_o + res.opponent_progress
	var t := cp + co
	return 0.0 if t == 0.0 else (cp - co) / t

func _preview_phases() -> Array: return qte_res.duplicate()

## pass target + plan: once the Exit QTE has finished (qte_i >= 3), off1 = the visual gap the sim's lead will give
## (same Combat.resolve_turn core.submit_qte uses). Until then the gap stays at off0 and there is no pass_plan.
## When the drawn order flips, the passer takes an open lane while the cars overlap if their lines would share a
## lane there (Austin: shared exit lane -> pass in an open lane, then settle). The sample window is the post-Exit
## animation (pass_after_exit_s), with s_player still following the playback clock and capping at the end of travel.
func _update_pass_target() -> void:
	if core.phase != "TIMING" and core.phase != "RESULT": return
	if qte_i < 3:
		off1_score = null; pass_plan = {}; return
	var sc := str(_preview_phases())
	if off1_score != null and String(off1_score) == sc: return
	off1_score = sc; off1 = Track.rival_draw_offset(_preview_lead(_preview_phases()), disp.visual_gap); pass_plan = {}
	if signf(off0) == signf(off1): return
	var pl: String = core.player_line(); var rl: String = core.line
	var travel: float = _travel()
	var dur: float = maxf(0.001, float(PB.pass_after_exit_s))
	var t_hold: float = _hold_t(2)
	var pb: float = float(disp.playback_s)
	var others := []; var mine := []; var conflict := false; var passer := "P" if off1 < off0 else "R"
	for i in 81:
		var t := dur * i / 80.0
		var o := lerpf(off0, off1, Track.smooth(t / dur))
		if absf(o) >= float(PB.overlap_clear_m): continue
		var sp := 8.0 + travel * minf(1.0, (t_hold + t) / pb)
		var dp := _line_d(pl, sp); var dr := _line_d(rl, sp + o)
		if absf(dp - dr) < float(PB.min_sep_m): conflict = true
		others.append(dr if passer == "P" else dp); mine.append(dp if passer == "P" else dr)
	if not conflict: return
	var w: float = disp.lane_width_m; var best := 0.0; var best_v := -1.0
	var avg := 0.0
	for m in mine: avg += float(m) / maxf(1.0, mine.size())
	for L in [-w, 0.0, w]:
		var mn := 99.0
		for ot in others: mn = minf(mn, absf(L - float(ot)))
		var v := mn - 0.01 * absf(L - avg)   # farthest from the other car; ties -> nearest to the passer's own line
		if v > best_v: best_v = v; best = L
	pass_plan = {"passer": passer, "open": best}

## longitudinal gap: hold the pre-turn gap exactly until the Exit QTE finishes, then lerp to the post-turn gap
## over pass_after_exit_s (smoothstep, no exp lag so RESULT lands on the resolved lead with no snap). The
## animation continues into RESULT when the leftover playback after the Exit hold is too short to read.
func _ease_gap(dt: float) -> void:
	if pb_started and (_playing() or core.phase == "RESULT"):
		if qte_i < 3:
			rival_offset = off0; return
		_update_pass_target()
		pass_t += dt
		var dur := maxf(0.001, float(PB.pass_after_exit_s))
		rival_offset = lerpf(off0, off1, Track.smooth(pass_t / dur))
		return
	if core.phase == "TIMING":
		rival_offset = off0; return
	rival_offset += (rival_offset_target - rival_offset) * (1.0 - exp(-dt / float(PB.gap_ease_s)))

## lateral positions with the pass offset: the passer moves to the open lane while the cars overlap, then back to its line
func _pass_lanes() -> Vector2:
	var dp := lat_p; var dr := lat_r
	if not pass_plan.is_empty() and (core.phase == "TIMING" or core.phase == "RESULT"):
		var a := absf(rival_offset)
		var w := 1.0 - Track.smooth((a - float(PB.overlap_full_m)) / (float(PB.overlap_clear_m) - float(PB.overlap_full_m)))
		if pass_plan.passer == "P": dp = lerpf(dp, float(pass_plan.open), w)
		else: dr = lerpf(dr, float(pass_plan.open), w)
	return Vector2(dp, dr)


# ── CEL: Cel A port (Arthur, unapproved experiment) ──
## Four extra 3D passes share the world: main-camera normals + depth (640x480) and rear-view normals + depth (mirror size).
## Every shader picks its output from the camera's cull layers (CEL_GB in cel.gdshaderinc), so all passes render in the same
## frame as the colour pass with identical PSX vertex snap. The post shader (shaders/post.gdshader) draws the ink from them.
## The HUD viewport is never touched: it is composited over the post rect after the dither, as in Gordon's build.
func _build_cel() -> void:
	var a := OS.get_cmdline_user_args()
	cel_enabled = bool(ProjectSettings.get_setting("cel/enabled", true))
	var ca = _arg("--cel", null)
	if ca != null: cel_enabled = String(ca) != "0"
	perf_on = a.has("--perf"); perf_skip = 30
	var clear := ~(CEL_BIT_N | CEL_BIT_D)
	cam.cull_mask = cam.cull_mask & clear; mirror_cam.cull_mask = mirror_cam.cull_mask & clear; glow_cam.cull_mask = glow_cam.cull_mask & clear
	var specs := [[world_vp, CEL_BIT_N], [world_vp, CEL_BIT_D], [mirror_vp, CEL_BIT_N], [mirror_vp, CEL_BIT_D]]
	for sp in specs:
		var src: SubViewport = sp[0]
		var vp := SubViewport.new(); vp.name = "CelGB%d" % cel_vps.size()
		vp.world_3d = world_vp.world_3d; vp.size = src.size; vp.msaa_3d = Viewport.MSAA_DISABLED
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		var c := Camera3D.new(); c.cull_mask = (0xFFFFF & clear & ~CEL_BIT_DECAL) | int(sp[1])
		var e := Environment.new(); e.background_mode = Environment.BG_COLOR
		e.background_color = Color.WHITE if sp[1] == CEL_BIT_D else Color(0.625, 0.625, 1.0)
		c.environment = e
		vp.add_child(c); c.current = true
		add_child(vp); move_child(vp, $Post.get_index())   # rendered before the post rect (GlowVP stays last, as Gordon's)
		cel_vps.append(vp); cel_cams.append(c)
	post_mat.set_shader_parameter("gn_tex", cel_vps[0].get_texture()); post_mat.set_shader_parameter("gd_tex", cel_vps[1].get_texture())
	post_mat.set_shader_parameter("mn_tex", cel_vps[2].get_texture()); post_mat.set_shader_parameter("md_tex", cel_vps[3].get_texture())
	post_mat.set_shader_parameter("mirror_flip", 1.0); post_mat.set_shader_parameter("dither_on", 1.0)
	post_mat.set_shader_parameter("ink_debug", 1.0 if a.has("--ink-debug") else 0.0)   # playtest flicker measure only
	set_cel(cel_enabled)
	print("CEL ", "ON" if cel_enabled else "OFF")

func set_cel(on: bool) -> void:
	cel_enabled = on
	RenderingServer.global_shader_parameter_set("cel_on", 1.0 if on else 0.0)
	post_mat.set_shader_parameter("ink_on", 1.0 if on else 0.0)
	for vp in cel_vps: (vp as SubViewport).render_target_update_mode = SubViewport.UPDATE_ALWAYS if on else SubViewport.UPDATE_DISABLED

func _sync_cel() -> void:
	if cel_cams.is_empty(): return
	for i in 4:
		var src: Camera3D = cam if i < 2 else mirror_cam
		var c: Camera3D = cel_cams[i]
		c.global_transform = src.global_transform; c.fov = src.fov; c.near = src.near; c.far = src.far
		c.keep_aspect = src.keep_aspect
	if cel_enabled:   # rear-view passes only while the mirror is shown
		var m := SubViewport.UPDATE_ALWAYS if _mirror_on() else SubViewport.UPDATE_DISABLED
		cel_vps[2].render_target_update_mode = m; cel_vps[3].render_target_update_mode = m

func _exit_tree() -> void:
	if not perf_on or perf_dts.size() < 10: return
	var arr := perf_dts.duplicate(); arr.sort()
	var tot := 0.0
	for v in arr: tot += v
	var mean := tot / arr.size()
	print("CEL_PERF cel=%s frames=%d mean_ms=%.2f avg_fps=%.1f p50_ms=%.2f p95_ms=%.2f p99_ms=%.2f" % ["on" if cel_enabled else "off", arr.size(), mean, 1000.0 / mean, arr[arr.size() / 2], arr[int(arr.size() * 0.95)], arr[int(arr.size() * 0.99)]])
