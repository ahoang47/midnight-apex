"""MX-5 (ND) body paint (1024^2, PSX / early-PS2): made-up "Daybreak Yellow" livery (period nod to the NA's 1992
yellow, picked because the lineup is already blue / red / blue / white), black fabric soft top, black windshield frame,
black lower lip / sill strip / rear diffuser band.  Baked AO + painted form shading; every detail the lean mesh doesn't
model is painted from the blueprint VECTORS (bp/feature_vectors.json, bp/vectors.py):
  panel / shut / DLO lines (TRANSPORT polylines), faint creases (DETAILS), lamps, grille slats, plates, made-up badge.
The ND sculpting the clay keeps flat is PAINTED as form shading driven by the DETAILS vectors (A.3.2 vectors, never a
traced raster): fender peaks + hood centre dip (top-view hood creases), the door scoop under the rear-fender crest
line and the arch flares (side view), the rolled tail corners and the tail crease (rear view).
Each view's vectors are drawn anti-aliased into a 2 mm/px canvas for that view (front seen from the front, rear seen
from behind so text reads); every texel samples the canvas of the view that owns it (dominant normal axis).
RGB555 + 4x4 Bayer.   python3 tex/make_body_mx5.py texels.npz out.png ao.png"""
import numpy as np, sys, os, json, cv2
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
src, dst = sys.argv[1], sys.argv[2]; ao_png = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load(src); P, N, FN, MK = D['pos'], D['nrm'], D['fnr'], D['mask']; SL = list(D['slots']); TS = P.shape[0]
V = json.load(open(os.path.join(HERE, 'bp', 'feature_vectors.json'))); FC = json.load(open(os.path.join(HERE, 'bp', 'fair_curves.json')))
CL = {k: SL.index(k) for k in SL}
# ---------------------------------------------------------------- palette (made-up livery)
PAINT = np.array([226, 182, 38], np.float32)           # "Daybreak Yellow" (warm, slightly deep so spec/env have headroom)
LINE = (112, 80, 14); CREASE = (196, 152, 30)
GBLACK = (22, 23, 26); MATTE = (16, 16, 18); MESH_BG = (10, 10, 12); MESH = (40, 42, 47)
GLASS = (24, 32, 44); FABRIC = (30, 30, 33); SEAM = (16, 16, 18)
RED = (176, 18, 22); RED_D = (92, 8, 12); RED_HI = (236, 70, 60); SMOKE = (70, 16, 20)
CHROME = (168, 172, 180); MIRROR_GL = (60, 70, 86)
RES = 0.002
EXT = dict(side=((-2.4, 2.4), (-0.1, 1.6)), top=((-2.4, 2.4), (-1.1, 1.1)), front=((-1.1, 1.1), (-0.1, 1.6)), rear=((-1.1, 1.1), (-0.1, 1.6)))
SG = dict(side=1.0, top=1.0, front=1.0, rear=-1.0)     # rear canvas u = -y (seen from behind: plate / badge text reads)
def canvas(view):
    (u0, u1), (v0, v1) = EXT[view]; W, H = int((u1 - u0) / RES), int((v1 - v0) / RES)
    col = np.zeros((H, W, 3), np.uint8); a = np.zeros((H, W), np.uint8)
    sg = SG[view]
    def px(pts): pts = np.asarray(pts, float) * [sg, 1.0]; return np.round(np.c_[(pts[:, 0] - u0) / RES, (v1 - pts[:, 1]) / RES] * 16).astype(np.int32)
    def pxi(u, v): return int(round((u * sg - u0) / RES)), int(round((v1 - v) / RES))
    def fill(P_, c, al=255):
        cv2.fillPoly(col, [px(P_)], tuple(int(x) for x in c), cv2.LINE_AA, shift=4); cv2.fillPoly(a, [px(P_)], al, cv2.LINE_AA, shift=4)
    def line(P_, c, w=2, closed=False, al=230):
        cv2.polylines(col, [px(P_)], closed, tuple(int(x) for x in c), w, cv2.LINE_AA, shift=4); cv2.polylines(a, [px(P_)], closed, al, w, cv2.LINE_AA, shift=4)
    def mask_of(polys):
        m = np.zeros((H, W), np.uint8)
        for p in polys: cv2.fillPoly(m, [px(p)], 1, cv2.LINE_8, shift=4)
        return m > 0
    def ellipse(c, r, colr, w=-1):
        u, v = pxi(*c); cv2.ellipse(col, (u, v), (int(r[0] / RES), int(r[1] / RES)), 0, 0, 360, colr, w, cv2.LINE_AA)
        cv2.ellipse(a, (u, v), (int(r[0] / RES), int(r[1] / RES)), 0, 0, 360, 255, w, cv2.LINE_AA)
    o = V[view]['polys']; g = lambda k: o.get(k, [])
    grille = None
    # ------- view-specific fills (order: big black areas -> lamps / glass -> mesh -> lines -> badges / plates)
    if view == 'side':
        for p in g('A_PILLAR_S'): fill(p, GBLACK)                                  # black windshield frame (photo check)
        for p in g('SOFTTOP_S'): fill(p, FABRIC)
        for p in g('DLO_GLASS'): fill(p, GLASS)
        for p in g('TAIL_S'): fill(p, RED); line(p, RED_D, 3, True)
        for p in g('HEADLAMP_S'): fill(p, (34, 37, 46)); line(p, (20, 20, 24), 3, True)
        fill([(0.585, 0.640), (0.640, 0.652), (0.648, 0.643), (0.592, 0.632)], CHROME)   # fender side garnish (small chrome blade behind the front arch)
    if view == 'top':
        for p in g('ROOF_T'): fill(p, FABRIC)
        for p in g('SIDE_GLASS_T') + g('WS_T'): fill(p, GLASS)
        for p in V['top']['details']:                                             # soft-top seams (DETAILS) stitched darker
            q = np.asarray(p)
            if q[:, 0].max() < -0.25 and q[:, 0].min() > -1.2: line(p, SEAM, 3, al=200)
    if view == 'front':
        for p in g('WS_F'): fill(p, GLASS)
        for p in g('HEADLAMP_F'): fill(p, (34, 37, 46)); line(p, (16, 16, 20), 3, True)
        gp = np.vstack([np.asarray(p) for p in g('GRILLE_F')])
        hull = cv2.convexHull(np.float32(gp))[:, 0, :]
        fill(hull, MESH_BG); m = mask_of([hull]); yy, xx = np.nonzero(m)
        c = 0.034 / RES; on = (yy % c) < c * 0.34; col[yy[on], xx[on]] = MESH        # horizontal slats (ND grille, photos)
        for p in g('GRILLE_F'): line(p, MESH, 2, True)                              # blueprint cell grid, dark (reads as slat breaks)
        for p in g('SIDE_INTAKE_F'): fill(p, MESH_BG); line(p, GBLACK, 2, True)
        for p in g('LIP_F'): fill(p, MATTE)
        grille = m
    if view == 'rear':
        for p in g('ROOF_R'): fill(p, FABRIC)
        for p in g('REAR_GLASS_R'): fill(p, GLASS)
        for p in g('MIRROR_R'): fill(p, MIRROR_GL); line(p, GBLACK, 3, True)
        for p in g('DIFFUSER_R'): fill(p, MATTE)
        for p in g('REFLECTOR_R'):                                                # photo check: dark corner recess with a slim reflector, not a red disc
            q = np.asarray(p); c_ = q.mean(0); fill(q, MATTE); fill(c_ + (q - c_) * [0.70, 0.22], RED_D)
        for p in g('EXHAUST_R'): fill(p, (8, 8, 9)); line(p, CHROME, 4, True)
        for p in g('TAIL_R'):
            q = np.asarray(p); c_ = q.mean(0); r_ = 0.5 * np.ptp(q, 0)
            if r_[0] / r_[1] < 1.6:                                                 # the round ring lamp (ND signature): red lens, lit LED ring, dark core
                fill(q, RED_D); ellipse(c_, r_ * 0.86, RED_HI, max(3, int(0.012 / RES))); ellipse(c_, r_ * 0.55, RED); ellipse(c_, r_ * 0.30, SMOKE)
                ellipse(c_ + [0.0, 0.012], r_ * [0.18, 0.08], (238, 120, 110))     # glint
                line(q, (30, 6, 8), 3, True)
            else:                                                                 # the bar running outboard: smoked red, thin lit line, white reverse segment
                fill(q, SMOKE); line(q, (30, 6, 8), 3, True)
                yb = np.linspace(q[:, 0].min() + 0.02, q[:, 0].max() - 0.02, 12); zb = np.full_like(yb, c_[1] + 0.004)
                line(np.c_[yb, zb], RED_HI, 4)
    # ------- lines: TRANSPORT (panel / shut / DLO / lamp edges), DETAILS faint
    lampm = mask_of(g('HEADLAMP_F')) if view == 'front' else None
    for p in V[view]['details']:
        if lampm is not None:
            u, v = pxi(*np.asarray(p).mean(0))
            if 0 <= v < H and 0 <= u < W and lampm[v, u]: continue              # lamp internals (projector ring) live in the lamp atlas, not on the paint
            if np.ptp(np.asarray(p)[:, 0]) < 0.03 and abs(np.asarray(p)[:, 0].mean()) > 0.6: continue   # lamp-tip tick outboard of the lens
        line(p, CREASE, 2, al=70)
    for p in V[view]['lines']:
        if grille is not None:
            q = np.asarray(p).mean(0); u, v = pxi(*q)
            if 0 <= v < H and 0 <= u < W and grille[v, u]: continue              # grille cells drawn above (dark)
        line(p, LINE, 3)
    # ------- plates (flat, made up) + badges (made-up badge in place of the dropped maker emblem)
    if view in ('front', 'rear'):
        if view == 'rear':
            pr = np.vstack(g('PLATE_R')); zc = 0.5 * (pr[:, 1].min() + pr[:, 1].max()); hw = 0.5 * np.ptp(pr[:, 0]) - 0.012; hh = 0.5 * np.ptp(pr[:, 1]) - 0.008
        else: zc, hw, hh = 0.330, 0.200, 0.048
        R_ = [(-hw, zc - hh), (hw, zc - hh), (hw, zc + hh), (-hw, zc + hh)]
        fill(R_, (226, 226, 216)); line(R_, (40, 40, 40), 3, True)
        txt = 'RD 15-89'; (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3); fs = 0.80 * (2 * hw / RES) / tw
        cx_ = (pxi(-hw, 0)[0] + pxi(hw, 0)[0]) // 2; cy_ = pxi(0, zc)[1]
        cv2.putText(col, txt, (int(cx_ - tw * fs / 2), int(cy_ + th * fs / 2)), cv2.FONT_HERSHEY_SIMPLEX, fs, (28, 30, 40), max(2, int(3 * fs)), cv2.LINE_AA)
        zb = 0.574 if view == 'front' else 0.810                                  # dropped emblem centres (vectors.py)
        ellipse((0.0, zb), (0.050, 0.030), CHROME, 4)                              # made-up badge: plain chrome oval ring + a "wing" chevron
        fill([(-0.034, zb - 0.010), (0.0, zb + 0.016), (0.034, zb - 0.010), (0.022, zb - 0.010), (0.0, zb + 0.004), (-0.022, zb - 0.010)], CHROME)
        if view == 'rear': fill([(0.17, 0.712), (0.27, 0.712), (0.27, 0.721), (0.17, 0.721)], (150, 154, 162))   # small chrome script bar, tail left of the badge (illegible)
    return col, a, (u0, v1)
