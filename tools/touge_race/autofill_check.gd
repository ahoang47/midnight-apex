## TOUGE check (Austin t121 item 8): timer-expiry auto-fill is random but seeded from race seed + turn, on its own RNG.
## Runs whole races where the player never picks (every turn auto-filled): two cores with the same seed must give the same
## lines; the sim rng draw count must equal a run where the same picks are made by hand (the auto-fill never touches the sim rng);
## different seeds should give different fills. Usage: godot --headless --path . -s tools/touge_race/autofill_check.gd
extends SceneTree
const RaceCore = preload("res://scripts/race_core.gd")
func _race(cfg: Dictionary, seed_v: int, forced = null) -> Dictionary:
	var core = RaceCore.new(); core.setup(cfg, seed_v)
	var lines := []; var k := 0
	while core.phase != "FINISHED":
		if core.phase == "SELECT":
			if forced != null:
				for i in forced[k]: core.pick(i)
			core.lock(); lines.append(core.picks.duplicate()); k += 1
		elif core.phase == "TIMING": core.submit_qte([0.8, 0.8, 0.8])
		elif core.phase == "RESULT": core.next()
	return {"lines": lines, "draws": core.rng.draws, "auto": core.autofilled}
func _init() -> void:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://spec/race_config.json"))
	var bad := 0; var diff := 0
	for sd in [1, 7, 42, 1234, 99991]:
		var a := _race(cfg, sd); var b := _race(cfg, sd); var h := _race(cfg, sd, a.lines)
		if a.lines != b.lines: bad += 1; print("seed %d: auto-fill not reproducible" % sd)
		if a.draws != h.draws: bad += 1; print("seed %d: sim rng draws differ auto %d vs hand %d" % [sd, a.draws, h.draws])
		var c := _race(cfg, sd + 1)
		if c.lines != a.lines: diff += 1
		print("seed %d lines %s draws %d" % [sd, str(a.lines), a.draws])
	print("AUTOFILL_CHECK %s reproducible+sim-rng-untouched bad=%d, seed-sensitive %d/5" % ["PASS" if bad == 0 and diff > 0 else "FAIL", bad, diff])
	quit()
