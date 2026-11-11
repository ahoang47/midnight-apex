"""Midnight Apex overworld free-roam mockup v1 (Racing Lagoon-style high overhead perspective camera, ~57 deg down).
Same pipeline as lane_chain/v5: pack models + pack textures (nearest), unlit texture x painted vertex light -> linear fog
-> emission, stepped sodium pools, glow sprites, blob shadows; cars use the A.4 faked shine. Pack building windows get
a per-face 'Lit' attribute that swaps in a lit-glass variant of the pack atlas (tex/houses_lit.png).
EEVEE Next 640x480, 1 sample, filter 0, Standard view; post_ow.py: bloom (glows only) -> HUD -> RGB555 + Bayer -> 2x.
Usage: blender -b -P build_ow.py"""
import bpy, bmesh, math, os, sys, json, random, zlib
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, 'tex'); RAW = os.path.join(HERE, 'raw'); os.makedirs(RAW, exist_ok=True)
SHOT = 'overworld'
AP = '/workspace/asset_packs/'; U = AP + 'psx-style-urban-stacked-pack/x/URBAN/'
KEN = AP + 'retro-urban-kit/x/Models/GLB format/'; IND = AP + 'ps1-style-industrial-buildings/x/exports/'
SHK = AP + '3dretroshacks/x/'; NAT = AP + 'retro-psx-nature-pack/x/retro_nature_pack/models/glTF/'
UTR = AP + 'ultimate-retro-psx-tree-pack/x/ultimate_retro_tree_pack/glb/'
CARS = '/workspace/midnight-apex/assets/cars/'
R = random.Random(4)
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c): return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
FOG = lin(hx('#261F38')); FOG_NEAR, FOG_FAR = 95.0, 235.0
AMB = hx('#8E90B4'); SOD = hx('#FF9947')
sys.path.insert(0, os.path.join(HERE, '..')); from tones import TONES      # tone presets (mockups/tones/work/tones.py)
TONE = os.environ.get('TONE', 'sodium'); T = TONES[TONE]
FOG = lin(hx(T['fog'])); AMB = hx(T['amb']); LAMPC = [hx(c) for c in T['lamps']]; SOD = LAMPC[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def coll(n): c = bpy.data.collections.new(n); sc.collection.children.link(c); return c
C_WORLD, C_NEON, C_CAR, C_SKY = coll('World'), coll('Neon'), coll('Car'), coll('Sky')

# ------------------------------------------------------------------ asset loading
IMPORTED = []
def _bake(objs, origin, rotz, scale, loc, coll_):
    out = []
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rotz, 4, 'Z') @ (Matrix.Diagonal((*scale, 1)) if isinstance(scale, tuple) else Matrix.Scale(scale, 4)) @ Matrix.Translation(-Vector(origin))
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
# ---- street lights (URBAN street_light: pole base at (9.65,12.65), head 1.7 m out along +x at z 6.4)
LAMPS = []
def streetlight(p, face):       # face = unit vector from pole toward the road
    a = math.atan2(face.y, face.x)
    load(U + 'Traffic lights/street_light.glb', p, a, origin=(9.65, 12.65, 0))
    head = Vector(p) + Vector((math.cos(a), math.sin(a), 0)) * 1.7 + Vector((0, 0, 6.35)); LAMPS.append(head); return head
NTX = AP + 'retro-psx-nature-pack/x/retro_nature_pack/textures/'
TREES = [(UTR + f'tree{n:03d}.glb', None) for n in (64, 64, 100, 12, 1, 64)] + [(NAT + f'trees/tree0{n}.glb', NTX + f'trees/tree0{n}_summer.png') for n in (1, 4, 7)]
def tree(p, s_):
    f, t = R.choice(TREES); return load(f, p, R.uniform(0, 6), s_, tex_override=t)
def bush(p, s_=1.0):
    n = R.choice((1, 2, 3, 5)); return load(NAT + f'bushes/bush0{n}.glb', p, R.uniform(0, 6), s_, tex_override=NTX + f'bushes/bush{n}_summer.png' if os.path.exists(NTX + f'bushes/bush{n}_summer.png') else None)
