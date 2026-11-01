"""Clay (rest pose, STI build) rasterised in the blueprint's own frame with materials + simple shading, and the
blueprint's traced lines on top: SIL red, GLASS / DLO cyan, FEAT yellow (beltline, shut lines, lamps, scoop, spoiler).
Lamp / grille outlines used for the decals in magenta.  Writes renders/clay_raw/feat_{view}.png and
renders/wrx_clay_bp_feature_overlay_800.jpg."""
import numpy as np, cv2, json, sys
sys.path.insert(0, 'parts')
from scipy import ndimage as ndi
import wrx_decals as DC
UP = 3
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']
T = np.load('bp/tris_carframe.npy').reshape(-1, 3, 3); TM = np.load('bp/tris_material.npy'); TO = np.load('bp/tris_object.npy')
keep = ~np.isin(TO, ('WRX_Scoop', 'WRX_LipSpoiler')); T, TM = T[keep], TM[keep]
Z = np.load('bp/bp_classes.npz')
COL = {'clay': (178, 178, 178), 'clay_glass': (78, 66, 60), 'clay_lamp': (120, 92, 80), 'clay_trim': (45, 45, 45),
       'under': (25, 25, 25), 'tire': (35, 35, 35), 'rim': (150, 150, 155)}
L = np.array([0.35, 0.45, 0.82]); L /= np.linalg.norm(L)
def proj(view, P):
    X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    if view == 'side': return (float(Z['side_CM']) - X0) - P[..., 0] / S, (float(Z['side_ZF']) - Y0) - P[..., 2] / S, -P[..., 1]
    if view == 'top': return (float(Z['top_CM']) - X0) - P[..., 0] / S, float(Z['top_CR']) + P[..., 1] / S, -P[..., 2]
    sg = 1 if view == 'front' else -1
    return float(Z[f'{view}_CC']) + sg * P[..., 1] / S, (float(Z[f'{view}_ZF']) - Y0) - P[..., 2] / S, -P[..., 0] * sg
def to2d(view, pts):
    pts = np.asarray(pts, float)
    P = {'side': lambda: np.c_[pts[:, 0], np.zeros(len(pts)), pts[:, 1]], 'top': lambda: np.c_[pts[:, 0], pts[:, 1], np.zeros(len(pts))]}.get(view, lambda: np.c_[np.zeros(len(pts)), pts[:, 0], pts[:, 1]])()
    u, v, _ = proj(view, P); return np.c_[u, v]
def render(view):
    M = Z[f'{view}_M']; H, Wd = M.shape
    img = np.full((H * UP, Wd * UP, 3), 255, np.uint8)
    u, v, dep = proj(view, T); order = np.argsort(dep.mean(1))[::-1]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    for t in order:
        c = np.array(COL.get(str(TM[t]), (178, 178, 178)), float); sh = 0.6 + 0.4 * abs(float(n[t] @ L))
        cv2.fillPoly(img, [np.round(np.stack([u[t], v[t]], -1) * UP * 8).astype(np.int32)], tuple(int(x) for x in np.clip(c * sh, 0, 255)), shift=3)
    up = lambda A: cv2.resize(A.astype(np.uint8), (Wd * UP, H * UP), interpolation=cv2.INTER_NEAREST) > 0
    Mu = up(M); sil = Mu & ~ndi.binary_erosion(Mu, iterations=2)
    Gu = up(Z[f'{view}_GL']); gl = Gu & ~ndi.binary_erosion(Gu, iterations=2)
    D = Z[f'{view}_D'] & ~Z[f'{view}_TY']
    Du = up(D) & ~ndi.binary_dilation(sil, iterations=4)
    img[Du] = (0, 215, 255); img[gl] = (255, 230, 0); img[sil] = (40, 40, 230)
    keys = {'side': (('R', 12, None), ('HL', 12, None)), 'front': (('LL', 12, None), ('K', 40, lambda p: np.abs(p[:, 0]).max() < 0.45 and p[:, 1].min() > 0.25 and p[:, 1].max() < 0.70)),
            'rear': (('R', 12, None),), 'top': ()}[view]
    for k, mp, flt in keys:
        for pg in DC.outlines(view, k, mp, 8, flt):
            cv2.polylines(img, [np.round(to2d(view, pg) * UP * 8).astype(np.int32)], True, (230, 0, 230), 2, cv2.LINE_AA, shift=3)
    cv2.imwrite(f'renders/clay_raw/feat_{view}.png', img); return img
ims = {v: render(v) for v in ('side', 'top', 'front', 'rear')}
def lab(im, t):
    im = cv2.copyMakeBorder(im, 40, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(im, t, (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA); return im
def fitw(i, W): return cv2.resize(i, (W, int(round(i.shape[0] * W / i.shape[1]))), interpolation=cv2.INTER_AREA)
W = 2000
side = fitw(lab(ims['side'], 'SIDE: clay in the blueprint frame + blueprint lines'), W)
top = fitw(lab(ims['top'], 'TOP'), W)
fr, re = lab(ims['front'], 'FRONT'), lab(ims['rear'], 'REAR'); h = max(fr.shape[0], re.shape[0])
pad = lambda m: cv2.copyMakeBorder(m, 0, h - m.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
row = fitw(np.hstack([pad(fr), np.full((h, 40, 3), 255, np.uint8), pad(re)]), W)
leg = np.full((60, W, 3), 255, np.uint8)
for k, (t, c) in enumerate((('blueprint silhouette', (40, 40, 230)), ('blueprint glass / DLO', (255, 230, 0)), ('blueprint feature lines', (0, 215, 255)), ('lamp / grille outlines used for the decals', (230, 0, 230)))):
    x = 14 + k * 470; cv2.rectangle(leg, (x, 16), (x + 34, 44), c, -1); cv2.putText(leg, t, (x + 44, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2, cv2.LINE_AA)
sheet = np.vstack([side, top, row, leg])
cv2.imwrite('renders/clay_raw/feature_overlay_full.png', sheet)
cv2.imwrite('renders/wrx_clay_bp_feature_overlay_800.jpg', fitw(sheet, 800), [cv2.IMWRITE_JPEG_QUALITY, 92]); print('ok', sheet.shape)
