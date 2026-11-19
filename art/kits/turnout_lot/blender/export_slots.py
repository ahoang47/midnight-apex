# Blender 4.2 headless: export the turnout kit in Gordon's LotArt frame
#   Godot: origin = road edge at the entrance, +X into the lot, +Y up, +Z along travel.
#   Blender (Z-up) stores (x, -z, y) so glTF export_yup yields that Godot frame.
# Env: POCKET_M TAPER_M POCKET_W ROWS N_LAMPS STALL_W STALL_D STALL_ANGLE OUT_TAG
import bpy, bmesh, os, math, json, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TEX = os.path.join(ROOT, 'tex')
LIB = os.path.join(ROOT, 'lib')
RAW = os.path.join(ROOT, 'renders', 'raw')
os.makedirs(RAW, exist_ok=True)

def envf(n, d):
    v = os.environ.get(n)
    return float(v) if v not in (None, '') else float(d)
def envi(n, d):
    v = os.environ.get(n)
    return int(v) if v not in (None, '') else int(d)

ROAD_W = envf('ROAD_W', 7.5)
POCKET_M = envf('POCKET_M', 62.0)
TAPER_M = envf('TAPER_M', 14.0)
POCKET_W = envf('POCKET_W', 16.0)
ROWS = envi('ROWS', 2)
N_LAMPS = max(2, min(4, envi('N_LAMPS', 2)))
STALL_W = envf('STALL_W', 2.5)
STALL_D = envf('STALL_D', 5.0)
STALL_ANGLE = envf('STALL_ANGLE', 70.0)
CURB_H = envf('CURB_H', 0.15)
ISLAND_0 = envf('ISLAND_0', 0.1)
ISLAND_1 = envf('ISLAND_1', 0.7)
OUT_TAG = os.environ.get('OUT_TAG', 'w16')
RH = ROAD_W * 0.5
MID_A, MID_B = TAPER_M, POCKET_M - TAPER_M
MID_LEN = MID_B - MID_A

# Approved kit writes to glb/; a non-default tag (e.g. w11) goes to glb/<tag>/.
if OUT_TAG in ('', 'w16'):
    OUT = os.path.join(ROOT, 'glb')
else:
    OUT = os.path.join(ROOT, 'glb', OUT_TAG)
os.makedirs(OUT, exist_ok=True)
STATS = []
_mats = {}

def B(x, y, z):
    """LotArt/Godot (x into lot, y up, z travel) -> Blender Z-up."""
    return (float(x), float(-z), float(y))

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
    else:
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        m.blend_method = 'OPAQUE'
    _mats[key] = m
    return m

def _ensure_solid_tex(name, rgb):
    path = os.path.join(TEX, name + '.png')
    if not os.path.exists(path):
        # tiny 16x16 written without Pillow; a raw RGBA PNG is overkill — use bpy image
        import struct, zlib
        w = h = 16
        r, g, b = rgb
        raw = b''.join(b'\x00' + bytes([r, g, b, 255]) * w for _ in range(h))
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
        open(path, 'wb').write(png)

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
        # vs in LotArt/Godot metres
        bv = [self.bm.verts.new(Vector(B(*v))) for v in vs]
        f = self.bm.faces.new(bv)
        f.material_index = self.mi(m)
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = uv
        return f
    def box(self, c, s, m, faces='all', uvscale=1.0):
        # c,s in LotArt: c=(x,y,z), s=(sx,sy,sz) with y up, z travel, x into lot
        # box from y=cy to y=cy+sy (height), centred in x and z
        cx, cy, cz = c
        sx, sy, sz = s
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy, cy + sy
        z0, z1 = cz - sz / 2, cz + sz / 2
        F = {
            '-x': ([(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)], sz, sy),
            '+x': ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], sz, sy),
            '-z': ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], sx, sy),
            '+z': ([(x1, y0, z1), (x0, y0, z1), (x0, y1, z1), (x1, y1, z1)], sx, sy),
            '+y': ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], sx, sz),
            '-y': ([(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)], sx, sz),
        }
        keys = F.keys() if faces == 'all' else faces
        for k in keys:
            vs, la, lb = F[k]
            self.quad(vs, [(0, 0), (la / uvscale, 0), (la / uvscale, lb / uvscale), (0, lb / uvscale)], m)
    def cyl(self, c, r0, r1, h, m, n=6, uvscale=1.0, cap=True, axis='y'):
        cx, cy, cz = c
        for i in range(n):
            a0 = 2 * math.pi * i / n
            a1 = 2 * math.pi * (i + 1) / n
            def p(a, r, t):
                if axis == 'y':
                    return (cx + r * math.cos(a), cy + t, cz + r * math.sin(a))
                return (cx + r * math.cos(a), cy + r * math.sin(a), cz + t)
            self.quad([p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, h), p(a0, r1, h)],
                      [(i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, h / uvscale), (i / n, h / uvscale)], m)
            if cap:
                top = (cx, cy + h, cz) if axis == 'y' else (cx, cy, cz + h)
                bv = [self.bm.verts.new(Vector(B(*v))) for v in (top, p(a0, r1, h), p(a1, r1, h))]
                f = self.bm.faces.new(bv)
                f.material_index = self.mi(m)
    def finish(self, tess=False):
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
        return ob

def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def export_glb(name, objects=None):
    if objects is None:
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    objects = [o for o in objects if o.type == 'MESH']
    if not objects:
        print('SKIP empty', name)
        return 0
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
    ntris = sum(tris_of(o) for o in objects)
    STATS.append({'name': name, 'tris': ntris, 'path': os.path.relpath(path, ROOT).replace(os.sep, '/')})
    print('EXPORT', OUT_TAG, name, ntris)
    return ntris

# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def stall_layout():
    ang = math.radians(STALL_ANGLE)
    spacing = STALL_W / max(0.35, math.sin(ang))
    perp = STALL_D * math.sin(ang)
    # one row along the back; optional second row for 16 m
    back = POCKET_W
    aisle0 = ISLAND_1 + 0.05
    # back row: stalls occupy [back-perp, back]
    back_row_x = back - perp * 0.5
    rows = [('back', back_row_x)]
    if ROWS >= 2:
        # second row closer to the aisle, leaving a small mid gap
        mid_x = aisle0 + 5.5 + perp * 0.5
        # keep a gap from the back row
        if mid_x + perp * 0.5 < back_row_x - perp * 0.5 - 0.4:
            rows.insert(0, ('centre', mid_x))
        else:
            mid_x = (aisle0 + 0.4 + back_row_x - perp * 0.5) * 0.5
            rows.insert(0, ('centre', mid_x))
    row_a, row_b = MID_A + 1.2, MID_B - 1.2
    n_st = max(1, int(math.floor((row_b - row_a) / spacing)))
    st0 = 0.5 * (row_a + row_b) - n_st * spacing * 0.5
    return {
        'ang': ang, 'spacing': spacing, 'perp': perp, 'rows': rows,
        'row_a': row_a, 'row_b': row_b, 'n_st': n_st, 'st0': st0,
        'aisle0': aisle0, 'aisle1': (rows[0][1] - perp * 0.5) if rows else back - perp,
    }

def lamp_zs():
    # even spacing along the mid, far enough that pools of radius R don't overlap
    # mid length * (frac_i). Default 2 lamps at Gordon's 0.22 / 0.78.
    if N_LAMPS == 2:
        fracs = (0.22, 0.78)
    elif N_LAMPS == 3:
        fracs = (0.18, 0.50, 0.82)
    else:
        fracs = (0.16, 0.39, 0.61, 0.84)
    return [MID_A + MID_LEN * f for f in fracs]

def pool_radius():
    zs = lamp_zs()
    if len(zs) < 2:
        return 6.0
    gap = min(zs[i + 1] - zs[i] for i in range(len(zs) - 1))
    # leave a 2 m clear gap between pools
    return max(3.5, min(6.0, 0.5 * gap - 1.0))

# ---------------------------------------------------------------------------
# Slot builders (all in LotArt metres)
# ---------------------------------------------------------------------------
def build_floor():
    m = mat('lot_asphalt', 'lot_asphalt', 'surface', 'Linear')
    b = Builder('lot_floor', 'surface')
    tile = 8.0
    # mid rectangle
    b.quad([(0, 0.0, MID_A), (POCKET_W, 0.0, MID_A), (POCKET_W, 0.0, MID_B), (0, 0.0, MID_B)],
           [(0, MID_A / tile), (POCKET_W / tile, MID_A / tile), (POCKET_W / tile, MID_B / tile), (0, MID_B / tile)], m)
    # tapers, 8 slices
    def taper(z0, z1, grow):
        n = 8
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            if grow > 0:
                w0, w1 = max(0.12, POCKET_W * u0), max(0.12, POCKET_W * u1)
            else:
                w0, w1 = max(0.12, POCKET_W * (1 - u0)), max(0.12, POCKET_W * (1 - u1))
            za = z0 + (z1 - z0) * u0
            zb = z0 + (z1 - z0) * u1
            b.quad([(0, 0.0, za), (w0, 0.0, za), (w1, 0.0, zb), (0, 0.0, zb)],
                   [(0, za / tile), (w0 / tile, za / tile), (w1 / tile, zb / tile), (0, zb / tile)], m)
    taper(0.0, MID_A, +1)
    taper(MID_B, POCKET_M, -1)
    return [b.finish(tess=True)]

def build_curbs():
    m = mat('lot_curb', 'lot_curb', 'prop', 'Linear')
    b = Builder('lot_curbs', 'prop')
    cap = 0.8
    # island
    z0, z1 = MID_A + cap, MID_B - cap
    w = ISLAND_1 - ISLAND_0
    cx = 0.5 * (ISLAND_0 + ISLAND_1)
    b.box((cx, 0, 0.5 * (z0 + z1)), (w, CURB_H, z1 - z0), m, uvscale=2.0)
    # bullnoses
    b.box((cx, 0, z0 - 0.3), (w, CURB_H, 0.6), m, uvscale=1.0)
    b.box((cx, 0, z1 + 0.3), (w, CURB_H, 0.6), m, uvscale=1.0)
    # back curb under the wall
    bw = 0.35
    b.box((POCKET_W + 0.05, 0, 0.5 * (MID_A + MID_B)), (bw, CURB_H, MID_LEN), m, uvscale=2.0)
    return [b.finish()]

def _paint_quad(b, m, x0, z0, x1, z1, y=0.025, width=None):
    # a strip from (x0,z0) to (x1,z1), width metres if given, else a quad with those corners
    b.quad([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], m)

