"""Pass 4: trace the BRZ blueprint (ref/brz_blueprint.jpg) view by view and classify every drawn line.

Pixel classes (HSV): white (background AND glass: glass is drawn white, quarter glass light grey, inside a thin grey
outline), grey (outline strokes, tinted quarter glass, tyres, black trim), blue paint, red lamps, dark line work.
Line classes used on the tracing sheet:
  SIL   outer silhouette (boundary of the filled car mask; the thin grey stroke over the glass IS the silhouette)
  GLASS glass / DLO edges (boundary of white/light-grey regions enclosed by the outline)
  FEAT  body feature lines (dark strokes inside the paint, lamp outlines, beltline, shut lines, bumper crease)
  TYRE  tyres / wheels
Frames: 14.076 mm/px (4.265 m over 303 px). Side/top x is centred on the two wheel centres (contact patches),
ground = bottom of the tyres; front/rear are centred on the body (median of the paint rows), same ground.
Output: bp/curves.json (metres, car frame x fwd / y left / z up), bp/bp_classes.npz (masks + frames)."""
import cv2, numpy as np, json
from scipy import ndimage as ndi
S = 4.265 / 303
im = cv2.imread('ref/brz_blueprint.jpg'); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
H, Sa, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
WHITE = (Sa < 35) & (V > 200); GREY = (Sa < 35) & (V <= 200) & (V >= 70); DARK = V < 70
BLUE = (H >= 95) & (H <= 125) & (Sa >= 35) & ~DARK; RED = ((H < 12) | (H > 165)) & (Sa >= 35) & ~DARK
VIEW = {'side': (36, 40, 346, 139), 'top': (36, 186, 346, 335), 'front': (362, 40, 512, 139), 'rear': (366, 214, 508, 312)}
GROUND = {'side': 137.5, 'front': 137.5, 'rear': 310.5}
out = {'scale_m_per_px': S}
def sub(m, k): x0, y0, x1, y1 = VIEW[k]; return m[y0:y1, x0:x1].copy()
def biggest(m):
    lab, n = ndi.label(m, np.ones((3, 3))); sz = ndi.sum(m, lab, range(1, n + 1)); return lab == 1 + np.argmax(sz)
BG = (Sa < 35) & (V >= 232)     # paper; the glass outline strokes are faint (V 185-230), so they count as drawn
def carmask(k):
    m = biggest(~sub(BG, k))
    return ndi.binary_fill_holes(ndi.binary_closing(m, np.ones((2, 2))))
VMED = ndi.median_filter(V, size=7)
LINE = (V < VMED - 28) | DARK        # drawn strokes: darker than the local paint / trim
def smooth(a, k=3):
    a = np.asarray(a, float); h = k // 2
    return np.array([np.median(a[max(0, i - h):i + h + 1]) for i in range(len(a))])
cls = {}
# ================================================================== SIDE
x0, y0, x1, y1 = VIEW['side']; M = carmask('side')
Wv, Gv, Bv, Rv, Dv = (sub(m, 'side') for m in (WHITE, GREY, BLUE, RED, DARK))
cols = np.nonzero(M.any(0))[0]
bot = np.array([np.nonzero(M[:, c])[0].max() if M[:, c].any() else 0 for c in range(M.shape[1])])
pat = [c for c in cols if bot[c] >= GROUND['side'] - y0 - 1.5]
grp = np.split(np.array(pat), np.nonzero(np.diff(pat) > 3)[0] + 1)
wc = [g.mean() + x0 for g in grp]; CM = 0.5 * (wc[0] + wc[1])
X = lambda c: (CM - (c + x0)) * S             # c, r local to the crop
Z = lambda r: (GROUND['side'] - (r + y0)) * S
# repair the outline: the watermark breaks the 1-px glass outline in places -> fill dips narrower than 4 columns
top = np.array([np.nonzero(M[:, c])[0].min() if M[:, c].any() else M.shape[0] for c in range(M.shape[1])], float)
fix = top.copy()
for c in cols:
    l = top[max(cols.min(), c - 4):c]; r = top[c + 1:min(cols.max(), c + 4) + 1]
    if len(l) and len(r): fix[c] = min(top[c], max(l.min(), r.min()))
