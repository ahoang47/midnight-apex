"""Low-poly PS2-style (v5) Honda S2000 with Spoon-style hardtop (AP1/AP2) built procedurally in Blender.
Usage: blender -b --python build_s2000.py [-- --no-render] [-- --no-export]
Axes: +X = forward, +Y = left (driver side, LHD), +Z = up. Units: metres.
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

OUT = os.environ.get("S2000_DIR", os.path.dirname(os.path.abspath(__file__)))  # repo: art/vehicles/s2000 (box original: /workspace/s2000)
RDIR = os.path.join(OUT, "renders")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
os.makedirs(RDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- dimensions
L_FRONT, L_REAR = 2.07, -2.07          # 4.14 m
WB_F, WB_R = 1.265, -1.148             # wheel centres measured on the blueprint (2.41 m)
TIRE_R, TIRE_W, TRACK_Y = 0.315, 0.215, 0.74
TRACK_F, TRACK_R = 0.72, 0.755          # blueprint front/rear tyre outer edges .82 / .86
ARCH_R = 0.37
SEAT_Z = 0.42
CP_FRONT, CP_REAR = 0.40, -0.845       # open cockpit (x range), from the blueprint
WS_TOP_X = 0.0                          # windshield header x (blueprint)
RIDE_DROP = 0.0                         # blueprint stance

# ---------------------------------------------------------------- texture atlas 256x256 (drawn by tex/make_atlas.py)
import subprocess, shutil
PY3 = shutil.which("python3") or "/usr/bin/python3"
def build_atlas():
    p = os.path.join(OUT, "s2000_atlas.png")
    subprocess.run([PY3, os.path.join(OUT, "tex", "make_atlas.py"), p], check=True)
    img = bpy.data.images.load(p, check_existing=False); img.name = "S2000_Atlas"
    return img
ATLAS = build_atlas()
UV_HEAD, UV_TAIL, UV_GRILLE, UV_WHEEL = (0, .5, .5, 1), (.5, .5, 1, 1), (0, 0, .5, .30), (.5, 0, 1, .5)
UV_S2000, UV_PLATE = (0, .31, .25, .365), (.13, .375, .49, .495)
UV_BADGE, UV_AMBER = (0.004, .379, .121, .496), (.41, .51, .48, .56)
UV_TAILLENS, UV_LAMP_OUT, UV_LAMP_IN = (.51, .77, .99, .985), (.5, .5, .75, .75), (.75, .5, 1, .75)

# ---------------------------------------------------------------- materials
def srgb(c): return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
def build_softtop_tex():
    p = os.path.join(OUT, "s2000_softtop.png")
    subprocess.run([PY3, os.path.join(OUT, "tex", "make_softtop.py"), p], check=True)
    img = bpy.data.images.load(p, check_existing=False); img.name = "S2000_SoftTopTex"
    return img
SOFTTOP_TEX = build_softtop_tex()

def make_mat(name, rgb, rough=0.55, metal=0.0, tex=False, coat=0.0, interp='Closest'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    col = (*srgb(rgb), 1)
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = col
    if coat:
        b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.04
    if tex:
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = ATLAS if tex is True else tex; n.interpolation = interp
        nt.links.new(n.outputs["Color"], b.inputs["Base Color"])
    return m
M = {
    "paint": make_mat("S2000_Paint_FormulaRed", (0.78, 0.05, 0.06), 0.45, coat=0.25),
    "softtop": make_mat("S2000_SoftTop_Fabric", (0.03, 0.03, 0.03), 0.92, tex=SOFTTOP_TEX, interp='Linear'),
    "black": make_mat("S2000_Trim_Black", (0.05, 0.05, 0.055), 0.7),
    "interior": make_mat("S2000_Interior", (0.09, 0.09, 0.10), 0.85),
    "seat": make_mat("S2000_Seat_Red", (0.45, 0.06, 0.06), 0.8),
    "glass": make_mat("S2000_Glass", (0.12, 0.14, 0.17), 0.08),
    "glass_rear": make_mat("S2000_Glass_RearWindow", (0.07, 0.08, 0.09), 0.55),
    "silver": make_mat("S2000_Silver", (0.62, 0.63, 0.65), 0.35, 0.6),
    "tire": make_mat("S2000_Tire", (0.04, 0.04, 0.04), 0.9),
    "atlas": make_mat("S2000_Lights_Atlas", (1, 1, 1), 0.3, tex=True, interp='Linear'),
}

M["glass_rear"].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.06   # dim, tinted plastic window

# ---------------------------------------------------------------- mesh builder
class MB:
    def __init__(self): self.v, self.f, self.sharp = [], [], []   # f: (idx tuple, mat key, uv list or None)
    def add_v(self, p): self.v.append(Vector(p)); return len(self.v) - 1
    def face(self, idx, mat, uvs=None): self.f.append((tuple(idx), mat, uvs))
    def box(self, c, he, mat, rot=(0, 0, 0)):
        R = Euler(rot).to_matrix(); c = Vector(c)
        ids = [self.add_v(c + R @ Vector((sx * he[0], sy * he[1], sz * he[2])))
               for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            self.face([ids[i] for i in q], mat)
    def beam(self, p0, p1, t, mat, up=(0, 0, 1)):
        p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0)
        a = d.normalized(); u = Vector(up)
        if abs(a.dot(u)) > 0.95: u = Vector((1, 0, 0))
        s = a.cross(u).normalized() * t / 2; u2 = s.cross(a).normalized() * t / 2
        ring = lambda p: [self.add_v(p + s + u2), self.add_v(p - s + u2), self.add_v(p - s - u2), self.add_v(p + s - u2)]
        r0, r1 = ring(p0), ring(p1)
        for i in range(4):
            j = (i + 1) % 4; self.face((r0[i], r0[j], r1[j], r1[i]), mat)
        self.face(r0[::-1], mat); self.face(r1, mat)
    def to_obj(self, name, mats, coll, smooth=None):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new(); bv = [bm.verts.new(p) for p in self.v]
        uvl = bm.loops.layers.uv.new("UVMap")
        keys = list(mats)
        for idx, mk, uvs in self.f:
            try: fa = bm.faces.new([bv[i] for i in idx])
            except ValueError: continue
            fa.material_index = keys.index(mk); fa.smooth = False
            if uvs:
                for lp, uv in zip(fa.loops, uvs): lp[uvl].uv = uv
        bm.edges.ensure_lookup_table()
        for a, b in self.sharp:
            e = bm.edges.get((bv[a], bv[b]))
            if e: e.smooth = False
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        if smooth: smooth_bm(bm, smooth)
        bm.to_mesh(me); bm.free()
        for k in keys: me.materials.append(M[k])
        ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
        return ob

def smooth_bm(bm, angle_deg):
    """PS2-style smoothing: smooth faces, but keep edges sharp above angle_deg, on material seams,
    on open borders, and wherever an edge was already flagged sharp (character line etc.)."""
    lim = math.radians(angle_deg)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        if not e.smooth: continue
        if len(e.link_faces) != 2: e.smooth = False; continue
        f0, f1 = e.link_faces
        if f0.material_index != f1.material_index or f0.normal.angle(f1.normal, 0) > lim: e.smooth = False

def smooth_mesh(me, angle_deg):
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); smooth_bm(bm, angle_deg); bm.to_mesh(me); bm.free()

def lerp_keys(keys, x):
    keys = sorted(keys)
    if x <= keys[0][0]: return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x0 <= x <= x1: return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return keys[-1][1]

# body section keyframes (x -> value)
# ---------------------------------------------------------------- blueprint-driven body curves
# Curves sampled from the user's S2000 blueprint (ref/blueprint.jpg) by bp/extract.py -> bp/curves.json:
#   side view  -> body top line (hood/belt/deck) and body bottom line (incl. wheel-arch openings)
#   top view   -> plan half-width per station (mirrors removed)
#   front/rear -> section envelope (used for the tuck / tumblehome factors below)
import json
BP = json.load(open(os.path.join(OUT, "bp", "curves.json")))
def _curve(key):
    a = np.array(BP[key], float); o = np.argsort(a[:, 0]); return a[o, 0], a[o, 1]
_TX, _TZ = _curve("side_body_top")
_BX, _BZ = _curve("side_body_bottom")
_WX, _WW = _curve("top_halfwidth")
_SX, _SZ = _curve("side_top_silhouette")
# clean-ups: the windshield base / door mirror confuse the belt extraction -> bridge it with the cowl-to-belt line
_m = (_TX > -0.03) & (_TX < 0.62)
_TZ[_m] = np.interp(_TX[_m], [-0.03, 0.62], [np.interp(-0.03, _TX, _TZ), np.interp(0.62, _TX, _TZ)])
_TZ = np.array([np.median(_TZ[max(0, i - 4):i + 5]) for i in range(len(_TZ))])
# vertical panel lines leave upward spikes in the bottom line -> rolling minimum
_BZ = np.array([_BZ[max(0, i - 7):i + 8].min() for i in range(len(_BZ))])
# the bumper lamps confuse the front arch's leading edge -> mirror the (clean) trailing half of the front arch
_wf = BP["wheel_x"][0]
for i, x in enumerate(_BX):
    if x > _wf + 0.30 and x < 2.0:
        dx = x - _wf
        _BZ[i] = np.interp(_wf - dx, _BX, _BZ) if dx < 0.40 else 0.19
_WW = np.array([np.mean(_WW[max(0, i - 3):i + 4]) for i in range(len(_WW))])
bp_top = lambda x: float(np.interp(x, _TX, _TZ))
ARCH_OPEN = .365   # wheel-arch opening radius about the hub (blueprint lip ~0.68 m above ground at the axle)
def bp_bot(x):
    z = float(np.interp(x, _BX, _BZ)) - .012
    for xc in (WB_F, WB_R):
        dx = abs(x - xc)
        if dx <= ARCH_OPEN + .004: z = max(.19, TIRE_R + math.sqrt(max(ARCH_OPEN ** 2 - dx * dx, 0)))
        elif dx <= ARCH_OPEN + .10: z = min(z, .19 if x < 1.9 else z)
    return z
bp_hw = lambda x: max(0.12, float(np.interp(x, _WX, _WW)))
bp_sil = lambda x: float(np.interp(x, _SX, _SZ))

K_ZC = [(2.07, .40), (1.95, .47), (1.6, .55), (1.23, .60), (0.6, .615), (0, .625), (-0.8, .635), (-1.2, .645), (-1.8, .655), (-2.07, .63)]
K_DOME = [(3, 0), (1.92, 0), (1.55, .018), (0.9, .022), (0.6, .02), (0.42, 0), (-3, 0)]   # soft hood power bulge

def pchip(keys, x):
    """Fritsch-Carlson monotone cubic through (x, y) keys."""
    k = sorted(keys); xs = [a for a, _ in k]; ys = [b for _, b in k]; n = len(k)
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0 if d[i - 1] * d[i] <= 0 else 3 * (xs[i + 1] - xs[i - 1]) /
                  ((2 * xs[i + 1] - xs[i] - xs[i - 1]) / d[i - 1] + (xs[i + 1] + xs[i] - 2 * xs[i - 1]) / d[i]) for i in range(1, n - 1)] + [d[-1]]
    i = max(j for j in range(n - 1) if xs[j] <= x); h = xs[i + 1] - xs[i]; t = (x - xs[i]) / h
    h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
    return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]

NH = 12   # points per half-section
# section shape factors measured on the blueprint front/rear views (fraction of the max half-width)
K_SF = [(3, .91), (0.6, .905), (0.0, .90), (-3, .905)]      # shoulder (belt) width
K_UF = [(3, .945), (-3, .95)]                            # upper side, between crease and shoulder
def section(x):
    w = bp_hw(x); ztop = bp_top(x); zb = bp_bot(x)
    zc = lerp_keys(K_ZC, x); dome = pchip(K_DOME, x)
    cp = CP_REAR < x < CP_FRONT
    front = x >= CP_FRONT
    if front: zs, zt = ztop, ztop - .012           # fenders a touch proud of the hood
    elif cp:  zs, zt = ztop, ztop
    else:     zs, zt = ztop - .012, ztop           # crowned rear deck
    zc = min(max(zc, zb + .02), zs - .035)
    zs = max(zs, zc + .03); h = zc - zb
    tk = max(0.0, min(1.0, h / .25))                # no tuck where the arch eats the lower body
    tf = lambda f: 1 - (1 - f) * tk
    sf = lerp_keys(K_SF, x)
    half = [(0, zb), (w * .86, zb), (w * tf(.925), zb + .2 * h), (w * tf(.955), zb + .5 * h), (w * tf(.978), zb + .8 * h),
            (w, zc), (w * lerp_keys(K_UF, x), zc + .5 * (zs - zc)), (w * sf, zs)]
    if cp:
        half += [(w * .865, zs + .005), (w * .83, zs - .12), (w * .78, SEAT_Z), (0, SEAT_Z)]
    else:
        sw = w * sf
        def hz(u):   # one continuous panel: soft cosine dome in the middle, shoulder blends in
            bump = 0.5 * (1 + math.cos(math.pi * min(u / 0.62, 1.0)))
            return zt + dome * bump + (zs - zt) * u ** 2.5
        half += [(sw * u, hz(u)) for u in (.73, .48, .24, 0)]
    ring = [(x, y, z) for y, z in half] + [(x, -y, z) for y, z in half[-2:0:-1]]
    return ring, cp

def build_body(coll):
    xs = {L_FRONT, 2.06, 2.05, 2.03, 2.0, 1.96, 1.91, 1.85, 1.78, CP_FRONT + .01, CP_FRONT - .01, CP_REAR + .01, CP_REAR - .01,
          -1.80, -1.88, -1.94, -1.99, -2.03, -2.05, -2.062, L_REAR}
    for xc in (WB_F, WB_R):
        for dx in (-0.40, -0.371, -0.36, -0.33, -0.28, -0.20, -0.10, 0, 0.10, 0.20, 0.28, 0.33, 0.36, 0.371, 0.40): xs.add(round(xc + dx, 4))
    xs = sorted(xs, reverse=True)
    filled = [xs[0]]
    for x in xs[1:]:                                 # keep stations no more than ~0.16 m apart
        gap = filled[-1] - x
        k = int(math.ceil(gap / 0.16))
        for j in range(1, k): filled.append(filled[-1] - gap / k * 1 if j == 1 else filled[-1] - gap / k)
        filled.append(x)
    xs = filled
    mb = MB(); rings = []
    for x in xs:
        ring, cp = section(x); rings.append(([mb.add_v(p) for p in ring], cp))
    n = len(rings[0][0])
    hidx = lambda k: k if k < NH else 2 * (NH - 1) - k
    for (ra, _), (rb, _) in zip(rings, rings[1:]):          # crisp character line + bottom edge of the rocker
        for k in (5, n - 5, 1, n - 1):
            mb.sharp.append((ra[k], rb[k]))
    for ((ra, ca), (rb, cb)), ra_x, rb_x in zip(zip(rings, rings[1:]), xs, xs[1:]):
        for i in range(n):
            j = (i + 1) % n
            e = {hidx(i), hidx(j)}
            mat = "paint"
            if e <= {0, 1, 2} and min(ra_x, rb_x) < 1.98: mat = "black"
            if (ca or cb) and e <= {8, 9, 10, 11}: mat = "interior"
            mb.face((ra[i], rb[i], rb[j], ra[j]), mat)
    mb.face(rings[0][0][::-1], "paint"); mb.face(rings[-1][0], "paint")
    ob = mb.to_obj("S2000_Body", ["paint", "black", "interior"], coll)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

def bvh_of(ob):
    return BVHTree.FromPolygons([v.co.copy() for v in ob.data.vertices], [list(p.vertices) for p in ob.data.polygons])

def decal_rays(mb, bvh, fn, nu, nv, uvrect, mat="atlas", off=0.008, skirt=None):
    """Grid decal; fn(s,t) -> (origin, direction) of the ray that places grid point (s,t) on the body."""
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            s, t = i / nu, j / nv
            o, d = fn(s, t); o, d = Vector(o), Vector(d).normalized()
            hit, nrm, _, _ = bvh.ray_cast(o, d)
            if hit is None:
                hit, nrm, _, _ = bvh.find_nearest(o + d * 3)
            row.append((mb.add_v(hit + nrm * off), (uvrect[0] + (uvrect[2] - uvrect[0]) * s, uvrect[1] + (uvrect[3] - uvrect[1]) * t), d))
            if skirt: row[-1] = row[-1] + (mb.add_v(hit - nrm * .004),)
        grid.append(row)
    if skirt:   # side walls from the lens edge down into the body
        ring = [grid[0][i] for i in range(nu + 1)] + [grid[j][nu] for j in range(1, nv + 1)] + \
               [grid[nv][i] for i in range(nu - 1, -1, -1)] + [grid[j][0] for j in range(nv - 1, 0, -1)]
        for k in range(len(ring)):
            a, b = ring[k], ring[(k + 1) % len(ring)]
            mb.face((a[0], b[0], b[3], a[3]), skirt)
    for j in range(nv):
        for i in range(nu):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            idx = [e[0] for e in q]; uv = [e[1] for e in q]; d = q[0][2]
            nrm = (mb.v[idx[1]] - mb.v[idx[0]]).cross(mb.v[idx[3]] - mb.v[idx[0]])
            if nrm.dot(d) > 0: idx, uv = idx[::-1], uv[::-1]
            mb.face(idx, mat, uv)

def decal(mb, bvh, corners, direction, nu, nv, uvrect, mat="atlas", off=0.008):
    """Project a bilinear grid spanned by 4 corners (A,B,C,D) onto the body along `direction`."""
    A, B, C, D = map(Vector, corners); d = Vector(direction).normalized()
    decal_rays(mb, bvh, lambda s, t: (A.lerp(B, s).lerp(D.lerp(C, s), t) - d * 3, d), nu, nv, uvrect, mat, off)

def mir(pts): return [(x, -y, z) for x, y, z in pts]

def decal_rays_free(mb, fn, nu, nv, uvrect, mat="atlas"):
    """Free-floating textured grid: fn(s,t) -> (point + 3*dir, dir); point used directly."""
    ids = [[None] * (nu + 1) for _ in range(nv + 1)]; uvs = [[None] * (nu + 1) for _ in range(nv + 1)]
    for j in range(nv + 1):
        for i in range(nu + 1):
            sv, tv = i / nu, j / nv
            o, d = fn(sv, tv); p = Vector(o) - Vector(d).normalized() * 3 * 0 - Vector((3, 0, 0))
            ids[j][i] = mb.add_v(p)
            uvs[j][i] = (uvrect[0] + (uvrect[2] - uvrect[0]) * sv, uvrect[1] + (uvrect[3] - uvrect[1]) * tv)
    for j in range(nv):
        for i in range(nu):
            q = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            mb.face([ids[a][b] for a, b in q], mat, [uvs[a][b] for a, b in q])

def mirror_pod(mb, c, s, k=1.0):
    """Tapered aero mirror housing (narrow nose forward, glass on the back)."""
    N = 10   # rounded oval housing: small nose ring -> wide back ring, glass on the back
    ring = lambda dx, ry, rz: [c + Vector((dx, s * ry * math.cos(2 * math.pi * i / N), rz * math.sin(2 * math.pi * i / N))) * k
                               for i in range(N)]
    rings = [[mb.add_v(p) for p in ring(dx, ry, rz)] for dx, ry, rz in ((.045, .03, .018), (.01, .055, .035), (-.035, .053, .035))]
    tip = mb.add_v(c + Vector((.07 * k, 0, 0)))
    def fc(ids, mat):
        nr = (mb.v[ids[1]] - mb.v[ids[0]]).cross(mb.v[ids[2]] - mb.v[ids[0]])
        ctr = sum((mb.v[i] for i in ids), Vector()) / len(ids)
        mb.face(ids if nr.dot(ctr - (c + Vector((.01, 0, 0)))) >= 0 else ids[::-1], mat)
    for i in range(N):
        j = (i + 1) % N
        fc((tip, rings[0][i], rings[0][j]), "paint")
        for ra, rb in zip(rings, rings[1:]): fc((ra[i], ra[j], rb[j], rb[i]), "paint")
    bi = rings[-1]
    gl = [mb.add_v(mb.v[i] + Vector((-.004, 0, 0)) + (c - mb.v[i]) * .15) for i in bi]
    fc(bi, "paint"); fc(gl, "black")

def cut_side_intakes(coll, body, bvh):
    """Boolean a real recessed scoop into each flank, just ahead of the rear wheel, deepening toward the rear."""
    mb = MB()   # (v7: side intakes removed - not on the real car; only the front mouth is cut)
    # wide, rounded-corner lower front mouth
    MOUTH = []
    for (cy, cz, ang0) in ((.32, .39, 0), (-.32, .39, 90), (-.32, .31, 180), (.32, .31, 270)):
        for k in range(3):
            a = math.radians(ang0 + 45 * k)
            MOUTH.append((cy + .065 * math.cos(a), cz + .065 * math.sin(a)))
    outer, inner = [], []
    for y, z in MOUTH:
        hit, _, _, _ = bvh.ray_cast(Vector((3, y, z)), Vector((-1, 0, 0)))
        outer.append(mb.add_v((2.4, y, z))); inner.append(mb.add_v((hit.x - .07, y, z)))
    k = len(MOUTH)
    mb.face(outer[::-1], "paint"); mb.face(inner, "black")
    for i in range(k):
        j = (i + 1) % k
        mb.face((outer[i], outer[j], inner[j], inner[i]), "interior")
    cut = mb.to_obj("S2000_IntakeCutter", ["paint", "interior", "black"], coll)
    bm = bmesh.new(); bm.from_mesh(cut.data)
    bmesh.ops.triangulate(bm, faces=bm.faces); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(cut.data); bm.free()
    mod = body.modifiers.new("intake", 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut
    mod.solver = 'EXACT'; mod.material_mode = 'TRANSFER'
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
    body.modifiers.clear(); old = body.data; body.data = me; me.name = "S2000_Body"
    bpy.data.meshes.remove(old); bpy.data.objects.remove(cut)
    smooth_mesh(me, 38)

def build_fairings(coll):
    """Body-coloured humps behind each headrest that taper and flow into the rear deck."""
    mb = MB()
    secs = [(-0.815, .155, 1.04), (-0.92, .155, 1.03), (-1.07, .14, .995), (-1.22, .11, .97), (-1.35, .07, .955), (-1.45, .035, .948)]
    seg = 7
    for s in (1, -1):
        cy = s * .36; rings = []
        for x, hw, top in secs:
            base = bp_top(x) - .03
            rings.append([mb.add_v((x, cy + hw * math.cos(math.pi * k / seg), base + (top - base) * math.sin(math.pi * k / seg)))
                          for k in range(seg + 1)])
        for ra, rb in zip(rings, rings[1:]):
            for k in range(seg):
                mb.face((ra[k], ra[k + 1], rb[k + 1], rb[k]), "paint")
        mb.face(rings[0], "paint"); mb.face(rings[-1][::-1], "paint")
    ob = mb.to_obj("S2000_Fairings", ["paint"], coll, smooth=45)
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

def build_details(coll, body):
    bvh = bvh_of(body)
    lights = MB()
    for s in (1, -1):
        f = lambda pts: pts if s == 1 else mir(pts)[::-1]
        # headlights: big swept teardrop units on the nose corners, wide end outboard, tapering in/down
        NAVG = {}
        def head(sv, tv, s=s, NAVG=NAVG):
            # blueprint lens outline: inner/front tip (1.95, .41, .545-.565) sweeping back along the hood/fender edge
            # to the big outer end (1.56, .73, .60-.68); lower edge forward-outboard, upper edge rear-inboard
            cx, cy = 1.95 - .39 * sv, .41 + .32 * sv
            wid = .03 + .095 * min(1.0, sv * 1.6) ** .6
            o = (0.5 - tv) * wid
            zlo = .545 + .055 * sv ** 2.5; zhi = .565 + .115 * sv ** 0.6
            T = Vector((cx + o * .63, s * (cy + o * .77), zlo + (zhi - zlo) * tv))
            if s not in NAVG:   # one projection direction per lamp (avg surface normal) -> no folded lens grid
                acc = Vector()
                for a_, b_ in ((.2, .5), (.5, .5), (.8, .5), (.5, .1), (.5, .9)):
                    c_x, c_y = 1.95 - .39 * a_, .41 + .32 * a_
                    acc += bvh.find_nearest(Vector((c_x, s * c_y, .62)))[1]
                NAVG[s] = acc.normalized()
            n = NAVG[s]
            return T + n * .5, -n
        decal_rays(lights, bvh, head, 10, 4, UV_HEAD, off=.016, skirt="black")
        # taillights: wrap-around wedge, rays fanned around the rear corner (straight back -> side)
        # blueprint rear view: y .335-.74, z .66-.82, rounded outer end, inner end tapering low;
        # side view: wraps to x -1.71 with a raked leading edge. Path traced around the tail at lamp height.
        Q = Vector((-1.62, s * .30, .74)); path = []
        for k in range(0, 91, 2):
            a = math.radians(k); hit, _, _, _ = bvh.ray_cast(Q, Vector((-math.cos(a), s * math.sin(a), 0)))
            if hit is not None and abs(hit.y) >= .335 and hit.x <= -1.71: path.append(hit)
        cum = [0.0]
        for a_, b_ in zip(path, path[1:]): cum.append(cum[-1] + (b_ - a_).length)
        def tail(sv, tv, s=s, path=path, cum=cum, Q=Q):
            L = sv * cum[-1]; i = max(j for j in range(len(cum)) if cum[j] <= L + 1e-9); i = min(i, len(path) - 2)
            f = (L - cum[i]) / max(cum[i + 1] - cum[i], 1e-6); pt = path[i].lerp(path[i + 1], min(f, 1))
            ay = abs(pt.y)
            if ay < .74:
                zhi = lerp_keys([(.335, .70), (.37, .75), (.40, .78), (.46, .80), (.55, .815), (.80, .815)], ay)
                zlo = lerp_keys([(.335, .672), (.40, .664), (.55, .66), (.80, .658)], ay)
            else:
                zhi = lerp_keys([(-2.2, .816), (-1.71, .80)], pt.x)
                zlo = lerp_keys([(-2.2, .662), (-1.81, .664), (-1.76, .713), (-1.73, .744), (-1.71, .787)], pt.x)
            out = Vector((pt.x - Q.x, pt.y - Q.y, 0)).normalized()
            o = Vector((pt.x, pt.y, zlo + (zhi - zlo) * tv)) + out * .4
            return o, -out
        decal_rays(lights, bvh, tail, 12, 2, UV_TAILLENS, off=.010, skirt="black")
        # the twin round lamps (outer: double ring, inner: with a bar), as small raised discs on the lens
        for ly, uvr in ((.587, UV_LAMP_OUT), (.439, UV_LAMP_IN)):
            hit, n, _, _ = bvh.ray_cast(Vector((-3, s * ly, .736)), Vector((1, 0, 0)))
            t1 = n.cross(Vector((0, 0, 1))).normalized(); t2 = t1.cross(n).normalized()
            if t1.y < 0: t1 = -t1
            if t2.z < 0: t2 = -t2
            cu, cv = (uvr[0] + uvr[2]) / 2, (uvr[1] + uvr[3]) / 2; hu, hv = (uvr[2] - uvr[0]) / 2 * .94, (uvr[3] - uvr[1]) / 2 * .94
            ids, uvs = [], []
            for k in range(10):
                a = 2 * math.pi * k / 10
                ids.append(lights.add_v(hit + n * .017 + (t1 * math.cos(a) + t2 * math.sin(a)) * .062))
                uvs.append((cu + hu * math.cos(a), cv + hv * math.sin(a)))
            nr = (lights.v[ids[1]] - lights.v[ids[0]]).cross(lights.v[ids[2]] - lights.v[ids[0]])
            if nr.dot(n) < 0: ids, uvs = ids[::-1], uvs[::-1]
            lights.face(ids, "atlas", uvs)
        # turn signals in the bumper's outer corners + small side markers
        decal(lights, bvh, f([(2.1, .49, .29), (2.08, .64, .29), (2.08, .64, .35), (2.1, .49, .35)]), (-1, -.35 * s, 0), 2, 1, UV_AMBER, off=.006)
        decal(lights, bvh, f([(.84, 2, .605), (.755, 2, .605), (.755, 2, .63), (.84, 2, .63)]), (0, -s, 0), 1, 1, UV_AMBER, off=.005)
    # H badge on the nose tip
    decal(lights, bvh, [(2.12, -.04, .55), (2.12, .04, .55), (2.12, .04, .59), (2.12, -.04, .59)], (-1, 0, -.35), 1, 1, UV_BADGE, off=.006)
    # front plate above the mouth, rear plate in its recess, rear H + 'S2000' emblems
    xs_ = [bvh.ray_cast(Vector((3, yy, zz)), Vector((-1, 0, 0)))[0].x for yy in (-.16, 0, .16) for zz in (.425, .48, .535)]
    xp = max(xs_) + .006                                  # flat plate face just ahead of the most forward bumper point
    pz0, pz1, ph = .423, .537, .16
    pid = [lights.add_v(v) for v in ((xp, -ph, pz0), (xp, ph, pz0), (xp, ph, pz1), (xp, -ph, pz1))]
    lights.face(pid, "atlas", [(UV_PLATE[0], UV_PLATE[1]), (UV_PLATE[2], UV_PLATE[1]), (UV_PLATE[2], UV_PLATE[3]), (UV_PLATE[0], UV_PLATE[3])])
    bx0 = min(xs_) - .02
    lights.box(((xp - .003 + bx0) / 2, 0, (pz0 + pz1) / 2), ((xp - .003 - bx0) / 2, ph - .004, (pz1 - pz0) / 2 - .004), "black")
    decal(lights, bvh, [(-3, .19, .485), (-3, -.19, .485), (-3, -.19, .59), (-3, .19, .59)], (1, 0, 0), 2, 1, UV_PLATE, off=.012)
    decal(lights, bvh, [(-3, .03, .752), (-3, -.03, .752), (-3, -.03, .80), (-3, .03, .80)], (1, 0, 0), 1, 1, UV_BADGE, off=.006)
    decal(lights, bvh, [(-3, -.12, .70), (-3, -.29, .70), (-3, -.29, .735), (-3, -.12, .735)], (1, 0, 0), 2, 1, UV_S2000, off=.006)
    # grille mesh sitting inside the (boolean-cut) front mouth
    for y0, y1 in ((-.36, 0), (0, .36)):
        def gr(sv, tv, y0=y0, y1=y1):
            y = y0 + (y1 - y0) * sv; z = .26 + .17 * tv
            hit, _, _, _ = bvh.ray_cast(Vector((3, y, z)), Vector((-1, 0, 0)))
            return Vector((hit.x - .05 + 3, y, z)), Vector((-1, 0, 0))
        grid_mb = lights
        decal_rays_free(grid_mb, gr, 3, 1, UV_GRILLE)
    lights_ob = lights.to_obj("S2000_Lights", ["atlas", "black"], coll)

    trim = MB()
    for s in (1, -1):
        f = lambda pts: pts if s == 1 else mir(pts)[::-1]
        # door shut lines
        pass   # (v8: door shut lines are painted into the body texture from the blueprint)
        # hood shut line around the headlight tops
        # trunk shut line just ahead of the ducktail
    # licence plate recess in the bumper, black lower valance/diffuser band
    decal(trim, bvh, [(-3, .25, .47), (-3, -.25, .47), (-3, -.25, .60), (-3, .25, .60)], (1, 0, 0), 1, 1, (0, 0, 0, 0), mat="black")
    decal(trim, bvh, [(-3, .58, .405), (-3, -.58, .405), (-3, -.58, .44), (-3, .58, .44)], (1, 0, 0), 2, 1, (0, 0, 0, 0), mat="black")
    # diffuser fins under the tail
    for yf in (-.42, -.14, .14, .42):
        trim.box((-2.0, yf, .31), (.06, .012, .04), "black")
    # exhaust tips
    cyl(trim, (-2.0, .42, .30), .045, .10, 8, "silver", axis='x')
    cyl(trim, (-2.0, -.42, .30), .045, .10, 8, "silver", axis='x')
    # wheel-well liners (hide see-through under the arches)
    for xc in (WB_F, WB_R):
        trim.box((xc, 0, .44), (ARCH_R, .60, .245), "black")
    # mirrors: small aero body-coloured pods on the door, just behind the A-pillar base
    for s in (1, -1):
        trim.beam((0.20, s * .75, .89), (0.14, s * .80, .935), .025, "paint")
        mirror_pod(trim, Vector((0.10, s * .835, .945)), s, k=1.25)
    trim_ob = trim.to_obj("S2000_Trim", ["black", "silver", "paint"], coll, smooth=40)

    # windshield
    glass = MB()
    # raked, modest-height screen; narrower at the top with chamfered upper corners
    bl, br = (0.50, .69, .885), (0.50, -.69, .885)
    tl1, tr1 = (WS_TOP_X + .045, .565, 1.205), (WS_TOP_X + .045, -.565, 1.205)
    tl2, tr2 = (WS_TOP_X + .02, .47, 1.24), (WS_TOP_X + .02, -.47, 1.24)
    ids = [glass.add_v(p) for p in (bl, br, tr1, tr2, tl2, tl1)]
    glass.face(ids, "glass")
    glass_ob = glass.to_obj("S2000_Windshield", ["glass"], coll)
    frame = MB()
    frame.beam(bl, tl1, .035, "black"); frame.beam(br, tr1, .035, "black")
    dn = Vector((0.006, 0, -0.012))   # header pieces sit just below the glass top edge, tucked under the soft-top lip
    frame.beam(Vector(tl1) + dn, Vector(tl2) + dn, .02, "black"); frame.beam(Vector(tr1) + dn, Vector(tr2) + dn, .02, "black")
    frame.beam(Vector(tl2) + dn, Vector(tr2) + dn, .02, "black")
    frame.beam(bl, br, .03, "black")

    # (v10: no interior - the raised soft top and opaque glass close the cabin)
    cockpit_ob = frame.to_obj("S2000_WindshieldFrame", ["black"], coll, smooth=40)
    cut_side_intakes(coll, body, bvh)
    return [lights_ob, trim_ob, glass_ob, cockpit_ob]

def cyl(mb, c, r, length, sides, mat, axis='y', tilt=0.0, cap_mat=None, cap_uv=None, outer_sign=1):
    c = Vector(c)
    if axis == 'y':
        R = Matrix.Identity(3)
    else:  # axis x
        R = Matrix.Rotation(-math.pi / 2, 3, 'Z')
    R = Matrix.Rotation(tilt, 3, 'Y') @ R
    rings = []
    for side in (-1, 1):
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides + math.pi / sides
            ring.append(mb.add_v(c + R @ Vector((r * math.cos(a), side * length / 2, r * math.sin(a)))))
        rings.append(ring)
    for k in range(sides):
        j = (k + 1) % sides
        mb.face((rings[0][k], rings[0][j], rings[1][j], rings[1][k]), mat)
    for si, ring in enumerate(rings):
        side = (-1, 1)[si]
        is_outer = side == outer_sign
        uvs = None; m = mat
        if is_outer and cap_mat:
            m = cap_mat
            uvs = []
            for k in range(sides):
                a = 2 * math.pi * k / sides + math.pi / sides
                cu, cv = (cap_uv[0] + cap_uv[2]) / 2, (cap_uv[1] + cap_uv[3]) / 2
                hu = (cap_uv[2] - cap_uv[0]) / 2 * 0.98
                uvs.append((cu - hu * math.cos(a) * side, cv + hu * math.sin(a)))
        idx = ring if side == 1 else ring[::-1]
        if uvs and side != 1: uvs = uvs[::-1]
        mb.face(idx, m, uvs)

def build_softtop(coll, body):
    """Stock S2000 soft top, raised: black fabric, flat roof with bows, small rear window, quarter panels down to
    the shoulder behind the doors, rear edge sitting on the deck just ahead of the trunk lid.
    Roofline = blueprint side silhouette (bp_sil); plan outline + rear window from the blueprint top view."""
    bvh = bvh_of(body)
    def body_z(x, y):
        hit, _, _, _ = bvh.ray_cast(Vector((x, y, 3)), Vector((0, 0, -1)))
        return hit.z if hit else bp_top(x)
    def zc_of(x):   # centre-line roof height (blueprint silhouette), header blended onto the windshield top
        if x >= -0.10: return 1.243 + (bp_sil(-0.10) - .004 - 1.243) * (0.03 - x) / 0.13
        return bp_sil(x) - .004
    ye_of = lambda x: lerp_keys([(0.03, .555), (0.0, .565), (-0.30, .60), (-0.70, .62), (-1.0, .64), (-1.37, .655)], x)
    qline = lambda x: lerp_keys([(-0.80, 1.214), (-1.28, .913)], x)      # quarter-panel trailing edge (side view)
    def dx_of(y):    # rear-edge plan curvature: centre at x -1.37, corners pulled forward
        return .09 * (y / .655) ** 2 if y <= .655 else .09 + (y - .655) / .065 * .15
    YS = .72         # quarter panels land on the body just inboard of the shoulder (top view)
    ROWS = [(0.03, 0), (0.0, 0), (-0.13, 0), (-0.26, 0), (-0.39, 1), (-0.54, 0), (-0.69, 1), (-0.72, 1), (-0.82, 1),
            (-0.91, 0), (-1.00, 0), (-1.10, 0), (-1.20, 0), (-1.29, 0), (-1.37, 0)]
    mb = MB(); rows = []
    for ri, (xc, bow) in enumerate(ROWS):
        w = min(1, max(0, (-xc - 1.0) / 0.37)); last = ri == len(ROWS) - 1
        zc = zc_of(xc) - (0 if bow or xc > -0.05 or xc < -0.75 else .005)   # fabric sags a touch between bows
        ye = ye_of(xc); ze = zc - .045
        quarter = xc < -0.70
        if quarter and xc <= -0.80: ze = min(ze, qline(xc))
        half = [(0, zc, .5), (.22, zc - .03 * (.22 / ye) ** 2, .5 + .3 * .22 / ye), (.42, zc - .03 * (.42 / ye) ** 2, .5 + .3 * .42 / ye),
                (ye - .05, max(ze + .02, zc - .03 * ((ye - .05) / ye) ** 2 - .006), .5 + .3 * (ye - .05) / ye), (ye, ze, .8)]
        if quarter:
            half += [((ye + YS) / 2 + .015, None, .9), (YS, None, 1.0)]
        else:
            half += [(ye - .004, ze - .025, .86), (ye - .014, ze - .04, .9)]
        pts = []
        for k, (y, z, vv) in enumerate(half):
            x = xc + w * dx_of(y)
            if z is None:   # quarter panel: mid point bulges slightly, bottom tucks into the body shoulder
                zb = body_z(x, YS)
                z = zb - .004 if k == len(half) - 1 else (ze + zb) / 2 + .015
            zfloor = body_z(x, y) + .006
            z = zfloor if last else max(z, zfloor)
            pts.append((x, y, z, (0.03 - x) / 1.40, vv))
        full = [(x, y, z, u, vv) for x, y, z, u, vv in pts[::-1]] + [(x, -y, z, u, 1 - vv) for x, y, z, u, vv in pts[1:]]
        rows.append([(mb.add_v((x, y, z)), (u, 1 - vv)) for x, y, z, u, vv in full])
    m = len(rows[0]); mid = m // 2
    for ra, rb in zip(rows, rows[1:]):
        for k in range(m - 1):
            q = (ra[k], rb[k], rb[k + 1], ra[k + 1])
            mb.face([e[0] for e in q], "softtop", [e[1] for e in q])
        for k in (mid - 4, mid + 4):          # crisp roof-edge seam line
            mb.sharp.append((ra[k][0], rb[k][0]))
    # front lip turned down over the windshield header (clean frame, no separate bar)
    fr = rows[0]
    lip = [mb.add_v(mb.v[i] + Vector((.012, 0, -.018))) for i, _ in fr]
    for k in range(m - 1):
        mb.face((lip[k], fr[k][0], fr[k + 1][0], lip[k + 1]), "softtop", [(0.0, fr[k][1][1]), (0.004, fr[k][1][1]), (0.004, fr[k + 1][1][1]), (0.0, fr[k + 1][1][1])])
    # dark door-window glass in the apertures (A-pillar -> B line at x -0.70)
    for s in (1, -1):
        ring, _ = section(0.50); _, yf, zf = ring[7]
        ring, _ = section(-0.70); _, yr, zr = ring[7]
        q = [(0.50, s * (yf - .07), zf - .05), (-0.70, s * (yr - .05), zr - .05), (-0.70, s * (ye_of(-0.70) - .016), zc_of(-0.70) - .09),
             (-0.64, s * (ye_of(-0.64) - .015), zc_of(-0.64) - .085), (WS_TOP_X + .05, s * .553, 1.19)]
        ids = [mb.add_v(v) for v in q]
        mb.face(ids if s == 1 else ids[::-1], "glass")
    ob = mb.to_obj("S2000_SoftTop", ["softtop", "glass", "black"], coll, smooth=40)
    # small rear window (rounded trapezoid, wider at the rear as in the blueprint top view): thin black rubber
    # surround, opaque dark-tinted glass
    tb = bvh_of(ob)
    x0w, x1w, hf, hr, rc = -0.90, -1.31, .45, .49, .055
    corners = [(x0w - rc, -hf + rc, -90), (x0w - rc, hf - rc, 0), (x1w + rc, hr - rc, 90), (x1w + rc, -hr + rc, 180)]
    outline = []
    for cx, cy, a0 in corners:
        for k in range(4):
            a = math.radians(a0 + 30 * k); outline.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    cxm = sum(p_[0] for p_ in outline) / len(outline)
    def onsurf(x, y):
        hit, n, _, _ = tb.ray_cast(Vector((x, y, 3)), Vector((0, 0, -1)))
        if n.z < 0: n = -n
        return hit, n
    wb = MB(); outer, top, inner = [], [], []
    for x, y in outline:
        h, n = onsurf(x, y); outer.append(wb.add_v(h + n * .002))
        h2, n2 = onsurf(x + (cxm - x) * .05, y * .95); top.append(wb.add_v(h2 + n2 * .009))
        h3, n3 = onsurf(x + (cxm - x) * .09, y * .91); inner.append(wb.add_v(h3 + n3 * .006))
    gn = (wb.v[inner[1]] - wb.v[inner[0]]).cross(wb.v[inner[2]] - wb.v[inner[0]])
    if gn.z < 0: outer, top, inner = outer[::-1], top[::-1], inner[::-1]
    k = len(outline)
    for i in range(k):
        j = (i + 1) % k
        wb.face((outer[i], outer[j], top[j], top[i]), "black"); wb.face((top[i], top[j], inner[j], inner[i]), "black")
    # glass as concentric rings re-projected onto the (curved) top, so the fabric never pokes through the chords
    cg = sum((wb.v[i] for i in inner), Vector()) / k
    prev = inner
    for f_ in (.66, .33):
        ring_ = []
        for i in inner:
            q_ = cg.lerp(wb.v[i], f_); h_, n_ = onsurf(q_.x, q_.y); ring_.append(wb.add_v(h_ + n_ * .006))
        for i in range(k):
            j = (i + 1) % k; wb.face((prev[i], prev[j], ring_[j], ring_[i]), "glass_rear")
        prev = ring_
    hc, nc = onsurf(cg.x, cg.y); ci = wb.add_v(hc + nc * .006)
    for i in range(k): wb.face((prev[i], prev[(i + 1) % k], ci), "glass_rear")
    wme = wb.to_obj("ST_Window", ["black", "glass_rear"], coll, smooth=30)
    bpy.ops.object.select_all(action='DESELECT'); wme.select_set(True); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.join()
    return ob

def build_wheels(coll):
    obs = []
    for name, x, s in (("FL", WB_F, 1), ("FR", WB_F, -1), ("RL", WB_R, 1), ("RR", WB_R, -1)):
        mb = MB()
        cyl(mb, (0, 0, 0), TIRE_R / math.cos(math.pi / 10), TIRE_W, 10, "tire", cap_mat="atlas", cap_uv=UV_WHEEL, outer_sign=s)
        ob = mb.to_obj("S2000_Wheel_" + name, ["tire", "atlas"], coll, smooth=40)   # round sidewalls, crisp rim face
        ob.location = (x, s * (TRACK_F if x > 0 else TRACK_R), TIRE_R)
        obs.append(ob)
    return obs

# ---------------------------------------------------------------- body texture (512, UV unwrapped, panel lines from the blueprint)
BODY_TS = 1024
def texture_body(body):
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # baked ambient occlusion (crevices, arches, under the soft top / lamps / mirrors), multiplied in by make_body.py
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
    if sc.world is None: sc.world = bpy.data.worlds.new("BakeWorld")
    sc.world.light_settings.distance = 0.30
    ao_img = bpy.data.images.new("S2000_AO", BODY_TS, BODY_TS, alpha=False)
    tmp = []
    for sl in body.material_slots:
        nt_ = sl.material.node_tree; n_ = nt_.nodes.new("ShaderNodeTexImage"); n_.image = ao_img
        nt_.nodes.active = n_; tmp.append((nt_, n_))
    sc.render.bake.margin = 16; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='AO', use_clear=True)
    ao_png = os.path.join(OUT, "tex", "body_ao.png"); ao_img.filepath_raw = ao_png; ao_img.file_format = 'PNG'; ao_img.save()
    for nt_, n_ in tmp: nt_.nodes.remove(n_)
    bpy.data.images.remove(ao_img)
    me = body.data; me.calc_loop_triangles(); uvd = me.uv_layers.active.data; TS = BODY_TS
    pos = np.zeros((TS, TS, 3), np.float32); nrm = np.zeros((TS, TS, 3), np.float32); mask = np.full((TS, TS), -1, np.int16)
    cn = me.corner_normals
    for lt in me.loop_triangles:
        uv = np.array([uvd[l].uv[:] for l in lt.loops]) * TS - 0.5
        Pv = np.array([me.vertices[v].co[:] for v in lt.vertices]); Nv = np.array([cn[l].vector[:] for l in lt.loops])
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, TS - 1), min(y1, TS - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        (ax, ay), (bx, by), (cx_, cy_) = uv
        den = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
        if abs(den) < 1e-12: continue
        l0 = ((by - cy_) * (gx - cx_) + (cx_ - bx) * (gy - cy_)) / den
        l1 = ((cy_ - ay) * (gx - cx_) + (ax - cx_) * (gy - cy_)) / den
        l2 = 1 - l0 - l1
        ins = (l0 >= -.02) & (l1 >= -.02) & (l2 >= -.02)
        if not ins.any(): continue
        L = np.stack([l0[ins], l1[ins], l2[ins]], 1)
        ry, rx = gy[ins], gx[ins]
        pos[ry, rx] = L @ Pv; nn = L @ Nv; nrm[ry, rx] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
        mask[ry, rx] = lt.material_index
    npz = os.path.join(OUT, "tex", "body_texels.npz"); np.savez_compressed(npz, pos=pos, nrm=nrm, mask=mask)
    png = os.path.join(OUT, "s2000_body.png")
    subprocess.run([PY3, os.path.join(OUT, "tex", "make_body.py"), npz, png, ao_png], check=True)
    img = bpy.data.images.load(png, check_existing=False); img.name = "S2000_BodyTex"
    pm = M["paint"].copy(); pm.name = "S2000_Paint_Body"; nt = pm.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = 'Linear'
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    for i, sl in enumerate(body.material_slots):
        if sl.material == M["paint"]: body.material_slots[i].material = pm

# ---------------------------------------------------------------- assemble
coll = bpy.data.collections.new("S2000"); bpy.context.scene.collection.children.link(coll)
root = bpy.data.objects.new("S2000_Root", None); coll.objects.link(root)
body = build_body(coll)
parts = [body] + build_details(coll, body) + [build_softtop(coll, body)]
for ob in parts: ob.data.transform(Matrix.Translation((0, 0, -RIDE_DROP)))   # lower the whole car body
parts += build_wheels(coll)
texture_body(body)   # after everything exists: the AO bake sees soft top, trim and wheels
for ob in parts: ob.parent = root

dg = bpy.context.evaluated_depsgraph_get()
tris = 0
for ob in parts:
    tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
print(f"S2000_TRIANGLES {tris}")

# ---------------------------------------------------------------- export
if "--no-export" not in ARGS:
    sc = bpy.context.scene
    # blueprint reference planes (viewport only, not rendered / exported), images packed into the .blend
    import json as _json
    PL = _json.load(open(os.path.join(OUT, "bp", "planes.json")))
    bcol = bpy.data.collections.new("Blueprint"); sc.collection.children.link(bcol)
    for key, d in PL.items():
        img = bpy.data.images.load(os.path.join(OUT, "ref", f"bp_{key}.png")); img.pack()
        m = bpy.data.materials.new("BP_" + key); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
        em = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(tex.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], o.inputs["Surface"])
        if d["axis"] == "side":
            V = [(d["x0"], -2.5, d["z0"]), (d["x1"], -2.5, d["z0"]), (d["x1"], -2.5, d["z1"]), (d["x0"], -2.5, d["z1"])]
        elif d["axis"] == "top":
            V = [(d["xb"], d["ya"], -0.05), (d["xb"], d["yb"], -0.05), (d["xa"], d["yb"], -0.05), (d["xa"], d["ya"], -0.05)]
        else:
            xp = -3.5 if d["axis"] == "front" else 3.5
            V = [(xp, d["ya"], d["z0"]), (xp, d["yb"], d["z0"]), (xp, d["yb"], d["z1"]), (xp, d["ya"], d["z1"])]
        me = bpy.data.meshes.new("BP_" + key); me.from_pydata(V, [], [(0, 1, 2, 3)])
        uvl = me.uv_layers.new(); 
        for li, uv in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))): uvl.data[li].uv = uv
        me.materials.append(m)
        ob = bpy.data.objects.new("Blueprint_" + key, me); bcol.objects.link(ob); ob.hide_render = True; ob.hide_select = True
    for im_ in bpy.data.images:
        if im_.source == 'FILE' and im_.packed_file is None:
            try: im_.pack()
            except Exception: pass
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "s2000_lowpoly.blend"))
    for ob in bpy.data.objects: ob.select_set(ob.name.startswith("S2000"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "s2000_lowpoly.glb"), export_format='GLB', use_selection=True)
    bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "s2000_lowpoly.obj"), export_selected_objects=True,
                          export_materials=True, path_mode='COPY', forward_axis='NEGATIVE_Z', up_axis='Y')
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "s2000_lowpoly.fbx"), use_selection=True,
                             path_mode='COPY', embed_textures=True)

# ---------------------------------------------------------------- render
if "--no-render" not in ARGS:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    # vertical gradient sky
    nt = world.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (*srgb((0.55, 0.57, 0.62)), 1)
    ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (*srgb((0.80, 0.84, 0.90)), 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
    gm = make_mat("Ground", (0.42, 0.43, 0.45), 0.9)
    bpy.ops.mesh.primitive_plane_add(size=40); gp = bpy.context.object; gp.name = "Ground"; gp.data.materials.append(gm)
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.data.angle = 0.1; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(-30))
    tgt = bpy.data.objects.new("CamTarget", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.55)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    views = {
        "front34": ((6.9, 2.7, 1.8), 45),
        "rear34": ((-5.4, -4.0, 1.6), 45),
        "side": ((0.0, 9.0, 0.75), 45),
        "top": ((0.0, 0.01, 11.0), 45),
        "front": ((9.0, 0.0, 0.62), 50),
    }
    def set_view(name):
        loc, lens = views[name]
        cam.location = loc; cam.data.lens = lens
        if name == "side": cam.data.type = 'ORTHO'; cam.data.ortho_scale = 5.0
        elif name in ("top", "front"): cam.data.type = 'ORTHO'; cam.data.ortho_scale = 5.0 if name == "top" else 2.45
        else: cam.data.type = 'PERSP'
    def upscale_bilinear(src, dst, k=1.5):
        """PS2-style: render low-res, then a soft bilinear upscale (like a TV/upscaler would)."""
        im = bpy.data.images.load(src); w, h = im.size
        px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)
        W, H = int(w * k), int(h * k)
        ys = np.clip((np.arange(H) + .5) / k - .5, 0, h - 1); xs = np.clip((np.arange(W) + .5) / k - .5, 0, w - 1)
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int); y1 = np.minimum(y0 + 1, h - 1); x1 = np.minimum(x0 + 1, w - 1)
        fy = (ys - y0)[:, None, None]; fx = (xs - x0)[None, :, None]
        top = px[y0][:, x0] * (1 - fx) + px[y0][:, x1] * fx; bot = px[y1][:, x0] * (1 - fx) + px[y1][:, x1] * fx
        big = top * (1 - fy) + bot * fy
        out = bpy.data.images.new("up", W, H, alpha=True)
        out.pixels.foreach_set(big.astype(np.float32).ravel()); out.filepath_raw = dst; out.file_format = 'PNG'; out.save()
        bpy.data.images.remove(im); bpy.data.images.remove(out)
    if "--compare" in ARGS:
        # orthographic silhouettes at 4 mm/px for blueprint overlay (composited by bp/compare.py)
        gp.hide_render = True; sc.render.film_transparent = True; sc.cycles.samples = 12; sc.render.filter_size = 0.8
        cam.constraints.clear(); cam.data.type = 'ORTHO'
        CV = {  # name: (location, rotation, ortho scale, res x, res y)
            "side": ((0, 9, .70), (math.pi / 2, 0, math.pi), 4.6, 1150, 375),
            "top": ((0, 0, 9), (0, 0, math.pi / 2), 4.6, 550, 1150),
            "front": ((9, 0, .70), (math.pi / 2, 0, math.pi / 2), 2.2, 550, 375),
            "rear": ((-9, 0, .70), (math.pi / 2, 0, -math.pi / 2), 2.2, 550, 375)}
        for tag in ("",):
            for name, (loc, rot, osc, rx, ry) in CV.items():
                cam.location = loc; cam.rotation_euler = rot; cam.data.ortho_scale = osc
                sc.render.resolution_x, sc.render.resolution_y = rx, ry
                sc.render.filepath = os.path.join(RDIR, f"cmp_{name}{tag}.png"); bpy.ops.render.render(write_still=True)
        raise SystemExit(0)
    for name in views:
        set_view(name)
        sc.render.resolution_x, sc.render.resolution_y = 640, 480
        sc.render.filter_size = 0.6; sc.cycles.samples = 32
        p = os.path.join(RDIR, f"s2000_{name}_640.png"); sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        upscale_bilinear(p, os.path.join(RDIR, f"s2000_{name}_ps2.png"))
        os.remove(p)
    if "--clean" in ARGS:
        sc.render.resolution_x, sc.render.resolution_y = 1280, 960; sc.render.filter_size = 1.5; sc.cycles.samples = 64
        for name, fn in (("front34", "s2000_front34_clean_1280.png"), ("rear34", "s2000_rear34_clean_1280.png"),
                         ("side", "s2000_side_clean_1280.png"), ("front", "s2000_front_clean_1280.png")):
            set_view(name); sc.render.filepath = os.path.join(RDIR, fn)
            bpy.ops.render.render(write_still=True)
        # texture close-ups (neutral light)
        for fn, loc, tg, lens in (("s2000_closeup_front_tex.png", (3.3, 1.75, 1.05), (1.80, 0.40, 0.55), 55),
                                  ("s2000_closeup_rear_tex.png", (-3.5, -2.3, 0.95), (-1.62, -0.55, 0.55), 50),
                                  ("s2000_closeup_softtop.png", (-3.0, 2.6, 2.0), (-0.75, 0.0, 1.0), 45)):
            cam.data.type = 'PERSP'; cam.location = loc; cam.data.lens = lens; tgt.location = tg
            sc.render.filepath = os.path.join(RDIR, fn); bpy.ops.render.render(write_still=True)
        tgt.location = (0, 0, 0.55)
