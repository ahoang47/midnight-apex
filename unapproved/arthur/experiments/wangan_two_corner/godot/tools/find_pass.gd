## WANGAN playtest helper (display-side search, never changes the sim): find scripted inputs where the order flips on BOTH
## corners (player passes in corner 1, the rival takes it back in corner 2), so the playtest shows both pass animations
## like the touge run did. Runs the real RaceCore. Usage:
##   godot --headless --path godot --script res://tools/find_pass.gd -- [seed0 seed1]
extends SceneTree
const RaceCore = preload("res://scripts/race_core.gd")
func _perms(n: int) -> Array:
	var out := []
	for a in n:
		for b in n:
			for c in n:
				if a != b and b != c and a != c: out.append([a, b, c])
	return out
func _init() -> void:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://spec/race_config.json"))
	var a := OS.get_cmdline_user_args(); var s0 := int(a[0]) if a.size() > 0 else 1; var s1 := int(a[1]) if a.size() > 1 else 60
	var Q1 := [0.8, 0.8, 0.8]; var Q2 := [0.3, 0.3, 0.3]
	for sd in range(s0, s1 + 1):
		var found := false
		for p1 in _perms(6):
			if found: break
			var core = RaceCore.new(); core.setup(cfg, sd)
			for i in p1: core.pick(i)
			core.lock(); core.submit_qte(Q1)
			if core.lead() <= 0.0: continue
			core.next()
			for p2 in _perms(6):
				var c2 = RaceCore.new(); c2.setup(cfg, sd)
				for i in p1: c2.pick(i)
				c2.lock(); c2.submit_qte(Q1); c2.next()
				for i in p2: c2.pick(i)
				c2.lock(); c2.submit_qte(Q2)
				if c2.lead() < 0.0:
					print("PASS_BOTH seed %d c1 %s (%s vs %s) c2 %s (%s vs %s) lead1 %.3f lead2 %.3f" % [sd, str(p1), core.history[0].player_line, core.history[0].line, str(p2), c2.history[1].player_line, c2.history[1].line, core.history[0].cum_player - core.history[0].cum_opponent, c2.lead()])
					found = true; break
	quit(0)