for c in cols: M[int(fix[c]):bot[c] + 1, c] = True     # side silhouette is column-convex (glass enclosed)
M = ndi.binary_opening(M, np.ones((3, 3)))              # watermark strokes stuck to the outline
cols = np.nonzero(M.any(0))[0]
fix = np.array([np.nonzero(M[:, c])[0].min() if M[:, c].any() else M.shape[0] for c in range(M.shape[1])], float)
bot = np.array([np.nonzero(M[:, c])[0].max() if M[:, c].any() else 0 for c in range(M.shape[1])])
out['side_wheel_x'] = [X(c - x0) for c in wc]
out['side_sil_top'] = [(X(c), Z(fix[c] - 0.5)) for c in cols]
out['side_sil_bot'] = [(X(c), Z(bot[c] + 0.5)) for c in cols]
# glass: white or (quarter) grey pixels enclosed by the outline, above z 0.85
GL = (Wv | Gv) & M
for c in cols:
    GL[:int(fix[c]) + 1, c] = False                       # the outline stroke itself
GL &= np.array([[Z(r) > 0.86 for _ in range(M.shape[1])] for r in range(M.shape[0])])
GL = ndi.binary_opening(GL, np.ones((2, 1)))
lab, n = ndi.label(GL, np.ones((3, 3))); keep = np.zeros_like(GL)
glass_regions = []
for i in range(1, n + 1):
    rr, cc = np.nonzero(lab == i)
    if len(rr) < 30: continue          # mirror glints etc.
    keep |= lab == i
    xs = [X(c) for c in cc]; glass_regions.append(dict(x=(min(xs), max(xs)), z=(Z(rr.max() + .5), Z(rr.min() - .5)),
        grey=float(Gv[rr, cc].mean()), n=int(len(rr))))
GL = ndi.binary_fill_holes(keep)
# per-column glass top / bottom (DLO lines) and the paint (blue) top
dlo = []
for c in cols:
    r = np.nonzero(GL[:, c])[0]
    if len(r): dlo.append((X(c), Z(r.min() - .5), Z(r.max() + .5)))
out['side_glass_cols'] = dlo; out['side_glass_regions'] = glass_regions
out['side_blue_top'] = [(X(c), Z(np.nonzero(Bv[:, c])[0].min() - .5)) for c in cols if Bv[:, c].any()]
# arch / body bottom = lowest paint pixel per column (tyres are grey/dark, never blue)
out['side_blue_bot'] = [(X(c), Z(np.nonzero(Bv[:, c])[0].max() + .5)) for c in cols if Bv[:, c].any()]
lamp = [(X(c), Z(np.nonzero(Rv[:, c])[0].min() - .5), Z(np.nonzero(Rv[:, c])[0].max() + .5)) for c in cols if Rv[:, c].sum() >= 2]
out['side_lamp'] = lamp
# tyres: grey/dark pixels inside the wheel circles
yy, xx = np.mgrid[0:M.shape[0], 0:M.shape[1]]
TY = np.zeros_like(M)
for w in wc:
    TY |= ((xx + x0 - w) ** 2 + (yy + y0 - (GROUND['side'] - 0.316 / S)) ** 2) <= (0.33 / S) ** 2
TY &= M & ~Bv
cls['side'] = dict(M=M, GL=GL, R=Rv & M, D=sub(LINE, 'side') & M & ~GL, B=Bv, TY=TY, X0=x0, Y0=y0, CM=CM, ZF=GROUND['side'])
# ================================================================== TOP (front at the left, upper rows = car's left)
x0, y0, x1, y1 = VIEW['top']; M = carmask('top')
Wt, Gt, Bt, Rt, Dt = (sub(m, 'top') for m in (WHITE, GREY, BLUE, RED, DARK))
mid = [c for c in range(M.shape[1]) if M[:, c].any()]
spans = {c: (np.nonzero(M[:, c])[0].min(), np.nonzero(M[:, c])[0].max()) for c in mid}
CR = np.median([(a + b) / 2 for a, b in spans.values()])     # local row of the centre line
Y = lambda r: (CR - r) * S
hw = np.array([(X(c), max(Y(spans[c][0] - .5), -Y(spans[c][1] + .5))) for c in mid])
hf = hw[:, 1].copy()                                         # mirrors: clamp to a running envelope
for i in range(len(hf)):
    lo, hi = max(0, i - 25), min(len(hf), i + 25); hf[i] = min(hf[i], np.percentile(hw[lo:hi, 1], 55) + 0.012)
out['top_halfwidth'] = list(zip(hw[:, 0].tolist(), hf.tolist()))
GT = Wt & M
GT = ndi.binary_opening(GT, np.ones((2, 2)))
lab, n = ndi.label(GT, np.ones((3, 3))); keep = np.zeros_like(GT); treg = []
for i in range(1, n + 1):
    rr, cc = np.nonzero(lab == i)
    if len(rr) < 10 or X(cc.min()) > 1.0: continue     # x > 1 m: headlight lenses, not glass
    keep |= lab == i
    treg.append(dict(x=(X(cc.max()), X(cc.min())), y=(Y(rr.max()), Y(rr.min())), n=int(len(rr))))