CV = {v: canvas(v) for v in EXT}
x, y, z = P[..., 0], P[..., 1], P[..., 2]; nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
filled = MK >= 0
fx, fy, fz = FN[..., 0], FN[..., 1], FN[..., 2]                                 # face normals choose the owner view (no seams across a face)
dom = np.argmax(np.stack([np.abs(fx), np.abs(fy), np.abs(fz)]), 0)
XF, XR = x[filled].max(), x[filled].min()
nose = filled & (fx > 0.50) & (x > XF - 0.55); tail = filled & (fx < -0.50) & (x < XR + 0.40)   # wrap-around lamps/bumper ends: keep the end views
front_o = filled & (((dom == 0) & (fx > 0)) | nose); rear_o = filled & (((dom == 0) & (fx < 0)) | tail)
own = dict(side=filled & (dom == 1) & ~front_o & ~rear_o, top=filled & (dom == 2) & (fz > 0) & ~front_o & ~rear_o, front=front_o, rear=rear_o)
coords = dict(side=(x, z), top=(x, y), front=(y, z), rear=(-y, z))
img = np.zeros((TS, TS, 3), np.float32) + PAINT
alpha = np.zeros((TS, TS), np.float32); feat = np.zeros((TS, TS, 3), np.float32)
for v, m in own.items():
    col, a, (u0, v1) = CV[v]; u, w = coords[v]
    c = np.clip(((u - u0) / RES).astype(int), 0, col.shape[1] - 1); r = np.clip(((v1 - w) / RES).astype(int), 0, col.shape[0] - 1)
    feat[m] = col[r[m], c[m]]; alpha[m] = a[r[m], c[m]] / 255.0
