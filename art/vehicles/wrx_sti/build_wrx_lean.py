"""WRX STI LEAN build: <= 2,000 triangles TOTAL (everything rendered: body, aero, mirrors, liners, underbody,
suspension, wheels).  Detail lives in the painted 1024^2 body texture + 256^2 wheel atlas, not in geometry.
Blueprint-only (same faired curves as clay pass 2); the pass-2 clay build (build_wrx.py, wrx_clay.*) is untouched.
  python3 bp/vectorize.py                                  # blueprint features -> vectors for the painter
  blender -b --factory-startup -P build_wrx_lean.py -- [--render]
  WRX_OUT=lean python3 bp/bpcompare.py && python3 bp/deliver_lean.py
or:  python3 make_lean.py
Outputs in lean/: wrx_lean.blend, wrx_lean.glb, tri_count.txt, bp/ (tris soup, iou, clearance, pose meta),
tex/ (body + wheel textures, AO), renders/.
Rig (Godot VehicleBody3D / VehicleWheel3D): WRX-vehicle (root, ground, mid-wheelbase)
  +- WRX_Body           ONE mesh (body, cabin, scoop, wing, lip, mirrors, liners, floor), origin at the centre of
  |                     mass estimate (x 0, z .50) at ride height
  +- Hub_FL-wheel ...   empties at the static hub centre (Godot VehicleWheel3D)
       +- Steer_FL/FR   front only, rotates about local Z (vertical axis through the hub)
            +- WRX_Wheel_FL   10-sided wheel, origin = hub, spins about local X
  +- Susp_FL ...        empties, siblings of the hubs: follow the hub POSITION (travel) and, front only, the STEER
       |                angle about Z - never the wheel spin (Godot: VehicleWheel3D spins its own node, so the struts
       |                cannot live under it; see lean/README.md 'Godot setup' + lean/godot/susp_follow.gd)
       +- WRX_Susp_FL   strut + lower arm (16 tris), hub-frame geometry"""
import bpy, bmesh, sys, os, math, importlib, json, subprocess, shutil
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, 'parts')); sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np
import build_wrx as W                                   # helpers only (main() is guarded)
import wrx_bp as B, wrx_geo as G, wrx_geo_lean as GL, psx_mat as PM, clearance as CL, lamps_lean as LAMP
for m in (GL, PM, CL, LAMP): importlib.reload(m)
OUT = os.path.join(HERE, 'lean'); os.makedirs(os.path.join(OUT, 'bp'), exist_ok=True); os.makedirs(os.path.join(OUT, 'tex'), exist_ok=True)
PY3 = shutil.which('python3') or '/usr/bin/python3'; TS = 1024
to_bl, car, loft, mat, obj_from_bm, smooth, empty = W.to_bl, W.car, W.loft, W.mat, W.obj_from_bm, W.smooth, W.empty
BUMP, DROOP, LOCK, ROLL = W.BUMP, W.DROOP, W.LOCK, W.ROLL
ZCOM = 0.50
CAP = 2000

# ---------------------------------------------------------------- body + cabin lofts
def mark_sharp(bm, vv, col, s0, s1):
    C = len(vv[0])
    for cc_ in (col, C - 1 - col):
        for s_ in range(max(s0, 0), min(s1, len(vv) - 1)):
            e = bm.edges.get((vv[s_][cc_], vv[s_ + 1][cc_]))
            if e: e.smooth = False
def build_body(M):
    X = GL.stations(); secs = [GL.lower_section(x) for x in X]
    bm = bmesh.new(); vv, F = loft(bm, secs, X); C = len(vv[0]); S_ = len(X)
    for s in range(S_ - 1):      # floor plates only under the overhangs (as pass 2)
        if not (min(X[s], X[s + 1]) > B.ARCH_F['x1'] or max(X[s], X[s + 1]) < B.ARCH_R['x0']): continue
        F.append((bm.faces.new((vv[s][0], vv[s][C - 1], vv[s + 1][C - 1], vv[s + 1][0])), s, -1))
    for s, rev in ((0, False), (S_ - 1, True)):
        ring = vv[s][:]; ring = ring[::-1] if rev else ring; F.append((bm.faces.new(ring), s, -2))
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _, _ in F])
    for f, s, c in F: f.material_index = 2 if c == -1 else 0
    idx = lambda x: int(np.argmin(np.abs(X - x)))
    ish = len(GL.T_SIDE) - 1
    mark_sharp(bm, vv, ish, idx(2.0), idx(G.XWS)); mark_sharp(bm, vv, ish, idx(G.XRG), idx(-2.06)); mark_sharp(bm, vv, 1, idx(0.85), idx(-0.86))
    W.QC['body'] = W.face_check(bm, [f for f, s, c in F if c >= 0 and f.is_valid])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = obj_from_bm('WRX_Body', bm, [M['paint'], M['glass'], M['under'], M['paint'], M['trim']]); smooth(ob, 45); return ob
