"""Stage C of the light headlamp molding (S2000 / BRZ lean): a thin raised surround around each painted headlamp,
added to the finished mono body (nothing else in the model changes; the baked body texture is reused).
  outer edge  : on the body, W_OUT outside the painted lamp outline (paint colour)
  lip         : at the outline, H_LIP proud of the body along the local normal (paint colour)
  inner wall  : back down to the body W_IN inside the outline (lamp housing colour = darkest housing texel)
=> the lens reads set into a shallow molded surround.  2 bands x N corners x 2 tris per lamp.
Outline: stage B (molding_outline.py) in a 3/4 ortho view; corners are ray-cast onto the body along that view.
blender -b <car>_lean.blend -P molding_ring.py -- P xfwd|xleft outline.json out_dir [H_LIP W_OUT W_IN]
Saves <out_dir>/<p>_lean.blend + .glb, bp/tris_carframe.npy, bp/clearance.json, tri_count.txt, molding.json."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'wrx_sti', 'parts'))
import leanlib as LL, psx_mat as PM
a = sys.argv[sys.argv.index('--') + 1:]
P, frame, ojs, OUT = a[0], a[1], a[2], a[3]
H_LIP, W_OUT, W_IN = (float(v) for v in a[4:7]) if len(a) >= 7 else (0.006, 0.010, 0.003)
FR = LL.Frame(frame); J = json.load(open(ojs))
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        alt = os.path.join(OUT, 'tex', os.path.basename(im.filepath))
        if os.path.exists(alt): im.filepath = alt; im.reload()
body = bpy.data.objects[P + '_Body']; me = body.data; mw = body.matrix_world; mwi = mw.inverted()
me.calc_loop_triangles(); uvl = me.uv_layers.active.data
bm0 = bmesh.new(); bm0.from_mesh(me); bm0.transform(mw); tree = BVHTree.FromBMesh(bm0); bm0.free()
tris_of = {}
for lt in me.loop_triangles: tris_of.setdefault(lt.polygon_index, []).append(lt)
def uv_at(p_w, poly):
    pl = mwi @ p_w; best = None
    for lt in tris_of[poly]:
        v = [me.vertices[i].co for i in lt.vertices]; u = [Vector((*uvl[l].uv, 0)) for l in lt.loops]
        q = barycentric_transform(pl, *v, *u)
        w = barycentric_transform(pl, *v, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        err = sum(max(0.0, -c) for c in w)
        if best is None or err < best[0]: best = (err, (q.x, q.y))
    return best[1]
# body texture (for the darkest housing texel)
slot_img = {}
for i, sl in enumerate(body.material_slots):
    m = sl.material
    img = next((n.image for n in (m.node_tree.nodes if m and m.use_nodes else []) if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] >= 512), None)
    slot_img[i] = img
pix_cache = {}
def texel(img, uv):
    if img.name not in pix_cache: pix_cache[img.name] = (np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4), img.size)
    A, (W, H) = pix_cache[img.name]; x = int(np.clip(uv[0] % 1 * W, 0, W - 1)); y = int(np.clip(uv[1] % 1 * H, 0, H - 1)); return A[y, x, :3]
# outline (view plane, Blender world) + 2-D offsets in the view plane
R = J['res']; S = J['size']; tgt = Vector(J['tgt_bl']); r = Vector(J['right_bl']); u = Vector(J['up_bl']); b = Vector(J['back_bl'])
Q = np.array(J['outline_px'], float); Q2 = np.c_[(Q[:, 0] + 0.5) / R - 0.5, 0.5 - (Q[:, 1] + 0.5) / R] * S   # metres (right, up)
if np.sum(Q2[:, 0] * np.roll(Q2[:, 1], -1) - np.roll(Q2[:, 0], -1) * Q2[:, 1]) < 0: Q2 = Q2[::-1]      # CCW
N = len(Q2)
def offset(Pp, d):           # +d outward (CCW polygon): miter offset, miter capped at 2.5 d
    out = []
    for k in range(N):
        p0, p1, p2 = Pp[k - 1], Pp[k], Pp[(k + 1) % N]
        n0 = np.array([p1[1] - p0[1], -(p1[0] - p0[0])]); n0 /= np.linalg.norm(n0)
        n1 = np.array([p2[1] - p1[1], -(p2[0] - p1[0])]); n1 /= np.linalg.norm(n1)
        m = n0 + n1; m /= np.linalg.norm(m); s = min(1.0 / max(m @ n0, 0.4), 2.5); out.append(p1 + m * d * s)
    return np.array(out)
def mirror_w(v):             # car-frame y -> -y, in Blender world
    c = FR.to_car(v); return FR.to_bl((c[0], -c[1], c[2]))
def cast(p2, side):
    o = tgt + r * float(p2[0]) + u * float(p2[1]) + b * 3.0; d = -b
    if side < 0: o = mirror_w(o); d = mirror_w(d) - mirror_w(Vector((0, 0, 0)))
    loc, nrm, idx, _ = tree.ray_cast(o, d, 8.0)
    if loc is None: raise RuntimeError(f'molding ray missed at {p2}')
    if nrm.dot(d) > 0: nrm = -nrm
    return loc, nrm.normalized(), idx
bm = bmesh.new(); bm.from_mesh(me); uvL = bm.loops.layers.uv.active
added = 0; rec = {'N': N, 'H_LIP': H_LIP, 'W_OUT': W_OUT, 'W_IN': W_IN, 'sides': {}}
for side in (1, -1):
    So = [cast(p, side) for p in offset(Q2, W_OUT)]; Sl = [cast(p, side) for p in Q2]; Si = [cast(p, side) for p in offset(Q2, -W_IN)]
    lip_w = [l + n * H_LIP for l, n, _ in Sl]; out_w = [l + n * 0.0008 for l, n, _ in So]; in_w = [l + n * 0.0008 for l, n, _ in Si]
    mi = me.polygons[So[0][2]].material_index; img = slot_img.get(mi)
    # paint UV: the outer ring point with the highest z (always on paint); housing UV: the darkest of the inner points
    top = max(range(N), key=lambda k: So[k][0].z); uv_paint = uv_at(So[top][0], So[top][2])
    cand = [uv_at(l, i) for l, _, i in Si]
    uv_dark = min(cand, key=lambda q: float(texel(img, q).sum())) if img is not None else cand[0]
    vo = [bm.verts.new(mwi @ p) for p in out_w]; vl = [bm.verts.new(mwi @ p) for p in lip_w]
    vl2 = [bm.verts.new(mwi @ p) for p in lip_w]; vi = [bm.verts.new(mwi @ p) for p in in_w]
    nav = sum((n for _, n, _ in Sl), Vector()).normalized()
    def quad(vs, uv):
        f = bm.faces.new(vs); f.material_index = mi; f.smooth = False
        for lp in f.loops: lp[uvL].uv = uv
        return f
    fs = []
    for k in range(N):
        k1 = (k + 1) % N
        fs.append(quad((vo[k], vo[k1], vl[k1], vl[k]), uv_paint)); fs.append(quad((vl2[k], vl2[k1], vi[k1], vi[k]), uv_dark))
    for f in fs:
        f.normal_update(); c = f.calc_center_median(); cw = mw @ c
        # outward = away from the lamp centre for the outer slope / toward the viewer, i.e. along the surface normal
        if (mw.to_3x3() @ f.normal).dot(nav) < 0: f.normal_flip()
    bmesh.ops.triangulate(bm, faces=fs, quad_method='BEAUTY'); added += 4 * N
    rec['sides']['L' if side > 0 else 'R'] = dict(uv_paint=list(uv_paint), uv_dark=list(uv_dark), dark_rgb=[round(float(x), 3) for x in texel(img, uv_dark)] if img else None,
                                                  outline_car=[[round(float(c), 4) for c in FR.to_car(l)] for l, _, _ in Sl])
bm.to_mesh(me); bm.free(); me.update(); me.calc_loop_triangles()
print('MOLDING added tris', added)
# ---- rig reconstruction (saved at rest) for clearance
root = bpy.data.objects[P + '-vehicle']
rig = dict(FR=FR, body=body, hub={}, steer={}, susp={}, hub_rest={})
c = FR.to_car(body.location); rig['com'] = (c[0], c[2])
for k in ('FL', 'FR', 'RL', 'RR'):
    hb = bpy.data.objects[f'Hub_{k}-wheel']; rig['hub'][k] = hb; rig['hub_rest'][k] = tuple(hb.location); rig['susp'][k] = bpy.data.objects[f'Susp_{k}']
    if k[0] == 'F': rig['steer'][k] = bpy.data.objects[f'Steer_{k}']
bpy.context.view_layer.update()
rig['hub_body_rest'] = {k: (body.matrix_world.inverted() @ hb.matrix_world.translation).z for k, hb in rig['hub'].items()}
spec = json.load(open(os.path.join(OUT, 'bp', 'clearance.json')))['spec']
rep = LL.clearance(rig, P, [P + '_Body'], spec['bump'], spec['droop'], spec['lock_deg'])
json.dump(rep, open(os.path.join(OUT, 'bp', 'clearance.json'), 'w'), indent=1); LL.set_pose(rig)
# ---- tri soup (IoU), tri count
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(P + '_') and '_Susp_' not in o.name and '_FX_' not in o.name]
np.save(os.path.join(OUT, 'bp', 'tris_carframe.npy'), LL.tri_soup(FR, meshes))
allm = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(P + '_')]
for o in allm: o.data.calc_loop_triangles()
cnt = {o.name: len(o.data.loop_triangles) for o in allm}; tot = sum(cnt.values())
tc = os.path.join(OUT, 'tri_count.txt'); old = open(tc).read().rstrip('\n').split('\n')
old = [l for l in old if not l.startswith('TOTAL') and not l.startswith('MONO') and not l.startswith('headlamp molding')]
old += [f'headlamp molding (2 x {N}-corner surround: raised lip + inner wall) {added}',
        f'MONO {P}_Body {cnt[P + "_Body"]} (incl. headlamp molding)', f'TOTAL rendered {tot}  (cap 2000: {"OK" if tot <= 2000 else "OVER"})']
open(tc, 'w').write('\n'.join(old) + '\n'); print('\n'.join(old[-3:]))
rec.update(added_tris=added, total_tris=tot, clearance=dict(all_clear=rep['all_clear'], tightest=rep['tightest']))
json.dump(rec, open(os.path.join(OUT, 'molding.json'), 'w'), indent=1)
# ---- save + glb (same export axes as the build)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, P.lower() + '_lean.blend'), compress=True)
PM.use_principled(True)
if frame == 'xfwd':
    ROT = Matrix.Rotation(-math.pi / 2, 4, 'Z'); LL.conjugate_rig(root, ROT)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, P.lower() + '_lean.glb'), export_format='GLB', use_visible=True)
if frame == 'xfwd': LL.conjugate_rig(root, ROT.inverted())
PM.use_principled(False)
print('MOLDING DONE', tot)
