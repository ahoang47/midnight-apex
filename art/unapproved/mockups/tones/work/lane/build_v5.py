"""Midnight Apex lane-chain mockup v4 — entry (rear chase) and apex (low trackside) shots.
Scene is laid out from the asset packs in /workspace/asset_packs (URBAN road_4 tiles, street lights, Jersey/Type-3
barriers, bollards, cones, prebuilt flats, Kenney/industrial fronts, 3dretroshacks sheds + chainlink, PSX tree packs),
with the packs' own textures (nearest filtering). Everything is unlit in the Tokyo v2 manner:
texture x vertex colour (painted light, half-scale x2) -> linear fog -> emission; sodium pools are vertex light plus a
stepped decal; glow sprites; cars use the A.4 faked shine (ambient + 1 key + Blinn + painted env x fresnel).
EEVEE Next 640x480, 1 sample, filter 0, Standard view; post_v5.py does bloom(glows only) -> HUD -> RGB555 + Bayer -> 2x.
Usage: blender -b -P build_v5.py -- entry|apex   (v5: lamp glows cull when the lamp faces away; apex framing fits both cars)"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, 'tex'); RAW = os.path.join(HERE, 'raw'); os.makedirs(RAW, exist_ok=True)
SHOT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'entry'
AP = '/workspace/asset_packs/'; U = AP + 'psx-style-urban-stacked-pack/x/URBAN/'
KEN = AP + 'retro-urban-kit/x/Models/GLB format/'; IND = AP + 'ps1-style-industrial-buildings/x/exports/'
SHK = AP + '3dretroshacks/x/'; NAT = AP + 'retro-psx-nature-pack/x/retro_nature_pack/models/glTF/'
UTR = AP + 'ultimate-retro-psx-tree-pack/x/ultimate_retro_tree_pack/glb/'
CARS = '/workspace/midnight-apex/assets/cars/'
R = random.Random(4)
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c): return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
FOG = lin(hx('#261F38')); FOG_NEAR, FOG_FAR = 16.0, 150.0
AMB = hx('#8E90B4'); SOD = hx('#FF9947')
sys.path.insert(0, os.path.join(HERE, '..')); from tones import TONES      # tone presets (mockups/tones/work/tones.py)
TONE = os.environ.get('TONE', 'sodium'); T = TONES[TONE]
FOG = lin(hx(T['fog'])); AMB = hx(T['amb']); LAMPC = [hx(c) for c in T['lamps']]; SOD = LAMPC[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def coll(n): c = bpy.data.collections.new(n); sc.collection.children.link(c); return c
C_WORLD, C_NEON, C_CAR, C_SKY = coll('World'), coll('Neon'), coll('Car'), coll('Sky')

# ------------------------------------------------------------------ track geometry (road_4 long corner, radius 18)
CX, CY, RAD = 18.0, 0.0, 18.0          # right-hand 90 deg corner: entry (0,0) heading +Y, exit (18,18) heading +X
LINE = {'OUT': -3.2, 'MID': 0.0, 'IN': 3.2}   # lateral offset to the right of travel
def track(s, off=0.0):
    """s<0: approach straight, 0..pi/2*R: arc, beyond: exit straight. Returns pos, heading."""
    La = math.pi / 2 * RAD
    if s < 0: return Vector((off, s, 0)), Vector((0, 1, 0))
    if s <= La:
        phi = math.pi - s / RAD; h = Vector((math.sin(phi), -math.cos(phi), 0))
        r = RAD - off; return Vector((CX + r * math.cos(phi), CY + r * math.sin(phi), 0)), h
    d = s - La; return Vector((CX + d, RAD - off, 0)), Vector((1, 0, 0))

# ------------------------------------------------------------------ asset loading
IMPORTED = []
def _bake(objs, origin, rotz, scale, loc, coll_):
    out = []
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rotz, 4, 'Z') @ Matrix.Scale(scale, 4) @ Matrix.Translation(-Vector(origin))
    for o in objs:
        if o.type != 'MESH': continue
        o.data = o.data.copy(); o.data.transform(M @ o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
        for c in list(o.users_collection): c.objects.unlink(o)
        coll_.objects.link(o); out.append(o)
    return out
IMG_INDEX = {}
for dp, dn, fn in os.walk(AP):
    for f in fn:
        if f.lower().endswith(('.png', '.jpg', '.jpeg')): IMG_INDEX.setdefault(f.lower(), os.path.join(dp, f))
def fix_images(meshes, tex_override=None):
    """Relink pack textures whose paths point at the author's machine; give untextured meshes their pack texture."""
    for o in meshes:
        if tex_override and not any(m and m.node_tree and any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes) for m in o.data.materials):
            m = bpy.data.materials.new('pack_' + os.path.basename(tex_override)); m.use_nodes = True
            t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(tex_override, check_existing=True)
            m.node_tree.links.new(t.outputs[1], m.node_tree.nodes['Principled BSDF'].inputs['Alpha']); m.blend_method = 'CLIP'
            o.data.materials.clear(); o.data.materials.append(m)
        for m in o.data.materials:
            if not (m and m.node_tree): continue
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image and not n.image.packed_file and not os.path.exists(bpy.path.abspath(n.image.filepath)):
                    b = os.path.basename(n.image.filepath.replace('\\', '/')).lower()
                    p = IMG_INDEX.get(b) or (IMG_INDEX['shed corrugated texture.png'] if 'corrugated' in b else None)
                    if p: n.image = bpy.data.images.load(p, check_existing=True)
