"""Headless WRX STI grey-clay build (blueprint-only).  Full pipeline (run from art/vehicles/wrx_sti):
  python3 bp/extract.py && python3 bp/classify_sheet.py && python3 bp/fair.py   # trace, classification sheet, faired curves
  blender -b -P build_wrx.py -- [--render]                          # this file: clay + rig + exports (+ renders)
  python3 bp/bpcompare.py && python3 bp/feature_overlay.py && python3 bp/deliver.py && python3 bp/keylines.py
or simply:  python3 make_all.py
Objects: WRX_Body / WRX_Cabin (blueprint lofts), base-car parts from the blueprint (WRX_Scoop, WRX_LipSpoiler),
STI stock parts (STI_Scoop, STI_Wing, STI_FrontLip, each <= 300 tris), mirrors, wheel-well liners, underbody, wheels.
Rig (Godot VehicleBody3D / VehicleWheel3D compatible): WRX-vehicle (root, ground origin)
  +- WRX_Body (+ all body parts as children; Blender-only roll / pitch / heave poses)
  +- Hub_FL-wheel ... Hub_RR-wheel  (empties at the static hub centre = Godot VehicleWheel3D nodes)
       +- Steer_FL / Steer_FR (front only, rotates about local Z = vertical axis through the hub; Blender authoring)
            +- WRX_Wheel_FL (mesh, origin at the hub, spins about local X = axle)
Writes wrx_clay.blend, wrx_clay.glb, tri_count.txt, bp/tris_carframe.npy (+ tris_material.npy, tris_object.npy)."""
import bpy, bmesh, sys, os, math, importlib
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'parts'))
os.chdir(HERE)
import numpy as np
import wrx_bp as B, wrx_geo as G, wrx_masks as MK, wrx_decals as DC
for m in (B, G, MK, DC): importlib.reload(m)

# ---------------- suspension / steering spec (estimates documented in README.md) ----------------
BUMP, DROOP = 0.065, 0.080        # wheel travel relative to the body from static ride height (m)
LOCK = 30.0                       # steering lock, degrees each way (front wheels, vertical axis through the hub)
ROLL = 3.0                        # pose-sheet body roll (deg)
LINER_R_F, LINER_R_R = 0.415, 0.400
LINER_YIN_F, LINER_YIN_R = 0.465, 0.590