# ------------------------------------------------------------------ street grid from URBAN road_4 tiles (16 x 16 m)
RD = U + 'Roads/Road type 4/'; H90 = math.pi / 2
def tile(n, x, y, rot=0.0, sub=2): load(RD + n + '.glb', (x, y, 0), rot, subdiv=sub)
for x in (-80, -64, -32, -16, 16, 32, 64, 80, 96): tile('road_4_straight', x, 0, H90)      # main street, E-W
tile('road_4_junction', 0, 0); tile('road_4_Tjunction', -48, 0, 0); tile('road_4_Tjunction', 48, 0, math.pi)
for y in (-64, -48, -32, -16, 16, 32, 48, 64): tile('road_4_straight', 0, y)               # cross street, N-S
for y in (-16, -32, -48, -64): tile('road_4_straight', -48, y)                            # side street south
for y in (16, 32, 48): tile('road_4_straight', 48, y)                                     # side street north ...
tile('road_4_corner', 48, 64, 0)                                                          # ... turning east
for x in (64, 80, 96): tile('road_4_straight', x, 64, H90)
load(RD + 'road_4_long_corner.glb', (5, 85, 0), -H90, subdiv=3)                           # the cross street sweeps east
for x in (26, 42, 58, 74, 90): tile('road_4_straight', x, 90, H90)
ROADS = [[(-96, 0), (104, 0)], [(0, -72), (0, 72)] + [(18 - 18 * math.cos(a), 72 + 18 * math.sin(a)) for a in [i * math.pi / 16 for i in range(1, 9)]] + [(98, 90)],
         [(48, 0), (48, 64), (104, 64)], [(-48, 0), (-48, -72)]]
def plate(f, x0, x1, y0, y1, z, tile_m=4.0, step=2.0, tex=None):
    """a Kenney unit plane stretched over a rectangle, UVs re-tiled so the 64 px pack texture stays ~tile_m per repeat"""
    ob = load(KEN + f + '.glb', ((x0 + x1) / 2, (y0 + y1) / 2, z), 0, (x1 - x0, y1 - y0, 1))
    # rebuild as a grid (a vertex every ~step m) so the painted sodium pools land on it; UVs repeat the pack texture
    nx, ny = max(1, round((x1 - x0) / step)), max(1, round((y1 - y0) / step))
    for o in ob:
        mats = list(o.data.materials); uvs = [l.uv[:] for l in o.data.uv_layers[0].data]
        u0, u1 = min(u[0] for u in uvs), max(u[0] for u in uvs); v0, v1 = min(u[1] for u in uvs), max(u[1] for u in uvs)
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
        uvl = bm.loops.layers.uv.new('UVMap')
        for v in bm.verts: v.co = Vector((x0 + (v.co.x + .5) * (x1 - x0), y0 + (v.co.y + .5) * (y1 - y0), z))
        for fc in bm.faces:
            for l in fc.loops:
                l[uvl].uv = (u0 + (l.vert.co.x - x0) / tile_m * (u1 - u0), v0 + (l.vert.co.y - y0) / tile_m * (v1 - v0))
        me = bpy.data.meshes.new(o.name + '_grid'); bm.to_mesh(me); bm.free()
        if tex:     # same pack, different texture (e.g. concrete lot)
            mats = [m.copy() for m in mats]
            for m in mats:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE': n.image = bpy.data.images.load(tex if os.path.isabs(tex) else KEN + 'Textures/' + tex, check_existing=True)
        for m in mats: me.materials.append(m)
        o.data = me
    return ob
