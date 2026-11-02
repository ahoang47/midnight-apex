extends SceneTree
# Builds res://humanoid_bonemap.tres (SkeletonProfileHumanoid <- Mixamo names) and checks every REQUIRED
# profile bone is mapped to a bone that exists in each imported skeleton.
const TABLE := {"Hips": "Hips", "Spine": "Spine", "Chest": "Spine1", "UpperChest": "Spine2", "Neck": "Neck", "Head": "Head",
	"LeftShoulder": "LeftShoulder", "LeftUpperArm": "LeftArm", "LeftLowerArm": "LeftForeArm", "LeftHand": "LeftHand",
	"RightShoulder": "RightShoulder", "RightUpperArm": "RightArm", "RightLowerArm": "RightForeArm", "RightHand": "RightHand",
	"LeftUpperLeg": "LeftUpLeg", "LeftLowerLeg": "LeftLeg", "LeftFoot": "LeftFoot", "LeftToes": "LeftToeBase",
	"RightUpperLeg": "RightUpLeg", "RightLowerLeg": "RightLeg", "RightFoot": "RightFoot", "RightToes": "RightToeBase"}
func _init():
	var prof := SkeletonProfileHumanoid.new()
	var bm := BoneMap.new(); bm.profile = prof
	for k in TABLE: bm.set_skeleton_bone_name(k, "mixamorig_" + TABLE[k])
	print("save bonemap: ", ResourceSaver.save(bm, "res://humanoid_bonemap.tres"))
	for f in ["res://char_base_m.glb", "res://char_base_f.glb"]:
		var n: Node = load(f).instantiate()
		var sk: Skeleton3D = n.find_children("*", "Skeleton3D", true, false)[0]
		var req := 0; var missing := []; var opt_unmapped := []
		for i in prof.bone_size:
			var pn := prof.get_bone_name(i); var sn := bm.get_skeleton_bone_name(pn)
			var ok := sn != StringName() and sk.find_bone(sn) >= 0
			if prof.is_required(i):
				req += 1
				if not ok: missing.append(pn)
			elif not ok: opt_unmapped.append(pn)
		print("%s  required=%d  UNMAPPED_REQUIRED=%s  optional_unmapped=%d %s" % [f, req, str(missing), opt_unmapped.size(), str(opt_unmapped)])
		n.free()
	quit()