def to_bl(p): return Vector((p[1], -p[0], p[2]))      # car (x fwd, y left, z) -> Blender (X left, Y = -fwd, Z)
def reset(): bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1); return m
def obj_from_bm(name, bm, mats, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    if parent is not None: ob.parent = parent
    return ob
def smooth(ob, angle=38):
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle), keep_sharp_edges=True); ob.select_set(False)
def empty(name, loc, parent=None, size=0.12, kind='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    bpy.context.collection.objects.link(e); e.parent = parent; e.location = loc; return e

# ---------------- face classification from the blueprint views ----------------
def classify(c, n, region):
    """c, n: car-frame centre / normal.  region: 'lower' or 'cabin'.  returns material index
    0 clay, 1 glass, 2 under, 3 lamp, 4 trim."""
    v = MK.view_of(n); p = (c[0], c[1], c[2])
    if region == 'cabin':
        return 0      # cabin faces are classified by strip + blueprint glass regions in build_cabin
    if v == 'side':
        if MK.hit('side', 'HL', p) or MK.hit('side', 'R', p): return 3
    elif v == 'front':
        if MK.hit('front', 'LL', p): return 3
        if abs(c[1]) < 0.42 and 0.25 < c[2] < 0.66 and MK.hit('front', 'K', p): return 4   # grille oval + lower intake
    elif v == 'rear':
        if MK.hit('rear', 'R', p): return 3
        if abs(c[1]) < 0.62 and c[2] < 0.40 and MK.hit('rear', 'K', p): return 4         # lower valance / exhaust
    elif v == 'top':
        if MK.hit('top', 'R', p): return 3
    return 0

def loft(bm, secs, X, closed_bottom=False):
    """secs: list of (NP,2) half sections at stations X -> mirrored grid of verts; returns (verts grid, faces)."""
    S_ = len(X); NPn = secs[0].shape[0]; C = 2 * NPn - 1
    vv = []
    for s in range(S_):
        row = [None] * C
        for i in range(NPn):
            y, z = secs[s][i]
            row[i] = bm.verts.new(to_bl((X[s], y, z)))
            if i < NPn - 1: row[C - 1 - i] = bm.verts.new(to_bl((X[s], -y, z)))
        vv.append(row)
    F = []
    for s in range(S_ - 1):
        for c in range(C - 1):
            q = (vv[s][c], vv[s + 1][c], vv[s + 1][c + 1], vv[s][c + 1])
            if len(set(q)) < 4: continue
            try: F.append((bm.faces.new(q), s, c))
            except ValueError: pass
    return vv, F

def car(v):  # blender co -> car frame
    return np.array([-v.y, v.x, v.z])

QC = {}
def face_check(bm, faces):
    """pass 2 shading QC on the loft quads: flipped (normal points inward vs the section side), skewed / non-planar
    quads (max corner-normal deviation), degenerate faces, and the spread of station spacing."""
    flipped = skew = degen = 0; worst = 0.0; where = []
    for f in faces:
        if f.calc_area() < 1e-7: degen += 1; continue
        c = car(f.calc_center_median()); n = f.normal; nc = np.array([-n.y, n.x, n.z])
        if abs(c[1]) > 0.05 and abs(nc[1]) > 0.3 and np.sign(nc[1]) != np.sign(c[1]): flipped += 1
        if len(f.verts) == 4:   # non-planarity: 4th corner's distance from the plane of the other three / diagonal
            p = [v.co for v in f.verts]; nn = (p[1] - p[0]).cross(p[2] - p[0])
            if nn.length < 1e-12: continue
            dev = 100 * abs((p[3] - p[0]).dot(nn.normalized())) / max((p[2] - p[0]).length, (p[3] - p[1]).length)
            worst = max(worst, dev); skew += dev > 5
            if dev > 5: where.append((round(dev, 1), [round(float(v), 3) for v in c]))
    return dict(faces=len(faces), flipped=flipped, degenerate=degen, nonplanar_gt5pct=int(skew), worst_nonplanar_pct=round(worst, 1), worst_at=sorted(where, reverse=True)[:8])

def build_body(M, root):
    X = G.stations(); secs = [G.lower_section(x) for x in X]
    bm = bmesh.new(); vv, F = loft(bm, secs, X)
    C = len(vv[0]); S_ = len(X)
    # bottom plates between left/right p0 where the station is not over a wheel arch
    # floor plates only in the overhangs (bumper bottoms are drawn in the front / rear views; the floor between the
    # axles is not -- the sills hide behind the tyres there, WRX_Under closes the bottom from z .30)
    for s in range(S_ - 1):
        if not (min(X[s], X[s + 1]) > B.ARCH_F['x1'] or max(X[s], X[s + 1]) < B.ARCH_R['x0']): continue
        F.append((bm.faces.new((vv[s][0], vv[s][C - 1], vv[s + 1][C - 1], vv[s + 1][0])), s, -1))
    # nose / tail caps
    for s, rev in ((0, False), (S_ - 1, True)):
        ring = vv[s][:] ; ring = ring[::-1] if rev else ring
        f = bm.faces.new(ring); F.append((f, s, -2))
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _, _ in F])
    for f, s, c in F:
        f.material_index = 2 if c == -1 else 0     # lamps / grille are blueprint-outline decals (build_decals)
    # crisp intended edges: shoulder line (p7 side top) over hood / deck, rocker (p1)
    def mark(i, s0, s1):
        for cc_ in (i, C - 1 - i):
            for s_ in range(s0, s1):
                e = bm.edges.get((vv[s_][cc_], vv[s_ + 1][cc_]))
                if e: e.smooth = False
    idx = lambda x: int(np.argmin(np.abs(X - x)))
    mark(7, idx(2.0), idx(G.XWS)); mark(7, idx(G.XRG), idx(-2.06)); mark(1, idx(0.85), idx(-0.86))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    QC['body'] = face_check(bm, [f for f, s, c in F if c >= 0 and f.is_valid])
    ob = obj_from_bm('WRX_Body', bm, [M['clay'], M['glass'], M['under'], M['lamp'], M['trim']], root); smooth(ob, 45); return ob

