# Vendored here on 2026-11-19 after unapproved/arthur/experiments/wangan_two_corner was deleted.
# Blender 4.2 headless: the Wangan expressway kit for the two-corner playtest (Arthur, unapproved experiment).
#   /workspace/tools/blender-4.2.3-linux-x64/blender -b -P blender/build_wangan.py
# Starts from ../../../mockups/districts/blender/build_assets.py (same Builder, same conventions; wangan_lamp and
# wangan_tower_0..2 are copied verbatim so this folder rebuilds every Wangan asset it uses) and adds the pieces the
# district frame did not have: a parapet module that Godot bends onto the sweepers, deck piers, an overhead sign
# gantry, a km-post plate, harbour cranes and a cable-stayed bay bridge for the far silhouette.
# Low-poly PSX modules, unlit in Godot (night values painted into ../godot/art/env/*.png by ../tex_src/make_tex.py).
# Material names starting "Emit_" are drawn full-bright in Godot; Godot maps every material name to
# res://art/env/<name lowercased>.png, so the textures embedded in the .glb are never used.
# Axes (Blender): +X = away from the road edge (or across the road for centred pieces), Y = along the road, Z = up.
# glTF is Y-up, so Blender -Y becomes Godot local +Z = the direction of travel; sign faces point to Blender +Y.
import bpy, bmesh, os, math, random, json
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
    t.interpolation = 'Closest'
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
        def u(la, lb):
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
            if uvfront and k in uvfront: self.quad(vs, [(0, 0), (1, 0), (1, 1), (0, 1)], uvfront[k])
            else: self.quad(vs, u(la, lb), m)
    def beam(self, a, b, w, m):
        """thin square beam from point a to point b (4 side faces, no caps): truss members, crane legs, stays."""
        ax, ay, az = a; bx, by, bz = b
        d = (bx - ax, by - ay, bz - az); L = math.sqrt(sum(c * c for c in d)); d = tuple(c / L for c in d)
        up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
        s1 = (d[1]*up[2] - d[2]*up[1], d[2]*up[0] - d[0]*up[2], d[0]*up[1] - d[1]*up[0]); n1 = math.sqrt(sum(c*c for c in s1)); s1 = tuple(c / n1 * w / 2 for c in s1)
        s2 = (d[1]*s1[2] - d[2]*s1[1], d[2]*s1[0] - d[0]*s1[2], d[0]*s1[1] - d[1]*s1[0]); n2 = math.sqrt(sum(c*c for c in s2)); s2 = tuple(c / n2 * w / 2 for c in s2)
        P = lambda o, i, j: (o[0] + i*s1[0] + j*s2[0], o[1] + i*s1[1] + j*s2[1], o[2] + i*s1[2] + j*s2[2])
        ring = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        for k in range(4):
            (i0, j0), (i1, j1) = ring[k], ring[(k + 1) % 4]
            self.quad([P(a, i0, j0), P(a, i1, j1), P(b, i1, j1), P(b, i0, j0)], [(0, 0), (1, 0), (1, L / 4), (0, L / 4)], m)
    def cyl(self, c, r0, r1, h, m, n=6, uvscale=1.0, cap=True):
        cx, cy, cz = c
        for i in range(n):
            a0 = 2*math.pi*i/n; a1 = 2*math.pi*(i+1)/n
            p = lambda a, r, z: (cx + r*math.cos(a), cy + r*math.sin(a), cz + z)
            self.quad([p(a0, r0, 0), p(a1, r0, 0), p(a1, r1, h), p(a0, r1, h)],
                      [(i/n, 0), ((i+1)/n, 0), ((i+1)/n, h/uvscale), (i/n, h/uvscale)], m)
            if cap:
                self.tri([(cx, cy, cz + h), p(a0, r1, h), p(a1, r1, h)], [(0.5, 0.5), (0, 0), (1, 0)], m)
    def finish(self, tess=True):
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

# --- copied from districts/build_assets.py (unchanged) ------------------------------------------------
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

def wangan_tower(i, W, D, H):
    reset(); n = 'wangan_tower_%d' % i; b = Builder(n); e = mat('Emit_tower_%d' % i, 'emit_tower_%d' % i)
    b.box((0, 0, 0), (D, W, H), e, faces=['-x', '+x', '-y', '+y'], uvscale=None)
    ob = b.finish(tess=False)
    me = ob.data; uv = me.uv_layers.active.data
    for p in me.polygons:
        xs = [me.vertices[v].co for v in p.vertices]
        wid = (xs[0] - xs[1]).length
        for li in p.loop_indices:
            u, v = uv[li].uv
            uv[li].uv = (u * max(1.0, wid / 14.0), v * H / 60.0)
    export(n)