GROUND = plate('road-asphalt-center', -160, 180, -160, 200, -0.02, 5.0, 5.0)
BLOCKS = [(8, 40, 8, 74), (-130, -8, 8, 160), (-40, -8, -130, -8), (-130, -56, -130, -8), (8, 130, -130, -8), (56, 130, 8, 56), (26, 130, 98, 160)]
for b in BLOCKS: plate('road-asphalt-pavement', *b, .3, 3.0)
# ---- street lights along every street (both sides, staggered), traffic lights at the junction
def lamps_along(p0, p1, step=22, off=6.7, skip=()):
    a = Vector((*p0, 0)); b = Vector((*p1, 0)); d = (b - a); L = d.length; d.normalize(); n = Vector((-d.y, d.x, 0)); k = 0
    t = 6.0
    while t < L - 4:
        p = a + d * t; s = 1 if k % 2 == 0 else -1
        if not any((p - Vector((*q, 0))).length < 11 for q in skip): streetlight(p + n * s * off + Vector((0, 0, .3)), -n * s)
        t += step; k += 1
JUNCS = [(0, 0), (-48, 0), (48, 0), (48, 64)]
lamps_along((-96, 0), (104, 0), skip=JUNCS); lamps_along((0, -72), (0, 72), skip=JUNCS); lamps_along((48, 0), (48, 64), skip=JUNCS)
lamps_along((-48, 0), (-48, -72), skip=JUNCS); lamps_along((56, 64), (104, 64), skip=JUNCS); lamps_along((26, 90), (98, 90))
for (x, y, r) in ((7.6, -7.6, 0), (-7.6, 7.6, math.pi), (7.6, 7.6, H90), (-7.6, -7.6, -H90)):
    load(U + 'Traffic lights/traffic_light_pole.glb', (x, y, .3), r)
# ---- buildings: tall flats to the north (background), low sheds / yards to the south so the camera sees the streets
FL = U + 'Buildings Prebuild/'
for f, x, y, r in (('flat_square_brick', 24, 28, 0), ('flat_square_concrete', 24, 58, H90), ('flat_Lshape', -30, 36, 0), ('flat_square_concrete_alt', -104, 56, H90),
                   ('flat_square_brick_alt', -64, 58, 0), ('flat_Lshape_large_alt', 76, 32, H90), ('flat_square_brick', 40, 116, 0), ('flat_square_concrete', 70, 116, H90),
                   ('flat_Lshape_vertical_stripes', 4, 120, 0), ('flat_square_brick_alt', -34, 96, 0), ('flat_square_concrete_alt', -66, 96, H90), ('flat_Lshape', 104, 112, 0),
                   ('flat_square_brick', -84, 30, 0), ('flat_square_concrete', 112, 30, 0)):
    load(FL + f + '.glb', (x, y, 0), r)