def build_cabin(M, body):
    X = G.cabin_stations(); secs = [G.cabin_section(x) for x in X]
    bm = bmesh.new(); vv, F = loft(bm, secs, X)
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _, _ in F])
    # strips: column c of the mirrored grid -> section strip i (0 base-belt, 1-2 side glass band, 3 pillar / roof rail,
    # 4-5 roof).  Glass = blueprint glass regions: side view (door glass, windshield wrap, rear-glass wrap) for the
    # side band, top view (windshield x .28-.92, rear glass x -1.07..-1.57) for the upper strips; the black B-pillar and
    # the rear-door sash triangle are the gaps between the side-view glass regions.
    NPn = secs[0].shape[0]; C_ = 2 * NPn - 1
    GLS = B.GLASS; tws = [r for r in B.D['top_glass_regions'] if r['n'] > 5000]
    def in_x(x, r, m=0.0): return r['x'][0] - m <= x <= r['x'][1] + m
    for f, s, c in F:
        i = c if c < NPn - 1 else C_ - 2 - c
        cc = car(f.calc_center_median()); x = cc[0]
        m = 0
        if i in (1, 2):
            if any(in_x(x, GLS[k]) for k in GLS): m = 1
            elif 'front_door' in GLS and 'rear_door' in GLS and GLS['rear_door']['x'][1] < x < GLS['front_door']['x'][0]: m = 4
            elif 'rear_door' in GLS and 'rear_glass' in GLS and GLS['rear_glass']['x'][1] < x < GLS['rear_door']['x'][0]: m = 4
        elif i >= 4 or (i == 3 and x > 0.6):
            if any(in_x(x, r, -0.02) for r in tws): m = 1
        f.material_index = m
    C = len(vv[0])
    for i in (3, 4):        # glass top / roof rail crease
        for cc_ in (i, C - 1 - i):
            for s_ in range(len(X) - 1):
                e = bm.edges.get((vv[s_][cc_], vv[s_ + 1][cc_]))
                if e: e.smooth = False
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    QC['cabin'] = face_check(bm, [f for f, s, c in F if f.is_valid])
    ob = obj_from_bm('WRX_Cabin', bm, [M['clay'], M['glass'], M['under'], M['lamp'], M['trim']], body); smooth(ob, 50); return ob

