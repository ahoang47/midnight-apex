# Blender 4.2 headless: turnout parking-lot kit + assembled preview + raw views.
#   blender -b -P blender/build_kit.py
# Env (length-adjustable): POCKET_M TAPER_M POCKET_W N_LAMPS CURVE_R STALL_W STALL_ANGLE
# Axes (Blender): +X = away from the road (into the lot), Y = along the road, Z = up.
# Module road-facing edge sits at x = 0. glTF export uses +Y up.
import bpy, bmesh, os, math, json, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TEX = os.path.join(ROOT, 'tex')
OUT = os.path.join(ROOT, 'glb')
RAW = os.path.join(ROOT, 'renders', 'raw')
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

def envf(name, default):
    v = os.environ.get(name)
    return float(v) if v not in (None, '') else float(default)

def envi(name, default):
    v = os.environ.get(name)
    return int(v) if v not in (None, '') else int(default)

# Defaults follow Gordon's display.json turnout placeholders, widened for the
# two-row angled layout in Austin's Hakone-style reference photo.
ROAD_W = envf('ROAD_W', 7.5)
POCKET_M = envf('POCKET_M', 62.0)
TAPER_M = envf('TAPER_M', 14.0)
POCKET_W = envf('POCKET_W', 16.0)
N_LAMPS = max(2, min(4, envi('N_LAMPS', 3)))
CURVE_R = envf('CURVE_R', 100.0)
STALL_W = envf('STALL_W', 2.6)
STALL_D = envf('STALL_D', 5.0)
STALL_ANGLE = envf('STALL_ANGLE', 70.0)  # deg from the road axis; 90 = perpendicular
CURB_H = envf('CURB_H', 0.15)
ISLAND_0 = envf('ISLAND_0', 0.15)
ISLAND_1 = envf('ISLAND_1', 0.75)
APPROACH = envf('APPROACH', 24.0)
AISLE_W = envf('AISLE_W', 5.5)
MODULE_L = 5.0
RAIL_L = 4.0
CURB_L = 4.0

RH = ROAD_W * 0.5          # road half-width
S0 = APPROACH              # pocket starts here along the path
S1 = APPROACH + POCKET_M
S_MID = 0.5 * (S0 + S1)
ROAD_A = S0 - APPROACH     # 0
ROAD_B = S1 + APPROACH

STATS = []
_mats = {}

# ---------------------------------------------------------------------------
# Path: gentle bend, lot on the OUTSIDE (+X at mid). Preview only; pieces are straight.
# ---------------------------------------------------------------------------
class Path:
    def __init__(self, R, s_mid):
        self.R = float(R); self.s_mid = float(s_mid)
    def ang(self, s):
        return (s - self.s_mid) / self.R
    def point(self, s, d=0.0, z=0.0):
        a = self.ang(s)
        ca, sa = math.cos(a), math.sin(a)
        # centreline + outward normal * d
        x = self.R * (ca - 1.0) + d * ca
        y = self.s_mid + self.R * sa + d * sa
        return Vector((x, y, z))
    def heading(self, s):
        return self.ang(s)  # yaw about Z; 0 => +Y
    def frame(self, s, d=0.0, z=0.0):
        a = self.ang(s)
        loc = self.point(s, d, z)
        # object +Y = tangent, +X = outward, +Z = up
        rot = Matrix.Rotation(a, 4, 'Z')
        return loc, rot
    def place(self, ob, s, d, z=0.0, yaw=0.0):
        loc, rot = self.frame(s, d, z)
        if yaw:
            rot = rot @ Matrix.Rotation(yaw, 4, 'Z')
        ob.matrix_world = Matrix.Translation(loc) @ rot
        return ob

# ---------------------------------------------------------------------------
# Scene / materials
# ---------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    bpy.context.scene.unit_settings.system = 'METRIC'

def load_img(name):
    path = os.path.join(TEX, name + '.png')
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'sRGB'
    img.alpha_mode = 'STRAIGHT'
    return img

def mat(name, tex, kind='surface', interp='Linear', alpha=None):
    """alpha: None, 'CLIP', or 'BLEND'."""
    key = (name, tex, kind, interp, alpha)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m['lot_kind'] = kind
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 1.0
    texn = nt.nodes.new('ShaderNodeTexImage')
    texn.image = load_img(tex)
    texn.interpolation = interp
    nt.links.new(texn.outputs['Color'], em.inputs['Color'])
    if alpha:
        trans = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(texn.outputs['Alpha'], mix.inputs['Fac'])
        nt.links.new(trans.outputs['BSDF'], mix.inputs[1])
        nt.links.new(em.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
        m.blend_method = 'CLIP' if alpha == 'CLIP' else 'BLEND'
        if hasattr(m, 'shadow_method'):
            m.shadow_method = 'NONE'
        m.use_backface_culling = True
        if hasattr(m, 'show_transparent_back'):
            m.show_transparent_back = False
    else:
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        m.blend_method = 'OPAQUE'
    _mats[key] = m
    return m

KIND_COLOR = {
    'surface': (0.15, 0.25, 0.95, 1),
    'decal':   (0.15, 0.95, 0.20, 1),
    'prop':    (0.95, 0.15, 0.12, 1),
    'emit':    (0.95, 0.95, 0.15, 1),
    'card':    (0.15, 0.90, 0.90, 1),
    'pool':    (0.95, 0.20, 0.90, 1),
}

class Builder:
    def __init__(self, name, kind='prop'):
        self.name = name
        self.kind = kind
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []
    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)
    def quad(self, vs, uvs, m):
        bv = [self.bm.verts.new(Vector(v)) for v in vs]
        f = self.bm.faces.new(bv)
        f.material_index = self.mi(m)
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = uv
        return f
    def tri(self, vs, uvs, m):
        bv = [self.bm.verts.new(Vector(v)) for v in vs]
        f = self.bm.faces.new(bv)
        f.material_index = self.mi(m)
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = uv
    def box(self, c, s, m, faces='all', uvscale=1.0):
        cx, cy, cz = c
        sx, sy, sz = s
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy - sy / 2, cy + sy / 2
        z0, z1 = cz, cz + sz
        F = {
            '-x': ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], sy, sz),
            '+x': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], sy, sz),
            '-y': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], sx, sz),
            '+y': ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], sx, sz),
            '+z': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], sx, sy),
            '-z': ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], sx, sy),
        }
        keys = F.keys() if faces == 'all' else faces
        for k in keys:
            vs, la, lb = F[k]
            self.quad(vs, [(0, 0), (la / uvscale, 0), (la / uvscale, lb / uvscale), (0, lb / uvscale)], m)
    def cyl(self, c, r0, r1, h, m, n=6, uvscale=1.0, cap=True):
        cx, cy, cz = c
        for i in range(n):
            a0 = 2 * math.pi * i / n
            a1 = 2 * math.pi * (i + 1) / n
            p = lambda a, r, z: (cx + r * math.cos(a), cy + r * math.sin(a), cz + z)
            self.quad([p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, h), p(a0, r1, h)],
                      [(i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, h / uvscale), (i / n, h / uvscale)], m)
            if cap:
                self.tri([(cx, cy, cz + h), p(a0, r1, h), p(a1, r1, h)], [(0.5, 0.5), (0, 0), (1, 0)], m)
    def finish(self, smooth=False, tess=False):
        if tess:
            for f in [f for f in self.bm.faces if f.calc_area() > 12.0]:
                if not f.is_valid:
                    continue
                cuts = min(2, max(1, int(math.sqrt(f.calc_area()) / 3.0)))
                bmesh.ops.subdivide_edges(self.bm, edges=list(f.edges), cuts=cuts, use_grid_fill=True)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        self.bm.normal_update()
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        ob['lot_kind'] = self.kind
        ob.color = KIND_COLOR.get(self.kind, (1, 1, 1, 1))
        bpy.context.scene.collection.objects.link(ob)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        return ob

