# ARTHUR CEL A PORT (unapproved experiment): copy of Gordon's two-corner main.gd. Every change is marked `# CEL:`.
# ARTHUR WANGAN TWO-CORNER (unapproved, Austin 2026-11-15): the Cel A soft port moved onto a Wangan expressway; every change marked `# WANGAN:`.
## Two-corner test, Godot presentation. Logic lives in race_core.gd. Scene refactor (2026-11-12): the nodes live in scenes
## (main.tscn composes track.tscn, touge_dressing.tscn, sky.tscn, car.tscn x2, camera_rig.tscn, hud.tscn; see the README
## 'Editor workflow'); this script wires them up and runs the game flow, cameras and passes exactly as before.
## User args (after --): --script-inputs <file> --shots <dir> --seed N --no-menu --line-preview-shots <dir>   (single look: 640x480, RGB555 + Bayer; no CRT/low-res)
## Main menu (Austin 2026-11-10) unless --script-inputs or --no-menu; --seed N prefills the seed field. headless_run.gd never shows it.
extends Control

const RaceCore = preload("res://scripts/race_core.gd")
const Track = preload("res://scripts/track.gd")
const C = preload("res://scripts/globals.gd")   # TOUGE: generated from sim/ by tools/gen_globals.py
const Combat = preload("res://scripts/combat.gd")  # display uses the pure resolve_stance only (no RNG)
const POST_SH = preload("res://shaders/post.gdshader")
const RoadScroller = preload("res://scripts/road_scroller.gd")
const GLOW_SH = preload("res://shaders/glow.gdshader")
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Dressing = preload("res://scripts/touge_dressing.gd")
const CamGuard = preload("res://scripts/cam_guard.gd")   # TOUGE: camera clearance (Austin t114u)
const LineChevrons = preload("res://scripts/line_chevrons.gd")
const WanganDressing = preload("res://scripts/wangan_dressing.gd")   # WANGAN:
var wangan_far = null   # WANGAN: {group, water} static bay / city / cranes / bridge
var gif_log: Array = []   # WANGAN: per gif frame: phase, corner, rig, mirror shown (playtest checks pick their frames from it)
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
var mode := "RACE"           # TOUGE: MENU -> CARSEL -> ROLE -> RACE
var carsel := {"sel": 0, "player": "mx5", "opp": "s2000"}   # TOUGE: car select (visual / model only)
var role_sel := 1             # TOUGE: 0 = LEAD, 1 = CHASE
var pending_seed := 0
var look_back := false        # TOUGE: head-on look-back toggle (L key / LOOK BACK button), every race
var turnout = null            # TOUGE: {t, off0, off_end, sgn0, s0, lat_p0, lat_r0} while the swap plays (after turn 5's RESULT)
var TO: Dictionary            # display.json turnout (PLACEHOLDERS)
var turnout_geo: Dictionary   # course s of the pocket (track_road.build_course)
var no_timer := false          # TOUGE debug (Austin t119u): planning + continue timers off (F6, --no-timer, display.json debug.no_timer)
var scroll_skip := 0.0         # TOUGE: road scroll withheld while the cars use the turnout lot (Austin t114u), so it resumes without a jump
var scroll_raw_prev := 0.0
var guard_c = null; var guard_s = null   # cam_guard.gd for the course / the scroll straight
var clip_stats := {"frames": 0, "raw": 0, "fixed": 0, "by_rig_raw": {}, "by_rig_fixed": {}, "max_raw": 0.0, "max_fixed": -1e9}
var heat_check := {"frames": 0, "max_err": 0.0, "bad": 0, "px_checks": 0, "px_bad": 0, "px_max_err": 0.0}
var cam_lot_from = null
var buttons: Array = []       # TOUGE: touch buttons drawn this frame (hit-tested by _tap)
var role_now := "chase"
var trace_zone := -1; var trace_ready := -1   # TOUGE: one trace line per QTE zone opening / RESULT ready (mobile check)
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
## TOUGE turnout clearance (Arthur ccd1126): car AABBs vs each other, the P sign, stall front (x=6.75) and back wall
var turnout_clear := {"frames": 0, "car_hits": 0, "sign_hits": 0, "stall_hits": 0, "wall_hits": 0,
	"min_car_gap": 99.0, "min_sign_gap": 99.0, "min_stall_gap": 99.0, "min_wall_gap": 99.0}
var gif_dir := ""; var gif_dt := 0.1; var gif_next := 0.0; var gif_n := 0
var chevrons: Node3D  # B.5d road chevrons (SELECT only, purely visual)
# CEL: Cel A port. Toggle = project setting cel/enabled, overridden by user arg --cel 0|1, live key F7.
const CEL_BIT_N := 1 << 18   # layer 19: view-normal pass (CEL_GB = 1)
const CEL_BIT_D := 1 << 19   # layer 20: linear-depth pass (CEL_GB = 2)
const CEL_BIT_DECAL := 1 << 17   # layer 18: car decals (blob shadow, headlight throw); seen by the colour cameras, not the G-buffer
var cel_enabled := true
var cel_soft := true         # CEL: Cel A soft (default, Austin 2026-11-14). Setting cel/soft, arg --cel-soft 0|1, key F8
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
	RS = disp.road_scroller; CC = disp.corner_cams; SC = disp.select_cam; TO = disp.get("turnout", {})
	carsel.player = String(cfg.player.car); carsel.opp = String(cfg.opponent.car)
	if _arg("--player-car") != null: carsel.player = _arg("--player-car")
	if _arg("--opp-car") != null: carsel.opp = _arg("--opp-car")
	scroller = RoadScroller.new(RS)
	no_timer = bool(disp.get("debug", {}).get("no_timer", false)) or OS.get_cmdline_user_args().has("--no-timer")
	road_W = float(disp.road_half_m) if disp.has("road_half_m") else float(disp.lane_width_m) * 1.5 + 1.0
	if _arg("--script-inputs") != null:
		script_in = _json(_arg("--script-inputs"))
	shots_dir = _arg("--shots", "")
	if shots_dir != "": DirAccess.make_dir_recursive_absolute(shots_dir)
	if script_in != null: races = script_in.races if script_in.has("races") else [script_in]
	var seed_v: int = int(races[0].seed) if script_in != null else int(_arg("--seed", "20261113"))
	mode = "RACE" if (script_in != null or OS.get_cmdline_user_args().has("--no-menu")) else "MENU"
	if script_in != null and bool(script_in.get("touge_flow", false)): mode = "MENU"   # TOUGE scripted playtest starts at the menu
	menu.seed_text = _arg("--seed", ""); menu.commit = "%s build %s" % [C.PIN_COMMIT.substr(0, 7), String(RaceCore.build_info().build)]
	menu.title = "touge race: 10 turns downhill"
	if not OS.has_feature("web"): menu.items.append("QUIT")  # Quit: Godot desktop only
	DIST = disp.districts; CS = disp.car_shading; PAL = disp.palette; PB = disp.playback_flow; QS = disp.qte_sweep
	gif_dir = _arg("--gif", ""); gif_dt = float(_arg("--gif-dt", "0.1"))
	if gif_dir != "": DirAccess.make_dir_recursive_absolute(gif_dir)
	_build_viewports()
	scale = Vector2(2, 2)   # 640x480 design units on the 1280x960 base
	_fit_scale(); get_window().size_changed.connect(_fit_scale)
	_build_course()
	for cc in cfg.corners:   # WANGAN: the far set is built once (the deck is rebuilt per corner like Gordon's road)
		if String(cc.district) == "wangan" and wangan_far == null: wangan_far = WanganDressing.build_static(art, course, $WorldVP)
	player_car = _load_car($WorldVP/PlayerCar)   # car.tscn: car_mx5.glb, mx5_env.png, car_shading.mx5
	rival_car = _load_car($WorldVP/RivalCar)     # car.tscn: car_s2000.glb, s2000_env.png, car_shading.s2000
	for c in [player_car, rival_car]:   # CEL: decals (StandardMaterial3D planes) stay out of the G-buffer, so they never get inked
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is StandardMaterial3D: (ch as MeshInstance3D).layers = CEL_BIT_DECAL
	chevrons = LineChevrons.new()
	chevrons.cfg = disp.get("line_preview", {})
	$WorldVP.add_child(chevrons)
	core = RaceCore.new()
	role_now = String(_arg("--role", races[0].get("role", "chase") if script_in != null else "chase"))
	_apply_cars()
	core.setup(_race_cfg(), seed_v, role_now)
	_qte_cam_on_race_start()
	_setup_corner()
	if script_in != null and bool(script_in.get("touge_flow", false)):
		_run_touge_script()
	elif script_in != null:
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
	hud.setup(load("res://assets/tex/kit/font_6x9.png"), _json("res://assets/tex/kit/font.json"), load("res://assets/tex/kit/panel9.png"), load("res://assets/tex/kit/logo_v3.png"))
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

## TOUGE: the race config with the selected cars (stats stay the parity block: race_core.car_stats, car choice is visual only)
func _race_cfg() -> Dictionary:
	var c := cfg.duplicate(true); c.player.car = carsel.player; c.opponent.car = carsel.opp
	return c

## TOUGE: swap a car.tscn instance to another model in assets/cars (car_<id>.glb + its env map, display.json car_shading.<id>)
func _set_car(car: Node3D, id: String) -> void:
	if String(car.car_id) == id and car.has_meta("root"): return
	for ch in car.get_children():
		if ch.name != "Model": car.remove_child(ch); ch.queue_free()
	car.car_id = id
	car.env_texture = load("res://assets/tex/cars/%s.png" % String(disp.cars.env[id]))
	car.mats.clear()
	car.model = load("res://assets/cars/%s/car_%s.glb" % [id, id])   # setter respawns Model
	car.setup(art, CS)
	for ch in car.get_children():   # CEL: decals stay out of the G-buffer
		if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is StandardMaterial3D: (ch as MeshInstance3D).layers = CEL_BIT_DECAL

func _apply_cars() -> void:
	_set_car(player_car, carsel.player); _set_car(rival_car, carsel.opp)
	car_mats.clear(); car_mats.append_array(player_car.mats); car_mats.append_array(rival_car.mats)
	if core != null and core.corner_index >= 0: _apply_district(String(core.corner().district))
	if cel_vps.size() > 0: _sync_cel_cars()
	_arthur_refresh_look()

func _sync_cel_cars() -> void: pass

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
	sky_mat.set_shader_parameter("tex", _tex(String(D.get("sky", dk)) + "_sky"))   # WANGAN: district may borrow a sky / band
	band_mat.set_shader_parameter("band_tex", _tex(String(D.band) if D.has("band") else ("street_skyline" if dk == "street" else "touge_ridge")))
	# CEL: ink fades into this district's fog
	post_mat.set_shader_parameter("fog_color", Vector3(fc.r, fc.g, fc.b))
	var fn = D.get("ink_near", D.get("fog_near", D.get("fog_near_m", 9.0))); var ff = D.get("ink_far", D.get("fog_far", D.get("fog_far_m", 78.0)))   # WANGAN: own ink fade
	post_mat.set_shader_parameter("fog_near", float(fn)); post_mat.set_shader_parameter("fog_far", float(ff))
	# CEL: road strips flatten wider (Cel A: 6 texels) and posterise in 9 sqrt-luma steps instead of 10. The touge asphalt
	# sits at luma 0.092 / 0.124 and 0.124 is exactly a 10-step boundary, which broke it into speckles that crawled as the road scrolled.
	for m in art.scroll_mats:
		var t = (m as ShaderMaterial).get_shader_parameter("tex")
		if t == _tex("touge_road") or t == _tex("street_road") or t == _tex("env/wangan_road"):
			m.set_shader_parameter("flat_radius", 6.0); m.set_shader_parameter("poster", 9.0)
		# CEL A SOFT: big surfaces (road, verge / terrain, cedar forest cards) keep smooth light: no toon bands, no posterise,
		# a wide de-dither blur. Props (guardrail strip, lamp posts) and the cars keep the hard bands. Ink is unchanged.
		var soft := { "touge_road": [14.0, 1.0], "street_road": [14.0, 1.0], "touge_verge": [8.0, 1.0], "street_walk": [8.0, 1.0],
			"touge_cedar_a": [3.0, 0.0], "touge_cedar_b": [3.0, 0.0],
			# WANGAN: road + shoulders (one texture), deck fascia / soffit and the bay are big surfaces -> smooth light
			"env/wangan_road": [14.0, 1.0], "env/wangan_fascia": [5.0, 1.0], "env/wangan_underside": [5.0, 0.0], "env/wangan_water": [10.0, 0.0] }
		for k in soft:
			if t == _tex(k):
				m.set_shader_parameter("soft_surface", 1.0); m.set_shader_parameter("soft_radius", soft[k][0]); m.set_shader_parameter("soft_clamp_u", soft[k][1])

## StraightRoad + CornerRoad (§13.1), dressed for the upcoming corner's district: road strips in track.tscn, props in touge_dressing.tscn
func _build_road(dk: String) -> void:
	var track = $WorldVP/Track; var dressing = $WorldVP/Dressing
	track.clear(); dressing.clear()
	art.reset_for_rebuild()
	var sr = track.build_strip(art, straight_path, RS.straight_from_m, RS.straight_to_m, dk, "StraightRoad")
	straight_d = dressing.build(art, straight_path, RS.straight_from_m, RS.straight_to_m, dk, "StraightDressing", {"gantries": [150.0]}); straight_d.road = sr
	var cr = track.build_strip(art, course, -60.0, course.length + 60.0, dk, "CourseRoad")   # the whole continuous course (both corners)
	var gan := []   # WANGAN: overhead sign gantries: one on the scroll straight, one on the course before corner 2's turn-in
	if dk == "wangan" and views.size() > 1: gan = [views[1].off + views[1].S - 34.0]
	corner_d = dressing.build(art, course, -60.0, course.length + 60.0, dk, "CourseDressing", {"gantries": gan, "turnout": turnout_geo}); corner_d.road = cr
	if dk == "touge" and disp.has("cam_guard"):   # TOUGE: camera clearance against the kit (lamps are fixed, so their poses are known now)
		_stream_district(corner_d, scroll_shown); _stream_district(straight_d, scroll_shown)
		var lot_l: Array = corner_d.lot_group.get_meta("lamps") if corner_d.get("lot_group") != null else []
		guard_c = CamGuard.new(); guard_c.setup(course, road_W, DIST[dk], disp.cam_guard, turnout_geo, _lamp_list(corner_d.items, lot_l))
		guard_s = CamGuard.new(); guard_s.setup(straight_path, road_W, DIST[dk], disp.cam_guard, {}, _lamp_list(straight_d.items, []))
	else:
		guard_c = null; guard_s = null
	start_marks = null
	if dk == "touge" and core.corner_index == 0: start_marks = _start_marks(dressing)
	for c in [player_car, rival_car]:  # car head/tail glow sprites keep their fog uniforms in step
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is ShaderMaterial and ((ch as MeshInstance3D).material_override as ShaderMaterial).shader == GLOW_SH:
				art.glow_mats.append((ch as MeshInstance3D).material_override)
	_apply_district(dk)