trim = MK == CL['clay_trim']                                                     # mirrors: body colour; only the rear (glass) face takes its canvas
alpha[trim & ~rear_o] = 0.0
img = img * (1 - alpha[..., None]) + feat * alpha[..., None]
# black windshield frame (photo check): every body texel inside the side-view A_PILLAR_S strip, whichever view owns it
_m = np.zeros(CV['side'][0].shape[:2], np.uint8); (u0s, _), (_, v1s) = EXT['side']
for p in V['side']['polys'].get('A_PILLAR_S', []):
    cv2.fillPoly(_m, [np.round(np.c_[(np.asarray(p)[:, 0] - u0s) / RES, (v1s - np.asarray(p)[:, 1]) / RES] * 16).astype(np.int32)], 1, cv2.LINE_8, shift=4)
_c = np.clip(((x - u0s) / RES).astype(int), 0, _m.shape[1] - 1); _r = np.clip(((v1s - z) / RES).astype(int), 0, _m.shape[0] - 1)
frame = filled & (MK == CL['clay']) & (_m[_r, _c] > 0) & (z > 0.86); img[frame] = GBLACK
# lower body: thin black sill strip, black underside-facing surfaces
low = filled & (MK == CL['clay']) & ((z < 0.212) | (nz < -0.55)); img[low] = MATTE
img[MK == CL['under']] = (10, 10, 11); img[MK == CL['clay_glass']] = GLASS
img[MK == CL['clay_pocket']] = (12, 12, 14); img[MK == CL['clay_chrome']] = CHROME
pf = MK == CL['clay_pocketfloor']; img[pf] = np.where(alpha[pf][..., None] > 0.3, feat[pf], MESH_BG)
# soft top: fabric (canvases already give FABRIC where the region exists; the loft's top slot is fabric everywhere) + weave
st = MK == CL['clay_softtop']
img[st] = FABRIC
seam = st & (alpha > 0.3) & (np.abs(feat - np.array(FABRIC, np.float32)).sum(-1) > 40) & (np.abs(feat - np.array(GLASS, np.float32)).sum(-1) > 12)
img[seam] = SEAM                                                                 # panel / seam lines on the fabric: darker stitching, not yellow
img[st & (alpha > 0.5) & (np.abs(feat - np.array(GLASS, np.float32)).sum(-1) <= 12)] = GLASS
rng = np.random.default_rng(3); weave = 1.0 + 0.06 * ((np.indices((TS, TS)).sum(0) % 2) - 0.5) + rng.normal(0, 0.025, (TS, TS))
# ---------------------------------------------------------------- painted form shading
shade = 0.80 + 0.22 * np.clip(nz, -0.3, 1.0)                                    # sky from above
shade *= 0.82 + 0.18 * np.clip((z - 0.18) / 0.45, 0, 1)                         # darker toward the sills
shade += 0.08 * np.exp(-((nz - 0.45) / 0.18) ** 2) * (np.abs(ny) > 0.3)         # soft shoulder highlight
body = filled & ((MK == CL['clay']) | trim)
def poly_interp(p, xs, k_in=0, k_out=1):
    q = np.asarray(p); o = np.argsort(q[:, k_in]); return np.interp(xs, q[o, k_in], q[o, k_out], left=np.nan, right=np.nan)
