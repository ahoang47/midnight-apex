## hud.tscn root. The HUD is laid out in 640x480 design units and drawn on a 1280x960 2x pixel grid (Austin 2026-11-11 22:21 PT:
## "Draw HUD text pixel-hard on a 2x grid (1280x960)"; art_direction.md B.5c: UI drawn sharp at 1280x960, no antialiasing,
## 2 px shadow, then whole-number scaling). main.gd puts this scene in a 1280x960 SubViewport at scale 2 and shows it nearest.
## Text is rasterised at size x 2, 1-bit (no antialiasing, no subpixel positioning, no oversampling), so 1 design px = a 2x2
## block for shapes and the 6x9 bitmap font, while glyph edges sit on the 1280x960 grid. The shadow is 1 design px = 2 px.
## Scene refactor (2026-11-12): every panel is its own Control node (scripts/hud/*.gd, all extending hud_panel.gd); this root
## only holds the fonts and the state from main.gd and decides which panels are visible (same draw order as before).
## @tool: in the editor the panels draw a sample state (pick it with editor_preview) so the layout can be seen and inspected.
@tool
extends Control
var font_tex: Texture2D
var fm: Dictionary
var panel: StyleBoxTexture
var logo: Texture2D
var st: Dictionary = {}
var fn: FontFile   # NimbusSansNarrow-Bold, 1-bit
var fi: FontFile   # -BoldOblique

## editor only: which sample state the panels draw
@export_enum("select", "lock", "qte", "play", "result", "finish", "menu") var editor_preview := "select":
	set(v): editor_preview = v; if is_inside_tree() and Engine.is_editor_hint(): _editor_preview()

@onready var P := {
	"mirror": $MirrorFrame, "plate": $CornerPlate, "gap": $GapMeter, "timer": $LineLockTimer, "debug": $DebugHud,
	"select": $LineSelect, "lanes": $LineSelect/Lanes, "entry": $LineSelect/EntryStrip, "plan": $LineSelect/PlanPanel,
	"lock": $LineLockedBanner, "qte": $QtePanel, "lvl": $LineVsLine, "cont": $ContinuePrompt, "finish": $FinishPanel, "menu": $MainMenu}

func setup(font_png: Texture2D, meta: Dictionary, panel_png: Texture2D, logo_png: Texture2D) -> void:
	font_tex = font_png; fm = meta; logo = logo_png
	panel = StyleBoxTexture.new(); panel.texture = panel_png
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]: panel.set_texture_margin(side, 4)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	size = Vector2(640, 480); mouse_filter = Control.MOUSE_FILTER_IGNORE
	fn = _font("res://fonts/NimbusSansNarrow-Bold.otf"); fi = _font("res://fonts/NimbusSansNarrow-BoldOblique.otf")
	for n in P.values():
		if "hud" in n: n.hud = self   # LineSelect is a plain container

const TS := 2   # text raster scale (2x grid)
func _font(p: String) -> FontFile:
	var f: FontFile = (load(p) as FontFile).duplicate()
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE; f.hinting = TextServer.HINTING_NORMAL
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED; f.oversampling = 1.0
	return f

## which panels show for a state (the order of the old single _draw: mirror, plate, gap meter, then per phase)
func show_state(s: Dictionary) -> void:
	st = s
	var on := {}
	if st.is_empty(): pass
	elif st.has("menu"): on.menu = true
	else:
		if st.mirror: on.mirror = true
		on.plate = true; on.gap = true
		if st.phase == "SELECT":
			# Entry lane strip is folded into the combined PlanPanel (Arthur line-preview pass 4, Austin 2026-11-12).
			on.timer = true; on.debug = 64.0; on.select = true; on.plan = true
			if int(st.plate.stop) == 0: on.lanes = true
		elif st.phase == "TIMING" and st.locked_hold:
			on.timer = true; on.debug = 64.0; on.lock = true
		elif st.phase == "TIMING" and st.get("qte") != null:   # shots11: phase QTE during playback, over the B.5a panel
			on.lvl = true; on.debug = 106.0; on.qte = true
		elif st.phase == "TIMING":
			on.lvl = true; on.debug = 106.0
		else:
			on.lvl = true; on.debug = 106.0
			if st.phase == "FINISHED": on.finish = true
			else: on.cont = true
	if on.has("debug"): P.debug.position.y = on.debug
	# Race split / tie-gap bar: top centre, directly under the REAR VIEW label (mirror at y=13-82, label at y=84).
	# Coords from Arthur pass 4; overridable via st.gap_pos (display.json line_preview.gap_pos).
	if P.has("gap") and on.has("gap"):
		var gp = st.get("gap_pos", [220, 98])
		P.gap.position = Vector2(float(gp[0]), float(gp[1]))
	for k in P:
		var n: Control = P[k]
		n.visible = on.has(k)
		if n.visible: n.queue_redraw()