func _pp(pth, s: float, d: float, y: float = 0.0) -> Vector3: return ArtKit.pp(pth, s, d, y)

## TOUGE (Austin t121 item 12): flat painted white start stripe across the road just ahead of the parked cars, plus a faded grid
## box round each car. Flat paint (chevron shader: unlit, fogged, absent from the cel G-buffer) = never inked, per the Cel A
## road-marking rule. Built on the first scroll straight; it slides back with the road scroll once the race starts.
## PLACEHOLDER (Gordon) sizes: display.json start_marks.
var start_marks: Node3D = null
func _start_marks(dressing) -> Node3D:
	var SM: Dictionary = disp.get("start_marks", {})
	var g := Node3D.new(); g.name = "StartMarks"; straight_d.group.add_child(g)
	var s_line: float = 8.0 + float(SM.get("ahead_m", 2.7))   # s_player = 8.0 (start_race), stripe just ahead of the bumpers
	var dep: float = float(SM.get("stripe_depth_m", 0.45)); var edge: float = float(SM.get("edge_in_m", 0.25))
	var paint = dressing._paint_mat(art, float(SM.get("stripe_gain", 0.92)))
	g.add_child(art.band(straight_path, s_line, s_line + dep, -(road_W - edge), 0.04, road_W - edge, 0.04, paint, dep, 1))
	var faded = dressing._paint_mat(art, float(SM.get("box_gain", 0.38)))
	var bw: float = float(SM.get("box_w_m", 2.5)); var bl: float = float(SM.get("box_l_m", 5.2)); var lw := 0.12
	for sd in [-1.0, 1.0]:
		var c: float = sd * float(disp.lane_width_m)
		var s0 := s_line - 0.3 - bl
		for dd in [c - bw * 0.5, c + bw * 0.5]:
			g.add_child(art.band(straight_path, s0, s_line - 0.3, dd - lw * 0.5, 0.035, dd + lw * 0.5, 0.035, faded, bl, 1))
		g.add_child(art.band(straight_path, s0, s0 + lw, c - bw * 0.5, 0.035, c + bw * 0.5, 0.035, faded, lw, 1))
	g.set_meta("s_line", s_line)
	return g

func _move_start_marks() -> void:
	if start_marks == null or not is_instance_valid(start_marks): return
	var s0: float = start_marks.get_meta("s_line")
	if _parked() or not start_marks.has_meta("k0"): start_marks.set_meta("k0", scroll_shown)   # scroll at the parked start
	var k: float = scroll_shown - float(start_marks.get_meta("k0")) if core.corner_index == 0 else 1e4
	start_marks.visible = k < 120.0
	if start_marks.visible: start_marks.position = _pp(straight_path, s0 - k, 0.0) - _pp(straight_path, s0, 0.0)

## lamp post bases + arm tips for cam_guard. Streamed lamps and Arthur's lot posts (lot_lamp_*, arm to local -X / the road)
## use global_position so a parent LotArt frame is honoured. Arm tip: placeholder lamp_mesh is (-1.4, 6.5, 0); Arthur's
## lot heads sit at about (-1.65, 5.95, 0) — the slightly longer arm is the conservative bound.
func _lamp_list(items: Array, extra: Array) -> Array:
	var out := []
	var nodes := []
	for it in items:
		if it.get("lamp", false): nodes.append(it.obj)
	nodes.append_array(extra)
	for n in nodes:
		var o := n as Node3D
		if o == null: continue
		var b: Vector3 = o.global_position
		out.append([b, b + o.global_transform.basis * Vector3(-1.65, 6.5, 0)])
	return out

# ── game flow ──
func _setup_corner() -> void:
	var c: Dictionary = core.corner()
	if mode == "RACE": _trace("turn %d/%d %s %s role=%s" % [core.corner_index + 1, cfg.corners.size(), c.corner, c.dir, core.role()])
	path = views[core.corner_index]; straight_path = straights[core.corner_index]
	_build_road(c.district)
	s_player = 8.0; phase_t = 0.0; qte_t = 0.0; reveal = 0; cam_curve_built = false; leader_changed = false
	cont_t = 0.0; pass_plan = {}; off1_score = null; pass_t = 0.0; cont_pending = false
	qte_i = 0; qte_seg = ""; qte_seg_t = 0.0; qte_show_t = 0.0; pb_started = false; qte_res = [null, null, null]; qte_press_ms = [null, null, null]; qte_from = null
	zone_ms = core.zone_ms()
	plan_sel = 0; _plan_fix_sel(0)
	last_stop = 0; stop_t = 99.0; stop_from = null; lock_hold_t = 99.0; lock_from = null
	rival_lane_d = Track.lane_offset_for_stance(core.entry_tell().stance, c.dir, disp.lane_width_m)
	rival_offset_target = _touge_offset(core.seg_lead(), core.role())
	scroller.transition_to_straight()
	if first_corner:
		rival_offset = rival_offset_target; back_t = 99.0
		tgt_p = null; tgt_r = null; err_p = 0.0; err_r = 0.0
	else:
		_return_to_chase()
	first_corner = false
	_qte_cam_pick_turn()
	_arthur_refresh_look()

## Full reset for START / RESTART / NEW RACE: a fresh RaceCore (fresh MT19937 seeded from s) and every display-side race variable.
func start_race(s: int, role_first := "") -> void:
	if role_first != "": role_now = role_first
	core = RaceCore.new(); core.setup(_race_cfg(), s, role_now); mode = "RACE"; turnout = null; look_back = false
	_qte_cam_on_race_start()
	scroller = RoadScroller.new(RS); scroll_skip = 0.0; scroll_raw_prev = 0.0; clock = 0.0; wheel_angle = 0.0; back_from = null; back_t = 99.0; pending_snap = false
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
		if item == "START RACE": _to_carsel(String(menu.seed_text).to_int() if menu.seed_text != "" else _random_seed())
		elif item == "SEED": menu.sel = 0
		elif item == "QUIT": get_tree().quit()

func _finish_choose(i: int) -> void:
	if i == 0: start_race(core.seed_value)
	elif i == 1: start_race(_random_seed())
	else: to_menu()

# ── TOUGE: car select -> parked start ("Lead or chase first?") -> race ──
func _to_carsel(sd: int) -> void:
	pending_seed = sd; mode = "CARSEL"; carsel.sel = 0
	start_race(sd); mode = "CARSEL"   # backdrop: the start line, cars parked
	_park(); _trace("mode=CARSEL seed=%d" % sd)

func _park() -> void:
	rival_offset = 0.0; rival_offset_target = 0.0; s_player = 8.0
	tgt_p = null; tgt_r = null; err_p = 0.0; err_r = 0.0

func _cycle_car(which: String, step: int) -> void:
	var order: Array = disp.cars.order
	var cur: String = carsel.player if which == "player" else carsel.opp
	var nxt: String = order[(order.find(cur) + step + order.size()) % order.size()]
	if which == "player": carsel.player = nxt
	else: carsel.opp = nxt
	_apply_cars(); _trace("car player=%s opp=%s" % [carsel.player, carsel.opp])

func _carsel_key(k: int) -> void:
	if k == KEY_UP: carsel.sel = (int(carsel.sel) + 2) % 3
	elif k == KEY_DOWN: carsel.sel = (int(carsel.sel) + 1) % 3
	elif (k == KEY_LEFT or k == KEY_RIGHT) and int(carsel.sel) < 2: _cycle_car("player" if int(carsel.sel) == 0 else "opp", -1 if k == KEY_LEFT else 1)
	elif k == KEY_ENTER or k == KEY_KP_ENTER:
		if int(carsel.sel) < 2: carsel.sel = int(carsel.sel) + 1
		else: _to_role()
	elif k == KEY_ESCAPE or k == KEY_BACKSPACE: to_menu()

func _to_role() -> void:
	mode = "ROLE"; role_sel = 1
	start_race(pending_seed); mode = "ROLE"; _park(); _trace("mode=ROLE")

func _role_key(k: int) -> void:
	if k == KEY_LEFT or k == KEY_UP: role_sel = 0
	elif k == KEY_RIGHT or k == KEY_DOWN: role_sel = 1
	elif k == KEY_ENTER or k == KEY_KP_ENTER: _choose_role("lead" if role_sel == 0 else "chase")
	elif k == KEY_ESCAPE or k == KEY_BACKSPACE: mode = "CARSEL"

## the race starts from the chosen position: the cars pull off the line and settle into the role's gap (no snap)
func _choose_role(r: String) -> void:
	start_race(pending_seed, r); _park()
	rival_offset_target = _touge_offset(core.seg_lead(), core.role())
	_trace("mode=RACE role=%s cars=%s/%s" % [r, carsel.player, carsel.opp])

func _parked() -> bool: return mode == "CARSEL" or mode == "ROLE"

## TOUGE drawn gap (display.json visual_gap.touge, PLACEHOLDERS): the rival never changes side, so there is no visible pass.
## chase -> rival ahead, nearer as this half's lead grows; lead -> rival behind, farther as this half's lead grows.
func _touge_offset(seg_lead: float, role: String) -> float:
	var T: Dictionary = disp.visual_gap.touge
	var span: float = float(T.far_m) - float(T.near_m); var k: float = float(T.lead_scale) * span * seg_lead
	if role == "chase": return clampf(float(T.neutral_m) - k, float(T.near_m), float(T.far_m))
	return -clampf(float(T.neutral_m) + k, float(T.near_m), float(T.far_m))

func _finish_key(k: int) -> void:
	if k >= KEY_1 and k <= KEY_3: _finish_choose(k - KEY_1)
	elif k == KEY_LEFT or k == KEY_UP: fin.sel = (int(fin.sel) + 2) % 3
	elif k == KEY_RIGHT or k == KEY_DOWN: fin.sel = (int(fin.sel) + 1) % 3
	elif k == KEY_ENTER or k == KEY_KP_ENTER: _finish_choose(int(fin.sel))

## shared by the keyboard and the restart test harness
func handle_key(k: int) -> void:
	if mode == "MENU": _menu_key(k); return
	if mode == "CARSEL": _carsel_key(k); return
	if mode == "ROLE": _role_key(k); return
	if k == KEY_L and core.phase != "FINISHED": look_back = not look_back; return   # TOUGE: head-on look-back, every race
	if core.phase == "FINISHED": _finish_key(k); return
	if core.phase == "SELECT":
		if k >= KEY_1 and k <= KEY_3: _pick_stance(PLAN_ORDER[k - KEY_1])   # TOUGE: 1/2/3 = POW/HAN/EN direct pick
		elif k == KEY_UP: _plan_fix_sel(-1)
		elif k == KEY_DOWN: _plan_fix_sel(1)
		elif (k == KEY_LEFT or k == KEY_RIGHT) and core.picks.size() == 0: _plan_lane_step(-1 if k == KEY_LEFT else 1)
		elif k == KEY_BACKSPACE: core.unpick(); _plan_fix_sel(0)
		elif k == KEY_ENTER or k == KEY_KP_ENTER:
			if core.picks.size() >= 3: _do_lock()
			else:
				_pick_stance(PLAN_ORDER[plan_sel])
	elif core.phase == "TIMING" and k == KEY_SPACE and qte_i <= 2 and qte_seg == "sweep" and script_in == null:
		_qte_press()
	elif core.phase == "RESULT" and (k == KEY_ENTER or k == KEY_KP_ENTER) and reveal >= 3 and turnout == null:
		_continue()

## pick a stance for the next clash (keyboard Enter / 1-3, or a touch lane button); the 3rd pick locks the line
func _pick_stance(k: String) -> void:
	if core.phase != "SELECT": return
	var idx: int = core.first_free(k)
	if idx < 0 or not core.can_pick(idx): return
	core.pick(idx); _trace("pick %s turn=%d picks=%d" % [k, core.corner_index + 1, core.picks.size()])
	if core.picks.size() >= 3: _do_lock()   # Enter on EXIT locks the line
	else: _plan_fix_sel(0)

## after-turn pause ends (Enter, or the countdown runs out): next corner, or the finish
func _continue() -> void:
	if pb_started and pass_t < float(PB.pass_after_exit_s):
		cont_pending = true; return
	cont_pending = false
	if core.at_swap() and not TO.is_empty() and turnout == null:   # TOUGE: the turnout plays before turn 6
		_start_turnout(); return
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
	var n := {"HP": "HAIRPIN", "N90": "90-DEGREE", "SW": "SWEEPER", "IR": "INC RADIUS", "ES": "ESSES", "DR": "DEC RADIUS", "CH": "CHICANE"}   # WANGAN: SW / IR; TOUGE: ES / DR / CH
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
## TOUGE (G2 heat): a stance is available while its gauge is unlocked after the planned picks (race_core.allowed); the count is
## the copies left in the 3 x POW/HAN/EN planning list, so a stance can be planned for every clash while its gauge allows
func _plan_avail(skip_first := false) -> Dictionary:
	var a := {"P": 0, "H": 0, "E": 0}
	var al: Array = core.allowed() if core.phase == "SELECT" else ["P", "H", "E"]
	for h in core.hand: a[h] += 1
	for j in core.picks.size():
		if skip_first and j == 0: continue
		a[core.hand[core.picks[j]]] -= 1
	for k in a:
		if not al.has(k): a[k] = 0
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
	car.position = Vector3(p.x, float(p.get("y", 0.0)), p.z)
	car.rotation.y = atan2(p.tx, p.tz)
	# TOUGE: pitched to the grade, rolled to the bank (course.elev)
	var gr: float = (float(pth.point(s + 1.0, d).get("y", 0.0)) - float(pth.point(s - 1.0, d).get("y", 0.0))) * 0.5
	car.rotation.x = -atan(gr)
	car.rotation.z = atan(float(pth.point(s, d - 1.0).get("y", 0.0)) - float(p.get("y", 0.0)))
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
	_trace("qte_press phase=%d ms=%d score=%s" % [qte_i, roundi(ms), str(qte_res[qte_i])])
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
		if trace_zone != qte_i and ms >= _qte_zone().x: trace_zone = qte_i; _trace("qte_zone phase=%d" % qte_i)
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
		_trace("qte_sweep phase=%d lead_ms=%d zone_ms=%d" % [qte_i, int(QS.lead_ms), int(zone_ms)]); trace_zone = -1
	else:
		qte_t += dt; dv = _travel() / float(disp.playback_s)
	s_player = 8.0 + _travel() * minf(1.0, qte_t / float(disp.playback_s))
	_update_pass_target()
	if qte_t >= float(disp.playback_s) and qte_seg == "" and qte_i >= 3:
		var before: float = core.lead()
		core.submit_qte(qte_res.duplicate()); reveal = 0; phase_t = 0.0; result_t = 0.0
		_trace("result turn=%d line=%s rival=%s p=%f o=%f" % [core.corner_index + 1, core.result.player_line, core.result.rival_played, core.result.player_progress, core.result.opponent_progress])
		var after: float = core.lead()
		leader_changed = false   # TOUGE: no visible passing (order never flips in a turn)
		rival_offset_target = _touge_offset(core.seg_lead(), core.role())  # = off1 (same resolve_turn)
		cont_t = 0.0
	return dv