def load(path, loc=(0, 0, 0), rotz=0.0, scale=1.0, origin='bbox', coll_=None, subdiv=0, tex_override=None):
    """Import a pack model; origin='bbox' puts its footprint centre / base at loc, or pass an explicit point."""
    coll_ = coll_ or C_WORLD; before = set(bpy.data.objects)
    if path.endswith('.glb'): bpy.ops.import_scene.gltf(filepath=path)
    else:
        with bpy.data.libraries.load(path) as (src, dst): dst.objects = list(src.objects)
        for o in dst.objects:
            if o: sc.collection.objects.link(o)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == 'MESH']
    fix_images(meshes, tex_override)
    if origin == 'bbox':
        vs = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
        origin = ((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, min(v.z for v in vs))
    out = _bake(meshes, origin, rotz, scale, loc, coll_)
    for o in new:
        if o not in out: bpy.data.objects.remove(o, do_unlink=True)
    if subdiv:
        for o in out:
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=subdiv, use_grid_fill=True); bm.to_mesh(o.data); bm.free()
    IMPORTED.extend(out); return out
def yaw(h): return math.atan2(h.y, h.x)

# ---- road: road_4 tiles (16 x 16 m, 2-lane carriageway ~10 m + sidewalks); long corner rotated -90 deg so it turns right
for k in range(7): load(U + 'Roads/Road type 4/road_4_straight.glb', (0, -8 - 16 * k, 0), 0, subdiv=3)
load(U + 'Roads/Road type 4/road_4_long_corner.glb', (5, 13, 0), -math.pi / 2, subdiv=4)
for k in range(5): load(U + 'Roads/Road type 4/road_4_straight.glb', (26 + 16 * k, 18, 0), math.pi / 2, subdiv=3)
# ground beyond the sidewalks (pack sidewalk texture, nearest) so nothing reads as void
GROUND = load(IND + 'Road.glb', (10, 10, -0.02), 0, scale=100)   # 4 m tile scaled; UVs re-tiled below
for o in GROUND:
    for lp in o.data.loops:
        uv = o.data.uv_layers[0].data[lp.index].uv; uv[0] *= 60; uv[1] *= 60

# ---- street lights (URBAN street_light: pole base at (9.65,12.65), head 1.7 m out along +x at z 6.4)
LAMPS = []
def streetlight(p, face):       # face = unit vector from pole toward the road
    a = math.atan2(face.y, face.x)
    load(U + 'Traffic lights/street_light.glb', p, a, origin=(9.65, 12.65, 0))
    head = Vector(p) + Vector((math.cos(a), math.sin(a), 0)) * 1.7 + Vector((0, 0, 6.35)); LAMPS.append(head); return head
for y in (-100, -76, -52, -28, -6):
    streetlight((-5.8, y, 0.3), Vector((1, 0, 0)))
for y in (-88, -64, -40, -16):
    streetlight((5.8, y, 0.3), Vector((-1, 0, 0)))
