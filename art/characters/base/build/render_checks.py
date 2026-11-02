"""Render turnarounds / swap sheets / deform check / lineup from char_base.blend (Workbench, flat texture).
blender -b char_base.blend -P build/render_checks.py   (writes /tmp/cb_*.png, then build/compose.py assembles)"""
import bpy, math, os, json
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_cavity = False
sc.render.film_transparent = False
if not sc.world: sc.world = bpy.data.worlds.new("W")
sc.world.color = (0.18, 0.18, 0.2)
sc.display.render_aa = "OFF"
OUT = "/tmp/cb"; os.makedirs(OUT, exist_ok=True)
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
ARM = {"m": bpy.data.objects["CharBase_M"], "f": bpy.data.objects["CharBase_F"]}
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "")
OUTFITS = {"m": ("outfit_tee", "outfit_hoodie"), "f": ("outfit_tee", "outfit_jacket")}
ADDON = {"m": "Hood", "f": "Collar"}
def set_outfit(s, alt):
    m = bpy.data.materials["%s_M_Outfit" % s.upper()]
    node = [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"][0]
    node.image = bpy.data.images["%s_%s" % (s, OUTFITS[s][1 if alt else 0])]

def setup(sex_list, shape="", hair="Hair_A", alt=False, frame=1):
    for s, arm in ARM.items():
        on = s in sex_list
        arm.hide_render = not on
        set_outfit(s, alt)
        for o in arm.children:
            part = o.name[2:]
            vis = on
            if part.startswith("Hair_"): vis = on and part == hair
            if part == ADDON[s]: vis = on and alt
            o.hide_render = not vis
            if o.data.shape_keys:
                kb = o.data.shape_keys.key_blocks
                kb["Slim"].value = 1.0 if shape == "slim" else 0.0
                kb["Bulky"].value = 1.0 if shape == "bulky" else 0.0
    sc.frame_set(frame)

def ortho(view, zc=0.92, scale=2.0, res=(640, 640), x=0.0):
    cd.type = "ORTHO"; cd.ortho_scale = scale; sc.render.resolution_x, sc.render.resolution_y = res
    d = {"front": ((x, -6, zc), (90, 0, 0)), "side": ((6, 0, zc), (90, 0, 90)), "back": ((x, 6, zc), (90, 0, 180)),
         "q34": ((4.2, -4.2, zc), (90, 0, 45))}[view]
    cam.location = d[0]; cam.rotation_euler = [math.radians(a) for a in d[1]]

def persp(loc, target, lens=50, res=(480, 640)):
    cd.type = "PERSP"; cd.lens = lens; sc.render.resolution_x, sc.render.resolution_y = res
    cam.location = loc; cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

def shot(name):
    sc.render.filepath = f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)

for s in ("m", "f"):
    for shape in ("standard", "slim", "bulky"):
        setup([s], "" if shape == "standard" else shape)
        for v in ("front", "side", "back"):
            ortho(v); shot(f"turn_{s}_{shape}_{v}")
        setup([s], "" if shape == "standard" else shape, frame=20)
        ortho("front", zc=0.92, scale=2.0, res=(560, 640)); shot(f"build_{s}_{shape}")
    for h in ("Hair_A", "Hair_B"):
        for alt in (False, True):
            setup([s], "", h, alt, frame=20)
            zc = 0.95 if s == "m" else 0.88
            persp((1.5, -3.4, 1.25), (0, 0, zc), 50); shot(f"swap_{s}_{h}_{'alt' if alt else 'tee'}")
    # head close-ups for hair (front + 3/4)
    for h in ("Hair_A", "Hair_B"):
        setup([s], "", h, False, 1)
        hz = 1.70 if s == "m" else 1.58
        persp((0, -1.6, hz), (0, 0, hz), 85, (320, 320)); shot(f"hair_{s}_{h}_front")
        persp((1.15, -1.15, hz), (0, 0, hz), 85, (320, 320)); shot(f"hair_{s}_{h}_q34")
    setup([s], "", "Hair_A", False, 1); persp((1.9, -3.8, 1.3), (0, 0, .9), 40); shot(f"def_{s}_1_tpose")
    setup([s], "", "Hair_A", False, 40); persp((1.9, -3.8, 1.3), (0, 0, .9), 40); shot(f"def_{s}_2_std")
    setup([s], "bulky", "Hair_B", True, 40); persp((1.9, -3.8, 1.3), (0, 0, .9), 40); shot(f"def_{s}_3_bulky_alt")
    setup([s], "slim", "Hair_B", False, 40); persp((-2.2, 3.6, 1.4), (0, 0, .9), 40); shot(f"def_{s}_4_slim_back")
    setup([s], "bulky", "Hair_A", False, 40); persp((2.6, -1.0, 1.25), (0.15, 0, 1.2), 70); shot(f"def_{s}_5_bulky_armpit")
setup(["m", "f"], "", "Hair_A", False, 20)
ARM["m"].location.x = -0.8; ARM["f"].location.x = 0.8
ortho("front", zc=0.95, scale=2.8, res=(1000, 1000)); shot("lineup")
ARM["m"].location.x = 0; ARM["f"].location.x = 0
print("RENDERS_DONE")
