"""Shared LEAN rebuild kit for the S2000 and BRZ (inside Blender 4.2).
The approved car (its .blend, built from the blueprint) is the shape source: every lean section is re-sampled from it
by 'star' rays in the station plane (outermost surface along each fixed angle from a smooth centre line), so the lean
loft inherits the blueprint-fitted shape with far fewer, evenly faired rows.  Detail is moved into texture by a
Cycles selected-to-active DIFFUSE-colour bake from the original textured meshes, times a light AO bake, then
RGB555 + 4x4 Bayer.  Rig = Godot VehicleBody3D / VehicleWheel3D naming (see README 'Godot setup').
Frame helpers: FR.to_bl(car xyz) -> Blender Vector, FR.to_car(Blender) -> car (x fwd, y left, z up)."""
import bpy, bmesh, math, os, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

class Frame:
    def __init__(self, kind):
        self.kind = kind                       # 'xfwd' (S2000: Blender = car) | 'xleft' (BRZ/WRX: X = left, -Y = fwd)
    def to_bl(self, p):
        return Vector((p[0], p[1], p[2])) if self.kind == 'xfwd' else Vector((p[1], -p[0], p[2]))
    def to_car(self, v):
        return (v[0], v[1], v[2]) if self.kind == 'xfwd' else (-v[1], v[0], v[2])
    def axle_bl(self):                         # wheel spin axis (car y) in Blender
        return 'Y' if self.kind == 'xfwd' else 'X'

# ------------------------------------------------------------------ BVH of the approved shape
def target_bvh(objs, min_island=0.6):
    """BVH of the given objects (world space) without small loose islands (mirrors, badges, decals): those would
    put bumps into the sections; they are rebuilt / painted instead.  Also returns per-face material names."""
    bm = bmesh.new(); names = []
    for ob in objs:
        b = bmesh.new(); b.from_mesh(ob.data); b.transform(ob.matrix_world)
        b.verts.ensure_lookup_table(); seen = set(); drop = set()
        for v in b.verts:
            if v.index in seen: continue
            st = [v]; isl = []; seen.add(v.index)
            while st:
                a = st.pop(); isl.append(a)
                for e in a.link_edges:
                    o = e.other_vert(a)
                    if o.index not in seen: seen.add(o.index); st.append(o)
            co = np.array([a.co[:] for a in isl])
            if np.linalg.norm(co.max(0) - co.min(0)) < min_island: drop.update(a.index for a in isl)
        bmesh.ops.delete(b, geom=[v for v in b.verts if v.index in drop], context='VERTS')
        mats = [s.material.name if s.material else '' for s in ob.material_slots]
        names += [mats[f.material_index] if f.material_index < len(mats) else '' for f in b.faces]
        me = bpy.data.meshes.new('_tmp'); b.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me); b.free()
    bm.faces.ensure_lookup_table()
    return BVHTree.FromBMesh(bm), names, bm

def star_grid(FR, bvh, X, ANG, zc_of, R=4.0, open_bottom=False):
    """P[s, k] = outermost hit (car frame) on the ray from C=(x,0,zc) at angle ANG[k] (deg, -90 = down, +90 = up,
    0 = straight out to +y).  Misses are filled from the neighbouring angles' radius."""
    P = np.zeros((len(X), len(ANG), 3)); ok = np.zeros((len(X), len(ANG)), bool)
    for s, x in enumerate(X):
        zc = zc_of(x)
        for k, a in enumerate(ANG):
            d = np.array([0.0, math.cos(math.radians(a)), math.sin(math.radians(a))])
            c = np.array([x, 0.0, zc]); far = c + R * d
            h = bvh.ray_cast(FR.to_bl(far), FR.to_bl(-d) - FR.to_bl((0, 0, 0)), R + 0.01)
            if h[0] is not None: P[s, k] = FR.to_car(h[0]); ok[s, k] = True
        r = np.linalg.norm(P[s, :, 1:] - np.array([0, zc]), axis=1)
        if not ok[s].all():
            if ok[s].any():
                kk = np.where(ok[s])[0]; r = np.interp(np.arange(len(ANG)), kk, r[kk])
            else: r = np.full(len(ANG), 0.01)
            for k in np.where(~ok[s])[0]:
                a = math.radians(ANG[k]); P[s, k] = (x, r[k] * math.cos(a), zc + r[k] * math.sin(a))
        if not open_bottom: P[s, 0, 1] = 0.0
        P[s, -1, 1] = 0.0
    return P, ok