for ang in (150, 118, 90 + 2):  # outside of the arc
    a = math.radians(ang); p = Vector((CX + 23.6 * math.cos(a), CY + 23.6 * math.sin(a), 0.3)); streetlight(p, (Vector((CX, CY, 0.3)) - p).normalized())
for x in (32, 56, 80): streetlight((x, 23.8, 0.3), Vector((0, -1, 0)))
for x in (44, 68): streetlight((x, 12.2, 0.3), Vector((0, 1, 0)))

# ---- outside of the corner: Jersey barriers on the sidewalk edge, chainlink behind, Type 3 warning barricades
def along_arc(r, a0, a1, step):
    n = max(1, int(abs(a1 - a0) * r / step)); return [a0 + (a1 - a0) * i / n for i in range(n + 1)]
for a in along_arc(26.4, math.radians(185), math.radians(87), 2.55):
    p = (CX + 26.4 * math.cos(a), CY + 26.4 * math.sin(a), 0.3)
    load(U + 'Cones & Barriers/Concrete Barriers/Jersey_barrier' + ('_dirty' if R.random() < .4 else '') + '.glb', p, a + math.pi / 2)
for y in range(-60, -4, 3): load(U + 'Cones & Barriers/Concrete Barriers/Jersey_barrier' + ('_dirty' if R.random() < .4 else '') + '.glb', (-8.4, y, .3), math.pi / 2)
for a in along_arc(28.6, math.radians(190), math.radians(84), 2.4):
    p = (CX + 28.6 * math.cos(a), CY + 28.6 * math.sin(a), 0.0)
    load(SHK + 'Chainlink Fence.blend', p, a - math.pi / 2, origin=(1.2, 0, 0))
for a in (math.radians(168), math.radians(150), math.radians(132), math.radians(114)):   # striped barricades = corner warning
    p = (CX + 25.2 * math.cos(a), CY + 25.2 * math.sin(a), 0.3)
    load(U + 'Cones & Barriers/Type 3 Barriers/Type_3_barrier_3_planks.glb', p, a + math.pi / 2)
for a in along_arc(25.0, math.radians(176), math.radians(96), 2.2):   # Kenney yellow/black hazard boards in front of them
    if any(abs(a - math.radians(t)) < .05 for t in (168, 150, 132, 114)): continue
    load(KEN + 'detail-barrier-type-a.glb', (CX + 25.0 * math.cos(a), CY + 25.0 * math.sin(a), 0.3), a + math.pi / 2, 3.4)
# inside kerb at the apex: reflector bollards + a few cones
CAM_PHI = float(os.environ.get('CAM_PHI', 122))
for a in along_arc(11.2, math.radians(172), math.radians(98), 3.2):
    if SHOT == 'apex' and abs(math.degrees(a) - CAM_PHI) < 9: continue
    load(U + 'Cones & Barriers/Bollards/square_bollard_reflectors.glb', (CX + 11.2 * math.cos(a), CY + 11.2 * math.sin(a), 0.3), a)
for (x, y) in ((6.2, -3.0), (6.6, -4.4), (7.1, -2.0)):
    load(U + 'Cones & Barriers/Cones/Traffic_cone_round.glb', (x, y, 0.3), R.uniform(0, 3))

# ---- buildings / yards
# outside: industrial yard behind the fence, flats further back (they carry the skyline in the rear view)
load(SHK + 'Large Shed A.blend', (-4, 37, 0), math.radians(30)); load(SHK + 'Large Shed B.blend', (10, 43, 0), math.radians(5))
load(SHK + 'Shack A.blend', (-16, 26, 0), math.radians(60)); load(SHK + 'Leanto B.blend', (-14, 16, 0), math.radians(80))
for i, x in enumerate((-30, -10, 14, 38)):
    load(U + 'Buildings Prebuild/' + ['flat_square_concrete', 'flat_Lshape', 'flat_square_brick', 'flat_Lshape_large_alt'][i] + '.glb', (x, 72 + (i % 2) * 10, 0), math.radians(R.choice((0, 90, 180))))
for i, y in enumerate(range(-96, -10, 14)):   # left of the approach: industrial / brick fronts behind the barrier
    load(IND + ('IndustrialBuilding.glb' if i % 2 else 'BrickBuilding.glb'), (-12.5, y, 0), -math.pi / 2)
    load(U + 'Buildings Prebuild/flat_square_brick_alt.glb' if i == 3 else IND + 'BrickBuilding.glb', (-12.6, y + 7, 0) if i != 3 else (-26, y, 0), -math.pi / 2)