load(FL + 'Hangar1.glb', (62, -22, 0), 0); load(FL + 'Hangar1.glb', (-74, -24, 0), H90)
load(SHK + 'Large Shed A.blend', (-26, -30, 0), H90); load(SHK + 'Large Shed B.blend', (-26, -58, 0), H90)
load(SHK + 'Shack A.blend', (42, -52, 0), 0.3); load(SHK + 'Leanto B.blend', (-12.5, -44, 0), 0); load(SHK + 'Leanto A.blend', (-36, -16, 0), math.pi)
load(SHK + 'Large Shed A.blend', (66, -54, 0), 0); load(SHK + 'Shack A.blend', (-70, -56, 0), 1.2)
load(SHK + 'Large Shed B.blend', (84, 78, 0), H90); load(SHK + 'Shack A.blend', (64, 79, 0), 0); load(SHK + 'Leanto B.blend', (28, 76, 0), H90)
# ---- low-rise street wall: Kenney retro-urban-kit wall cubes (1 m modules scaled to 3 m), windows/doors face outward
KS = 4.0
VENTS = [U + 'Vents/' + f for f in ('vent_cover.glb', 'duct.glb', 'duct_long.glb', 'duct_corner_sharp.glb')]
def kbuild(x0, y0, nx, ny, nz, style='a', doors=True):
    """x0,y0 = SW corner; nx x ny cubes footprint, nz storeys. Perimeter cubes face out, interior only on the top storey (roof)."""
    rr = random.Random(int(x0 * 7 + y0 * 13))
    for i in range(nx):
        for j in range(ny):
            edge = []
            if j == 0: edge.append((0, -1))
            if j == ny - 1: edge.append((0, 1))
            if i == 0: edge.append((-1, 0))
            if i == nx - 1: edge.append((1, 0))
            for k in range(nz):
                if not edge and k < nz - 1: continue
                if edge:
                    f = edge[0] if len(edge) == 1 else rr.choice(edge)
                    if len(edge) > 1: n = f'wall-{style}'
                    elif k == 0 and doors: n = rr.choice((f'wall-{style}-door', f'wall-{style}-garage', f'wall-{style}-window', f'wall-{style}-window', f'wall-{style}'))
                    else: n = rr.choice((f'wall-{style}-window', f'wall-{style}-window', f'wall-{style}-window', f'wall-{style}'))
                    rot = math.atan2(-f[0], f[1])
                else: n = f'wall-{style}'; rot = 0
                load(KEN + n + '.glb', (x0 + (i + .5) * KS, y0 + (j + .5) * KS, .3 + k * KS), rot, KS)
    for _ in range(max(1, nx * ny // 6)):    # rooftop vents / ducts (URBAN)
        load(rr.choice(VENTS), (x0 + rr.uniform(1, nx * KS - 1), y0 + rr.uniform(1, ny * KS - 1), .3 + nz * KS), rr.choice((0, H90)), 1.0)
for args in ((9, 9, 2, 2, 2, 'b'), (19, 9, 5, 2, 1, 'a'), (34, 20, 1, 4, 3, 'b'), (9, 38, 2, 2, 1, 'a'), (34, 40, 1, 5, 2, 'a'),
             (-41, 9, 5, 2, 3, 'a'), (-17, 9, 2, 3, 2, 'b'), (-17, 25, 2, 4, 3, 'a'), (-17, 45, 2, 3, 2, 'b'), (-57, 9, 3, 3, 2, 'b'),
             (-38, 54, 3, 2, 2, 'b'), (-57, 25, 2, 4, 4, 'a'), (-95, 9, 8, 2, 2, 'a'), (-68, -46, 3, 2, 1, 'a'),
             (43, -21, 3, 3, 2, 'a'), (12, -60, 6, 3, 3, 'b'), (74, -21, 4, 3, 2, 'b'), (56, 9, 7, 2, 2, 'b')):
    kbuild(*args)
# ---- yards and street props
for i in range(12):   # chainlink around the SW yard
    load(SHK + 'Chainlink Fence.blend', (-39 + i * 2.4, -9.2, .0), 0, origin=(0, 0, 0))
for i in range(8): load(SHK + 'Chainlink Fence.blend', (-9.4, -12 - i * 2.4, 0), -H90, origin=(0, 0, 0))
for p in ((-17, -20), (-16, -21.5), (-18.4, -21), (-33, -44), (-34, -45.5)): load(SHK + 'Barrel.blend', (*p, 0), R.uniform(0, 6))
for p in ((-20, -36), (-21.5, -37.5)): load(SHK + 'Pallet.blend', (*p, 0), R.uniform(0, 6))
for i, p in enumerate(((52, -38), (55.5, -38), (72, -40))): load(KEN + ('truck-grey-cargo.glb', 'truck-green.glb', 'truck-flat.glb')[i], (*p, 0), H90, 2.6)
load(KEN + 'truck-grey.glb', (-16, -27, 0), 0.0, 2.6) if os.path.exists(KEN + 'truck-grey.glb') else load(KEN + 'truck-flat.glb', (-16, -27, 0), 0.0, 2.6)
for p, f in (((36, 38), 'dumpster_diagonal_closed_blue'), ((-19.5, 21), 'dumpster_diagonal_closed'), ((9.8, -50), 'dumpster_diagonal_closed_red'), ((14, 47.5), 'dumpster_diagonal_closed')):
    load(U + 'Litter/Dumpsters/' + f + '.glb', (*p, .3), R.choice((0, H90)))
for p in ((14, 8.4), (-20, 8.4), (-8.6, 30), (8.6, -26), (60, 8.4), (-56, -8.4)): load(U + 'Litter/TrashCan/trash_can.glb', (*p, .3), 0)
for p in ((-9, 44), (8.8, 40), (24, -8.6), (-60, 8.6)): load(U + 'Litter/Trash/trashpile_1.glb', (*p, .3), R.uniform(0, 6))
load(U + 'Bus stops/busstop_bench.glb', (-26, 6.6, .3), math.pi)
for i in range(6): load(U + 'Cones & Barriers/Concrete Barriers/Jersey_barrier.glb', (12.5 + i * 2.6, -9.6, .3), 0)   # meet lot edge
for i in range(4): load(U + 'Cones & Barriers/Concrete Barriers/Jersey_barrier.glb', (40.6, -14 - i * 2.6, .3), H90)
for p in ((32.5, -10.6), (33.8, -11.2)): load(U + 'Cones & Barriers/Cones/Traffic_cone_round.glb', (*p, .3), 0)
for p in ((-3, -66), (3, -66)): load(U + 'Cones & Barriers/Type 3 Barriers/Type_3_barrier_3_planks.glb', (*p, .16), 0)   # road works, south
# meet lot surface (plain asphalt tile from ps1-industrial, scaled) and its own lamp
plate('road-asphalt-center', 11.5, 40, -40, -10, .33, 4.0, tex=os.path.join(TEX, 'asphalt_lot.png'))
streetlight((38.4, -36, .0), Vector((-1, .4, 0)).normalized()); streetlight((13, -37, .0), Vector((1, .5, 0)).normalized())
plate('road-dirt-center', -39, -10, -70, -10, .32, 4.0)          # the fenced yard is dirt
for p in ((-37, -40), (-37, -42.5), (-14, -60)): load(KEN + 'pallet.glb', (*p, .32), R.uniform(0, 6), 2.0)
load(KEN + 'detail-dumpster-open.glb', (38, -45, .3), 0, 2.4)
# trees and bushes: street trees on the north cross street, clumps in yards and the leftover corners
for y in range(14, 62, 10): tree((-7.4, y, .3), R.uniform(1.2, 1.5)); tree((7.4, y + 5, .3), R.uniform(1.2, 1.5))
for p in ((-44, 16), (40, 46), (34, 44), (56, 48), (60, 72), (44, 80), (-12, 80), (-18, 74), (-86, -10), (-58, -66), (92, -26), (90, -40), (22, -70), (-4, -84), (-38, -70)):
    tree((p[0] + R.uniform(-1, 1), p[1] + R.uniform(-1, 1), 0), R.uniform(1.4, 2.2))
for p in ((10.5, -42), (11.5, -45), (36, -42), (-44, 10.5), (54.5, 12), (13, 60)): bush((*p, .3), R.uniform(.9, 1.3))

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
LITMAP = {'houses': 'houses_lit.png', 'windows': 'windows_lit.png'}
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
    cs = x2.outputs[0]
    litk = next((k for k in LITMAP if tex and tex.image.name.lower().startswith(k)), None)
    if litk:     # per-face lit windows: lit-glass variant of the pack texture x 'Lit' tint, picked by Lit.alpha
        lt = nt.nodes.new('ShaderNodeTexImage'); lt.image = img(LITMAP[litk]); lt.interpolation = 'Closest'; nt.links.new(uvn.outputs[0], lt.inputs[0])
        la = nt.nodes.new('ShaderNodeVertexColor'); la.layer_name = 'Lit'
        lm = nt.nodes.new('ShaderNodeMix'); lm.data_type = 'RGBA'; lm.blend_type = 'MULTIPLY'; lm.inputs['Factor'].default_value = 1
        nt.links.new(lt.outputs[0], lm.inputs[6]); nt.links.new(la.outputs[0], lm.inputs[7])
        l2 = nt.nodes.new('ShaderNodeVectorMath'); l2.operation = 'SCALE'; l2.inputs[3].default_value = 2.0; nt.links.new(lm.outputs[2], l2.inputs[0])
        mx_ = nt.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; nt.links.new(la.outputs[1], mx_.inputs['Factor']); nt.links.new(cs, mx_.inputs[6]); nt.links.new(l2.outputs[0], mx_.inputs[7]); cs = mx_.outputs[2]
    cs = fog_mix(nt, cs); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cs, em.inputs[0])
    if alpha and asock is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
        nt.links.new(asock, gt.inputs[0]); nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs[0]); n.surface_render_method = 'DITHERED'
    else: nt.links.new(em.outputs[0], out.inputs[0])
    n.use_backface_culling = False; UNLIT[m.name] = n; return n
