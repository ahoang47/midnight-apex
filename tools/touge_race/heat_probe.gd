## TOUGE debug probe (Gordon): print the player's heat gauges per turn in the scripted race (fill, load, cap, locked).
extends SceneTree
const RaceCore = preload("res://scripts/race_core.gd")
func _init() -> void:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://spec/race_config.json"))
	var inp: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://spec/touge_playtest.json"))
	cfg.player.car = inp.player_car; cfg.opponent.car = inp.opp_car
	var core = RaceCore.new(); core.setup(cfg, int(inp.seed), String(inp.role))
	print("CAP ", core.p_heat.cap, " REC ", core.p_heat.rec, " REL ", core.p_heat.release)
	while core.phase != "FINISHED":
		var c: Dictionary = inp.corners[core.corner_index]
		if core.phase == "SELECT":
			for ch in String(c.pick):
				var i: int = core.first_free(ch)
				if not core.pick(i): core.pick(core.first_free(core.allowed()[0]))
			print("T%d proj fill %s" % [core.corner_index + 1, str(core.projected().fill())])
			core.lock()
		elif core.phase == "TIMING": core.submit_qte(c.qte)
		elif core.phase == "RESULT":
			print("T%d %s line=%s load=%s fill=%s locked=%s" % [core.corner_index + 1, core.corner().corner, core.result.player_line, str(core.p_heat.load), str(core.p_heat.fill()), str(core.p_heat.locked)])
			core.next()
	quit()