# inside of the corner: hangar + low block, trees
load(U + 'Buildings Prebuild/Hangar1.glb', (19, 4.5, 0.0), math.radians(90))
for i, y in enumerate(range(-100, -40, 16)):
    load(U + 'Buildings Prebuild/' + ('flat_square_concrete_alt' if i % 2 else 'flat_square_brick') + '.glb', (19, y, 0), math.radians(90 * (i % 4)))
for i, x in enumerate(range(34, 100, 18)):
    load(U + 'Buildings Prebuild/' + ('flat_Lshape' if i % 2 else 'flat_square_concrete') + '.glb', (x, 36, 0), math.radians(180))
    load(U + 'Buildings Prebuild/flat_square_brick.glb', (x + 4, 0, 0), 0)
# trees: PSX tree pack + nature pack, dense cheap clumps
NTX = AP + 'retro-psx-nature-pack/x/retro_nature_pack/textures/'
TREES = [(UTR + f'tree{n:03d}.glb', None) for n in (64, 64, 100, 12, 1, 64)] + [(NAT + f'trees/tree0{n}.glb', NTX + f'trees/tree0{n}_summer.png') for n in (1, 4, 7)]
def tree(p, s_):
    f, t = R.choice(TREES); return load(f, p, R.uniform(0, 6), s_, tex_override=t)
def bush(p, s_=1.0):
    n = R.choice((1, 2, 3, 5)); return load(NAT + f'bushes/bush0{n}.glb', p, R.uniform(0, 6), s_, tex_override=NTX + f'bushes/bush{n}_summer.png' if os.path.exists(NTX + f'bushes/bush{n}_summer.png') else None)
for a in along_arc(31, math.radians(200), math.radians(80), 3.4):
    tree((CX + 31 * math.cos(a) + R.uniform(-1, 1), CY + 31 * math.sin(a) + R.uniform(-1, 1), 0), R.uniform(1.4, 2.2))
for (x, y) in ((24, 11.5), (27, 9), (22, 7)): tree((x, y, 0.3), R.uniform(1.3, 1.9))
for (x, y) in ((9.5, 4), (10.2, 7.5), (9.2, -1), (9.4, -7)): bush((x, y, 0.3), R.uniform(.9, 1.3))
for y in range(-70, -26, 9): tree((9.5, y, 0.3), R.uniform(1.4, 2.0))

# ------------------------------------------------------------------ unlit materials + painted vertex light
IMGS = {}
def img(n):
    if n not in IMGS: IMGS[n] = bpy.data.images.load(os.path.join(TEX, n))
    return IMGS[n]
def fog_mix(nt, cs):
    cam = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.clamp = True
    mr.inputs[1].default_value, mr.inputs[2].default_value = FOG_NEAR, FOG_FAR; nt.links.new(cam.outputs['View Z Depth'], mr.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(mr.outputs[0], mx.inputs['Factor']); nt.links.new(cs, mx.inputs[6])
    mx.inputs[7].default_value = (*FOG, 1); return mx.outputs[2]
UNLIT = {}
def unlit_from(m):
    if m.name in UNLIT: return UNLIT[m.name]
    nt0 = m.node_tree if m.use_nodes else None
    tex = next((n for n in nt0.nodes if n.type == 'TEX_IMAGE' and n.image), None) if nt0 else None
    bsdf = next((n for n in nt0.nodes if n.type == 'BSDF_PRINCIPLED'), None) if nt0 else None
    alpha = bool(bsdf and bsdf.inputs['Alpha'].is_linked) or (tex is not None and m.blend_method in ('CLIP', 'BLEND', 'HASHED')) \
        or (tex is not None and any(k in m.name.lower() for k in ('tree', 'leaf', 'chain', 'fence', 'bush', 'grass')))
    base_col = bsdf.inputs['Base Color'].default_value[:] if bsdf else (.5, .5, .5, 1)
    n = bpy.data.materials.new('U_' + m.name); n.use_nodes = True; nt = n.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex.image; t.interpolation = 'Closest'
        uvn = nt.nodes.new('ShaderNodeUVMap'); nt.links.new(uvn.outputs[0], t.inputs[0])
        # keep any UV mapping node the importer added (Kenney/URBAN use plain UVs)
        cs = t.outputs[0]; asock = t.outputs[1]
    else:
        c = nt.nodes.new('ShaderNodeRGB'); c.outputs[0].default_value = base_col; cs = c.outputs[0]; asock = None
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(cs, mul.inputs[6]); nt.links.new(vc.outputs[0], mul.inputs[7])
    x2 = nt.nodes.new('ShaderNodeVectorMath'); x2.operation = 'SCALE'; x2.inputs[3].default_value = 2.0; nt.links.new(mul.outputs[2], x2.inputs[0])
    cs = fog_mix(nt, x2.outputs[0]); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cs, em.inputs[0])
    if alpha and asock is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
        nt.links.new(asock, gt.inputs[0]); nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs[0]); n.surface_render_method = 'DITHERED'
    else: nt.links.new(em.outputs[0], out.inputs[0])
    n.use_backface_culling = False; UNLIT[m.name] = n; return n