def build_cabin(M, body):
    X = GL.cabin_stations(); secs = [GL.cabin_section(x) for x in X]
    bm = bmesh.new(); vv, F = loft(bm, secs, X)
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _, _ in F])
    NPn = secs[0].shape[0]; C_ = 2 * NPn - 1
    GLS = B.GLASS; tws = [r for r in B.D['top_glass_regions'] if r['n'] > 5000]
    def in_x(x, r, m=0.0): return r['x'][0] - m <= x <= r['x'][1] + m
    for f, s, c in F:          # strip 0 belt->glass bottom (paint), 1 side glass, 2 roof rail, 3-4 roof
        i = c if c < NPn - 1 else C_ - 2 - c; x = car(f.calc_center_median())[0]; m = 0
        if i == 1:
            if any(in_x(x, GLS[k]) for k in GLS): m = 1
            else: m = 4                                                       # B-pillar / sash: black (painted trim)
        elif i >= 3 or (i == 2 and x > 0.6):
            if any(in_x(x, r, -0.02) for r in tws): m = 1
        f.material_index = m
    mark_sharp(bm, vv, 2, 0, len(X)); mark_sharp(bm, vv, 3, 0, len(X))
    W.QC['cabin'] = W.face_check(bm, [f for f, s, c in F if f.is_valid])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = obj_from_bm('WRX_Cabin', bm, [M['paint'], M['glass'], M['under'], M['paint'], M['trim']], body); smooth(ob, 50); return ob