def build_stall_lines():
    lay = stall_layout()
    mw = mat('lot_paint_white', 'lot_paint_white', 'decal', 'Closest')
    b = Builder('lot_stall_lines', 'decal')
    ang = lay['ang']
    # stall axis in the XZ plane: angle from +Z toward +X (into the lot)
    # A line of length STALL_D along that axis, 0.20 m wide.
    ca, sa = math.cos(ang), math.sin(ang)  # z component, x component of the stall axis
    half_w = 0.10
    def line_at(x, z, length=STALL_D):
        # centre of the line, axis (sa, ca) in (x,z)
        dx, dz = sa, ca
        px, pz = -dz, dx  # perpendicular
        hx, hz = dx * length * 0.5, dz * length * 0.5
        wx, wz = px * half_w, pz * half_w
        # four corners
        b.quad([
            (x - hx - wx, 0.026, z - hz - wz),
            (x + hx - wx, 0.026, z + hz - wz),
            (x + hx + wx, 0.026, z + hz + wz),
            (x - hx + wx, 0.026, z - hz + wz),
        ], [(0, 0), (1, 0), (1, 1), (0, 1)], mw)
    zs = []
    for i in range(lay['n_st'] + 1):
        z = lay['st0'] + i * lay['spacing']
        zs.append(z)
        for name, x in lay['rows']:
            line_at(x, z)
    # front line of each row (continuous, across the bays)
    z0, z1 = zs[0], zs[-1]
    for name, x in lay['rows']:
        # front is the aisle-side of the stall
        xf = x - lay['perp'] * 0.5
        b.quad([
            (xf - 0.06, 0.026, z0), (xf + 0.06, 0.026, z0),
            (xf + 0.06, 0.026, z1), (xf - 0.06, 0.026, z1),
        ], [(0, 0), (1, 0), (1, 1), (0, 1)], mw)
    # white edge line on the road face of the island (mid only)
    xe = 0.04
    b.quad([
        (xe - 0.075, 0.023, MID_A + 0.8), (xe + 0.075, 0.023, MID_A + 0.8),
        (xe + 0.075, 0.023, MID_B - 0.8), (xe - 0.075, 0.023, MID_B - 0.8),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], mw)
    # arrows in the through-aisle, pointing +Z (travel / exit)
    aisle_x = 0.5 * (lay['aisle0'] + max(lay['aisle0'] + 2.0, lay['aisle1']))
    for i in range(3):
        z = MID_A + MID_LEN * (i + 1) / 4.0
        arrow(b, mw, aisle_x, z, 2.6, 0.9)
    return [b.finish()]