def centre_line(FR, bvh, xs, ZC, frac=0.3, smooth_n=5):
    """smooth star centre height: ZC clamped inside the y=0 section (vertical rays), gaussian-smoothed along x."""
    zc = []
    for x in xs:
        top = bvh.ray_cast(FR.to_bl((x, 0, 5)), FR.to_bl((0, 0, -1)) - FR.to_bl((0, 0, 0)), 10)
        bot = bvh.ray_cast(FR.to_bl((x, 0, -1)), FR.to_bl((0, 0, 1)) - FR.to_bl((0, 0, 0)), 10)
        if top[0] is None or bot[0] is None: zc.append(np.nan); continue
        zt, zb = top[0].z, bot[0].z; h = zt - zb
        zc.append(min(max(ZC, zb + frac * h), zt - frac * h))
    zc = np.array(zc); good = ~np.isnan(zc); zc = np.interp(xs, np.array(xs)[good], zc[good])
    k = np.exp(-0.5 * (np.arange(-3 * smooth_n, 3 * smooth_n + 1) / smooth_n) ** 2); k /= k.sum()
    zp = np.pad(zc, 3 * smooth_n, mode='edge'); zs = np.convolve(zp, k, 'valid')
    return lambda x: float(np.interp(x, xs, zs))

def raise_wells(P, X, arches, tire_r, r_well, edge_keep=0.03):
    """inside each arch, points on the arch roof that are inboard of the side skin go up to the wheel-well radius
    (tyre radius + bump + margin), so full bump clears; the outer arch edge (side silhouette) is kept."""
    for s, x in enumerate(X):
        for a in arches:
            dx = x - a['xc']
            if abs(dx) >= r_well: continue
            zw = a['zc'] + math.sqrt(r_well ** 2 - dx ** 2)
            ymax = P[s, :, 1].max()
            for k in range(P.shape[1]):
                y, z = P[s, k, 1], P[s, k, 2]
                if z < zw and y < ymax - edge_keep and z > a['zc'] - 0.02 and abs(dx) < a['r'] + 0.01: P[s, k, 2] = zw
    return P

def loft_mesh(FR, P, name, caps=True):
    """mirrored ring loft from half sections P[s, k] (k: bottom centre .. top centre)."""
    S, K, _ = P.shape; bm = bmesh.new(); rings = []
    for s in range(S):
        half = [P[s, k] for k in range(K)]
        full = half + [np.array((p[0], -p[1], p[2])) for p in half[-2:0:-1]]
        rings.append([bm.verts.new(FR.to_bl(p)) for p in full])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if caps:
        for r in (rings[0], rings[-1]):
            f = bm.faces.new(r)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0005)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    return bm

