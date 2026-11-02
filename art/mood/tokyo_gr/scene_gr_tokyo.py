"""GR Corolla night vibe check on the Tokyo v2 street (non-binding mood reference, art_direction.md Part B).
Same recipe as art/mood/tokyo_v2/scene_duo.py: runs scene_v2.py's world section unchanged (exec up to its render
setup), removes the S2000, then imports the GR Corolla .glb (exactly what Godot imports) into the S2000's world slot
one block before the konbini and gives it the scene's faked shine (ambient + 1 key + Blinn + painted env map x
fresnel, env <= .45, fog -> emission), a blob shadow, a headlight-throw decal and the scene's lamp-glow sprites.
EEVEE Next 640x448, 1 sample, filter 0, Standard view + neon-only pass; post_gr_tokyo.py = post_duo recipe
(bloom -> RGB555 + 4x4 Bayer -> 2x nearest, 1280x896).
scene_v2.py writes its generated textures next to itself, so run it from a scratch copy of the repo layout:
  TOKYO_V2=<copy>/art/mood/tokyo_v2/scene_v2.py GR_GLB=<car_gr_corolla.glb> blender -b --python scene_gr_tokyo.py
(the copy needs art/vehicles/s2000 next to it, as scene_v2.py appends the S2000 before we delete it)."""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.environ.get('TOKYO_V2', os.path.normpath(os.path.join(HERE, '..', 'tokyo_v2', 'scene_v2.py')))          # repo: art/mood/tokyo_gr -> art/mood/tokyo_v2
GLB = os.environ.get('GR_GLB', os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'cars', 'gr_corolla', 'car_gr_corolla.glb')))
RD = os.environ.get('GR_RD', os.path.join(HERE, 'renders', 'raw')); os.makedirs(RD, exist_ok=True)
code = open(V2).read(); cut = code.index("# ------------------------------------------------------------------ render setup")
g = {"__file__": V2, "__name__": "scene_v2_world"}
_argv = sys.argv; sys.argv = [sys.argv[0]]; exec(compile(code[:cut], V2, "exec"), g); sys.argv = _argv
sc = bpy.context.scene; C_CAR = g["C_CAR"]; quad = g["quad"]; mesh_obj = g["mesh_obj"]; decal = g["decal"]
additive = g["additive"]; billboard = g["billboard"]; fake_shine = g["fake_shine"]; GLOWS = g["GLOWS"]
# ---- remove the S2000 (root, its meshes, blob shadow, throw decal, glow sprites)
s2 = bpy.data.objects["S2000_Root"]; gone = [s2] + list(s2.children_recursive)
for o in gone:
    if o in GLOWS: GLOWS.remove(o)
for o in gone: bpy.data.objects.remove(o, do_unlink=True)
# ---- GR Corolla from the game .glb (glTF -> Blender: X = car left, -Y = car forward, Z up)
X0 = -24.0; AT = (X0, -1.55)
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=GLB); new = [o for o in bpy.data.objects if o not in before]
for o in new:
    for c in list(o.users_collection): c.objects.unlink(o)
    C_CAR.objects.link(o)
    if '_FX_' in o.name: o.hide_render = True                                 # the scene's own glow sprites are used instead
root = bpy.data.objects["GRC-vehicle"]; root.rotation_mode = "XYZ"; root.location = (*AT, 0); root.rotation_euler = (0, 0, -math.pi / 2)  # nose -> world -X
# white paint: env .22 cool-tinted, as the BRZ (at .30 the neon env map smeared a rainbow band across the black lower front)
SHINE = {"GRC_Paint_Body": dict(spec=.55, env=.22, amb=.5, tint=(.80, .86, 1.0)), "GRC_Glass": dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0)),
         "GRC_Lamp": dict(emissive=0.9, spec=.5, env=.2), "GRC_Wheel": dict(spec=.3, env=.12), "GRC_Under": dict(spec=.05, env=.03)}
for m in bpy.data.materials:
    if m.name in SHINE: fake_shine(m, **SHINE[m.name])
bs = mesh_obj("GR_BlobShadow", [quad((-1.05, -2.5, 0.012), (2.1, 0, 0), (0, 5.0, 0))], [decal("blob_gr", "blob_shadow.png")], C_CAR, light=False)
for lp in bs.data.loops:
    uv = bs.data.uv_layers[0].data[lp.index].uv; uv[0], uv[1] = uv[1], 1 - uv[0]
bs.parent = root
ht = mesh_obj("GR_HeadlightThrow", [quad((-1.6, -2.2, 0.014), (3.2, 0, 0), (0, -9.0, 0), (0, 1), (1, 0))], [decal("throw_gr", "headlight_throw.png", 'ADD', 0.45)], C_CAR, light=False)
for lp in ht.data.loops:
    uv = ht.data.uv_layers[0].data[lp.index].uv; uv[0], uv[1] = uv[1], uv[0]
ht.parent = root
gh = additive("glow_head_gr", "glow_head.png", 1.1); gt = additive("glow_tail_gr", "glow_tail.png", 1.4)
for s in (1, -1):                                                              # lamp centres from the blueprint (HEADLAMP_F / TAIL_R)
    b = billboard(f"GR_HeadGlow_{s}", (0, 0, 0), .55, gh, C_CAR); b.parent = root; b.location = (s * .60, -2.12, .68)
    b = billboard(f"GR_TailGlow_{s}", (0, 0, 0), .70, gt, C_CAR); b.parent = root; b.location = (s * .64, 1.99, .88)
# ---- render setup (as scene_v2.py / scene_duo.py)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("Tgt", None); sc.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
cam.data.clip_start = .1; cam.data.clip_end = 400
for gl in GLOWS:
    d = gl.constraints.new('TRACK_TO'); d.target = cam; d.track_axis = 'TRACK_NEGATIVE_Y'; d.up_axis = 'UP_Z'
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = 640, 448; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
SHOTS = {"gr_hero_front34": ((X0 - 6.6, 1.6, 1.15), (X0 + 0.4, -1.55, 0.62), 32),
         "gr_rear34": ((X0 + 6.4, 1.8, 1.35), (X0 - 0.4, -1.55, 0.62), 32),
         "gr_establishing": ((X0 + 14.5, 0.8, 5.2), (X0 - 2.5, -1.3, 0.6), 28)}
SHOTS.update(eval(os.environ.get("GR_SHOTS", "{}")))
vl = sc.view_layers[0]
for name, (loc, tg, lens) in SHOTS.items():
    cam.location = loc; tgt.location = tg; cam.data.lens = lens
    for lc in vl.layer_collection.children: lc.holdout = False
    sc.render.film_transparent = False; sc.render.filepath = os.path.join(RD, f"raw_{name}.png"); bpy.ops.render.render(write_still=True)
    for lc in vl.layer_collection.children: lc.holdout = lc.name not in ("Neon",)
    sc.render.film_transparent = True; sc.render.filepath = os.path.join(RD, f"neon_{name}.png"); sc.render.image_settings.color_mode = 'RGBA'
    bpy.ops.render.render(write_still=True); sc.render.image_settings.color_mode = 'RGB'
print("GR TOKYO DONE")
