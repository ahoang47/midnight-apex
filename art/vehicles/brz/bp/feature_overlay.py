"""Clay orthos rasterised in the blueprint's own frame (shaded, materials), with the blueprint's traced lines on top:
silhouette (red), glass / DLO outline (cyan), body feature lines (yellow), lamp outlines used for the build (magenta).
Writes renders/clay_raw/feat_{view}.png and the sheet renders/brz_clay_bp_feature_overlay{SUF}_800.jpg."""
import numpy as np, cv2, json, sys, os
sys.path.insert(0, 'parts'); import brz_bp as BP
from scipy import ndimage as ndi
SUF = sys.argv[1] if len(sys.argv) > 1 else '_p4'
UP = 6
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']
T = np.load('bp/tris_carframe.npy').reshape(-1, 3, 3); TM = np.load('bp/tris_material.npy')
z = np.load('bp/bp_classes.npz')
COL = {'clay': (175, 175, 175), 'clay_glass': (70, 62, 58), 'clay_lamp': (150, 120, 105), 'clay_trim': (40, 40, 40),
       'under': (25, 25, 25), 'tire': (30, 30, 30), 'rim': (150, 150, 155)}
L = np.array([0.35, 0.45, 0.82]); L /= np.linalg.norm(L)
def proj(view, P):
    X0, Y0 = int(z[f'{view}_X0']), int(z[f'{view}_Y0'])
    if view == 'side':
        u = (float(z['side_CM']) - X0) - P[..., 0] / S; v = (float(z['side_ZF']) - Y0) - P[..., 2] / S; dep = -P[..., 1]
    elif view == 'top':
        u = (float(z['top_CM']) - X0) - P[..., 0] / S; v = float(z['top_CR']) - P[..., 1] / S; dep = -P[..., 2]
    else:
        sg = 1 if view == 'front' else -1
        u = float(z[f'{view}_CC']) + sg * P[..., 1] / S; v = (float(z[f'{view}_ZF']) - Y0) - P[..., 2] / S
        dep = -P[..., 0] * sg
    return u, v, dep
def to2d(view, pts):
    pts = np.asarray(pts, float)
    if view == 'side': P = np.c_[pts[:, 0], np.zeros(len(pts)), pts[:, 1]]
    elif view == 'top': P = np.c_[pts[:, 0], pts[:, 1], np.zeros(len(pts))]
    else: P = np.c_[np.zeros(len(pts)), pts[:, 0], pts[:, 1]]
    u, v, _ = proj(view, P); return np.c_[u, v]
def render(view):
    M = z[f'{view}_M']; H, Wd = M.shape
    img = np.full((H * UP, Wd * UP, 3), 255, np.uint8)
    u, v, dep = proj(view, T); order = np.argsort(dep.mean(1))[::-1]     # far first
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    for t in order:
        c = np.array(COL.get(str(TM[t]), (175, 175, 175)), float)
        sh = 0.55 + 0.45 * abs(float(n[t] @ L)); col = tuple(int(x) for x in np.clip(c * sh, 0, 255))
        P = np.stack([u[t], v[t]], -1) * UP
        cv2.fillPoly(img, [np.round(P * 8).astype(np.int32)], col, shift=3)
    # blueprint lines
    up = lambda A: cv2.resize(A.astype(np.uint8), (Wd * UP, H * UP), interpolation=cv2.INTER_NEAREST) > 0
    Mu = up(M); sil = Mu & ~ndi.binary_erosion(Mu, iterations=2)
    G = z[f'{view}_GL']; Gu = up(G); gl = Gu & ~ndi.binary_erosion(Gu, iterations=2)
    Du = up(z[f'{view}_D'] & ~z[f'{view}_TY'] if f'{view}_TY' in z else z[f'{view}_D'])
    Du = Du & ~ndi.binary_dilation(up(ndi.binary_erosion(M, iterations=0) & ~ndi.binary_erosion(M)), iterations=3)
    img[Du] = (0, 215, 255); img[gl] = (255, 230, 0); img[sil] = (40, 40, 230)
    # lamp outlines used by the build
    for key in ('side', 'side_f') if view == 'side' else (('top', 'top_f') if view == 'top' else (view,)):
        pg = BP.FEAT['lamp'].get(key)
        if pg is None: continue
        for sgn in ((1, -1) if view in ('rear', 'front', 'top') else (1,)):
            q = [(a, sgn * b) for a, b in pg] if view == 'top' else ([(sgn * a, b) for a, b in pg] if view in ('rear', 'front') else pg)
            cv2.polylines(img, [np.round(to2d(view, q) * UP * 8).astype(np.int32)], True, (230, 0, 230), 1, cv2.LINE_AA, shift=3)
    cv2.imwrite(f'renders/clay_raw/feat_{view}.png', img); return img
ims = {v: render(v) for v in ('side', 'top', 'front', 'rear')}
def lab(im, t):
    im = cv2.copyMakeBorder(im, 34, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(im, t, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2, cv2.LINE_AA); return im
def hcat(a, b):
    h = max(a.shape[0], b.shape[0]); f = lambda m: cv2.copyMakeBorder(m, 0, h - m.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    return np.hstack([f(a), f(b)])
r1 = hcat(lab(ims['side'], 'SIDE: clay (blueprint frame) + blueprint lines'), lab(ims['front'], 'FRONT'))
r2 = hcat(lab(ims['top'], 'TOP'), lab(ims['rear'], 'REAR'))
w = max(r1.shape[1], r2.shape[1])
pad = lambda a: cv2.copyMakeBorder(a, 0, 0, 0, w - a.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))
sheet = np.vstack([pad(r1), pad(r2)])
leg = np.full((40, w, 3), 255, np.uint8)
for k, (t, c) in enumerate((('silhouette', (40, 40, 230)), ('glass / DLO', (255, 230, 0)), ('body feature lines', (0, 215, 255)), ('lamp outlines (build)', (230, 0, 230)))):
    x = 12 + k * 330; cv2.rectangle(leg, (x, 12), (x + 26, 30), c, -1); cv2.putText(leg, t, (x + 34, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
sheet = np.vstack([sheet, leg])
cv2.imwrite('renders/clay_raw/feature_overlay_full.png', sheet)
h = int(round(sheet.shape[0] * 800 / sheet.shape[1]))
cv2.imwrite(f'renders/brz_clay_bp_feature_overlay{SUF}_800.jpg', cv2.resize(sheet, (800, h), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('ok', sheet.shape)