# ---------------------------------------------------------------- small parts (minimal)
def tube(name, rings, mats, parent, mi=None, cap=(True, True), angle=40):
    bm = bmesh.new(); R = [[bm.verts.new(to_bl(p)) for p in r] for r in rings]; n = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if cap[0]: bm.faces.new(R[0])
    if cap[1]: bm.faces.new(R[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if mi:
        for f in bm.faces: f.material_index = mi(f)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    ob = obj_from_bm(name, bm, mats, parent); smooth(ob, angle); return ob
def build_scoop(M, body):
    """STI bonnet scoop (estimated, as pass 2): 3 rings x 4 points; mouth = painted black (trim slot)."""
    x1, x0, yb, yt, h = 1.515, 1.19, 0.34, 0.26, 0.088
    rings = []
    for x, hh in zip((x1, 1.37, x0), (h, h * 0.7, 0.004)):
        zh = G.ZTB(x) - 0.004; rings.append([(x, -yb, zh), (x, -yt, zh + hh), (x, yt, zh + hh), (x, yb, zh)])
    def mi(f): c = car(f.calc_center_median()); return 4 if c[0] > x1 - 0.003 and -f.normal.y > 0.7 else 0
    return tube('STI_Scoop', rings, [M['paint'], M['glass'], M['under'], M['paint'], M['trim']], body, mi, (True, False))
def build_wing(M, body):
    """STI pedestal wing (estimated, as pass 2): blade 3 rings x 4 + two 4-sided uprights."""
    def blade(y, dz=0.0): return [(-1.87, y, 1.212 + dz), (-1.93, y, 1.238 + dz), (-2.14, y, 1.258 + dz), (-2.12, y, 1.222 + dz)]
    ob = tube('STI_Wing', [blade(-0.70, 0.02), blade(0.0), blade(0.70, 0.02)], [M['paint'], M['glass'], M['under'], M['paint'], M['trim']], body, None, (True, True), 35)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for ys in (-0.52, 0.52):
        loops = [[bm.verts.new(to_bl(p)) for p in ((x0, ys - w, z), (x1, ys - w, z), (x1, ys + w, z), (x0, ys + w, z))]
                 for x0, x1, z, w in ((-1.96, -2.06, G.ZTB(-2.0) - 0.004, 0.022), (-1.95, -2.03, 1.214, 0.016))]
        a, b = loops
        for k in range(4): bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free(); return ob
def build_lip(M, body):
    """STI front lip (estimated): one angled strip under the bumper, 7 points across, painted black."""
    X = [x for x in GL.stations() if x > 1.70 and G.ZB(x) <= 0.265]          # stations whose bumper bottom is low
    ys = np.linspace(0.0, 0.80, 4)
    xs = [max([x for x in X if GL.lower_section(x)[0, 0] >= y - 0.02] or [1.75]) for y in ys]
    full = [(x, -y) for x, y in list(zip(xs, ys))[::-1]] + list(zip(xs, ys))[1:]
    bm = bmesh.new()
    top = [bm.verts.new(to_bl((x - 0.03, y, 0.240))) for x, y in full]
    bot = [bm.verts.new(to_bl((x + 0.01, y, 0.205))) for x, y in full]
    for k in range(len(full) - 1): bm.faces.new((top[k], top[k + 1], bot[k + 1], bot[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.y > 0: f.normal_flip()          # face forward (-Y blender)
        f.material_index = 4
    return obj_from_bm('STI_FrontLip', bm, [M['paint'], M['glass'], M['under'], M['paint'], M['trim']], body)
def build_mirror(name, s, M, body):
    """minimal door mirror: tapered 8-vert box (12 tris), blueprint x .84-1.04, z .93-1.05, out to y .97; black."""
    r0 = [(1.03, s * 0.80, 0.95), (1.03, s * 0.80, 1.00), (1.03, s * 0.86, 1.00), (1.03, s * 0.86, 0.95)]
    r1 = [(0.88, s * 0.80, 0.93), (0.88, s * 0.80, 1.05), (0.88, s * 0.97, 1.05), (0.88, s * 0.97, 0.93)]
    return tube(name, [r0, r1], [M['trim']], body, None, (True, True), 30)
def build_liner(name, xc, side, front, M, body):
    """arch tunnel (5 segments) + inner wall (14 tris), radius about the static hub, sized for bump + lock."""
    R = W.LINER_R_F if front else W.LINER_R_R; yin = W.LINER_YIN_F if front else W.LINER_YIN_R; yout = 0.80
    ang = np.radians(np.linspace(-8, 188, 6)); bm = bmesh.new()
    o = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yout, G.HUB_Z + R * math.sin(a)))) for a in ang]
    i = [bm.verts.new(to_bl((xc + R * math.cos(a), side * yin, G.HUB_Z + R * math.sin(a)))) for a in ang]
    for k in range(len(ang) - 1): bm.faces.new((o[k], o[k + 1], i[k + 1], i[k]))
    bm.faces.new(i[::-1])                       # inner wall: closes the well (no see-through; blueprint draws it dark)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.normal_flip(); f.material_index = 0
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return obj_from_bm(name, bm, [M['under']], body)
def build_floor(M, body):
    bm = bmesh.new(); v = [bm.verts.new(to_bl(p)) for p in ((1.95, 0.44, 0.30), (1.95, -0.44, 0.30), (-1.95, -0.44, 0.30), (-1.95, 0.44, 0.30))]
    f = bm.faces.new(v); f.normal_update()
    if f.normal.z > 0: f.normal_flip()
    return obj_from_bm('WRX_Under', bm, [M['under']], body)
def build_wheel(name, M, parent, side, seg=10):
    """10-sided wheel: tread (seg quads) + outer and inner caps (n-gons).  Origin = hub, axle = local X.  UV: outer cap
    -> painted disc (tyre sidewall + gold rim) in the wheel atlas, tread -> tread strip; inner cap -> dark."""
    r = G.TIRE_OD / 2; h = G.TIRE_W / 2; bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    ring_o, ring_i = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        ring_o.append(bm.verts.new(Vector((side * h, r * math.cos(a), r * math.sin(a)))))
        ring_i.append(bm.verts.new(Vector((-side * h, r * math.cos(a), r * math.sin(a)))))
    for k in range(seg):
        k1 = (k + 1) % seg; f = bm.faces.new((ring_o[k], ring_o[k1], ring_i[k1], ring_i[k])); f.material_index = 0
        for lp, uv in zip(f.loops, ((0.5 + 0.5 * k / seg, 1.0), (0.5 + 0.5 * (k + 1) / seg, 1.0), (0.5 + 0.5 * (k + 1) / seg, 0.0), (0.5 + 0.5 * k / seg, 0.0))):
            lp[uvl].uv = uv
    fo = bm.faces.new(ring_o); fi = bm.faces.new(ring_i[::-1])
    for lp in fo.loops:
        co = lp.vert.co; lp[uvl].uv = (0.25 + 0.246 * co.y / r * (-side), 0.75 + 0.246 * co.z / r)
    for lp in fi.loops: lp[uvl].uv = (0.49, 0.51)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[fo, fi])
    ob = obj_from_bm(name, bm, [M['wheel']], parent); smooth(ob, 40); return ob