def vlight(p, nrm):
    """painted night light: cool ambient (darker with height) + stepped sodium pools from every lamp head."""
    k = 0.19 + 0.05 * max(0.0, nrm.z)
    k *= max(0.45, 1.0 - max(0.0, p.z - 3.0) / 25.0) * T['amb_k']
    if nrm.z > .7 and p.z < .5: k *= T['ground_k']          # rain: darker, wet-looking ground
    c = [AMB[i] * k for i in range(3)]
    for li, L in enumerate(LAMPS):
        d = (p - L).length; lv = max(0.0, 1 - d / 13.0); lv = math.floor(lv * T['steps']) / T['steps']
        lc = LAMPC[li % len(LAMPC)]
        gk = T.get('lane_ground_lamp', 1.0) if nrm.z > .7 else 1.0     # blends: ground pools mostly from the hard decal, road stays navy
        for i in range(3): c[i] += lc[i] * lv * T['lamp_k'] * gk
    return tuple(min(1.0, x * 0.5) for x in c) + (1.0,)
def paint(o):
    me = o.data
    if 'Col' in me.color_attributes: me.color_attributes.remove(me.color_attributes['Col'])
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index]; ca.data[li].color = vlight(v.co, poly.normal)
    for i, m in enumerate(me.materials):
        if m: me.materials[i] = unlit_from(m)
    if not me.materials: me.materials.append(unlit_from(bpy.data.materials.new('plain')))
for o in IMPORTED: paint(o)

# ------------------------------------------------------------------ decals, glows, sky
def additive(name, tex, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex); t.extension = 'CLIP'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'SCALE'; nt.links.new(t.outputs[0], mul.inputs[0]); nt.links.new(t.outputs[1], mul.inputs[3])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value = strength; nt.links.new(mul.outputs[0], em.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs[0])
    m.surface_render_method = 'BLENDED'; return m
def darken(name, tex):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex); t.extension = 'CLIP'
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (0, 0, 0, 1)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(t.outputs[1], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0]); m.surface_render_method = 'BLENDED'; return m
def quad_obj(name, corners, uvs, mat, coll_):
    me = bpy.data.meshes.new(name); me.from_pydata([Vector(c) for c in corners], [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new(); [setattr(uv.data[i], 'uv', uvs[i]) for i in range(4)]
    o = bpy.data.objects.new(name, me); coll_.objects.link(o); me.materials.append(mat); return o
GLOWS = []
def billboard(name, p, size, mat, coll_=C_NEON, parent=None):
    s = size / 2; o = quad_obj(name, [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)], [(0, 0), (1, 0), (1, 1), (0, 1)], mat, coll_)
    o.location = p
    if parent: o.parent = parent
    GLOWS.append(o); return o
pool_ms = [additive(f'pool{j}', f'pool_{TONE}_{j}.png', T['pool_k'] * T.get('lane_pool_mul', 1.0)) for j in range(len(LAMPC))]
if TONE != 'sodium':     # PS1 look: nearest-sampled pool decal so its bands are hard-edged
    for m in pool_ms:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE': n.interpolation = 'Closest'; glow_sods = [additive(f'glow_sodium{j}', f'glow_{TONE}_{j}.png', 0.9) for j in range(len(LAMPC))]
for i, L in enumerate(LAMPS):
    g = Vector((L.x, L.y, 0.175)); s = 6.5
    quad_obj(f'Pool_{i}', [g + Vector((-s, -s, 0)), g + Vector((s, -s, 0)), g + Vector((s, s, 0)), g + Vector((-s, s, 0))], [(0, 0), (1, 0), (1, 1), (0, 1)], pool_ms[i % len(LAMPC)], C_WORLD)
    billboard(f'LampGlow_{i}', L + Vector((0, 0, -0.15)), 1.5, glow_sods[i % len(LAMPC)])
def sky_unlit(name, tex, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex); t.extension = 'EXTEND'; t.interpolation = 'Closest'
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs[0], em.inputs[0])
    if alpha:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = .5; nt.links.new(t.outputs[1], gt.inputs[0])
        nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
        m.surface_render_method = 'DITHERED'
    else: nt.links.new(em.outputs[0], out.inputs[0])
    return m