WINRECTS = [(130, 130, 188, 248), (400, 130, 460, 248), (190, 130, 242, 195), (693, 95, 766, 188)]
def vlight(p, nrm):
    """painted night light: cool ambient (darker with height) + stepped sodium pools from every lamp head."""
    k = 0.19 + 0.05 * max(0.0, nrm.z)
    k *= max(0.45, 1.0 - max(0.0, p.z - 3.0) / 25.0) * T['amb_k']
    if nrm.z > .7 and p.z < .5: k *= T['ground_k']          # rain: darker, wet-looking ground
    c = [AMB[i] * k for i in range(3)]
    for li, L in enumerate(LAMPS):
        d = (p - L).length; lv = max(0.0, 1 - d / 13.0); lv = math.floor(lv * T['steps']) / T['steps']
        lc = LAMPC[li % len(LAMPC)]
        gk = T.get('ow_ground_lamp', 1.0) if nrm.z > .7 else 1.0     # ground pools come mostly from the hard-edged decal
        for i in range(3): c[i] += lc[i] * lv * T['lamp_k'] * gk
    return tuple(min(1.0, x * 0.5) for x in c) + (1.0,)
def paint(o):
    me = o.data
    if 'Col' in me.color_attributes: me.color_attributes.remove(me.color_attributes['Col'])
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index]; ca.data[li].color = vlight(v.co, poly.normal)
    def texname(m):
        t = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if (m and m.node_tree) else None
        return t.image.name.lower() if t else ''
    names = [texname(m) for m in me.materials]
    if any(nm.startswith(('houses', 'windows')) for nm in names):
        la = me.color_attributes.new('Lit', 'BYTE_COLOR', 'CORNER'); uv = me.uv_layers[0].data; rr = random.Random(zlib.crc32(o.name.encode()) & 0xffff)
        share = rr.uniform(.25, .55); obj_on = rr.random() < .45     # Kenney modules: one window per cube, lit or not
        for poly in me.polygons:
            nm = names[poly.material_index] if poly.material_index < len(names) else ''
            if nm.startswith('windows'):
                on = obj_on and poly.normal.z < .5
            else:
                u = sum(uv[li].uv[0] for li in poly.loop_indices) / poly.loop_total % 1.0; v = sum(uv[li].uv[1] for li in poly.loop_indices) / poly.loop_total % 1.0
                px, py = u * 1024, (1 - v) * 1024
                win = nm.startswith('houses') and any(x0 <= px <= x1 and y0 <= py <= y1 for x0, y0, x1, y1 in WINRECTS)
                on = win and rr.random() < share
            col = rr.choice(((.5, .46, .38), (.5, .46, .38), (.5, .42, .3), (.36, .44, .5))) if on else (.5, .5, .5)
            for li in poly.loop_indices: la.data[li].color = (*col, 1.0 if on else 0.0)
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
pool_ms = [additive(f'pool{j}', f'pool_{TONE}_{j}.png', T['pool_k'] * T.get('ow_pool_mul', 1.0)) for j in range(len(LAMPC))]
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
def car(glb, root_name, prefix, s, off, head, tail, shine, lights=True):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        C_CAR.objects.link(o)
        if '_FX_' in o.name: o.hide_render = True
    for m in {m for o in new if o.type == 'MESH' for m in o.data.materials if m}:
        for k, kw in shine.items():
            if m.name.startswith(prefix + k): fake_shine(m, **kw)
    root = bpy.data.objects[root_name] if root_name else next(o for o in new if o.parent is None and o.type == 'EMPTY')
    p, h = Vector(s), Vector(off)
    root.rotation_mode = 'XYZ'; root.location = p + Vector((0, 0, 0.16)); root.rotation_euler = (0, 0, yaw(h) + math.pi / 2)
    b = quad_obj(prefix + 'Blob', [(-1.15, -2.6, .012), (1.15, -2.6, .012), (1.15, 2.6, .012), (-1.15, 2.6, .012)], [(0, 1), (0, 0), (1, 0), (1, 1)], blob_m, C_CAR); b.parent = root
    if not lights: return root
    t = quad_obj(prefix + 'Throw', [(-1.7, -2.2, .016), (1.7, -2.2, .016), (1.7, -11.5, .016), (-1.7, -11.5, .016)], [(0, 1), (1, 1), (1, 0), (0, 0)], throw_m, C_CAR); t.parent = root
    for sx in (1, -1):
        bh = billboard(prefix + f'Head{sx}', (sx * head[0], head[1], head[2]), .42, gh, C_CAR, root); bh['face'] = (0, -1, 0)
        bt = billboard(prefix + f'Tail{sx}', (sx * tail[0], tail[1], tail[2]), .75, gt, C_CAR, root); bt['face'] = (0, 1, 0)
    return root
