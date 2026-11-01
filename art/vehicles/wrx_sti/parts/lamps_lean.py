"""WRX lean headlamp + fog lamp lens caps (geometry + UVs into the parts atlas) and the optional headlamp glow quads.
Outlines: bp/lamp_outlines.json (tex/lamp/trace_lamps.py: blueprint front view, sub-pixel, Fourier-smoothed).
Each lamp is a lens face that sits on the nose (its own UVs + atlas art) instead of being painted across the faceted
corner by the body texture's per-view projection.
  head lamp: the body's front facets clipped to the outline (conforming lens face, ~30-40 tris); fog lamp 8 rim verts
  -> 8 tris (rim + fan)
UVs: planar projection along the lamp's own mean normal (no stretch where the nose turns the corner), uniform scale,
into the spare bottom-left quadrant of the 256^2 parts atlas (tile boxes below, atlas pixels, y down).  The right-hand
lamp is the mirror of the left and uses the same UVs (u mirrored in geometry, so the art mirrors with it).
Writes lean/tex/lamp_uv.json for the lamp painter (tex/lamp/paint_lamps.py)."""
import bpy, bmesh, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HEAD_TILE = (2, 130, 94, 222)      # x0, y0, x1, y1 (atlas px)
FOG_TILE = (97, 130, 127, 160)
N_HEAD, N_FOG = 12, 8
RIM_OFF, IN_OFF, C_OFF = 0.004, 0.009, 0.012
DECAL_OFF = 0.004
FOG_RIM_OFF, FOG_C_OFF = 0.003, 0.007
def _resample(P, n, start_angle_deg=90.0):
    P = np.asarray(P, float); c = P.mean(0)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))]
    a = np.degrees(np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])); i0 = int(np.argmin(np.abs(((a - start_angle_deg) + 180) % 360 - 180)))
    t = (L[i0] + np.linspace(0, L[-1], n, endpoint=False)) % L[-1]
    return np.c_[np.interp(t, L, np.r_[P[:, 0], P[0, 0]]), np.interp(t, L, np.r_[P[:, 1], P[0, 1]])]
def _bvh(objs):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm); bm.free(); return tree
def _hit(tree, to_bl, car, y, z):
    o = to_bl((3.0, y, z)); d = (to_bl((-1.0, y, z)) - o).normalized()
    loc, nrm, _, _ = tree.ray_cast(o, d, 6.0)
    if loc is None: raise RuntimeError(f'lamp ray missed the nose at y {y:.3f} z {z:.3f}')
    if nrm.dot(d) > 0: nrm = -nrm
    return np.array(car(loc)), np.array(car(nrm))
# The bugeye lamp is not on the front face: the blueprint side view puts it at x 1.88-2.08 (lens + bezel, axis from
# (2.043, .607) to (1.879, .810)) and the top view at x 1.86-2.02 (axis from (2.00, .49) to (1.87, .73)), i.e. set back
# on the upper nose corner, facing forward-up-outboard.  The lens rim's fore-aft position is a plane
# x = x0 + p*y + q*z least-squares fitted so that the rim agrees with BOTH of those axes; (y, z) come from the traced
# front view.  The lean nose is fuller than the real recessed lamp pocket there, so each 3D target point is moved to the
# NEAREST point of the body surface (the residual vs the blueprint is reported).
SIDE_AXIS = ((2.043, 0.607), (1.879, 0.810)); TOP_AXIS = ((2.000, 0.490), (1.870, 0.730))
def _x_plane(O):
    (sx0, sz0), (sx1, sz1) = SIDE_AXIS; (tx0, ty0), (tx1, ty1) = TOP_AXIS
    xs = lambda z: sx0 + (z - sz0) * (sx1 - sx0) / (sz1 - sz0); xt = lambda y: tx0 + (y - ty0) * (tx1 - tx0) / (ty1 - ty0)
    A = np.vstack([np.c_[np.ones(len(O)), O], np.c_[np.ones(len(O)), O]]); b = np.r_[xs(O[:, 1]), xt(O[:, 0])]
    return np.linalg.lstsq(A, b, rcond=None)[0]
