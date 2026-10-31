"""Tokyo v2 DUO vibe check: the S2000 and the BRZ (detail pass) parked side by side on the Tokyo v2 night street.
Reuses scene_v2.py verbatim for the world + the S2000 (its world/car section is executed from that file, so the
single-car scene is untouched and stays the one source of truth), then moves the S2000 into the right-hand slot and
appends the BRZ from brz_lowpoly.blend with the same faked-shine treatment (ambient + 1 key + Blinn + painted env map
x fresnel, env <= .45, fog -> emission), blob shadow, headlight-throw decal and lamp glow sprites.
Same render recipe as Tokyo v2: EEVEE Next 640x448, 1 sample, filter 0, Standard view + neon-only pass; post_duo.py
does the bloom -> RGB555 + 4x4 Bayer -> 2x nearest (1280x896), same as post_v2.py.
Usage: blender -b --python scene_duo.py [-- --no-render] [--only shot ...]
Mood reference only; NOT a game standard (art_direction.md Part B)."""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, "scene_v2.py")
# BRZ: box layout (/workspace/brz) or repo layout (art/vehicles/brz next to art/vehicles/s2000)
for cand in (os.path.normpath(os.path.join(HERE, "..", "..", "brz")), os.path.normpath(os.path.join(HERE, "..", "..", "..", "vehicles", "brz")),
             os.path.normpath(os.path.join(HERE, "..", "..", "vehicles", "brz"))):
    if os.path.exists(os.path.join(cand, "brz_lowpoly.blend")): BRZ_DIR = cand; break
else: raise SystemExit("brz_lowpoly.blend not found")
RD = os.path.join(os.path.dirname(HERE), "renders", "tokyo_duo") if os.path.basename(HERE) == "tokyo" else os.path.join(HERE, "renders", "duo")
os.makedirs(RD, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# ---- world + S2000 from scene_v2.py (everything up to its render setup)
code = open(V2).read(); cut = code.index("# ------------------------------------------------------------------ render setup")
g = {"__file__": V2, "__name__": "scene_v2_world"}
_argv = sys.argv; sys.argv = [sys.argv[0]]            # scene_v2 reads its own ARGS; give it none
exec(compile(code[:cut], V2, "exec"), g); sys.argv = _argv
sc = bpy.context.scene; C_CAR = g["C_CAR"]; quad = g["quad"]; mesh_obj = g["mesh_obj"]; decal = g["decal"]
additive = g["additive"]; billboard = g["billboard"]; fake_shine = g["fake_shine"]; GLOWS = g["GLOWS"]

# ---- slots: both nose toward -X (same heading as the v2 hero), ~1 m door-to-door gap, BRZ staggered 1.1 m back.
# Parked one block down from the konbini (x -4..16), under the sodium lamp at x -24 (-Y side), so the storefront
# sits in the distance instead of filling the frame.
X0 = -24.0
S2000_AT = (X0, -2.75); BRZ_AT = (X0 + 1.1, 0.05)
root = bpy.data.objects["S2000_Root"]; root.location = (*S2000_AT, 0)

# ---- BRZ: append car meshes (not its studio FX), swap materials to the scene's fake shine
with bpy.data.libraries.load(os.path.join(BRZ_DIR, "brz_lowpoly.blend")) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("BRZ_") and not n.startswith("BRZ_FX")]
brz = bpy.data.objects.new("BRZ_Root", None); C_CAR.objects.link(brz)
brz.location = (*BRZ_AT, 0); brz.rotation_euler = (0, 0, -math.pi / 2)   # BRZ file: nose along -Y -> world -X
for ob in dst.objects:
    C_CAR.objects.link(ob); ob.parent = brz
# BRZ paint env .22, slightly cool-tinted (S2000 .45): on its darker blue base the neon env map blotched the faceted panels at .32-.45
BRZ_SHINE = {"BRZ_Paint_Body": dict(spec=.6, env=.22, tint=(.8, .85, 1.0)), "BRZ_Glass": dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0)),
             "BRZ_Lamps_Atlas": dict(emissive=0.9, spec=.5, env=.2), "BRZ_Parts_Atlas": dict(spec=.3, env=.12),
             "BRZ_Lamp_Bezel": dict(spec=.1, env=.05), "BRZ_Under": dict(spec=.05, env=.03), "BRZ_Exhaust_Chrome": dict(spec=.8, env=.4)}