# --- NEW: parapet module (4 m), cast-in-place concrete wall on the deck edge ---------------------------
# Profile (x away from the road, z up), road-side foot at x = 0. Two 2 m rows along so Godot's bend stays smooth.
# u follows the painted bands of wangan_parapet.png: road face 0..0.55, top 0.55..0.68, back face 0.68..1.
PARAPET = [(0.00, 0.00, 0.00), (0.00, 0.10, 0.08), (0.07, 0.30, 0.22), (0.20, 0.62, 0.42), (0.24, 1.00, 0.55),
           (0.46, 1.00, 0.68), (0.50, 0.92, 0.74), (0.50, -1.10, 1.00)]
def wangan_parapet():
    reset(); b = Builder('wangan_parapet'); m = mat('wangan_parapet', 'wangan_parapet')
    L, rows = 4.0, 2
    for r in range(rows):
        ya, yb = -L/2 + L * r / rows, -L/2 + L * (r + 1) / rows
        va, vb = (ya + L/2) / L, (yb + L/2) / L
        for (xa, za, ua), (xc, zc, uc) in zip(PARAPET, PARAPET[1:]):
            b.quad([(xa, yb, za), (xa, ya, za), (xc, ya, zc), (xc, yb, zc)], [(ua, vb), (ua, va), (uc, va), (uc, vb)], m)
    b.finish(tess=False); export('wangan_parapet')

# --- NEW: deck pier (single column + crosshead) under the road centre, top at the deck soffit -------------
def wangan_pier():
    reset(); b = Builder('wangan_pier'); m = mat('wangan_pier', 'wangan_pier')
    soffit, water = -1.9, -16.0
    b.box((0, 0, water), (2.4, 1.8, soffit - 1.6 - water), m, faces=['-x', '+x', '-y', '+y'], uvscale=6.0)
    b.box((0, 0, soffit - 1.6), (12.0, 2.0, 1.6), m, faces=['-x', '+x', '-y', '+y', '-z'], uvscale=6.0)
    for x in (-4.6, -1.6, 1.6, 4.6):   # bearing blocks
        b.box((x, 0, soffit - 0.0 - 0.3), (0.7, 0.9, 0.3), m, faces=['-x', '+x', '-y', '+y'])
    b.finish(); export('wangan_pier')