# (1) hood: fender peaks + centre dip.  Ridge line = top-view hood creases (DETAILS, x .54-1.64, |y| .36-.67)
hc = [np.asarray(p) for p in V['top']['details'] if np.asarray(p)[:, 0].min() > 0.4 and np.asarray(p)[:, 0].max() > 1.5]
ridge = poly_interp(np.abs(hc[0]), x, 0, 1)
hood = body & (nz > 0.35) & (x > 0.45) & ~np.isnan(ridge)
dd = np.abs(y) - np.nan_to_num(ridge)
tx = np.clip((x - 0.45) / 0.15, 0, 1) * np.clip((1.75 - x) / 0.20, 0, 1)
hs = (0.18 * np.exp(-((dd - 0.035) / 0.045) ** 2)                               # crest of the fender peak (catches the sky)
      - 0.13 * np.exp(-((dd + 0.075) / 0.060) ** 2)                             # valley just inboard of the peak
      - 0.08 * np.exp(-(y / 0.22) ** 2)) * tx                                   # shallow centre dip
shade[hood] += hs[hood]
# (2) sides: the ND door scoop under the rear-fender crest (side DETAILS line from the deck down into the door), arch flares
sd = [np.asarray(p) for p in V['side']['details']]
crest = max(sd, key=lambda q: np.ptp(q[:, 0]) * (q[:, 1].max() > 0.8))         # x -1.02 .. -0.17, z .88 -> .54
zc = poly_interp(crest, x, 0, 1)
side = body & (np.abs(ny) > 0.45) & (z > 0.215)
dz = z - np.nan_to_num(zc, nan=-9)
fx_ = np.clip((x + 1.05) / 0.12, 0, 1) * np.clip((-0.17 - x) / 0.25, 0, 1)
ss = np.where(dz > 0, 0.11 * np.exp(-dz / 0.05), -0.17 * np.exp(dz / 0.12)) * fx_
ext = side & (x > -0.17) & (x < 0.60)                                           # the scoop runs on, fading, to the front of the door
zl = float(crest[np.argmax(crest[:, 0]), 1]); ef = np.clip((0.60 - x) / 0.77, 0, 1) ** 1.5
ss2 = np.where(z > zl, 0.0, -0.15 * np.exp((z - zl) / 0.12)) * ef
ok = side & ~np.isnan(zc); shade[ok] += ss[ok]; shade[ext] += ss2[ext]
for A in (FC['arch_f'], FC['arch_r']):                                          # arch flares: bright lip band just outside the arch circle
    rr = np.hypot(x - A['xc'], z - A['zc']) - A['r']
    fl = side & (z > A['zc'] - 0.05) & (rr > 0)
    shade[fl] += (0.12 * np.exp(-((rr - 0.035) / 0.035) ** 2) - 0.05 * np.exp(-((rr - 0.11) / 0.04) ** 2))[fl]