func _do_lock() -> void:
	_trace("locked line=%s" % core.player_line() if core.picks.size() >= 3 else "locked (timer)")
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

## TOUGE (Austin t109u): touch. emulate_mouse_from_touch is off (project.godot), so a tap arrives once as InputEventScreenTouch;
## a desktop left click is handled the same way. Positions are mapped to 640x480 design units (make_input_local cancels the
## window scale and this node's x2).
func _input(e: InputEvent) -> void:
	if script_in != null: return
	var tapped := (e is InputEventScreenTouch and (e as InputEventScreenTouch).pressed) or \
		(e is InputEventMouseButton and (e as InputEventMouseButton).pressed and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT)
	if not tapped: return
	var le := make_input_local(e)
	_tap(le.position)
	get_viewport().set_input_as_handled()

func _tap(p: Vector2) -> void:
	for i in range(buttons.size() - 1, -1, -1):
		var b: Dictionary = buttons[i]
		if Rect2(b.r[0], b.r[1], b.r[2], b.r[3]).grow(2.0).has_point(p):
			if b.get("on", true): _button(String(b.id))
			return
	# no button: a tap anywhere counts as the QTE press during a sweep, and as Enter after a turn
	if mode == "RACE" and core.phase == "TIMING" and qte_i <= 2 and qte_seg == "sweep": _trace("tap anywhere=qte"); _qte_press()
	elif mode == "RACE" and core.phase == "RESULT" and reveal >= 3 and turnout == null: _trace("tap anywhere=continue"); _continue()
	else: _trace("tap miss at %d,%d mode=%s" % [roundi(p.x), roundi(p.y), mode])

## one console line per input / flow event (the Playwright mobile check reads them; cheap, also handy on device logs)
func _trace(msg: String) -> void:
	if script_in == null: print("TOUGE ", msg)

func _button(id: String) -> void:
	_trace("tap button=%s mode=%s" % [id, mode])
	match id:
		"start": _to_carsel(String(menu.seed_text).to_int() if menu.seed_text != "" else _random_seed())
		"p_prev": carsel.sel = 0; _cycle_car("player", -1)
		"p_next": carsel.sel = 0; _cycle_car("player", 1)
		"o_prev": carsel.sel = 1; _cycle_car("opp", -1)
		"o_next": carsel.sel = 1; _cycle_car("opp", 1)
		"next": _to_role()
		"lead": role_sel = 0; _choose_role("lead")
		"chase": role_sel = 1; _choose_role("chase")
		"pick_P", "pick_H", "pick_E": plan_sel = PLAN_ORDER.find(id.right(1)); _pick_stance(id.right(1))
		"undo": core.unpick(); _plan_fix_sel(0)
		"qte": if core.phase == "TIMING" and qte_i <= 2 and qte_seg == "sweep": _qte_press()
		"cont": _continue()
		"look": look_back = not look_back; _trace("look_back=%s" % str(look_back))
		"fin0": _finish_choose(0)
		"fin1": _finish_choose(1)
		"fin2": _finish_choose(2)

## the touch buttons for this frame (drawn by hud/touch_buttons.gd, hit-tested by _tap)
func _touch_buttons() -> Array:
	var T: Dictionary = disp.touch_ui; var out := []
	var r4 := func(a: Array) -> Array: return [float(a[0]), float(a[1]), float(a[2]), float(a[3])]
	if mode == "MENU":
		out.append({"id": "start", "r": r4.call(T.menu_start), "label": "START RACE", "sel": true}); return out
	if mode == "CARSEL":
		for i in 2:
			var y := 270.0 + i * 52.0; var pre := "p_" if i == 0 else "o_"
			out.append({"id": pre + "prev", "r": [150.0, y, 48.0, 40.0], "label": "<", "sz": 16, "sel": int(carsel.sel) == i})
			out.append({"id": pre + "next", "r": [442.0, y, 48.0, 40.0], "label": ">", "sz": 16, "sel": int(carsel.sel) == i})
		out.append({"id": "next", "r": [250.0, 422.0, 140.0, 40.0], "label": "NEXT", "sel": int(carsel.sel) == 2}); return out
	if mode == "ROLE":
		out.append({"id": "lead", "r": [166.0, 352.0, 142.0, 60.0], "label": "LEAD", "sub": "mouse", "sz": 18, "sel": role_sel == 0, "col": Color("#3CC8FF")})
		out.append({"id": "chase", "r": [332.0, 352.0, 142.0, 60.0], "label": "CHASE", "sub": "cat", "sz": 18, "sel": role_sel == 1, "col": Color("#FF9C3C")})
		return out
	if core.phase == "FINISHED":
		var fr: Array = r4.call(T.fin_row)
		for i in 3: out.append({"id": "fin%d" % i, "r": [fr[0] + i * (fr[2] + 8.0), fr[1], fr[2], fr[3]], "label": ["SAME SEED", "NEW RACE", "MENU"][i], "sel": int(fin.sel) == i})
		return out
	out.append({"id": "look", "r": r4.call(T.lookback), "label": "LOOK BACK" if not look_back else "FORWARD", "sz": 10, "sel": look_back})
	if core.phase == "SELECT" and core.picks.size() < 3 and turnout == null:
		var sr: Array = r4.call(T.stance_row); var lanes := _screen_lanes(); var a := _plan_avail()
		for i in 3:
			var k: String = lanes[i]
			out.append({"id": "pick_" + k, "r": [sr[0] + i * (sr[2] + 6.0), sr[1], sr[2], sr[3]], "label": {"P": "POW", "H": "HAN", "E": "EN"}[k],
				"sub": Track.LANE_FOR[k], "col": {"P": Color8(44, 184, 74), "H": Color8(240, 200, 40), "E": Color8(232, 40, 44)}[k], "on": int(a[k]) > 0, "sel": PLAN_ORDER[plan_sel] == k})
		if core.picks.size() > 0: out.append({"id": "undo", "r": r4.call(T.undo), "label": "UNDO", "sz": 11})
	elif _qte_active() and qte_seg == "sweep":
		out.append({"id": "qte", "r": r4.call(T.qte), "label": "TAP", "sz": 18, "sel": true})
	elif core.phase == "RESULT" and reveal >= 3 and turnout == null:
		out.append({"id": "cont", "r": r4.call(T.cont), "label": "CONTINUE", "sel": true})
	return out

# ── TOUGE: turnout after turn 5 (display only; the sim state is untouched until core.next() banks turns 1-5) ──
func _start_turnout() -> void:
	var sgn0: float = signf(rival_offset) if rival_offset != 0.0 else (1.0 if core.role() == "chase" else -1.0)
	var nr := "lead" if core.role() == "chase" else "chase"
	turnout = {"t": 0.0, "off0": rival_offset, "sgn0": sgn0, "s0": s_player, "new_role": nr, "off_end": _touge_offset(0.0, nr),
		"lat_p": lat_p, "lat_r": lat_r}
	look_back = false

func _turnout_u() -> float: return clampf(float(turnout.t) / float(TO.duration_s), 0.0, 1.0)
## distance fraction covered at time fraction u: speed = 1 - (1 - m) sin^2(pi u), normalised (dips to m, never stops)
func _turnout_F(u: float) -> float:
	var m: float = TO.min_speed_frac
	return (u - (1.0 - m) * (u / 2.0 - sin(TAU * u) / (4.0 * PI))) / ((1.0 + m) / 2.0)

func _step_turnout(dt: float) -> float:
	turnout.t = float(turnout.t) + dt
	var u := _turnout_u(); var s_prev := s_player
	s_player = float(turnout.s0) + float(TO.total_m) * _turnout_F(u)
	var near: float = float(disp.visual_gap.touge.near_m); var g0: float = turnout.sgn0
	var su: Array = TO.swap_u
	if u < float(su[0]): rival_offset = lerpf(float(turnout.off0), g0 * near, Track.smooth(u / float(su[0])))
	elif u < float(su[1]): rival_offset = lerpf(g0 * near, -g0 * near, Track.smooth((u - float(su[0])) / (float(su[1]) - float(su[0]))))
	else: rival_offset = lerpf(-g0 * near, float(turnout.off_end), Track.smooth((u - float(su[1])) / (1.0 - float(su[1]))))
	rival_offset_target = rival_offset
	var spd := (s_player - s_prev) / maxf(dt, 1e-6)
	if u >= 1.0:
		turnout = null
		core.next()   # banks turns 1-5 (race_core.next), starts turn 6 with the roles swapped
		if core.phase != "FINISHED": _setup_corner()
	return spd

## line-select (pick) timer: display.json pick_timer_s = 12.0 (Austin 2026-11-19, t121 item 9; no sim/globals constant yet)
func _pick_timer() -> float:
	return float(disp.get("pick_timer_s", RaceCore.STRAIGHT_DURATION))

## side of the turnout lot: the inside of the swap turn (-1 = left of travel); the drop is on the other side (Austin t121 item 11)
func _lot_ins() -> float:
	if turnout_geo.is_empty(): return -1.0
	return -course.drop_at((float(turnout_geo.s0) + float(turnout_geo.s1)) * 0.5)

## TOUGE turnout lanes (Austin t114u): both cars pull into the lot through its entrance taper, run its aisle and leave by the
## exit taper. Lateral position follows the lot outline at each car's own course s (so nobody crosses the island curb): the
## leader (front car at the start) takes the deep aisle lane and slows, the other car the near lane and goes by.
func _turnout_lanes() -> Vector2:
	var ins := _lot_ins()
	var rival_leads: bool = float(turnout.sgn0) > 0.0
	var deep := ins * (road_W + float(TO.lane_deep_m)); var near := ins * (road_W + float(TO.lane_near_m))
	var dp: float = turnout.lat_p; var dr: float = turnout.lat_r
	if turnout_geo.is_empty(): return Vector2(dp, dr)
	var a: float = turnout_geo.s0; var b: float = turnout_geo.s1; var tp: float = turnout_geo.taper
	var prof := func(sc: float) -> float: return Track.smooth(clampf(minf((sc - a) / tp, (b - sc) / tp), 0.0, 1.0))
	var kp: float = prof.call(path.off + s_player); var kr: float = prof.call(path.off + s_player + rival_offset)
	return Vector2(lerpf(dp, near if rival_leads else deep, kp), lerpf(dr, deep if rival_leads else near, kr))

## TOUGE turnout camera: the swap turn's held Exit camera watches the cars pull away (authored path, u < cam_hold_u), then a
## fixed shot from the lot's exit end on the valley side of the road, then back to chase. Returns false = use the corner camera.
func _turnout_cam(ch: Array, tgt: Vector3) -> bool:
	var u := _turnout_u()
	if u < float(TO.cam_hold_u): return false
	var cl: Dictionary = TO.cam_lot; var out := -_lot_ins()
	var sl: float = lerpf(float(turnout_geo.s0), float(turnout_geo.s1), float(cl.s_frac))
	var q: Dictionary = course.point(sl, out * (road_W + float(cl.d_out_m)))
	var lot_pos := Vector3(q.x, float(q.y) + float(cl.h_m), q.z)
	var mid: Vector3 = (player_car.position + rival_car.position) * 0.5 + Vector3(0, 0.8, 0)
	var lu: Array = TO.cam_lot_u
	rig = "TOL"
	if u < float(lu[1]):
		cam_pos = lot_pos; cam_look = mid; cam_fov = float(cl.fov); return true
	var k := Track.smooth((u - float(lu[1])) / maxf(1.0 - float(lu[1]), 1e-3))
	cam_pos = lot_pos.lerp(ch[0], k); cam_look = mid.lerp(ch[1], k); cam_fov = lerpf(float(cl.fov), cam_fov, k); rig = "BCH"
	return true

func _parked_cam(_pp: Dictionary) -> void:
	var pk: Dictionary = disp.parked_cam
	var c: Dictionary = straight_path.point(s_player + float(pk.ahead_m), float(pk.side_m))
	var t: Dictionary = straight_path.point(s_player, 0.0)
	cam_pos = Vector3(c.x, float(c.get("y", 0.0)) + float(pk.h_m), c.z); cam_look = Vector3(t.x, float(t.get("y", 0.0)) + float(pk.look_y), t.z)
	cam_fov = float(pk.fov); rig = "PRK"

func _course_pt(sv: float) -> Dictionary: return (straight_path if _in_straight() else path).point(sv, 0.0)