# ---------------- blueprint-outline decals (lamps, grille / intake) ----------------
def build_decals(M, body):
    """each outline = convex hull of a blueprint mask component in its own view, ray-cast along the view direction
    onto WRX_Body and lifted 4 mm: headlamps + fogs (front view lenses), headlamp / marker side lenses (side view),
    tail lamps (rear + side view red), grille oval + lower intake (front view dark trim)."""
    bm = bmesh.new()
    def cast(o, d):
        ok, loc, nor, idx = body.ray_cast(to_bl(o), to_bl(d))
        return (loc + nor * 0.006) if ok else None
    def add_rings(poly, castf, mi):
        """poly (n,2) in view coords -> rings at 100 % / 55 % / centre, each vertex ray-cast (conforms to the body)."""
        P = np.asarray(poly, float); c2 = P.mean(0)
        R1 = [castf(u, v) for u, v in P]; R2 = [castf(*(c2 + 0.55 * (p - c2))) for p in P]; C0 = castf(*c2)
        if C0 is None or any(p is None for p in R1 + R2): return
        v1 = [bm.verts.new(p) for p in R1]; v2 = [bm.verts.new(p) for p in R2]; vc = bm.verts.new(C0); n = len(P)
        for k in range(n):
            k1 = (k + 1) % n
            bm.faces.new((v1[k], v1[k1], v2[k1], v2[k])).material_index = mi
            bm.faces.new((vc, v2[k], v2[k1])).material_index = mi
    grille = lambda p: np.abs(p[:, 0]).max() < 0.45 and p[:, 1].min() > 0.25 and p[:, 1].max() < 0.70
    for view, key, mi, flt, mp in (('front', 'LL', 0, None, 12), ('front', 'K', 1, grille, 40), ('rear', 'R', 0, None, 12),
                                   ('side', 'R', 0, None, 12), ('side', 'HL', 0, None, 12)):
        for poly in DC.outlines(view, key, mp, 8, flt):
            if view == 'front': add_rings(poly, lambda u, v: cast((5, u, v), (-1, 0, 0)), mi)
            elif view == 'rear': add_rings(poly, lambda u, v: cast((-5, u, v), (1, 0, 0)), mi)
            else:
                for s in (1, -1): add_rings(poly, lambda u, v, s=s: cast((u, 5 * s, v), (0, -s, 0)), mi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:       # face the viewer (outward): flip any face whose normal points into the body
        c = f.calc_center_median(); ok, loc, nor, i = body.closest_point_on_mesh(c)
        if ok and f.normal.dot(nor) < 0: f.normal_flip()
    ob = obj_from_bm('WRX_Decals', bm, [M['lamp'], M['trim']], body); smooth(ob, 70); return ob

# ---------------- generic small-part loft (rings across a span) ----------------
def ring_loft(name, rings, mats, parent, mat_idx=None, cap=True, angle=40):
    """rings: list of lists of car-frame points (same count, closed loops) -> tube with end caps."""
    bm = bmesh.new(); R = [[bm.verts.new(to_bl(p)) for p in r] for r in rings]; n = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if cap: bm.faces.new(R[0]); bm.faces.new(R[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if mat_idx:
        for f in bm.faces: f.material_index = mat_idx(f)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = obj_from_bm(name, bm, mats, parent); smooth(ob, angle); return ob

def build_scoop(name, M, body, x0, x1, yb, yt, h):
    """bonnet scoop: mouth (open, dark) facing forward at x1, blends into the hood at x0.  yb/yt: base/top half-width,
    h: mouth height above the hood."""
    xs = np.linspace(x1, x0, 5); hs = [h, h * 0.97, h * 0.75, h * 0.42, 0.006]
    rings = []
    for x, hh in zip(xs, hs):
        zh = G.ZTB(x) - 0.004
        rings.append([(x, -yb, zh), (x, -yt, zh + hh), (x, -yt * 0.6, zh + hh + 0.006), (x, yt * 0.6, zh + hh + 0.006), (x, yt, zh + hh), (x, yb, zh)])
    def mi(f):
        c = car(f.calc_center_median()); n = f.normal
        return 1 if (c[0] > x1 - 0.003 and -n.y > 0.7) else 0
    ob = ring_loft(name, rings, [M['clay'], M['trim']], body, mi)
    return ob

def build_lip_spoiler(M, body):
    """base WRX boot spoiler, blueprint side profile: on the deck at x -1.70, tip (-2.065, 1.135 top / 1.09 under)."""
    prof = [(-1.70, 1.068), (-2.065, 1.135), (-2.075, 1.092), (-1.90, 1.052)]
    rings = []
    for y, s in ((-0.66, 0.6), (-0.60, 1.0), (0.0, 1.0), (0.60, 1.0), (0.66, 0.6)):
        r = []
        for (x, z) in prof:
            zd = G.ZTB(x) if x > -2.06 else 1.02
            r.append((x + (0.02 if s < 1 and x < -1.95 else 0), y, zd + (z - zd) * s + (0.002 if z <= 1.07 else 0)))
        rings.append(r)
    return ring_loft('WRX_LipSpoiler', rings, [M['clay']], body, angle=35)

def build_sti_wing(M, body):
    """GDB (2001-02) STI tall pedestal wing -- ESTIMATED (not on the WRX sheet): two uprights at y +-.52 rising from the
    deck to a blade (chord x -1.87..-2.14, top 1.255) spanning +-.70 with small end kick-ups."""
    def blade(y, dz=0.0):
        return [(-1.87, y, 1.212 + dz), (-1.93, y, 1.236 + dz), (-2.14, y, 1.258 + dz), (-2.145, y, 1.240 + dz), (-1.93, y, 1.205 + dz)]
    rings = [blade(-0.70, 0.022), blade(-0.64), blade(-0.30), blade(0.0), blade(0.30), blade(0.64), blade(0.70, 0.022)]
    bm_obs = [ring_loft('STI_Wing', rings, [M['clay']], body, angle=35)]
    ob = bm_obs[0]
    # uprights merged into the same object
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for ys in (-0.52, 0.52):
        loops = []
        for x0, x1, z, w in ((-1.96, -2.06, G.ZTB(-2.0) - 0.004, 0.024), (-1.95, -2.03, 1.212, 0.018)):
            loops.append([bm.verts.new(to_bl(p)) for p in ((x0, ys - w, z), (x1, ys - w, z), (x1, ys + w, z), (x0, ys + w, z))])
        a, b = loops
        for k in range(4): bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(ob.data); bm.free(); return ob

def build_sti_lip(M, body):
    """STI front bumper lower lip -- ESTIMATED: thin splitter following the bumper bottom outline, 3 cm proud, z .20-.235."""
    X = [x for x in G.stations() if x > 1.65]
    pts = []
    for x in X:
        sec = G.lower_section(x); pts.append((x, sec[1, 0]))
    pts = sorted(pts, key=lambda p: -p[1])               # outer corner -> centre
    path = [(x + 0.03 * (1 if y < 0.6 else 0.5), y + (0.02 if y > 0.6 else 0)) for x, y in pts if y < 0.80]
    path = path[::3] + [path[-1]] if len(path) > 6 else path
    left = [(x, y) for x, y in path]; full = [(x, -y) for x, y in left] + [(x, y) for x, y in left[::-1]]
    full = [p for i, p in enumerate(full) if i == 0 or abs(p[1] - full[i - 1][1]) > 1e-4]
    bm = bmesh.new(); top = []; bot = []
    for x, y in full:
        zb = G.ZB(x)
        top.append(bm.verts.new(to_bl((x - 0.03, y, zb + 0.012)))); bot.append(bm.verts.new(to_bl((x, y, zb - 0.022))))
    for k in range(len(full) - 1):
        bm.faces.new((top[k], top[k + 1], bot[k + 1], bot[k]))
    inner = [bm.verts.new(to_bl((x - 0.09, y * 0.97, G.ZB(x) - 0.012))) for x, y in full]
    for k in range(len(full) - 1):
        bm.faces.new((bot[k], bot[k + 1], inner[k + 1], inner[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.material_index = 1
    return obj_from_bm('STI_FrontLip', bm, [M['clay'], M['trim']], body)

def build_mirror(name, s, M, body):
    """door mirror, blueprint: side x .84-1.04 (black), front view z .935-1.045, out to y .965."""
    def r6(x, yi, yo, z0, z1):
        zm = 0.5 * (z0 + z1)
        return [(x, s * yi, z0), (x, s * (yo - 0.015), z0), (x, s * yo, zm), (x, s * (yo - 0.015), z1), (x, s * yi, z1), (x, s * (yi - 0.01), zm)]
    rings = [r6(1.035, 0.80, 0.86, 0.950, 1.000), r6(0.99, 0.80, 0.972, 0.925, 1.058), r6(0.85, 0.80, 0.972, 0.932, 1.050)]
    return ring_loft(name, rings, [M['trim']], body, angle=50)

def build_liner(name, xc, side, front, M, body):
    """wheel-well liner: arch tunnel (radius about the static hub) + inner wall, sized for bump + lock."""
    R = LINER_R_F if front else LINER_R_R; yin = LINER_YIN_F if front else LINER_YIN_R; yout = 0.80
    ang = np.radians(np.linspace(-12, 192, 10))
    bm = bmesh.new()
    o = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yout, G.HUB_Z + R * math.sin(a)))) for a in ang]
    i = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yin, G.HUB_Z + R * math.sin(a)))) for a in ang]
    for k in range(len(ang) - 1): bm.faces.new((o[k], o[k + 1], i[k + 1], i[k]))
    bm.faces.new(i[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.normal_flip()     # visible from inside the well
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return obj_from_bm(name, bm, [M['under']], body)

def build_under(M, body):
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)['verts']
    x0, x1, y0, y1, z0, z1 = -1.95, 1.95, -0.44, 0.44, 0.30, 0.52
    for v in r: v.co = Vector(((y0 if v.co.x < 0 else y1), (-x0 if v.co.y < 0 else -x1), (z0 if v.co.z < 0 else z1)))
    return obj_from_bm('WRX_Under', bm, [M['under']], body)

def build_wheel(name, M, parent, side, seg=12):
    """tyre + dished rim; mesh origin at the hub centre, axle = local X (Blender X = car y)."""
    r = G.TIRE_OD / 2; rr = G.RIM_D / 2; h = G.TIRE_W / 2
    prof = [(rr * 1.02, -h + 0.012), (r * 0.95, -h), (r, -h + 0.035), (r, h - 0.035), (r * 0.95, h), (rr * 1.04, h - 0.004),
            (rr * 0.97, h - 0.03), (rr * 0.25, h - 0.045)]
    MATI = [0, 0, 0, 0, 0, 1, 1]
    bm = bmesh.new(); rings = []
    for k in range(seg):
        a = 2 * math.pi * (k + 0.5) / seg
        rings.append([bm.verts.new(Vector((side * off, rad * math.cos(a), rad * math.sin(a)))) for rad, off in prof])
    for k in range(seg):
        a, b = rings[k], rings[(k + 1) % seg]
        for i in range(len(prof) - 1):
            f = bm.faces.new((a[i], b[i], b[i + 1], a[i + 1])); f.material_index = MATI[i]
    hub = bm.faces.new([rg[-1] for rg in rings]); hub.material_index = 1
    inner = bm.faces.new([rg[0] for rg in rings]); inner.material_index = 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[hub, inner])
    ob = obj_from_bm(name, bm, [M['tire'], M['rim'], M['under']], parent); smooth(ob, 50); return ob

