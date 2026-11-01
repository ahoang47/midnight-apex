"""WRX (GD 'bugeye', 2001) blueprint trace -- ref/wrx_blueprint.jpg (the-blueprints.com, 1280x906 native, 1:25).
Same method as BRZ pass 4, adapted to this COLOURED sheet:
  paper  = neutral (S < 2) and V >= 249  (the watermark letters over the paper are neutral grey too -> never 'car')
  car    = everything else in the biggest component of a view crop, holes filled
  glass  = light neutral regions (S < 20, V 215-247, ~RGB 233,237,238) INSIDE the car mask -- not background
  blue   = paint, red = lamps, dark = trim / tyres / lines, LINE = darker than the local median by 28
Line classes: SIL (car-mask boundary), GLASS (glass-region boundary), FEAT (dark strokes inside the paint, lamp edges),
TYRE. Frames: S = 4.405 m over the side-view length (px); side/top x centred on the wheel centres (contact patches),
z from the tyre bottoms; front/rear centred on the paint rows. Top view: nose left, image TOP = car's RIGHT (-y).
Output: bp/curves.json (metres, car frame x fwd / y left / z up), bp/bp_classes.npz."""
import cv2, numpy as np, json
from scipy import ndimage as ndi
im = cv2.imread('ref/wrx_blueprint.jpg'); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
H, Sa, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
DARK = V < 75
BLUE = (H >= 95) & (H <= 130) & (Sa >= 45) & ~DARK
RED = ((H < 12) | (H > 165)) & (Sa >= 60) & ~DARK
LIGHT = (Sa < 22) & (V >= 212) & (V <= 247)              # glass tint (and lamp lenses)
GREY = (Sa < 40) & (V < 212) & ~DARK
VIEW = {'side': (4, 64, 796, 340), 'top': (4, 462, 796, 802), 'front': (878, 60, 1236, 338), 'rear': (878, 478, 1236, 755)}
INK = ((Sa >= 2) & (V < 249)) | (V < 120)
def sub(m, k): x0, y0, x1, y1 = VIEW[k]; return m[y0:y1, x0:x1].copy()
def biggest(m):
    lab, n = ndi.label(m, np.ones((3, 3))); sz = ndi.sum(m, lab, range(1, n + 1)); return lab == 1 + np.argmax(sz)
DISK = lambda r: (np.add.outer(np.arange(-r, r + 1) ** 2, np.arange(-r, r + 1) ** 2) <= r * r)
def carmask(k):
    m = biggest(sub(INK, k))
    m = ndi.binary_fill_holes(ndi.binary_closing(m, np.ones((3, 3))))
    m = biggest(ndi.binary_opening(m, DISK(3)))             # watermark letters touching the outline (1-3 px strokes)
    if k == 'side':                                         # side silhouette is column-convex: median the top/bottom lines
        cs = np.nonzero(m.any(0))[0]
        t = np.array([np.nonzero(m[:, c])[0].min() for c in cs]); b = np.array([np.nonzero(m[:, c])[0].max() for c in cs])
        t = ndi.median_filter(t, 7, mode='nearest'); b = ndi.median_filter(b, 5, mode='nearest')
        m[:] = False
        for c, a, z in zip(cs, t, b): m[a:z + 1, c] = True
    return m
VMED = ndi.median_filter(V, size=7)
LINE = (V < VMED - 28) | DARK
FRAME = BLUE | DARK | RED
def glass_regions(GL, minpx, frame=None):
    GL = ndi.binary_opening(GL, np.ones((3, 3)))          # watermark letters are 1-2 px strokes
    if frame is not None:                                  # letters INSIDE the glass: close over them, never over paint
        GL = ndi.binary_closing(GL, DISK(5)) & ~ndi.binary_dilation(frame, np.ones((2, 2))) | GL
    lab, n = ndi.label(GL, np.ones((3, 3))); keep = np.zeros_like(GL); regs = []
    for i in range(1, n + 1):
        rr, cc = np.nonzero(lab == i)
        if len(rr) >= minpx: keep |= lab == i; regs.append((rr, cc))
    return ndi.binary_fill_holes(ndi.binary_closing(keep, np.ones((3, 3)))), regs