PAINT = dict(spec=.55, env=.22, amb=.5, tint=(.80, .86, 1.0)); GLASS = dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0))
# ------------------------------------------------------------------ cars: player GR (driving, lights on), rival WRX parked at the meet, a BRZ roaming
LOFF = {}
player = car(CARS + 'gr_corolla/car_gr_corolla.glb', 'GRC-vehicle', 'GRC_', (-14.0, -2.6, 0), (1, 0, 0), (.60, -2.12, .68), (.64, 1.99, .88),
             {'Paint': PAINT, 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})
rival = car(CARS + 'wrx_sti/car_wrx_sti.glb', 'WRX-vehicle', 'WRX_', (21.0, -22.5, 0.17), Vector((1, -.35, 0)).normalized(), (.62, -2.1, .70), (.66, 2.12, .86),
            {'Paint': dict(spec=.55, env=.28, amb=.5, tint=(.8, .86, 1.0)), 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)}, lights=False)
roam = car(CARS + 'brz/car_brz.glb', None, 'BRZ_', (2.6, 38.0, 0), (0, -1, 0), (.62, -2.1, .66), (.66, 2.1, .86),
           {'Paint': PAINT, 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})
meet2 = car(CARS + 's2000/car_s2000.glb', None, 'S2K_', (34.5, -17.0, 0.17), Vector((-.6, -1, 0)).normalized(), (.62, -2.1, .66), (.66, 2.1, .86),
            {'Paint': dict(spec=.55, env=.3, amb=.5), 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)}, lights=False)