for m in bpy.data.materials:
    if m.name in BRZ_SHINE:
        nt = m.node_tree
        if "Principled BSDF" in nt.nodes and "ALBEDO" not in nt.nodes:   # untextured: carry its colour into an RGB node
            pass
        fake_shine(m, **BRZ_SHINE[m.name])
# blob shadow + headlight throw + glows (BRZ local frame: X = car left, Y = car rear, Z up)
bs = mesh_obj("BRZ_BlobShadow", [quad((-1.05, -2.5, 0.012), (2.1, 0, 0), (0, 5.0, 0))], [decal("blob_brz", "blob_shadow.png")], C_CAR, light=False)
# the blob texture is authored long along U; rotate its UVs a quarter turn to match this quad
for lp in bs.data.loops:
    uv = bs.data.uv_layers[0].data[lp.index].uv; uv[0], uv[1] = uv[1], 1 - uv[0]
bs.parent = brz
ht = mesh_obj("BRZ_HeadlightThrow", [quad((-1.6, -2.0, 0.014), (3.2, 0, 0), (0, -9.0, 0), (0, 1), (1, 0))], [decal("throw_brz", "headlight_throw.png", 'ADD', 0.45)], C_CAR, light=False)
for lp in ht.data.loops:
    uv = ht.data.uv_layers[0].data[lp.index].uv; uv[0], uv[1] = uv[1], uv[0]
ht.parent = brz
gh = additive("glow_head_brz", "glow_head.png", 1.1); gt = additive("glow_tail_brz", "glow_tail.png", 1.4)
for s in (1, -1):
    b = billboard(f"BRZ_HeadGlow_{s}", (0, 0, 0), .55, gh, C_CAR); b.parent = brz; b.location = (s * .70, -1.86, .72)
    b = billboard(f"BRZ_TailGlow_{s}", (0, 0, 0), .75, gt, C_CAR); b.parent = brz; b.location = (s * .70, 2.02, .85)

# ---- render setup (as scene_v2.py)
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
SHOTS = {  # name: cam loc, target, lens(mm)   (world: road along X, cars nose -X, konbini on the -Y side)
    "duo_hero_front34": ((X0 - 6.4, 2.6, 1.20), (X0 + 0.6, -1.20, 0.62), 32),
    "duo_rear34": ((X0 + 6.8, 2.8, 1.40), (X0 - 0.4, -1.20, 0.62), 32),
    "duo_side_by_side": ((X0 - 6.2, -1.25, 0.58), (X0 + 0.6, -1.30, 0.52), 32),
    "duo_establishing": ((X0 + 14.5, 0.8, 5.2), (X0 - 2.5, -1.3, 0.6), 28),
}
SHOTS.update(eval(os.environ.get("DUO_SHOTS", "{}")))       # framing trials without editing the file
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "tokyo_duo.blend"), relative_remap=True)
if "--no-render" not in ARGS:
    vl = sc.view_layers[0]
    for name, (loc, tg, lens) in SHOTS.items():
        if "--only" in ARGS and name not in ARGS: continue
        cam.location = loc; tgt.location = tg; cam.data.lens = lens
        for lc in vl.layer_collection.children: lc.holdout = False
        sc.render.film_transparent = False
        sc.render.filepath = os.path.join(RD, f"raw_{name}.png"); bpy.ops.render.render(write_still=True)
        for lc in vl.layer_collection.children: lc.holdout = lc.name not in ("Neon",)
        sc.render.film_transparent = True
        sc.render.filepath = os.path.join(RD, f"neon_{name}.png"); sc.render.image_settings.color_mode = 'RGBA'
        bpy.ops.render.render(write_still=True); sc.render.image_settings.color_mode = 'RGB'
print("DUO SCENE DONE")
