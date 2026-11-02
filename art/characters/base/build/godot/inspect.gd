extends SceneTree
func _init():
	for f in ["res://char_base_m.glb", "res://char_base_f.glb"]:
		var n: Node = load(f).instantiate()
		var sk: Skeleton3D = n.find_children("*", "Skeleton3D", true, false)[0]
		var names := []
		for i in sk.get_bone_count(): names.append(sk.get_bone_name(i))
		print(f, " skeleton=", n.get_path_to(sk), " bones=", sk.get_bone_count(), " ", names)
		for m in n.find_children("*", "MeshInstance3D", true, false):
			var mi := m as MeshInstance3D
			var bs := []
			for b in mi.mesh.get_blend_shape_count(): bs.append(mi.mesh.get_blend_shape_name(b))
			print("   mesh ", mi.name, " surfaces=", mi.mesh.get_surface_count(), " blendshapes=", bs, " skin=", mi.skin != null)
		var ap := n.find_children("*", "AnimationPlayer", true, false)
		if ap.size(): print("   anims ", (ap[0] as AnimationPlayer).get_animation_list())
		n.free()
	quit()