def build_susp(name, M, parent, side, front):
    """strut (4-sided, open ends, 8 tris) + lower arm (4-sided beam, 8 tris), in the hub frame (Blender axes: X = car
    left, -Y = car fwd, Z up), inboard of the tyre so it never touches it at any lock (it steers with the wheel)."""
    bm = bmesh.new()
    def beam(p0, p1, w, t):
        p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized(); up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1))
        a = d.cross(up).normalized() * w; b = d.cross(a).normalized() * t
        R0 = [bm.verts.new(p0 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        R1 = [bm.verts.new(p1 + sa * a + sb * b) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for k in range(4): bm.faces.new((R0[k], R0[(k + 1) % 4], R1[(k + 1) % 4], R1[k]))
    ins = -side                                          # toward the car centre (Blender X sign)
    beam((ins * 0.19, 0.0, 0.0), (ins * 0.17, 0.0, 0.30 if front else 0.27), 0.035, 0.035)        # strut / damper
    beam((ins * 0.17, 0.0, -0.13), (ins * 0.47, 0.0, -0.12), 0.06, 0.012)                        # lower arm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = obj_from_bm(name, bm, [M['under']], parent); return ob

# ---------------------------------------------------------------- rig poses (body origin at the COM height)
def set_pose(rig, heave=0.0, roll=0.0, pitch=0.0, steer=0.0, wheel_dz=None):
    body = rig['body']; body.location = (0, 0, ZCOM + heave)
    body.rotation_euler = (math.radians(-pitch), math.radians(-roll), 0)
    for k, st in rig['steer'].items(): st.rotation_euler = (0, 0, math.radians(steer))
    for k, hb in rig['hub'].items(): hb.location = Vector(rig['hub_rest'][k]) + Vector((0, 0, (wheel_dz or {}).get(k, 0.0)))
    for k, sp in rig.get('susp', {}).items():      # strut node: hub position + steer only (no spin)
        sp.location = rig['hub'][k].location; sp.rotation_euler = (0, 0, math.radians(steer) if k[0] == 'F' else 0.0)
    bpy.context.view_layer.update()
def rel_travel(rig):
    body = rig['body']; inv = body.matrix_world.inverted(); out = {}
    for k, hb in rig['hub'].items(): out[k] = round((inv @ hb.matrix_world.translation).z - rig['hub_body_rest'][k], 4)
    return out

# ---------------------------------------------------------------- texture (UV, AO bake, texels, painter)
def run(*a): subprocess.run([PY3, *a], check=True)
def texture_body(body):
    for o in bpy.context.selected_objects: o.select_set(False)
    body.select_set(True); bpy.context.view_layer.objects.active = body
    lamp_slots = [i for i, sl in enumerate(body.material_slots) if sl.material.name == 'clay_lampcap']
    bpy.ops.object.mode_set(mode='OBJECT')
    for p_ in body.data.polygons: p_.select = p_.material_index not in lamp_slots      # lamp caps keep their atlas UVs
    lampv = {v for p_ in body.data.polygons if p_.material_index in lamp_slots for v in p_.vertices}
    for v_ in body.data.vertices: v_.select = v_.index not in lampv
    for e_ in body.data.edges: e_.select = not (e_.vertices[0] in lampv or e_.vertices[1] in lampv)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48
    if sc.world is None: sc.world = bpy.data.worlds.new('BakeWorld')
    sc.world.light_settings.distance = 0.30
    ao_img = bpy.data.images.new('WRX_AO', TS, TS, alpha=False); tmp = []
    dummy = bpy.data.images.new('WRX_AO_lampcap_dummy', 8, 8, alpha=False)
    for i_, sl in enumerate(body.material_slots):
        nt_ = sl.material.node_tree; n_ = nt_.nodes.new('ShaderNodeTexImage'); n_.image = dummy if i_ in lamp_slots else ao_img
        nt_.nodes.active = n_; tmp.append((nt_, n_))
    sc.render.bake.margin = 8; sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='AO', use_clear=True)
    ao_png = os.path.join(OUT, 'tex', 'body_ao.png'); ao_img.filepath_raw = ao_png; ao_img.file_format = 'PNG'; ao_img.save()
    for nt_, n_ in tmp: nt_.nodes.remove(n_)
    bpy.data.images.remove(ao_img); bpy.data.images.remove(dummy)
    me = body.data; me.calc_loop_triangles(); uvd = me.uv_layers.active.data; mw = body.matrix_world
    pos = np.zeros((TS, TS, 3), np.float32); nrm = np.zeros((TS, TS, 3), np.float32); mask = np.full((TS, TS), -1, np.int16)
    cls = {'clay': 0, 'clay_glass': 1, 'under': 2, 'clay_lamp': 3, 'clay_trim': 4}
    slotcls = [cls.get(sl.material.name, 0) for sl in body.material_slots]
    cn = me.corner_normals
    for lt in me.loop_triangles:
        if lt.material_index in lamp_slots: continue
        uv = np.array([uvd[l].uv[:] for l in lt.loops]) * TS - 0.5
        Pv = np.array([car(mw @ me.vertices[v].co) for v in lt.vertices]); Nv = np.array([car(mw.to_3x3() @ cn[l].vector) for l in lt.loops])
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
    npz = os.path.join(OUT, 'tex', 'body_texels.npz'); np.savez_compressed(npz, pos=pos, nrm=nrm, mask=mask)
    body_png = os.path.join(OUT, 'tex', 'wrx_body.png'); run(os.path.join(HERE, 'tex', 'make_body_wrx.py'), npz, body_png, ao_png)
    return body_png

def cut_pocket(body, cutter):
    """light head lamp pocket: exact boolean of the lens-plane prism (parts/lamps_lean.py _pocket) out of the body loft.
    Cutter back cap -> recessed flat lens (clay_lampcap, atlas UVs); cutter sides -> pocket walls (clay_trim, painted
    black + AO).  The UV layer must exist on the body so the lens UVs survive the boolean."""
    if not body.data.uv_layers: body.data.uv_layers.new(name='UVMap')
    n0 = len(body.data.polygons)
    md = body.modifiers.new('pocket', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = cutter
    md.material_mode = 'TRANSFER'; md.use_hole_tolerant = True
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier='pocket')
    bpy.data.objects.remove(cutter, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(body.data); bm.free()
    slots = [sl.material.name for sl in body.material_slots]
    lamp = [i for i, n in enumerate(slots) if n == 'clay_lampcap']
    for p_ in body.data.polygons:
        if p_.material_index in lamp: p_.use_smooth = True          # shallow dish: smooth so the fan facets don't read
    body.data.calc_loop_triangles(); print('POCKET cut: polys', n0, '->', len(body.data.polygons), 'slots', slots)

def main():
    W.reset()
    M = dict(paint=mat('clay', (0.66, 0.66, 0.66), 0.55), glass=mat('clay_glass', (0.16, 0.17, 0.19), 0.3),
             under=mat('under', (0.02, 0.02, 0.02), 1.0), trim=mat('clay_trim', (0.08, 0.08, 0.085), 0.8),
             wheel=mat('clay_wheel', (0.12, 0.12, 0.12), 0.8), lampcap=mat('clay_lampcap', (0.75, 0.77, 0.80), 0.2),
             glow=mat('clay_glow', (1.0, 0.95, 0.85), 1.0))
    root = empty('WRX-vehicle', (0, 0, 0), size=0.5, kind='ARROWS')
    body = build_body(M); body.parent = root
    parts = [build_cabin(M, body), build_scoop(M, body), build_wing(M, body), build_lip(M, body),
             build_mirror('WRX_Mirror_L', 1, M, body), build_mirror('WRX_Mirror_R', -1, M, body), build_floor(M, body)]
    for nm, xc, sd, fr in (('FL', G.AXF, 1, True), ('FR', G.AXF, -1, True), ('RL', G.AXR, 1, False), ('RR', G.AXR, -1, False)):
        parts.append(build_liner('WRX_Liner_' + nm, xc, sd, fr, M, body))
    # head + fog lamp lens caps (joined into the mono body) and the optional head lamp glow quads (separate FX object)
    caps, glow, cutter = LAMP.build(to_bl, car, obj_from_bm, [body], (M['lampcap'], M['glow'], M['lampcap'], M['trim']), os.path.join(OUT, 'tex'), None)
    for c_ in caps: c_.parent = root
    glow.parent = root; parts += caps
    cut_pocket(body, cutter)
    rig = dict(body=body, hub={}, steer={}, hub_rest={}, susp={})
    for nm, xc, yc in (('FL', G.AXF, G.TRACK_F / 2), ('FR', G.AXF, -G.TRACK_F / 2), ('RL', G.AXR, G.TRACK_R / 2), ('RR', G.AXR, -G.TRACK_R / 2)):
        loc = to_bl((xc, yc, G.HUB_Z)); hb = empty(f'Hub_{nm}-wheel', loc, root, 0.2, 'ARROWS'); rig['hub'][nm] = hb; rig['hub_rest'][nm] = tuple(loc)
        par = hb
        if nm[0] == 'F': st = empty(f'Steer_{nm}', (0, 0, 0), hb, 0.25, 'SINGLE_ARROW'); rig['steer'][nm] = st; par = st
        sd = 1 if yc > 0 else -1
        sp = empty(f'Susp_{nm}', loc, root, 0.15, 'PLAIN_AXES'); rig['susp'][nm] = sp
        build_wheel('WRX_Wheel_' + nm, M, par, sd); build_susp('WRX_Susp_' + nm, M, sp, sd, nm[0] == 'F')
    bpy.context.view_layer.update()
    # tri counts (per part, before the join)
    lines = []; tot = 0
    for ob in sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name):
        ob.data.calc_loop_triangles(); n = len(ob.data.loop_triangles); tot += n; lines.append(f'{ob.name:16s} {n:5d}')
    # triangle soup (rest pose, car frame) for the IoU sets
    T = []; TO = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name.startswith('WRX_Susp_') or ob.name.startswith('WRX_FX_'): continue
        me = ob.data; mw = ob.matrix_world
        for t in me.loop_triangles: T.append([list(car(mw @ me.vertices[i].co)) for i in t.vertices]); TO.append(ob.name)
    np.save(os.path.join(OUT, 'bp', 'tris_carframe.npy'), np.array(T, np.float32)); np.save(os.path.join(OUT, 'bp', 'tris_object.npy'), np.array(TO))
    # mono body: join, then move the origin to the COM estimate (x 0, z .50) at ride height
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in parts: o.select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    body.data.transform(Matrix.Translation((0, 0, -ZCOM))); body.location = (0, 0, ZCOM); bpy.context.view_layer.update()
    rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
    body.data.calc_loop_triangles(); mono = len(body.data.loop_triangles)
    wheels = sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.name.startswith('WRX_Wheel_'))
    susp = sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.name.startswith('WRX_Susp_'))
    glow.data.calc_loop_triangles(); fx = len(glow.data.loop_triangles); tot_ = mono + wheels + susp + fx
    lines += ['', f'MONO WRX_Body {mono} (body + cabin + scoop + wing + lip + mirrors + liners + floor + head/fog lamp caps)', f'wheels (4 x 10-sided) {wheels}',
              f'suspension (4 x strut + arm) {susp}', f'FX head lamp glow quads (WRX_FX_HeadGlow, off by default) {fx}',
              f'TOTAL rendered {tot_}  (cap {CAP}: {"OK" if tot_ <= CAP else "OVER"})',
              f'shading QC (loft quads): {json.dumps(W.QC)}']
    open(os.path.join(OUT, 'tri_count.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    # clearance (mono body: tyres vs WRX_Body incl. liners)
    rep = CL.check(rig, set_pose, rel_travel, BUMP, DROOP, LOCK, ROLL)
    json.dump(rep, open(os.path.join(OUT, 'bp', 'clearance.json'), 'w'), indent=1); set_pose(rig)
    # textures + PSX fake-shine materials
    body_png = texture_body(body)
    whl_png = os.path.join(OUT, 'tex', 'wrx_wheel.png'); run(os.path.join(HERE, 'tex', 'make_wheel_wrx.py'), whl_png)
    glow_png = os.path.join(OUT, 'tex', 'wrx_glow.png')
    run(os.path.join(HERE, 'tex', 'lamp', 'paint_lamps.py'), whl_png, os.path.join(OUT, 'tex', 'lamp_uv.json'), glow_png)
    env_png = os.path.join(OUT, 'tex', 'wrx_env.png'); run(os.path.join(HERE, 'tex', 'make_env.py'), env_png)
    PM.set_env(bpy.data.images.load(env_png))
    bimg = bpy.data.images.load(body_png); wimg = bpy.data.images.load(whl_png)
    paint = PM.fake_mat('WRX_Paint_Body', img=bimg, ambient=0.48, key=0.62, spec=0.45, shin=55, env=0.38, interp='Closest')
    glass = PM.fake_mat('WRX_Glass', rgb=(0.010, 0.014, 0.022), ambient=1.0, key=0.0, spec=0.6, shin=90, env=0.45, env_tint=(0.55, 0.70, 1.0))
    und = PM.fake_mat('WRX_Under', rgb=(0.006, 0.006, 0.007), ambient=1.0, key=0.0, spec=0.0, env=0.0)
    whl = PM.fake_mat('WRX_Wheel', img=wimg, ambient=0.55, key=0.55, spec=0.25, shin=30, env=0.15, interp='Closest')
    # lamp lens: same parts atlas, glassy but restrained (painted hotspot carries the brightness; spec/env low so the
    # RGB555 lamp art never clips to white)
    lampm = PM.fake_mat('WRX_Lamp', img=wimg, ambient=0.66, key=0.30, spec=0.30, shin=110, env=0.20, env_tint=(0.75, 0.82, 1.0), interp='Closest')
    gimg = bpy.data.images.load(glow_png); glowm = bpy.data.materials.new('WRX_FX_Glow'); glowm.use_nodes = True
    gnt = glowm.node_tree; gpb = gnt.nodes['Principled BSDF']; gtx = gnt.nodes.new('ShaderNodeTexImage'); gtx.image = gimg
    gpb.inputs['Base Color'].default_value = (0, 0, 0, 1); gnt.links.new(gtx.outputs['Color'], gpb.inputs['Emission Color'])
    gpb.inputs['Emission Strength'].default_value = 1.5; gnt.links.new(gtx.outputs['Alpha'], gpb.inputs['Alpha'])
    glowm.surface_render_method = 'BLENDED'; glowm.use_backface_culling = True
    glow.hide_render = True                                   # FX: lights-off renders; still exported (toggle in Godot)
    TEXM = {'clay': paint, 'clay_glass': glass, 'under': und, 'clay_trim': paint, 'clay_wheel': whl, 'clay_lampcap': lampm, 'clay_glow': glowm}
    CLAY_SLOTS = {o.name: [sl.material for sl in o.material_slots] for o in bpy.data.objects if o.type == 'MESH'}
    def apply(textured):
        for o in bpy.data.objects:
            if o.type != 'MESH': continue
            for sl, m0 in zip(o.material_slots, CLAY_SLOTS[o.name]): sl.material = TEXM[m0.name] if textured else m0
    apply(True)
    # exports: blend (fake-shine) + glb (Principled with the same textures)
    bpy.context.preferences.filepaths.save_version = 0
    for im in (bimg, wimg, gimg): im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'wrx_lean.blend'), compress=True)
    PM.use_principled(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'wrx_lean.glb'), export_format='GLB', use_visible=True)
    PM.use_principled(False)
    if '--render' in sys.argv:
        import render_wrx, render_lean; importlib.reload(render_wrx); importlib.reload(render_lean)
        apply(False); render_wrx.render_all(OUT, rig, set_pose, rel_travel, dict(BUMP=BUMP, DROOP=DROOP, LOCK=LOCK, ROLL=ROLL))
        apply(True); render_lean.render_textured(OUT, rig, set_pose, 'WRX')
if __name__ == '__main__': main()
