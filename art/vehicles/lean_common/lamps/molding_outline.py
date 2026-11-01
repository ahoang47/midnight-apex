"""Stage B of the light headlamp molding: segment the painted headlamp (everything that is not body paint) in the
3/4 ortho close render from stage A, take the component at the lamp, fill holes, and simplify the outline to exactly
N corners (Douglas-Peucker, curvature-adaptive).  python3 molding_outline.py view_prefix paint_hue_ranges N [paint_min_sat] [close_px] [hull]
paint_hue_ranges like '0-9,165-180' (OpenCV hue).  Writes <prefix>_outline.json (+ _seg.png record)."""
import sys, json, numpy as np, cv2
pre, hues, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); SAT = int(sys.argv[4]) if len(sys.argv) > 4 else 80; CL = int(sys.argv[5]) if len(sys.argv) > 5 else 9; HULL = len(sys.argv) > 6 and sys.argv[6] == 'hull'
a = cv2.imread(pre + '.png', cv2.IMREAD_UNCHANGED); al = a[..., 3] > 128; hsv = cv2.cvtColor(a[..., :3], cv2.COLOR_BGR2HSV)
H, S, V = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
paint = np.zeros_like(al)
for r in hues.split(','):
    h0, h1 = map(int, r.split('-')); paint |= (H >= h0) & (H <= h1) & (S > SAT) & (V > 40)
m = (al & ~paint).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))           # drops the painted shut / panel lines
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((CL, CL), np.uint8))
k, lab, st, cen = cv2.connectedComponentsWithStats(m)
R = a.shape[0]; c0 = np.array([R / 2, R / 2])
i = 1 + int(np.argmax([st[j, 4] / (1 + np.linalg.norm(cen[j] - c0) / 100) for j in range(1, k)]))
sel = (lab == i).astype(np.uint8)
ff = np.pad(sel, 1); h, w = ff.shape; cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1); sel = sel | (1 - ff[1:-1, 1:-1])
cs, _ = cv2.findContours(sel, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
if HULL: c = cv2.convexHull(c)          # bridge notches left by chrome / highlight texels inside the lamp art
lo, hi = 0.1, 60.0
for _ in range(60):
    eps = 0.5 * (lo + hi); p = cv2.approxPolyDP(c, eps, True)
    if len(p) > N: lo = eps
    elif len(p) < N: hi = eps
    else: break
P = p[:, 0].astype(float); print(pre, 'corners', len(P), 'eps px', round(eps, 2), 'area px', int(sel.sum()))
J = json.load(open(pre + '.json')); J.update(outline_px=P.tolist(), mask_area_px=int(sel.sum()))
json.dump(J, open(pre + '_outline.json', 'w'))
r = a[..., :3].copy(); r[sel > 0] = (r[sel > 0] * 0.5 + np.array([0, 160, 0]) * 0.5).astype(np.uint8)
cv2.polylines(r, [P.astype(np.int32)], True, (0, 0, 255), 3); cv2.imwrite(pre + '_seg.png', r)