def _near(tree, to_bl, car, p):
    loc, nrm, _, _ = tree.find_nearest(to_bl(tuple(p)))
    q = np.array(car(loc)); nn = np.array(car(nrm)); nn /= np.linalg.norm(nn)
    if nn[0] < -0.2: nn = -nn
    return q, nn
def _surf(tree, to_bl, car, yz, plane):
    if plane is None: return _hit(tree, to_bl, car, *yz)
    y, z = yz; x = plane[0] + plane[1] * y + plane[2] * z
    q, nn = _near(tree, to_bl, car, (x, y, z))
    hq, _ = _hit(tree, to_bl, car, q[1], q[2])                  # not under an overhang: take the front-most surface there
    return (q, nn) if hq[0] - q[0] < 0.01 else _hit(tree, to_bl, car, y, z)
def _cap(tree, to_bl, car, outline, n, rim_off, c_off, in_off=None, in_k=0.72, plane=None):
    O = np.asarray(outline, float); c2 = O.mean(0)
    rim2 = _resample(O, n)
    R = [_surf(tree, to_bl, car, yz, plane) for yz in rim2]
    C = _surf(tree, to_bl, car, c2, plane)
    Nl = np.sum([r[1] for r in R], 0) + C[1] * n * 0.5; Nl /= np.linalg.norm(Nl)
    rim = [p + nn * rim_off for p, nn in R]
    inner = None
    if in_off is not None:
        inner = []
        for yz in c2 + (rim2 - c2) * in_k:
            p, nn = _surf(tree, to_bl, car, yz, plane); inner.append(p + Nl * in_off)
    cen = C[0] + Nl * c_off
    rim = np.array(rim); inner = None if inner is None else np.array(inner)
    # keep every point of every cap face in front of the body (the faceted nose can bulge between the ray hits):
    # sample each face, measure penetration along -x against the body, lift the face's vertices along Nl; iterate
    V = np.vstack([rim] + ([inner] if inner is not None else []) + [cen[None]]); ic = len(V) - 1
    if inner is None: F = [(k, (k + 1) % n, ic) for k in range(n)]
    else:
        F = [f for k in range(n) for f in ((k, (k + 1) % n, n + (k + 1) % n), (k, n + (k + 1) % n, n + k), (n + k, n + (k + 1) % n, ic))]
    B = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, 7) for b in np.linspace(0, 1, 7) if a + b <= 1.0001])
    CLEAR = 0.003
    for it in range(6):
        lift = np.zeros(len(V)); worst = 0.0
        for f in F:
            P = B @ V[list(f)]
            for w, p in zip(B, P):
                q, nn = _near(tree, to_bl, car, p); sd = (p - q) @ nn
                pen = CLEAR - sd if (sd < CLEAR) else 0.0
                if pen > 0:
                    worst = max(worst, pen); dl = pen / max(float(nn @ Nl), 0.3)
                    for wi, vi in zip(w, f): lift[vi] = max(lift[vi], dl * min(1.0, wi * 2.5))
        if worst <= 1e-4: break
        V = V + lift[:, None] * Nl[None]
    rim = V[:n]; inner = V[n:2 * n] if inner is not None else None; cen = V[ic]
    print(f'cap depth fix: {it} passes, residual penetration {worst * 1000:.1f} mm')
    return dict(rim=rim, inner=inner, cen=cen, normal=Nl, rim2=rim2, c2=c2)
def _clip(poly, clipper):
    """Sutherland-Hodgman: polygon (k,2) clipped by a CCW convex polygon."""
    out = [tuple(p) for p in poly]
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]; inp, out = out, []
        if not inp: break
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        for j in range(len(inp)):
            P, Q = inp[j], inp[(j + 1) % len(inp)]; sp, sq = side(P), side(Q)
            if sp >= 0: out.append(P)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq); out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    return out
