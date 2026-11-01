"""Three-view sheets: side (nose left) | front, top below side (aligned on length) | rear below front. One scale."""
import cv2, numpy as np, sys, os
_HERE = os.path.dirname(os.path.abspath(__file__)); _VEH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); CARDIR = {'wrx': 'wrx_sti', 's2000': 's2000', 'brz': 'brz'}; sys.path.insert(0, os.path.dirname(_HERE)); from deliver_kit import BAYER
RAW = os.path.join(_HERE, 'raw'); MPP = 0.0044
BG = np.array([23, 23, 23]) * 255 // 31 + 0          # RGB555-exact neutral grey -> no dither on the background
def _tot(c):
    t = [l for l in open(os.path.join(_VEH, CARDIR[c], 'lean', 'tri_count.txt')).read().splitlines() if l.startswith('TOTAL')][0]; return int(t.split()[2])
_w = _tot('wrx')
CARS = {'wrx': ('WRX (lean)', f'{_w:,} tris  ({_w - 4:,} + 4 glow FX, hidden)'),
        's2000': ('S2000 (lean)', f"{_tot('s2000'):,} tris"), 'brz': ('BRZ (lean)', f"{_tot('brz'):,} tris")}
def load(c, v):
    a = cv2.imread(f'{RAW}/{c}_{v}.png', cv2.IMREAD_UNCHANGED).astype(float); al = a[..., 3:] / 255
    return (a[..., :3] * al + BG * (1 - al)), a[..., 3] > 8
def psx(a):
    H, W, _ = a.shape; t = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
    return (np.clip(np.floor(a / 255 * 31 + 0.5 + t * 0.9), 0, 31) * 255 / 31).astype(np.uint8)
def ext(ms, ax):  # occupied index range along axis (0 rows, 1 cols) over several same-length masks
    i = np.nonzero(np.logical_or.reduce([m.any(axis=1 - ax) for m in ms]))[0]; return i.min(), i.max()
def text(im, t, org, s, col=(40, 40, 40), th=1):
    cv2.putText(im, t, org, cv2.FONT_HERSHEY_SIMPLEX, s, col, th, cv2.LINE_AA)
def dash(im, p, q, col=(150, 150, 150), d=6):
    p, q = np.array(p, float), np.array(q, float); n = int(np.linalg.norm(q - p) // d)
    for k in range(0, n, 2): cv2.line(im, tuple((p + (q - p) * k / n).astype(int)), tuple((p + (q - p) * min(k + 1, n) / n).astype(int)), col, 1)
for c, (name, tris) in CARS.items():
    V = {v: load(c, v) for v in ('side', 'front', 'rear', 'top')}
    P = 6
    # shared ranges keep the projections aligned: side/top share columns, side/front share rows, top/rear share rows
    s0, s1 = ext([V['side'][1], V['top'][1]], 1); r0, r1 = ext([V['side'][1], V['front'][1], V['rear'][1]], 0)
    t0, t1 = ext([V['top'][1]], 0)
    ground = int(round(0.75 / MPP + V['side'][0].shape[0] / 2))           # z=0 row (target z .75 at image centre)
    r1 = max(r1, ground)
    f0, f1 = ext([V['front'][1], V['rear'][1]], 1)
    cx0, cx1 = s0 - P, s1 + P + 1; fx0, fx1 = f0 - P, f1 + P + 1; ry0, ry1 = r0 - P, r1 + P + 1; ty0, ty1 = t0 - P, t1 + P + 1
    side, front = V['side'][0][ry0:ry1, cx0:cx1], V['front'][0][ry0:ry1, fx0:fx1]
    top, rear = V['top'][0][ty0:ty1, cx0:cx1], V['rear'][0][ry0:ry1, fx0:fx1]
    M, G, HEAD = 40, 70, 64
    W = M + side.shape[1] + G + front.shape[1] + M
    H = HEAD + side.shape[0] + G + max(top.shape[0], rear.shape[0]) + 34
    sheet = np.empty((H, W, 3)); sheet[:] = BG
    xs, xf, ys, yt = M, M + side.shape[1] + G, HEAD, HEAD + side.shape[0] + G
    yr = yt + (top.shape[0] - rear.shape[0]) // 2                        # rear centred on the top view's height
    sheet[ys:ys + side.shape[0], xs:xs + side.shape[1]] = side; sheet[ys:ys + front.shape[0], xf:xf + front.shape[1]] = front
    sheet[yt:yt + top.shape[0], xs:xs + top.shape[1]] = top
    sheet[yr:yr + rear.shape[0], xf:xf + rear.shape[1]] = rear
    out = psx(sheet)
    # drafting marks (after the PSX pass so lines stay crisp)
    gy = ys + ground - ry0
    for x0, x1 in ((xs - 14, xs + side.shape[1] + 14), (xf - 14, xf + front.shape[1] + 14)): cv2.line(out, (x0, gy), (x1, gy), (70, 70, 70), 1)
    ry = yr + ground - ry0; cv2.line(out, (xf - 14, ry), (xf + rear.shape[1] + 14, ry), (70, 70, 70), 1)
    for x in (xs + P, xs + side.shape[1] - P - 1): dash(out, (x, gy + 4), (x, yt + P - 2))              # length extents
    for y in (ys + P, gy): dash(out, (xs + side.shape[1] + 4, y), (xf + P - 2, y))                       # height extents
    L = (s1 - s0) * MPP; Wd = (f1 - f0) * MPP; Hh = (ground - r0) * MPP
    text(out, name, (M, 34), 0.8, (25, 25, 25), 2); text(out, tris, (M, 54), 0.5)
    text(out, f'L {L:.2f} m   W {Wd:.2f} m (mirrors)   H {Hh:.2f} m   |   ortho, 1 px = {MPP*1000:.1f} mm, all views', (W - 560, 54), 0.42, (70, 70, 70))
    for lbl, x, y in (('SIDE (L)', xs, ys + side.shape[0] + 16), ('FRONT', xf, ys + side.shape[0] + 16),
                      ('TOP', xs, yt + top.shape[0] + 18), ('REAR', xf, yr + rear.shape[0] + 16)):
        text(out, lbl, (x, y), 0.42, (90, 90, 90))
    cv2.imwrite(os.path.join(_VEH, CARDIR[c], 'lean', 'renders', f'{c}_lean_threeview.png'), out)
    small = cv2.resize(out, (800, round(out.shape[0] * 800 / out.shape[1])), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(_VEH, CARDIR[c], 'lean', 'renders', f'{c}_lean_threeview_800.jpg'), small, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(c, out.shape, f'L{L:.2f} W{Wd:.2f} H{Hh:.2f}')