func _heat_hud():
	if core == null or mode != "RACE": return null
	# Austin t119u (POW gauge): planning and the locked turn's playback show the planned plays (core.projected(), the same
	# heat.play the sim runs in resolve_turn); from RESULT on, the resolved gauges (plays + passive, then recovery). Before this,
	# TIMING showed the pre-turn gauges, so the planned plays vanished at LINE LOCKED and POW (recovery 2.42 > a turn's POW
	# cost for a 45 % POW car) never showed any heat at all outside planning.
	var g = core.projected() if (core.phase == "SELECT" or core.phase == "TIMING") else core.p_heat
	if core.phase == "TIMING" and OS.get_cmdline_user_args().has("--heat-legacy"): g = core.p_heat   # before/after stills only
	var fl: Array = g.fill(); var lk: Array = g.locked
	var over := {}
	if core.phase == "SELECT" and core.picks.size() < 3 and not g.all_locked():
		var k: String = PLAN_ORDER[plan_sel]
		over[k] = g.selectable(k) and g.overrun_if(k, String(core.corner().corner)) > 0.0
	return {"fill": {"P": fl[0], "H": fl[1], "E": fl[2]}, "locked": {"P": lk[0], "H": lk[1], "E": lk[2]}, "over": over, "release": float(C.HEAT_RELEASE), "who": "YOU"}

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_F7:   # CEL: live toggle
		set_cel(not cel_enabled); print("CEL ", "ON" if cel_enabled else "OFF"); return
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_F8:   # CEL: soft / original Cel A
		set_cel_soft(not cel_soft); print("CEL SOFT ", "ON" if cel_soft else "OFF (original Cel A)"); return
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_F6:   # TOUGE debug (Austin t119u)
		no_timer = not no_timer; print("TIMER ", "OFF" if no_timer else "ON"); _trace("no_timer %s" % str(no_timer)); return
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

# ── TOUGE scripted playtest (spec/touge_playtest.json): menu -> car select -> parked start + prompt -> 10 turns with the
## turnout swap -> finish, through the same key / button paths a player uses. Writes stills (_shot) and touge_result.json
## (the stances actually played, exact QTE scores, totals) for tools/parity_touge.py --game-result.
func _tw(sec: float) -> void:
	var t0 := clock
	await _wait_game(func(): return clock >= t0 + sec)

func _run_touge_script() -> void:
	var sc: Dictionary = script_in
	await _tw(0.6); await _shot("t00_menu")
	menu.seed_text = str(int(sc.seed)); handle_key(KEY_ENTER)   # START RACE -> car select
	await _tw(0.3)
	var want_p: String = sc.get("player_car", carsel.player); var want_o: String = sc.get("opp_car", carsel.opp)
	var guard := 0
	while carsel.player != want_p and guard < 6: _button("p_next"); guard += 1; await _tw(0.25)
	guard = 0
	while carsel.opp != want_o and guard < 6: _button("o_next"); guard += 1; await _tw(0.25)
	await _tw(0.5); await _shot("t01_car_select")
	handle_key(KEY_DOWN); handle_key(KEY_DOWN); handle_key(KEY_ENTER)   # NEXT -> parked start
	await _tw(0.6)
	role_sel = 0 if String(sc.get("role", "chase")) == "lead" else 1
	await _shot("t02_start_prompt")
	handle_key(KEY_ENTER)   # LEAD / CHASE
	await _tw(1.2); await _shot("t03_race_start")
	var played := []
	while core.phase != "FINISHED":
		var ci: int = core.corner_index
		var inp: Dictionary = sc.corners[ci]
		var want: String = String(inp.get("pick", "PHE"))
		await _tw(0.8)
		if ci == int(sc.get("lookback_turn", -1)):
			handle_key(KEY_L); await _tw(0.4); await _shot("t%02d_lookback" % (ci + 1)); handle_key(KEY_L); await _tw(0.2)
		if ci == 0 or ci == int(sc.get("shot_turn", 2)): await _shot("t%02d_select" % (ci + 1))
		for j in 3:
			var k: String = want[j] if j < want.length() else "P"
			if not core.allowed().has(k): k = core.allowed()[0]   # gauge locked: first allowed (logged in touge_result.json)
			plan_sel = PLAN_ORDER.find(k); await _tw(0.25)
			if j == 1 and ci == int(sc.get("shot_turn", 2)):
				await _wait_game(func(): return stop_t >= float(SC.move_s) + 0.1)
				await _shot("t%02d_apex_stop" % (ci + 1))
			if j == 2: await _heat_px_check("t%02d_select2" % (ci + 1))
			handle_key(KEY_ENTER)
			await get_tree().process_frame; await get_tree().process_frame
		script_qte = []
		for v in inp.qte:
			var sv = RaceCore.fdec(v)
			script_qte.append(null if sv == null else Combat.round_qte_score(float(sv)))
		var cam_turns: Array = (sc.get("cam_turns", []) as Array).map(func(v): return int(v))
		if ci == int(sc.get("shot_turn", 2)):
			await _wait_game(func(): return core.phase != "TIMING" or (qte_i == 1 and qte_seg == "sweep" and _qte_ms() >= float(QS.lead_ms) * 0.3))
			if core.phase == "TIMING":   # treadmill pair (Austin t115u/t116u): walls / rails / verge scroll with the road, lamps stay
				await _heat_px_check("t%02d_timing" % (ci + 1))
				await _shot("t%02d_qte_treadmill_a" % (ci + 1)); await _tw(0.12); await _shot("t%02d_qte_treadmill_b" % (ci + 1))
			await _wait_game(func(): return core.phase != "TIMING" or (qte_i == 1 and qte_seg == "sweep" and _qte_ms() >= float(QS.lead_ms) * 0.8))
			if core.phase == "TIMING":
				await _shot("t%02d_qte_apex" % (ci + 1))
				await _maybe_qte_cam_still()
			await _wait_game(func(): return core.phase != "TIMING" or qte_t >= 0.85 * float(disp.playback_s))
			if core.phase == "TIMING": await _shot("t%02d_playback" % (ci + 1))
		if cam_turns.has(ci + 1):   # dynamic camera: the corner path at the Entry / Exit QTE holds
			await _wait_game(func(): return core.phase != "TIMING" or (qte_i == 0 and qte_seg == "sweep" and _qte_ms() >= float(QS.lead_ms) * 0.8))
			if core.phase == "TIMING": await _shot("t%02d_cam_entry_qte" % (ci + 1))
			await _wait_game(func(): return core.phase != "TIMING" or (qte_i == 2 and qte_seg == "sweep" and _qte_ms() >= float(QS.lead_ms) * 0.8))
			if core.phase == "TIMING": await _shot("t%02d_cam_exit_qte" % (ci + 1))
		await _wait_game(func(): return core.phase == "RESULT" and reveal >= 3 and result_t > 0.4)
		await _heat_px_check("t%02d_result" % (ci + 1))
		if cam_turns.has(ci + 1): await _shot("t%02d_cam_exit_hold" % (ci + 1))
		played.append({"pick": String(core.result.player_line), "planned": want, "qte": (core.result.qte_in as Array).map(func(v): return null if v == null else RaceCore.fhex(float(v))), "qte_script": inp.qte, "rival": String(core.result.rival_played),
			"p": RaceCore.fhex(core.result.player_progress), "o": RaceCore.fhex(core.result.opponent_progress), "role": String(core.result.role),
			"heat_fill": (core.history[-1].p_fill as Array).map(func(v): return RaceCore.fhex(float(v))), "heat_drawn": hud.P.heat.drawn.duplicate()})
		if ci == 0 or ci == int(sc.get("shot_turn", 2)) or core.at_swap(): await _shot("t%02d_result" % (ci + 1))
		await _wait_game(func(): return (not pb_started) or pass_t >= float(PB.pass_after_exit_s))
		var swap: bool = core.at_swap()
		_continue()
		if swap:
			for m in 5:
				await _wait_game(func(): return turnout == null or _turnout_u() >= 0.1 + m * 0.2)
				if turnout != null: await _shot("t%02d_turnout_%d" % [ci + 1, m])
				if turnout != null and m == 2: await _lot_overview_shot("t%02d_lot_overview" % (ci + 1))
			await _wait_game(func(): return turnout == null)
			await _tw(0.5); await _shot("t%02d_after_swap" % (ci + 2))
	await _tw(1.5); await _shot("t99_finish")
	var out := {"seed": core.seed_value, "role_first": core.role_first, "player_car": carsel.player, "opp_car": carsel.opp,
		"use_draft_blocks": bool(cfg.get("use_draft_blocks", false)), "corners": played, "player_total": RaceCore.fhex(core.cum_p),
		"opponent_total": RaceCore.fhex(core.cum_o), "banked": [RaceCore.fhex(core.banked_p), RaceCore.fhex(core.banked_o)], "winner": core.winner(),
		"min_sep_overlap_m": min_sep_overlap, "clip_check": clip_stats, "heat_check": heat_check, "heat_px": heat_px_log, "turnout_clearance": turnout_clear}
	print("CLIP_CHECK frames=%d raw_clipping=%d fixed_clipping=%d max_raw_pen=%.3f max_fixed_pen=%.3f raw_by_rig=%s fixed_by_rig=%s" % [clip_stats.frames, clip_stats.raw, clip_stats.fixed, clip_stats.max_raw, clip_stats.max_fixed, str(clip_stats.by_rig_raw), str(clip_stats.by_rig_fixed)])
	print("HEAT_CHECK frames=%d bad=%d max_err=%s px_checks=%d px_bad=%d px_max_err=%.1f %s" % [heat_check.frames, heat_check.bad, str(heat_check.max_err), heat_check.px_checks, heat_check.px_bad, heat_check.px_max_err, "PASS" if heat_check.bad == 0 and heat_check.px_bad == 0 else "FAIL"])
	var tc_ok: bool = int(turnout_clear.car_hits) == 0 and int(turnout_clear.sign_hits) == 0 and int(turnout_clear.stall_hits) == 0 and int(turnout_clear.wall_hits) == 0
	print("TURNOUT_CLEARANCE_CHECK frames=%d car_overlap=%d sign=%d stall=%d wall=%d min_car_gap=%.3f min_sign_gap=%.3f min_stall_gap=%.3f min_wall_gap=%.3f %s" % [int(turnout_clear.frames), int(turnout_clear.car_hits), int(turnout_clear.sign_hits), int(turnout_clear.stall_hits), int(turnout_clear.wall_hits), float(turnout_clear.min_car_gap), float(turnout_clear.min_sign_gap), float(turnout_clear.min_stall_gap), float(turnout_clear.min_wall_gap), "PASS" if tc_ok else "FAIL"])
	var od: String = shots_dir if shots_dir != "" else ProjectSettings.globalize_path("res://.out")   # was ../out (outside the repo; null file when it is missing)
	DirAccess.make_dir_recursive_absolute(od)
	FileAccess.open(od.path_join("touge_result.json"), FileAccess.WRITE).store_string(JSON.stringify(out, " ", false, true))
	print("TOUGE_PLAYTEST_DONE winner=%s P=%f O=%f" % [core.winner(), core.cum_p, core.cum_o])
	get_tree().quit()

## review only: a high three-quarter view over the turnout lot (camera moved for this one frame, restored next frame)
func _lot_overview_shot(nm: String) -> void:
	var a: float = turnout_geo.s0; var b: float = turnout_geo.s1; var ins := _lot_ins()
	var c: Dictionary = course.point((a + b) * 0.5, ins * (road_W + 4.0)); var e: Dictionary = course.point(a - 10.0, -ins * 14.0)
	cam_override = [Vector3(e.x, float(e.y) + 22.0, e.z), Vector3(c.x, float(c.y), c.z), 55.0]
	await _shot(nm)
	cam_override = null
var cam_override = null

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
	if gif_dir != "": FileAccess.open(gif_dir.path_join("frames.json"), FileAccess.WRITE).store_string(JSON.stringify(gif_log))   # WANGAN:
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
	if not _parked(): scroller.update(dt)   # infinite scroll on the Entry straight and during playback (incl. the QTE holds); TOUGE: parked = speed 0
	var raw_scroll: float = scroller.scroll_m()
	if turnout != null: scroll_skip += raw_scroll - scroll_raw_prev   # TOUGE: the lot is fixed; the road scroll waits while the cars use it
	scroll_raw_prev = raw_scroll
	if not (core.phase == "SELECT" and _sel_stop() > 0): scroll_shown = raw_scroll - scroll_skip   # Apex / Exit selection stops are static (Austin 2026-11-12)
	var v: float = 0.0 if _parked() else scroller.speed_ms()
	if mode == "MENU" or _parked(): phase_t = 0.0  # backdrop: the straight scrolls, the selection timer never runs
	if core.phase == "SELECT" and phase_t >= _pick_timer() and script_in == null and not no_timer:
		_do_lock()  # timer expiry -> auto-fill (guide §4.2)
	if _playing(): v += _step_play(dt)
	if turnout != null: v += _step_turnout(dt)
	_ease_gap(dt)
	if core.phase == "RESULT":
		result_t += dt
		reveal = mini(3, int(floor(phase_t / 0.6)) + 1)
		if reveal >= 3: cont_t += dt
		if reveal >= 3 and trace_ready != core.corner_index: trace_ready = core.corner_index; _trace("result_ready turn=%d" % (core.corner_index + 1))
		var auto: bool = script_in == null or bool(script_in.get("demo", {}).get("auto_continue", false))
		if auto and mode == "RACE" and cont_t >= float(PB.continue_s) and turnout == null and not no_timer: _continue()
		if cont_pending and turnout == null: _continue()
	wheel_angle += minf(float(RS.wheel_spin_cap_rad_s), v / 0.31) * dt
	_step_lanes(dt)
	_render_hud(); _update_scene()
	if gif_dir != "" and clock >= gif_next:
		gif_next += gif_dt; _gif_frame()

func _gif_frame() -> void:
	busy = true
	await RenderingServer.frame_post_draw
	gif_log.append({"n": gif_n, "phase": core.phase, "ci": core.corner_index, "rig": rig, "mirror": _mirror_on(), "stop": _sel_stop(), "chev": core.phase == "SELECT" and mode == "RACE"})   # WANGAN: playtest frame log
	get_viewport().get_texture().get_image().save_png(gif_dir.path_join("f%05d.png" % gif_n)); gif_n += 1
	busy = false

## fixed chase camera (B.5b frames: build_lsc.py:245, see display.json camera)
func _chase_pose(pp: Dictionary) -> Array:
	var t := Vector3(pp.tx, 0, pp.tz); var p := Vector3(pp.x, float(pp.get("y", 0.0)), pp.z); var rt := Vector3(-pp.tz, 0, pp.tx)
	var k := 1.0; var cm: Dictionary = disp.camera   # 'fixed' chase camera: frame offsets as given, not mirrored per corner
	return [p - t * float(cm.back) + rt * (k * float(cm.side)) + Vector3(0, cm.height, 0),
		p + t * float(cm.look_ahead) + rt * (k * float(cm.look_side)) + Vector3(0, cm.look_y, 0)]