def _decal(body_objs, car, outline, n_out, Nl, off, tree=None, to_bl=None):
    """Lens face that CONFORMS to the nose: the body's front-facing triangles clipped (front view) to the lamp outline,
    lifted `off` along the lamp normal.  No chord can cut into the body (it lies on the body facets), shared edges stay
    shared (same lift for every piece), so no cracks and no bulge.  Returns (verts car frame, faces)."""
    O = _resample(outline, n_out); O = O if np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) > 0 else O[::-1]
    pts = sorted(map(tuple, O)); cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cr(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cr(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1])                     # CCW convex hull (monotone chain)
    lo, hi = hull.min(0) - 0.01, hull.max(0) + 0.01
    V, F, key = [], [], {}
    def vid(p):
        k = tuple(np.round(p, 5))
        if k not in key: key[k] = len(V); V.append(np.asarray(p, float))
        return key[k]
    for ob in body_objs:
        me = ob.data; me.calc_loop_triangles(); mw = ob.matrix_world
        Pw = np.array([car(mw @ v.co) for v in me.vertices])
        for lt in me.loop_triangles:
            T = Pw[list(lt.vertices)]; n = np.cross(T[1] - T[0], T[2] - T[0]); nn = np.linalg.norm(n)
            if nn < 1e-9: continue
            n = n / nn
            if n[0] < -0.02 or T[:, 0].mean() < 1.6: continue
            if n[0] < 0.05 and tree is not None:          # near edge-on facets (hood crease): only if not hidden from the front
                cc = T.mean(0); hp, _ = _hit(tree, to_bl, car, cc[1], cc[2])
                if hp[0] - cc[0] > 0.01: continue
            if (T[:, 1:] < lo).all(0).any() or (T[:, 1:] > hi).all(0).any(): continue
            P2 = T[:, 1:]
            if np.cross(P2[1] - P2[0], P2[2] - P2[0]) < 0: P2 = P2[::-1]
            C = _clip(P2, hull)
            if len(C) < 3: continue
            ids = []
            for y, z in C:
                if abs(n[0]) > 1e-3: x = T[0, 0] - (n[1] * (y - T[0, 1]) + n[2] * (z - T[0, 2])) / n[0]
                else: x = T[:, 0].mean()
                ids.append(vid(np.array([x, y, z]) + Nl * off))
            ids = [i for j, i in enumerate(ids) if i != ids[j - 1]]
            if len(set(ids)) >= 3: F.append(ids)
            elif len(C) >= 3: print('decal piece collapsed', np.round(C, 3).tolist())
    return np.array(V), F
def _plane_basis(Nl):
    up = np.array([0.0, 0.0, 1.0]); e1 = np.cross(up, Nl); e1 /= np.linalg.norm(e1)      # +e1 = toward car left (outboard on the left lamp) when Nl ~ +x
    e2 = np.cross(Nl, e1); return e1, e2
def _uv_map(cap, tile, dense, tree, to_bl, car, margin=0.04, plane=None):
    e1, e2 = _plane_basis(cap['normal']); o = cap['cen']
    pts = [cap['rim'], cap['inner'], cap['cen'][None]] if cap['inner'] is not None else [cap['rim'], cap['cen'][None]]
    D = np.array([_surf(tree, to_bl, car, yz, plane)[0] for yz in dense])        # dense outline on the surface (for the painter)
    proj = lambda P: np.c_[(P - o) @ e1, (P - o) @ e2]
    Pd = proj(D); lo, hi = Pd.min(0), Pd.max(0); span = (hi - lo).max() * (1 + 2 * margin); mid = (lo + hi) / 2
    x0, y0, x1, y1 = tile; W = x1 - x0
    def to_uv(P):
        q = (proj(P) - mid) / span                                             # -.5 .. .5, +x outboard, +y up
        px = x0 + (q[:, 0] + 0.5) * W; py = y1 - (q[:, 1] + 0.5) * (y1 - y0)   # atlas pixels (y down)
        return np.c_[px / 256.0, 1.0 - py / 256.0], np.c_[px, py]
    return to_uv, to_uv(D)[1], span