# ---------------- rig poses ----------------
def set_pose(rig, heave=0.0, roll=0.0, pitch=0.0, steer=0.0, wheel_dz=None):
    """Blender authoring pose.  Body: heave (m, + up), roll (deg, + = body leans to the car's right), pitch (deg, + nose
    up).  Wheels stay planted on the ground (Hub empties never move) -> the body motion IS the suspension travel.
    steer: deg, + = left lock.  wheel_dz: optional per-corner hub offsets (m) for wheel-only bump / droop poses."""
    body = rig['body']; body.location = (0, 0, heave)
    body.rotation_euler = (math.radians(-pitch), math.radians(-roll), 0)   # Blender X = car left axis (+ = nose down), Y = -fwd
    for k, st in rig['steer'].items(): st.rotation_euler = (0, 0, math.radians(steer))
    for k, hb in rig['hub'].items():
        hb.location = Vector(rig['hub_rest'][k]) + Vector((0, 0, (wheel_dz or {}).get(k, 0.0)))
    bpy.context.view_layer.update()

def rel_travel(rig):
    """per-corner wheel travel relative to the body (m, + = bump) for the current pose."""
    out = {}
    body = rig['body']; inv = body.matrix_world.inverted()
    for k, hb in rig['hub'].items():
        p_body = inv @ hb.matrix_world.translation
        out[k] = round(p_body.z - rig['hub_rest'][k][2], 4)
    return out

