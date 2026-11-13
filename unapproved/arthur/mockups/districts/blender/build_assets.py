# Blender 4.2 headless: build the district prop kit and export glTF for Godot.
#   blender -b -P blender/build_assets.py
# Low-poly PSX modules, unlit in Godot (night values are painted into ../tex/*.png by tex_src/make_tex.py).
# Material names starting "Emit_" are drawn full-bright in Godot; everything else gets the district prop gain.
# Axes (Blender): +X = away from the road edge, Y = along the road, Z = up. Module road-facing edge sits at x = 0.
# Bases from the downloaded packs: Urban Stacked Jersey_barrier (geometry), Kenney / Shacks textures (via make_tex.py).
import bpy, bmesh, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.normpath(os.path.join(HERE, '..', 'godot', 'art', 'env'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'godot', 'assets', 'env'))
os.makedirs(OUT, exist_ok=True)
STATS = []

_mats = {}
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()

def mat(name, tex):
    key = (name, tex)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, tex + '.png'))
    t.interpolation = 'Linear'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 1.0
    _mats[key] = m
    return m

class Builder:
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []
    def mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)
    def quad(self, vs, uvs, m):
        """vs: 4 corners CCW seen from the visible side; uvs matching."""
        bv = [self.bm.verts.new(v) for v in vs]
        f = self.bm.faces.new(bv); f.material_index = self.mi(m)
        for l, uv in zip(f.loops, uvs): l[self.uv].uv = uv
        return f
    def tri(self, vs, uvs, m):
        bv = [self.bm.verts.new(v) for v in vs]
        f = self.bm.faces.new(bv); f.material_index = self.mi(m)
        for l, uv in zip(f.loops, uvs): l[self.uv].uv = uv
    def box(self, c, s, m, faces='all', uvscale=None, uvfront=None):
        cx, cy, cz = c; sx, sy, sz = s
        x0, x1, y0, y1, z0, z1 = cx - sx/2, cx + sx/2, cy - sy/2, cy + sy/2, cz, cz + sz
        def u(a, b, la, lb):
            if uvscale: return [(0, 0), (la/uvscale, 0), (la/uvscale, lb/uvscale), (0, lb/uvscale)]
            return [(0, 0), (1, 0), (1, 1), (0, 1)]
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
            mm = m
            if uvfront and k in uvfront:
                mm = uvfront[k]; self.quad(vs, [(0, 0), (1, 0), (1, 1), (0, 1)], mm)
            else:
                self.quad(vs, u(0, 0, la, lb), mm)
    def cyl(self, c, r0, r1, h, m, n=6, uvscale=1.0, cap=True):
        cx, cy, cz = c
        for i in range(n):
            a0 = 2*math.pi*i/n; a1 = 2*math.pi*(i+1)/n
            p = lambda a, r, z: (cx + r*math.cos(a), cy + r*math.sin(a), cz + z)
            self.quad([p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, h), p(a0, r1, h)],
                      [(i/n, 0), ((i+1)/n, 0), ((i+1)/n, h/uvscale), (i/n, h/uvscale)], m)
            if cap:
                self.tri([(cx, cy, cz + h), p(a0, r1, h), p(a1, r1, h)], [(0.5, 0.5), (0, 0), (1, 0)], m)
    def finish(self, smooth=False, tess=True):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        if tess:
            # PSX affine UVs warp badly on big quads seen up close: grid-split large faces (~3 m cells)
            for f in [f for f in self.bm.faces if f.calc_area() > 12.0]:
                if not f.is_valid: continue
                cuts = min(2, max(1, int(math.sqrt(f.calc_area()) / 3.0)))
                bmesh.ops.subdivide_edges(self.bm, edges=list(f.edges), cuts=cuts, use_grid_fill=True)
        self.bm.normal_update(); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(ob)
        return ob

def export(name):
    tris = sum(len(p.vertices) - 2 for o in bpy.context.scene.objects if o.type == 'MESH' for p in o.data.polygons)
    p = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', export_apply=True, export_yup=True,
                              export_image_format='AUTO', export_materials='EXPORT')
    STATS.append((name, tris)); print('EXPORT', name, tris)

# --- Touge: cut slope (rock + shotcrete toe), 6 m module -------------------------------------------
def touge_cutslope(seed, name):
    reset(); b = Builder(name); m = mat('touge_cutslope', 'touge_cutslope'); g = mat('touge_grasslip', 'touge_grasslip')
    rr = random.Random(seed)
    L, H, lean = 6.0, 7.5, 3.2
    ny, nz = 4, 5
    def jit(i, j):
        if i in (0, ny) or j == 0: return 0.0
        return rr.uniform(-0.35, 0.45)
    J = [[jit(i, j) for j in range(nz + 1)] for i in range(ny + 1)]
    P = lambda i, j: (lean * (j / nz) ** 0.8 + J[i][j], -L/2 + L * i / ny, H * j / nz + (0.3 * J[i][j] if j not in (0, nz) else 0))
    for i in range(ny):
        for j in range(nz):
            vs = [P(i + 1, j), P(i, j), P(i, j + 1), P(i + 1, j + 1)]
            uvs = [((i + 1) / ny * 1.5, j / nz), (i / ny * 1.5, j / nz), (i / ny * 1.5, (j + 1) / nz), ((i + 1) / ny * 1.5, (j + 1) / nz)]
            b.quad(vs, uvs, m)
    # grass lip on top running back
    for i in range(ny):
        a, c = P(i, nz), P(i + 1, nz)
        b.quad([c, a, (a[0] + 4, a[1], a[2] + 0.6), (c[0] + 4, c[1], c[2] + 0.6)], [(1, 0), (0, 0), (0, 1), (1, 1)], g)
    b.finish(); export(name)

