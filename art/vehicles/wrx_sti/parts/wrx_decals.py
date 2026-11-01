"""Blueprint-exact lamp / grille decals: every outline is a contour of a blueprint class mask (bp/bp_classes.npz),
converted to car-frame 2D in its own view, then ray-cast along that view's direction onto the clay body and lifted
4 mm off the surface.  numpy + cv2-free (contours traced here) so it runs in Blender's Python."""
import numpy as np
import wrx_masks as MK
from wrx_bp import S
Z = MK.Z
def _components(m, min_px):
    """connected components (4-neigh) of a bool mask -> list of (rows, cols)."""
    m = m.copy(); H, W = m.shape; out = []
    seen = np.zeros_like(m)
    for r0 in range(H):
        for c0 in np.nonzero(m[r0] & ~seen[r0])[0]:
            if seen[r0, c0]: continue
            st = [(r0, c0)]; seen[r0, c0] = True; rr = []; cc = []
            while st:
                r, c = st.pop(); rr.append(r); cc.append(c)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = r + dr, c + dc
                    if 0 <= a < H and 0 <= b < W and m[a, b] and not seen[a, b]: seen[a, b] = True; st.append((a, b))
            if len(rr) >= min_px: out.append((np.array(rr), np.array(cc)))
    return out
def _hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3: return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]
def _resample(poly, n):
    P = np.array(poly + [poly[0]], float); seg = np.hypot(*np.diff(P, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, cum[-1], n, endpoint=False)
    return np.c_[np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])]
def outlines(view, key, min_px=12, n=12, filt=None):
    """car-frame 2D outlines (convex hulls, n points) of the components of view/key.
    side: (x, z), front/rear: (y, z), top: (x, y)."""
    m = Z[f'{view}_{key}'].astype(bool); X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    out = []
    for rr, cc in _components(m, min_px):
        if view == 'side':
            u = (float(Z['side_CM']) - X0 - cc) * S; v = (float(Z['side_ZF']) - Y0 - rr) * S
        elif view == 'top':
            u = (float(Z['top_CM']) - X0 - cc) * S; v = (rr - float(Z['top_CR'])) * S
        else:
            sg = 1 if view == 'front' else -1
            u = sg * (cc - float(Z[f'{view}_CC'])) * S; v = (float(Z[f'{view}_ZF']) - Y0 - rr) * S
        pts = np.c_[u, v]
        if filt is not None and not filt(pts): continue
        # pixel-corner hull (+-half px) so the outline encloses the drawn region
        h = 0.5 * S; corners = np.vstack([pts + [dx, dy] for dx in (-h, h) for dy in (-h, h)])
        out.append(_resample(_hull([tuple(np.round(p, 5)) for p in corners]), n))
    return out