def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def export_glb(name, objects=None):
    if objects is None:
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True,
        export_apply=True, export_yup=True, export_image_format='AUTO',
        export_materials='EXPORT', export_cameras=False, export_lights=False,
    )
    ntris = sum(tris_of(o) for o in objects if o.type == 'MESH')
    STATS.append({'name': name, 'tris': ntris, 'path': path})
    print('EXPORT', name, ntris)

# ---------------------------------------------------------------------------
# Modular pieces (straight, origin at road-facing edge / base)
# ---------------------------------------------------------------------------
def piece_asphalt_module(name='lot_asphalt_module', length=MODULE_L, width=None, tex='lot_asphalt'):
    width = POCKET_W if width is None else width
    b = Builder(name, 'surface')
    m = mat('lot_asphalt', tex, 'surface', 'Linear')
    # x 0..width (away from road), y -L/2..L/2, z = 0
    x0, x1, y0, y1 = 0.0, width, -length / 2, length / 2
    # UV in metres / 8 m tile
    tile = 8.0
    b.quad([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)],
           [(0, 0), (width / tile, 0), (width / tile, length / tile), (0, length / tile)], m)
    return b.finish(tess=True)

def piece_asphalt_taper(name='lot_asphalt_taper', length=None, width=None, tex='lot_asphalt'):
    """Right-hand taper: at y=0 width=0, at y=length width=full. Entry uses this;
    exit is the same mesh rotated 180° about Z."""
    length = TAPER_M if length is None else length
    width = POCKET_W if width is None else width
    b = Builder(name, 'surface')
    m = mat('lot_asphalt', tex, 'surface', 'Linear')
    tile = 8.0
    # trapezoid with a sliver at the tip so UVs stay sane: tip is 0.15 m wide
    tip = 0.15
    b.quad([(0, 0, 0), (tip, 0, 0), (width, length, 0), (0, length, 0)],
           [(0, 0), (tip / tile, 0), (width / tile, length / tile), (0, length / tile)], m)
    return b.finish(tess=True)

def piece_road_module(name='lot_road_module', length=MODULE_L):
    b = Builder(name, 'surface')
    m = mat('lot_road', 'lot_road', 'surface', 'Linear')
    x0, x1, y0, y1 = -RH, RH, -length / 2, length / 2
    tile = 8.0
    b.quad([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)],
           [(0, 0), (ROAD_W / tile, 0), (ROAD_W / tile, length / tile), (0, length / tile)], m)
    return b.finish(tess=True)

def piece_island_curb(name='lot_island_curb', length=CURB_L):
    b = Builder(name, 'prop')
    m = mat('lot_curb', 'lot_curb', 'prop', 'Linear')
    w = ISLAND_1 - ISLAND_0
    # origin at the road-facing bottom edge, centre of the module
    b.box((w / 2, 0, 0), (w, length, CURB_H), m, uvscale=2.0)
    return b.finish()

def piece_island_end(name='lot_island_end'):
    """Short end-cap / bullnose for the island at a taper opening."""
    b = Builder(name, 'prop')
    m = mat('lot_curb', 'lot_curb', 'prop', 'Linear')
    w = ISLAND_1 - ISLAND_0
    b.box((w / 2, 0, 0), (w, 0.6, CURB_H), m, uvscale=1.0)
    return b.finish()

def piece_wheel_stop(name='lot_wheel_stop'):
    b = Builder(name, 'prop')
    m = mat('lot_wheel_stop', 'lot_wheel_stop', 'prop', 'Linear')
    # 1.6 x 0.16 x 0.13, long axis Y (rotated on place to sit across the stall)
    b.box((0, 0, 0), (0.16, 1.6, 0.13), m, uvscale=1.0)
    return b.finish()

def piece_guardrail(name='lot_guardrail', length=RAIL_L):
    b = Builder(name, 'prop')
    m = mat('lot_guardrail', 'lot_guardrail', 'prop', 'Linear')
    # W-beam facing -X (toward the lot when +X is outward), posts behind it.
    prof = [(0.00, 0.80), (-0.06, 0.70), (0.00, 0.62), (-0.06, 0.52), (0.00, 0.44)]
    for k in range(len(prof) - 1):
        (xa, za), (xb, zb) = prof[k], prof[k + 1]
        va, vb = 1 - k / (len(prof) - 1), 1 - (k + 1) / (len(prof) - 1)
        b.quad([(xb, length / 2, zb), (xb, -length / 2, zb), (xa, -length / 2, za), (xa, length / 2, za)],
               [(1, vb), (0, vb), (0, va), (1, va)], m)
    for y in (-length / 4, length / 4):
        b.box((0.10, y, 0.0), (0.10, 0.10, 0.78), m, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=1.0)
    return b.finish()