func _sel_stop() -> int: return mini(core.picks.size(), 2) if core.phase == "SELECT" and mode == "RACE" else 0

## B.5b Apex / Exit stop poses on the corner path: [pos, look, fov]
## TOUGE (Austin t114u, no camera in the geometry): camera moves between stop poses run along the course in (s, d, height above
## the road) instead of a straight chord, which on a hairpin cuts through the cut slope inside it. --no-cam-guard keeps the chord
## (before count only).
func _cam_lerp(a: Vector3, b: Vector3, k: float) -> Vector3:
	if guard_c == null or OS.get_cmdline_user_args().has("--no-cam-guard"): return a.lerp(b, k)
	var sa: float = guard_c.locate(a); var da: float = guard_c.sd_of(a.x, a.z)[1]
	var sb: float = guard_c.locate(b); var db: float = guard_c.sd_of(b.x, b.z)[1]
	var ha: float = a.y - course.elev(sa, da); var hb: float = b.y - course.elev(sb, db)
	var s := lerpf(sa, sb, k); var d := lerpf(da, db, k)
	var q: Dictionary = course.point(s, d)
	return Vector3(q.x, float(q.y) + lerpf(ha, hb, k), q.z)

func _stop_pose(stop: int) -> Array:
	var c: Dictionary = core.corner(); var k: float = Track.inside_sign(String(c.dir)); var arc: float = path.R * path.A
	var q: Dictionary = (SC.apex if stop == 1 else SC.exit).duplicate()
	var ov: Dictionary = disp.get("select_cam_by_code", {}).get(String(c.corner), {}).get("apex" if stop == 1 else "exit", {})   # WANGAN: per-corner stop poses
	for ok in ov: q[ok] = ov[ok]
	var out_m: float = float(q.cam_out_m)
	var D: Dictionary = DIST[String(c.district)]
	if D.has("sidewalk_w_m"): out_m = minf(out_m, road_W + float(D.sidewalk_w_m) - 0.5)   # Street: stay in front of the facade wall (no Street frame exists; DERIVED)
	var cp: Dictionary = path.point(path.S + arc * float(q.cam_arc), -k * out_m)
	var ts: float = path.S + arc * float(q.tgt_arc) if stop == 1 else path.S + arc + float(q.tgt_after_m)
	var tp: Dictionary = path.point(ts, k * float(q.tgt_in_m))
	return [Vector3(cp.x, float(q.cam_h) + float(cp.get("y", 0.0)), cp.z), Vector3(tp.x, float(q.tgt_y) + float(tp.get("y", 0.0)), tp.z), float(q.fov)]

## camera rig: chase (BCH) / authored corner Path3D (BCL/BCR, §13.3) / swing back to chase. No swing_overtake (Austin override).
func _update_camera(pc: Dictionary, pp: Dictionary) -> void:
	var ch := _chase_pose(pc)   # B.5b fixed chase camera on the road centre line (the car moves across its lanes in front of it)
	var c: Dictionary = core.corner()
	var cc = CC.get(c.corner)
	cam_fov = float(disp.camera.fov)
	if _parked(): _parked_cam(pp); return
	if look_back and core.phase != "FINISHED":   # TOUGE: head-on look-back (display.json lookback, Arthur Pass 4)
		var lb: Dictionary = disp.lookback; var fwd := Vector3(pp.tx, 0, pp.tz)
		var cpos: Vector3 = player_car.position
		cam_pos = cpos - fwd * float(lb.back_m) + Vector3.UP * float(lb.up_m); cam_look = cam_pos - fwd * float(lb.look_m)
		cam_look.y = float(_course_pt(s_player - float(lb.look_m)).get("y", cpos.y)) + float(lb.up_m)
		cam_fov = float(lb.fov); rig = "LKB"; return
	var stp := _sel_stop()
	if core.phase == "SELECT" and (stp > 0 or (stop_from != null and stop_t < float(SC.move_s))):
		var tgt: Array = _stop_pose(stp) if stp > 0 else [ch[0], ch[1], float(disp.camera.fov)]
		rig = ["BCH", "STA", "STX"][stp]
		if stop_from != null and stop_t < float(SC.move_s):
			var kk := Track.smooth(stop_t / float(SC.move_s))
			cam_pos = _cam_lerp(stop_from.pos, tgt[0], kk); cam_look = (stop_from.look as Vector3).lerp(tgt[1], kk); cam_fov = lerpf(float(stop_from.fov), tgt[2], kk)
		else:
			cam_pos = tgt[0]; cam_look = tgt[1]; cam_fov = tgt[2]
		return
	if core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s):   # B.5b: camera returns to Entry, LINE LOCKED, then playback
		rig = "BCH"
		if lock_from != null and lock_hold_t < float(SC.move_s):
			var kk := Track.smooth(lock_hold_t / float(SC.move_s))
			cam_pos = _cam_lerp(lock_from.pos, ch[0], kk); cam_look = (lock_from.look as Vector3).lerp(ch[1], kk); cam_fov = lerpf(float(lock_from.fov), cam_fov, kk)
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
	if core.phase == "TIMING" and _qte_cams_enabled():
		_apply_qte_cam(pp, pc, ch)
		return
	# TOUGE: chase camera through playback, the turnout and RESULT (the authored corner cameras are not used in the touge race)
	if bool(disp.get("touge_chase_only", true)):
		rig = "BCH"; cam_pos = ch[0]; cam_look = ch[1]
		if back_from != null and back_t < float(CC.transition_to_straight_s):
			var kb := Track.smooth(back_t / float(CC.transition_to_straight_s))
			cam_pos = (back_from.pos as Vector3).lerp(ch[0], kb); cam_look = (back_from.look as Vector3).lerp(ch[1], kb)
		return
	rig = "BCL" if c.dir == "L" else "BCR"
	var u: float = qte_t / float(disp.playback_s) if core.phase == "TIMING" else 1.0
	var tgt := Vector3(pp.x, 0.8 + float(pp.get("y", 0.0)), pp.z)   # TOUGE: road height
	if turnout != null and _turnout_cam(ch, tgt): return
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
			if guard_c != null and not OS.get_cmdline_user_args().has("--no-cam-guard"):   # TOUGE: a key buried in the cut slope moves to the open (valley) side (Austin t114u)
				var alt: Array = path.corner_cam_points("R" if c.dir == "L" else "L", cc)
				for i in pts.size():
					guard_c.locate(pts[i]); var cp: float = guard_c.clip(pts[i])
					guard_c.locate(alt[i]); var ca: float = guard_c.clip(alt[i])
					if cp > 0.0 and ca < cp: pts[i] = alt[i]
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

## mesh AABB in a given space (inv * global). For cars, only the glb under Model (blob shadow /
## headlight throw are unnamed PlaneMeshes on the car root and would inflate the box).
func _aabb_in(n: Node, inv: Transform3D) -> AABB:
	var root := n.get_node_or_null("Model")
	if root == null and n.has_meta("root"): root = n.get_meta("root")
	var acc: Array = []
	_collect_aabb_in(root if root != null else n, inv, acc)
	if acc.is_empty(): return AABB()
	var b: AABB = acc[0]
	for i in range(1, acc.size()):
		b = b.merge(acc[i])
	return b

func _collect_aabb_in(n: Node, inv: Transform3D, acc: Array) -> void:
	if n is MeshInstance3D and (n as MeshInstance3D).visible and (n as MeshInstance3D).mesh != null:
		var nm := String(n.name).to_lower()
		if nm.find("glow") < 0 and nm.find("decal") < 0 and nm.find("fx_") < 0 and nm.find("throw") < 0 and nm.find("shadow") < 0 and nm.find("blob") < 0 and nm.find("pool") < 0:
			var mi := n as MeshInstance3D
			acc.append(inv * mi.global_transform * mi.get_aabb())
	for ch in n.get_children():
		_collect_aabb_in(ch, inv, acc)

## +ve = separated, -ve = penetrating (metres)
func _aabb_gap(a: AABB, b: AABB) -> float:
	var dx := maxf(a.position.x - (b.position.x + b.size.x), b.position.x - (a.position.x + a.size.x))
	var dy := maxf(a.position.y - (b.position.y + b.size.y), b.position.y - (a.position.y + a.size.y))
	var dz := maxf(a.position.z - (b.position.z + b.size.z), b.position.z - (a.position.z + a.size.z))
	if dx <= 0.0 and dy <= 0.0 and dz <= 0.0:
		return -minf(minf(-dx, -dy), -dz)
	var gx := maxf(dx, 0.0); var gy := maxf(dy, 0.0); var gz := maxf(dz, 0.0)
	return sqrt(gx * gx + gy * gy + gz * gz)

func _find_named(n: Node, nm: String) -> Node3D:
	if n.name == nm and n is Node3D: return n as Node3D
	for ch in n.get_children():
		var h := _find_named(ch, nm)
		if h != null: return h
	return null

## during the turnout, in LotArt space (cars follow +Z): car vs car, P sign, stall front (x=6.75) and back wall (x=pocket_w_m)
func _turnout_clearance() -> void:
	var lg = corner_d.get("lot_group") if corner_d != null else null
	if lg == null: return
	var la := (lg as Node).get_node_or_null("LotArt") as Node3D
	if la == null: return
	var inv := la.global_transform.affine_inverse()
	var ap := _aabb_in(player_car, inv); var ar := _aabb_in(rival_car, inv)
	if ap.size == Vector3.ZERO or ar.size == Vector3.ZERO: return
	turnout_clear.frames = int(turnout_clear.frames) + 1
	var cg := _aabb_gap(ap, ar)
	turnout_clear.min_car_gap = minf(float(turnout_clear.min_car_gap), cg)
	if cg < 0.0: turnout_clear.car_hits = int(turnout_clear.car_hits) + 1
	var sign := _find_named(lg, "Sign")
	if sign != null:
		var sb := _aabb_in(sign, inv)
		var sg := minf(_aabb_gap(ap, sb), _aabb_gap(ar, sb))
		turnout_clear.min_sign_gap = minf(float(turnout_clear.min_sign_gap), sg)
		if sg < 0.0: turnout_clear.sign_hits = int(turnout_clear.sign_hits) + 1
	var aisle1 := 6.75
	var wall_x := float(TO.pocket_w_m)
	for box in [ap, ar]:
		var b: AABB = box
		var xmax: float = b.position.x + b.size.x
		var stall_gap: float = aisle1 - xmax
		var wall_gap: float = wall_x - xmax
		turnout_clear.min_stall_gap = minf(float(turnout_clear.min_stall_gap), stall_gap)
		turnout_clear.min_wall_gap = minf(float(turnout_clear.min_wall_gap), wall_gap)
		if stall_gap < 0.0: turnout_clear.stall_hits = int(turnout_clear.stall_hits) + 1
		if wall_gap < 0.0: turnout_clear.wall_hits = int(turnout_clear.wall_hits) + 1

func _update_scene() -> void:
	var st := _in_straight()
	straight_d.group.visible = st; corner_d.group.visible = not st; straight_d.road.visible = st; corner_d.road.visible = not st
	for m in art.scroll_mats:
		if m.has_meta("scrolls"): m.set_shader_parameter("scroll_m", scroll_shown)
	_stream_district(straight_d if st else corner_d, scroll_shown)
	_move_start_marks()
	for it in corner_d.items:   # keep props out of every camera lens (build_lsc.py:254 drops cedars within 5.5 m of a camera)
		var o: Node3D = it.obj
		var far := Vector2(o.position.x - cam_pos.x, o.position.z - cam_pos.z).length() >= 5.5
		if it.has("side"): o.visible = o.visible and (far or not bool(it.card))   # TOUGE kit6: only cedar cards; walls / rails / lamps are solved by cam_guard
		else: o.visible = far
	var pth = straight_path if st else path
	var lp := _pass_lanes()
	var pp := _place(player_car, pth, s_player, lp.x)
	_place(rival_car, pth, s_player + rival_offset, lp.y)
	if absf(rival_offset) < float(PB.car_len_m) and player_car.visible: min_sep_overlap = minf(min_sep_overlap, absf(lp.x - lp.y))
	if turnout != null: _turnout_clearance()
	_update_camera(pth.point(s_player, 0.0), pp)
	_guard_camera(st)
	if cam_override != null: cam_pos = cam_override[0]; cam_look = cam_override[1]; cam_fov = cam_override[2]
	cam.position = cam_pos
	cam.look_at(cam_look)
	cam.fov = cam_fov; glow_cam.fov = cam_fov
	glow_cam.global_transform = cam.global_transform
	_arthur_push_nearest_lamps()
	_arthur_update_trails()
	var cars_on: bool = not (((core.phase == "SELECT" and mode == "RACE" and _sel_stop() > 0)) and bool(SC.hide_cars_at_stops))
	player_car.visible = cars_on; rival_car.visible = cars_on
	post_mat.set_shader_parameter("mirror_on", 1.0 if _mirror_on() else 0.0)
	sky_root.position = cam_pos  # painted sky follows the camera
	if wangan_far != null:   # WANGAN: the bay follows the camera in whole 48 m tiles, so its texture stays world-locked
		(wangan_far.water as Node3D).position = Vector3(snappedf(cam_pos.x, 48.0), 0.0, snappedf(cam_pos.z, 48.0))
	if look_back and mode == "RACE": player_car.visible = false   # TOUGE: the camera sits inside the player's car on the look-back
	var t := Vector3(pp.tx, 0, pp.tz); var p := Vector3(pp.x, float(pp.get("y", 0.0)), pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)  # build_lsc.py:246
	mirror_cam.look_at(p - t * float(disp.mirror.look_back) + Vector3(0, float(disp.mirror.look_y), 0))
	_update_line_preview()
	_sync_cel()   # CEL:

