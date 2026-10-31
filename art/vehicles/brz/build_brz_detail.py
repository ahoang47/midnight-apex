"""BRZ detail + texture pass (PSX / early-PS2 look, same pipeline as the S2000).  Run:
  blender -b -P build_brz_detail.py -- [--no-export]
Silhouette = the approved pass-4 clay (build_brz.py, DETAIL=True: lamp/plate insets dropped, they are atlas decals now)
plus small gated tweaks (rear-face rake / rounder rear corners).  Adds: joined textured body (UV, Cycles-baked AO,
painted 1024^2 texture from tex/make_body.py), 256^2 parts atlas (tex/make_atlas.py), wedge headlight and swept
boomerang taillight decals shaped from the blueprint lamp outlines, flat plates + made-up badges, 16-sided atlas wheels
(10 twin-spoke), glow sprites and a blob shadow, fake-shine materials (ambient + key + Blinn + painted env x fresnel).
Writes bp/tris_carframe.npy (car meshes only, for bp/bpcompare.py), brz_lowpoly.blend (textures packed, blueprint
planes viewport-only), .glb / .obj+.mtl / .fbx (Principled materials with the same textures for export)."""
import bpy, bmesh, sys, os, math, subprocess, json, importlib
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'parts'))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
import shutil; PY3 = shutil.which('python3') or '/usr/bin/python3'; TS = 1024
TEX = os.path.join(HERE, 'tex'); os.makedirs(os.path.join(TEX, 'build'), exist_ok=True)
def to_car(v): return np.array([-v[1], v[0], v[2]])

# ---------------------------------------------------------------- gated geometry tweaks (see README: detail pass)
# rear face raked forward toward the top + rounder plan corners on the lamp / lip columns (softens the tall flat rear);
# applied inside parts/brz_geo.py at import.  Default = the gated choice; BRZ_REAR_TWEAK env overrides for trials.
os.environ.setdefault('BRZ_REAR_TWEAK', json.dumps({'p4': [-2.085, 0.95], 'p5': [-2.050, 1.00], 'p6': [-2.012, 0.92], 'p7': [-2.015, 0.80]}))
import build_brz as B; B.DETAIL = True
G = B.G; import brz_bp as BP
to_bl = B.to_bl

# ---------------------------------------------------------------- textures
def run(*a): subprocess.run([PY3, *a], check=True)
ATLAS_PNG = os.path.join(HERE, 'brz_atlas.png'); ENV_PNG = os.path.join(HERE, 'brz_env.png'); BODY_PNG = os.path.join(HERE, 'brz_body.png')
run(os.path.join(TEX, 'make_atlas.py'), ATLAS_PNG); run(os.path.join(TEX, 'make_env.py'), ENV_PNG)
UV = dict(WHEEL=(0, .5, .5, 1), HEAD=(.5, .75, 1, 1), TAIL=(.5, .5, 1, .75), PLATE=(.5, .25, .875, .4375),
          WORD=(.5, .4375, .875, .5), EMBLEM=(.875, .4375, 1, .5), EXH=(.875, .3125, 1, .4375), TREAD=(0, 0, .5, .25))
DARK_UV = (0.885, 0.33)          # a black texel in the atlas (exhaust tile corner)