def flat_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*lin(col), 1)
    nt.links.new(e.outputs[0], o.inputs[0]); return m
# worn parking-bay lines on the lot (hand-built thin quads, flat dim paint)
bay_m = flat_mat('bay_paint', (.30, .30, .28))
for k in range(9):
    x = 13.5 + k * 3.0
    quad_obj(f'Bay{k}', [Vector((x - .09, -39.6, .345)), Vector((x + .09, -39.6, .345)), Vector((x + .09, -34.6, .345)), Vector((x - .09, -34.6, .345))], [(0, 0)] * 4, bay_m, C_WORLD)
for k in range(5):
    y = -36.5 + k * 3.0
    quad_obj(f'BayE{k}', [Vector((39.6, y - .09, .345)), Vector((39.6, y + .09, .345)), Vector((34.6, y + .09, .345)), Vector((34.6, y - .09, .345))], [(0, 0)] * 4, bay_m, C_WORLD)
# meet marker: stepped amber ground ring (decal) + a slow-spinning faceted pin, flat two-tone, like a PS1 pickup
MEET = Vector((28.0, -27.0, 0.0))
ring_m = additive('meet_ring', 'meet_ring.png', 0.6); s = 5.5
quad_obj('MeetRing', [MEET + Vector((-s, -s, .37)), MEET + Vector((s, -s, .37)), MEET + Vector((s, s, .37)), MEET + Vector((-s, s, .37))], [(0, 0), (1, 0), (1, 1), (0, 1)], ring_m, C_NEON)
pm = [flat_mat('pin_a', hx('#FFC038')), flat_mat('pin_b', hx('#C86A10')), flat_mat('pin_c', hx('#FFE6A0'))]
me = bpy.data.meshes.new('pin'); r_, h_ = 1.5, 2.2
vs = [(0, 0, h_), (0, 0, -h_ * 1.2)] + [(r_ * math.cos(k * math.pi / 2), r_ * math.sin(k * math.pi / 2), 0) for k in range(4)]
fs = [(0, 2 + k, 2 + (k + 1) % 4) for k in range(4)] + [(1, 2 + (k + 1) % 4, 2 + k) for k in range(4)]
me.from_pydata(vs, [], fs); me.update()
for i, p in enumerate(me.polygons): p.material_index = (0 if i % 2 == 0 else 2) if i < 4 else 1
for m in pm: me.materials.append(m)
pin = bpy.data.objects.new('MeetPin', me); C_NEON.objects.link(pin); pin.location = MEET + Vector((0, 0, 6.0)); pin.rotation_euler = (0, 0, .5)
billboard('MeetGlow', MEET + Vector((0, 0, 6.0)), 4.5, additive('meet_glow', 'glow_sodium.png', .5))