func _ready() -> void:
	if Engine.is_editor_hint(): _editor_preview()

func _editor_preview() -> void:
	setup(load("res://art/font_6x9.png"), JSON.parse_string(FileAccess.get_file_as_string("res://art/font.json")), load("res://art/panel9.png"), load("res://art/logo_v3.png"))
	show_state(_sample(editor_preview))

## editor sample states (display only, never used by the game): corner 1 HP L, hand A A S S D D
func _sample(kind: String) -> Dictionary:
	if kind == "menu":
		return {"menu": {"items": ["START RACE", "SEED", "QUIT"], "sel": 0, "seed_text": "", "blink": false, "commit": "f0efecf build (editor)"}}
	var pts := []
	for i in 25:   # a stand-in hairpin for the plate map: straight, half circle, straight back
		if i < 6: pts.append(Vector2(0.0, -i * 2.0))
		elif i <= 18:
			var a := (i - 6) / 12.0 * PI; pts.append(Vector2(-14.0 + 14.0 * cos(a), -12.0 - 14.0 * sin(a)))
		else: pts.append(Vector2(-28.0, -12.0 + (i - 18) * 2.0))
	var plate := {"name": "HAIRPIN L", "icon": {"pts": pts, "stops": [pts[4], pts[12], pts[21]]}, "mode": "VIEW", "stop": 0, "done": 0}
	var s := {"phase": "SELECT", "title": "CORNER 1/2 TOUGE HP (L)", "sub": "seed 3 f0efecf BCH 25m/s", "build": "editor", "lead": -0.05, "gap": -0.05,
		"left": 8.4, "total": 12.0, "slots": [null, null, null], "hand": ["P", "P", "H", "H", "E", "E"], "used": [],
		"qte": null, "line": "", "rline": "", "outs": [], "plate": plate, "locked_hold": false, "mirror": true, "play_phase": 0,
		"plan": {"phase": 0, "sel": 0, "avail": {"P": 2, "H": 2, "E": 2}, "avail_entry": {"P": 2, "H": 2, "E": 2}, "entry": ""},
		"turn_m": 60.0, "dir": "L", "lanes": {"P": Vector2(372, 300), "H": Vector2(320, 300), "E": Vector2(268, 300)},
		"result": {}, "reveal": 0, "cont_left": 8.0, "leader_changed": false, "winner": "", "cum_p": 0.0, "cum_o": 0.0, "last_corner": false, "fin": null}
	match kind:
		"lock":
			s.phase = "TIMING"; s.locked_hold = true; s.line = "ASD"; s.plate.mode = "LOCK"
		"qte":
			s.phase = "TIMING"; s.mirror = false; s.line = "ASD"; s.rline = "SDA"; s.outs = [1, -1, 0]; s.play_phase = 1; s.plate.mode = "QTE"; s.plate.stop = 1
			s.qte = {"i": 1, "seg": "sweep", "ms": 900.0, "zone": [700.0, 1500.0], "zone_w": 1.0, "bar_ms": 1700.0, "res": [0.92, null, null],
				"press": [1068.0, null, null], "line": "ASD", "key": "SPACE", "t_left": 0.8, "t_total": 1.7}
		"play":
			s.phase = "TIMING"; s.mirror = false; s.line = "ASD"; s.rline = "SDA"; s.outs = [1, -1, 0]; s.play_phase = 1; s.plate.mode = "PLAY"; s.plate.stop = 1
		"result", "finish":
			s.phase = "RESULT" if kind == "result" else "FINISHED"; s.mirror = kind == "finish"; s.line = "ASD"; s.rline = "SDA"; s.outs = [1, -1, 0]; s.plate.mode = "DONE"
			s.result = {"qte_in": [0.92, null, 0.55], "q_time": 0.49, "autofilled": false}; s.reveal = 3; s.cont_left = 7.2
			if kind == "finish": s.winner = "Player"; s.cum_p = 0.61; s.cum_o = 0.39; s.fin = {"items": ["RESTART SAME SEED", "NEW RACE", "MAIN MENU"], "sel": 0}
	return s