out = {}; cls = {}
# ================================================================== SIDE (nose left, car's LEFT side visible)
x0, y0, x1, y1 = VIEW['side']; M = carmask('side')
cols = np.nonzero(M.any(0))[0]
L_px = cols.max() - cols.min() + 1; S = 4.405 / L_px; out['scale_m_per_px'] = S
bot = np.array([np.nonzero(M[:, c])[0].max() if M[:, c].any() else 0 for c in range(M.shape[1])])
ZF = bot.max() + y0 + 0.5                                 # ground = tyre bottoms
pat = [c for c in cols if bot[c] >= bot.max() - 3]
grp = np.split(np.array(pat), np.nonzero(np.diff(pat) > 3)[0] + 1)
wc = [g.mean() + x0 for g in grp]; CM = 0.5 * (wc[0] + wc[1])
X = lambda c: (CM - (c + x0)) * S
Z = lambda r: (ZF - (r + y0)) * S
top = np.array([np.nonzero(M[:, c])[0].min() if M[:, c].any() else M.shape[0] for c in range(M.shape[1])], float)
out['side_wheel_x'] = [X(c - x0) for c in wc]; out['wheelbase_px_m'] = abs(wc[1] - wc[0]) * S
out['side_sil_top'] = [(X(c), Z(top[c] - 0.5)) for c in cols]
out['side_sil_bot'] = [(X(c), Z(bot[c] + 0.5)) for c in cols]
Bv, Rv, Lv, Gv = (sub(m, 'side') for m in (BLUE, RED, LIGHT, GREY))
zz = np.array([Z(r) for r in range(M.shape[0])])[:, None] * np.ones((1, M.shape[1]))
GL, regs = glass_regions(Lv & M & (zz > 0.90), 60, sub(FRAME, 'side'))
sreg = []
for rr, cc in regs:
    sreg.append(dict(x=(X(cc.max()), X(cc.min())), z=(Z(rr.max() + .5), Z(rr.min() - .5)), n=int(len(rr))))
out['side_glass_regions'] = sreg
out['side_glass_cols'] = [(X(c), Z(np.nonzero(GL[:, c])[0].min() - .5), Z(np.nonzero(GL[:, c])[0].max() + .5)) for c in cols if GL[:, c].any()]
out['side_blue_top'] = [(X(c), Z(np.nonzero(Bv[:, c])[0].min() - .5)) for c in cols if Bv[:, c].any()]
out['side_blue_bot'] = [(X(c), Z(np.nonzero(Bv[:, c])[0].max() + .5)) for c in cols if Bv[:, c].any()]
out['side_red'] = [(X(c), Z(np.nonzero(Rv[:, c])[0].min() - .5), Z(np.nonzero(Rv[:, c])[0].max() + .5)) for c in cols if Rv[:, c].sum() >= 2]
# headlamp lens: light region low at the nose (z < .90)
HL, hreg = glass_regions(Lv & M & (zz <= 0.90) & (zz > 0.45) & (np.array([[X(c) for c in range(M.shape[1])]]) > 1.5), 15)
out['side_headlamp'] = [dict(x=(X(cc.max()), X(cc.min())), z=(Z(rr.max() + .5), Z(rr.min() - .5))) for rr, cc in hreg]
# tyres: non-blue pixels inside the wheel circles (radius from the arch: probe .33 m)
yy, xx = np.mgrid[0:M.shape[0], 0:M.shape[1]]
TY = np.zeros_like(M)
for w in wc:
    TY |= ((xx + x0 - w) ** 2 + (yy + y0 - (ZF - 0.31 / S)) ** 2) <= (0.315 / S) ** 2