def piece_lamp_pole(name='lot_lamp_pole'):
    b = Builder(name, 'prop')
    pole = mat('lot_pole', 'lot_pole', 'prop', 'Linear')
    metal = mat('lot_metal', 'lot_metal', 'prop', 'Linear')
    emit = mat('Emit_sodium', 'emit_sodium', 'emit', 'Linear')
    # post at origin, arm toward +X (into the lot)
    b.cyl((0, 0, 0), 0.11, 0.08, 6.15, pole, n=6, uvscale=3.0)
    b.box((0.85, 0, 5.95), (1.7, 0.07, 0.07), metal, uvscale=1.0)
    b.box((1.65, 0, 5.82), (0.38, 0.18, 0.12), metal, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=1.0)
    # emit underside of the head
    b.quad([(1.46, -0.10, 5.81), (1.84, -0.10, 5.81), (1.84, 0.10, 5.81), (1.46, 0.10, 5.81)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], emit)
    return b.finish()

def piece_glow(name='lot_glow_sprite'):
    b = Builder(name, 'emit')
    m = mat('lot_glow', 'lot_glow', 'emit', 'Linear', alpha='BLEND')
    s = 0.9
    b.quad([(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return b.finish()

def piece_pool(name='lot_pool_decal'):
    b = Builder(name, 'pool')
    m = mat('lot_pool', 'lot_pool', 'pool', 'Linear', alpha='BLEND')
    # oval: 14 m along the aisle (Y) x 10 m across, so it doesn't stamp a hard circle from above
    sx, sy = 4.0, 5.0
    b.quad([(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return b.finish()

def piece_vending(name='lot_vending'):
    b = Builder(name, 'prop')
    body = mat('lot_vending_body', 'lot_vending_body', 'prop', 'Linear')
    front = mat('Emit_vending_front', 'emit_vending_front', 'emit', 'Linear')
    # front faces -X (toward the road / aisle when +X is outward)
    b.box((0.38, 0, 0), (0.75, 1.0, 1.85), body, faces=['+x', '-y', '+y', '+z'], uvscale=1.0)
    b.quad([(0.005, -0.50, 0.0), (0.005, 0.50, 0.0), (0.005, 0.50, 1.85), (0.005, -0.50, 1.85)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], front)
    return b.finish()

def piece_sign(name='lot_sign'):
    b = Builder(name, 'prop')
    metal = mat('lot_metal', 'lot_metal', 'prop', 'Linear')
    face = mat('lot_sign_face', 'lot_sign_face', 'prop', 'Linear')
    b.cyl((0, 0, 0), 0.035, 0.03, 2.35, metal, n=6, uvscale=1.0, cap=True)
    # A single double-sided plate (no metal box covering the art). +Z up, faces ±Y.
    b.quad([(-0.28, 0.0, 2.05), (0.28, 0.0, 2.05), (0.28, 0.0, 2.75), (-0.28, 0.0, 2.75)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], face)
    b.quad([(0.28, 0.0, 2.05), (-0.28, 0.0, 2.05), (-0.28, 0.0, 2.75), (0.28, 0.0, 2.75)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], face)
    return b.finish()

def piece_decal_plane(name, tex, size, kind='decal', interp='Closest'):
    """size = (width_x, length_y). Origin at centre, z=0, sits in XY."""
    b = Builder(name, kind)
    m = mat(name, tex, kind, interp, alpha='CLIP')
    sx, sy = size
    b.quad([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return b.finish()

def piece_cedar(name='lot_cedar_card', tex='touge_cedar_a', h=11.0, w=None):
    w = (h * 64 / 192) if w is None else w
    b = Builder(name, 'card')
    m = mat(name + '_' + tex, tex, 'card', 'Closest', alpha='CLIP')
    # cross card, +X / +Y planes, origin at the ground
    # plane 1: in XZ, facing ±Y
    b.quad([(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    # plane 2: in YZ, facing ±X
    b.quad([(0, -w / 2, 0), (0, w / 2, 0), (0, w / 2, h), (0, -w / 2, h)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return b.finish()

def export_pieces():
    specs = [
        ('lot_asphalt_module', lambda: piece_asphalt_module()),
        ('lot_asphalt_taper', lambda: piece_asphalt_taper()),
        ('lot_road_module', lambda: piece_road_module()),
        ('lot_island_curb', lambda: piece_island_curb()),
        ('lot_island_end', lambda: piece_island_end()),
        ('lot_wheel_stop', lambda: piece_wheel_stop()),
        ('lot_guardrail', lambda: piece_guardrail()),
        ('lot_lamp_pole', lambda: piece_lamp_pole()),
        ('lot_glow_sprite', lambda: piece_glow()),
        ('lot_pool_decal', lambda: piece_pool()),
        ('lot_vending', lambda: piece_vending()),
        ('lot_sign', lambda: piece_sign()),
        ('lot_decal_stall', lambda: piece_decal_plane('lot_decal_stall', 'lot_decal_stall', (0.14, 5.0))),
        ('lot_decal_arrow', lambda: piece_decal_plane('lot_decal_arrow', 'lot_decal_arrow', (0.9, 2.6))),
        ('lot_decal_chevron', lambda: piece_decal_plane('lot_decal_chevron', 'lot_decal_chevron', (2.8, 2.2))),
        ('lot_decal_center_line', lambda: piece_decal_plane('lot_decal_center_line', 'lot_decal_center', (0.15, 4.0))),
        ('lot_decal_edge_line', lambda: piece_decal_plane('lot_decal_edge_line', 'lot_decal_edge', (0.15, 4.0))),
        ('lot_cedar_card', lambda: piece_cedar()),
    ]
    for name, fn in specs:
        reset()
        fn()
        export_glb(name)

# ---------------------------------------------------------------------------
# Assembled preview (gentle bend, lot on the outside)
# ---------------------------------------------------------------------------
def ribbon(name, pth, s0, s1, d0, d1, z, mat_, kind, tile=8.0, step=2.5, z1=None):
    """A strip along the path from (s0,d0) to (s1,d1). z1 if the outer edge drops."""
    b = Builder(name, kind)
    n = max(2, int(math.ceil(abs(s1 - s0) / step)))
    z1 = z if z1 is None else z1
    for i in range(n):
        sa = s0 + (s1 - s0) * (i / n)
        sb = s0 + (s1 - s0) * ((i + 1) / n)
        p00, p10 = pth.point(sa, d0, z), pth.point(sa, d1, z1)
        p01, p11 = pth.point(sb, d0, z), pth.point(sb, d1, z1)
        u0, u1 = d0 / tile, d1 / tile
        v0, v1 = sa / tile, sb / tile
        b.quad([p00, p10, p11, p01], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat_)
    return b.finish(tess=False)

def box_strip(name, pth, s0, s1, d0, d1, h, mat_, kind='prop', step=2.0):
    """Raised curb-like box following the path (top + sides + end caps)."""
    b = Builder(name, kind)
    n = max(1, int(math.ceil(abs(s1 - s0) / step)))
    def ring(s, z):
        return pth.point(s, d0, z), pth.point(s, d1, z)
    for i in range(n):
        sa = s0 + (s1 - s0) * (i / n)
        sb = s0 + (s1 - s0) * ((i + 1) / n)
        a0, a1 = ring(sa, 0); A0, A1 = ring(sa, h)
        c0, c1 = ring(sb, 0); C0, C1 = ring(sb, h)
        # top
        b.quad([A0, A1, C1, C0], [(0, 0), (1, 0), (1, 1), (0, 1)], mat_)
        # sides
        b.quad([a0, c0, C0, A0], [(0, 0), (1, 0), (1, 1), (0, 1)], mat_)
        b.quad([a1, A1, C1, c1], [(0, 0), (1, 0), (1, 1), (0, 1)], mat_)
    # end caps
    for s, flip in ((s0, False), (s1, True)):
        a0, a1 = ring(s, 0); A0, A1 = ring(s, h)
        vs = [a0, a1, A1, A0] if not flip else [a1, a0, A0, A1]
        b.quad(vs, [(0, 0), (1, 0), (1, 1), (0, 1)], mat_)
    return b.finish()

def unique(name):
    """Avoid object-name collisions when instancing pieces."""
    base = name
    i = 1
    existing = {o.name for o in bpy.data.objects}
    while name in existing:
        i += 1
        name = '%s_%d' % (base, i)
    return name

def instance(fn, name, pth, s, d, z=0.0, yaw=0.0):
    ob = fn()
    ob.name = unique(name)
    pth.place(ob, s, d, z, yaw=yaw)
    return ob

def assemble(pth):
    """Build the full preview scene. Returns layout dict."""
    layout = {
        'pocket_m': POCKET_M, 'taper_m': TAPER_M, 'pocket_w_m': POCKET_W,
        'road_w_m': ROAD_W, 'curve_r_m': CURVE_R, 'n_lamps': N_LAMPS,
        'stall_w_m': STALL_W, 'stall_d_m': STALL_D, 'stall_angle_deg': STALL_ANGLE,
        's0': S0, 's1': S1, 'aisle_w_m': AISLE_W,
        'island_d_m': [ISLAND_0, ISLAND_1], 'curb_h_m': CURB_H,
        'how_to_set_length': 'POCKET_M TAPER_M POCKET_W N_LAMPS CURVE_R ./run.sh',
        'pieces': [],
    }
    m_asph = mat('lot_asphalt', 'lot_asphalt', 'surface', 'Linear')
    m_road = mat('lot_road', 'lot_road', 'surface', 'Linear')
    m_curb = mat('lot_curb', 'lot_curb', 'prop', 'Linear')
    m_verge = mat('lot_verge', 'lot_verge', 'surface', 'Linear')
    m_cut = mat('lot_cut_slope', 'lot_cut_slope', 'surface', 'Linear')
    m_sky = mat('lot_sky', 'lot_sky', 'surface', 'Linear')

    # --- sky dome (inside-facing hemisphere) ---
    bsky = Builder('lot_sky', 'surface')
    Rsky = 280.0
    # sit the dome on the path mid-point so the camera stays well inside it
    mid = pth.point(S_MID, 0.0, 0.0)
    segs, rings = 24, 10
    for i in range(rings):
        # start slightly below the horizon so there is no equator gap
        v0, v1 = (i / rings) * 1.08 - 0.08, ((i + 1) / rings) * 1.08 - 0.08
        v0, v1 = max(v0, -0.08), max(v1, -0.08)
        z0, z1 = Rsky * math.sin(v0 * math.pi * 0.5), Rsky * math.sin(v1 * math.pi * 0.5)
        r0, r1 = Rsky * math.cos(v0 * math.pi * 0.5), Rsky * math.cos(v1 * math.pi * 0.5)
        for j in range(segs):
            a0, a1 = 2 * math.pi * j / segs, 2 * math.pi * (j + 1) / segs
            def P(r, a, z):
                return (mid.x + r * math.cos(a), mid.y + r * math.sin(a), z)
            # inward faces (CW)
            bsky.quad([P(r0, a1, z0), P(r0, a0, z0), P(r1, a0, z1), P(r1, a1, z1)],
                      [(j / segs, max(0, v0)), ((j + 1) / segs, max(0, v0)),
                       ((j + 1) / segs, max(0, v1)), (j / segs, max(0, v1))], m_sky)
    bsky.finish()

    # --- road ---
    ribbon('lot_road_surface', pth, ROAD_A, ROAD_B, -RH, RH, 0.0, m_road, 'surface', step=2.5)

    # --- lot asphalt: full-depth mid section + tapers ---
    mid_a, mid_b = S0 + TAPER_M, S1 - TAPER_M
    d_edge, d_back = RH, RH + POCKET_W
    ribbon('lot_asphalt_mid', pth, mid_a, mid_b, d_edge - 0.02, d_back, 0.0, m_asph, 'surface', step=2.5)

    def taper_mesh(name, s_start, s_end, grow):
        # grow=+1: width 0 -> full as s increases (entry). grow=-1: full -> 0 (exit).
        b = Builder(name, 'surface')
        n = 8
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            if grow > 0:
                w0, w1 = POCKET_W * u0, POCKET_W * u1
            else:
                w0, w1 = POCKET_W * (1 - u0), POCKET_W * (1 - u1)
            # keep a sliver at the tip
            w0 = max(w0, 0.12); w1 = max(w1, 0.12)
            sa = s_start + (s_end - s_start) * u0
            sb = s_start + (s_end - s_start) * u1
            p00 = pth.point(sa, d_edge - 0.02, 0)
            p10 = pth.point(sa, d_edge - 0.02 + w0, 0)
            p01 = pth.point(sb, d_edge - 0.02, 0)
            p11 = pth.point(sb, d_edge - 0.02 + w1, 0)
            tile = 8.0
            b.quad([p00, p10, p11, p01],
                   [(0, sa / tile), (w0 / tile, sa / tile), (w1 / tile, sb / tile), (0, sb / tile)], m_asph)
        return b.finish()

    taper_mesh('lot_asphalt_entry', S0, mid_a, +1)
    taper_mesh('lot_asphalt_exit', mid_b, S1, -1)

    # gravel / verge strip behind the rail, and a forest floor
    ribbon('lot_verge_back', pth, mid_a, mid_b, d_back, d_back + 10.0, 0.04, m_verge, 'surface', step=3.0)
    # taper flanks: verge follows the diagonal
    for s_a, s_b, grow in ((S0, mid_a, +1), (mid_b, S1, -1)):
        b = Builder('lot_verge_flank', 'surface')
        n = 6
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            def w(u, g):
                return POCKET_W * (u if g > 0 else (1 - u))
            sa = s_a + (s_b - s_a) * u0
            sb = s_a + (s_b - s_a) * u1
            w0, w1 = w(u0, grow), w(u1, grow)
            p00 = pth.point(sa, d_edge + w0, 0.04)
            p10 = pth.point(sa, d_edge + w0 + 8.0, 0.04)
            p01 = pth.point(sb, d_edge + w1, 0.04)
            p11 = pth.point(sb, d_edge + w1 + 8.0, 0.04)
            b.quad([p00, p10, p11, p01], [(0, 0), (1, 0), (1, 1), (0, 1)], m_verge)
        b.finish()

    # inside-of-bend drop (context, not part of the kit proper)
    ribbon('lot_cut_slope', pth, ROAD_A, ROAD_B, -RH - 0.05, -RH - 14.0, 0.0, m_cut, 'surface',
           step=3.0, z1=-7.0)
    ribbon('lot_verge_shoulder', pth, ROAD_A, ROAD_B, -RH - 0.05, -RH, 0.03, m_verge, 'surface', step=3.0)

    # --- island curb between road and lot, openings at both tapers ---
    d_ia, d_ib = RH + ISLAND_0, RH + ISLAND_1
    cap = 0.8
    box_strip('lot_island_curb_run', pth, mid_a + cap, mid_b - cap, d_ia, d_ib, CURB_H, m_curb, step=2.0)
    # bullnoses
    box_strip('lot_island_end_a', pth, mid_a + cap - 0.6, mid_a + cap, d_ia, d_ib, CURB_H, m_curb, step=0.6)
    box_strip('lot_island_end_b', pth, mid_b - cap, mid_b - cap + 0.6, d_ia, d_ib, CURB_H, m_curb, step=0.6)

    # a low back curb under the guardrail along the mid section
    box_strip('lot_back_curb', pth, mid_a, mid_b, d_back - 0.20, d_back + 0.15, 0.12, m_curb, step=2.0)

    # --- white guardrail along the outer edge, including taper diagonals ---
    def rail_along(s_a, s_b, d_fn, yaw_extra=0.0):
        length = abs(s_b - s_a)
        # for a diagonal, the actual path length is longer
        n = max(1, int(math.ceil(length / RAIL_L)))
        for i in range(n):
            u = (i + 0.5) / n
            s = s_a + (s_b - s_a) * u
            d = d_fn(s)
            # yaw: follow the outer-edge tangent. For a taper diagonal, add the flare angle.
            instance(piece_guardrail, 'lot_guardrail', pth, s, d, 0.0, yaw=yaw_extra)

    rail_along(mid_a, mid_b, lambda s: d_back)
    # flare rails along each taper's outer edge
    flare = math.atan(POCKET_W / TAPER_M)
    rail_along(S0 + 1.0, mid_a, lambda s: d_edge + POCKET_W * max(0.05, (s - S0) / TAPER_M), yaw_extra=flare)
    rail_along(mid_b, S1 - 1.0, lambda s: d_edge + POCKET_W * max(0.05, (S1 - s) / TAPER_M), yaw_extra=-flare)

    # --- decals: centre line, edge line, chevrons, stall lines, arrows ---
    def stamp_line(tex_name, size, s_a, s_b, d, z=0.025, step=None):
        L = size[1]
        step = L if step is None else step
        s = s_a + L / 2
        while s + L / 2 <= s_b + 1e-4:
            instance(lambda tn=tex_name, sz=size: piece_decal_plane(tn, tn, sz),
                     tex_name, pth, s, d, z)
            s += step

    # yellow centre line along the visible road
    stamp_line('lot_decal_center', (0.15, 4.0), ROAD_A + 1, ROAD_B - 1, 0.0, z=0.022)
    # white edge line on the road face of the island (mid section only — openings stay clear)
    stamp_line('lot_decal_edge', (0.15, 4.0), mid_a + cap, mid_b - cap, RH + 0.04, z=0.023)
    # orange-red chevrons in the lot-side lane, direction of travel = +Y / +s
    lane_d = RH * 0.5  # centre of the right lane (~1.875 m)
    # yaw=pi: the chevron texture's tip is at +Y, but after UV/path it pointed toward -s; flip so it points with traffic.
    def stamp_chevron(s_a, s_b, d, z=0.024, step=2.35):
        L = 2.2
        s = s_a + L / 2
        while s + L / 2 <= s_b + 1e-4:
            instance(lambda: piece_decal_plane('lot_decal_chevron', 'lot_decal_chevron', (2.8, 2.2)),
                     'lot_decal_chevron', pth, s, d, z, yaw=math.pi)
            s += step
    stamp_chevron(S0 - 2.0, S1 + 2.0, lane_d)

    # stall rows
    ang = math.radians(STALL_ANGLE)
    # spacing along the road so the bay is STALL_W measured across the stall
    spacing = STALL_W / max(0.35, math.sin(ang))
    stall_perp = STALL_D * math.sin(ang)
    aisle_start = d_ib + 0.05
    aisle_end = aisle_start + AISLE_W
    # centre row sits just after the through-aisle; outer row against the rail
    centre_d = aisle_end + stall_perp * 0.5
    outer_d = d_back - stall_perp * 0.5
    # keep a small gap if they would overlap
    if outer_d - centre_d < stall_perp * 0.55:
        mid = 0.5 * (aisle_end + d_back)
        centre_d = mid - stall_perp * 0.55
        outer_d = mid + stall_perp * 0.55

    # stall lines live in the straight mid pocket, inset 1 m from the taper joints
    row_a, row_b = mid_a + 1.2, mid_b - 1.2
    n_st = max(1, int(math.floor((row_b - row_a) / spacing)))
    # centre the row
    st0 = 0.5 * (row_a + row_b) - n_st * spacing * 0.5

    def stall_row(d_row, s_offset, yaw_off=0.0):
        placed = []
        for i in range(n_st + 1):
            s = st0 + i * spacing + s_offset
            if s < row_a - 0.2 or s > row_b + 0.2:
                continue
            # line yaw: stall lines run at STALL_ANGLE from +s, out into the lot
            # piece_decal_stall is long along +Y; rotate so +Y follows the stall axis
            yaw = (math.pi / 2 - ang) + yaw_off
            instance(lambda: piece_decal_plane('lot_decal_stall', 'lot_decal_stall', (0.14, STALL_D)),
                     'lot_decal_stall', pth, s, d_row, 0.026, yaw=yaw)
            placed.append(s)
        return placed

    # same angle for both rows (matches the ref); slight s-offset on the centre row
    outer_ss = stall_row(outer_d, 0.0)
    centre_ss = stall_row(centre_d, spacing * 0.35)

    # wheel stops at the deep end of each bay (not on the last divider)
    def stops_for(ss, d_row, toward=+1):
        # toward=+1: deep end is further out (outer row, against the rail)
        # toward=-1: deep end is further in? For centre row, cars pull in from the aisle
        # so the deep end is the far side of the stall (further out, +d) if they pull from the aisle.
        # Both rows: pull from the through-aisle / mid-aisle toward +d, so deep end is +d.
        d_stop = d_row + toward * (stall_perp * 0.5 - 0.35)
        for a, b_ in zip(ss[:-1], ss[1:]):
            s = 0.5 * (a + b_)
            # wheel stop long axis is Y on the piece; rotate to sit across the stall (perp to stall axis)
            yaw = (math.pi / 2 - ang) + math.pi / 2
            instance(piece_wheel_stop, 'lot_wheel_stop', pth, s, d_stop, 0.0, yaw=yaw)

    stops_for(outer_ss, outer_d, toward=+1)
    stops_for(centre_ss, centre_d, toward=+1)

    # white arrows in the through-aisle, pointing toward the exit (+s)
    aisle_d = 0.5 * (aisle_start + aisle_end)
    n_arrows = 3
    for i in range(n_arrows):
        u = (i + 1) / (n_arrows + 1)
        s = mid_a + (mid_b - mid_a) * u
        instance(lambda: piece_decal_plane('lot_decal_arrow', 'lot_decal_arrow', (0.9, 2.6)),
                 'lot_decal_arrow', pth, s, aisle_d, 0.027)

    # --- lamps, pools, glow ---
    # fractions along the mid island; arms already point +X (outward / over the aisle)
    lamp_fracs = {
        2: (0.28, 0.72),
        3: (0.22, 0.50, 0.78),
        4: (0.16, 0.39, 0.61, 0.84),
    }[N_LAMPS]
    lamp_s = []
    for fr in lamp_fracs:
        s = mid_a + (mid_b - mid_a) * fr
        lamp_s.append(s)
        instance(piece_lamp_pole, 'lot_lamp_pole', pth, s, d_ib - 0.15, 0.0, yaw=0.0)
        # pool under the head (~1.65 m into the lot from the post)
        instance(piece_pool, 'lot_pool_decal', pth, s, d_ib - 0.15 + 1.65, 0.03)
        gl = instance(piece_glow, 'lot_glow_sprite', pth, s, d_ib - 0.15 + 1.65, 5.95)
        gl['billboard'] = 1

    # --- sign at the entry opening (incoming traffic looks at -Y of the piece) ---
    # Sit it just inside the entry, on the lot side of the island start.
    instance(piece_sign, 'lot_sign', pth, mid_a - 1.0, d_ib + 0.4, 0.0, yaw=0.0)

    # --- vending, mid-lot, lot-side of the island (front faces the aisle / road) ---
    instance(piece_vending, 'lot_vending', pth, S_MID, d_ib + 0.45, 0.0, yaw=0.0)

    # a low-poly forest mass behind the rail (cards alone fall apart from overhead)
    bhedge = Builder('lot_forest_mass', 'surface')
    n = 16
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        sa = (S0 + 1.0) + ((S1 - 1.0) - (S0 + 1.0)) * u0
        sb = (S0 + 1.0) + ((S1 - 1.0) - (S0 + 1.0)) * u1
        def width_at(s):
            if s < mid_a:
                return POCKET_W * max(0.15, (s - S0) / TAPER_M)
            if s > mid_b:
                return POCKET_W * max(0.15, (S1 - s) / TAPER_M)
            return POCKET_W
        d0, d1 = d_edge + width_at(sa) + 0.8, d_edge + width_at(sb) + 0.8
        p00 = pth.point(sa, d0, 0.0); p10 = pth.point(sa, d0 + 6.0, 0.0)
        p01 = pth.point(sb, d1, 0.0); p11 = pth.point(sb, d1 + 6.0, 0.0)
        h = 9.0
        # top of the mass + the road-facing wall (dark verge colour)
        p00h, p01h = pth.point(sa, d0, h), pth.point(sb, d1, h)
        p10h, p11h = pth.point(sa, d0 + 6.0, h + 3.0), pth.point(sb, d1 + 6.0, h + 3.0)
        bhedge.quad([p00, p01, p01h, p00h], [(0, 0), (1, 0), (1, 1), (0, 1)], m_verge)
        bhedge.quad([p00h, p01h, p11h, p10h], [(0, 0), (1, 0), (1, 1), (0, 1)], m_verge)
    bhedge.finish()

    # --- cedar wall behind the rail ---
    rng_step = 3.2
    s = S0 + 1.0
    idx = 0
    while s < S1 - 1.0:
        # width at this s (tapers shrink the lot)
        if s < mid_a:
            w_here = POCKET_W * max(0.15, (s - S0) / TAPER_M)
        elif s > mid_b:
            w_here = POCKET_W * max(0.15, (S1 - s) / TAPER_M)
        else:
            w_here = POCKET_W
        d_outer = d_edge + w_here
        for row, dd, h0 in ((0, 1.6, 11.0), (1, 4.4, 13.5), (2, 7.6, 15.0)):
            ss = s + (0.6 if row == 1 else (-0.4 if row == 2 else 0.0))
            hh = h0 + (1.4 if (idx + row) % 3 == 0 else 0.0)
            tex = 'touge_cedar_a' if (idx + row) % 2 == 0 else 'touge_cedar_b'
            instance(lambda t=tex, h=hh: piece_cedar('lot_cedar_card', t, h),
                     'lot_cedar_card', pth, ss, d_outer + dd, 0.0,
                     yaw=(0.3 if row else 0.0))
        # a few cedars on the drop side for context
        if idx % 2 == 0:
            instance(lambda: piece_cedar('lot_cedar_card', 'touge_cedar_b', 10.0 + (idx % 3)),
                     'lot_cedar_card', pth, s, -RH - 6.0 - (idx % 3), -2.5,
                     yaw=0.4)
        s += rng_step
        idx += 1

    layout.update({
        'mid_a': mid_a, 'mid_b': mid_b,
        'n_stalls_per_row': n_st,
        'stall_spacing_m': spacing,
        'stall_perp_m': stall_perp,
        'aisle_d_m': [aisle_start - RH, aisle_end - RH],  # metres beyond road edge
        'centre_row_d_m': centre_d - RH,
        'outer_row_d_m': outer_d - RH,
        'lamp_s': lamp_s,
        'arrow_count': n_arrows,
    })
    return layout

# ---------------------------------------------------------------------------
# Cameras + render
# ---------------------------------------------------------------------------
def make_camera(name, loc, look, fov_deg, clip_end=260.0):
    cam = bpy.data.cameras.new(name)
    cam.lens_unit = 'FOV'
    cam.angle = math.radians(fov_deg)  # vertical FOV, matches Godot Camera3D
    cam.clip_start = 0.15
    cam.clip_end = clip_end
    cam.sensor_fit = 'VERTICAL'
    cam.dof.use_dof = False
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    # look at
    direction = (look - loc).normalized()
    # Blender camera looks along -Z, +Y up
    rot = direction.to_track_quat('-Z', 'Y')
    ob.rotation_euler = rot.to_euler()
    return ob

def face_billboards(cam_loc):
    for o in bpy.data.objects:
        if o.get('billboard'):
            direction = (cam_loc - o.location)
            if direction.length < 1e-5:
                continue
            o.rotation_euler = direction.normalized().to_track_quat('Y', 'Z').to_euler()

def setup_eevee(scene, w=640, h=480):
    # 4.2: EEVEE; 4.2 with next is experimental
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    if hasattr(scene.render, "filter_size"):
        scene.render.filter_size = 0.01
    elif hasattr(scene.render, "pixel_filter_size"):
        scene.render.pixel_filter_size = 0.01
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 0
    scene.render.filepath = os.path.join(RAW, 'tmp.png')
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 1
    if hasattr(scene.eevee, 'use_taa_reprojection'):
        scene.eevee.use_taa_reprojection = False
    if hasattr(scene.eevee, 'use_gtao'):
        scene.eevee.use_gtao = False
    if hasattr(scene.eevee, 'use_bloom'):
        scene.eevee.use_bloom = False
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = False
    # colour management: painted values as-is
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.sequencer_colorspace_settings.name = 'sRGB'
    # world = fog colour
    world = bpy.data.worlds.new('lot_world') if 'lot_world' not in bpy.data.worlds else bpy.data.worlds['lot_world']
    world.use_nodes = True
    wn = world.node_tree
    wn.nodes.clear()
    bg = wn.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0x0B / 255, 0x17 / 255, 0x2B / 255, 1)
    bg.inputs['Strength'].default_value = 1.0
    wout = wn.nodes.new('ShaderNodeOutputWorld')
    wn.links.new(bg.outputs['Background'], wout.inputs['Surface'])
    scene.world = world

def kind_of(ob):
    if ob.get('lot_kind'):
        return ob['lot_kind']
    if ob.type == 'MESH' and ob.data.materials:
        m = ob.data.materials[0]
        if m and m.get('lot_kind'):
            return m['lot_kind']
    return 'surface'

def make_override_mats():
    def emit_color(col, name):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (*col, 1)
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        return m
    mask_by_kind = {k: emit_color(v[:3], 'mask_' + k) for k, v in KIND_COLOR.items()}
    # depth: Camera Data view distance, 0-120 m -> 0-1
    dmat = bpy.data.materials.new('lot_depth')
    dmat.use_nodes = True
    nt = dmat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    cam = nt.nodes.new('ShaderNodeCameraData')
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.0
    ramp.inputs['From Max'].default_value = 120.0
    ramp.inputs['To Min'].default_value = 0.0
    ramp.inputs['To Max'].default_value = 1.0
    ramp.clamp = True
    nt.links.new(cam.outputs['View Distance'], ramp.inputs['Value'])
    nt.links.new(ramp.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mask_by_kind, dmat

def render_one(scene, cam, name, mask_by_kind, dmat):
    scene.camera = cam
    face_billboards(cam.location)
    # beauty
    scene.view_layers[0].material_override = None
    path = os.path.join(RAW, name + '_beauty.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDER beauty', path)
    # mask: per-object override via object color? material_override is global, so
    # assign a kind material as the active material slot override by swapping
    # (we stash and restore).
    stashed = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        k = kind_of(o)
        stashed.append((o, list(o.data.materials)))
        mk = mask_by_kind.get(k, mask_by_kind['surface'])
        if o.data.materials:
            for i in range(len(o.data.materials)):
                o.data.materials[i] = mk
        else:
            o.data.materials.append(mk)
    path = os.path.join(RAW, name + '_mask.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDER mask', path)
    for o, mats in stashed:
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
    # depth
    scene.view_layers[0].material_override = dmat
    scene.render.image_settings.color_depth = '16'
    scene.render.image_settings.color_mode = 'BW'
    path = os.path.join(RAW, name + '_depth.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDER depth', path)
    scene.view_layers[0].material_override = None
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.color_mode = 'RGB'

def setup_cameras(pth):
    # race camera: 2.45 m up, 47° lens, passing the lot, aimed 34 m up the road
    s_cam = S0 + 6.0
    loc = pth.point(s_cam, -0.6, 2.45)
    look = pth.point(s_cam + 34.0, 3.2, 0.9)
    race = make_camera('race_cam', loc, look, 47.0)
    # overhead, Hakone-ref composition: from the inside of the bend, lot on the right
    loc_o = pth.point(S_MID - 4.0, -22.0, 42.0)
    look_o = pth.point(S_MID + 2.0, RH + POCKET_W * 0.45, 0.0)
    over = make_camera('overhead_cam', loc_o, look_o, 40.0, clip_end=320.0)
    # close-ups
    loc_i = pth.point(S_MID - 4.0, -1.0, 2.2)
    look_i = pth.point(S_MID + 6.0, RH + 1.5, 0.2)
    island = make_camera('close_island', loc_i, look_i, 40.0)
    loc_s = pth.point(S_MID - 2.0, RH + 4.0, 3.4)
    look_s = pth.point(S_MID + 8.0, RH + 10.0, 0.1)
    stalls = make_camera('close_stalls', loc_s, look_s, 42.0)
    # lamp close: one mid lamp
    # stand in the aisle, 3/4 on a lamp: post, glowing head and the soft pool on the ground
    loc_l = pth.point(S_MID - 9.0, RH + 5.0, 1.8)
    look_l = pth.point(S_MID, RH + ISLAND_1 + 1.5, 2.4)
    lamp = make_camera('close_lamp', loc_l, look_l, 55.0)
    # incoming traffic, close enough to read the P, with the taper and rail in frame
    loc_e = pth.point(S0 + TAPER_M - 5.5, RH - 1.2, 1.55)
    look_e = pth.point(S0 + TAPER_M - 1.0, RH + ISLAND_1 + 0.35, 1.7)
    entry = make_camera('close_entry', loc_e, look_e, 38.0)
    return [
        ('race_cam', race),
        ('overhead', over),
        ('close_island', island),
        ('close_stalls', stalls),
        ('close_lamp', lamp),
        ('close_entry', entry),
    ]

def render_views(pth):
    scene = bpy.context.scene
    setup_eevee(scene)
    cams = setup_cameras(pth)
    mask_by_kind, dmat = make_override_mats()
    for name, cam in cams:
        render_one(scene, cam, name, mask_by_kind, dmat)

def write_stats(layout):
    assembled = [o for o in bpy.data.objects if o.type == 'MESH']
    total = sum(tris_of(o) for o in assembled)
    by_kind = {}
    for o in assembled:
        k = kind_of(o)
        by_kind[k] = by_kind.get(k, 0) + tris_of(o)
    kit_only = total - by_kind.get('card', 0) - (by_kind.get('surface', 0) and 0)
    # kit pieces without sky / cut-slope context: report assembled total and per-piece STATS
    piece_tris = STATS
    prev = os.path.join(ROOT, 'tri_counts.json')
    if not piece_tris and os.path.exists(prev):
        try:
            piece_tris = json.load(open(prev)).get('piece_tris', [])
        except Exception:
            piece_tris = []
    report = {
        'layout': layout,
        'piece_tris': piece_tris,
        'assembled_tris_total': total,
        'assembled_tris_by_kind': by_kind,
    }
    p = os.path.join(ROOT, 'tri_counts.json')
    with open(p, 'w') as f:
        json.dump(report, f, indent=2)
    print('STATS total', total, 'by_kind', by_kind)
    return report

def main():
    mode = os.environ.get('LOT_MODE', 'all')  # pieces, assemble, all
    if mode in ('pieces', 'all'):
        export_pieces()
    layout = None
    if mode in ('assemble', 'all'):
        reset()
        pth = Path(CURVE_R, S_MID)
        layout = assemble(pth)
        # export the assembled preview as one glb (no sky, to keep it game-usable)
        kit_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'lot_sky'
                    and not o.name.startswith('lot_cut_slope')
                    and not o.name.startswith('lot_verge_shoulder')]
        # keep a full assembled and a kit-only assembled
        export_glb('lot_assembled_preview', [o for o in bpy.data.objects if o.type == 'MESH'])
        # write layout now, render next
        lp = os.path.join(ROOT, 'layout.json')
        with open(lp, 'w') as f:
            json.dump(layout, f, indent=2)
        print('LAYOUT', lp)
        write_stats(layout)
        if os.environ.get('SKIP_RENDER') == '1':
            return
        render_views(pth)
    print('DONE')

if __name__ == '__main__':
    main()
