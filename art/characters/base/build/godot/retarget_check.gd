extends SceneTree
func _init():
	var prof := SkeletonProfileHumanoid.new()
	for f in ["res://char_base_m.glb", "res://char_base_f.glb"]:
		var n: Node = load(f).instantiate()
		var sk: Skeleton3D = n.find_children("*", "Skeleton3D", true, false)[0]
		var names := []; for i in sk.get_bone_count(): names.append(String(sk.get_bone_name(i)))
		var missing := []
		for i in prof.bone_size:
			if prof.is_required(i) and sk.find_bone(prof.get_bone_name(i)) < 0: missing.append(prof.get_bone_name(i))
		var ap: AnimationPlayer = n.find_children("*", "AnimationPlayer", true, false)[0]
		var a: Animation = ap.get_animation("deform_test")
		var tracks := []; for t in a.get_track_count(): tracks.append(String(a.track_get_path(t)))
		print("%s  skeleton=%s  bones=%s" % [f, str(n.get_path_to(sk)), str(names)])
		print("   required profile bones missing after retarget: %s" % str(missing))
		print("   deform_test tracks (retargeted): %s" % str(tracks.slice(0, 6)))
		n.free()
	quit()