def arrow(b, m, x, z, length, width):
    # filled arrow pointing +Z, shaft + head, at y=0.027
    y = 0.027
    half = width * 0.5
    # shaft (rear 0.55 of length)
    z0 = z - length * 0.5
    z1 = z + length * 0.05
    sw = width * 0.34
    b.quad([
        (x - sw, y, z0), (x + sw, y, z0), (x + sw, y, z1), (x - sw, y, z1),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    # head: triangle pointing +Z
    zt = z + length * 0.5
    zb = z1 + 0.02
    # Godot winding CCW from above (+Y)
    b.quad  # placeholder to keep parser happy if I slip
    # use a triangle via a degenerate? Builder has no tri() that takes Godot coords — add via quad that's a thin tri? 
    # I'll add a dedicated tri helper below by writing three verts.
    vs = [(x, y, zt), (x - half, y, zb), (x + half, y, zb)]
    # reuse quad by repeating a vert? Better: add tri method call through bm
    bv = [b.bm.verts.new(Vector(B(*v))) for v in vs]
    f = b.bm.faces.new(bv)
    f.material_index = b.mi(m)
    for l, uv in zip(f.loops, [(0.5, 1), (0, 0), (1, 0)]):
        l[b.uv].uv = uv

def build_wheel_stops():
    lay = stall_layout()
    m = mat('lot_wheel_stop', 'lot_wheel_stop', 'prop', 'Linear')
    b = Builder('lot_wheel_stops', 'prop')
    ang = lay['ang']
    ca, sa = math.cos(ang), math.sin(ang)
    # stop sits across the stall at the deep end, 1.6 x 0.16 x 0.13
    for name, x in lay['rows']:
        x_stop = x + lay['perp'] * 0.5 - 0.35
        for i in range(lay['n_st']):
            z = lay['st0'] + (i + 0.5) * lay['spacing']
            # local long axis is perpendicular to the stall axis (across the bay)
            # stall axis (sa, ca) in (x,z); across is (-ca, sa)
            # We'll just place a box rotated: easier to emit 4 sides in world
            # Build a small box oriented across the stall.
            lx, lz = -ca, sa  # long axis
            wx, wz = sa, ca   # short axis (along stall)
            L, W, H = 1.6, 0.16, 0.13
            def cnr(sL, sW, y):
                return (x_stop + sL * lx * L * 0.5 + sW * wx * W * 0.5, y, z + sL * lz * L * 0.5 + sW * wz * W * 0.5)
            # top
            b.quad([cnr(-1, -1, H), cnr(1, -1, H), cnr(1, 1, H), cnr(-1, 1, H)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
            for y0, y1, uv in ((0, H, True),):
                b.quad([cnr(-1, -1, 0), cnr(1, -1, 0), cnr(1, -1, H), cnr(-1, -1, H)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
                b.quad([cnr(1, 1, 0), cnr(-1, 1, 0), cnr(-1, 1, H), cnr(1, 1, H)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
                b.quad([cnr(1, -1, 0), cnr(1, 1, 0), cnr(1, 1, H), cnr(1, -1, H)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
                b.quad([cnr(-1, 1, 0), cnr(-1, -1, 0), cnr(-1, -1, H), cnr(-1, 1, H)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return [b.finish()]

def build_road_paint():
    """Yellow centre line + solid filled chevrons in the lot-side lane. Lives under LotArt (x < 0 is the road)."""
    my = mat('lot_paint_yellow', 'lot_decal_center', 'decal', 'Closest')
    mc = mat('lot_paint_chevron', 'lot_paint_chevron', 'decal', 'Closest')
    b = Builder('lot_road_paint', 'decal')
    y = 0.022
    # yellow centre line at x = -RH (road centre), z along the visible pocket plus a little approach
    b.quad([
        (-RH - 0.075, y, -4.0), (-RH + 0.075, y, -4.0),
        (-RH + 0.075, y, POCKET_M + 4.0), (-RH - 0.075, y, POCKET_M + 4.0),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], my)
    # solid filled chevrons in the lot-side lane, pointing +Z
    lane_x = -RH * 0.5  # centre of the lane next to the lot
    # each chevron is a solid triangle, 3.0 m wide, 2.4 m long, spaced 2.5 m
    half = 1.50
    length = 2.40
    step = 2.55
    z = 0.0
    while z + length <= POCKET_M + 2.0:
        z0, z1 = z, z + length  # z0 back, z1 tip (+Z)
        vs = [
            (lane_x, y, z1),            # tip
            (lane_x - half, y, z0),
            (lane_x + half, y, z0),
        ]
        bv = [b.bm.verts.new(Vector(B(*v))) for v in vs]
        f = b.bm.faces.new(bv)
        f.material_index = b.mi(mc)
        for l, uv in zip(f.loops, [(0.5, 1), (0, 0), (1, 0)]):
            l[b.uv].uv = uv
        z += step
    return [b.finish()]

def build_lamp_module():
    """A single lamp, local LotArt: origin at the post, arm toward the road (-X). Includes glow + pool."""
    pole = mat('lot_pole', 'lot_pole', 'prop', 'Linear')
    metal = mat('lot_metal', 'lot_metal', 'prop', 'Linear')
    emit = mat('Emit_sodium', 'emit_sodium', 'emit', 'Linear')
    b = Builder('lot_lamp', 'prop')
    b.cyl((0, 0, 0), 0.11, 0.08, 6.15, pole, n=6, uvscale=3.0)
    # arm toward -X, 1.7 m
    b.box((-0.85, 5.95, 0), (1.7, 0.07, 0.07), metal, uvscale=1.0)
    b.box((-1.65, 5.82, 0), (0.38, 0.12, 0.18), metal, faces=['-x', '+x', '-z', '+z', '+y'], uvscale=1.0)
    # emit underside
    b.quad([(-1.46, 5.81, -0.10), (-1.84, 5.81, -0.10), (-1.84, 5.81, 0.10), (-1.46, 5.81, 0.10)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], emit)
    obs = [b.finish()]
    # glow sprite at the head, in the XZ... actually a Y-facing? For preview, a small XY/ZY plane.
    bg = Builder('lot_glow_sprite', 'emit')
    g = mat('lot_glow', 'lot_glow', 'emit', 'Linear', alpha='BLEND')
    s = 0.7
    # vertical plane facing -X (toward the road / camera on the road)
    bg.quad([(-1.65, 5.95 - s, -s), (-1.65, 5.95 - s, s), (-1.65, 5.95 + s, s), (-1.65, 5.95 + s, -s)],
            [(0, 0), (1, 0), (1, 1), (0, 1)], g)
    glow = bg.finish()
    glow['billboard'] = 1
    obs.append(glow)
    # soft pool under the head, radius from pool_radius(), no overlap by construction
    R = pool_radius()
    bp = Builder('lot_pool_decal', 'pool')
    pmat = mat('lot_pool', 'lot_pool', 'pool', 'Linear', alpha='BLEND')
    # oval slightly along Z, 2R across
    sx, sz = R, R * 0.95
    cx = -1.65
    bp.quad([(cx - sx, 0.03, -sz), (cx + sx, 0.03, -sz), (cx + sx, 0.03, sz), (cx - sx, 0.03, sz)],
            [(0, 0), (1, 0), (1, 1), (0, 1)], pmat)
    obs.append(bp.finish())
    return obs

def place_lamp_at(z, x):
    obs = build_lamp_module()
    # objects are at origin; move them in Blender space by Godot delta (x, 0, z)
    dx, dy, dz = B(x, 0, z)
    for o in obs:
        o.location = o.location + Vector((dx, dy, dz))
        o.name = o.name + ('_z%.0f' % z)
    return obs

def build_lamps():
    # posts on the back curb, arms toward the road (-X) over the stalls
    x = POCKET_W + 0.2
    obs = []
    for z in lamp_zs():
        obs.extend(place_lamp_at(z, x))
    return obs

def build_props():
    obs = []
    # vending at mid, just inside the back (doesn't block the aisle)
    bv = Builder('lot_vending', 'prop')
    body = mat('lot_vending_body', 'lot_vending_body', 'prop', 'Linear')
    front = mat('Emit_vending_front', 'emit_vending_front', 'emit', 'Linear')
    # front faces -X (toward the aisle / road)
    # box centred, front at smaller x
    x, z = POCKET_W + 0.4, 0.5 * (MID_A + MID_B)
    bv.box((x + 0.38, 0, z), (0.75, 1.85, 1.0), body, faces=['+x', '-z', '+z', '+y'], uvscale=1.0)
    bv.quad([
        (x + 0.01, 0.0, z - 0.50), (x + 0.01, 0.0, z + 0.50),
        (x + 0.01, 1.85, z + 0.50), (x + 0.01, 1.85, z - 0.50),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], front)
    vend = bv.finish()
    vend.name = 'Vending'
    obs.append(vend)
    # sign at the entry opening, plate faces -Z (incoming traffic).
    # Geometry P on a solid blue plate — readable even if a texture bind flakes.
    _ensure_solid_tex('lot_paint_blue', (24, 72, 168))
    bs = Builder('lot_sign', 'prop')
    metal = mat('lot_metal', 'lot_metal', 'prop', 'Linear')
    blue = mat('lot_sign_blue', 'lot_paint_blue', 'prop', 'Closest')
    white = mat('lot_sign_p', 'lot_paint_white', 'prop', 'Closest')
    face = mat('lot_sign_face', 'lot_sign_face', 'prop', 'Closest')
    sx, sz = ISLAND_1 + 0.45, MID_A - 1.0
    # post sits BEHIND the plate (deeper in +Z) so it no longer splits the P
    bs.cyl((sx, 0, sz + 0.10), 0.045, 0.04, 2.70, metal, n=6, uvscale=1.0)
    pw, ph, pt = 0.78, 0.98, 0.07
    y0 = 1.62
    # solid blue plate fully in front of the post, facing incoming traffic (-Z)
    bs.box((sx, y0, sz - 0.06), (pw, ph, pt), blue, uvscale=1.0)
    # painted P on the incoming face only (no geometry P — the two overlapped into a "9")
    zf = sz - 0.06 - pt / 2 - 0.003
    # U is flipped so the stem sits on the viewer's left when seen by incoming traffic
    # (the incoming face is the back of a CCW-from-+Z winding).
    bs.quad([
        (sx - pw / 2 + 0.03, y0 + 0.03, zf),
        (sx + pw / 2 - 0.03, y0 + 0.03, zf),
        (sx + pw / 2 - 0.03, y0 + ph - 0.03, zf),
        (sx - pw / 2 + 0.03, y0 + ph - 0.03, zf),
    ], [(1, 0), (0, 0), (0, 1), (1, 1)], face)
    # unused on purpose (kept so the material is packed): a tiny hidden white cap
    bs.box((sx, y0 + ph + 0.02, sz + 0.10), (0.08, 0.04, 0.08), white, uvscale=1.0)
    sign = bs.finish()
    sign.name = 'Sign'
    obs.append(sign)
    return obs

def import_lattice_template():
    """Import mtn_lattice_slope_g and return the mesh object, already aligned to LotArt
    (+X into the slope, +Y up, +Z along travel) at the origin."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(LIB, 'mtn_lattice_slope_g.glb'))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    if not new:
        return None
    # join if multiple
    if len(new) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in new:
            o.select_set(True)
        bpy.context.view_layer.objects.active = new[0]
        bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
    else:
        ob = new[0]
    # After glTF import into Z-up Blender, the original module (X into slope, Y along, Z up)
    # typically arrives already Z-up. Measure and rotate so:
    #   size.x ~ 8 m (into lot / +X), size.z ~ 7.6 m (up, Blender Z), size.y ~ 4 m (along, Blender Y = -travel)
    # We'll compute AABB and rotate to match.
    bpy.context.view_layer.update()
    xs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    size = Vector((max(p.x for p in xs) - min(p.x for p in xs),
                   max(p.y for p in xs) - min(p.y for p in xs),
                   max(p.z for p in xs) - min(p.z for p in xs)))
    print('LATTICE imported size', tuple(size))
    # We want Blender size ≈ (8, 4, 7.6) = (into, along, up).
    # If the import already looks like that, just shift so the road-facing base sits at x=0, y=0, z=0 (up).
    # If Y is up (~7.6) and Z is along (~4), it came in Y-up and we need -90° around X... 
    # We'll pick the axis closest to 7.6 as up, 4 as along, 8 as into.
    axes = [('x', size.x), ('y', size.y), ('z', size.z)]
    up = max(axes, key=lambda a: abs(a[1] - 7.6))[0]
    along = max([a for a in axes if a[0] != up], key=lambda a: abs(a[1] - 4.15))[0]
    into = [a[0] for a in axes if a[0] not in (up, along)][0]
    print('LATTICE axes into,along,up', into, along, up)
    # Build a rotation that maps current (into, along, up) onto (X, Y, Z)
    # Easier: apply Euler rotations based on the three cases we actually see.
    # Target: into=+X, along=+Y (Blender, which is -travel), up=+Z.
    def rot(axis, deg):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.transform.rotate(value=math.radians(deg), orient_axis=axis, orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # Map up -> Z
    if up == 'x':
        rot('Y', -90)
        # recompute along/into after this would be messy; apply location snap below
    elif up == 'y':
        rot('X', 90)  # Y up -> Z up, Z -> -Y
    # now assume up is Z. If 'along' ended up on X, rotate 90° around Z.
    xs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    size = Vector((max(p.x for p in xs) - min(p.x for p in xs),
                   max(p.y for p in xs) - min(p.y for p in xs),
                   max(p.z for p in xs) - min(p.z for p in xs)))
    if abs(size.x - 4.15) < abs(size.y - 4.15):
        # along is currently X; rotate 90° around Z so along becomes Y
        rot('Z', 90)
    # snap: min X (road face) at 0, mid Y at 0, min Z at 0
    bpy.context.view_layer.update()
    xs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    mn = Vector((min(p.x for p in xs), min(p.y for p in xs), min(p.z for p in xs)))
    mx = Vector((max(p.x for p in xs), max(p.y for p in xs), max(p.z for p in xs)))
    midy = 0.5 * (mn.y + mx.y)
    ob.location -= Vector((mn.x, midy, mn.z))
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.name = 'lattice_template'
    ob['lot_kind'] = 'prop'
    print('LATTICE snapped size', tuple(mx - mn), 'min now ~0')
    return ob

def instance_lattice_row(template, zs, x, yaw_godot=0.0):
    """Duplicate the template along travel (zs centres) at LotArt x, y=0."""
    obs = []
    for z in zs:
        o = template.copy()
        o.data = template.data  # share mesh
        bpy.context.scene.collection.objects.link(o)
        loc = Vector(B(x, 0, z))
        # yaw around Godot +Y = Blender +Z
        o.location = loc
        o.rotation_euler = (0, 0, -yaw_godot)  # Blender Z rot; Godot +yaw around Y... careful
        # Godot yaw around +Y, looking from above: +yaw rotates +Z toward -X? 
        # We'll use yaw_godot as rotation around up, from +Z toward +X (right-hand).
        # Blender up is Z, right-hand +Z rotation rotates +X toward +Y.
        # Godot +Y rotation rotates +Z toward -X (Y-up right-hand).
        # Mapping is messy; taper flanks will be visually checked.
        if yaw_godot:
            o.rotation_euler[2] = yaw_godot  # try direct; tweak if flanks are wrong
        o.name = 'lattice_z%.1f' % z
        o['lot_kind'] = 'prop'
        obs.append(o)
    return obs

def build_back_wall():
    tmpl = import_lattice_template()
    obs = []
    step = 4.0
    # mid run, just behind the back curb — modules stay axis-aligned (into +X)
    z = MID_A + 2.0
    zs = []
    while z < MID_B - 0.1:
        zs.append(z)
        z += step
    if tmpl:
        # unique mesh copies so mask restore / export is unambiguous
        row = instance_lattice_row(tmpl, zs, POCKET_W + 0.7, 0.0)
        for o in row:
            o.data = o.data.copy()
        obs.extend(row)
        tmpl.hide_set(True)
        tmpl.hide_render = True
    # taper flanks: a simple cut-slope panel (yawed lattice modules presented a giant face to the road)
    ms = mat('lot_cut_slope', 'lot_cut_slope', 'surface', 'Linear')
    b = Builder('lot_taper_cut', 'surface')
    def taper_bank(z0, z1, grow):
        n = 6
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            if grow > 0:
                w0, w1 = max(0.4, POCKET_W * u0), max(0.4, POCKET_W * u1)
            else:
                w0, w1 = max(0.4, POCKET_W * (1 - u0)), max(0.4, POCKET_W * (1 - u1))
            za = z0 + (z1 - z0) * u0
            zb = z0 + (z1 - z0) * u1
            # face: from the lot edge up the cut, 5 m run, 7.2 m rise (matches the lattice module)
            b.quad([
                (w0 + 0.35, 0.0, za), (w1 + 0.35, 0.0, zb),
                (w1 + 5.35, 7.2, zb), (w0 + 5.35, 7.2, za),
            ], [(0, 0), (1, 0), (1, 1), (0, 1)], ms)
    taper_bank(0.0, MID_A, +1)
    taper_bank(MID_B, POCKET_M, -1)
    obs.append(b.finish())
    return [o for o in obs if not o.hide_render]

def build_hill_top():
    mv = mat('lot_verge', 'lot_verge', 'surface', 'Linear')
    b = Builder('lot_hill_verge', 'surface')
    # verge strip behind the lattice
    x0, x1 = POCKET_W + 5.5, POCKET_W + 16.0
    b.quad([
        (x0, 7.4, MID_A), (x1, 9.5, MID_A), (x1, 9.5, MID_B), (x0, 7.4, MID_B),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], mv)
    obs = [b.finish()]
    # cedar cards on the cut top
    z = 1.0
    idx = 0
    while z < POCKET_M - 1.0:
        if z < MID_A:
            w_here = POCKET_W * max(0.2, z / TAPER_M)
        elif z > MID_B:
            w_here = POCKET_W * max(0.2, (POCKET_M - z) / TAPER_M)
        else:
            w_here = POCKET_W
        for row, dx, h0 in ((0, 6.5, 11.0), (1, 10.0, 13.5), (2, 13.5, 15.0)):
            tex = 'touge_cedar_a' if (idx + row) % 2 == 0 else 'touge_cedar_b'
            h = h0 + (1.2 if (idx + row) % 3 == 0 else 0)
            zz = z + (0.7 if row == 1 else (-0.4 if row == 2 else 0))
            xx = w_here + dx
            obs.append(cedar_card(tex, h, xx, 7.6, zz, idx * 10 + row))
        z += 3.4
        idx += 1
    return obs

def cedar_card(tex, h, x, y, z, seed):
    w = h * 64 / 192
    b = Builder('lot_cedar_%d' % seed, 'card')
    m = mat('lot_cedar_' + tex, tex, 'card', 'Closest', alpha='CLIP')
    # cross card: one plane facing ±Z, one facing ±X
    b.quad([
        (x - w / 2, y, z), (x + w / 2, y, z), (x + w / 2, y + h, z), (x - w / 2, y + h, z),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    b.quad([
        (x, y, z - w / 2), (x, y, z + w / 2), (x, y + h, z + w / 2), (x, y + h, z - w / 2),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], m)
    return b.finish()

# ---------------------------------------------------------------------------
# Preview-only context (not in slot glbs)
# ---------------------------------------------------------------------------
def build_preview_context():
    mr = mat('lot_road', 'lot_road', 'surface', 'Linear')
    mc = mat('lot_cut_slope', 'lot_cut_slope', 'surface', 'Linear')
    mv = mat('lot_verge', 'lot_verge', 'surface', 'Linear')
    ms = mat('lot_sky', 'lot_sky', 'surface', 'Linear')
    obs = []
    br = Builder('preview_road', 'surface')
    tile = 8.0
    br.quad([
        (-ROAD_W, 0.0, -16.0), (0.02, 0.0, -16.0), (0.02, 0.0, POCKET_M + 16.0), (-ROAD_W, 0.0, POCKET_M + 16.0),
    ], [(0, 0), (ROAD_W / tile, 0), (ROAD_W / tile, (POCKET_M + 32) / tile), (0, (POCKET_M + 32) / tile)], mr)
    obs.append(br.finish(tess=True))
    # drop / cut on the outside of the road (x more negative)
    bc = Builder('preview_drop', 'surface')
    bc.quad([
        (-ROAD_W - 0.05, 0.0, -16.0), (-ROAD_W - 14.0, -7.0, -16.0),
        (-ROAD_W - 14.0, -7.0, POCKET_M + 16.0), (-ROAD_W - 0.05, 0.0, POCKET_M + 16.0),
    ], [(0, 0), (1, 0), (1, 1), (0, 1)], mc)
    obs.append(bc.finish())
    # sky dome (preview only)
    bsky = Builder('lot_sky', 'surface')
    Rsky = 240.0
    segs, rings = 20, 8
    for i in range(rings):
        v0 = (i / rings) * 1.06 - 0.06
        v1 = ((i + 1) / rings) * 1.06 - 0.06
        z0, z1 = Rsky * math.sin(v0 * math.pi * 0.5), Rsky * math.sin(v1 * math.pi * 0.5)
        r0, r1 = Rsky * math.cos(v0 * math.pi * 0.5), Rsky * math.cos(v1 * math.pi * 0.5)
        for j in range(segs):
            a0, a1 = 2 * math.pi * j / segs, 2 * math.pi * (j + 1) / segs
            def P(r, a, y):
                # LotArt: x = r cos, z = r sin, y up; centre at mid pocket
                return (r * math.cos(a), y, r * math.sin(a) + 0.5 * POCKET_M)
            bsky.quad([P(r0, a1, z0), P(r0, a0, z0), P(r1, a0, z1), P(r1, a1, z1)],
                      [(j / segs, max(0, v0)), ((j + 1) / segs, max(0, v0)),
                       ((j + 1) / segs, max(0, v1)), (j / segs, max(0, v1))], ms)
    obs.append(bsky.finish())
    return obs

# ---------------------------------------------------------------------------
# Cameras (LotArt frame) + render (reuses the previous post)
# ---------------------------------------------------------------------------
def make_camera(name, loc_g, look_g, fov_deg, clip_end=260.0):
    cam = bpy.data.cameras.new(name)
    cam.lens_unit = 'FOV'
    cam.angle = math.radians(fov_deg)
    cam.clip_start = 0.15
    cam.clip_end = clip_end
    cam.sensor_fit = 'VERTICAL'
    cam.dof.use_dof = False
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(B(*loc_g))
    # Look-at in Blender space
    loc = Vector(B(*loc_g))
    look = Vector(B(*look_g))
    direction = (look - loc).normalized()
    rot = direction.to_track_quat('-Z', 'Y')
    ob.rotation_euler = rot.to_euler()
    return ob

def setup_eevee(scene, w=640, h=480):
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    if hasattr(scene.render, 'filter_size'):
        scene.render.filter_size = 0.01
    scene.render.use_motion_blur = False
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 0
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 1
    if hasattr(scene.eevee, 'use_taa_reprojection'):
        scene.eevee.use_taa_reprojection = False
    if hasattr(scene.eevee, 'use_bloom'):
        scene.eevee.use_bloom = False
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = False
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    world = bpy.data.worlds.new('lot_world')
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

def _mesh_slots():
    """Map mesh -> list of materials, unique by mesh (instances share data)."""
    out = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        if o.data not in out:
            out[o.data] = list(o.data.materials)
    return out

def _assign_mask(mask_by_kind):
    # Use a DISTINCT mask material per slot so Blender does not collapse slots
    # when two slots of one mesh (e.g. yellow line + chevron) get the same mk.
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        k = kind_of(o)
        base = mask_by_kind.get(k, mask_by_kind['surface'])
        if o.data.materials:
            for i in range(len(o.data.materials)):
                slot_m = base.copy()
                slot_m.name = 'mask_%s_%d' % (k, i)
                o.data.materials[i] = slot_m
        else:
            o.data.materials.append(base)

def _restore_slots(stashed):
    for me, mats in stashed.items():
        while len(me.materials) > 0:
            me.materials.pop(index=0)
        for m in mats:
            me.materials.append(m)

def render_all(scene, shots, mask_by_kind, dmat):
    """Beauties first (so a mask-slot collapse can never tint a later beauty)."""
    scene.view_layers[0].material_override = None
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.color_mode = 'RGB'
    for name, cam in shots:
        scene.camera = cam
        path = os.path.join(RAW, '%s_%s_beauty.png' % (OUT_TAG, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print('RENDER beauty', path)
    stashed = _mesh_slots()
    _assign_mask(mask_by_kind)
    for name, cam in shots:
        scene.camera = cam
        path = os.path.join(RAW, '%s_%s_mask.png' % (OUT_TAG, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    _restore_slots(stashed)
    scene.view_layers[0].material_override = dmat
    scene.render.image_settings.color_depth = '16'
    scene.render.image_settings.color_mode = 'BW'
    for name, cam in shots:
        scene.camera = cam
        path = os.path.join(RAW, '%s_%s_depth.png' % (OUT_TAG, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = None
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.color_mode = 'RGB'

def render_views():
    scene = bpy.context.scene
    setup_eevee(scene)
    # race cam: on the road, 2.45 m up, 47°, passing the entrance, aimed 34 m up the road
    race = make_camera('race_cam',
                       (-RH - 0.5, 2.45, 6.0),
                       (2.5, 0.9, 40.0), 47.0)
    # overhead from the drop side (road in the foreground, lot on the far side / inside)
    over = make_camera('overhead',
                       (-18.0, 38.0, 20.0),
                       (POCKET_W * 0.45, 0.0, 0.5 * POCKET_M), 42.0, clip_end=320.0)
    # close: stalls + sign + chevrons
    close = make_camera('close_paint',
                        (-2.0, 2.3, MID_A - 4.0),
                        (3.0, 0.3, MID_A + 8.0), 40.0)
    close_sign = make_camera('close_sign',
                             (ISLAND_1 + 0.45, 2.10, MID_A - 4.2),
                             (ISLAND_1 + 0.45, 2.10, MID_A - 1.0), 32.0)
    mask_by_kind, dmat = make_override_mats()
    shots = (('race_cam', race), ('overhead', over), ('close_paint', close), ('close_sign', close_sign))
    render_all(scene, shots, mask_by_kind, dmat)

def write_layout():
    lay = stall_layout()
    data = {
        'tag': OUT_TAG,
        'frame': 'LotArt: origin=road edge at entrance, +X into lot, +Y up, +Z along travel (Godot Y-up)',
        'pocket_m': POCKET_M, 'taper_m': TAPER_M, 'pocket_w_m': POCKET_W,
        'rows': ROWS, 'n_lamps': N_LAMPS, 'n_stalls_per_row': lay['n_st'],
        'stall_w_m': STALL_W, 'stall_d_m': STALL_D, 'stall_angle_deg': STALL_ANGLE,
        'stall_spacing_m': lay['spacing'], 'curb_h_m': CURB_H,
        'island_d_m': [ISLAND_0, ISLAND_1],
        'lamp_z_m': lamp_zs(), 'pool_radius_m': pool_radius(),
        'aisle_x_m': [lay['aisle0'], lay['aisle1']],
        'piece_tris': STATS,
        'mapping': {
            'lot_floor.glb': 'Floor',
            'lot_curbs.glb': 'Curbs',
            'lot_stall_lines.glb': 'StallLines',
            'lot_wheel_stops.glb': 'WheelStops',
            'lot_back_wall.glb': 'BackWall',
            'lot_hill_top.glb': 'HillTop',
            'lot_lamps.glb (Lamp children) / lot_lamp.glb': 'Lamps',
            'lot_props.glb (Sign, Vending)': 'Props',
            'lot_road_paint.glb': 'LotArt',
        },
    }
    slots = [s for s in STATS if s['name'] != 'lot_assembled_preview']
    data['piece_tris'] = slots
    data['total_tris'] = sum(s['tris'] for s in slots)
    p = os.path.join(OUT, 'layout.json')
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)
    print('LAYOUT', p)
    if OUT_TAG in ('', 'w16'):
        root_layout = os.path.join(ROOT, 'layout.json')
        with open(root_layout, 'w') as f:
            json.dump(data, f, indent=2)
        tri = {
            'pocket_m': POCKET_M, 'taper_m': TAPER_M, 'pocket_w_m': POCKET_W,
            'rows': ROWS, 'n_lamps': N_LAMPS, 'n_stalls_per_row': lay['n_st'],
            'stall_w_m': STALL_W, 'stall_d_m': STALL_D, 'stall_angle_deg': STALL_ANGLE,
            'piece_tris': slots, 'total_tris': data['total_tris'],
        }
        with open(os.path.join(ROOT, 'tri_counts.json'), 'w') as f:
            json.dump(tri, f, indent=2)
        print('LAYOUT', root_layout)
    return data

def write_tscn():
    # Godot 4 packed scene. Approved kit lives at res://art/kits/turnout_lot/glb/.
    if OUT_TAG in ('', 'w16'):
        rel = 'res://art/kits/turnout_lot/glb'
        tscn_name = 'turnout_lot.tscn'
    else:
        rel = 'res://art/kits/turnout_lot/glb/%s' % OUT_TAG
        tscn_name = 'turnout_lot_%s.tscn' % OUT_TAG
    slots = [
        ('Floor', 'lot_floor.glb'),
        ('Curbs', 'lot_curbs.glb'),
        ('StallLines', 'lot_stall_lines.glb'),
        ('WheelStops', 'lot_wheel_stops.glb'),
        ('BackWall', 'lot_back_wall.glb'),
        ('HillTop', 'lot_hill_top.glb'),
        ('Lamps', 'lot_lamps.glb'),
        ('Props', 'lot_props.glb'),
        ('LotArt', 'lot_road_paint.glb'),
    ]
    lines = ['[gd_scene load_steps=%d format=3]\n' % (len(slots) + 2)]
    lines.append('[ext_resource type="Script" path="res://scripts/turnout_lot.gd" id="1"]\n')
    for i, (node, glb) in enumerate(slots, start=2):
        lines.append('[ext_resource type="PackedScene" path="%s/%s" id="%d"]\n' % (rel, glb, i))
    lines.append('\n[node name="TurnoutLot" type="Node3D"]\n')
    lines.append('script = ExtResource("1")\n')
    for i, (node, glb) in enumerate(slots, start=2):
        lines.append('\n[node name="%s" type="Node3D" parent="."]\n' % node)
        lines.append('\n[node name="%s" parent="%s" instance=ExtResource("%d")]\n' % (glb.replace('.glb', ''), node, i))
    scenes = os.path.join(ROOT, 'scenes')
    os.makedirs(scenes, exist_ok=True)
    path = os.path.join(scenes, tscn_name)
    with open(path, 'w') as f:
        f.writelines(lines)
    print('TSCN', path)

def main():
    reset()
    groups = {}
    groups['lot_floor'] = build_floor()
    groups['lot_curbs'] = build_curbs()
    groups['lot_stall_lines'] = build_stall_lines()
    groups['lot_wheel_stops'] = build_wheel_stops()
    groups['lot_road_paint'] = build_road_paint()
    groups['lot_props'] = build_props()
    groups['lot_lamps'] = build_lamps()
    # also export a single lamp module at the origin for instancing
    # (build_lamps already placed copies; export a fresh one later)
    groups['lot_back_wall'] = build_back_wall()
    groups['lot_hill_top'] = build_hill_top()

    # export each group from this assembled scene (objects already placed)
    # hide others while exporting? use_selection on the group's objects is enough.
    for name, obs in groups.items():
        export_glb(name, obs)

    # single lamp module at origin (separate scene would be cleaner; skip if already have lot_lamps)
    # Preview context + views
    build_preview_context()
    write_layout()
    write_tscn()
    if os.environ.get('SKIP_RENDER') != '1':
        render_views()
    # assembled preview glb (same 1444 tris in one file). Off by default so it
    # is not committed next to the per-child pieces.
    if os.environ.get('PREVIEW_GLB') == '1':
        slot_obs = []
        for n, obs in groups.items():
            slot_obs.extend(obs)
        export_glb('lot_assembled_preview', slot_obs)
    print('DONE', OUT_TAG)

if __name__ == '__main__':
    main()
