"""Midnight Apex: dynamic Entry / Apex / Exit line-select camera mockup (UNAPPROVED PROPOSAL).
Cheap Touge right hairpin built in Blender (road strip, 3 lanes, W-beam guardrail, chevron boards, cut bank, drop-off,
cedar cards, sparse pale-sodium lamps). Same unlit pipeline as the earlier lane_chain/v5 and race_state_study/entry_matrix mockups (removed 2026-11-13; git history):
texture x painted vertex light (half scale, x2) -> linear fog -> emission; hard 3-step lamp pools; glow sprites;
game cars (MX5 player, S2000 rival) with the A.4 faked shine. Tone = blend50 (tones/work/tones.py).
EEVEE Next 640x480, 1 sample, filter 0, Standard view. post_lsc.py does bloom (glows only) -> HUD -> RGB555 + Bayer -> 2x.
Renders: chase (frames 1 and 4: fixed chase camera, offset (1.4,-7.6,2.94), 25 mm) + 192x64 rear mirror, apex, exit.
Usage: blender -b -P build_lsc.py"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'raw'); MYTEX = os.path.join(HERE, 'tex')
TEX = '/workspace/mockups/tones/work/lane/tex'; os.makedirs(RAW, exist_ok=True)
AP = '/workspace/asset_packs/'; U = AP + 'psx-style-urban-stacked-pack/x/URBAN/'; CARS = '/workspace/midnight-apex/assets/cars/'
R = random.Random(11)
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lin(c): return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
sys.path.insert(0, '/workspace/mockups/tones/work'); from tones import TONES
TONE = 'blend50'; T = TONES[TONE]
FOG = lin(hx(T['fog'])); AMB = hx(T['amb']); LAMPC = [hx(c) for c in T['lamps']]
FOG_NEAR, FOG_FAR = 9.0, 78.0          # Touge: fog-heavy, shorter than the city (art_direction B.3 Touge ~8-55 m, pushed out so the corner reads)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def coll(n): c = bpy.data.collections.new(n); sc.collection.children.link(c); return c
C_WORLD, C_NEON, C_CAR, C_SKY = coll('World'), coll('Neon'), coll('Car'), coll('Sky')

# ------------------------------------------------------------------ hairpin geometry: right-hand 180, radius 12 (centre lane)
CX, CY, RAD = 12.0, 0.0, 12.0          # entry straight x=0 heading +Y, arc over the top, exit straight x=24 heading -Y
LA = math.pi * RAD
LANE = {'OUT': -3.3, 'MID': 0.0, 'IN': 3.3}     # lateral offset to the right of travel (right hairpin: inside = right)
HALF = 5.0
def track(s, off=0.0):
    if s < 0: return Vector((off, s, 0)), Vector((0, 1, 0))
    if s <= LA:
        phi = math.pi - s / RAD; r = RAD - off
        return Vector((CX + r * math.cos(phi), CY + r * math.sin(phi), 0)), Vector((math.sin(phi), -math.cos(phi), 0))
    return Vector((CX + RAD - off, -(s - LA), 0)), Vector((0, -1, 0))
def samples(s0, s1):
    out, s = [], s0
    while s < s1:
        out.append(s); s += 0.5 if 0 <= s <= LA else 2.0
    out.append(s1); return out

# ------------------------------------------------------------------ materials
IMGS = {}
def img(path):
    if path not in IMGS: IMGS[path] = bpy.data.images.load(path)
    return IMGS[path]
def texmat(name, path, rgb=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if path:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(path); nt.links.new(t.outputs[0], b.inputs['Base Color'])
    else: b.inputs['Base Color'].default_value = rgb + (1,)
    return m
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
        uvn = nt.nodes.new('ShaderNodeUVMap'); nt.links.new(uvn.outputs[0], t.inputs[0]); cs = t.outputs[0]; asock = t.outputs[1]
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
LAMPS = []
def vlight(p, nrm):
    """painted night light: cool ambient (darker with height) + hard 3-step pale-sodium pools from every lamp head."""
    k = 0.19 + 0.05 * max(0.0, nrm.z)
    k *= max(0.45, 1.0 - max(0.0, p.z - 3.0) / 25.0) * T['amb_k']
    c = [AMB[i] * k for i in range(3)]
    for li, L in enumerate(LAMPS):
        d = (p - L).length; lv = max(0.0, 1 - d / 13.0); lv = math.floor(lv * T['steps']) / T['steps']
        gk = T.get('lane_ground_lamp', 1.0) if nrm.z > .7 else 1.0
        for i in range(3): c[i] += LAMPC[0][i] * lv * T['lamp_k'] * gk
    return tuple(min(1.0, x * 0.5) for x in c) + (1.0,)
PAINTED = []
def paint(o):
    me = o.data
    if 'Col' in me.color_attributes: me.color_attributes.remove(me.color_attributes['Col'])
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    mw = o.matrix_world
    for poly in me.polygons:
        nrm = (mw.to_3x3() @ poly.normal).normalized()
        for li in poly.loop_indices:
            ca.data[li].color = vlight(mw @ me.vertices[me.loops[li].vertex_index].co, nrm)
    for i, m in enumerate(me.materials):
        if m: me.materials[i] = unlit_from(m)
    if not me.materials: me.materials.append(unlit_from(texmat('plain', None, (.5, .5, .5))))

def mesh_obj(name, verts, faces, uvs, mat, coll_=None):
    """faces: index tuples; uvs: per-face list of uv tuples."""
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(); k = 0
    for fi, poly in enumerate(me.polygons):
        for j, li in enumerate(poly.loop_indices): uvl.data[li].uv = uvs[fi][j]
    o = bpy.data.objects.new(name, me); (coll_ or C_WORLD).objects.link(o); me.materials.append(mat); PAINTED.append(o); return o
def strip(name, s0, s1, prof, mat, vscale=4.0, closed_u=None):
    """sweep a cross-section prof = [(off, z, u), ...] along the path."""
    ss = samples(s0, s1); verts = []; faces = []; uvs = []; n = len(prof)
    for s in ss:
        for off, z, u in prof:
            p, _ = track(s, off); verts.append(Vector((p.x, p.y, z)))
    for i in range(len(ss) - 1):
        for j in range(n - 1):
            a, b = i * n + j, i * n + j + 1; c, d = b + n, a + n
            faces.append((a, b, c, d)); v0, v1 = ss[i] / vscale, ss[i + 1] / vscale
            uvs.append([(prof[j][2], v0), (prof[j + 1][2], v0), (prof[j + 1][2], v1), (prof[j][2], v1)])
    return mesh_obj(name, verts, faces, uvs, mat)

S0, S1 = -110.0, LA + 90.0
# road (3 x 3.3 m lanes), asphalt from the entry_matrix approach, nearest
asph = texmat('Asphalt', os.path.join(MYTEX, 'asphalt.png'))
strip('Road', S0, S1, [(-HALF, .18, 0), (-1.65, .18, .67), (1.65, .18, 1.33), (HALF, .18, 2)], asph, vscale=100 / 30)
paintm = texmat('LanePaint', None, (.74, .74, .66))
def line_dashes(off, w, on, gap, name, solid=False):
    ss = [S0] if solid else []
    s = S0; verts = []; faces = []; uvs = []
    while s < S1:
        e = S1 if solid else min(S1, s + on); seg = [x for x in samples(s, e)]
        for i in range(len(seg) - 1):
            k = len(verts)
            for (ss_, o_) in ((seg[i], off - w / 2), (seg[i], off + w / 2), (seg[i + 1], off + w / 2), (seg[i + 1], off - w / 2)):
                p, _ = track(ss_, o_); verts.append(Vector((p.x, p.y, .192)))
            faces.append((k, k + 1, k + 2, k + 3)); uvs.append([(0, 0)] * 4)
        if solid: break
        s += on + gap
    mesh_obj(name, verts, faces, uvs, paintm)
line_dashes(-1.65, .11, 3.0, 3.0, 'LaneDivL'); line_dashes(1.65, .11, 3.0, 3.0, 'LaneDivR')
line_dashes(-4.72, .13, 0, 0, 'EdgeL', True); line_dashes(4.72, .13, 0, 0, 'EdgeR', True)
conc = texmat('Concrete', os.path.join(MYTEX, 'concrete.png'))
strip('ShoulderOut', S0, S1, [(-HALF - 1.7, .17, 0), (-HALF, .18, 1)], conc, vscale=2)
strip('GutterIn', S0, S1, [(HALF, .18, 0), (HALF + .25, .05, .3), (HALF + .6, .3, 1)], conc, vscale=2)
# cut bank + hill on the inside (rises to the hairpin's centre), drop-off on the outside
slope = texmat('Slope', os.path.join(MYTEX, 'slope.png'))
def hill_z(off): t = max(0.0, min(1.0, (off - 5.6) / 6.4)); return .3 + 2.9 * t ** 1.2
strip('InsideHill', S0, S1, [(o, hill_z(o), (o - 5.6) / 2) for o in (5.6, 6.4, 7.6, 9.0, 10.5, 12.0)], slope, vscale=4)
def drop_z(off): t = max(0.0, min(1.0, (-6.7 - off) / 11.0)); return .17 - 9.2 * t ** 1.3
strip('OutsideDrop', S0, S1, [(o, drop_z(o), (-6.7 - o) / 2) for o in (-6.7, -8.0, -10.5, -13.5, -17.7)], slope, vscale=4)
lowg = texmat('LowGround', os.path.join(MYTEX, 'slope.png'))
mesh_obj('LowGround', [Vector((-260, -260, -9.05)), Vector((280, -260, -9.05)), Vector((280, 260, -9.05)), Vector((-260, 260, -9.05))], [(0, 1, 2, 3)],
         [[(0, 0), (90, 0), (90, 90), (0, 90)]], lowg)

# W-beam guardrail on the outside, steel posts every 2 m
gr = texmat('Guardrail', os.path.join(MYTEX, 'guardrail.png'))
strip('Guardrail', S0, S1, [(-5.95, .42, 1.0), (-5.86, .61, .5), (-5.95, .80, 0.0)], gr, vscale=4)
postm = texmat('Post', None, (.55, .57, .58)); verts = []; faces = []; uvs = []
s = S0
while s < S1:
    p, h = track(s, -6.04); side = Vector((-h.y, h.x, 0)) * .06; fw = h * .06; k = len(verts)
    for dz in (0, .76):
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)): verts.append(p + side * a + fw * b + Vector((0, 0, dz - .2 if dz == 0 else dz)))
    for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):
        faces.append(tuple(k + x for x in f)); uvs.append([(0, 0)] * 4)
    s += 2.0 if not (0 <= s <= LA) else 2.0
mesh_obj('GuardPosts', verts, faces, uvs, postm)

# chevron boards along the outside of the arc (point in the turn direction), on short posts behind the rail
chev = texmat('Chevron', os.path.join(MYTEX, 'chevron.png')); verts = []; faces = []; uvs = []
for i in range(9):
    s = LA * (0.04 + 0.92 * i / 8); p, h = track(s, -6.25); k = len(verts)
    for dx, z in ((-.45, 1.0), (.45, 1.0), (.45, 1.9), (-.45, 1.9)): verts.append(p + h * dx + Vector((0, 0, z)))
    faces.append((k, k + 1, k + 2, k + 3)); uvs.append([(0, 0), (1, 0), (1, 1), (0, 1)])
cv = mesh_obj('Chevrons', verts, faces, uvs, chev); CULL = ['Chevron']
bverts = []; bfaces = []; buvs = []
for i in range(9):
    s_ = LA * (0.04 + 0.92 * i / 8); p, h = track(s_, -6.29); k = len(bverts)
    for dx, z in ((.45, 1.0), (-.45, 1.0), (-.45, 1.9), (.45, 1.9)): bverts.append(p + h * dx + Vector((0, 0, z)))
    bfaces.append((k, k + 1, k + 2, k + 3)); buvs.append([(0, 0)] * 4)
mesh_obj('ChevronBacks', bverts, bfaces, buvs, texmat('ChevronBack', None, (.35, .36, .38)))
# hairpin warning plate on the outside of the approach (same pixel sign as entry_matrix)
sign = texmat('HairpinSign', os.path.join(MYTEX, 'hairpin_sign.png'))
mesh_obj('HairpinSign', [Vector((-7.5, -5, 2.0)), Vector((-6.1, -5, 2.0)), Vector((-6.1, -5, 3.4)), Vector((-7.5, -5, 3.4))], [(0, 1, 2, 3)], [[(0, 0), (1, 0), (1, 1), (0, 1)]], sign)
mesh_obj('SignPole', [Vector((-6.84, -4.98, -.3)), Vector((-6.76, -4.98, -.3)), Vector((-6.76, -4.98, 2.0)), Vector((-6.84, -4.98, 2.0))], [(0, 1, 2, 3)], [[(0, 0)] * 4], postm)

# ------------------------------------------------------------------ lamps (URBAN street_light, sparse) — before painting
IMPORTED = []
def load(path, loc, rotz, origin):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; bpy.context.view_layer.update()
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rotz, 4, 'Z') @ Matrix.Translation(-Vector(origin))
    for o in new:
        if o.type != 'MESH': continue
        o.data = o.data.copy(); o.data.transform(M @ o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
        for c in list(o.users_collection): c.objects.unlink(o)
        C_WORLD.objects.link(o); IMPORTED.append(o)
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
def streetlight(s, off=-7.3):
    p, h = track(s, off); face = (track(s, 0)[0] - p).normalized(); a = math.atan2(face.y, face.x)
    load(U + 'Traffic lights/street_light.glb', (p.x, p.y, -.25), a, (9.65, 12.65, 0))
    LAMPS.append(Vector((p.x, p.y, -.25)) + face * 1.7 + Vector((0, 0, 6.35)))
for s in (-62, -13, LA * .70, LA + 26): streetlight(s)

# ------------------------------------------------------------------ cedar cards (crossed quads), outside drop + inside hill
cedar = texmat('cedar_tree', os.path.join(MYTEX, 'cedar.png')); verts = []; faces = []; uvs = []
CAM_KEEP = []          # filled after cameras are defined: keep cedars out of the lens
def cedar_at(p, h):
    w = h / 3.0; k = len(verts); a = R.uniform(0, math.pi)
    for ang in (a, a + math.pi / 2):
        dv = Vector((math.cos(ang), math.sin(ang), 0)) * w / 2; k = len(verts)
        verts.extend([p - dv, p + dv, p + dv + Vector((0, 0, h)), p - dv + Vector((0, 0, h))])
        faces.append((k, k + 1, k + 2, k + 3)); uvs.append([(0, 0), (1, 0), (1, 1), (0, 1)])
TREES = []
s = S0
while s < S1:
    for _ in range(2):   # outside, falling away: roots on the drop, tops at or above road level
        o = -R.uniform(9.0, 34.0); p, _ = track(s + R.uniform(-2, 2), o); TREES.append((Vector((p.x, p.y, drop_z(o) if o > -17.7 else -9.05)), R.uniform(11, 16)))
    if R.random() < .8:  # inside hill
        o = R.uniform(7.2, 12.0); p, _ = track(s + R.uniform(-2, 2), o); TREES.append((Vector((p.x, p.y, hill_z(o) - .2)), R.uniform(9, 14)))
    s += 3.2 if 0 <= s <= LA else 4.5
for (x, y) in [(12 + R.uniform(-3, 3), R.uniform(-60, -4)) for _ in range(30)]: TREES.append((Vector((x, y, hill_z(12) - .2)), R.uniform(10, 15)))

# ------------------------------------------------------------------ cameras (defined before the cedars are baked so none sit in a lens)
cams = {}
def mkcam(name, loc, tgt, lens, w=640, h=480):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.type = 'PERSP'; c.data.sensor_fit = 'HORIZONTAL'; c.data.sensor_width = 36; c.data.lens = lens
    c.data.clip_start = .1; c.data.clip_end = 600; c.rotation_mode = 'XYZ'; c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); cams[name] = c; return c
PLAYER_ROOT = Vector((0, -28, .16))
mkcam('chase', PLAYER_ROOT + Vector((1.4, -7.6, 2.94)), (3.6, -6, -.9), 25)          # fixed chase (entry_matrix exact)
mkcam('mirror', (0, -28, 1.60), (0, -60, -2.2), 14)
AP_PHI = math.radians(float(os.environ.get('AP_PHI', 104))); AP_R = float(os.environ.get('AP_R', 22.5)); AP_Z = float(os.environ.get('AP_Z', 8.0))
ap_t = math.radians(float(os.environ.get('AP_TPHI', 84)))
mkcam('apex', (CX + AP_R * math.cos(AP_PHI), CY + AP_R * math.sin(AP_PHI), AP_Z), (CX + 9.5 * math.cos(ap_t), CY + 9.5 * math.sin(ap_t), -.8), float(os.environ.get('AP_LENS', 19)))
EX_S = LA * float(os.environ.get('EX_F', .75)); ep, eh = track(EX_S, float(os.environ.get('EX_OFF', -7.5)))
et, _ = track(LA + float(os.environ.get('EX_T', 24)), 1.0)
mkcam('exit', ep + Vector((0, 0, float(os.environ.get('EX_Z', 7.5)))), et + Vector((0, 0, -1.2)), float(os.environ.get('EX_LENS', 19)))
# B.5c pass (2026-11-11): the Exit stop now uses the same closer rear-quarter camera as the line_vs_line exit playback
# (line_clash/build_clash.py 'pb_exit', now in art/ui/line_vs_line/; the unapproved line_clash/ copy was removed 2026-11-13, git history), so the pick view and the playback view match. The old 'exit' camera is kept only so
# the cedar keep-out set (and so the rest of the scene) stays identical to that playback scene.
PX_S = LA + float(os.environ.get('PX_S', -5.0)); pxp, _ = track(PX_S, float(os.environ.get('PX_OFF', -5.4)))
pxt, _ = track(LA + float(os.environ.get('PX_T', 9.0)), float(os.environ.get('PX_TOFF', 1.2)))
mkcam('pb_exit', pxp + Vector((0, 0, float(os.environ.get('PX_Z', 3.4)))), pxt + Vector((0, 0, float(os.environ.get('PX_TZ', 0.2)))), float(os.environ.get('PX_LENS', 24)))
for p, h in TREES:
    if any((Vector((p.x, p.y, 0)) - Vector((c.location.x, c.location.y, 0))).length < 5.5 for k_, c in cams.items() if k_ != 'mirror'): continue
    cedar_at(p, h)
mesh_obj('Cedars', verts, faces, uvs, cedar)

for o in PAINTED + IMPORTED: paint(o)
for m in bpy.data.materials:      # chevron faces are one-sided (no mirrored arrows seen from behind)
    if m.name.startswith('U_Chevron'): m.use_backface_culling = True

# ------------------------------------------------------------------ decals, glows, sky
def additive(name, path, strength=1.0, nearest=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(path); t.extension = 'CLIP'
    if nearest: t.interpolation = 'Closest'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'SCALE'; nt.links.new(t.outputs[0], mul.inputs[0]); nt.links.new(t.outputs[1], mul.inputs[3])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value = strength; nt.links.new(mul.outputs[0], em.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs[0])
    m.surface_render_method = 'BLENDED'; return m
def darken(name, path):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(path); t.extension = 'CLIP'
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
pool_m = additive('pool', os.path.join(TEX, f'pool_{TONE}_0.png'), T['pool_k'] * T.get('lane_pool_mul', 1.0), nearest=True)
glow_m = additive('glow_lamp', os.path.join(TEX, f'glow_{TONE}_0.png'), 0.9)
for i, L in enumerate(LAMPS):
    # pool decal follows the road + shoulder only (never floats over the drop-off); UV = world xy around the lamp
    ss = [x for x in samples(S0, S1) if (track(x, 0)[0] - Vector((L.x, L.y, 0))).length < 15]
    offs = [-6.7, -5.0, -2.5, 0.0, 2.5, 5.0, 5.6]; pv = []; pf = []
    for a_, s_ in enumerate(ss):
        for o_ in offs:
            p_, _ = track(s_, o_); pv.append(Vector((p_.x, p_.y, .2 if o_ > -5.01 else .19)))
    for a_ in range(len(ss) - 1):
        for b_ in range(len(offs) - 1):
            k = a_ * len(offs) + b_; pf.append((k, k + 1, k + 1 + len(offs), k + len(offs)))
    me = bpy.data.meshes.new(f'Pool_{i}'); me.from_pydata(pv, [], pf); me.update(); uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = pv[me.loops[li].vertex_index]; uvl.data[li].uv = ((v.x - L.x) / 13 + .5, (v.y - L.y) / 13 + .5)
    po = bpy.data.objects.new(f'Pool_{i}', me); C_WORLD.objects.link(po); me.materials.append(pool_m)
    billboard(f'LampGlow_{i}', L + Vector((0, 0, -0.15)), 1.5, glow_m)
def sky_unlit(name, path, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(path); t.extension = 'EXTEND'; t.interpolation = 'Closest'
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs[0], em.inputs[0])
    if alpha:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = .5; nt.links.new(t.outputs[1], gt.inputs[0])
        nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
        m.surface_render_method = 'DITHERED'
    else: nt.links.new(em.outputs[0], out.inputs[0])
    return m
sky_m = sky_unlit('sky', os.path.join(TEX, f'sky_{TONE}.png'))
ridges = [(sky_unlit('ridgeF', os.path.join(MYTEX, 'ridge_far.png'), True), 270, 70, 0.0), (sky_unlit('ridgeN', os.path.join(MYTEX, 'ridge_near.png'), True), 210, 46, .13)]
SC = Vector((12, 0, 0))
for i in range(12):
    a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
    p0 = SC + Vector((math.cos(a0), math.sin(a0), 0)) * 330; p1 = SC + Vector((math.cos(a1), math.sin(a1), 0)) * 330
    quad_obj(f'Sky_{i}', [p0 + Vector((0, 0, -40)), p1 + Vector((0, 0, -40)), p1 + Vector((0, 0, 330)), p0 + Vector((0, 0, 330))], [(0, 0), (1, 0), (1, 1), (0, 1)], sky_m, C_SKY)
    for j, (m, rr, hh, sh) in enumerate(ridges):
        q0 = SC + Vector((math.cos(a0 + sh), math.sin(a0 + sh), 0)) * rr; q1 = SC + Vector((math.cos(a1 + sh), math.sin(a1 + sh), 0)) * rr
        u0 = (i * .41 + j * .5) % 1
        quad_obj(f'Ridge_{i}_{j}', [q0 + Vector((0, 0, -30)), q1 + Vector((0, 0, -30)), q1 + Vector((0, 0, hh)), q0 + Vector((0, 0, hh))], [(u0, 0), (u0 + .5, 0), (u0 + .5, 1), (u0, 1)], m, C_SKY)
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (*FOG, 1)

# ------------------------------------------------------------------ cars (game .glb) with the A.4 faked shine
ENV = img(os.path.join(TEX, 'env_street.png'))
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
blob_m = darken('blob', os.path.join(TEX, 'blob_shadow.png'))
gh = additive('glow_head', os.path.join(TEX, 'glow_head.png'), 0.20); gtl = additive('glow_tail', os.path.join(TEX, 'glow_tail.png'), .65)
CAR_OBJS = {}
def car(glb, root_name, prefix, loc, head, tail, shine):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        C_CAR.objects.link(o)
        if '_FX_' in o.name: o.hide_render = True
    for m in {m for o in new if o.type == 'MESH' for m in o.data.materials if m}:
        for k, kw in shine.items():
            if m.name.startswith(prefix + k): fake_shine(m, **kw)
    root = bpy.data.objects[root_name]; root.rotation_mode = 'XYZ'; root.location = loc; root.rotation_euler = (0, 0, math.pi)
    b = quad_obj(prefix + 'Blob', [(-1.15, -2.6, .012), (1.15, -2.6, .012), (1.15, 2.6, .012), (-1.15, 2.6, .012)], [(0, 1), (0, 0), (1, 0), (1, 1)], blob_m, C_CAR); b.parent = root
    extra = [b]
    for sx in (1, -1):
        bh = billboard(prefix + f'Head{sx}', (sx * head[0], head[1], head[2]), .42, gh, C_CAR, root); bh['face'] = (0, -1, 0)
        bt = billboard(prefix + f'Tail{sx}', (sx * tail[0], tail[1], tail[2]), .75, gtl, C_CAR, root); bt['face'] = (0, 1, 0); extra += [bh, bt]
    CAR_OBJS[prefix] = [o for o in new] + extra
    return root
PAINT = dict(spec=.55, env=.22, amb=.5, tint=(.80, .86, 1.0)); GLASS = dict(spec=.9, env=.45, amb=.4, tint=(.55, .75, 1.0))
player = car(CARS + 'mx5/car_mx5.glb', 'MX5-vehicle', 'MX5_', PLAYER_ROOT, (.60, -1.92, .63), (.64, 1.90, .76),
             {'Paint': PAINT, 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})
RIVAL_ROOT = Vector((LANE['OUT'], -16.0, .16))     # rival 12 m ahead, Entry lane OUTSIDE = ATK tell (right hairpin)
rival = car(CARS + 's2000/car_s2000.glb', 'S2000-vehicle', 'S2000_', RIVAL_ROOT, (.61, -2.1, .64), (.66, 2.04, .75),
            {'Paint': dict(spec=.55, env=.28, amb=.5, tint=(.8, .86, 1.0)), 'Glass': GLASS, 'Lamp': dict(emissive=.9, spec=.5, env=.2), 'Under': dict(spec=.05, env=.03)})
for g in GLOWS:
    c = g.constraints.new('TRACK_TO'); c.track_axis = 'TRACK_NEGATIVE_Y'; c.up_axis = 'UP_Z'

# ------------------------------------------------------------------ render
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
def scr(c, p, w=640, h=480):
    v = world_to_camera_view(sc, c, Vector(p)); return [round(v.x * w, 1), round((1 - v.y) * h, 1), round(v.z, 2)]
PHASE_S = {'chase': -3.0, 'apex': LA / 2, 'exit': LA + 9.0}
def render(shot, w=640, h=480, glow=True, rival_on=True):
    c = cams[{'exit': 'pb_exit'}.get(shot, shot)]; sc.camera = c; sc.render.resolution_x, sc.render.resolution_y = w, h
    for o in CAR_OBJS['S2000_']:
        o.hide_render = not rival_on
    for g in GLOWS:
        for con in g.constraints:
            if con.type == 'TRACK_TO': con.target = c
        if 'face' in g:
            if 'S2000_' in g.name and not rival_on: g.hide_render = True; continue
            fw = (g.parent.matrix_world.to_3x3() @ Vector(g['face'])).normalized(); wp = g.matrix_world.translation
            g.hide_render = fw.dot((c.location - wp).normalized()) < .15
    for o in bpy.data.objects:
        if o.type == 'MESH': o.is_holdout = False
    bpy.context.view_layer.update()
    sc.render.film_transparent = False; sc.render.image_settings.color_mode = 'RGB'
    sc.render.filepath = os.path.join(RAW, f'raw_{shot}.png'); bpy.ops.render.render(write_still=True)
    if glow:
        names = {g.name for g in GLOWS if not g.hide_render}
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name not in names and not o.hide_render: o.is_holdout = True
        sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
        sc.render.filepath = os.path.join(RAW, f'glow_{shot}.png'); bpy.ops.render.render(write_still=True)
    if shot in PHASE_S:
        s = PHASE_S[shot]
        A = {'lanes': {k: scr(c, track(s, o)[0] + Vector((0, 0, .2))) for k, o in LANE.items()},
             'player': scr(c, player.location + Vector((0, 0, 1.4))), 'rival': scr(c, rival.location + Vector((0, 0, 1.4))),
             'camera': list(c.location), 'lens': c.data.lens}
        json.dump(A, open(os.path.join(RAW, f'anchors_{shot}.json'), 'w'), indent=1)
SHOTS = os.environ.get('SHOTS', 'chase,mirror,apex,exit').split(',')
for shot in SHOTS:
    if shot == 'mirror': render('mirror', 192, 64, glow=False)
    else: render(shot, rival_on=(shot == 'chase'))
    print('SHOT_DONE', shot, flush=True)
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and o.users_collection and o.users_collection[0].name in ('World',))
print('WORLD_TRIANGLES', tri)
if os.environ.get('SAVE_BLEND', '1') == '1': bpy.ops.wm.save_as_mainfile(filepath=os.path.join(RAW, 'scene_line_select_cam.blend'))
print('DONE')