TY &= M & ~Bv
cls['side'] = dict(M=M, GL=GL, HL=HL, K=ndi.binary_opening(sub(DARK | GREY, 'side') & M & ~TY, np.ones((3, 3))), R=Rv & M, D=sub(LINE, 'side') & M & ~GL, B=Bv, TY=TY, X0=x0, Y0=y0, CM=CM, ZF=ZF)
# ================================================================== TOP (nose left, image top = car's RIGHT)
x0, y0, x1, y1 = VIEW['top']; Mt = carmask('top')
mid = [c for c in range(Mt.shape[1]) if Mt[:, c].any()]
spans = {c: (np.nonzero(Mt[:, c])[0].min(), np.nonzero(Mt[:, c])[0].max()) for c in mid}
CR = np.median([(a + b) / 2 for a, b in spans.values()])
CMt = CM - (VIEW['side'][0]) + 0                           # same x alignment: compare nose columns
nose_side = cols.min() + VIEW['side'][0]; nose_top = min(mid) + x0
CMt = CM + (nose_top - nose_side)                          # top view is drawn at the same x as the side view
Xt = lambda c: (CMt - (c + x0)) * S
Y = lambda r: (r - CR) * S                                 # image down = car's left (+y)
hw = np.array([(Xt(c), -Y(spans[c][0] - .5), Y(spans[c][1] + .5)) for c in mid])
def _clamp(a):                                             # mirrors: clamp to a running envelope
    f = a.copy()
    for i in range(len(f)):
        lo, hi = max(0, i - 25), min(len(f), i + 25); f[i] = min(f[i], np.percentile(a[lo:hi], 55) + 0.012)
    return f
hf = 0.5 * (_clamp(hw[:, 1]) + _clamp(hw[:, 2]))           # both sides averaged (symmetric car, 1-px jpeg wobble)
out['top_halfwidth'] = list(zip(hw[:, 0].tolist(), hf.tolist())); out['top_halfwidth_raw'] = hw.tolist()
Bt, Rt, Lt = (sub(m, 'top') for m in (BLUE, RED, LIGHT))
GT, tregs = glass_regions(Lt & Mt, 60, sub(FRAME, 'top'))
treg = [dict(x=(Xt(cc.max()), Xt(cc.min())), y=(Y(rr.min()), Y(rr.max())), n=int(len(rr))) for rr, cc in tregs]
tg = []
for c in mid:
    r = np.nonzero(GT[:, c])[0]
    if not len(r): continue
    runs = np.split(r, np.nonzero(np.diff(r) > 1)[0] + 1)
    tg.append((Xt(c), [(Y(a[0] - .5), Y(a[-1] + .5)) for a in runs]))