## TOUGE (Austin t114u): every camera pose (chase, corner path, exit hold, look-back, parked start, turnout, stops) is checked
## against the kit model (cam_guard.gd) and pulled in along its line of sight when it would clip. clip_stats counts the raw and
## the fixed poses per rig, so the scripted run reports the before / after numbers (CLIP_CHECK line at the end).
func _guard_camera(st: bool) -> void:
	var g = guard_s if (st or _parked()) else guard_c
	if g == null or mode == "MENU": return
	var raw := cam_pos
	g.locate(raw)   # hint from the camera itself (stop / corner cameras sit far from s_player; was path.off + s_player)
	var c0: float = g.clip(raw)
	if OS.get_cmdline_user_args().has("--no-cam-guard"): pass   # before / after count only: poses as authored, nothing pulled in
	elif look_back:   # the look-back sits inside the player's car: keep it there, only lift it if a slope would cut the lens
		if c0 > 0.0:
			var q := raw
			for k in 20:
				q.y += 0.1
				if g.clip(q) <= 0.0: break
			cam_pos = q
	else:
		cam_pos = g.fix(raw, cam_look)
	var c1: float = g.clip(cam_pos)
	if mode == "RACE":
		clip_stats.frames += 1
		var cf = _arg("--clip-frames", null)   # review only: save these race frames (pairs with a --no-cam-guard run's clip snaps)
		if cf != null and _arg("--clip-shots", null) != null and String(cf).split(",").has(str(clip_stats.frames)):
			_clip_snap(String(_arg("--clip-shots")), "frame_%s_f%05d" % [rig, clip_stats.frames], c0, c1)
		clip_stats.max_raw = maxf(clip_stats.max_raw, c0); clip_stats.max_fixed = maxf(clip_stats.max_fixed, c1)
		if c0 > 0.0: clip_stats.raw += 1; clip_stats.by_rig_raw[rig] = int(clip_stats.by_rig_raw.get(rig, 0)) + 1
		if c0 > 0.0:   # where the authored poses clip (turn / phase / rig / frame / penetration), for the before / after stills
			if not clip_stats.has("worst"): clip_stats.worst = {}
			var w: Dictionary = clip_stats.worst.get(rig, {})
			if c0 > float(w.get("pen", -1.0)): clip_stats.worst[rig] = {"pen": snappedf(c0, 0.001), "frame": clip_stats.frames, "turn": core.corner_index + 1, "phase": core.phase}
			var cs = _arg("--clip-shots", null)   # first frame per rig that clips by > 0.3 m: save the screen (run with and without the guard)
			if cs != null and c0 > 0.3 and not clip_snapped.has(rig):
				clip_snapped[rig] = true; _clip_snap(String(cs), "clip_%s_t%02d_f%05d" % [rig, core.corner_index + 1, clip_stats.frames], c0, c1)
				var sd0: Array = g.sd_of(raw.x, raw.z); g.locate(cam_pos); var sd1: Array = g.sd_of(cam_pos.x, cam_pos.z)
				print("CLIP_SNAP rig=%s raw=%s fixed=%s look=%s c0=%.3f c1=%.3f raw_sd=%s fixed_sd=%s straight_guard=%s st=%s phase=%s stop=%d" % [rig, str(raw), str(cam_pos), str(cam_look), c0, c1, str(sd0), str(sd1), str(g == guard_s), str(st), core.phase, _sel_stop()])
		if c1 > 0.0: clip_stats.fixed += 1; clip_stats.by_rig_fixed[rig] = int(clip_stats.by_rig_fixed.get(rig, 0)) + 1

var clip_snapped := {}
func _clip_snap(dir: String, nm: String, c0: float, c1: float) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join(nm + ".png"))
	_trace("clip snap %s raw %.3f shown %.3f" % [nm, c0, c1])

## rear-view mirror only on the chase camera (B.5b frames 1 and 4); none during corner playback (B.5a frames) or at the Apex/Exit stops
func _mirror_on() -> bool:
	if mode == "MENU" or _parked(): return false   # the menu logo sits where the mirror goes
	if look_back: return false
	if turnout != null: return true
	if core.phase == "SELECT": return _sel_stop() == 0 and not (stop_from != null and stop_t < float(SC.move_s))
	if core.phase == "TIMING": return lock_hold_t < float(SC.lock_hold_s)
	return core.phase == "FINISHED" and back_t >= float(CC.transition_to_straight_s)

var heat_ref_prev = null   # TOUGE heat check: the reference fills handed to the HUD last frame
## TOUGE (Austin t119u): every frame the HUD paints the gauges, compare the drawn bar fraction with the sim value: planning /
## locked playback = the planned plays (heat.play, as the sim's resolve_turn), from RESULT on = the turn's resolved p_fill
## (race_core history, the sim's TurnResult.player_heat_fill). Pixel widths are checked separately (_heat_px_check).
func _heat_ref():
	if core == null or mode != "RACE": return null
	var fl: Array
	if core.phase == "SELECT" or core.phase == "TIMING": fl = core.projected().fill()
	elif not core.history.is_empty(): fl = core.history[-1].p_fill
	else: fl = core.p_heat.fill()
	return {"P": float(fl[0]), "H": float(fl[1]), "E": float(fl[2])}

func _heat_check_frame() -> void:
	var hp = hud.P.get("heat")
	if hp == null or heat_ref_prev == null or not hp.visible or hp.drawn.is_empty() or hp.drawn_frame < 0: return
	heat_check.frames += 1
	var bad := false
	for k in ["P", "H", "E"]:
		var e := absf(float(hp.drawn[k]) - clampf(float(heat_ref_prev[k]), 0.0, 1.0))
		heat_check.max_err = maxf(heat_check.max_err, e)
		if e > 1e-6: bad = true
	if bad: heat_check.bad += 1

## pixel check: measure each bar's filled width in the HUD viewport (1280x960, panel at display.json touch_ui.heat_pos in 640
## space, trough 50..138 px, scale 2) against the reference fill; tolerance 2 px of 176
func _heat_px_check(tag: String) -> void:
	await RenderingServer.frame_post_draw
	var ref = heat_ref_prev
	if ref == null or not hud.P.heat.visible: return
	var img := hud_vp.get_texture().get_image()
	var hp: Array = disp.touch_ui.heat_pos
	var row := {}
	for r in 3:
		var k: String = ["P", "E", "H"][r]
		var y := int((float(hp[1]) + 15.0 + r * 16.0 + 4.0) * 2.0) + 1
		var x0 := int((float(hp[0]) + 50.0) * 2.0); var n := 0
		for x in range(x0, x0 + 176):
			var c := img.get_pixel(x, y)
			if absf(c.r - 20.0 / 255.0) < 0.03 and absf(c.g - 24.0 / 255.0) < 0.03 and absf(c.b - 40.0 / 255.0) < 0.03: break
			n += 1
		var want := clampf(float(ref[k]), 0.0, 1.0) * 176.0
		var err := absf(n - want)
		heat_check.px_checks += 1; heat_check.px_max_err = maxf(heat_check.px_max_err, err)
		if err > 2.0: heat_check.px_bad += 1
		row[k] = [n, snappedf(want, 0.1)]
	heat_px_log.append({"at": tag, "px": row})
var heat_px_log := []