def obj_from_bm(name, bm, mats, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    ob.parent = parent; return ob

def smooth(ob, angle=45):
    for p in ob.data.polygons: p.use_smooth = True
    try: ob.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception: pass

def empty(name, loc, parent=None, size=0.12, kind='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    bpy.context.collection.objects.link(e); e.parent = parent; e.location = loc; return e

def tube(FR, name, rings, mats, parent=None, cap=(True, True), angle=40):
    bm = bmesh.new(); R = [[bm.verts.new(FR.to_bl(p)) for p in r] for r in rings]; n = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if cap[0]: bm.faces.new(R[0])
    if cap[1]: bm.faces.new(R[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = obj_from_bm(name, bm, mats, parent); smooth(ob, angle); return ob

def liner(FR, name, xc, zc, side, R, yin, yout, mats, parent=None, seg=5):
    """arch tunnel (seg segments) + inner wall, radius about the static hub (5 segs: 14 tris, 7 segs: 20 tris)."""
    ang = np.radians(np.linspace(-8, 188, seg + 1)); bm = bmesh.new()
    o = [bm.verts.new(FR.to_bl((xc + R * math.cos(a), side * yout, zc + R * math.sin(a)))) for a in ang]
    i = [bm.verts.new(FR.to_bl((xc + R * math.cos(a), side * yin, zc + R * math.sin(a)))) for a in ang]
    for k in range(len(ang) - 1): bm.faces.new((o[k], o[k + 1], i[k + 1], i[k]))
    bm.faces.new(i[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return obj_from_bm(name, bm, mats, parent)

def susp(FR, name, mat, parent, side, front):
    """strut (4-sided, open ends) + lower arm (4-sided beam): 16 tris, hub-frame geometry, inboard of the tyre."""
    bm = bmesh.new()
    def beam(p0, p1, w, t):
        p0, p1 = FR.to_bl(p0) - FR.to_bl((0, 0, 0)), FR.to_bl(p1) - FR.to_bl((0, 0, 0))
        d = (p1 - p0).normalized(); up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else (FR.to_bl((1, 0, 0)) - FR.to_bl((0, 0, 0)))
        a = d.cross(up).normalized() * w; b = d.cross(a).normalized() * t
        R0 = [bm.verts.new(p0 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        R1 = [bm.verts.new(p1 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for k in range(4): bm.faces.new((R0[k], R0[(k + 1) % 4], R1[(k + 1) % 4], R1[k]))
    ins = -side
    beam((0.0, ins * 0.19, 0.0), (0.0, ins * 0.17, 0.30 if front else 0.27), 0.035, 0.035)
    beam((0.0, ins * 0.17, -0.13), (0.0, ins * 0.47, -0.12), 0.06, 0.012)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(name, bm, [mat], parent)

def wheel(FR, name, mat, parent, side, r, w, uv_disc, uv_tread, dark_uv, seg=10, mats=None, inner_uv=None, phase_deg=90.0):
    """10-sided wheel: tread quads + outer/inner caps.  Origin = hub.  uv_disc = (u0,v0,u1,v1) tile for the painted
    sidewall+rim disc; uv_tread tile for the tread strip; inner cap -> dark_uv."""
    h = w / 2; bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    ax = lambda t, c, s_: FR.to_bl((c, t, s_)) - FR.to_bl((0, 0, 0))     # car (x=c, y=t axle, z=s_)
    ro, ri = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg + math.radians(phase_deg)      # phase 90: vertices at the contact patch and top
        ro.append(bm.verts.new(ax(side * h, r * math.cos(a), r * math.sin(a))))
        ri.append(bm.verts.new(ax(-side * h, r * math.cos(a), r * math.sin(a))))
    T = uv_tread
    for k in range(seg):
        k1 = (k + 1) % seg; f = bm.faces.new((ro[k], ro[k1], ri[k1], ri[k]))
        u0 = T[0] + (T[2] - T[0]) * k / seg; u1 = T[0] + (T[2] - T[0]) * (k + 1) / seg
        for lp, uv in zip(f.loops, ((u0, T[3]), (u1, T[3]), (u1, T[1]), (u0, T[1]))): lp[uvl].uv = uv
    fo = bm.faces.new(ro); fi = bm.faces.new(ri[::-1])
    U = uv_disc; cu, cv, hu = (U[0] + U[2]) / 2, (U[1] + U[3]) / 2, (U[2] - U[0]) / 2 * 0.985
    for k, lp in enumerate(fo.loops):
        c = FR.to_car(lp.vert.co); lp[uvl].uv = (cu - hu * c[0] / r * side, cv + hu * c[2] / r)   # reads left-to-right from outside, both sides
    for lp in fi.loops: lp[uvl].uv = dark_uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[fo, fi])
    ob = obj_from_bm(name, bm, [mat], parent); smooth(ob, 40); return ob

# ------------------------------------------------------------------ rig
def set_pose(rig, heave=0.0, roll=0.0, pitch=0.0, steer=0.0, wheel_dz=None):
    """body origin at the COM estimate; hubs move in the root frame; Susp_XX = hub position + steer (never spin)."""
    FR = rig['FR']; body = rig['body']; cx, cz = rig['com']; body.location = FR.to_bl((cx, 0, cz + heave))
    # pitch: nose down positive; roll: right side down positive (car frame) -> Blender euler
    if FR.kind == 'xfwd': body.rotation_euler = (math.radians(roll), math.radians(pitch), 0)
    else: body.rotation_euler = (math.radians(-pitch), math.radians(-roll), 0)
    for k, st in rig['steer'].items(): st.rotation_euler = (0, 0, math.radians(steer))
    for k, hb in rig['hub'].items(): hb.location = Vector(rig['hub_rest'][k]) + Vector((0, 0, (wheel_dz or {}).get(k, 0.0)))
    for k, sp in rig['susp'].items():
        sp.location = rig['hub'][k].location; sp.rotation_euler = (0, 0, math.radians(steer) if k[0] == 'F' else 0.0)
    bpy.context.view_layer.update()
def rel_travel(rig):
    body = rig['body']; inv = body.matrix_world.inverted(); out = {}
    for k, hb in rig['hub'].items(): out[k] = round((inv @ hb.matrix_world.translation).z - rig['hub_body_rest'][k], 4)
    return out

def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); bm.from_object(ob, dg); bm.transform(ob.matrix_world)
    t = BVHTree.FromBMesh(bm); verts = [v.co.copy() for v in bm.verts]; bm.free(); return t, verts
def clearance(rig, prefix, static, BUMP, DROOP, LOCK):
    """9 poses (lock -,0,+ x bump/static/droop), every corner: tyre vs mono body (BVH overlap + min vertex gap)."""
    rep = {'spec': dict(bump=BUMP, droop=DROOP, lock_deg=LOCK), 'poses': []}; worst = None; wf = None
    for st in (-LOCK, 0.0, LOCK):
        for dz in (BUMP, 0.0, -DROOP):
            name = f'steer {st:+.0f} deg, travel {dz:+.3f}'
            set_pose(rig, steer=st, wheel_dz={k: dz for k in ('FL', 'FR', 'RL', 'RR')})
            stat = {n: bvh_of(bpy.data.objects[n])[0] for n in static}
            row = {'pose': name, 'corners': {}}
            for k in ('FL', 'FR', 'RL', 'RR'):
                tw, tv = bvh_of(bpy.data.objects[f'{prefix}_Wheel_{k}'])
                hits = {n: len(tw.overlap(t)) for n, t in stat.items()}; hits = {n: c for n, c in hits.items() if c}
                dmin = 9.0; who = ''
                for n, t in stat.items():
                    for v in tv:
                        r = t.find_nearest(v, 0.3)
                        if r[0] is not None and r[3] < dmin: dmin, who = r[3], n
                row['corners'][k] = dict(overlaps=hits, min_gap_m=round(dmin, 4), nearest=who)
                if worst is None or dmin < worst[0]: worst = (dmin, name, k, who)
                if k[0] == 'F' and (wf is None or dmin < wf[0]): wf = (dmin, name, k, who)
            rep['poses'].append(row)
    rep['all_clear'] = all(not c['overlaps'] for r in rep['poses'] for c in r['corners'].values())
    rep['tightest'] = dict(gap_m=round(worst[0], 4), pose=worst[1], corner=worst[2], against=worst[3])
    rep['tightest_front'] = dict(gap_m=round(wf[0], 4), pose=wf[1], corner=wf[2], against=wf[3])
    set_pose(rig); print('CLEARANCE all_clear', rep['all_clear'], rep['tightest'])
    for r in rep['poses']:
        bad = {k: c['overlaps'] for k, c in r['corners'].items() if c['overlaps']}
        if bad: print('   OVERLAP', r['pose'], bad)
    return rep

# ------------------------------------------------------------------ texture: bake original -> lean
def principled_sources(on=True):
    """fake-shine (emission) materials -> Principled output so a DIFFUSE colour bake reads their albedo."""
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nd = m.node_tree.nodes
        if 'FAKESHINE' in nd and 'Principled BSDF' in nd:
            m.node_tree.links.new(nd['Principled BSDF' if on else 'FAKESHINE'].outputs[0], nd['Material Output'].inputs['Surface'])
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5
def rgb555_bayer(a):          # a: float 0..1 (H, W, 3) -> uint8, 5 bits/channel with 4x4 ordered dither
    H, W, _ = a.shape; t = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
    q = np.clip(np.floor(a * 31 + 0.5 + t * 0.9), 0, 31); return (q * 255 / 31).astype(np.uint8)
def bake_lean(lean, sources, out_dir, tag, TS=1024, extrusion=0.035, ray=0.09, ao_mix=0.30):
    """UV (smart project) -> DIFFUSE colour bake from the approved textured meshes (selected-to-active) -> AO bake
    (lean mesh + wheels) -> albedo * (1 - ao_mix + ao_mix * AO) -> RGB555 + Bayer -> png.  Returns png path."""
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = lean; lean.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.006, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
    if sc.world is None: sc.world = bpy.data.worlds.new('BakeWorld')
    sc.world.light_settings.distance = 0.30
    col = bpy.data.images.new(tag + '_COL', TS, TS, alpha=False); ao = bpy.data.images.new(tag + '_AO', TS, TS, alpha=False)
    tmp = []
    def target(img):
        for nt_, n_ in tmp: nt_.nodes.remove(n_)
        tmp.clear()
        for sl in lean.material_slots:
            nt_ = sl.material.node_tree; n_ = nt_.nodes.new('ShaderNodeTexImage'); n_.image = img; nt_.nodes.active = n_; tmp.append((nt_, n_))
    bk = sc.render.bake; bk.margin = 6; bk.margin_type = 'EXTEND'
    principled_sources(True)
    target(col)
    for o in sources: o.hide_render = False; o.select_set(True)
    lean.select_set(True); bpy.context.view_layer.objects.active = lean
    bk.use_selected_to_active = True; bk.cage_extrusion = extrusion; bk.max_ray_distance = ray
    bk.use_pass_direct = False; bk.use_pass_indirect = False; bk.use_pass_color = True
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True)
    for o in sources: o.select_set(False)
    principled_sources(False)
    hidden = [o for o in sources if not o.hide_render]
    for o in hidden: o.hide_render = True
    bk.use_selected_to_active = False; target(ao); sc.cycles.samples = 48
    bpy.ops.object.bake(type='AO', use_clear=True)
    for o in hidden: o.hide_render = False
    target(col); tmp and [nt_.nodes.remove(n_) for nt_, n_ in tmp]; tmp.clear()
    c = np.array(col.pixels[:], np.float32).reshape(TS, TS, 4)[..., :3]; a = np.array(ao.pixels[:], np.float32).reshape(TS, TS, 4)[..., :1]
    def srgb(x): return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, 1), 1 / 2.4) - 0.055)
    lin = c * (1 - ao_mix + ao_mix * a)
    q = rgb555_bayer(srgb(lin))             # quantise in display space
    os.makedirs(out_dir, exist_ok=True)
    for img, nm in ((col, 'bake_colour'), (ao, 'bake_ao')):
        img.filepath_raw = os.path.join(out_dir, f'{tag}_{nm}.png'); img.file_format = 'PNG'; img.save()
    outp = os.path.join(out_dir, f'{tag}_body.png')
    im = bpy.data.images.new(tag + '_BODY', TS, TS, alpha=False)
    lin_q = np.where(q / 255.0 <= 0.04045, q / 255.0 / 12.92, ((q / 255.0 + 0.055) / 1.055) ** 2.4)
    im.pixels[:] = np.concatenate([lin_q, np.ones((TS, TS, 1))], 2).astype(np.float32).ravel()
    im.filepath_raw = outp; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im); bpy.data.images.remove(col); bpy.data.images.remove(ao)
    return outp

def classify_faces(FR, ob, bvh, names, rules, default=0):
    """material index per lean face from the nearest approved-mesh face's material name (rules: [(substr, idx)])."""
    mw = ob.matrix_world
    for p in ob.data.polygons:
        c = mw @ p.center; r = bvh.find_nearest(c, 0.25); idx = default
        if r[0] is not None:
            nm = names[r[2]]
            for sub, i in rules:
                if sub in nm: idx = i; break
        p.material_index = idx

def tri_soup(FR, objs):
    T = []
    for ob in objs:
        ob.data.calc_loop_triangles(); mw = ob.matrix_world
        for t in ob.data.loop_triangles: T.append([list(FR.to_car(mw @ ob.data.vertices[i].co)) for i in t.vertices])
    return np.array(T, np.float32)

def feature_grid(FR, bvh, X, zc_of, anchors, fill, R=4.0, sigma=0.12, step=1.0, a_lo=-90.0, start_at_first_hit=False):
    """feature-anchored star sections.  anchors: list of support directions (uy, uz) (car frame, y>=0 half) - or
    callables f(yz_points, angles, hit_mask, x) -> angle - giving an anchor ANGLE per station on the dense (step-deg)
    star scan; anchor angles are smoothed along x (gaussian, sigma m) so the rows stay fair; fill[i] evenly spaced
    extra angles between consecutive anchors.  Sections run from a_lo (default -90 = bottom centre; or the first
    hit angle if start_at_first_hit, for open shells like a soft top) to +90 (top centre).  Returns P[s,k], ANG, A."""
    dense = np.arange(a_lo, 90.001, step)
    D, ok = star_grid(FR, bvh, X, list(dense), zc_of, R, start_at_first_hit)
    nA = len(anchors) + (1 if start_at_first_hit else 0)
    A = np.zeros((len(X), nA))
    for s in range(len(X)):
        yz = D[s, :, 1:]; hit = ok[s]; j0 = 0
        if start_at_first_hit:
            A[s, 0] = dense[np.argmax(hit)] if hit.any() else 90.0; j0 = 1
        for j, u in enumerate(anchors):
            if callable(u): A[s, j0 + j] = u(yz, dense, hit, X[s])
            else:
                sc = yz @ np.array(u); sc[~hit] = -9
                A[s, j0 + j] = dense[int(np.argmax(sc))]
    As = A.copy()
    for s in range(len(X)):
        w = np.exp(-0.5 * ((X - X[s]) / sigma) ** 2); As[s] = (w[:, None] * A).sum(0) / w.sum()
    rows = []
    for s in range(len(X)):
        if start_at_first_hit: a = [As[s, 0]] + sorted(np.clip(As[s, 1:], As[s, 0] + 1, 88)) + [90.0]
        else: a = [-90.0] + sorted(np.clip(As[s], -88, 88)) + [90.0]
        ang = []
        for i in range(len(a) - 1):
            n = fill[i] if i < len(fill) else 0
            ang += list(np.linspace(a[i], a[i + 1], n + 2)[:-1])
        ang.append(90.0); rows.append(ang)
    ANG = np.array(rows)
    P = np.zeros((len(X), ANG.shape[1], 3)); OK = np.zeros((len(X), ANG.shape[1]), bool)
    for s in range(len(X)):
        Ps, oks = star_grid(FR, bvh, [X[s]], list(ANG[s]), zc_of, R, start_at_first_hit); P[s] = Ps[0]; OK[s] = oks[0]
    return P, ANG, A, OK

def strip_mesh(FR, P):
    """open mirrored strip loft (no bottom, no caps): half sections from the side edge (k=0) to top centre."""
    S, K, _ = P.shape; bm = bmesh.new(); rings = []
    for s in range(S):
        half = [P[s, k] for k in range(K)]
        full = half + [np.array((p[0], -p[1], p[2])) for p in half[-2::-1]]
        rings.append([bm.verts.new(FR.to_bl(p)) for p in full])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n - 1): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0005)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.0005)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    return bm