out['top_glass_cols'] = tg; out['top_glass_regions'] = treg
out['top_red'] = [(Xt(c), [Y(r) for r in np.nonzero(Rt[:, c])[0]]) for c in mid if Rt[:, c].any()]
cls['top'] = dict(M=Mt, GL=GT, K=ndi.binary_opening(sub(DARK | GREY, 'top') & Mt, np.ones((3, 3))), R=Rt & Mt, D=sub(LINE, 'top') & Mt & ~GT, B=Bt, TY=np.zeros_like(Mt), X0=x0, Y0=y0, CM=CMt, CR=CR)
# ================================================================== FRONT / REAR (per height)
for k in ('front', 'rear'):
    x0, y0, x1, y1 = VIEW[k]; Mk = carmask(k)
    Bk, Rk, Lk, Gk = (sub(m, k) for m in (BLUE, RED, LIGHT, GREY))
    bw = [(np.nonzero(Bk[r])[0].min(), np.nonzero(Bk[r])[0].max()) for r in range(Mk.shape[0]) if Bk[r].sum() > 60]
    CC = np.median([(a + b) / 2 for a, b in bw])
    zf = np.nonzero(Mk.any(1))[0].max() + y0 + 0.5
    Zk = lambda r: (zf - (r + y0)) * S
    sgn = -1 if k == 'front' else 1                        # front: car's left on the image right
    Yk = lambda c: sgn * (CC - c) * S
    prof = []
    for r in range(Mk.shape[0]):
        lab, n = ndi.label(Mk[r]); Lb = lab[int(round(CC))]
        if Lb == 0: continue
        seg = np.nonzero(lab == Lb)[0]; prof.append([Zk(r), (CC - seg.min() + .5) * S, (seg.max() + .5 - CC) * S])
    out[k + '_outline_raw'] = prof
    zzk = np.array([Zk(r) for r in range(Mk.shape[0])])[:, None] * np.ones((1, Mk.shape[1]))
    gl, gregs = glass_regions(Lk & Mk & (zzk > 0.95), 80, sub(FRAME, k))
    if gregs:   # the biggest light region high up = windshield / rear glass
        rr, cc = max(gregs, key=lambda q: len(q[0])); gl = np.zeros_like(Mk); gl[rr, cc] = True
        gl = ndi.binary_fill_holes(ndi.binary_closing(gl, np.ones((5, 5))))
    out[k + '_glass'] = [(Zk(r), (CC - np.nonzero(gl[r])[0].min() + .5) * S, (np.nonzero(gl[r])[0].max() + .5 - CC) * S) for r in range(Mk.shape[0]) if gl[r].any()]
    # lamps: light lenses below the glass (front: round headlamps + fogs), red (rear)
    ll, lregs = glass_regions(Lk & Mk & (zzk < 0.95) & (zzk > 0.15), 12)
    out[k + '_light_regions'] = [dict(y=(Yk(cc.min()), Yk(cc.max())), z=(Zk(rr.max() + .5), Zk(rr.min() - .5)), n=int(len(rr))) for rr, cc in lregs]
    out[k + '_red'] = [(Zk(r), [Yk(c) for c in np.nonzero(Rk[r])[0]]) for r in range(Mk.shape[0]) if Rk[r].any()]
    yy, xx = np.mgrid[0:Mk.shape[0], 0:Mk.shape[1]]
    TY = Mk & ~Bk & ~Rk & (np.abs(CC - xx) * S > 0.58) & ((zf - (yy + y0)) * S < 0.30)
    cls[k] = dict(M=Mk, GL=gl, LL=ll, K=ndi.binary_opening(sub(DARK | GREY, k) & Mk & ~TY, np.ones((3, 3))), R=Rk & Mk, D=sub(LINE, k) & Mk & ~gl, B=Bk, GR=sub(DARK, k) & Mk, TY=TY, X0=x0, Y0=y0, CC=CC, ZF=zf)
json.dump(out, open('bp/curves.json', 'w'))
np.savez_compressed('bp/bp_classes.npz', **{f'{k}_{n}': np.asarray(v) for k, d in cls.items() for n, v in d.items()})
if __name__ == '__main__':
    print('S mm/px', round(S * 1000, 3), 'L px', L_px, 'wheels x', [round(v, 3) for v in out['side_wheel_x']], 'WB', round(out['wheelbase_px_m'], 3))
    for k in ('front', 'rear'):
        p = np.array(out[k + '_outline_raw']); print(k, 'H', round(p[:, 0].max(), 3), 'max W', round((p[:, 1] + p[:, 2]).max(), 3))
    hw = np.array(out['top_halfwidth']); print('top L', round(hw[:, 0].max() - hw[:, 0].min(), 3), 'x', round(hw[:, 0].max(), 3), round(hw[:, 0].min(), 3), 'W', round(2 * hw[:, 1].max(), 3))
    st = np.array(out['side_sil_top']); print('side H', round(st[:, 1].max(), 3), 'x', round(st[:, 0].max(), 3), round(st[:, 0].min(), 3))
    print('side glass'); [print('  ', {a: tuple(round(float(q), 3) for q in b) if isinstance(b, tuple) else b for a, b in g.items()}) for g in sreg]
    print('side headlamp', out['side_headlamp'])
    print('top glass'); [print('  ', {a: tuple(round(float(q), 3) for q in b) if isinstance(b, tuple) else b for a, b in g.items()}) for g in treg]
    for k in ('front', 'rear'):
        print(k, 'lights'); [print('  ', {a: tuple(round(float(q), 3) for q in b) if isinstance(b, tuple) else b for a, b in g.items()}) for g in out[k + '_light_regions']]