# ---------------------------------------------------------------- head lamp POCKET (light molding)
# Blueprint line classes around the bugeye (front / side / top views): the closed grey ring around the white lens is the
# LAMP OUTLINE (lens + chrome bezel = the pocket opening); the line that leaves it up-and-outboard toward the A-pillar
# (front view) / runs back along the bonnet (top view) is the BONNET-FENDER SHUT LINE (a body line, painted in the body
# texture, never cut); the dark arc behind the lens in the side view is the pocket's inner wall (shadow), the small
# clear lens behind / below the lamp is the side marker (painted).  The blueprint puts the lens plane 10-15 cm behind
# the lean nose at its lower edge; the approved brief is a LIGHT pocket (don't over-carve the nose), so the lens is set a
# constant ~3.5 cm behind the nose surface (measured along the local surface normal; on the bonnet-top part of the rim
# that is a longer step back along x, capped at 6 cm so the dish stays shallow), as a shallow faceted dish: rim + centre fan.  The opening is cut
# along the car's x axis, so the front view keeps the traced outline exactly.
POCKET_D, POCKET_N, POCKET_XF, POCKET_XCAP = 0.035, 14, 2.45, 0.06
def _pocket(tree, to_bl, car, outline):
    O = _resample(outline, POCKET_N); O = O if np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) > 0 else O[::-1]
    c2 = O.mean(0); H = [_hit(tree, to_bl, car, y, z) for y, z in np.vstack([O, c2[None]])]
    S = np.array([h[0] for h in H]); Nn = np.array([h[1] for h in H])
    dx = np.minimum(POCKET_D / np.maximum(Nn[:, 0], 0.35), POCKET_XCAP)      # step back along x for ~D normal depth
    fl = S - np.c_[dx, np.zeros((len(S), 2))]
    # normal of the dish (area-weighted fan), used for the planar lens UVs and the glow quad
    nf = np.zeros(3)
    for k in range(POCKET_N): nf += np.cross(fl[k] - fl[-1], fl[(k + 1) % POCKET_N] - fl[-1])
    nf /= np.linalg.norm(nf); nf = nf if nf[0] > 0 else -nf
    front = np.c_[np.full(len(O), POCKET_XF), O]
    return dict(O=O, normal=nf, floor=fl[:-1], cen=fl[-1], front=front, depth_x=dx, depth_n=dx * Nn[:, 0])
