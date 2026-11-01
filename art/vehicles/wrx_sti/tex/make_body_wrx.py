"""WRX lean body paint (1024^2, PSX / early-PS2): WR-blue paint + baked AO + painted form shading, with every lost
geometry detail painted in: lamps, grille / intakes / vents, black trim, glass edges, and the panel / shut lines.
All features are VECTORS (bp/feature_vectors.json, from bp/vectorize.py): each view's vectors are drawn
anti-aliased into a 2 mm/px canvas for that view, and every texel samples the canvas of the view that owns it
(dominant normal axis: side / top / front / rear).  RGB555 + 4x4 Bayer.
python3 tex/make_body_wrx.py texels.npz out.png ao.png"""
import numpy as np, sys, os, json, cv2
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
src, dst = sys.argv[1], sys.argv[2]; ao_png = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load(src); P, N, MK = D['pos'], D['nrm'], D['mask']; TS = P.shape[0]
V = json.load(open(os.path.join(HERE, 'bp', 'feature_vectors.json')))
PAINT = np.array([30, 62, 160], np.float32)           # WR-blue-ish (made-up livery colour), blueprint draws blue too
LINE = np.array([10, 20, 55]); BLACK = np.array([16, 16, 18]); GLASS = np.array([24, 32, 44])
LENS = np.array([196, 204, 214]); LENS_RIM = np.array([90, 96, 110]); RED = np.array([196, 24, 22]); RED_RIM = np.array([90, 10, 10])
FOG = np.array([170, 178, 190])
HOUSING = np.array([26, 28, 32]); IND = np.array([186, 150, 92]); IND_RIM = np.array([70, 58, 40]); IND_HI = np.array([214, 196, 160])
LO = json.load(open(os.path.join(HERE, 'bp', 'lamp_outlines.json')))
_fk = [np.asarray(p) for p in V['front']['polys'].get('K', []) if 0.5 < np.mean(np.asarray(p)[:, 0]) < 0.75 and 0.30 < np.mean(np.asarray(p)[:, 1]) < 0.55]
_fb = np.vstack(_fk) if _fk else np.array([[0.524, 0.329], [0.718, 0.518]])
FOGC = (_fb.min(0) + _fb.max(0)) / 2; FOGR = (_fb.max(0) - _fb.min(0)) / 2      # blueprint fog housing box (rounded square)
_t = np.linspace(0, 2 * np.pi, 72, endpoint=False)
FOG_HOUSING = FOGC + FOGR * np.c_[np.sign(np.cos(_t)) * np.abs(np.cos(_t)) ** 0.5, np.sign(np.sin(_t)) * np.abs(np.sin(_t)) ** 0.5]
FOGBOX = lambda q: (np.abs(np.abs(q.mean(0)[0]) - FOGC[0]) < 0.05) and (np.abs(q.mean(0)[1] - FOGC[1]) < 0.05)
RES = 0.002
EXT = dict(side=((-2.4, 2.4), (-0.1, 1.6)), top=((-2.4, 2.4), (-1.1, 1.1)), front=((-1.1, 1.1), (-0.1, 1.6)), rear=((-1.1, 1.1), (-0.1, 1.6)))
def canvas(view):
    (u0, u1), (v0, v1) = EXT[view]; W, H = int((u1 - u0) / RES), int((v1 - v0) / RES)
    col = np.zeros((H, W, 3), np.uint8); a = np.zeros((H, W), np.uint8)
    sgn = -1.0 if view == 'rear' else 1.0         # rear canvas runs right-to-left as seen from behind (plate text reads)
    def px(pts): pts = np.asarray(pts, float) * [sgn, 1.0]; return np.round(np.c_[(pts[:, 0] - u0) / RES, (v1 - pts[:, 1]) / RES] * 16).astype(np.int32)
    o = V[view]['polys']
    def fill(key, c, rim=None, rim_w=3):
        for p in o.get(key, []):
            cv2.fillPoly(col, [px(p)], tuple(int(x) for x in c), cv2.LINE_AA, shift=4); cv2.fillPoly(a, [px(p)], 255, cv2.LINE_AA, shift=4)
            if rim is not None: cv2.polylines(col, [px(p)], True, tuple(int(x) for x in rim), rim_w, cv2.LINE_AA, shift=4)
    fill('GL', GLASS)
    # head / fog lamps are lens-cap geometry with their own painted atlas tiles (parts/lamps_lean.py,
    # tex/lamp/paint_lamps.py).  Here: dark housing under the caps (only seen through the rim gap), a clean fog-lamp
    # housing instead of the ragged blueprint black-ring contours, no outline specks around the head lamp, and the
    # corner indicator (clear lens, amber bulb) from the traced outline (front) / the blueprint side-marker shape (side).
    near_lamp = lambda q: any(np.min(np.hypot(*(np.abs(np.asarray(q))[:, None, :] - np.asarray(LO[k])[None]).transpose(2, 0, 1)), axis=1).min() < 0.045 for k in ('head', 'fog'))
    for p in o.get('K', []):
        q = np.asarray(p); a_ = 0.5 * abs(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]))
        if view == 'front' and near_lamp(q) and (a_ < 6e-4 or FOGBOX(q)): continue
        if view == 'side' and a_ < 6e-4 and np.min(np.hypot(*(q[:, None, :] - np.asarray(LO['marker_side'])[None]).transpose(2, 0, 1))) < 0.03: continue
        cv2.fillPoly(col, [px(p)], tuple(int(x) for x in BLACK), cv2.LINE_AA, shift=4); cv2.fillPoly(a, [px(p)], 255, cv2.LINE_AA, shift=4)
    def shape(P, c, rim=None, rim_w=3):
        cv2.fillPoly(col, [px(P)], tuple(int(x) for x in c), cv2.LINE_AA, shift=4); cv2.fillPoly(a, [px(P)], 255, cv2.LINE_AA, shift=4)
        if rim is not None: cv2.polylines(col, [px(P)], True, tuple(int(x) for x in rim), rim_w, cv2.LINE_AA, shift=4)
    if view == 'front':
        for sd in (1, -1):
            m_ = np.array([sd, 1.0])
            shape(FOG_HOUSING * m_, BLACK)
            for k in ('head', 'fog'):
                c_ = np.mean(LO[k], 0); shape((c_ + (np.asarray(LO[k]) - c_) * 0.97) * m_, HOUSING)
            ind = np.asarray(LO['indicator']) * m_; shape(ind, IND, IND_RIM, 3)
            c_ = ind.mean(0); shape(c_ + (ind - c_) * [0.35, 0.80] + [-0.003 * sd, 0.004], IND_HI)
    if view == 'side':                               # side marker behind the head lamp (traced outline): clear lens, amber bulb
        q = np.asarray(LO['marker_side']); shape(q, IND, IND_RIM, 3); c_ = q.mean(0)
        shape(c_ + (q - c_) * 0.45 + [0.004, 0.006], IND_HI)
    fill('R', RED, RED_RIM, 4)
    for p in V[view]['lines']:
        cv2.polylines(col, [px(p)], False, tuple(int(x) for x in LINE), 2, cv2.LINE_AA, shift=4); cv2.polylines(a, [px(p)], False, 220, 2, cv2.LINE_AA, shift=4)
    # made-up plate (flat, painted): front bumper centre / rear bumper centre
    if view in ('front', 'rear'):
        zc = 0.43 if view == 'front' else 0.60
        p = [(-0.17 * sgn, zc - 0.055), (0.17 * sgn, zc - 0.055), (0.17 * sgn, zc + 0.055), (-0.17 * sgn, zc + 0.055)]
        cv2.fillPoly(col, [px(p)], (226, 226, 216), cv2.LINE_AA, shift=4); cv2.fillPoly(a, [px(p)], 255, cv2.LINE_AA, shift=4)
        cv2.polylines(col, [px(p)], True, (40, 40, 40), 3, cv2.LINE_AA, shift=4)
        cv2.putText(col, 'MA 2001', (int((-0.13 - u0) / RES), int((v1 - zc + 0.025) / RES)), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (30, 30, 40), 3, cv2.LINE_AA)
    return col, a, (u0, v1)