func _render_hud() -> void:
	buttons = _touch_buttons()
	_heat_check_frame(); heat_ref_prev = _heat_ref()
	if mode == "MENU":
		menu.blink = int(floor(clock * 2.0)) % 2 == 0
		hud.show_state({"menu": menu, "buttons": buttons}); return
	if mode == "CARSEL":
		var ud := bool(cfg.get("use_draft_blocks", false))
		var ps: Dictionary = RaceCore.car_stats(carsel.player, ud); var os: Dictionary = RaceCore.car_stats(carsel.opp, ud)
		var draft: bool = ud and C.CAR_STAT_BLOCKS.get(carsel.player) == null
		var rr: float = (ps.pow + ps.han + ps.en) / (os.pow + os.han + os.en)
		hud.show_state({"buttons": buttons, "carsel": {"sel": carsel.sel, "rows": [
			{"label": "YOU", "car": disp.cars.names[carsel.player]}, {"label": "RIVAL  ·  %s" % String(cfg.opponent.name).to_upper(), "car": disp.cars.names[carsel.opp]}],
			"stats": ("POW %d  HAN %d  EN %d   vs   POW %d  HAN %d  EN %d" % [ps.pow, ps.han, ps.en, os.pow, os.han, os.en]) if draft else "stats: TODO(barry) parity placeholder (even, equal)",
			"parity": "%s  r = %.3f  (cap %.2f)" % ["IN PARITY" if RaceCore.in_parity(ps, os) else "OUT OF PARITY", rr, float(C.CAR_BLOCKS_PARITY_CAP_R)], "ok": RaceCore.in_parity(ps, os),
			"source": ("Barry draft blocks @%s (UNAPPROVED) · car choice is visual only" % C.CAR_BLOCKS_PIN) if draft else "car choice is visual only"}}); return
	if mode == "ROLE":
		hud.show_state({"buttons": buttons, "role_prompt": {"swap": core.swap_after(), "n": cfg.corners.size(), "you": disp.cars.names[carsel.player], "rival": "%s (%s)" % [String(cfg.opponent.name).to_upper(), disp.cars.names[carsel.opp]]}}); return
	var c: Dictionary = core.corner()
	var r = core.result if core.phase == "RESULT" else (core.history[-1] if core.history.size() > 0 else {})
	var slots := []
	for i in 3: slots.append(core.hand[core.picks[i]] if i < core.picks.size() else null)
	var left: float = maxf(0.0, _pick_timer() - phase_t)
	var turn_m: float = left * scroller.speed_ms()   # display: distance to turn-in at the current scroll speed
	var plan := {"phase": core.picks.size(), "sel": plan_sel, "avail": _plan_avail(), "avail_entry": _plan_avail(true),
		"entry": core.hand[core.picks[0]] if core.picks.size() > 0 else ""}
	var lanes = null
	if core.phase == "SELECT" and mode == "RACE" and false:   # WANGAN: no floating OUT / MID / IN markers (locked look: coloured road chevrons only)
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
	var to_st = null
	if turnout != null: to_st = {"new_role": turnout.new_role, "from": core.swap_after() + 1, "n": cfg.corners.size(), "banked": core.cum_p - core.cum_o}
	hud.show_state({"phase": core.phase, "title": "TURN %d/%d %s %s (%s)" % [core.corner_index + 1, cfg.corners.size(), String(c.district).to_upper(), c.corner, c.dir],
		"role": core.role() if turnout == null else String(turnout.new_role), "heat": _heat_hud(), "no_timer": no_timer, "heat_pos": disp.touch_ui.heat_pos, "turnout": to_st, "buttons": buttons,
		"sub": "seed %d %s %s %dm/s" % [core.seed_value, C.PIN_COMMIT.substr(0, 7), rig, roundi(scroller.speed_ms())], "build": String(RaceCore.build_info().build), "lead": 0.0 if turnout != null else core.seg_lead(), "gap": 0.0 if turnout != null else core.seg_gap(),
		"left": left, "total": _pick_timer(), "slots": slots, "hand": core.hand, "used": core.picks,
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
	course = tr.course; views = tr.views; straights = tr.straights; turnout_geo = tr.get("turnout", {})

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
## TOUGE: this half's lead once the turn resolves (core.preview = the same _resolve submit_qte runs, on copies of the gauges)
func _preview_lead(phases: Array) -> float:
	var res: Dictionary = core.preview(phases)
	var cp: float = core.seg_p() + res.player_progress; var co: float = core.seg_o() + res.opponent_progress
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
	off1_score = sc; off1 = _touge_offset(_preview_lead(_preview_phases()), core.role()); pass_plan = {}
	return   # TOUGE: the rival never changes side inside a turn, so there is never a pass to plan
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
	if turnout != null: return   # TOUGE: _step_turnout drives the gap
	if _parked(): rival_offset = 0.0; return
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
	if _parked(): return Vector2(-float(disp.lane_width_m), float(disp.lane_width_m))   # TOUGE: side by side on the start line (+/-1.45 m)
	if turnout != null: return _turnout_lanes()
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
	cel_soft = bool(ProjectSettings.get_setting("cel/soft", true))
	var cs = _arg("--cel-soft", null)
	if cs != null: cel_soft = String(cs) != "0"
	set_cel_soft(cel_soft)
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
	print("CEL ", "ON" if cel_enabled else "OFF", " SOFT ", "ON" if cel_soft else "OFF")

func set_cel_soft(on: bool) -> void:
	cel_soft = on
	RenderingServer.global_shader_parameter_set("cel_soft", 1.0 if on else 0.0)

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

# ── B.2b live night lighting (Arthur) + QTE camera types (outside / front / chase; inside removed Austin pt132u) ──
const QTE_CAM_TYPES := ["outside", "front", "chase"]
var qte_cam_rng: RandomNumberGenerator
var qte_cam_picks: Array = ["chase", "chase", "chase"]
var qte_cam_from = null
var qte_cam_section := -1
var qte_cam_still_done := false
var _arthur_lit_mats: Array = []
var _arthur_lamps_all: Array = []

const ARTHUR_TRAIL_SEC := 0.12
const ARTHUR_TRAIL_W0 := 0.12
const ARTHUR_TRAIL_W1 := 0.01
const ARTHUR_TRAIL_V0 := 6.0
const ARTHUR_TRAIL_V1 := 20.0
const ARTHUR_TRAIL_PEAK := 0.45

func _qte_cam_on_race_start() -> void:
	qte_cam_rng = RandomNumberGenerator.new()
	var off: int = 130001
	if disp != null and disp.has("qte_cams"):
		off = int(disp.qte_cams.get("seed_offset", 130001))
	var s: int = core.seed_value if core != null else 0
	qte_cam_rng.seed = s + off
	qte_cam_still_done = false

func _qte_cam_force() -> String:
	var cli = _arg("--qte-cam", "")
	if cli != null and String(cli) != "":
		return String(cli).strip_edges().to_lower()
	if disp != null and disp.has("qte_cams"):
		return String(disp.qte_cams.get("force", "")).strip_edges().to_lower()
	return ""

func _qte_cam_pick_turn() -> void:
	qte_cam_from = null
	qte_cam_section = -1
	var force := _qte_cam_force()
	qte_cam_picks = []
	if qte_cam_rng == null:
		_qte_cam_on_race_start()
	for i in 3:
		if force in QTE_CAM_TYPES:
			qte_cam_picks.append(force)
		else:
			qte_cam_picks.append(QTE_CAM_TYPES[qte_cam_rng.randi() % QTE_CAM_TYPES.size()])
	if mode == "RACE" and core != null:
		print("QTE_CAM turn=%d picks=%s force=%s seed=%d" % [core.corner_index + 1, ",".join(qte_cam_picks), force if force != "" else "rng", core.seed_value])

func _qte_cams_enabled() -> bool:
	return disp != null and disp.has("qte_cams")

func _qte_cam_kind() -> String:
	if qte_cam_picks.size() != 3:
		return "chase"
	var i: int = clampi(qte_i, 0, 2)
	return String(qte_cam_picks[i])

func _qte_cam_pose(kind: String, pp: Dictionary, pc: Dictionary) -> Array:
	var ch := _chase_pose(pc)
	var qc: Dictionary = disp.get("qte_cams", {})
	if kind == "chase" or not qc.has(kind):
		var fov_c: float = float(qc.get("chase", {}).get("fov", disp.camera.fov)) if qc.has("chase") else float(disp.camera.fov)
		return [ch[0], ch[1], fov_c]
	var spec: Dictionary = qc[kind]
	var pth = path if path != null else course
	if pth == null:
		return [ch[0], ch[1], float(disp.camera.fov)]
	var car_p := Vector3(pp.x, float(pp.get("y", 0.0)), pp.z)
	if kind == "front":
		var ahead: float = float(spec.get("ahead_m", 10.0))
		var side: float = float(spec.get("side_m", 0.0))
		var q: Dictionary = pth.point(s_player + ahead, side)
		var pos := Vector3(q.x, float(q.get("y", 0.0)) + float(spec.get("height_m", 2.2)), q.z)
		var look := car_p + Vector3(0.0, float(spec.get("look_y", 0.8)), 0.0)
		if pos.distance_to(look) < 0.2:
			look = car_p
		return [pos, look, float(spec.get("fov", 50.0))]
	# outside: drop / valley side, opposite Track.inside_sign (hairpins included). Inside cam removed (Austin pt132u).
	var c: Dictionary = core.corner()
	var ins: float = Track.inside_sign(String(c.dir))
	var sign: float = -ins
	var s_loc: float = s_player + float(spec.get("along_m", 2.0))
	var dist: float = float(spec.get("dist_m", 8.5))
	if course != null and path != null:
		var cap: float = course.cap_at(float(path.off) + s_loc, sign)
		dist = minf(dist, cap - 0.8)
		dist = maxf(dist, 2.0)
	var q2: Dictionary = pth.point(s_loc, sign * dist)
	var pos2 := Vector3(q2.x, float(q2.get("y", 0.0)) + float(spec.get("height_m", 1.8)), q2.z)
	var look2 := car_p + Vector3(0.0, float(spec.get("look_y", 0.7)), 0.0)
	if pos2.distance_to(look2) < 0.2:
		look2 = car_p
	return [pos2, look2, float(spec.get("fov", 52.0))]

func _apply_qte_cam(pp: Dictionary, pc: Dictionary, _ch: Array) -> void:
	var kind := _qte_cam_kind()
	var sec: int = clampi(qte_i, 0, 2)
	var pose: Array = _qte_cam_pose(kind, pp, pc)
	if qte_cam_section != sec:
		qte_cam_from = {"pos": cam_pos, "look": cam_look, "fov": cam_fov, "t0": clock}
		qte_cam_section = sec
	var ts: float = float(disp.qte_cams.get("transition_s", 0.45))
	var elapsed: float = clock - float(qte_cam_from.t0) if qte_cam_from != null else 99.0
	if qte_cam_from != null and elapsed < ts and ts > 0.0:
		var k := Track.smooth(elapsed / ts)
		cam_pos = _cam_lerp(qte_cam_from.pos, pose[0], k)
		cam_look = (qte_cam_from.look as Vector3).lerp(pose[1], k)
		cam_fov = lerpf(float(qte_cam_from.fov), pose[2], k)
	else:
		cam_pos = pose[0]; cam_look = pose[1]; cam_fov = pose[2]
	rig = {"outside": "QOUT", "front": "QFR", "chase": "QCH"}.get(kind, "QCH")

func _shot_to(path: String) -> void:
	if path == "":
		return
	busy = true
	_render_hud(); _update_scene()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var dir := path.get_base_dir()
	if dir != "":
		DirAccess.make_dir_recursive_absolute(dir)
	img.save_png(path)
	print("QTE_CAM_STILL ", path, " rig=", rig, " kind=", _qte_cam_kind())
	busy = false

func _maybe_qte_cam_still() -> void:
	var p = _arg("--qte-cam-still", "")
	if p == null or String(p) == "" or qte_cam_still_done:
		return
	await _shot_to(String(p))
	qte_cam_still_done = true

func _arthur_sodium_col() -> Vector3:
	return Vector3(0.941176, 0.784314, 0.580392)  # #F0C894

func _arthur_mercury_col() -> Vector3:
	return Vector3(0.658824, 0.878431, 0.831373)  # unused in the keeper look (sodium only)

func _arthur_moon_k() -> float:
	var raw = _arg("--moon-k")
	if raw != null:
		return float(raw)
	return 1.30

func _arthur_ambient_k() -> float:
	var raw = _arg("--ambient-k")
	if raw != null:
		return float(raw)
	return 0.56

func _arthur_moon_dir() -> Vector3:
	return Vector3(0.383, 0.643, -0.663).normalized()

func _arthur_refresh_look() -> void:
	if player_car == null or not is_inside_tree():
		return
	_arthur_apply_vertex_lit()
	_arthur_clear_flares()
	_arthur_apply_flares()
	_arthur_ensure_trails()
	_arthur_reset_trail_history()

func _arthur_clear_flares() -> void:
	var root := $WorldVP.get_node_or_null("ArthurFlares")
	if root != null:
		for ch in root.get_children():
			root.remove_child(ch)
			ch.free()
	for car in [player_car, rival_car]:
		if car == null:
			continue
		var drop: Array = []
		for ch in car.get_children():
			if "arthurflare" in String(ch.name).to_lower():
				drop.append(ch)
		for ch in drop:
			car.remove_child(ch)
			ch.free()

func _arthur_ensure_trails() -> void:
	var root := $WorldVP.get_node_or_null("ArthurTrails")
	if root == null:
		root = Node3D.new()
		root.name = "ArthurTrails"
		$WorldVP.add_child(root)
	var fog := Vector2(9.0, 78.0)
	if DIST != null and DIST.has("touge"):
		fog = Vector2(float(DIST.touge.fog_near), float(DIST.touge.fog_far))
	var sh: Shader = load("res://shaders/tail_trail.gdshader")
	var n := 0
	for car in [player_car, rival_car]:
		if car == null:
			continue
		var tails: Array = _arthur_trail_tail_locals(car)
		for i in tails.size():
			var nm := "ArthurTrail_%s_%d" % [car.name, i]
			var mi: MeshInstance3D = root.get_node_or_null(nm)
			if mi == null:
				mi = MeshInstance3D.new()
				mi.name = nm
				mi.mesh = ImmediateMesh.new()
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				mi.layers = 3
				mi.extra_cull_margin = 16384.0
				var mat := ShaderMaterial.new()
				mat.shader = sh
				mat.set_shader_parameter("color", Vector3(1.0, 0.12, 0.08))
				mat.set_shader_parameter("strength", 0.9)
				mat.set_shader_parameter("fog_near", fog.x)
				mat.set_shader_parameter("fog_far", fog.y)
				mat.render_priority = 6
				mi.material_override = mat
				root.add_child(mi)
			mi.set_meta("car", car)
			mi.set_meta("local", tails[i])
			if not mi.has_meta("hist"):
				mi.set_meta("hist", [])
			n += 1
	if not root.has_meta("ready_log"):
		root.set_meta("ready_log", true)
		print("TRAILS ribbons=", n, " window=", ARTHUR_TRAIL_SEC, "s width=", ARTHUR_TRAIL_W0, "->", ARTHUR_TRAIL_W1, " peak_a=", ARTHUR_TRAIL_PEAK, " speed=", ARTHUR_TRAIL_V0, "-", ARTHUR_TRAIL_V1, "m/s")

func _arthur_trail_tail_locals(car: Node3D) -> Array:
	var heads: Array = []
	var tails: Array = []
	_arthur_find_car_lights(car, car, heads, tails)
	if tails.is_empty():
		for x in [-0.58, 0.58]:
			tails.append(Vector3(x, 0.80, -2.06))
	return tails

func _arthur_reset_trail_history() -> void:
	var root := $WorldVP.get_node_or_null("ArthurTrails")
	if root == null:
		return
	for ch in root.get_children():
		ch.set_meta("hist", [])
		ch.set_meta("hold_hist", [])
		ch.set_meta("last_p", Vector3.ZERO)
		ch.set_meta("hold_k", 0.0)
		ch.set_meta("holding", false)
		if ch is MeshInstance3D and (ch as MeshInstance3D).mesh is ImmediateMesh:
			((ch as MeshInstance3D).mesh as ImmediateMesh).clear_surfaces()

func _arthur_trail_hold() -> bool:
	if mode != "RACE" or _parked() or core == null:
		return false
	if core.phase == "TIMING" and qte_seg != "":
		return true
	if core.phase == "SELECT" and _sel_stop() > 0:
		return true
	if core.phase == "TIMING" and lock_hold_t < float(SC.lock_hold_s):
		return true
	return false

func _arthur_lamp_xf(car: Node3D, local: Vector3) -> Transform3D:
	var xf := car.global_transform
	xf.origin = car.to_global(local)
	return xf

func _arthur_ribbon_follow_lamp(src: Array, from_xf: Transform3D, to_xf: Transform3D) -> Array:
	var out: Array = []
	var xform := to_xf * from_xf.affine_inverse()
	for rec in src:
		out.append({"t": rec.t, "p": xform * rec.p})
	return out

func _arthur_update_trails() -> void:
	var root := $WorldVP.get_node_or_null("ArthurTrails")
	if root == null:
		if player_car != null:
			_arthur_ensure_trails()
			root = $WorldVP.get_node_or_null("ArthurTrails")
		if root == null:
			return
	var now: float = clock
	var cam_p: Vector3 = cam.global_position if cam != null else Vector3.ZERO
	var hold: bool = _arthur_trail_hold()
	for ch in root.get_children():
		if not (ch is MeshInstance3D):
			continue
		var mi := ch as MeshInstance3D
		var car = mi.get_meta("car") if mi.has_meta("car") else null
		if car == null or not is_instance_valid(car) or not (car as Node3D).is_inside_tree():
			_arthur_draw_ribbon(mi, [], 0.0, cam_p)
			continue
		var car_n := car as Node3D
		var local: Vector3 = mi.get_meta("local") if mi.has_meta("local") else Vector3(0, 0.8, -2.06)
		var wp: Vector3 = car_n.to_global(local)
		var cur_xf: Transform3D = _arthur_lamp_xf(car_n, local)
		var hist: Array = mi.get_meta("hist") if mi.has_meta("hist") else []
		var last_p: Vector3 = mi.get_meta("last_p") if mi.has_meta("last_p") else Vector3.ZERO
		var was_hold: bool = bool(mi.get_meta("holding")) if mi.has_meta("holding") else false
		if (not hold) and last_p != Vector3.ZERO and wp.distance_to(last_p) > 8.0:
			hist.clear()
			mi.set_meta("hold_k", 0.0)
			mi.set_meta("hold_hist", [])
			was_hold = false
		var phys := 0.0
		if last_p != Vector3.ZERO:
			var dt: float = maxf(get_process_delta_time(), 1e-4)
			phys = wp.distance_to(last_p) / dt
		mi.set_meta("last_p", wp)
		var moving: bool = phys >= ARTHUR_TRAIL_V0
		var k: float = clampf((phys - ARTHUR_TRAIL_V0) / maxf(ARTHUR_TRAIL_V1 - ARTHUR_TRAIL_V0, 0.01), 0.0, 1.0)
		if hold or (not moving and hist.size() >= 2):
			if not was_hold and hist.size() >= 2:
				var src: Array = hist.duplicate(true)
				mi.set_meta("hold_hist", src)
				var from_xf: Transform3D
				if mi.has_meta("lamp_xf"):
					from_xf = mi.get_meta("lamp_xf")
				else:
					from_xf = cur_xf
					from_xf.origin = src[src.size() - 1].p
				mi.set_meta("hold_xf", from_xf)
				mi.set_meta("hold_k", k if k > 0.02 else float(mi.get_meta("hold_k") if mi.has_meta("hold_k") else 1.0))
				if float(mi.get_meta("hold_k")) < 0.2:
					mi.set_meta("hold_k", 1.0)
			var fk: float = float(mi.get_meta("hold_k")) if mi.has_meta("hold_k") else 1.0
			if fk < 0.2:
				fk = 1.0
				mi.set_meta("hold_k", fk)
			var frozen: Array = mi.get_meta("hold_hist") if mi.has_meta("hold_hist") else hist
			if frozen.size() >= 2 and mi.has_meta("hold_xf"):
				hist = _arthur_ribbon_follow_lamp(frozen, mi.get_meta("hold_xf"), cur_xf)
			mi.set_meta("holding", true)
			mi.set_meta("hist", hist)
			mi.set_meta("lamp_xf", cur_xf)
			if hist.size() >= 2 and mode == "RACE" and not _parked():
				_arthur_draw_ribbon(mi, hist, fk, cam_p)
			else:
				_arthur_draw_ribbon(mi, [], 0.0, cam_p)
			continue
		if was_hold and hist.size() >= 2:
			var win_r: float = ARTHUR_TRAIL_SEC * maxf(k, 0.35)
			var nh: int = hist.size()
			for i in nh:
				hist[i].t = now - win_r * (1.0 - float(i) / float(max(nh - 1, 1)))
		mi.set_meta("holding", false)
		if mode == "RACE" and not _parked() and car_n.visible and k > 0.02:
			hist.append({"t": now, "p": wp})
		var win: float = ARTHUR_TRAIL_SEC * maxf(k, 0.01)
		var kept: Array = []
		for rec in hist:
			if now - float(rec.t) <= win + 0.02:
				kept.append(rec)
		if kept.size() > 32:
			kept = kept.slice(kept.size() - 32, kept.size())
		mi.set_meta("hist", kept)
		mi.set_meta("hold_k", k)
		mi.set_meta("lamp_xf", cur_xf)
		if not (mode == "RACE" and not _parked()) or k <= 0.02 or kept.size() < 2:
			_arthur_draw_ribbon(mi, [], 0.0, cam_p)
		else:
			_arthur_draw_ribbon(mi, kept, k, cam_p)

func _arthur_draw_ribbon(mi: MeshInstance3D, hist: Array, k: float, cam_p: Vector3) -> void:
	var mesh := mi.mesh as ImmediateMesh
	if mesh == null:
		mesh = ImmediateMesh.new()
		mi.mesh = mesh
	mesh.clear_surfaces()
	if hist.size() < 2 or k <= 0.0:
		return
	mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	var n: int = hist.size()
	var head_cut := 0.10
	for i in n:
		var p: Vector3 = hist[i].p
		var t: float = 0.0 if n <= 1 else float(i) / float(n - 1)
		if t > 1.0 - head_cut and i == n - 1 and n >= 3:
			var back: Vector3 = hist[n - 2].p
			p = p.lerp(back, 0.35)
			t = 1.0 - head_cut
		var prev: Vector3 = hist[i].p if i == 0 else hist[i - 1].p
		var nxt: Vector3 = hist[i].p if i == n - 1 else hist[i + 1].p
		var tang: Vector3 = nxt - prev
		if tang.length_squared() < 1e-8:
			tang = Vector3(0, 0, -1)
		else:
			tang = tang.normalized()
		var view: Vector3 = cam_p - p
		var side: Vector3 = tang.cross(view)
		if side.length_squared() < 1e-8:
			side = tang.cross(Vector3.UP)
		if side.length_squared() < 1e-8:
			side = Vector3.RIGHT
		side = side.normalized()
		var w: float = lerpf(ARTHUR_TRAIL_W1, ARTHUR_TRAIL_W0, t)
		var fade: float = pow(t, 2.6) * ARTHUR_TRAIL_PEAK * (0.7 + 0.3 * k)
		var col := Color(1.0, 0.14, 0.09, fade)
		mesh.surface_set_color(col)
		mesh.surface_add_vertex(p + side * w * 0.5)
		mesh.surface_set_color(col)
		mesh.surface_add_vertex(p - side * w * 0.5)
	mesh.surface_end()

func _arthur_apply_vertex_lit() -> void:
	_arthur_lamps_all = _arthur_collect_lamp_records()
	var hidden: int = _arthur_hide_pool_decals($WorldVP)
	_arthur_lit_mats.clear()
	var map := {
		"res://shaders/scroll.gdshader": load("res://shaders/scroll_vertex_lit.gdshader"),
		"res://shaders/env.gdshader": load("res://shaders/env_vertex_lit.gdshader"),
		"res://shaders/chevron.gdshader": load("res://shaders/chevron_vertex_lit.gdshader"),
		"res://shaders/car.gdshader": load("res://shaders/car_vertex_lit.gdshader"),
	}
	var n_swap := [0]
	_arthur_swap_lit($WorldVP, map, n_swap)
	var nearest: Array = _arthur_nearest_lamps(cam_pos if cam != null else Vector3.ZERO, _arthur_lamps_all, 16)
	_arthur_push_lamp_uniforms(nearest)
	print("VERTEX_LIT lamps=", _arthur_lamps_all.size(), " nearest=", nearest.size(), " swapped=", n_swap[0], " mats=", _arthur_lit_mats.size(), " pools_hidden=", hidden, " moon_k=", _arthur_moon_k(), " ambient_k=", _arthur_ambient_k())

func _arthur_collect_lamp_records() -> Array:
	var raw: Array = []
	_arthur_walk_lamps($WorldVP, raw, false)
	var kept: Array = []
	for rec in raw:
		var hit := false
		for q in kept:
			if rec.pos.distance_to(q.pos) < 1.2:
				q.lot = q.lot or rec.lot
				hit = true
				break
		if not hit:
			kept.append({"pos": rec.pos, "lot": rec.lot})
	return kept

func _arthur_lamp_head(mi: MeshInstance3D) -> Vector3:
	return mi.global_transform * mi.get_aabb().get_center()

func _arthur_walk_lamps(n: Node, raw: Array, in_lot: bool) -> void:
	var lot: bool = in_lot or String(n.name) == "TurnoutLot"
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		var nm := String(mi.name).to_lower()
		if "pool" not in nm:
			var sh: Shader = null
			if mi.material_override is ShaderMaterial:
				sh = (mi.material_override as ShaderMaterial).shader
			if (sh != null and sh.resource_path.ends_with("glow.gdshader")) or "glow" in nm:
				raw.append({"pos": _arthur_lamp_head(mi), "lot": lot})
	for ch in n.get_children():
		_arthur_walk_lamps(ch, raw, lot)

func _arthur_hide_pool_decals(n: Node) -> int:
	var n_hide := 0
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		var nm := String(mi.name).to_lower()
		var hide := "pool" in nm
		if not hide and mi.mesh is PlaneMesh and absf(mi.position.y) < 0.3:
			var par := mi.get_parent()
			var pn := ""
			while par != null:
				pn += " " + String(par.name).to_lower()
				par = par.get_parent()
			if "car" in pn:
				hide = false
			elif "lamp" in pn or ("dressing" in pn and "glow" in nm):
				hide = true
		if hide and mi.visible:
			mi.visible = false
			n_hide += 1
	for ch in n.get_children():
		n_hide += _arthur_hide_pool_decals(ch)
	return n_hide

func _arthur_swap_lit(n: Node, map: Dictionary, n_swap: Array) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.material_override is ShaderMaterial:
			_arthur_lit_one(mi.material_override, map, n_swap, mi)
		if mi.mesh != null:
			for si in mi.mesh.get_surface_count():
				var ov = mi.get_surface_override_material(si)
				if ov is ShaderMaterial:
					_arthur_lit_one(ov, map, n_swap, mi)
				var act = mi.get_active_material(si)
				if act is ShaderMaterial and act != mi.material_override and act != ov:
					_arthur_lit_one(act, map, n_swap, mi)
	for ch in n.get_children():
		_arthur_swap_lit(ch, map, n_swap)

func _arthur_lit_one(m: ShaderMaterial, map: Dictionary, n_swap: Array, mi: MeshInstance3D) -> void:
	if m.shader == null:
		return
	var path := m.shader.resource_path
	if map.has(path):
		m.shader = map[path]
		n_swap[0] += 1
		path = m.shader.resource_path
	elif not path.ends_with("_vertex_lit.gdshader"):
		return
	if m not in _arthur_lit_mats:
		_arthur_lit_mats.append(m)
	# static material flags (uniforms that do not depend on the nearest-16 set)
	var nm := String(mi.name).to_lower()
	var matn := ""
	if mi.mesh != null and mi.mesh.get_surface_count() > 0:
		var sm0 = mi.mesh.surface_get_material(0)
		if sm0 != null:
			matn = String(sm0.resource_name).to_lower()
	var soft := float(m.get_shader_parameter("soft_surface") or 0.0)
	var roadish := soft > 0.5 or "road" in nm or "asphalt" in nm or "road" in matn or "asphalt" in matn
	var paint := path.ends_with("chevron_vertex_lit.gdshader") or path.ends_with("chevron.gdshader")
	m.set_shader_parameter("unbake", 0.85 if roadish and not paint else 0.0)
	m.set_shader_parameter("light_mix", 0.70 if paint else 1.0)
	var emit := "emit" in matn or matn.begins_with("emit_") or "glow" in nm or "glow" in matn
	m.set_shader_parameter("live_light", 0.0 if emit else 1.0)
	m.set_shader_parameter("lamp_color", _arthur_sodium_col())
	m.set_shader_parameter("mercury_color", _arthur_mercury_col())
	m.set_shader_parameter("lamp_intensity", 1.05)
	m.set_shader_parameter("lamp_range", 16.0)
	m.set_shader_parameter("ambient_col", Vector3(0.333333, 0.458824, 0.627451))
	m.set_shader_parameter("ambient_k", _arthur_ambient_k())
	m.set_shader_parameter("moon_dir", _arthur_moon_dir())
	m.set_shader_parameter("moon_color", Vector3(0.561, 0.659, 0.847))  # #8FA8D8
	m.set_shader_parameter("moon_k", _arthur_moon_k())

func _arthur_nearest_lamps(origin: Vector3, all: Array, cap: int = 16) -> Array:
	if all.size() <= cap:
		return all
	var scored: Array = []
	for rec in all:
		scored.append({"pos": rec.pos, "lot": rec.lot, "d": rec.pos.distance_squared_to(origin)})
	scored.sort_custom(func(a, b): return a.d < b.d)
	return scored.slice(0, cap)

func _arthur_push_lamp_uniforms(lamps: Array) -> void:
	for m in _arthur_lit_mats:
		if m == null:
			continue
		for bi in 4:
			var proj := Projection()
			for ci in 4:
				var i: int = bi * 4 + ci
				var p := Vector3(0, -999, 0)
				if i < lamps.size():
					p = lamps[i].pos
				proj[ci] = Vector4(p.x, p.y, p.z, 0.0)  # w=0 sodium
			m.set_shader_parameter("lamps%d" % bi, proj)
		m.set_shader_parameter("lamp_count", float(lamps.size()))

func _arthur_push_nearest_lamps() -> void:
	if _arthur_lit_mats.is_empty():
		return
	if _arthur_lamps_all.is_empty():
		return
	var origin: Vector3 = cam.global_position if cam != null else cam_pos
	_arthur_push_lamp_uniforms(_arthur_nearest_lamps(origin, _arthur_lamps_all, 16))

func _arthur_load_png(res_path: String) -> Texture2D:
	# Prefer the imported texture (the only form in web/mobile exports); fall back to raw Image.load.
	if ResourceLoader.exists(res_path):
		var t = load(res_path)
		if t is Texture2D:
			return t
	var img := Image.new()
	var err := img.load(ProjectSettings.globalize_path(res_path))
	if err != OK:
		push_error("arthur png load failed %s err=%s" % [res_path, str(err)])
		return null
	return ImageTexture.create_from_image(img)

func _arthur_apply_flares() -> void:
	var tex: Texture2D = _arthur_load_png("res://assets/tex/flare_64.png")
	if tex == null:
		push_error("flare texture missing")
		return
	var fog := Vector2(9.0, 78.0)
	if DIST != null and DIST.has("touge"):
		fog = Vector2(float(DIST.touge.fog_near), float(DIST.touge.fog_far))
	var root := $WorldVP.get_node_or_null("ArthurFlares")
	if root == null:
		root = Node3D.new(); root.name = "ArthurFlares"; $WorldVP.add_child(root)
	var n_lamp := 0
	var lamps: Array = _arthur_lamps_all if not _arthur_lamps_all.is_empty() else _arthur_collect_lamp_records()
	var sod := Color(_arthur_sodium_col().x, _arthur_sodium_col().y, _arthur_sodium_col().z)
	for rec in lamps:
		var f := _arthur_make_flare(tex, sod, Vector2(6.5, 3.4), 0.52, Vector3(0, 0, 1), 0.0, fog)
		f.name = "ArthurFlareLamp%d" % n_lamp
		root.add_child(f)
		f.global_position = rec.pos
		n_lamp += 1
	var n_car := [0]
	for car in [player_car, rival_car]:
		if car != null:
			_arthur_add_car_flares(car, tex, fog, n_car)
	print("FLARES lamps=", n_lamp, " car_lights=", n_car[0], " fog=", fog)

func _arthur_make_flare(tex: Texture2D, col: Color, size: Vector2, strength: float, fwd: Vector3, facing: float, fog: Vector2) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new(); q.size = Vector2(1, 1)
	mi.mesh = q
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/flare.gdshader")
	m.set_shader_parameter("tex", tex)
	m.set_shader_parameter("color", Vector3(col.r, col.g, col.b))
	m.set_shader_parameter("size", size)
	m.set_shader_parameter("strength", strength)
	m.set_shader_parameter("local_forward", fwd)
	m.set_shader_parameter("facing_k", facing)
	m.set_shader_parameter("fog_near", fog.x)
	m.set_shader_parameter("fog_far", fog.y)
	m.set_shader_parameter("snap_res", Vector2(320.0, 240.0))
	m.render_priority = 7
	mi.material_override = m
	mi.layers = 3
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.extra_cull_margin = 16384.0
	return mi

func _arthur_add_car_flares(car: Node3D, tex: Texture2D, fog: Vector2, n: Array) -> void:
	var heads: Array = []
	var tails: Array = []
	_arthur_find_car_lights(car, car, heads, tails)
	if heads.is_empty():
		for x in [-0.58, 0.58]:
			heads.append(Vector3(x, 0.66, 2.08))
	if tails.is_empty():
		for x in [-0.58, 0.58]:
			tails.append(Vector3(x, 0.80, -2.06))
	var hw := Color(1.0, 0.92, 0.78)
	var rd := Color(0.95, 0.16, 0.12)
	for lp in heads:
		var f := _arthur_make_flare(tex, hw, Vector2(2.6, 1.25), 0.74, Vector3(0, 0, 1), 1.0, fog)
		f.name = "ArthurFlareHead"
		car.add_child(f)
		f.position = lp
		n[0] += 1
	for lp in tails:
		var f := _arthur_make_flare(tex, rd, Vector2(2.0, 1.05), 0.70, Vector3(0, 0, -1), 1.0, fog)
		f.name = "ArthurFlareTail"
		car.add_child(f)
		f.position = lp
		n[0] += 1

func _arthur_find_car_lights(n: Node, car: Node3D, heads: Array, tails: Array) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		var nm := String(mi.name).to_lower()
		if "arthurflare" in nm:
			pass
		else:
			var sh: Shader = null
			if mi.material_override is ShaderMaterial:
				sh = (mi.material_override as ShaderMaterial).shader
			var path := sh.resource_path if sh != null else ""
			var is_glow := "glow" in nm or "fx_lamp" in nm or "fx_head" in nm or path.ends_with("glow.gdshader") or path.ends_with("fx.gdshader")
			if is_glow:
				var wp: Vector3 = mi.global_transform * mi.get_aabb().get_center()
				var lp: Vector3 = car.to_local(wp)
				var bucket: Array = tails if ("tail" in nm or lp.z < -0.2) else heads
				var hit := false
				for q in bucket:
					if lp.distance_to(q) < 0.35:
						hit = true
						break
				if not hit:
					bucket.append(lp)
	for ch in n.get_children():
		_arthur_find_car_lights(ch, car, heads, tails)