sky_m = sky_unlit('sky', f'sky_{TONE}.png'); skl = [sky_unlit('skyA', 'skyline_a.png', True), sky_unlit('skyB', 'skyline_b.png', True)]
SC = Vector((10, 0, 0))
for i in range(12):   # ring of sky cards (fog-coloured horizon) + skyline cards with lit windows
    a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
    p0 = SC + Vector((math.cos(a0), math.sin(a0), 0)) * 330; p1 = SC + Vector((math.cos(a1), math.sin(a1), 0)) * 330
    quad_obj(f'Sky_{i}', [p0 + Vector((0, 0, -10)), p1 + Vector((0, 0, -10)), p1 + Vector((0, 0, 330)), p0 + Vector((0, 0, 330))], [(0, 0), (1, 0), (1, 1), (0, 1)], sky_m, C_SKY)
    for j, (rr, hh) in enumerate(((260, 70), (215, 46))):
        q0 = SC + Vector((math.cos(a0 + j * .2), math.sin(a0 + j * .2), 0)) * rr; q1 = SC + Vector((math.cos(a1 + j * .2), math.sin(a1 + j * .2), 0)) * rr
        u0 = (i * .37 + j * .5) % 1
        quad_obj(f'Skyline_{i}_{j}', [q0 + Vector((0, 0, -2)), q1 + Vector((0, 0, -2)), q1 + Vector((0, 0, hh)), q0 + Vector((0, 0, hh))], [(u0, 0), (u0 + .5, 0), (u0 + .5, 1), (u0, 1)], skl[(i + j) % 2], C_SKY)
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*FOG, 1)