CV = {v: canvas(v) for v in EXT}
x, y, z = P[..., 0], P[..., 1], P[..., 2]; nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
filled = MK >= 0
dom = np.argmax(np.stack([np.abs(nx), np.abs(ny), np.abs(nz)]), 0)
own = dict(side=filled & (dom == 1), top=filled & (dom == 2) & (nz > 0), front=filled & (dom == 0) & (nx > 0), rear=filled & (dom == 0) & (nx < 0))
coords = dict(side=(x, z), top=(x, y), front=(y, z), rear=(-y, z))
img = np.zeros((TS, TS, 3), np.float32) + PAINT
alpha = np.zeros((TS, TS), np.float32); feat = np.zeros((TS, TS, 3), np.float32)
for v, m in own.items():
    col, a, (u0, v1) = CV[v]; u, w = coords[v]
    c = np.clip(((u - u0) / RES).astype(int), 0, col.shape[1] - 1); r = np.clip(((v1 - w) / RES).astype(int), 0, col.shape[0] - 1)
    feat[m] = col[r[m], c[m]]; alpha[m] = a[r[m], c[m]] / 255.0
img = img * (1 - alpha[..., None]) + feat * alpha[..., None]
img[MK == 2] = (10, 10, 11); img[MK == 1] = GLASS; img[MK == 4] = BLACK
# painted form shading (baked-normal style): sky light from above, darker toward the sills, soft shoulder highlight
shade = 0.80 + 0.22 * np.clip(nz, -0.3, 1.0)
shade *= 0.80 + 0.20 * np.clip((z - 0.18) / 0.45, 0, 1)
shade += 0.10 * np.exp(-((nz - 0.45) / 0.18) ** 2) * (np.abs(ny) > 0.3)
if ao_png:
    ao = np.asarray(Image.open(ao_png).convert('L').resize((TS, TS)), np.float32)[::-1] / 255.0
    shade *= 0.35 + 0.65 * ao ** 0.9
img = img * shade[..., None]
img[~filled] = PAINT * 0.6
out = rgb555_bayer(Image.fromarray(np.clip(img[::-1], 0, 255).astype(np.uint8)))
# grow islands 4 px into the empty gutter so mip / nearest sampling at seams never picks the gutter colour
a = np.asarray(out).copy(); fm = filled[::-1].astype(np.uint8)
for _ in range(4):
    dil = cv2.dilate(a, np.ones((3, 3), np.uint8)); ring = (cv2.dilate(fm, np.ones((3, 3), np.uint8)) > 0) & (fm == 0)
    a[ring] = dil[ring]; fm = fm | ring.astype(np.uint8)
Image.fromarray(a).save(dst); print('body tex', dst, 'texels used', round(filled.mean() * 100, 1), '%')