def build(to_bl, car, obj_from_bm, body_objs, mats, out_tex_dir, mirror_name):
    """mats: (lamp_material, glow_material, lens(pocket floor)_material, pocket_wall_material).  Returns ([fog lens cap
    objects], glow object, head lamp pocket cutter object)."""
    J = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bp', 'lamp_outlines.json')))
    tree = _bvh(body_objs); rec = {}; caps = []
    for key, tile, n, kw in (('head', HEAD_TILE, N_HEAD, dict(rim_off=RIM_OFF, c_off=C_OFF, in_off=IN_OFF)),
                             ('fog', FOG_TILE, N_FOG, dict(rim_off=FOG_RIM_OFF, c_off=FOG_C_OFF))):
        plane = None          # front-view exact (see README: the lean nose is fuller than the blueprint lamp pocket)
        cap = _cap(tree, to_bl, car, J[key], n, plane=plane, **kw)
        dense = _resample(J[key], 96)
        to_uv, dense_px, span = _uv_map(cap, tile, dense, tree, to_bl, car, plane=plane)
        Dsurf = np.array([_surf(tree, to_bl, car, yz, plane)[0] for yz in dense]); dev = np.linalg.norm(Dsurf[:, 1:] - dense, axis=1)
        uv_rim, rim_px = to_uv(cap['rim']); uv_c, c_px = to_uv(cap['cen'][None]); uv_in = to_uv(cap['inner'])[0] if cap['inner'] is not None else None
        e1, e2 = _plane_basis(cap['normal'])
        rec[key] = dict(tile=tile, outline_px=np.round(dense_px, 2).tolist(), centre_px=np.round(c_px[0], 2).tolist(), span_m=round(float(span), 4),
                        normal_car=np.round(cap['normal'], 3).tolist(), rim_x_range=[round(float(cap['rim'][:, 0].min()), 3), round(float(cap['rim'][:, 0].max()), 3)],
                        front_view_dev_mm=dict(mean=round(float(dev.mean()) * 1000, 1), max=round(float(dev.max()) * 1000, 1)),
                        plane_x=None if plane is None else np.round(plane, 4).tolist(),
                        target_x_range=None if plane is None else [round(float((plane[0] + dense @ plane[1:]).min()), 3), round(float((plane[0] + dense @ plane[1:]).max()), 3)])
        if key == 'head':
            pk = _pocket(tree, to_bl, car, J[key]); nf = pk['normal']; o_ = pk['cen']
            e1, e2 = _plane_basis(np.array([1.0, 0.0, 0.0]))     # lens UVs projected along x: the art reads true in the (blueprint) front view
            Fr = pk['floor']; Dfl = np.vstack([Fr[k] + (Fr[(k + 1) % len(Fr)] - Fr[k]) * t for k in range(len(Fr)) for t in np.linspace(0, 1, 7, endpoint=False)])   # the dish rim, densified (art bezel == geometric rim)
            proj = lambda P: np.c_[(P - o_) @ e1, (P - o_) @ e2]
            Pd = proj(Dfl); lo, hi = Pd.min(0), Pd.max(0); span = (hi - lo).max() * 1.08; mid = (lo + hi) / 2
            x0, y0, x1, y1 = tile
            def to_uv(P):
                q = (proj(P) - mid) / span; px = x0 + (q[:, 0] + 0.5) * (x1 - x0); py = y1 - (q[:, 1] + 0.5) * (y1 - y0)
                return np.c_[px / 256.0, 1.0 - py / 256.0], np.c_[px, py]
            uvf = to_uv(pk['floor'])[0]; uvc = to_uv(pk['cen'][None])[0][0]
            rec[key].update(outline_px=np.round(to_uv(Dfl)[1], 2).tolist(), centre_px=np.round(to_uv(o_[None])[1][0], 2).tolist(), span_m=round(float(span), 4),
                            normal_car=np.round(nf, 3).tolist(), rim_x_range=[round(float(pk['floor'][:, 0].min()), 3), round(float(pk['floor'][:, 0].max()), 3)],
                            pocket=dict(step_back_x_cm=np.round(pk['depth_x'] * 100, 1).tolist(), depth_normal_cm=np.round(pk['depth_n'] * 100, 1).tolist(), n_rim=POCKET_N))
            rec['_pocket_cen'] = pk['cen'].tolist()
            # cutter: closed prism along +x (front cap well ahead of the nose, back cap = the lens plane).  Booleaned out of
            # the body by build_wrx_lean.py (exact solver, materials transferred): its back cap becomes the recessed lens
            # (atlas UVs, lamp material), its sides become the pocket walls (black trim class, painted dark).
            bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); n_ = len(pk['O'])
            for side in (1, -1):
                m_ = np.array([1, side, 1])
                fl = [bm.verts.new(to_bl(tuple(p * m_))) for p in pk['floor']]; fr = [bm.verts.new(to_bl(tuple(p * m_))) for p in pk['front']]
                vc = bm.verts.new(to_bl(tuple(pk['cen'] * m_)))
                for k in range(n_):                                     # dish: rim + centre fan
                    tri = (fl[k], fl[(k + 1) % n_], vc); f = bm.faces.new(tri if side < 0 else tri[::-1]); f.material_index = 0
                    for lp in f.loops: lp[uvl].uv = tuple(uvc) if lp.vert is vc else tuple(uvf[fl.index(lp.vert)])
                f = bm.faces.new(fr[::-1] if side < 0 else fr); f.material_index = 1
                for k in range(n_):
                    k1 = (k + 1) % n_; q = (fl[k], fl[k1], fr[k1], fr[k]); f = bm.faces.new(q if side > 0 else q[::-1]); f.material_index = 1
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            cutter = obj_from_bm('WRX_PocketCutter', bm, list(mats[2:4]))
            continue
        for side in (1, -1):
            bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); m_ = np.array([1, side, 1])
            V = lambda P: bm.verts.new(to_bl(tuple(P * m_)))
            rim = [V(p) for p in cap['rim']]; cen = V(cap['cen']); inner = [V(p) for p in cap['inner']] if cap['inner'] is not None else None
            def face(vs, uvs):
                if side < 0: vs, uvs = vs[::-1], uvs[::-1]
                f = bm.faces.new(vs)
                for lp, uv in zip(f.loops, uvs): lp[uvl].uv = tuple(uv)
            for k in range(n):
                k1 = (k + 1) % n
                if inner is None: face([rim[k], rim[k1], cen], [uv_rim[k], uv_rim[k1], uv_c[0]])
                else:
                    face([rim[k], rim[k1], inner[k1], inner[k]], [uv_rim[k], uv_rim[k1], uv_in[k1], uv_in[k]])
                    face([inner[k], inner[k1], cen], [uv_in[k], uv_in[k1], uv_c[0]])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            # make sure the caps face outward (same side as the lamp normal)
            fn = sum((f.normal for f in bm.faces), Vector()); want = to_bl(tuple(cap['normal'] * m_)) - to_bl((0, 0, 0))
            if fn.dot(want) < 0:
                for f in bm.faces: f.normal_flip()
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY')
            nm = {'head': 'WRX_HeadLamp', 'fog': 'WRX_FogLamp'}[key] + ('_L' if side > 0 else '_R')
            ob = obj_from_bm(nm, bm, [mats[0]]); caps.append(ob)
            for p in ob.data.polygons: p.use_smooth = True
    # glow quads (FX, separate object): one camera-agnostic quad per head lamp, 1.5 cm in front of the lens centre,
    # facing the lamp normal, 1.5 x the lamp span; alpha sprite (own 64^2 RGBA texture).  Off by default in Godot.
    hc = rec['head']; nf = np.asarray(hc['normal_car']); e1, e2 = _plane_basis(nf); s = hc['span_m'] * 0.75
    c = np.asarray(rec.pop('_pocket_cen')) + nf * 0.02
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    uvq = [(0, 0), (1, 0), (1, 1), (0, 1)]                        # own 64^2 RGBA sprite (tex/wrx_glow.png)
    for side in (1, -1):
        m_ = np.array([1, side, 1]); Q = [c - e1 * s - e2 * s, c + e1 * s - e2 * s, c + e1 * s + e2 * s, c - e1 * s + e2 * s]
        vs = [bm.verts.new(to_bl(tuple(q * m_))) for q in Q]; uvs = uvq
        if side < 0: vs, uvs = vs[::-1], uvs[::-1]
        f = bm.faces.new(vs)
        for lp, uv in zip(f.loops, uvs): lp[uvl].uv = uv
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    glow = obj_from_bm('WRX_FX_HeadGlow', bm, [mats[1]])
    json.dump(rec, open(os.path.join(out_tex_dir, 'lamp_uv.json'), 'w'), indent=1)
    print('LAMPS', json.dumps({k: {kk: v.get(kk) for kk in ('rim_x_range', 'normal_car', 'pocket')} for k, v in rec.items()}))
    return caps, glow, cutter