# ------------------------------------------------------------------ cars (game .glb) with the A.4 faked shine
ENV = img('env_street.png')
def fake_shine(m, emissive=0.0, spec=0.6, env=0.45, amb=0.55, tint=None):
    nt = m.node_tree; bsdf = nt.nodes.get('Principled BSDF'); tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if tex is not None: tex.interpolation = 'Linear'; base = tex.outputs[0]
    else:
        c = nt.nodes.new('ShaderNodeRGB'); c.outputs[0].default_value = bsdf.inputs['Base Color'].default_value if bsdf else (.5, .5, .5, 1); base = c.outputs[0]
    for n in list(nt.nodes):
        if n.type not in ('TEX_IMAGE', 'UVMAP', 'RGB', 'MAPPING', 'TEX_COORD'): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); geo = nt.nodes.new('ShaderNodeNewGeometry')
    key = nt.nodes.new('ShaderNodeCombineXYZ'); kv = Vector((-0.35, 0.45, 0.82)).normalized()
    key.inputs[0].default_value, key.inputs[1].default_value, key.inputs[2].default_value = kv
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(key.outputs[0], dot.inputs[1])
    dif = nt.nodes.new('ShaderNodeMapRange'); dif.clamp = True; dif.inputs[3].default_value = amb; dif.inputs[4].default_value = 1.0; nt.links.new(dot.outputs['Value'], dif.inputs[0])
    sh = nt.nodes.new('ShaderNodeVectorMath'); sh.operation = 'SCALE'; nt.links.new(base, sh.inputs[0]); nt.links.new(dif.outputs[0], sh.inputs[3])
    hv = nt.nodes.new('ShaderNodeVectorMath'); hv.operation = 'ADD'; nt.links.new(key.outputs[0], hv.inputs[0]); nt.links.new(geo.outputs['Incoming'], hv.inputs[1])
    hn = nt.nodes.new('ShaderNodeVectorMath'); hn.operation = 'NORMALIZE'; nt.links.new(hv.outputs[0], hn.inputs[0])
    nh = nt.nodes.new('ShaderNodeVectorMath'); nh.operation = 'DOT_PRODUCT'; nt.links.new(geo.outputs['Normal'], nh.inputs[0]); nt.links.new(hn.outputs[0], nh.inputs[1])
    mx0 = nt.nodes.new('ShaderNodeMath'); mx0.operation = 'MAXIMUM'; mx0.inputs[1].default_value = 0; nt.links.new(nh.outputs['Value'], mx0.inputs[0])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 48; nt.links.new(mx0.outputs[0], pw.inputs[0])
    sp = nt.nodes.new('ShaderNodeMath'); sp.operation = 'MULTIPLY'; sp.inputs[1].default_value = spec; nt.links.new(pw.outputs[0], sp.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); et = nt.nodes.new('ShaderNodeTexEnvironment'); et.image = ENV; nt.links.new(tc.outputs['Reflection'], et.inputs[0])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.35
    fr = nt.nodes.new('ShaderNodeMapRange'); fr.inputs[3].default_value = 0.06; fr.inputs[4].default_value = env; nt.links.new(lw.outputs['Facing'], fr.inputs[0])
    ev = nt.nodes.new('ShaderNodeVectorMath'); ev.operation = 'SCALE'; nt.links.new(et.outputs[0], ev.inputs[0]); nt.links.new(fr.outputs[0], ev.inputs[3])
    if tint:
        tn = nt.nodes.new('ShaderNodeVectorMath'); tn.operation = 'MULTIPLY'; tn.inputs[1].default_value = tint; nt.links.new(et.outputs[0], tn.inputs[0]); nt.links.new(tn.outputs[0], ev.inputs[0])
    a1 = nt.nodes.new('ShaderNodeVectorMath'); a1.operation = 'ADD'; nt.links.new(sh.outputs[0], a1.inputs[0]); nt.links.new(ev.outputs[0], a1.inputs[1])
    a2 = nt.nodes.new('ShaderNodeVectorMath'); a2.operation = 'ADD'; nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(sp.outputs[0], a2.inputs[1])
    cs = a2.outputs[0]
    if emissive:
        e = nt.nodes.new('ShaderNodeVectorMath'); e.operation = 'MULTIPLY_ADD'; e.inputs[1].default_value = (emissive,) * 3; nt.links.new(base, e.inputs[0]); nt.links.new(cs, e.inputs[2]); cs = e.outputs[0]
    cs = fog_mix(nt, cs); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cs, em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
blob_m = darken('blob', 'blob_shadow.png'); throw_m = additive('throw', 'headlight_throw.png', 0.40)
gh = additive('glow_head', 'glow_head.png', 0.8); gt = additive('glow_tail', 'glow_tail.png', 1.5)
def car(glb, root_name, prefix, s, off, head, tail, shine):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        C_CAR.objects.link(o)
        if '_FX_' in o.name: o.hide_render = True
    for m in {m for o in new if o.type == 'MESH' for m in o.data.materials if m}:
        for k, kw in shine.items():
            if m.name.startswith(prefix + k): fake_shine(m, **kw)
    root = bpy.data.objects[root_name]; p, h = track(s, off)
    root.rotation_mode = 'XYZ'; root.location = p + Vector((0, 0, 0.16)); root.rotation_euler = (0, 0, yaw(h) + math.pi / 2)
    b = quad_obj(prefix + 'Blob', [(-1.15, -2.6, .012), (1.15, -2.6, .012), (1.15, 2.6, .012), (-1.15, 2.6, .012)], [(0, 1), (0, 0), (1, 0), (1, 1)], blob_m, C_CAR); b.parent = root
    t = quad_obj(prefix + 'Throw', [(-1.7, -2.2, .016), (1.7, -2.2, .016), (1.7, -11.5, .016), (-1.7, -11.5, .016)], [(0, 1), (1, 1), (1, 0), (0, 0)], throw_m, C_CAR); t.parent = root
    for sx in (1, -1):
        bh = billboard(prefix + f'Head{sx}', (sx * head[0], head[1], head[2]), .42, gh, C_CAR, root); bh['face'] = (0, -1, 0)
        bt = billboard(prefix + f'Tail{sx}', (sx * tail[0], tail[1], tail[2]), .75, gt, C_CAR, root); bt['face'] = (0, 1, 0)
    return root