# --- Touge: W-beam guardrail, 4 m module with 2 posts + 1 reflector ----------------------------------
def touge_guardrail():
    reset(); b = Builder('touge_guardrail'); m = mat('touge_guardrail', 'touge_guardrail'); e = mat('Emit_reflector', 'emit_reflector')
    L = 4.0
    # W-beam: three slanted faces, rows of the texture v 0.34..1 (top of image = top of beam)
    prof = [(0.00, 0.80), (-0.06, 0.70), (0.00, 0.62), (-0.06, 0.52), (0.00, 0.44)]
    for k in range(len(prof) - 1):
        (xa, za), (xb, zb) = prof[k], prof[k + 1]
        va, vb = 1 - k / (len(prof) - 1) * 0.66, 1 - (k + 1) / (len(prof) - 1) * 0.66
        b.quad([(xb, L/2, zb), (xb, -L/2, zb), (xa, -L/2, za), (xa, L/2, za)], [(1, vb), (0, vb), (0, va), (1, va)], m)
    for y in (-L/4, L/4):
        b.box((0.12, y, 0.0), (0.12, 0.12, 0.76), m, faces=['-x', '+x', '-y', '+y'])
    b.quad([(-0.07, -L/4 + 0.04, 0.72), (-0.07, -L/4 - 0.04, 0.72), (-0.07, -L/4 - 0.04, 0.80), (-0.07, -L/4 + 0.04, 0.80)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    b.finish(); export('touge_guardrail')

# --- Street: concrete utility pole with crossarms, transformer and a small sodium lamp --------------
def street_pole():
    reset(); b = Builder('street_pole'); c = mat('street_pole_concrete', 'street_pole_concrete'); mt = mat('street_metal', 'street_metal'); e = mat('Emit_sodium', 'emit_sodium')
    b.cyl((0, 0, 0), 0.17, 0.12, 9.6, c, n=6, uvscale=3.0)
    for z, w in ((9.1, 1.8), (8.5, 1.4)):
        b.box((0, 0, z), (w, 0.10, 0.10), mt)
        for x in (-w/2 + 0.1, w/2 - 0.1):
            b.box((x, 0, z + 0.1), (0.06, 0.06, 0.14), mt, faces=['-x', '+x', '-y', '+y', '+z'])
    b.cyl((0.32, 0, 6.6), 0.22, 0.22, 0.75, mt, n=6)       # transformer can
    b.box((-0.7, 0, 5.4), (1.4, 0.06, 0.06), mt)             # lamp arm toward the road (-x)
    b.box((-1.35, 0, 5.28), (0.42, 0.18, 0.12), mt, faces=['-x', '+x', '-y', '+y', '+z'])
    b.quad([(-1.55, -0.08, 5.27), (-1.15, -0.08, 5.27), (-1.15, 0.08, 5.27), (-1.55, 0.08, 5.27)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    b.box((-0.05, 0, 2.6), (0.04, 0.34, 0.9), mt, faces=['-x'])  # pole number plate
    b.finish(); export('street_pole')

# --- Street: shop buildings (front facade texture + plain sides), vertical sign, awning, roof box ---
def street_shop(i, W, H, D, sign, awning):
    reset(); n = 'street_shop_%d' % i; b = Builder(n)
    f = mat('street_shop_%d' % i, 'street_shop_%d' % i); s = mat('street_sidewall', 'street_sidewall'); mt = mat('street_metal', 'street_metal')
    b.box((D/2, 0, 0), (D, W, H), s, faces=['-x', '-y', '+y', '+z'], uvscale=4.0, uvfront={'-x': f})
    if sign is not None:
        e = mat('Emit_sign_v%d' % sign, 'emit_sign_v%d' % sign)
        y = W/2 - 0.5
        b.box((-0.42, y, H * 0.36), (0.5, 0.14, H * 0.42), e, faces=['-y', '+y'], uvfront=None)
        b.box((-0.42, y, H * 0.36), (0.5, 0.14, H * 0.42), mt, faces=['-x', '+z'])
        b.box((-0.12, y, H * 0.36 + H * 0.2), (0.24, 0.06, 0.06), mt, faces=['+z', '-z', '-y'])
    if awning:
        z0 = H * 0.25 + 0.05
        b.quad([(-1.1, W/2 - 0.2, z0 - 0.4), (-1.1, -W/2 + 0.2, z0 - 0.4), (0, -W/2 + 0.2, z0), (0, W/2 - 0.2, z0)], [(0, 0), (1, 0), (1, 1), (0, 1)], mt)
    b.box((D * 0.55, -W * 0.15, H), (1.8, 1.4, 1.1), s, faces=['-x', '-y', '+y', '+z'], uvscale=2.0)
    b.finish(); export(n)

# --- Street: vending machine --------------------------------------------------------------------
def street_vending():
    reset(); b = Builder('street_vending'); e = mat('Emit_vending_front', 'emit_vending_front'); body = mat('vending_body', 'vending_body')
    b.box((0.38, 0, 0), (0.75, 1.0, 1.85), body, faces=['-x', '-y', '+y', '+z'], uvfront={'-x': e})
    b.finish(); export('street_vending')

# --- Wangan: tall expressway lamp with a long arm over the lanes -----------------------------------
def wangan_lamp():
    reset(); b = Builder('wangan_lamp'); g = mat('wangan_galv', 'wangan_galv'); e = mat('Emit_sodium', 'emit_sodium')
    b.cyl((0.25, 0, 0.9), 0.14, 0.10, 10.4, g, n=6, uvscale=4.0)
    pts = [(0.25, 11.3), (-0.6, 11.75), (-2.2, 11.95), (-4.2, 11.95)]
    for (xa, za), (xb, zb) in zip(pts, pts[1:]):
        b.quad([(xa, -0.06, za), (xb, -0.06, zb), (xb, 0.06, zb), (xa, 0.06, za)], [(0, 0), (1, 0), (1, 1), (0, 1)], g)
        b.quad([(xa, -0.06, za - 0.1), (xb, -0.06, zb - 0.1), (xb, -0.06, zb), (xa, -0.06, za)], [(0, 0), (1, 0), (1, 1), (0, 1)], g)
    b.box((-4.5, 0, 11.75), (0.95, 0.36, 0.2), g, faces=['-x', '+x', '-y', '+y', '+z'])
    b.quad([(-4.95, -0.16, 11.74), (-4.05, -0.16, 11.74), (-4.05, 0.16, 11.74), (-4.95, 0.16, 11.74)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    b.finish(); export('wangan_lamp')

# --- Wangan: jersey barrier, geometry from the Urban Stacked pack, night-tinted texture ---------------
def wangan_jersey():
    reset()
    src = '/workspace/district_scenes/assets/urban/Jersey_barrier.glb'
    bpy.ops.import_scene.gltf(filepath=src)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    m = mat('wangan_barrier', 'wangan_barrier')
    for o in obs:
        o.data.materials.clear(); o.data.materials.append(m)
    # recentre on the AABB (pack pieces carry baked world offsets), base on z = 0
    import mathutils
    pts = [o.matrix_world @ mathutils.Vector(c) for o in obs for c in o.bound_box]
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size = mx - mn; print('JERSEY size', tuple(size))
    for o in obs:
        o.matrix_world = mathutils.Matrix.Translation(-mathutils.Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))) @ o.matrix_world
    # long axis along Y (along the road)
    if size.x > size.y:
        for o in obs:
            o.matrix_world = mathutils.Matrix.Rotation(math.pi / 2, 4, 'Z') @ o.matrix_world
    export('wangan_jersey')

# --- Wangan: distant city towers (emissive window facades) ----------------------------------------
def wangan_tower(i, W, D, H):
    reset(); n = 'wangan_tower_%d' % i; b = Builder(n); e = mat('Emit_tower_%d' % i, 'emit_tower_%d' % i)
    b.box((0, 0, 0), (D, W, H), e, faces=['-x', '+x', '-y', '+y'], uvscale=None)
    # retile: scale UVs so windows stay ~1.3 m
    ob = b.finish(tess=False)
    me = ob.data; uv = me.uv_layers.active.data
    for p in me.polygons:
        xs = [me.vertices[v].co for v in p.vertices]
        wid = max((xs[0] - xs[1]).length, (xs[1] - xs[2]).length if False else 0.0)
        for li in p.loop_indices:
            u, v = uv[li].uv
            uv[li].uv = (u * max(1.0, wid / 14.0), v * H / 60.0)
    export(n)

touge_cutslope(3, 'touge_cutslope_a'); touge_cutslope(8, 'touge_cutslope_b')
touge_guardrail()
street_pole()
street_shop(0, 7.0, 12.0, 8.0, 0, True)
street_shop(1, 6.0, 10.0, 8.0, 1, False)
street_shop(2, 7.5, 12.0, 8.0, None, True)
street_shop(3, 6.5, 10.0, 8.0, 3, False)
street_vending()
wangan_lamp(); wangan_jersey()
wangan_tower(0, 22, 18, 64); wangan_tower(1, 16, 16, 88); wangan_tower(2, 28, 20, 48)
print('STATS', STATS)