# ---------------------------------------------------------------- fake-shine material (A.3 shader formula)
KEY_L = Vector(to_bl((0.45, 0.55, 0.70))).normalized()   # key from front-left-above (car frame)
ENV_IMG = None
def fake_mat(name, rgb=(1, 1, 1), img=None, ambient=0.42, key=0.70, spec=0.35, shin=40.0, env=0.30, env_tint=(1, 1, 1),
             emit=0.0, interp='Closest'):
    """colour = albedo*(ambient + key*N.L) + spec*(N.H)^shin + env(reflect(V,N))*tint*fres,
    fres = env*(1-max(N.V,0))^2 + 0.08 (scaled by env so matte parts stay matte) ; output = Emission (no scene lights).
    A Principled BSDF with the same albedo is kept in the tree (unlinked) and swapped in for the glb/obj/fbx export."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nd = nt.nodes; L = nt.links.new
    pb = nd['Principled BSDF']; out = nd['Material Output']
    pb.inputs['Base Color'].default_value = (*rgb, 1); pb.inputs['Roughness'].default_value = 0.45 if env > 0.2 else 0.8
    m.diffuse_color = (*rgb, 1)
    if img is not None:
        t = nd.new('ShaderNodeTexImage'); t.image = img; t.interpolation = interp; t.name = 'ALBEDO'
        L(t.outputs['Color'], pb.inputs['Base Color']); alb = t.outputs['Color']
    else:
        c = nd.new('ShaderNodeRGB'); c.outputs[0].default_value = (*rgb, 1); alb = c.outputs[0]
    geo = nd.new('ShaderNodeNewGeometry'); N, V = geo.outputs['Normal'], geo.outputs['Incoming']
    def vm(op, a, b=None, val=None):
        n = nd.new('ShaderNodeVectorMath'); n.operation = op; L(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list, Vector)): n.inputs[1].default_value = tuple(b)
            else: L(b, n.inputs[1])
        if val is not None: n.inputs[3].default_value = val
        return n
    def mm(op, a, b=None, c=None, clamp=False):
        n = nd.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    ndl = mm('MAXIMUM', vm('DOT_PRODUCT', N, KEY_L).outputs['Value'], 0.0)
    dif = mm('MULTIPLY_ADD', ndl, key, ambient)
    lit = vm('SCALE', alb); L(dif, lit.inputs['Scale'])
    H = vm('NORMALIZE', vm('ADD', V, KEY_L).outputs[0])
    ndh = mm('MAXIMUM', vm('DOT_PRODUCT', N, H.outputs[0]).outputs['Value'], 0.0)
    sp = mm('MULTIPLY', mm('POWER', ndh, shin), spec)
    if img is not None:      # painted black trim on the shared paint texture: dimmer spec + env than the clear coat
        lum = nd.new('ShaderNodeRGBToBW'); L(alb, lum.inputs[0]); kpaint = mm('MULTIPLY_ADD', lum.outputs[0], 8.0, 0.22, clamp=True)
        sp = mm('MULTIPLY', sp, kpaint)
    ndv = mm('MAXIMUM', vm('DOT_PRODUCT', N, V).outputs['Value'], 0.0)
    fres = mm('MULTIPLY_ADD', mm('POWER', mm('SUBTRACT', 1.0, ndv), 2.0), env, 0.08 * min(env / 0.3, 1.0))
    R = vm('REFLECT', vm('SCALE', V, val=-1.0).outputs[0], N)
    et = nd.new('ShaderNodeTexEnvironment'); et.image = ENV_IMG; et.interpolation = 'Linear'; L(R.outputs[0], et.inputs['Vector'])
    envc = vm('MULTIPLY', et.outputs['Color'], tuple(env_tint))
    if img is not None: fres = mm('MULTIPLY', fres, kpaint)
    envs = vm('SCALE', envc.outputs[0]); L(fres, envs.inputs['Scale'])
    acc = vm('ADD', lit.outputs[0], envs.outputs[0])
    spv = nd.new('ShaderNodeCombineXYZ'); [L(sp, spv.inputs[i]) for i in range(3)]
    acc = vm('ADD', acc.outputs[0], spv.outputs[0])
    if emit:
        ee = vm('SCALE', alb, val=emit); acc = vm('ADD', acc.outputs[0], ee.outputs[0])
    em = nd.new('ShaderNodeEmission'); em.name = 'FAKESHINE'; L(acc.outputs[0], em.inputs['Color'])
    L(em.outputs[0], out.inputs['Surface']); return m
def use_principled(on):
    for m in bpy.data.materials:
        if not m.use_nodes or 'FAKESHINE' not in m.node_tree.nodes or 'Principled BSDF' not in m.node_tree.nodes: continue
        nt = m.node_tree; out = nt.nodes['Material Output']
        src = nt.nodes['Principled BSDF'] if on else nt.nodes['FAKESHINE']
        nt.links.new(src.outputs[0], out.inputs['Surface'])

# ---------------------------------------------------------------- simple mesh builder (car-frame points)
class MB:
    def __init__(s): s.v, s.f = [], []
    def add(s, p): s.v.append(Vector(p)); return len(s.v) - 1          # Blender coords
    def face(s, idx, mat, uvs=None): s.f.append((tuple(idx), mat, uvs))
    def obj(s, name, mats, smooth_angle=None, coll=None):
        me = bpy.data.meshes.new(name); bm = bmesh.new(); bv = [bm.verts.new(p) for p in s.v]; uvl = bm.loops.layers.uv.new('UVMap')
        for idx, mk, uvs in s.f:
            try: fa = bm.faces.new([bv[i] for i in idx])
            except ValueError: continue
            fa.material_index = mk; fa.smooth = smooth_angle is not None
            for lp, uv in zip(fa.loops, uvs or [DARK_UV] * len(idx)): lp[uvl].uv = uv
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bm.to_mesh(me); bm.free()
        for m in mats: me.materials.append(m)
        ob = bpy.data.objects.new(name, me); (coll or bpy.context.collection).objects.link(ob)
        if smooth_angle is not None:
            me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        return ob

def bvh_of(obs):
    V, F = [], []
    for ob in obs:
        me = ob.data; mw = ob.matrix_world; o = len(V)
        V += [mw @ v.co for v in me.vertices]; F += [[o + i for i in p.vertices] for p in me.polygons]
    return BVHTree.FromPolygons(V, F)
def decal_rays(mb, bvh, fn, nu, nv, uvrect, mat, off=0.006, skirt=None):
    """grid decal: fn(s,t) -> (target point, outward dir) in car frame; ray from target+0.3*dir along -dir."""
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            s, t = i / nu, j / nv; p, n = fn(s, t); n = np.asarray(n, float); n /= np.linalg.norm(n)
            o = to_bl(np.asarray(p) + 0.3 * n); d = -to_bl(n)
            hit, nrm, _, _ = bvh.ray_cast(o, d, 1.0)
            if hit is None: hit, nrm, _, _ = bvh.find_nearest(to_bl(p))
            e = (mb.add(hit + nrm * off), (uvrect[0] + (uvrect[2] - uvrect[0]) * s, uvrect[1] + (uvrect[3] - uvrect[1]) * t), d)
            if skirt is not None: e = e + (mb.add(hit - nrm * 0.004),)
            row.append(e)
        grid.append(row)
    if skirt is not None:
        ring = [grid[0][i] for i in range(nu + 1)] + [grid[j][nu] for j in range(1, nv + 1)] + \
               [grid[nv][i] for i in range(nu - 1, -1, -1)] + [grid[j][0] for j in range(nv - 1, 0, -1)]
        for k in range(len(ring)):
            a, b = ring[k], ring[(k + 1) % len(ring)]
            mb.face((a[0], b[0], b[3], a[3]), skirt)
    for j in range(nv):
        for i in range(nu):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            idx = [e[0] for e in q]; uv = [e[1] for e in q]; d = q[0][2]
            nn = (mb.v[idx[1]] - mb.v[idx[0]]).cross(mb.v[idx[3]] - mb.v[idx[0]])
            if nn.length < 1e-10: nn = (mb.v[idx[2]] - mb.v[idx[1]]).cross(mb.v[idx[3]] - mb.v[idx[1]])
            if nn.dot(d) > 0: idx, uv = idx[::-1], uv[::-1]
            mb.face(idx, mat, uv)

# ---------------------------------------------------------------- lamps from the blueprint outlines
def lerp(keys, v):
    k = np.asarray(keys, float); return float(np.interp(v, k[:, 0], k[:, 1]))
def head_fn(sgn):
    """wedge headlight: plan path = blueprint top_f centre line (inner tip by the nose -> outer end on the fender);
    height = blueprint front-view outline: thin inner tip, tall outer end."""
    PX = [(0.0, 2.012), (0.5, 1.900), (1.0, 1.645)]; PY = [(0.0, 0.405), (0.5, 0.590), (1.0, 0.775)]
    def fn(s, t):
        x, yy = lerp(PX, s), lerp(PY, s)
        lo = 0.622 + 0.078 * s ** 1.6; hi = 0.652 + 0.128 * s ** 0.75
        nrm = (1.0 - 0.75 * s, (0.30 + 0.75 * s) * sgn, 0.25)
        return (x, sgn * yy, lo + (hi - lo) * t), nrm
    return fn
def tail_path(bvh, z=0.845, n=160):
    """plan path of the taillight band: ray fan from inside the car at lamp height, inner end on the rear face
    (|y| .40) round the corner and forward along the flank to the side-view tip (x -1.62)."""
    Q = np.array([-1.60, 0.0, z]); pts = []
    for th in np.linspace(math.radians(40), math.radians(89.5), n):
        d = np.array([-math.cos(th), math.sin(th), 0.0])
        hit, nrm, _, _ = bvh.ray_cast(to_bl(Q + 2.0 * d), -to_bl(d), 3.0)
        if hit is None: continue
        p = to_car(hit)
        if p[1] < 0.405 or p[0] > -1.625: continue
        pts.append(p[:2])
    pts = np.array(pts); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    return pts, seg / seg[-1]
def tail_fn(pts, cum, sgn):
    def fn(s, t):
        x = float(np.interp(s, cum, pts[:, 0])); yy = float(np.interp(s, cum, pts[:, 1]))
        s2 = min(s + 0.01, 1.0); s1 = max(s - 0.01, 0.0)
        tx = np.interp(s2, cum, pts[:, 0]) - np.interp(s1, cum, pts[:, 0]); ty = np.interp(s2, cum, pts[:, 1]) - np.interp(s1, cum, pts[:, 1])
        nl = math.hypot(tx, ty) + 1e-9; nrm = (-ty / nl, tx / nl * sgn, 0.12)     # outward = tangent rotated +90 deg in plan
        # rear-face part follows the blueprint rear-view outline (by |y|), flank part the side-view outline (by x),
        # blended by how far the surface has turned (plan normal), so the band stays continuous round the corner
        lo_r = lerp([(.405, .800), (.42, .778), (.72, .800), (.80, .800)], yy); hi_r = lerp([(.405, .830), (.45, .893), (.80, .900)], yy)
        lo_s = lerp([(-2.05, .790), (-1.93, .768), (-1.80, .788), (-1.70, .818), (-1.64, .850), (-1.62, .878)], x)
        hi_s = lerp([(-2.05, .900), (-1.90, .893), (-1.62, .886)], x)
        w = float(np.clip((abs(tx / nl) - 0.70) / 0.25, 0, 1)); w = w * w * (3 - 2 * w)
        lo = lo_r + (lo_s - lo_r) * w; hi = hi_r + (hi_s - hi_r) * w
        return (x, sgn * yy, lo + (hi - lo) * t), nrm
    return fn

def build_wheel(mb, x, y):
    """16-sided wheel: tread band (atlas tread tile), sidewall + rim lip + dished rim face planar-mapped onto the
    atlas wheel tile (10 twin-spoke, sidewall lettering mirrored per side so it reads correctly), dark inner cap."""
    side = 1 if y > 0 else -1; r = G.TIRE_OD / 2; rr = G.RIM_D / 2; h = G.TIRE_W / 2; seg = 16; zc = G.TIRE_OD / 2
    prof = [(r, -h + 0.02), (r, h - 0.02), (r * 0.955, h), (rr * 1.05, h - 0.002), (rr * 0.98, h - 0.010), (rr * 0.93, h - 0.032)]
    U = UV['WHEEL']; cu, cv, hu = (U[0] + U[2]) / 2, (U[1] + U[3]) / 2, (U[2] - U[0]) / 2 * 0.995
    T = UV['TREAD']
    ring = []
    for k in range(seg + 1):
        a = 2 * math.pi * k / seg
        ring.append([mb.add(to_bl((x + rad * math.cos(a), y + side * off, zc + rad * math.sin(a)))) for rad, off in prof])
    def puv(rad, a): return (cu - side * hu * rad / r * math.cos(a), cv + hu * rad / r * math.sin(a))
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg; A, Bk = ring[k], ring[k + 1]
        u0, u1 = T[0] + (T[2] - T[0]) * k / seg, T[0] + (T[2] - T[0]) * (k + 1) / seg
        f = [A[0], Bk[0], Bk[1], A[1]]; uv = [(u0, T[1]), (u1, T[1]), (u1, T[3]), (u0, T[3])]
        mb.face(f if side > 0 else f[::-1], 0, uv if side > 0 else uv[::-1])
        for i in range(1, len(prof) - 1):
            f = [A[i], Bk[i], Bk[i + 1], A[i + 1]]
            uv = [puv(prof[i][0], a0), puv(prof[i][0], a1), puv(prof[i + 1][0], a1), puv(prof[i + 1][0], a0)]
            mb.face(f if side > 0 else f[::-1], 0, uv if side > 0 else uv[::-1])
    cap = [ring[k][-1] for k in range(seg)]; uv = [puv(prof[-1][0], 2 * math.pi * k / seg) for k in range(seg)]
    mb.face(cap if side > 0 else cap[::-1], 0, uv if side > 0 else uv[::-1])
    inner = [ring[k][0] for k in range(seg)]
    mb.face(inner[::-1] if side > 0 else inner, 0, [DARK_UV] * seg)

def flat_quad(mb, c, n, up, w, h, uvr, mat, off=0.006):
    """flat textured quad centred at car point c, facing n (car frame), 'up' approx vertical"""
    n = np.asarray(n, float); n /= np.linalg.norm(n); up = np.asarray(up, float); up = up - n * up.dot(n); up /= np.linalg.norm(up)
    rt = np.cross(up, n)        # viewer's right when looking against n
    c = np.asarray(c, float) + n * off
    P = [c - rt * w / 2 - up * h / 2, c + rt * w / 2 - up * h / 2, c + rt * w / 2 + up * h / 2, c - rt * w / 2 + up * h / 2]
    ids = [mb.add(to_bl(p)) for p in P]
    mb.face(ids, mat, [(uvr[0], uvr[1]), (uvr[2], uvr[1]), (uvr[2], uvr[3]), (uvr[0], uvr[3])])
def surf(bvh, p, d):
    """hit point/normal (car frame) of a ray from car point p along car dir d"""
    hit, nrm, _, _ = bvh.ray_cast(to_bl(np.asarray(p, float)), to_bl(np.asarray(d, float)), 4.0)
    return to_car(hit), to_car(nrm)

# ================================================================ build
B.reset()
ENV_IMG = bpy.data.images.load(ENV_PNG); ENV_IMG.name = 'BRZ_Env'
ATLAS = bpy.data.images.load(ATLAS_PNG); ATLAS.name = 'BRZ_Atlas'
M = dict(clay=B.mat('clay', (0.66, 0.66, 0.66)), glass=B.mat('clay_glass', (0.16, 0.17, 0.19)), tire=B.mat('tire', (.05, .05, .05)),
         rim=B.mat('rim', (.6, .6, .62)), under=B.mat('under', (.02, .02, .02)), lamp=B.mat('clay_lamp', (.3, .32, .36)), trim=B.mat('clay_trim', (.08, .08, .085)))
body = B.build_body(M); cab = B.build_cabin(M)
mirs = [B.build_mirror('BRZ_Mirror_L', 1, M), B.build_mirror('BRZ_Mirror_R', -1, M)]
under = B.build_under(M)
exh = [B.build_exhaust('BRZ_Exhaust_L', 0.45, M), B.build_exhaust('BRZ_Exhaust_R', -0.45, M)]
for o in bpy.data.objects: o.select_set(False)
for o in [body, cab] + mirs: o.select_set(True)
bpy.context.view_layer.objects.active = body; bpy.ops.object.join(); body.name = 'BRZ_Body'; body.data.name = 'BRZ_Body'
body.select_set(False)
bvh = bvh_of([body])

# ---- atlas parts: lamps, plates, badges, wheels
MAT_ATLAS = fake_mat('BRZ_Parts_Atlas', img=ATLAS, ambient=0.55, key=0.55, spec=0.30, shin=30, env=0.18)
MAT_LAMP = fake_mat('BRZ_Lamps_Atlas', img=ATLAS, ambient=0.85, key=0.25, spec=0.55, shin=60, env=0.35, env_tint=(0.75, 0.85, 1.0), emit=0.35)
MAT_SKIRT = fake_mat('BRZ_Lamp_Bezel', rgb=(0.01, 0.01, 0.012), ambient=1.0, key=0.0, spec=0.0, env=0.0)
lm = MB()
for sgn in (1, -1):
    decal_rays(lm, bvh, head_fn(sgn), 8, 2, UV['HEAD'], 0, off=0.006, skirt=1)
pts, cum = tail_path(bvh)
for sgn in (1, -1):
    decal_rays(lm, bvh, tail_fn(pts, cum, sgn), 12, 2, UV['TAIL'], 0, off=0.006, skirt=1)
lamps = lm.obj('BRZ_Lamps', [MAT_LAMP, MAT_SKIRT], smooth_angle=50)
pm = MB()
c, n = surf(bvh, (3.0, 0, 0.415), (-1, 0, 0)); flat_quad(pm, c, (1, 0, 0.05), (0, 0, 1), 0.28, 0.14, UV['PLATE'], 0, off=0.012)
c, n = surf(bvh, (-3.0, 0, 0.49), (1, 0, 0)); flat_quad(pm, c, (-1, 0, 0.05), (0, 0, 1), 0.28, 0.14, UV['PLATE'], 0, off=0.010)
c, n = surf(bvh, (3.0, 0, 0.535), (-1, 0, 0)); flat_quad(pm, c, n, (0, 0, 1), 0.085, 0.043, UV['EMBLEM'], 0)
c, n = surf(bvh, (-3.0, 0, 0.84), (1, 0, 0)); flat_quad(pm, c, n, (0, 0, 1), 0.085, 0.043, UV['EMBLEM'], 0)
c, n = surf(bvh, (-3.0, 0.27, 0.80), (1, 0, 0)); flat_quad(pm, c, (-1, 0, 0.1), (0, 0, 1), 0.16, 0.027, UV['WORD'], 0)
for xa, ya in ((G.AXF, G.TRACK_F / 2), (G.AXF, -G.TRACK_F / 2), (G.AXR, G.TRACK_R / 2), (G.AXR, -G.TRACK_R / 2)):
    build_wheel(pm, xa, ya)
parts = pm.obj('BRZ_Parts', [MAT_ATLAS], smooth_angle=40)
# split wheels into their own objects for game use? keep plates/badges + wheels in one atlas object per S2000 practice

# ---- paint: UV, Cycles AO bake, per-texel data, painter
def texture_body():
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
    if sc.world is None: sc.world = bpy.data.worlds.new('BakeWorld')
    sc.world.light_settings.distance = 0.30
    ao_img = bpy.data.images.new('BRZ_AO', TS, TS, alpha=False); tmp = []
    for sl in body.material_slots:
        nt_ = sl.material.node_tree; n_ = nt_.nodes.new('ShaderNodeTexImage'); n_.image = ao_img; nt_.nodes.active = n_; tmp.append((nt_, n_))
    sc.render.bake.margin = 16; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='AO', use_clear=True)
    ao_png = os.path.join(TEX, 'build', 'body_ao.png'); ao_img.filepath_raw = ao_png; ao_img.file_format = 'PNG'; ao_img.save()
    for nt_, n_ in tmp: nt_.nodes.remove(n_)
    bpy.data.images.remove(ao_img)
    me = body.data; me.calc_loop_triangles(); uvd = me.uv_layers.active.data
    pos = np.zeros((TS, TS, 3), np.float32); nrm = np.zeros((TS, TS, 3), np.float32); mask = np.full((TS, TS), -1, np.int16)
    cls = {'clay': 0, 'clay_glass': 1, 'under': 2, 'clay_lamp': 3, 'clay_trim': 4}
    slotcls = [cls.get(sl.material.name, 0) for sl in body.material_slots]
    cn = me.corner_normals
    for lt in me.loop_triangles:
        uv = np.array([uvd[l].uv[:] for l in lt.loops]) * TS - 0.5
        Pv = np.array([to_car(me.vertices[v].co) for v in lt.vertices]); Nv = np.array([to_car(cn[l].vector) for l in lt.loops])
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, TS - 1), min(y1, TS - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        (ax, ay), (bx, by), (cx_, cy_) = uv
        den = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
        if abs(den) < 1e-12: continue
        l0 = ((by - cy_) * (gx - cx_) + (cx_ - bx) * (gy - cy_)) / den; l1 = ((cy_ - ay) * (gx - cx_) + (ax - cx_) * (gy - cy_)) / den; l2 = 1 - l0 - l1
        ins = (l0 >= -.02) & (l1 >= -.02) & (l2 >= -.02)
        if not ins.any(): continue
        Lb = np.stack([l0[ins], l1[ins], l2[ins]], 1); ry, rx = gy[ins], gx[ins]
        pos[ry, rx] = Lb @ Pv; nn = Lb @ Nv; nrm[ry, rx] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-6)
        mask[ry, rx] = slotcls[lt.material_index]
    npz = os.path.join(TEX, 'build', 'body_texels.npz'); np.savez_compressed(npz, pos=pos, nrm=nrm, mask=mask)
    run(os.path.join(TEX, 'make_body.py'), npz, BODY_PNG, ao_png)
    img = bpy.data.images.load(BODY_PNG, check_existing=False); img.name = 'BRZ_BodyTex'
    paint = fake_mat('BRZ_Paint_Body', img=img, ambient=0.48, key=0.62, spec=0.45, shin=55, env=0.38, interp='Linear')
    glass = fake_mat('BRZ_Glass', rgb=(0.010, 0.014, 0.022), ambient=1.0, key=0.0, spec=0.6, shin=90, env=0.45, env_tint=(0.55, 0.70, 1.0))
    und = fake_mat('BRZ_Under', rgb=(0.006, 0.006, 0.007), ambient=1.0, key=0.0, spec=0.0, env=0.0)
    for i, sl in enumerate(body.material_slots):
        k = slotcls[i]; sl.material = glass if k == 1 else (und if k == 2 else paint)
    return paint, und
# wheels/lamps exist now so the AO sees them
paint, und = texture_body()
for o in [under]: o.data.materials[0] = und
chrome = fake_mat('BRZ_Exhaust_Chrome', rgb=(0.45, 0.46, 0.48), ambient=0.5, key=0.5, spec=0.8, shin=80, env=0.45)
for o in exh: o.data.materials[0] = chrome; o.data.materials[1] = und
for o in exh + [under, lamps, parts]: o.select_set(False)
for m in ('clay', 'clay_glass', 'tire', 'rim', 'under', 'clay_lamp', 'clay_trim'):
    if m in bpy.data.materials and bpy.data.materials[m].users == 0: bpy.data.materials.remove(bpy.data.materials[m])

# ---- glow sprites + blob shadow (effects; not counted in the model tris, excluded from the IoU and from exports)
def glow_mat(name, rgb, k):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nd = nt.nodes; nd.clear(); L = nt.links.new
    tc = nd.new('ShaderNodeTexCoord'); gr = nd.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = nd.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 1)
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs[0], gr.inputs['Vector'])
    pw = nd.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2; L(gr.outputs['Fac'], pw.inputs[0])
    em = nd.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*rgb, 1); L(pw.outputs[0], em.inputs['Strength'])
    em.inputs['Strength'].default_value = k
    mul = nd.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = k; L(pw.outputs[0], mul.inputs[0]); L(mul.outputs[0], em.inputs['Strength'])
    tr = nd.new('ShaderNodeBsdfTransparent'); ad = nd.new('ShaderNodeAddShader'); o = nd.new('ShaderNodeOutputMaterial')
    L(tr.outputs[0], ad.inputs[0]); L(em.outputs[0], ad.inputs[1]); L(ad.outputs[0], o.inputs['Surface'])
    m.surface_render_method = 'BLENDED'; return m
def blob_mat():
    m = bpy.data.materials.new('BRZ_BlobShadow'); m.use_nodes = True; nt = m.node_tree; nd = nt.nodes; nd.clear(); L = nt.links.new
    tc = nd.new('ShaderNodeTexCoord'); gr = nd.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    L(tc.outputs['Object'], gr.inputs['Vector'])
    mr = nd.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.55
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 0.78; L(gr.outputs['Fac'], mr.inputs['Value'])
    tr = nd.new('ShaderNodeBsdfTransparent'); em = nd.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0, 0, 0, 1)
    mx = nd.new('ShaderNodeMixShader'); o = nd.new('ShaderNodeOutputMaterial')
    L(mr.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], o.inputs['Surface'])
    m.surface_render_method = 'BLENDED'; return m
fx = MB()
GW, GR_ = glow_mat('BRZ_Glow_Head', (1.0, 0.97, 0.9), 1.4), glow_mat('BRZ_Glow_Tail', (1.0, 0.08, 0.05), 1.4)
def sprite(c, n, s, mi):
    n = np.asarray(n, float); n /= np.linalg.norm(n); up = np.array([0, 0, 1.0]) - n * n[2]; up /= np.linalg.norm(up); rt = np.cross(up, n)
    c = np.asarray(c) + n * 0.03
    ids = [fx.add(to_bl(c + (rt * a + up * b) * s)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    fx.face(ids, mi, [(0, 0), (1, 0), (1, 1), (0, 1)])
for sgn in (1, -1):
    sprite((1.80, sgn * 0.70, 0.73), (0.85, 0.5 * sgn, 0.0), 0.085, 0)
    sprite((-2.0, sgn * 0.66, 0.85), (-0.85, 0.5 * sgn, 0.0), 0.08, 1)
glow = fx.obj('BRZ_FX_Glow', [GW, GR_])
# sprite quads use object-space gradient: give each its own local frame by separating per quad is overkill; use UV-based falloff
for m_ in (GW, GR_):
    nd = m_.node_tree.nodes; L = m_.node_tree.links.new
    uvn = nd.new('ShaderNodeUVMap'); mp = [n for n in nd if n.type == 'MAPPING'][0]
    mp.inputs['Location'].default_value = (-1, -1, 0); mp.inputs['Scale'].default_value = (2, 2, 1)
    L(uvn.outputs['UV'], mp.inputs['Vector'])
bs = MB(); ids = [bs.add(to_bl((x_, y_, 0.004))) for x_, y_ in ((-2.55, -1.15), (2.55, -1.15), (2.55, 1.15), (-2.55, 1.15))]
bs.face(ids, 0, [(0, 0), (1, 0), (1, 1), (0, 1)])
blob = bs.obj('BRZ_FX_BlobShadow', [blob_mat()])
bm_ = blob.data.materials[0].node_tree; nd = bm_.nodes; L = bm_.links.new
uvn = nd.new('ShaderNodeUVMap'); mp = nd.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-1, -1, 0); mp.inputs['Scale'].default_value = (2, 2, 1)
L(uvn.outputs['UV'], mp.inputs['Vector']); L(mp.outputs[0], [n for n in nd if n.type == 'TEX_GRADIENT'][0].inputs['Vector'])

# ---- collections, tri count, IoU soup
car_obs = [body, lamps, parts, under] + exh
coll = bpy.data.collections.new('BRZ'); bpy.context.scene.collection.children.link(coll)
fxc = bpy.data.collections.new('BRZ_FX'); bpy.context.scene.collection.children.link(fxc)
for o in list(bpy.data.objects):
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    (fxc if o.name.startswith('BRZ_FX') else coll).objects.link(o)
tris = 0; lines = []
for o in car_obs:
    o.data.calc_loop_triangles(); n = len(o.data.loop_triangles); tris += n; lines.append(f'{o.name} {n}')
fxt = sum(len(o.data.polygons) * 2 for o in (glow, blob))
lines += [f'TOTAL {tris}', f'(effects, not in total: glow sprites + blob shadow {fxt})']
open(os.path.join(HERE, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
T = []
for o in car_obs:
    me = o.data; mw = o.matrix_world
    for t in me.loop_triangles: T.append([to_car(mw @ me.vertices[i].co) for i in t.vertices])
np.save(os.path.join(HERE, 'bp', 'tris_carframe.npy'), np.array(T, np.float32))

# ---------------------------------------------------------------- save + export
if '--no-export' not in ARGS:
    sc = bpy.context.scene
    z = np.load(os.path.join(HERE, 'bp', 'bp_classes.npz')); S = json.load(open(os.path.join(HERE, 'bp', 'curves.json')))['scale_m_per_px']
    bpc = bpy.data.collections.new('Blueprint'); sc.collection.children.link(bpc)
    for view in ('side', 'top', 'front', 'rear'):
        X0, Y0 = int(z[f'{view}_X0']), int(z[f'{view}_Y0']); h_, w_ = z[f'{view}_M'].shape
        pth = os.path.join(TEX, 'build', f'bp_{view}.png')
        subprocess.run([PY3, '-c', f"from PIL import Image; Image.open('{os.path.join(HERE, 'ref', 'brz_blueprint.jpg')}').convert('RGB').crop(({X0},{Y0},{X0 + w_},{Y0 + h_})).save('{pth}')"], check=True)
        img = bpy.data.images.load(pth); img.pack()
        # plane corners in car frame from the blueprint frame used by bp/bpcompare.py
        if view == 'side':
            CM, ZF = float(z['side_CM']), float(z['side_ZF'])
            xa, xb = (CM - X0) * S, (CM - X0 - w_) * S; za, zb = (ZF - Y0 - h_) * S, (ZF - Y0) * S
            V = [(xa, -1.6, za), (xb, -1.6, za), (xb, -1.6, zb), (xa, -1.6, zb)]
            uvq = [(0, 0), (1, 0), (1, 1), (0, 1)]
        elif view == 'top':
            CM, CR = float(z['top_CM']), float(z['top_CR'])
            xa, xb = (CM - X0) * S, (CM - X0 - w_) * S; ya, yb = CR * S, (CR - h_) * S
            V = [(xa, yb, -0.02), (xb, yb, -0.02), (xb, ya, -0.02), (xa, ya, -0.02)]; uvq = [(0, 0), (1, 0), (1, 1), (0, 1)]
        else:
            CC, ZF = float(z[f'{view}_CC']), float(z[f'{view}_ZF']); sg = 1 if view == 'front' else -1
            ya, yb = -sg * CC * S, sg * (w_ - CC) * S; za, zb = (ZF - Y0 - h_) * S, (ZF - Y0) * S
            xp = 3.2 if view == 'front' else -3.2
            V = [(xp, ya, za), (xp, yb, za), (xp, yb, zb), (xp, ya, zb)]; uvq = [(0, 0), (1, 0), (1, 1), (0, 1)]
        m = bpy.data.materials.new('BP_' + view); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        t_ = nt.nodes.new('ShaderNodeTexImage'); t_.image = img; em = nt.nodes.new('ShaderNodeEmission'); o_ = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(t_.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], o_.inputs['Surface'])
        me = bpy.data.meshes.new('BP_' + view); me.from_pydata([to_bl(v) for v in V], [], [(0, 1, 2, 3)]); uvl = me.uv_layers.new()
        for li, uv in enumerate(uvq): uvl.data[li].uv = uv
        me.materials.append(m); ob = bpy.data.objects.new('Blueprint_' + view, me); bpc.objects.link(ob)
        ob.hide_render = True; ob.hide_select = True
    for im_ in bpy.data.images:
        if im_.source == 'FILE' and im_.packed_file is None:
            try: im_.pack()
            except Exception: pass
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'brz_lowpoly.blend'), compress=True)
    use_principled(True)
    for o in bpy.data.objects: o.select_set(o in car_obs)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'brz_lowpoly.glb'), export_format='GLB', use_selection=True)
    bpy.ops.wm.obj_export(filepath=os.path.join(HERE, 'brz_lowpoly.obj'), export_selected_objects=True, export_materials=True,
                          path_mode='STRIP', forward_axis='NEGATIVE_Z', up_axis='Y')
    bpy.ops.export_scene.fbx(filepath=os.path.join(HERE, 'brz_lowpoly.fbx'), use_selection=True, path_mode='COPY', embed_textures=True)
    use_principled(False)
print('DETAIL BUILD DONE')
