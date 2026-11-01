"""Lean pass: blueprint features -> VECTORS (car metres, per view) for the painted texture.  Nothing is copied from
the raster into the texture: panel / shut lines are thinned, traced and simplified into polylines; lamps, grille,
intakes, handles, black trim and glass are traced into polygons.  The painter (tex/make_body_wrx.py) draws them as
anti-aliased vector shapes in the view plane that owns each texel.
Coordinates: side (x, z), top (x, y), front / rear (y, z) -- car frame x fwd, y left, z up.
Writes bp/feature_vectors.json and renders/clay_raw/feature_vectors.png (record)."""
import json, numpy as np, cv2
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']; Z = np.load('bp/bp_classes.npz')
def to_m(view, cc, rr):
    X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    if view == 'side': return (float(Z['side_CM']) - X0 - cc) * S, (float(Z['side_ZF']) - Y0 - rr) * S
    if view == 'top': return (float(Z['top_CM']) - X0 - cc) * S, (rr - float(Z['top_CR'])) * S
    sg = 1 if view == 'front' else -1
    return sg * (cc - float(Z[f'{view}_CC'])) * S, (float(Z[f'{view}_ZF']) - Y0 - rr) * S
def thin(m):
    """Zhang-Suen thinning (numpy)."""
    m = np.pad(m.astype(np.uint8), 1)
    while True:
        changed = False
        for it in (0, 1):
            P = [np.roll(np.roll(m, -dy, 0), -dx, 1) for dy, dx in ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))]
            Bn = sum(P); A = sum(((P[i] == 0) & (P[(i + 1) % 8] == 1)).astype(int) for i in range(8))
            c1 = (P[0] * P[2] * P[4] == 0) if it == 0 else (P[0] * P[2] * P[6] == 0)
            c2 = (P[2] * P[4] * P[6] == 0) if it == 0 else (P[0] * P[4] * P[6] == 0)
            rm = (m == 1) & (Bn >= 2) & (Bn <= 6) & (A == 1) & c1 & c2
            if rm.any(): m[rm] = 0; changed = True
        if not changed: break
    return m[1:-1, 1:-1].astype(bool)
NB = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
def trace(sk):
    """skeleton -> pixel paths split at junctions."""
    H, W = sk.shape; deg = np.zeros(sk.shape, int)
    for dy, dx in NB: deg += np.roll(np.roll(sk, dy, 0), dx, 1)
    deg *= sk; used = np.zeros_like(sk); paths = []
    def nbrs(r, c):
        return [(r + dy, c + dx) for dy, dx in NB if 0 <= r + dy < H and 0 <= c + dx < W and sk[r + dy, c + dx]]
    starts = list(zip(*np.nonzero(sk & (deg == 1)))) + list(zip(*np.nonzero(sk & (deg >= 3)))) + list(zip(*np.nonzero(sk)))
    for s in starts:
        for n0 in nbrs(*s):
            if used[n0] and deg[n0] < 3: continue
            p = [s, n0]; prev, cur = s, n0
            while deg[cur] == 2 and not used[cur]:
                used[cur] = True; nx = [q for q in nbrs(*cur) if q != prev and q not in p[-3:]]
                if not nx: break
                prev, cur = cur, nx[0]; p.append(cur)
            used[s] = True
            if len(p) >= 3: paths.append(np.array(p))
    return paths
out = {}
rec = []
for view in ('side', 'top', 'front', 'rear'):
    M = Z[f'{view}_M']; ed = cv2.morphologyEx(M.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)) > 0
    excl = ed | cv2.dilate(Z[f'{view}_TY'].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) | Z[f'{view}_GL']
    D = Z[f'{view}_D'] & M & ~excl
    lines = []
    for p in trace(thin(D)):
        ap = cv2.approxPolyDP(p[:, ::-1].astype(np.float32).reshape(-1, 1, 2), 0.9, False).reshape(-1, 2)
        L = np.hypot(*np.diff(ap, axis=0).T).sum()
        u, v = to_m(view, ap[:, 0], ap[:, 1]); Lm = L * S
        ang = abs(np.degrees(np.arctan2(v[-1] - v[0], u[-1] - u[0]))); ang = min(ang, 180 - ang)
        # keep panel / shut lines, drop the blueprint's hatch shading (short, near-horizontal strokes on the flanks):
        # >= 20 cm, or >= 8 cm and steeper than 40 deg (shut lines), front / rear views >= 10 cm
        keep = Lm >= 0.20 or (Lm >= 0.08 and ang > 40) or (view in ('front', 'rear') and Lm >= 0.10)
        if keep: lines.append(np.round(np.c_[u, v], 4).tolist())
    polys = {}
    for key in ('HL', 'LL', 'R', 'K', 'GL'):
        if f'{view}_{key}' not in Z.files: continue
        m = Z[f'{view}_{key}'].astype(np.uint8)
        if key == 'K': m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        pl = []
        for c in cs:
            if cv2.contourArea(c) < (10 if key != 'GL' else 60): continue
            ap = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2).astype(float)
            u, v = to_m(view, ap[:, 0], ap[:, 1]); pl.append(np.round(np.c_[u, v], 4).tolist())
        polys[key] = pl
    out[view] = dict(lines=lines, polys=polys)
    # record image
    im = np.full(M.shape + (3,), 255, np.uint8); im[M] = (235, 225, 205); sc = 3
    im = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_NEAREST)
    def px(pts):
        pts = np.asarray(pts); X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
        if view == 'side': cc = float(Z['side_CM']) - X0 - pts[:, 0] / S; rr = float(Z['side_ZF']) - Y0 - pts[:, 1] / S
        elif view == 'top': cc = float(Z['top_CM']) - X0 - pts[:, 0] / S; rr = float(Z['top_CR']) + pts[:, 1] / S
        else:
            sg = 1 if view == 'front' else -1; cc = float(Z[f'{view}_CC']) + sg * pts[:, 0] / S; rr = float(Z[f'{view}_ZF']) - Y0 - pts[:, 1] / S
        return (np.c_[cc, rr] * sc).astype(np.int32)
    col = dict(HL=(200, 0, 200), LL=(200, 0, 200), R=(0, 0, 230), K=(40, 40, 40), GL=(0, 160, 0))
    for k, pl in polys.items():
        for p in pl: cv2.polylines(im, [px(p)], True, col[k], 1, cv2.LINE_AA)
    for p in lines: cv2.polylines(im, [px(p)], False, (200, 60, 0), 1, cv2.LINE_AA)
    rec.append(im)
json.dump(out, open('bp/feature_vectors.json', 'w'))
W = max(i.shape[1] for i in rec); rec = [cv2.copyMakeBorder(i, 4, 4, 0, W - i.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in rec]
cv2.imwrite('renders/clay_raw/feature_vectors.png', np.vstack(rec))
print({v: (len(o['lines']), {k: len(p) for k, p in o['polys'].items()}) for v, o in out.items()})