def main():
    reset()
    M = dict(clay=mat('clay', (0.66, 0.66, 0.66), 0.55), glass=mat('clay_glass', (0.16, 0.17, 0.19), 0.3),
             tire=mat('tire', (0.05, 0.05, 0.05), 0.9), rim=mat('rim', (0.62, 0.62, 0.64), 0.4),
             under=mat('under', (0.02, 0.02, 0.02), 1.0), lamp=mat('clay_lamp', (0.30, 0.32, 0.36), 0.2),
             trim=mat('clay_trim', (0.08, 0.08, 0.085), 0.8))
    root = empty('WRX-vehicle', (0, 0, 0), size=0.5, kind='ARROWS')
    body = build_body(M, root)
    build_cabin(M, body)
    bpy.context.view_layer.update(); build_decals(M, body)
    build_mirror('WRX_Mirror_L', 1, M, body); build_mirror('WRX_Mirror_R', -1, M, body)
    build_under(M, body)
    for nm, xc, sd, fr in (('FL', G.AXF, 1, True), ('FR', G.AXF, -1, True), ('RL', G.AXR, 1, False), ('RR', G.AXR, -1, False)):
        build_liner('WRX_Liner_' + nm, xc, sd, fr, M, body)
    base = [build_scoop('WRX_Scoop', M, body, 1.25, 1.48, 0.30, 0.22, 0.062), build_lip_spoiler(M, body)]
    sti = [build_scoop('STI_Scoop', M, body, 1.19, 1.515, 0.34, 0.26, 0.088), build_sti_wing(M, body), build_sti_lip(M, body)]
    # rig
    rig = dict(body=body, hub={}, steer={}, hub_rest={})
    for nm, xc, yc in (('FL', G.AXF, G.TRACK_F / 2), ('FR', G.AXF, -G.TRACK_F / 2), ('RL', G.AXR, G.TRACK_R / 2), ('RR', G.AXR, -G.TRACK_R / 2)):
        loc = to_bl((xc, yc, G.HUB_Z)); hb = empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F':
            st = empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        build_wheel('WRX_Wheel_' + nm, M, par, 1 if yc > 0 else -1)
    # collections: base WRX parts hidden, STI parts shown (STI is the target car)
    def coll(name, obs, hide):
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
        for o in obs:
            for uc in o.users_collection: uc.objects.unlink(o)
            c.objects.link(o)
        c.hide_render = hide; c.hide_viewport = hide
        return c
    coll('WRX_base_parts', base, True); coll('STI_parts', sti, False)
    # tri counts
    tris = 0; lines = []
    for ob in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
        ob.data.calc_loop_triangles(); n = len(ob.data.loop_triangles)
        hidden = ob.name in ('WRX_Scoop', 'WRX_LipSpoiler')
        if not hidden: tris += n
        lines.append(f'{ob.name:18s} {n:5d}' + ('   (base-WRX blueprint part, hidden in the STI build)' if hidden else ''))
    lines.append(f'TOTAL (STI build, as rendered) {tris}')
    body_n = sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.name in ('WRX_Body', 'WRX_Cabin'))
    lines.append(f'body shell (WRX_Body + WRX_Cabin) {body_n}')
    open(os.path.join(HERE, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    # triangle soup in the car frame (rest pose), with material + object names
    bpy.context.view_layer.update()
    T = []; TM = []; TO = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        me = ob.data; me.calc_loop_triangles(); mw = ob.matrix_world
        for t in me.loop_triangles:
            T.append([[-(mw @ me.vertices[i].co).y, (mw @ me.vertices[i].co).x, (mw @ me.vertices[i].co).z] for i in t.vertices])
            TM.append(me.materials[t.material_index].name if me.materials else 'clay'); TO.append(ob.name)
    np.save('bp/tris_carframe.npy', np.array(T, np.float32)); np.save('bp/tris_material.npy', np.array(TM)); np.save('bp/tris_object.npy', np.array(TO))
    # clearance check: posed tyres vs body / liners / parts (BVH overlap in the body frame)
    import clearance; importlib.reload(clearance)
    rep = clearance.check(rig, set_pose, rel_travel, BUMP, DROOP, LOCK, ROLL)
    # pass 2: ONE mono body mesh (user preference): body + cabin + decals + mirrors + liners + underbody + STI scoop /
    # wing / lip joined into WRX_Body; wheels stay separate objects under the Hub / Steer pivots.  Per-part tri counts
    # and the per-part triangle soup above were written before the join (IoU sets / clearance attribution).
    set_pose(rig)
    parts = [o for o in bpy.data.objects if o.type == 'MESH' and o is not body and not o.name.startswith('WRX_Wheel_')
             and o.name not in ('WRX_Scoop', 'WRX_LipSpoiler')]
    joined = sorted(o.name for o in parts)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    for c in list(bpy.data.collections):
        if c.name == 'STI_parts': bpy.data.collections.remove(c)
    body.data.calc_loop_triangles(); mono_n = len(body.data.loop_triangles)
    rep['mono_recheck'] = clearance.check(rig, set_pose, rel_travel, BUMP, DROOP, LOCK, ROLL, summary_only=True)
    rep['shading_qc'] = QC
    import json; json.dump(rep, open('bp/clearance.json', 'w'), indent=1)
    wheels = sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.name.startswith('WRX_Wheel_'))
    with open(os.path.join(HERE, 'tri_count.txt'), 'a') as fh:
        fh.write(f'\nMONO BODY (pass 2): WRX_Body = {mono_n} tris  (joined: {", ".join(joined)})\n')
        fh.write(f'wheels (4 separate pivoted objects) = {wheels}\nTOTAL as exported (WRX_Body + 4 wheels) = {mono_n + wheels}\n')
        fh.write(f'shading QC (loft quads): {json.dumps(QC)}\n')
    print('MONO', mono_n, 'wheels', wheels, 'QC', QC)
    set_pose(rig)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'wrx_clay.blend'), compress=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'wrx_clay.glb'), export_format='GLB', use_visible=True)
    if '--render' in sys.argv:
        import render_wrx; importlib.reload(render_wrx); render_wrx.render_all(HERE, rig, set_pose, rel_travel, dict(BUMP=BUMP, DROOP=DROOP, LOCK=LOCK, ROLL=ROLL))

if __name__ == '__main__': main()
