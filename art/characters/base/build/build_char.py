"""Build the Midnight Apex base characters (male + female) in Blender 4.2, headless.
blender -b -P build/build_char.py
-> char_base.blend (collections Male/Female), char_base_m.glb, char_base_f.glb, build/tris.json"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib, spec; importlib.reload(spec)
P = spec.P
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
TEXFILE = {"Head": "head.png", "Hair_A": "hair_a.png", "Hair_B": "hair_b.png"}   # Body + add-ons use the outfit atlas

# ------------------------------------------------------------------ weights (male reference space)
def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def keyw(t, keys):
    if t <= keys[0][0]: return {keys[0][1]: 1.0}
    for (a, ba), (b, bb) in zip(keys, keys[1:]):
        if t <= b:
            f = (t - a) / (b - a); w = {}
            w[ba] = w.get(ba, 0) + 1 - f; w[bb] = w.get(bb, 0) + f; return w
    return {keys[-1][1]: 1.0}
def mix(w1, w2, f):
    out = {k: v * (1 - f) for k, v in w1.items()}
    for k, v in w2.items(): out[k] = out.get(k, 0) + v * f
    return out
SPINE = [(0.90, "Hips"), (1.00, "Hips"), (1.10, "Spine"), (1.24, "Spine1"), (1.38, "Spine2"), (1.47, "Spine2"), (1.54, "Neck"), (1.60, "Neck"), (1.645, "Head")]
def w_trunk(p):
    S = "Left" if p.x >= 0 else "Right"
    w = keyw(p.z, SPINE)
    s = ss(.09, .16, abs(p.x)) * ss(1.33, 1.42, p.z)
    if s > 0: w = mix(w, {S + "Shoulder": 1}, s)
    a = ss(.12, .19, abs(p.x)) * ss(1.36, 1.43, p.z) * 0.7      # shoulder corner follows the upper arm (no pads in A-pose)
    if a > 0: w = mix(w, {S + "Arm": 1}, a)
    l = min(1, max(0, (0.99 - p.z) / 0.12)) * ss(0.0, 0.09, abs(p.x))
    if l > 0: w = mix(w, {S + "UpLeg": 1}, l)
    return w
def w_arm(p):
    S = "Left" if p.x >= 0 else "Right"
    w = keyw(abs(p.x), [(.10, "Shoulder"), (.14, "Shoulder"), (.21, "Arm"), (.41, "Arm"), (.51, "ForeArm"), (.71, "ForeArm"), (.79, "Hand")])
    return {S + k: v for k, v in w.items()}
def w_leg(p):
    S = "Left" if p.x >= 0 else "Right"
    w = keyw(-p.z, [(-.99, "Hips"), (-.86, "UpLeg"), (-.56, "UpLeg"), (-.42, "Leg"), (-.15, "Leg"), (-.07, "Foot")])
    return {(k if k == "Hips" else S + k): v for k, v in w.items()}
def w_foot(p):
    S = "Left" if p.x >= 0 else "Right"
    w = keyw(-p.y, [(.03, "Foot"), (.13, "ToeBase")])
    w = {S + k: v for k, v in w.items()}
    c = ss(.09, .15, p.z)
    return mix(w, {S + "Leg": 1}, c) if c > 0 else w
WFN = {"trunk": w_trunk, "arm": w_arm, "leg": w_leg, "foot": w_foot, "head": lambda p: {"Head": 1.0}}

# ------------------------------------------------------------------ geometry
class Piece:
    def __init__(s, name): s.name = name; s.V = []; s.W = []; s.SL = []; s.BU = []; s.F = []; s.UV = []; s.LB = []; s.cur = ""
    def vert(s, p, w, sl, bu): s.V.append(p); s.W.append(w); s.SL.append(sl); s.BU.append(bu); return len(s.V) - 1
    def face(s, idx, uvs): s.F.append(tuple(idx)); s.UV.append(tuple(uvs)); s.LB.append(s.cur)

def frame(lf, rings, i):
    c = Vector(rings[i][:3]); a = lf["axis"]
    if a == "z": return c, X, Y
    if a == "x": return c, Z, Y
    if a == "y": return c, X, -Z
    if a == "d":
        t = Vector(lf["d"]).normalized(); e1 = Z; return c, e1, t.cross(e1).normalized()
    # path
    pts = [Vector(r[:3]) for r in rings]
    t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
    e1 = Vector(lf["e1"]); e1 = (e1 - t * e1.dot(t)).normalized()
    return c, e1, t.cross(e1).normalized()

def ring_point(c, e1, e2, rx, ry, ex, th):
    p = c + e1 * (rx * math.sin(th)) - e2 * (ry * math.cos(th))
    dz = ex.get("tilt", 0) * math.cos(th) + ex.get("tilt2", 0) * math.cos(2 * th)
    p = p + Z * dz
    if "sweep" in ex: p = p + Z * (ex["sweep"] * math.sin(th) * max(0.0, math.cos(th)))
    if "push" in ex and math.cos(th) > 0.3:
        p = p + Vector((0, ex["push"][0], ex["push"][1])) * math.cos(th)
    return p

def shape_pos(lf, p, c, e1, e2, which, zM):
    g = lf["group"]
    if g == "trunk": f1, f2 = spec.trunk_factor(zM, which)
    else:
        f = spec.SHAPE[g]; f1, f2 = (f[0], f[1]) if which == "slim" else (f[2], f[3])
    if g == "head":
        return Vector((p.x * f1, p.y * f2, p.z))
    d = p - c; a = d.dot(e1); b = d.dot(e2); r = d - e1 * a - e2 * b
    if g == "shoe": f2 = 1.0
    out = c + e1 * (a * f1) + e2 * (b * f2) + r
    if g in spec.SHIFT:          # limbs move outward with the wider (or narrower) trunk / hips
        sh = spec.SHIFT[g][0 if which == "slim" else 1]
        out.x += sh * (1 if c.x >= 0 else -1)
    return out

def build_loft(pc, lf, sex):
    sides = lf["sides"]; ringsM = lf["rings"]
    ringsS = [spec.map_ring(lf, r, sex) for r in ringsM]; pc.cur = lf["name"]
    vs, vc0, vc1 = spec.ring_vs(lf); u0, _, u1, _ = lf["rect"]
    U = lambda k: u0 + (u1 - u0) * k / sides
    wfn = WFN[lf["chain"]]
    idx = []
    for i in range(len(ringsM)):
        cM, e1M, e2M = frame(lf, ringsM, i); cS, e1S, e2S = frame(lf, ringsS, i)
        row = []
        for k in range(sides):
            th = -math.pi + 2 * math.pi * k / sides
            pm = ring_point(cM, e1M, e2M, ringsM[i][3], ringsM[i][4], ringsM[i][5], th)
            ps = ring_point(cS, e1S, e2S, ringsS[i][3], ringsS[i][4], ringsS[i][5], th)
            zM = ringsM[i][2]
            row.append(pc.vert(ps, wfn(pm), shape_pos(lf, ps, cS, e1S, e2S, "slim", zM), shape_pos(lf, ps, cS, e1S, e2S, "bulky", zM)))
        idx.append(row)
    faces = []
    for i in range(len(ringsM) - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            faces.append(([idx[i][k], idx[i][k1], idx[i + 1][k1], idx[i + 1][k]],
                          [(U(k), vs[i]), (U(k + 1), vs[i]), (U(k + 1), vs[i + 1]), (U(k), vs[i + 1])]))
    # outward check on the first face
    a, b, c_, d = [pc.V[j] for j in faces[0][0]]
    n = (b - a).cross(d - a); cen = frame(lf, ringsS, 0)[0]
    flip = n.dot(a - cen) < 0
    for f, uv in faces:
        if flip: f = f[::-1]; uv = uv[::-1]
        pc.face(f, uv)
    for end in (0, 1):
        if not lf.get("cap%d" % end): continue
        ri = 0 if end == 0 else len(ringsM) - 1
        ccM = Vector(lf.get("cap%d_c" % end, ringsM[ri][:3]))
        ccS = Vector(spec.map_point(*ccM, lf["group"], sex))
        if sex == "f" and lf["axis"] == "y": ccS.z = ccM.z * 0.92
        cS = frame(lf, ringsS, ri)
        sl = shape_pos(lf, ccS, cS[0], cS[1], cS[2], "slim", ringsM[ri][2]); bu = shape_pos(lf, ccS, cS[0], cS[1], cS[2], "bulky", ringsM[ri][2])
        ci = pc.vert(ccS, wfn(ccM), sl, bu)
        vcap = vc0 if end == 0 else vc1
        other = frame(lf, ringsS, 1 if end == 0 else len(ringsM) - 2)[0]
        tris = []
        for k in range(sides):
            k1 = (k + 1) % sides
            tris.append(([idx[ri][k], idx[ri][k1], ci], [(U(k), vs[ri]), (U(k + 1), vs[ri]), ((U(k) + U(k + 1)) / 2, vcap)]))
        a, b, c_ = [pc.V[j] for j in tris[0][0]]
        flip = (b - a).cross(c_ - a).dot(ccS - other) < 0
        for f, uv in tris:
            if flip: f = f[::-1]; uv = uv[::-1]
            pc.face(f, uv)

def build_ears(pc, sex):
    u0, v0, u1, v1 = spec.EARS["rect"]; pc.cur = "ears"
    for s in (1, -1):
        quad = [(0.083 * s, -0.006, 1.663), (0.083 * s, 0.030, 1.663), (0.095 * s, 0.032, 1.722), (0.092 * s, -0.008, 1.722)]
        ids = []
        for q in quad:
            pm = Vector(q); ps = Vector(spec.map_point(*q, "head", sex))
            f = spec.SHAPE["head"]
            ids.append(pc.vert(ps, {"Head": 1.0}, Vector((ps.x * f[0], ps.y * f[1], ps.z)), Vector((ps.x * f[2], ps.y * f[3], ps.z))))
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)] if s > 0 else [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]
        if s < 0: ids = ids[::-1]; uv = uv[::-1]
        pc.face(ids, uv)

# ------------------------------------------------------------------ blender objects
def make_material(name, path, img=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = False
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs: bsdf.inputs["Specular IOR Level"].default_value = 0.0
    if img is None:
        img = bpy.data.images.load(path); img.pack(); img.name = name.split("_M_")[0].lower() + "_" + os.path.basename(path)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    return m

def make_armature(sex, coll):
    arm = bpy.data.armatures.new("CharBase_%s_Rig" % sex.upper())
    ob = bpy.data.objects.new("CharBase_%s" % sex.upper(), arm); coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects: o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for n, par, h, t, d in spec.bones(sex):
        b = arm.edit_bones.new(P + n); b.head = h; b.tail = t; b.use_deform = d; b.roll = 0.0
        if par: b.parent = eb[par]; b.use_connect = False
        eb[n] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"; ob.show_in_front = True
    return ob

OUTFIT_MAT = {}
def outfit_material(sex):
    if sex in OUTFIT_MAT: return OUTFIT_MAT[sex]
    imgs = []
    for o in spec.OUTFITS[sex]:
        img = bpy.data.images.load(os.path.join(spec.TEXDIR, sex, o + ".png")); img.pack(); img.use_fake_user = True
        img.name = "%s_%s" % (sex, o); imgs.append(img)
    m = make_material("%s_M_Outfit" % sex.upper(), None, imgs[0]); OUTFIT_MAT[sex] = m
    return m

def make_piece_obj(pc, sex, arm, coll):
    me = bpy.data.meshes.new("%s_%s" % (sex.upper(), pc.name))
    me.from_pydata([tuple(v) for v in pc.V], [], pc.F); me.update()
    uvl = me.uv_layers.new(name="UVMap")
    li = 0
    for poly, uvs in zip(me.polygons, pc.UV):
        for j, li in enumerate(poly.loop_indices): uvl.data[li].uv = uvs[j]
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new("%s_%s" % (sex.upper(), pc.name), me); coll.objects.link(ob)
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    groups = {}
    for n, par, h, t, d in spec.bones(sex):
        if d: groups[n] = ob.vertex_groups.new(name=P + n)
    for i, w in enumerate(pc.W):
        tot = sum(w.values())
        for b, v in w.items():
            if v > 1e-4: groups[b].add([i], v / tot, "REPLACE")
    ob.shape_key_add(name="Basis", from_mix=False)
    for nm, arr in (("Slim", pc.SL), ("Bulky", pc.BU)):
        k = ob.shape_key_add(name=nm, from_mix=False)
        for i, p in enumerate(arr): k.data[i].co = p
    if pc.name in TEXFILE: mat = make_material("%s_M_%s" % (sex.upper(), pc.name), os.path.join(spec.TEXDIR, sex, TEXFILE[pc.name]))
    else: mat = outfit_material(sex)
    ob.data.materials.append(mat)
    return ob

def add_test_action(arm):
    arm.animation_data_create()
    if "deform_test" in bpy.data.actions:          # one shared action for every body (same bone names)
        arm.animation_data.action = bpy.data.actions["deform_test"]
        for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"
        return
    act = bpy.data.actions.new("deform_test"); act.use_fake_user = True; arm.animation_data.action = act
    R = lambda ax, deg: Matrix.Rotation(math.radians(deg), 3, ax)
    poses = {  # frame: {bone: world rotation (rest-relative)}
        1: {},
        20: {"LeftArm": R("Y", 45), "RightArm": R("Y", -45), "LeftForeArm": R("Z", -15), "RightForeArm": R("Z", 15)},
        40: {"LeftArm": R("Y", 45), "RightArm": R("Y", -45), "LeftForeArm": R("Z", -15), "RightForeArm": R("Z", 15),
             "LeftUpLeg": R("X", -45), "LeftLeg": R("X", 85), "RightUpLeg": R("X", -10), "RightLeg": R("X", 20),
             "Head": R("Z", 35), "Spine2": R("Z", 8)},
    }
    names = set(k for p in poses.values() for k in p)
    for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"
    for f, pose in poses.items():
        for n in names:
            pb = arm.pose.bones[P + n]; M = pb.bone.matrix_local.to_3x3()
            Rw = pose.get(n, Matrix.Identity(3))
            pb.rotation_quaternion = (M.inverted() @ Rw @ M).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=f)
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 40

def tri_count(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

# ------------------------------------------------------------------ main
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
report = {}
for sex, cname in (("m", "Male"), ("f", "Female")):
    coll = bpy.data.collections.new(cname); sc.collection.children.link(coll)
    arm = make_armature(sex, coll)
    pieces = {}
    for lf in spec.lofts(sex):
        pc = pieces.setdefault(lf["piece"], Piece(lf["piece"]))
        build_loft(pc, lf, sex)
    build_ears(pieces["Head"], sex)
    objs = {n: make_piece_obj(pc, sex, arm, coll) for n, pc in pieces.items()}
    addon = spec.ADDON[sex]
    for n in ("Hair_B", addon): objs[n].hide_render = True; objs[n].hide_set(True)
    uv = [dict(loft=lb, uv=[list(map(lambda q: round(q, 5), t)) for t in uvs]) for n in ("Body", addon)
          for lb, uvs in zip(pieces[n].LB, pieces[n].UV)]
    json.dump(uv, open(os.path.join(HERE, "uv_%s.json" % sex), "w"))
    add_test_action(arm)
    report[sex] = {n: tri_count(o) for n, o in objs.items()}
    zs = [v.co.z for o in objs.values() for v in o.data.vertices]
    report[sex]["_height_body_hairA"] = round(max(v.co.z for n in ("Head", "Hair_A") for v in objs[n].data.vertices), 3)
    report[sex]["_lowest"] = round(min(zs), 3)
    base = report[sex]["Body"] + report[sex]["Head"]
    o_t, o_a = spec.OUTFITS[sex]
    report[sex]["_combos"] = {f"{h}+{o}": base + report[sex][h] + (report[sex][addon] if o == o_a else 0)
                              for h in ("Hair_A", "Hair_B") for o in (o_t, o_a)}
json.dump(report, open(os.path.join(HERE, "tris.json"), "w"), indent=1)
print("REPORT", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, "char_base.blend"), compress=True)

for sex, cname in (("m", "Male"), ("f", "Female")):
    for o in bpy.context.view_layer.objects: o.select_set(False)
    arm = bpy.data.objects["CharBase_%s" % sex.upper()]
    for o in [arm] + list(arm.children):
        o.hide_set(False); o.select_set(True)
    sc.frame_set(1)
    bpy.ops.export_scene.gltf(filepath=os.path.join(spec.GAMEDIR, "char_base_%s.glb" % sex), export_format="GLB", use_selection=True,
                              export_apply=False, export_morph=True, export_skins=True, export_animations=True, export_yup=True)
print("DONE")