# --- NEW: overhead sign gantry spanning the 11.9 m deck; posts stand outside the parapets ----------------
def wangan_gantry():
    reset(); b = Builder('wangan_gantry'); st = mat('wangan_steel', 'wangan_steel'); e = mat('Emit_sodium', 'emit_sodium')
    s0 = mat('wangan_sign_0', 'wangan_sign_0'); s1 = mat('wangan_sign_1', 'wangan_sign_1'); s2 = mat('wangan_sign_2', 'wangan_sign_2')
    X = 7.1; z0, z1 = 6.9, 7.7          # bottom / top chord heights
    for x in (-X, X):                    # posts (on brackets off the deck edge) + base plates
        b.box((x, 0, -1.2), (0.45, 0.45, z1 + 0.3 + 1.2), st, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=3.0)
    for z in (z0, z1):                   # chords
        for y in (-0.3, 0.3):
            b.beam((-X, y, z), (X, y, z), 0.16, st)
    n = 8                                # Warren web on the front and back faces
    for y in (-0.3, 0.3):
        for i in range(n):
            xa, xb = -X + 2 * X * i / n, -X + 2 * X * (i + 1) / n
            b.beam((xa, y, z0 if i % 2 == 0 else z1), (xb, y, z1 if i % 2 == 0 else z0), 0.08, st)
    # sign faces toward the oncoming car (Blender +Y), hung off the front chord; backs are plain steel
    def panel(cx, w, h, top, tex):
        y = 0.42; xa, xb = cx - w/2, cx + w/2; zb = top - h
        b.quad([(xb, y, zb), (xa, y, zb), (xa, y, top), (xb, y, top)], [(1, 0), (0, 0), (0, 1), (1, 1)], tex)
        b.quad([(xa, y - 0.06, zb), (xb, y - 0.06, zb), (xb, y - 0.06, top), (xa, y - 0.06, top)], [(0, 0), (1, 0), (1, 1), (0, 1)], st)
        b.quad([(xa, y + 0.6, zb - 0.05), (xb, y + 0.6, zb - 0.05), (xb, y, zb - 0.05), (xa, y, zb - 0.05)], [(0, 0), (1, 0), (1, 1), (0, 1)], st)   # lamp catwalk
        for lx in (cx - w/4, cx + w/4):  # small sign lamps on the catwalk, heads lit
            b.quad([(lx - 0.18, y + 0.58, zb - 0.04), (lx + 0.18, y + 0.58, zb - 0.04), (lx + 0.18, y + 0.4, zb - 0.04), (lx - 0.18, y + 0.4, zb - 0.04)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    panel(-2.9, 4.8, 1.8, z1 + 0.15, s0)
    panel(2.3, 4.8, 1.8, z1 + 0.15, s1)
    panel(6.0, 1.6, 0.8, z1 - 0.1, s2)
    b.finish(); export('wangan_gantry')

# --- NEW: km post plate on a stub, sits on the parapet top ------------------------------------------
def wangan_kpost():
    reset(); b = Builder('wangan_kpost'); st = mat('wangan_steel', 'wangan_steel'); k = mat('wangan_kpost', 'wangan_kpost')
    b.box((0.25, 0, 1.0), (0.06, 0.06, 0.35), st, faces=['-x', '+x', '-y', '+y'])
    b.quad([(0.05, 0.22, 1.25), (0.05, -0.22, 1.25), (0.05, -0.22, 1.65), (0.05, 0.22, 1.65)], [(1, 0), (0, 0), (0, 1), (1, 1)], k)
    b.finish(tess=False); export('wangan_kpost')

# --- NEW: container gantry crane, far silhouette (60 m), red aviation light on the apex ----------------
def wangan_crane():
    reset(); b = Builder('wangan_crane'); s = mat('wangan_silhouette', 'wangan_silhouette'); e = mat('Emit_aviation', 'emit_aviation')
    G, D, H = 18.0, 14.0, 42.0           # gauge (along the quay), depth, portal height
    for x in (-G/2, G/2):
        for y in (-D/2, D/2):
            b.beam((x, y, 0), (x, y, H), 1.4, s)
        b.beam((x, -D/2, H * 0.55), (x, D/2, H * 0.55), 0.9, s)
    for y in (-D/2, D/2): b.beam((-G/2, y, H), (G/2, y, H), 1.6, s)
    b.beam((0, -D/2 - 34.0, H + 2.0), (0, D/2 + 22.0, H + 2.0), 2.2, s)     # boom out over the water + back reach
    b.beam((0, -2.0, H), (0, 0.0, H + 18.0), 1.0, s)                       # apex frame
    b.beam((0, 0.0, H + 18.0), (0, -D/2 - 30.0, H + 2.4), 0.5, s)          # forestay
    b.beam((0, 0.0, H + 18.0), (0, D/2 + 20.0, H + 2.4), 0.5, s)           # backstay
    b.box((0, D/2 + 18.0, H + 0.4), (6.0, 6.0, 4.0), s, faces=['-x', '+x', '-y', '+y', '+z'])   # machinery house
    b.box((0, 0.0, H + 18.0), (1.0, 1.0, 1.0), e, faces=['-x', '+x', '-y', '+y', '+z'])
    b.finish(tess=False); export('wangan_crane')

# --- NEW: cable-stayed bay bridge, far silhouette: 2 towers, deck, fan stays, a string of deck lamps ----
def wangan_bridge():
    reset(); b = Builder('wangan_bridge'); s = mat('wangan_silhouette', 'wangan_silhouette')
    e = mat('Emit_bridge_lamp', 'emit_bridge_lamp'); av = mat('Emit_aviation', 'emit_aviation')
    L, Wd, Hd, T = 520.0, 24.0, 32.0, 150.0   # deck length, width, deck height above water, tower top
    b.box((0, 0, Hd), (Wd, L, 3.0), s, faces=['-x', '+x', '-z', '+z'])
    for ty in (-L * 0.22, L * 0.22):
        for x in (-Wd/2 - 1.0, Wd/2 + 1.0):    # H tower legs, leaning in
            b.beam((x * 1.3, ty, 0), (x * 0.7, ty, T), 4.0, s)
        b.beam((-Wd/2 * 0.9, ty, Hd - 2.0), (Wd/2 * 0.9, ty, Hd - 2.0), 3.0, s)
        b.beam((-Wd/2 * 0.75, ty, T * 0.82), (Wd/2 * 0.75, ty, T * 0.82), 2.4, s)
        b.box((0, ty, T - 1.0), (1.6, 1.6, 1.6), av, faces=['-x', '+x', '-y', '+y'])
        for k in range(1, 7):                  # fan stays both ways (1.2 m wide so they survive 640x480 at distance)
            for sg in (-1, 1):
                b.beam((0, ty, T * (0.94 - 0.03 * k)), (0, ty + sg * k * 30.0, Hd + 1.5), 1.2, s)
    for k in range(-8, 9):                     # deck lamps: pale sodium dots every 30 m on both edges
        for x in (-Wd/2 + 0.3, Wd/2 - 0.3):
            b.box((x, k * 30.0, Hd + 1.5), (0.9, 0.9, 0.9), e, faces=['-x', '+x'])
    b.finish(tess=False); export('wangan_bridge')

wangan_lamp()
wangan_tower(0, 22, 18, 64); wangan_tower(1, 16, 16, 88); wangan_tower(2, 28, 20, 48)
wangan_parapet(); wangan_pier(); wangan_gantry(); wangan_kpost(); wangan_crane(); wangan_bridge()
json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts.json'), 'w'), indent=1)
print('STATS', STATS)
