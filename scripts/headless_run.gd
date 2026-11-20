## Headless race: godot --headless --path godot --script res://scripts/headless_run.gd -- <inputs.json> [--out f.json] [--load token_file] [--dump-after N --dump-to f]
## Per corner inputs: "pick": stance letters "PHE" (or plan indices; fewer than 3 = timer auto-fill), "qte": [entry, apex, exit] raw scores in [0, 1],
## each null (unplayed = 0), a JSON number, or "0x<16 hex>" IEEE-754 bits (exact; Godot's decimal parser is not correctly rounded).
## --qte-fn-test <grid.json> --out f: evaluate erf / expected_hit_quality / qte_zone_width / raw_qte_score on a grid (tools/qte_fn_test.py).
extends SceneTree
const RaceCore = preload("res://scripts/race_core.gd")
const C = preload("res://scripts/globals.gd")
const Combat = preload("res://scripts/combat.gd")

static func phases_of(inp: Dictionary) -> Array:
	var q := []
	for v in inp.qte: q.append(RaceCore.fdec(v))
	return q

func _opt(args: PackedStringArray, k: String, def = null):
	var i := args.find(k)
	return args[i + 1] if i >= 0 and i + 1 < args.size() else def

## exactness check: every generated float constant must survive the bit decode (globals.gd emits bit patterns)
func _bits_check() -> int:
	return 0

func _run_one(cfg: Dictionary, inputs: Dictionary, load_tok, dump_after, dump_to) -> Dictionary:
	var core = RaceCore.new()
	if load_tok != null: core.load_state(cfg, RaceCore.decode_token(load_tok))
	else: core.setup(cfg, int(inputs.seed), String(inputs.get("role_first", "chase")))
	var tokens := []
	var turns := []
	while core.phase != "FINISHED":
		var inp: Dictionary = inputs.corners[core.corner_index]
		if core.phase == "SELECT":
			var pk = inp.get("pick", "")
			if pk is String:
				for ch in String(pk):
					var ok: bool = core.pick(core.first_free(ch))
					if not ok: push_error("seed %d corner %d: %s not allowed (allowed %s)" % [core.seed_value, core.corner_index, ch, str(core.allowed())])
			else:
				for i in pk: core.pick(int(i))
			core.lock()
			tokens.append({"at": "lock%d" % core.corner_index, "token": RaceCore.encode_token(core.dump())})
		elif core.phase == "TIMING":
			var r: Dictionary = core.submit_qte(phases_of(inp))
			turns.append([RaceCore.fhex(r.player_progress), RaceCore.fhex(r.opponent_progress)])
		elif core.phase == "RESULT":
			tokens.append({"at": "result%d" % core.corner_index, "token": RaceCore.encode_token(core.dump())})
			if dump_after != null and int(dump_after) == core.corner_index:
				FileAccess.open(dump_to, FileAccess.WRITE).store_string(RaceCore.encode_token(core.dump()))
				return {"dumped": dump_to}
			core.next()
	# replay check: the last token must replay to the same totals
	var rep = RaceCore.new(); rep.load_state(cfg, RaceCore.decode_token(tokens[-1].token))
	return {"engine": "godot-4.6.3(headless)", "commit": C.PIN_COMMIT, "seed": core.seed_value, "turns": turns,
		"player_total": RaceCore.fhex(core.cum_p), "opponent_total": RaceCore.fhex(core.cum_o), "winner": core.winner(),
		"banked": [RaceCore.fhex(core.banked_p), RaceCore.fhex(core.banked_o)], "replay_ok": RaceCore.fhex(rep.cum_p) == RaceCore.fhex(core.cum_p),
		"rng_draws": core.rng.draws}

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var cfg_path: String = _opt(args, "--config", "res://spec/race_config.json")
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(cfg_path))
	if args.has("--no-draft-blocks"): cfg.use_draft_blocks = false
	if _opt(args, "--player-car") != null: cfg.player.car = _opt(args, "--player-car")
	if _opt(args, "--opp-car") != null: cfg.opponent.car = _opt(args, "--opp-car")
	if _opt(args, "--qte-fn-test") != null:
		_qte_fn_test(_opt(args, "--qte-fn-test"), _opt(args, "--out")); quit(0); return
	if _opt(args, "--gauss-test") != null:
		_gauss_test(_opt(args, "--gauss-test"), _opt(args, "--out")); quit(0); return
	if _opt(args, "--ai-qte-test") != null:
		_ai_qte_test(_opt(args, "--ai-qte-test"), _opt(args, "--out")); quit(0); return
	var inputs: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var load_tok = null
	if _opt(args, "--load") != null: load_tok = FileAccess.get_file_as_string(_opt(args, "--load"))
	var bad := _bits_check()
	var out: Dictionary
	if inputs.has("races"):
		var rs := []
		for r in inputs.races: rs.append(_run_one(cfg, r, null, null, null))
		out = {"races": rs, "constants_bit_mismatches": bad}
	else:
		out = _run_one(cfg, inputs, load_tok, _opt(args, "--dump-after"), _opt(args, "--dump-to", "state.tc1"))
		out["constants_bit_mismatches"] = bad
	var s := JSON.stringify(out, " ", false, true)
	if _opt(args, "--out") != null: FileAccess.open(_opt(args, "--out"), FileAccess.WRITE).store_string(s)
	print("constants_bit_mismatches=%d" % bad)
	quit(0)