PAINT = dict(spec=.55, env=.22, amb=.5, tint=(.80, .86, 1.0)); GLASS = dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0))
if SHOT == 'entry':
    P_S, P_L, O_S, O_L = -16.0, 'OUT', -6.5, 'IN'
else:
    P_S, P_L, O_S, O_L = math.pi / 4 * RAD - 1.5, 'IN', math.pi / 4 * RAD - 0.8, 'OUT'
player = car(CARS + 'gr_corolla/car_gr_corolla.glb', 'GRC-vehicle', 'GRC_', P_S, LINE[P_L], (.60, -2.12, .68), (.64, 1.99, .88),
             {'Paint': PAINT, 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})
rival = car(CARS + 'wrx_sti/car_wrx_sti.glb', 'WRX-vehicle', 'WRX_', O_S, LINE[O_L], (.62, -2.1, .70), (.66, 2.12, .86),
            {'Paint': dict(spec=.55, env=.28, amb=.5, tint=(.8, .86, 1.0)), 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})

# ------------------------------------------------------------------ camera
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = .1; cam.data.clip_end = 500; cam.rotation_mode = 'XYZ'
def look(loc, tgt, lens, roll=0.0):
    cam.location = loc; cam.data.lens = lens
    q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y'); cam.rotation_euler = (q @ Matrix.Rotation(roll, 4, 'Z').to_quaternion()).to_euler()
if SHOT == 'entry':
    pp, ph = track(P_S, LINE[P_L])
    look(pp - ph * 7.6 + Vector((1.4, 0, 3.1)), pp + ph * 22 + Vector((3.6, 0, -0.9)), 25)
else:
    a = math.radians(CAM_PHI); cl = Vector((CX + 12.9 * math.cos(a), CY + 12.9 * math.sin(a), 0.5))
    pp, ph = track(P_S, LINE[P_L]); rp, _ = track(O_S, LINE[O_L])
    look(cl, (pp * 0.62 + rp * 0.38) + Vector((0, 0, 0.55)), float(os.environ.get('APEX_LENS', 17)), math.radians(-8))
bpy.context.view_layer.update()
for g in GLOWS:   # a lamp sprite only shows when its lamp faces the camera (no glow leaking around the body)
    if 'face' in g:
        f = (g.parent.matrix_world.to_3x3() @ Vector(g['face'])).normalized(); w = g.matrix_world.translation
        if f.dot((cam.location - w).normalized()) < 0.15: g.hide_render = True
for g in GLOWS:
    c = g.constraints.new('TRACK_TO'); c.target = cam; c.track_axis = 'TRACK_NEGATIVE_Y'; c.up_axis = 'UP_Z'
bpy.context.view_layer.update()
# screen anchors for the HUD (post_v5.py)
def scr(p):
    v = world_to_camera_view(sc, cam, Vector(p)); return [v.x * 640, (1 - v.y) * 480, v.z]
anch = {'lanes': {k: scr(track(0.0, o)[0] + Vector((0, 0, 1.6))) for k, o in LINE.items()},
        'lanes_ground': {k: scr(track(0.0, o)[0] + Vector((0, 0, .2))) for k, o in LINE.items()},
        'player': scr(player.location + Vector((0, 0, 1.6))), 'rival': scr(rival.location + Vector((0, 0, 1.7)))}
json.dump(anch, open(os.path.join(RAW, f'anchors_{SHOT}.json'), 'w'), indent=1)
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)
print('TRIANGLES', tri)

# ------------------------------------------------------------------ render (base + glow-only pass for bloom)
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = 640, 480; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
vl = sc.view_layers[0]
sc.render.filepath = os.path.join(RAW, f'raw_{SHOT}_{TONE}.png'); bpy.ops.render.render(write_still=True)
neon_names = {o.name for o in GLOWS}
hidden = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name not in neon_names and not o.hide_render:
        o.is_holdout = True; hidden.append(o)
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = os.path.join(RAW, f'glow_{SHOT}_{TONE}.png'); bpy.ops.render.render(write_still=True)
print('DONE', SHOT)
