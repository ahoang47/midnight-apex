## Headless race: godot --headless --path godot --script res://scripts/headless_run.gd -- <inputs.json> [--out f.json] [--load token_file] [--dump-after N --dump-to f]
## Per corner inputs: "pick": hand indices (fewer than 3 = timer auto-fill), "qte": [entry, apex, exit] raw scores in [0, 1],
## each null (unplayed = 0), a JSON number, or "0x<16 hex>" IEEE-754 bits (exact; Godot's decimal parser is not correctly rounded).
## --qte-fn-test <grid.json> --out f: evaluate erf / expected_hit_quality / qte_zone_width / raw_qte_score on a grid (tools/qte_fn_test.py).
extends SceneTree
const RaceCore = preload("res://scripts/race_core.gd")
const C = preload("res://scripts/sim_constants.gd")
const Combat = preload("res://scripts/combat.gd")

static func phases_of(inp: Dictionary) -> Array:
	var q := []
	for v in inp.qte: q.append(RaceCore.fdec(v))
	return q

func _opt(args: PackedStringArray, k: String, def = null):
	var i := args.find(k)
	return args[i + 1] if i >= 0 and i + 1 < args.size() else def

func _bits_check() -> int:
	var bad := 0
	for path in C.FLOAT_BITS.keys():
		var parts := []
		for p in path.replace("]", "").split("["): parts.append(p)
		var v = C.ALL[parts[0]]
		for j in range(1, parts.size()):
			v = v[int(parts[j])] if v is Array else (v[int(parts[j])] if v.has(int(parts[j])) and not v.has(parts[j]) else v[parts[j]])
		var b := PackedByteArray(); b.resize(8); b.encode_double(0, float(v))
		if b.decode_s64(0) != int(C.FLOAT_BITS[path]): bad += 1; printerr("bit mismatch ", path)
	return bad

func _run_one(cfg: Dictionary, inputs: Dictionary, load_tok, dump_after, dump_to) -> Dictionary:
	var core = RaceCore.new()
	if load_tok != null: core.load_state(cfg, RaceCore.decode_token(load_tok))
	else: core.setup(cfg, int(inputs.seed))
	var tokens := []
	while core.phase != "FINISHED":
		var inp: Dictionary = inputs.corners[core.corner_index]
		if core.phase == "SELECT":
			for i in inp.get("pick", []): core.pick(int(i))
			core.lock()
			tokens.append({"at": "lock%d" % core.corner_index, "token": RaceCore.encode_token(core.dump())})
		elif core.phase == "TIMING":
			core.submit_qte(phases_of(inp))
		elif core.phase == "RESULT":
			tokens.append({"at": "result%d" % core.corner_index, "token": RaceCore.encode_token(core.dump())})
			if dump_after != null and int(dump_after) == core.corner_index:
				FileAccess.open(dump_to, FileAccess.WRITE).store_string(RaceCore.encode_token(core.dump()))
				return {"dumped": dump_to}
			core.next()
	return {"engine": "godot-4.6.3(headless)", "commit": C.PIN_COMMIT, "seed": core.seed_value, "build": RaceCore.build_info().build, "zone_width": core.zone_width(),
		"corners": core.history, "player_total": core.cum_p, "opponent_total": core.cum_o, "winner": core.winner(),
		"rng_draws": core.rng.draws, "tokens": tokens}

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var cfg_path: String = _opt(args, "--config", ProjectSettings.globalize_path("res://").path_join("../spec/race_config.json"))
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(cfg_path))
	if _opt(args, "--qte-fn-test") != null:
		_qte_fn_test(_opt(args, "--qte-fn-test"), _opt(args, "--out")); quit(0); return
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