def fair_rows(P, X, zc_of, protect=None, dent=0.010, passes=1):
    """row fairing in star (radius) space: a station whose radius dips more than `dent` below the mean of its two
    neighbours (a ray that fell into an intake / shut gap of the approved mesh) is lifted to that mean; then one
    [1/4, 1/2, 1/4] pass on interior stations (not the first/last two, not where protect(s, k) is True).
    Angles are preserved, so the rows stay on their rays."""
    S, K, _ = P.shape; Q = P.copy()
    C = np.array([[x, 0.0, zc_of(x)] for x in X])
    for k in range(K):
        d = Q[:, k, 1:] - C[:, None, 1:][:, 0]; r = np.linalg.norm(d, axis=1); u = d / np.maximum(r[:, None], 1e-9)
        r2 = r.copy()
        for s in range(1, S - 1):
            if protect is not None and protect(s, k): continue
            m = 0.5 * (r[s - 1] + r[s + 1])
            if m - r[s] > dent: r2[s] = m
        r3 = r2.copy()
        for _ in range(passes):
            for s in range(2, S - 2):
                if protect is not None and (protect(s, k) or protect(s - 1, k) or protect(s + 1, k)): continue
                r3[s] = 0.25 * r2[s - 1] + 0.5 * r2[s] + 0.25 * r2[s + 1]
            r2 = r3.copy()
        Q[:, k, 1:] = C[:, None, 1:][:, 0] + u * r2[:, None]
    return Q

def conjugate_rig(root, M):
    """Re-express a whole rig in rotated axes WITHOUT putting a rotation on any node: every child's local matrices are
    conjugated (M L M^-1) and mesh data is rotated by M, so the root stays identity and the hubs/steer/susp empties stay
    un-rotated.  Used to export the S2000 (built X-forward) with the same Godot axes as the WRX/BRZ (+Z forward, +X
    left).  Call again with M.inverted() to undo."""
    Mi = M.inverted(); done = set()
    def walk(o):
        for c in o.children:
            c.matrix_parent_inverse = M @ c.matrix_parent_inverse @ Mi
            c.matrix_basis = M @ c.matrix_basis @ Mi
            if c.type == 'MESH' and c.data.name not in done: c.data.transform(M); done.add(c.data.name)
            walk(c)
    walk(root); bpy.context.view_layer.update()
