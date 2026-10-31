"""Tokyo v2 vibe-check scene (REBUILT 2026-10-31 after data loss; original scene_v2.py was lost).
Authentic PSX/PS2-era fake: everything unlit (texture x vertex colour -> linear fog -> emission), lighting painted in,
dry matte road with stepped sodium pools, glow billboards, car with faked shine (ambient + 1 key + Blinn + painted env map),
blob shadow + headlight-throw decal. EEVEE Next 640x448, 1 sample, filter 0, Standard view. Post: tokyo/post_v2.py.
Usage: blender -b --python scene_v2.py [-- --no-render]
Mood reference only; NOT a game standard (see art_direction.md Part B)."""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
# works both in the box layout (/workspace/s2000/tokyo) and the repo layout (art/mood/tokyo_v2 + art/vehicles/s2000)
ROOT = os.path.dirname(HERE) if os.path.exists(os.path.join(os.path.dirname(HERE), "s2000_lowpoly.blend")) else \
    os.path.normpath(os.path.join(HERE, "..", "..", "vehicles", "s2000"))
TEX = os.path.join(HERE, "tex"); os.makedirs(TEX, exist_ok=True)
RD = os.path.join(os.path.dirname(HERE), "renders", "tokyo_v2") if os.path.basename(HERE) == "tokyo" else os.path.join(HERE, "renders")
os.makedirs(RD, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
R = random.Random(11)
FOG_NEAR, FOG_FAR = 14.0, 105.0
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c): return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
FOG = lin(hx('#30263F')); VAMB = hx('#ADADC8'); SOD = hx('#FF9947')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
LAMPS = [[x, s] for x in range(-104, 105, 16) for s in ((-1,) if (x // 16) % 2 == 0 else (1,))]
json.dump(LAMPS, open(os.path.join(TEX, "lamps.json"), "w"))
import subprocess, shutil
subprocess.run([shutil.which("python3") or "/usr/bin/python3", os.path.join(HERE, "make_tex_v2.py"), TEX], check=True)

# ------------------------------------------------------------------ collections
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
C_WORLD, C_NEON, C_CAR, C_SKY = coll("World"), coll("Neon"), coll("Car"), coll("Sky")

# ------------------------------------------------------------------ materials
IMGS = {}
def img(name):
    if name not in IMGS:
        im = bpy.data.images.load(os.path.join(TEX, name)); IMGS[name] = im
    return IMGS[name]

def fog_mix(nt, col_socket, fog=True):
    if not fog: return col_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
    mr.inputs[1].default_value, mr.inputs[2].default_value = FOG_NEAR, FOG_FAR
    nt.links.new(cam.outputs["View Z Depth"], mr.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    nt.links.new(mr.outputs[0], mx.inputs["Factor"]); nt.links.new(col_socket, mx.inputs[6])
    mx.inputs[7].default_value = (*FOG, 1)
    return mx.outputs[2]

MATS = {}
def unlit(name, tex=None, color=(1, 1, 1), fog=True, alpha=False, vcol=True, strength=1.0, interp='Linear', ext='REPEAT'):
    key = (name, tex, color, fog, alpha, vcol, strength)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeRGB"); col.outputs[0].default_value = (*lin(color), 1); cs = col.outputs[0]; asock = None
    if tex:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(tex); t.interpolation = interp; t.extension = ext
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1
        nt.links.new(t.outputs[0], mul.inputs[6]); nt.links.new(cs, mul.inputs[7]); cs = mul.outputs[2]; asock = t.outputs[1]
    if vcol:   # vertex colours stored at half scale (glTF clamp rule) -> x2
        a = nt.nodes.new("ShaderNodeVertexColor"); a.layer_name = "Col"
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1
        nt.links.new(cs, mul.inputs[6]); nt.links.new(a.outputs[0], mul.inputs[7])
        x2 = nt.nodes.new("ShaderNodeVectorMath"); x2.operation = 'SCALE'; x2.inputs[3].default_value = 2.0
        nt.links.new(mul.outputs[2], x2.inputs[0]); cs = x2.outputs[0]
    cs = fog_mix(nt, cs, fog)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = strength; nt.links.new(cs, em.inputs[0])
    if alpha and asock is not None:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
        nt.links.new(asock, gt.inputs[0]); nt.links.new(gt.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
        m.surface_render_method = 'DITHERED'
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    MATS[key] = m; return m

def additive(name, tex, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(tex); t.extension = 'CLIP'
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = 'SCALE'
    nt.links.new(t.outputs[0], mul.inputs[0]); nt.links.new(t.outputs[1], mul.inputs[3])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = strength; nt.links.new(mul.outputs[0], em.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs[0])
    m.surface_render_method = 'BLENDED'; return m

def decal(name, tex, mode='MULT', strength=1.0):
    """Blob shadow (darken by alpha) or additive light decal."""
    if mode == 'ADD': return additive(name, tex, strength)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(tex); t.extension = 'CLIP'
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0, 0, 0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(t.outputs[1], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0]); m.surface_render_method = 'BLENDED'; return m

# ------------------------------------------------------------------ vertex lighting (painted light, stored half-scale)
def vlight(p, base=VAMB, k=0.75, lamps=True, glow=None):
    c = [base[i] * k for i in range(3)]
    if lamps:
        for lx, s in LAMPS:
            d = math.dist((p[0], p[1], p[2]), (lx, s * 3.6, 7.5))
            lv = max(0.0, 1 - d / 13.0); lv = math.floor(lv * 4) / 4
            for i in range(3): c[i] += SOD[i] * lv * 0.9
    if glow:
        gp, gc, gr = glow; d = math.dist(p, gp); lv = max(0, 1 - d / gr)
        for i in range(3): c[i] += gc[i] * lv
    return tuple(min(1.0, x * 0.5) for x in c) + (1.0,)

def mesh_obj(name, quads, mats, collection=C_WORLD, light=True, base=VAMB, k=0.75, glow=None):
    """quads: list of (verts[4], uvs[4], mat_index)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    cl = bm.loops.layers.color.new("Col")
    for vs, uvs, mi in quads:
        bv = [bm.verts.new(v) for v in vs]; f = bm.faces.new(bv); f.material_index = mi
        for lp, uv in zip(f.loops, uvs):
            lp[uvl].uv = uv; lp[cl] = vlight(lp.vert.co, base, k, light, glow) if light else (0.5, 0.5, 0.5, 1)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    return ob

def quad(p0, du, dv, u=(0, 1), v=(0, 1), mi=0):
    p0 = Vector(p0); du = Vector(du); dv = Vector(dv)
    return ([p0, p0 + du, p0 + du + dv, p0 + dv], [(u[0], v[0]), (u[1], v[0]), (u[1], v[1]), (u[0], v[1])], mi)

def subdiv_quad(p0, du, dv, nu, nv, u=(0, 1), v=(0, 1), mi=0):
    out = []; p0 = Vector(p0); du = Vector(du); dv = Vector(dv)
    for i in range(nu):
        for j in range(nv):
            out.append(quad(p0 + du * (i / nu) + dv * (j / nv), du / nu, dv / nv,
                            (u[0] + (u[1] - u[0]) * i / nu, u[0] + (u[1] - u[0]) * (i + 1) / nu),
                            (v[0] + (v[1] - v[0]) * j / nv, v[0] + (v[1] - v[0]) * (j + 1) / nv), mi))
    return out

def box(name, c, s, mats_faces, collection=C_WORLD, light=True, base=VAMB, k=0.75, uvscale=(1, 1)):
    """Axis box. mats_faces: list of 1 or 6 materials (+x,-x,+y,-y,+z,-z)."""
    x, y, z = c; sx, sy, sz = (s[0] / 2, s[1] / 2, s[2] / 2)
    q = [quad((x + sx, y - sy, z - sz), (0, 2 * sy, 0), (0, 0, 2 * sz), (0, uvscale[0]), (0, uvscale[1]), 0),
         quad((x - sx, y + sy, z - sz), (0, -2 * sy, 0), (0, 0, 2 * sz), (0, uvscale[0]), (0, uvscale[1]), 1),
         quad((x + sx, y + sy, z - sz), (-2 * sx, 0, 0), (0, 0, 2 * sz), (0, uvscale[0]), (0, uvscale[1]), 2),
         quad((x - sx, y - sy, z - sz), (2 * sx, 0, 0), (0, 0, 2 * sz), (0, uvscale[0]), (0, uvscale[1]), 3),
         quad((x - sx, y - sy, z + sz), (2 * sx, 0, 0), (0, 2 * sy, 0), (0, 1), (0, 1), 4),
         quad((x - sx, y + sy, z - sz), (2 * sx, 0, 0), (0, -2 * sy, 0), (0, 1), (0, 1), 5)]
    mats = mats_faces if len(mats_faces) == 6 else mats_faces * 6
    return mesh_obj(name, q, mats, collection, light, base, k)

# ------------------------------------------------------------------ road + sidewalks
X0, X1 = -110.0, 110.0
road_m = unlit("road", "road.png", vcol=False, ext='EXTEND')
mesh_obj("Road", [quad((X0, -4.5, 0), (X1 - X0, 0, 0), (0, 9, 0), (1, 0), (0, 1))], [road_m], light=False)
# fix road UV orientation: u across, v along (image top = x0)
me = bpy.data.objects["Road"].data
for lp in me.loops:
    co = me.vertices[lp.vertex_index].co; me.uv_layers[0].data[lp.index].uv = ((co.y + 4.5) / 9, 1 - (co.x - X0) / (X1 - X0))
side_m = unlit("sidewalk", "sidewalk.png"); curb_m = unlit("curb", color=(0.55, 0.53, 0.5))
for s in (-1, 1):
    y_in, y_out = 4.5 * s, 7.5 * s
    q = []
    for i in range(44):
        xa = X0 + i * 5
        p0 = (xa, min(y_in, y_out), 0.15); q.append(quad(p0, (5, 0, 0), (0, 3, 0), (0, 1.25 * 1), (0, 0.75 * 1 / 1)))
        q.append(quad((xa, y_in, 0) if s > 0 else (xa + 5, y_in, 0), (5 * s, 0, 0), (0, 0, 0.15), (0, 5), (0, .15)))
    ob = mesh_obj(f"Sidewalk_{s}", q, [side_m])
    for f in ob.data.polygons:
        if abs(f.normal.z) < .5: f.material_index = 0
    ob.data.materials.append(curb_m)
    for f in ob.data.polygons:
        if abs(f.normal.z) < .5: f.material_index = 1

# ------------------------------------------------------------------ buildings
fac_m = [unlit(f"facade_{i:02d}", f"facade_{i:02d}.png") for i in range(12)]
side_wall = [unlit(f"wall_{i}", color=c) for i, c in enumerate([(.35, .33, .32), (.28, .27, .3), (.4, .3, .26)])]
roof_m = unlit("roof", color=(.18, .17, .2))
B_TRIS = 0
def building(x, w, s, h, fi, depth=12.0):
    y0 = 7.5 * s; yb = y0 + depth * s; cx = x + w / 2
    reps_u = max(1, round(w / 8)); reps_v = h / 24
    q = []
    if s > 0:   # facade faces -Y (toward street)
        q += subdiv_quad((x, y0, 0), (w, 0, 0), (0, 0, h), reps_u * 2, max(2, int(h / 4)), (0, reps_u), (0, reps_v), 0)
    else:
        q += subdiv_quad((x + w, y0, 0), (-w, 0, 0), (0, 0, h), reps_u * 2, max(2, int(h / 4)), (0, reps_u), (0, reps_v), 0)
    for xe, dirx in ((x, -1), (x + w, 1)):   # end walls
        a, b = (y0, yb) if (dirx * s) < 0 else (yb, y0)
        q.append(quad((xe, a, 0), (0, b - a, 0), (0, 0, h), (0, 1), (0, 1), 1))
    q.append(quad((x, min(y0, yb), h), (w, 0, 0), (0, depth, 0), mi=2))
    return mesh_obj(f"Bldg_{s}_{x:.0f}", q, [fac_m[fi], side_wall[fi % 3], roof_m])
KONBINI = (-4.0, 16.0)
for s in (-1, 1):
    x = X0
    while x < X1:
        w = R.choice([6, 8, 8, 10, 12]); h = R.choice([10, 12, 14, 16, 20, 24, 28]); fi = R.randrange(12)
        if s < 0 and x < KONBINI[1] and x + w > KONBINI[0]:
            w = KONBINI[1] - x if x >= KONBINI[0] else KONBINI[0] - x
            if x >= KONBINI[0]: building(x, w, s, 14, 4); x += w; continue
        building(x, w, s, h, fi); x += w
# konbini storefront panel on the ground floor (toned down: never brighter than the car)
kon = unlit("konbini", "konbini.png", strength=0.55)
mesh_obj("Konbini", [quad((KONBINI[1], -7.45, 0.15), (KONBINI[0] - KONBINI[1], 0, 0), (0, 0, 5))], [kon], light=False)
mesh_obj("Konbini_Canopy", [quad((KONBINI[1], -7.45, 5.0), (KONBINI[0] - KONBINI[1], 0, 0), (0, 1.0, 0.2))], [unlit("kcan", color=(.43, .24, .67))], light=False)

# ------------------------------------------------------------------ neon signs (perpendicular blades, unflipped text both sides)
neon_m = [unlit(f"neon_{i:02d}", f"neon_{i:02d}.png", fog=True, vcol=False, strength=1.0) for i in range(8)]
box_m = [unlit(f"box_{i:02d}", f"box_{i:02d}.png", vcol=False) for i in range(6)]
glow_cols = ['#FF3C8C', '#C85AFF', '#FF4632', '#3CC8FF', '#FFAA28', '#78FF78', '#3CC8FF', '#FFAA28']
def blade(name, x, y, z, w, h, m, coll_=C_NEON):
    # u runs toward the viewer's right on both faces, so text is never mirrored (checklist rule)
    q = [quad((x - .01, y + w / 2, z), (0, -w, 0), (0, 0, h), (0, 1), (0, 1)),   # seen from -X
         quad((x + .01, y - w / 2, z), (0, w, 0), (0, 0, h), (0, 1), (0, 1))]    # seen from +X
    return mesh_obj(name, q, [m], coll_, light=False)
for i, x in enumerate([v + o for v in range(-96, 100, 9) for o in (0, 4)]):
    s = -1 if (i // 2) % 2 else 1
    if i % 2: s = -s
    if s < 0 and KONBINI[0] - 1 < x < KONBINI[1] + 1: continue
    k = R.randrange(8); im = img(f"neon_{k:02d}.png"); ar = im.size[1] / im.size[0]
    w = 1.15; h = min(w * ar, 7.0); z = R.uniform(3.6, 8.5)
    blade(f"Neon_{i}", x, s * 6.9, z, w, h, neon_m[k])
    if R.random() < .6:
        kb = R.randrange(6); ib = img(f"box_{kb:02d}.png"); blade(f"Box_{i}", x + 3.5, s * 6.95, R.uniform(2.6, 4.0), .6, .6 * ib.size[1] / ib.size[0], box_m[kb], C_WORLD)
drug = unlit("drug", "box_drug.png", vcol=False)
mesh_obj("DrugSign", [quad((30, 7.44, 3.2), (4, 0, 0), (0, 0, 1.0))], [drug], C_NEON, light=False)

# ------------------------------------------------------------------ utility poles, wires, streetlights
pole_m = unlit("pole", color=(.62, .6, .58)); stripe_m = unlit("stripe", color=(.9, .75, .1)); black_m = unlit("black", color=(.06, .06, .07))
lamp_m = unlit("lamphead", color=(1.0, .78, .5), vcol=False, fog=False, strength=1.6)
glow_sod = additive("glow_sodium", "glow_sodium.png", 0.9)
GLOWS = []
def billboard(name, p, size, m, coll_=C_NEON):
    q = [quad((-size / 2, 0, -size / 2), (size, 0, 0), (0, 0, size))]
    ob = mesh_obj(name, q, [m], coll_, light=False); ob.location = p; GLOWS.append(ob); return ob
POLES = []
for i, x in enumerate(range(-100, 101, 18)):
    for s in (-1, 1):
        px = x + (5 if s > 0 else 0); py = 4.85 * s
        box(f"Pole_{s}_{x}", (px, py, 5.0), (.28, .28, 10.0), [pole_m]); POLES.append((px, py))
        box(f"PoleStripe_{s}_{x}", (px, py, 1.6), (.3, .3, .8), [stripe_m])
        box(f"PoleXarm_{s}_{x}", (px, py, 9.2), (.12, 1.4, .12), [black_m])
for s in (-1, 1):   # sagging flat-ribbon wires along each side
    ps = sorted([p for p in POLES if p[1] * s > 0])
    for (xa, ya), (xb, yb) in zip(ps, ps[1:]):
        for wz in (9.6, 9.0, 8.4):
            q = []
            for j in range(6):
                t0, t1 = j / 6, (j + 1) / 6; sag0 = -0.6 * 4 * t0 * (1 - t0); sag1 = -0.6 * 4 * t1 * (1 - t1)
                q.append(quad((xa + (xb - xa) * t0, ya, wz + sag0), ((xb - xa) / 6, 0, sag1 - sag0), (0, 0, .035)))
            mesh_obj(f"Wire_{s}_{xa}_{wz}", q, [black_m], light=False)
for x, s in LAMPS:   # streetlights: pole + arm over road + lamp head + glow
    box(f"SLPole_{x}", (x, 5.0 * s, 3.9), (.16, .16, 7.8), [unlit("slpole", color=(.4, .4, .42))])
    box(f"SLArm_{x}", (x, 4.3 * s, 7.75), (.1, 1.5, .1), [unlit("slpole", color=(.4, .4, .42))])
    box(f"SLHead_{x}", (x, 3.6 * s, 7.6), (.5, .3, .12), [lamp_m])
    billboard(f"SLGlow_{x}", (x, 3.6 * s, 7.45), 2.4, glow_sod)

# ------------------------------------------------------------------ props (pre-lit cutouts, vending machines)
cut = {k: unlit(f"cut_{k}", f"cut_{k}.png", alpha=True, ext='CLIP') for k in ('bike', 'cone', 'barrier', 'plant', 'board')}
def card(name, kind, p, w, h, facing='x'):
    x, y, z = p
    if facing == 'x':   # two-sided card in the YZ plane... visible from street ends
        q = [quad((x, y - w / 2, z), (0, w, 0), (0, 0, h)), quad((x, y + w / 2, z), (0, -w, 0), (0, 0, h))]
    else:               # card along X (faces the street)
        q = [quad((x - w / 2, y, z), (w, 0, 0), (0, 0, h)), quad((x + w / 2, y, z), (-w, 0, 0), (0, 0, h))]
    return mesh_obj(name, q, [cut[kind]])
for i, x in enumerate((-60, -33, 22, 41, 70)):
    for j in range(R.randint(1, 3)): card(f"Bike_{i}_{j}", 'bike', (x + j * .7, 6.6 if i % 2 else -6.6, .15), 1.7, 1.7, 'y')
for i, x in enumerate(range(-90, 95, 23)):
    card(f"Plant_{i}", 'plant', (x, 7.2 if i % 2 else -7.2, .15), .9, .9, 'y')
    card(f"Board_{i}", 'board', (x + 6, -7.0 if i % 2 else 7.0, .15), .7, 1.0, 'y')
vend_m = unlit("vending", "vending.png")
for i, x in enumerate((-40, 18, 27, 52)):
    s = 1 if i % 2 == 0 else -1
    if s < 0 and KONBINI[0] < x < KONBINI[1]: s = 1
    box(f"Vend_{i}", (x, 7.0 * s, 1.05), (1.0, .8, 1.8), [unlit("vend_side", color=(.75, .78, .82)), unlit("vend_side", color=(.75, .78, .82)),
        vend_m if s < 0 else unlit("vend_side", color=(.75, .78, .82)), vend_m if s > 0 else unlit("vend_side", color=(.75, .78, .82)),
        unlit("vend_side", color=(.75, .78, .82)), unlit("vend_side", color=(.75, .78, .82))], base=(1, 1, 1), k=.9)
for p in ((14, 2.2), (15.5, 1.0), (13.2, 3.3), (17, 2.8), (12, 1.6), (-14, 3.8), (-13, 3.2)):
    card(f"Cone_{p[0]}_{p[1]}", 'cone', (p[0], p[1], 0), .45, .7, 'x')
card("Barrier", 'barrier', (12.5, 2.6, 0), 2.0, 1.1, 'x'); card("Barrier2", 'barrier', (-15.5, 3.6, 0), 2.0, 1.1, 'x')

# ------------------------------------------------------------------ sky + skyline cards (unfogged, fog-matched)
sky_m = unlit("sky", "sky.png", fog=False, vcol=False, ext='EXTEND')
for xe, d in ((X1 + 6, -1), (X0 - 6, 1)):
    mesh_obj(f"Sky_{xe}", [quad((xe, 160 * d, -2), (0, -320 * d, 0), (0, 0, 120))], [sky_m], C_SKY, light=False)
for xe, d, nm in ((X1 + 2, -1, 'skyline_a.png'), (X0 - 2, 1, 'skyline_b.png')):
    sm = unlit(f"sl_{nm}", nm, fog=False, vcol=False, alpha=True, ext='CLIP')
    mesh_obj(f"Skyline_{xe}", [quad((xe, 40 * d, 0), (0, -80 * d, 0), (0, 0, 22))], [sm], C_SKY, light=False)
    tow = unlit(f"tow_{nm}", nm, fog=False, vcol=False, alpha=True, ext='CLIP')
    mesh_obj(f"Tower_{xe}", [quad((xe - 1 * d * -1, 9 * d, 0), (0, -14 * d, 0), (0, 0, 45), (0.1, 0.25), (0, 1))], [tow], C_SKY, light=False)
w = sc.world = bpy.data.worlds.new("W"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (*FOG, 1)

# ------------------------------------------------------------------ car: append the S2000, swap to faked-shine materials
SRC = os.path.join(ROOT, "s2000_lowpoly.blend")
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("S2000")]
for ob in dst.objects: C_CAR.objects.link(ob)
root = bpy.data.objects["S2000_Root"]; root.location = (0, -1.7, 0); root.rotation_euler = (0, 0, math.pi)
ENV = img("env_street.png")
def fake_shine(m, emissive=0.0, spec=0.6, env=0.45, amb=0.55, tint=None):
    """albedo x (ambient + key N.L) + Blinn spec + painted env map x fresnel (env <= .45) -> fog -> emission."""
    nt = m.node_tree; base = None; bsdf = nt.nodes.get("Principled BSDF")
    tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if tex is not None:
        tex.interpolation = 'Linear'; base = tex.outputs[0]
    else:
        c = nt.nodes.new("ShaderNodeRGB"); c.outputs[0].default_value = bsdf.inputs["Base Color"].default_value if bsdf else (.5, .5, .5, 1); base = c.outputs[0]
    for n in list(nt.nodes):
        if n.type not in ('TEX_IMAGE', 'UVMAP', 'RGB', 'MAPPING', 'TEX_COORD'): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); geo = nt.nodes.new("ShaderNodeNewGeometry")
    key = nt.nodes.new("ShaderNodeCombineXYZ"); kv = Vector((-0.35, 0.45, 0.82)).normalized()
    key.inputs[0].default_value, key.inputs[1].default_value, key.inputs[2].default_value = kv
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs["Normal"], dot.inputs[0]); nt.links.new(key.outputs[0], dot.inputs[1])
    dif = nt.nodes.new("ShaderNodeMapRange"); dif.clamp = True; dif.inputs[1].default_value = 0; dif.inputs[2].default_value = 1
    dif.inputs[3].default_value = amb; dif.inputs[4].default_value = 1.0; nt.links.new(dot.outputs["Value"], dif.inputs[0])
    sh = nt.nodes.new("ShaderNodeVectorMath"); sh.operation = 'SCALE'; nt.links.new(base, sh.inputs[0]); nt.links.new(dif.outputs[0], sh.inputs[3])
    # Blinn: H = normalize(L + V)
    hv = nt.nodes.new("ShaderNodeVectorMath"); hv.operation = 'ADD'; nt.links.new(key.outputs[0], hv.inputs[0]); nt.links.new(geo.outputs["Incoming"], hv.inputs[1])
    hn = nt.nodes.new("ShaderNodeVectorMath"); hn.operation = 'NORMALIZE'; nt.links.new(hv.outputs[0], hn.inputs[0])
    nh = nt.nodes.new("ShaderNodeVectorMath"); nh.operation = 'DOT_PRODUCT'; nt.links.new(geo.outputs["Normal"], nh.inputs[0]); nt.links.new(hn.outputs[0], nh.inputs[1])
    mx0 = nt.nodes.new("ShaderNodeMath"); mx0.operation = 'MAXIMUM'; mx0.inputs[1].default_value = 0; nt.links.new(nh.outputs["Value"], mx0.inputs[0])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 48; nt.links.new(mx0.outputs[0], pw.inputs[0])
    sp = nt.nodes.new("ShaderNodeMath"); sp.operation = 'MULTIPLY'; sp.inputs[1].default_value = spec; nt.links.new(pw.outputs[0], sp.inputs[0])
    # painted env map read by the reflection vector, fresnel-weighted
    tc = nt.nodes.new("ShaderNodeTexCoord"); et = nt.nodes.new("ShaderNodeTexEnvironment"); et.image = ENV
    nt.links.new(tc.outputs["Reflection"], et.inputs[0])
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
    fr = nt.nodes.new("ShaderNodeMapRange"); fr.inputs[3].default_value = 0.06; fr.inputs[4].default_value = env; nt.links.new(lw.outputs["Facing"], fr.inputs[0])
    ev = nt.nodes.new("ShaderNodeVectorMath"); ev.operation = 'SCALE'; nt.links.new(et.outputs[0], ev.inputs[0]); nt.links.new(fr.outputs[0], ev.inputs[3])
    if tint:
        tn = nt.nodes.new("ShaderNodeVectorMath"); tn.operation = 'MULTIPLY'; tn.inputs[1].default_value = tint
        nt.links.new(et.outputs[0], tn.inputs[0]); nt.links.new(tn.outputs[0], ev.inputs[0])
    a1 = nt.nodes.new("ShaderNodeVectorMath"); a1.operation = 'ADD'; nt.links.new(sh.outputs[0], a1.inputs[0]); nt.links.new(ev.outputs[0], a1.inputs[1])
    a2 = nt.nodes.new("ShaderNodeVectorMath"); a2.operation = 'ADD'; nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(sp.outputs[0], a2.inputs[1])
    cs = a2.outputs[0]
    if emissive:
        e = nt.nodes.new("ShaderNodeVectorMath"); e.operation = 'MULTIPLY_ADD'; e.inputs[1].default_value = (emissive,) * 3
        nt.links.new(base, e.inputs[0]); nt.links.new(cs, e.inputs[2]); cs = e.outputs[0]
    cs = fog_mix(nt, cs, True)
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(cs, em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
SHINE = {"S2000_Paint_Body": dict(spec=.7, env=.45), "S2000_Paint_FormulaRed": dict(spec=.7, env=.45),
         "S2000_Glass": dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0)), "S2000_Glass_RearWindow": dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0)),
         "S2000_Lights_Atlas": dict(emissive=0.9, spec=.5, env=.2), "S2000_SoftTop_Fabric": dict(spec=.05, env=.04, amb=.6),
         "S2000_Tire": dict(spec=.05, env=.03), "S2000_Trim_Black": dict(spec=.3, env=.12), "S2000_Silver": dict(spec=.8, env=.4),
         "S2000_Interior": dict(spec=.05, env=.03)}
for m in bpy.data.materials:
    if m.name in SHINE: fake_shine(m, **SHINE[m.name])
# blob shadow, headlight throw decal, lamp glow sprites (travel with the car)
def car_local(p): return root.matrix_world @ Vector(p)
bs = mesh_obj("BlobShadow", [quad((-2.45, -1.05, 0.012), (4.9, 0, 0), (0, 2.1, 0))], [decal("blob", "blob_shadow.png")], C_CAR, light=False); bs.parent = root
ht = mesh_obj("HeadlightThrow", [quad((2.0, 1.6, 0.014), (0, -3.2, 0), (9.0, 0, 0), (0, 1), (1, 0))], [decal("throw", "headlight_throw.png", 'ADD', 0.45)], C_CAR, light=False); ht.parent = root
gh = additive("glow_head", "glow_head.png", 1.1); gt = additive("glow_tail", "glow_tail.png", 1.4)
for y in (.58, -.58):
    b = billboard(f"HeadGlow_{y}", (0, 0, 0), .55, gh, C_CAR); b.parent = root; b.location = (2.0, y, .62)
    b = billboard(f"TailGlow_{y}", (0, 0, 0), .7, gt, C_CAR); b.parent = root; b.location = (-2.07, y * 1.05, .72)

# ------------------------------------------------------------------ render setup
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("Tgt", None); sc.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
cam.data.clip_start = .1; cam.data.clip_end = 400
for g in GLOWS:
    d = g.constraints.new('TRACK_TO'); d.target = cam; d.track_axis = 'TRACK_NEGATIVE_Y'; d.up_axis = 'UP_Z'
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = 640, 448; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
SHOTS = {  # name: cam loc, target, lens(mm)
    "hero_front34": ((-8.8, 0.9, 1.25), (0.4, -2.2, 0.85), 33),
    "rear34": ((5.6, 0.6, 1.45), (-1.0, -2.4, 0.85), 26),
    "establishing": ((15.5, 0.4, 6.2), (-5.0, -1.2, 1.0), 24),
}
def tris():
    n = 0
    for o in bpy.data.objects:
        if o.type == 'MESH': n += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return n
print("TOKYO_TRIANGLES", tris())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "tokyo_s2000_v2.blend"), relative_remap=True)
if "--no-render" not in ARGS:
    vl = sc.view_layers[0]
    for name, (loc, tg, lens) in SHOTS.items():
        if "--only" in ARGS and name not in ARGS: continue
        cam.location = loc; tgt.location = tg; cam.data.lens = lens
        for lc in vl.layer_collection.children: lc.holdout = False
        sc.render.film_transparent = False
        sc.render.filepath = os.path.join(RD, f"raw_{name}.png"); bpy.ops.render.render(write_still=True)
        # neon-only pass for bloom: everything except Neon/glows held out
        for lc in vl.layer_collection.children: lc.holdout = lc.name not in ("Neon",)
        sc.render.film_transparent = True
        sc.render.filepath = os.path.join(RD, f"neon_{name}.png"); sc.render.image_settings.color_mode = 'RGBA'
        bpy.ops.render.render(write_still=True); sc.render.image_settings.color_mode = 'RGB'