GT = ndi.binary_fill_holes(keep)                          # watermark letters over the rear glass
tg = []
for c in mid:
    r = np.nonzero(GT[:, c])[0]
    if not len(r): continue
    runs = np.split(r, np.nonzero(np.diff(r) > 1)[0] + 1)
    tg.append((X(c), [(Y(a[0] - .5), Y(a[-1] + .5)) for a in runs]))
out['top_glass_cols'] = tg; out['top_glass_regions'] = treg
out['top_red'] = [(X(c), [Y(r) for r in np.nonzero(Rt[:, c])[0]]) for c in mid if Rt[:, c].any()]
cls['top'] = dict(M=M, GL=GT, R=Rt & M, D=sub(LINE, 'top') & M & ~GT, B=Bt, TY=np.zeros_like(M), X0=x0, Y0=y0, CM=CM, CR=CR)
# ================================================================== FRONT / REAR (per height)
for k in ('front', 'rear'):
    x0, y0, x1, y1 = VIEW[k]; M = carmask(k)
    Wk, Gk, Bk, Rk, Dk = (sub(m, k) for m in (WHITE, GREY, BLUE, RED, DARK))
    bw = [(np.nonzero(Bk[r])[0].min(), np.nonzero(Bk[r])[0].max()) for r in range(M.shape[0]) if Bk[r].sum() > 40]
    CC = np.median([(a + b) / 2 for a, b in bw])           # local column of the centre line
    Zk = lambda r: (GROUND[k] - (r + y0)) * S; Yk = lambda c: (CC - c) * S
    prof = []
    for r in range(M.shape[0]):
        lab, n = ndi.label(M[r]); L = lab[int(round(CC))]
        if L == 0: continue
        seg = np.nonzero(lab == L)[0]; prof.append([Zk(r), Yk(seg.min() - .5), -Yk(seg.max() + .5)])
    prof = np.array(prof)
    # mirror rows (z 0.84-1.06): clamp to the line between the clean rows either side
    zz = prof[:, 0]; m = (zz > 0.84) & (zz < 1.06)
    for j in (1, 2):
        lo = prof[zz <= 0.84][0, j] if (zz <= 0.84).any() else prof[m][-1, j]
        hi = prof[zz >= 1.06][-1, j]
        lin = np.interp(zz[m], [0.84, 1.06], [lo, hi]); prof[m, j] = np.minimum(prof[m, j], lin + 0.03)
    out[k + '_outline'] = prof.tolist()
    # glass: white enclosed above z .95 (windshield / rear glass), opened
    gl = Wk & M & (np.array([[Zk(r) > 0.95] * M.shape[1] for r in range(M.shape[0])]))
    gl = biggest(ndi.binary_opening(gl, np.ones((2, 2)))) if gl.any() else gl
    out[k + '_glass'] = [(Zk(r), Yk(np.nonzero(gl[r])[0].min() - .5), -Yk(np.nonzero(gl[r])[0].max() + .5)) for r in range(M.shape[0]) if gl[r].any()]
    out[k + '_red'] = [(Zk(r), [Yk(c) for c in np.nonzero(Rk[r])[0]]) for r in range(M.shape[0]) if Rk[r].any()]
    # tyres: grey/dark at the bottom outer corners (|y| > 0.6, z < 0.33)
    yy, xx = np.mgrid[0:M.shape[0], 0:M.shape[1]]
    TY = M & ~Bk & (np.abs(CC - xx) * S > 0.62) & ((GROUND[k] - (yy + y0)) * S < 0.33)
    cls[k] = dict(M=M, GL=gl, R=Rk & M, D=sub(LINE, k) & M & ~gl, B=Bk, GR=Gk & M, TY=TY, X0=x0, Y0=y0, CC=CC, ZF=GROUND[k])
json.dump(out, open('bp/curves.json', 'w'))
np.savez_compressed('bp/bp_classes.npz', **{f'{k}_{n}': np.asarray(v) for k, d in cls.items() for n, v in d.items()})
if __name__ == '__main__':
    print('wheels', out['side_wheel_x'])
    print('side glass regions'); [print('  ', {a: (tuple(round(float(q), 3) for q in b) if isinstance(b, tuple) else round(b, 3)) for a, b in g.items()}) for g in glass_regions]
    print('top glass regions'); [print('  ', {a: (tuple(round(float(q), 3) for q in b) if isinstance(b, tuple) else b) for a, b in g.items()}) for g in treg]