# ------------------------------------------------------------------ camera
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = .1; cam.data.clip_end = 500; cam.rotation_mode = 'XYZ'
def look(loc, tgt, lens, roll=0.0):
    cam.location = loc; cam.data.lens = lens
    q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y'); cam.rotation_euler = (q @ Matrix.Rotation(roll, 4, 'Z').to_quaternion()).to_euler()
CAM_YAW = math.radians(float(os.environ.get('CAM_YAW', 18)))      # camera is rotatable in game; this view looks NNE
PITCH = math.radians(float(os.environ.get('CAM_PITCH', 57))); DIST = float(os.environ.get('CAM_DIST', 95))
FOCUS = Vector((float(os.environ.get('FX', 10)), float(os.environ.get('FY', -3)), 0))
fwd = Vector((math.sin(CAM_YAW), math.cos(CAM_YAW), 0))
look(FOCUS - fwd * DIST * math.cos(PITCH) + Vector((0, 0, DIST * math.sin(PITCH))), FOCUS, float(os.environ.get('CAM_LENS', 28)))
bpy.context.view_layer.update()
for g in GLOWS:   # car lamp sprites: show when the lamp faces the camera in plan view (top-down camera)
    if 'face' in g:
        f = (g.parent.matrix_world.to_3x3() @ Vector(g['face'])); f.z = 0; f.normalize(); w = g.matrix_world.translation
        v = cam.location - w; v.z = 0; v.normalize()
        if f.dot(v) < -0.2: g.hide_render = True

for g in GLOWS:   # a lamp sprite only shows when its lamp faces the camera (no glow leaking around the body)
    if 'face' in g:
        f = (g.parent.matrix_world.to_3x3() @ Vector(g['face'])).normalized(); w = g.matrix_world.translation
        if f.dot((cam.location - w).normalized()) < 0.15: g.hide_render = True
for g in GLOWS:
    c = g.constraints.new('TRACK_TO'); c.target = cam; c.track_axis = 'TRACK_NEGATIVE_Y'; c.up_axis = 'UP_Z'
bpy.context.view_layer.update()
def scr(p):
    v = world_to_camera_view(sc, cam, Vector(p)); return [v.x * 640, (1 - v.y) * 480, v.z]
anch = {'player': scr(player.location + Vector((0, 0, 1.5))), 'rival': scr(rival.location + Vector((0, 0, 1.5))), 'pin': scr(pin.location),
        'meet_ground': scr(MEET), 'player_xy': list(player.location[:2]), 'player_hdg': 0.0, 'meet_xy': list(MEET[:2]), 'roads': ROADS,
        'cam_yaw': math.degrees(CAM_YAW), 'lamps_xy': [list(L[:2]) for L in LAMPS]}
json.dump(anch, open(os.path.join(RAW, 'anchors_overworld.json'), 'w'), indent=1)

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