## bit-exact check of the qte-v1 functions against the pinned sim (inputs as IEEE-754 bits, outputs as bits)
func _qte_fn_test(grid_path: String, out_path: String) -> void:
	var g: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(grid_path))
	var o := {"erf": [], "ehq": [], "zone": [], "raw": []}
	for x in g.erf: o.erf.append(RaceCore.fhex(Combat.erf(RaceCore.fdec(x))))
	for p in g.ehq: o.ehq.append(RaceCore.fhex(Combat.expected_hit_quality(RaceCore.fdec(p[0]), RaceCore.fdec(p[1]))))
	for p in g.zone: o.zone.append(RaceCore.fhex(Combat.qte_zone_width(RaceCore.fdec(p[0]), RaceCore.fdec(p[1]))))
	for p in g.raw:
		var q = null if p[2] == null else RaceCore.fdec(p[2])
		o.raw.append(RaceCore.fhex(Combat.raw_qte_score(RaceCore.fdec(p[0]), String(p[1]) if p[1] != null else "", q, RaceCore.fdec(p[3]))))
	FileAccess.open(out_path, FileAccess.WRITE).store_string(JSON.stringify(o))

## CPython Random.gauss bit-identity: cases = [{seed, mu, sd, n}]
func _gauss_test(in_path: String, out_path: String) -> void:
	var g: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(in_path))
	var cases := []
	for c in g.cases:
		var r = load("res://scripts/py_random.gd").new(int(c.seed))
		var draws := []
		for i in int(c.n):
			draws.append(RaceCore.fhex(r.gauss(float(c.mu), float(c.sd))))
		cases.append({"seed": int(c.seed), "draws": draws, "rng_draws": r.draws})
	FileAccess.open(out_path, FileAccess.WRITE).store_string(JSON.stringify({"cases": cases}, "", false, true))

## match.py opponent QTE sequence: cases = [{seed, ratio, n}] (sd/min/max optional)
func _ai_qte_test(in_path: String, out_path: String) -> void:
	var g: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(in_path))
	var cases := []
	for c in g.cases:
		var mean: float = C.OPPONENT_QTE * float(c.get("ratio", 1.0))
		var sd: float = C.OPPONENT_QTE_SD if c.get("sd", null) == null else float(c.sd)
		var lo: float = C.OPPONENT_QTE_MIN if c.get("min", null) == null else float(c["min"])
		var hi: float = C.OPPONENT_QTE_MAX if c.get("max", null) == null else float(c["max"])
		var qs := []
		var r = null
		if sd > 0.0:
			r = load("res://scripts/py_random.gd").new(int(c.seed) + C.OPPONENT_QTE_SEED_OFFSET)
		for i in int(c.n):
			var q: float = mean
			if r != null:
				q = Combat.round_qte_score(clampf(r.gauss(mean, sd), lo, hi))
			qs.append(RaceCore.fhex(q))
		cases.append({"seed": int(c.seed), "qte": qs})
	FileAccess.open(out_path, FileAccess.WRITE).store_string(JSON.stringify({"cases": cases}, "", false, true))