lowdoor = poly_interp(max(sd, key=lambda q: np.ptp(q[:, 0]) * (q[:, 1].max() < 0.45) * (q[:, 1].min() > 0.25)), x, 0, 1)
ld = side & ~np.isnan(lowdoor) & (z < np.nan_to_num(lowdoor, nan=-9))
shade[ld] -= 0.10                                                               # tucked rocker under the lower door line
# (3) tail: rolled corners, highlight above the tail crease, darker below it
rc = max([np.asarray(p) for p in V['rear']['details']], key=lambda q: np.ptp(q[:, 0]))   # crease across the tail, z ~.57-.62
zr = poly_interp(rc * [-1, 1], -y, 0, 1)
tail_ = body & rear_o & ~np.isnan(zr)
dzr = z - np.nan_to_num(zr)
ts = np.where(dzr > 0, 0.10 * np.exp(-((dzr - 0.04) / 0.05) ** 2), -0.10 * np.exp(dzr / 0.10))
shade[tail_] += ts[tail_]
rear_all = body & rear_o
shade[rear_all] -= (0.20 * np.clip(-nx, 0, 1) * np.clip(np.abs(ny) / 0.6, 0, 1) ** 1.5)[rear_all]   # tail corners roll away (normal-driven: no seam at the owner switch)
sb = body & (nx < -0.15) & ~rear_o; shade[sb] -= (0.20 * np.clip(-nx, 0, 1) * np.clip(np.abs(ny) / 0.6, 0, 1) ** 1.5)[sb]
shade[st] *= weave[st]
if ao_png:
    ao = np.asarray(Image.open(ao_png).convert('L').resize((TS, TS)), np.float32)[::-1] / 255.0
    shade *= 0.38 + 0.62 * ao ** 0.9
img = img * shade[..., None]
img = np.minimum(img, 236.0)
img[~filled] = PAINT * 0.6
out = rgb555_bayer(Image.fromarray(np.clip(img[::-1], 0, 255).astype(np.uint8)))
a = np.asarray(out).copy(); fm = filled[::-1].astype(np.uint8)
for _ in range(4):
    dil = cv2.dilate(a, np.ones((3, 3), np.uint8)); ring = (cv2.dilate(fm, np.ones((3, 3), np.uint8)) > 0) & (fm == 0)
    a[ring] = dil[ring]; fm = fm | ring.astype(np.uint8)
Image.fromarray(a).save(dst); print('body tex', dst, 'texels used', round(filled.mean() * 100, 1), '%')
