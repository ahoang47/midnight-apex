"""GR Corolla body paint (1024^2, PSX / early-PS2): made-up "Apex White" livery with a gloss-black roof, wing, mirror
heads and lower aero, a thin red accent on the front lip and the rear diffuser; baked AO + painted form shading; every
detail the lean mesh doesn't model is painted from the blueprint VECTORS (bp/feature_vectors.json, bp/vectors.py):
  panel / shut / DLO lines (TRANSPORT layer polylines), faint creases (DETAILS layer), lamps, grille + intake
  honeycomb, hood / fender / corner vents, diffuser fins, glass, black trim, plates and made-up badges.
Each view's vectors are drawn anti-aliased into a 2 mm/px canvas for that view (front seen from the front, rear seen
from behind so text reads); every texel samples the canvas of the view that owns it (dominant normal axis).
RGB555 + 4x4 Bayer.   python3 tex/make_body_gr.py texels.npz out.png ao.png"""
import numpy as np, sys, os, json, cv2
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from quant import rgb555_bayer
src, dst = sys.argv[1], sys.argv[2]; ao_png = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load(src); P, N, FN, MK = D['pos'], D['nrm'], D['fnr'], D['mask']; SL = list(D['slots']); TS = P.shape[0]
V = json.load(open(os.path.join(HERE, 'bp', 'feature_vectors.json')))
CL = {k: SL.index(k) for k in SL}
# ---------------------------------------------------------------- palette (made-up livery)
PAINT = np.array([214, 217, 220], np.float32)          # "Apex White" (cool white; values leave headroom for spec/env)
LINE = (122, 125, 132); CREASE = (182, 185, 190)
GBLACK = (22, 23, 26); MATTE = (16, 16, 18); MESH_BG = (10, 10, 12); MESH = (46, 48, 53)
GLASS = (24, 32, 44); RED = (190, 22, 26); RED_D = (110, 10, 14); RED_HI = (226, 70, 64); ACCENT = (200, 24, 30)
LENS = (178, 186, 198); HOUSING = (34, 36, 42); AMBER = (196, 132, 40); CHROME = (168, 172, 180)
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
    def pattern(m, kind, cell):
        """mesh patterns inside mask m (cell in metres): 'hex' honeycomb, 'slat' horizontal slats, 'fin' vertical fins."""
        yy, xx = np.nonzero(m)
        if not len(yy): return
        c = cell / RES
        if kind == 'hex':
            r = (yy // (c * 0.866)).astype(int); q = ((xx + (r % 2) * c / 2) // c).astype(int)
            cx = q * c - (r % 2) * c / 2 + c / 2; cy = r * c * 0.866 + c * 0.433
            d = np.maximum(np.abs(xx - cx) / (c / 2), np.abs(yy - cy) / (c * 0.433))
            on = d > 0.62
        elif kind == 'slat': on = (yy % c) < c * 0.32
        else: on = (xx % c) < c * 0.22
        col[yy, xx] = MESH_BG; col[yy[on], xx[on]] = MESH; a[yy, xx] = 255
    o = V[view]['polys']; g = lambda k: o.get(k, [])
    # ------- view-specific fills (order: big black areas -> lamps / glass -> mesh -> lines -> badges / plates)
    if view == 'side':
        for p in g('ROOF_RAIL') + g('DLO_PILLAR') + g('WING_S') + g('MIRROR_S'): fill(p, GBLACK)
        for p in g('DLO_GLASS') + g('HATCH_GLASS_S'): fill(p, GLASS)
        for p in g('SKIRT_S'): fill(p, MATTE)
        for p in g('TAIL_S'): fill(p, RED); line(p, RED_D, 3, True)
        for p in g('HEADLAMP_S'): fill(p, HOUSING); line(p, (20, 20, 24), 3, True)
        pattern(mask_of(g('FENDER_VENT_S')), 'slat', 0.022)
    if view == 'top':
        for p in g('ROOF_T') + g('WING_T') + g('MIRROR_T'): fill(p, GBLACK)
        for p in g('SIDE_GLASS_T') + g('WS_T'): fill(p, GLASS)
        pattern(mask_of(g('HOOD_VENT_T')), 'slat', 0.020)
    if view == 'front':
        for p in g('MIRROR_F'): fill(p, GBLACK)
        for p in g('WS_F'): fill(p, GLASS)
        for p in g('HEADLAMP_F'): fill(p, HOUSING); line(p, (16, 16, 20), 3, True)
        pattern(mask_of(g('GRILLE_F')), 'hex', 0.052); pattern(mask_of(g('SIDE_INTAKE_F')), 'hex', 0.040)
        for p in g('LIP_F'):
            fill(p, MATTE); q = np.asarray(p); top = q[q[:, 1] > np.percentile(q[:, 1], 70)]
            top = top[np.argsort(top[:, 0])]; line(top, ACCENT, 3)                   # red accent along the lip's top edge
    if view == 'rear':
        for p in g('WING_R') + g('MIRROR_R'): fill(p, GBLACK)
        for p in g('REAR_GLASS_R'): fill(p, GLASS)
        side = [p for p in g('DIFFUSER_R') if abs(np.mean(np.asarray(p)[:, 0])) > 0.2]; cen = [p for p in g('DIFFUSER_R') if abs(np.mean(np.asarray(p)[:, 0])) <= 0.2]
        pattern(mask_of(side), 'hex', 0.040)                                       # big corner vents: mesh (painted, not cut)
        pattern(mask_of(cen), 'fin', 0.10)
        for p in cen: q = np.asarray(p); bot = q[q[:, 1] < np.percentile(q[:, 1], 25)]; line(bot[np.argsort(bot[:, 0])], ACCENT, 3)
        for p in g('EXHAUST_R'): fill(p, (8, 8, 9)); line(p, CHROME, 4, True)
        for p in g('TAIL_R'):
            q = np.asarray(p); fill(q, RED); line(q, RED_D, 4, True)
            c_ = q.mean(0); fill(c_ + (q - c_) * [0.80, 0.42], RED_HI)               # lit bar inside the lens
            if abs(c_[0]) < 0.7: fill(c_ + (q - c_) * [0.30, 0.30] + [0.0, 0.0], (230, 228, 222))   # reversing lamp (inner lens)
    # ------- lines: TRANSPORT (panel / shut / DLO / lamp edges), DETAILS faint
    for p in V[view]['details']: line(p, CREASE, 2, al=90)
    for p in V[view]['lines']: line(p, LINE, 3)
    # ------- plates (flat, made up) + badges (made-up chevron emblem, illegible red block badge)
    if view in ('front', 'rear'):
        zc = 0.3965 if view == 'front' else 0.4795; hw, hh = 0.233, 0.0545
        fill([(-hw, zc - hh), (hw, zc - hh), (hw, zc + hh), (-hw, zc + hh)], (226, 226, 216)); line([(-hw, zc - hh), (hw, zc - hh), (hw, zc + hh), (-hw, zc + hh)], (40, 40, 40), 3, True)
        txt = 'KT 22-16'; (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3); fs = 0.78 * (2 * hw / RES) / tw
        lx = min(pxi(-hw, 0)[0], pxi(hw, 0)[0]); rx = max(pxi(-hw, 0)[0], pxi(hw, 0)[0])
        cx_ = (lx + rx) // 2; cy_ = pxi(0, zc)[1]
        cv2.putText(col, txt, (int(cx_ - tw * fs / 2), int(cy_ + th * fs / 2)), cv2.FONT_HERSHEY_SIMPLEX, fs, (28, 30, 40), max(2, int(3 * fs)), cv2.LINE_AA)
        zb = 0.597 if view == 'front' else 0.880                                  # made-up apex chevron, in place of the (dropped) maker emblem
        chev = [(-0.065, zb - 0.030), (0.0, zb + 0.030), (0.065, zb - 0.030), (0.040, zb - 0.030), (0.0, zb + 0.006), (-0.040, zb - 0.030)]
        fill(chev, CHROME); line(chev, (60, 62, 70), 2, True)
        if view == 'front':                                                      # red block badge, upper-left of the grille (illegible)
            bx = 0.36; fill([(bx, 0.445), (bx + 0.075, 0.445), (bx + 0.075, 0.470), (bx, 0.470)], RED)
            for k in range(3): fill([(bx + 0.012 + k * 0.02, 0.452), (bx + 0.022 + k * 0.02, 0.452), (bx + 0.022 + k * 0.02, 0.463), (bx + 0.012 + k * 0.02, 0.463)], (236, 236, 236))
        else:                                                                    # chrome wordmark bar, hatch right (illegible)
            fill([(-0.42, 0.66), (-0.26, 0.66), (-0.26, 0.675), (-0.42, 0.675)], CHROME)
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
img = img * (1 - alpha[..., None]) + feat * alpha[..., None]
# body below the side-skirt line and the floor-facing surfaces: matte black (GR lower aero / sills)
acc = (alpha > 0.5) & (np.abs(feat - np.array(ACCENT, np.float32)).sum(-1) < 30)     # red accents survive the matte lower body
low = filled & (MK == CL['clay']) & ((z < 0.255) | (nz < -0.55)) & ~acc; img[low] = MATTE
img[MK == CL['under']] = (10, 10, 11); img[MK == CL['clay_glass']] = GLASS; img[MK == CL['clay_trim']] = GBLACK
img[MK == CL['clay_pocket']] = (12, 12, 14); img[MK == CL['clay_chrome']] = CHROME
pf = MK == CL['clay_pocketfloor']; img[pf] = np.where(alpha[pf][..., None] > 0.3, feat[pf], MESH_BG)
# painted form shading (sky from above, darker toward the sills, soft shoulder highlight) x baked AO
shade = 0.80 + 0.22 * np.clip(nz, -0.3, 1.0)
shade *= 0.82 + 0.18 * np.clip((z - 0.18) / 0.45, 0, 1)
shade += 0.08 * np.exp(-((nz - 0.45) / 0.18) ** 2) * (np.abs(ny) > 0.3)
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
