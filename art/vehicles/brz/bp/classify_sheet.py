"""Tracing sheet: blueprint views with every drawn line colour-coded by class (from bp/extract.py masks).
red = outer silhouette, cyan = glass / DLO edge, yellow = body feature line (shut lines, beltline, lamp outlines,
bumper crease, grille/diffuser edges), green = tyre / wheel. Writes renders/brz_bp_line_classification_p4_800.jpg
(and a 2x working copy in renders/clay_raw/)."""
import cv2, numpy as np, json, sys
from scipy import ndimage as ndi
z = np.load('bp/bp_classes.npz'); im = cv2.imread('ref/brz_blueprint.jpg')
VIEW = {'side': (36, 40, 346, 139), 'top': (36, 186, 346, 335), 'front': (362, 40, 512, 139), 'rear': (366, 214, 508, 312)}
COL = {'SIL': (40, 40, 230), 'GLASS': (230, 200, 0), 'FEAT': (0, 210, 255), 'TYRE': (40, 170, 40)}
def edge(m): return m & ~ndi.binary_erosion(m, np.ones((3, 3)))
def view_img(k, up):
    x0, y0, x1, y1 = VIEW[k]; base = im[y0:y1, x0:x1]
    g = cv2.cvtColor(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    g = (255 - (255 - g) * 0.45).astype(np.uint8)                       # faded drawing underneath
    big = cv2.resize(g, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    M = z[f'{k}_M']; GL = z[f'{k}_GL']; D = z[f'{k}_D']; R = z[f'{k}_R']; TY = z[f'{k}_TY']
    sil = edge(M); gle = edge(GL) & M
    feat = (D & ~ndi.binary_dilation(sil | gle, np.ones((3, 3))) & ~TY) | edge(R)
    if f'{k}_GR' in z.files:                                           # black trim (grille / diffuser) edges
        GR = z[f'{k}_GR'] & ~TY & ~ndi.binary_dilation(sil, np.ones((3, 3)))
        feat |= edge(ndi.binary_opening(GR, np.ones((2, 2))))
    tye = edge(TY) | (TY & D)
    layers = [('FEAT', feat & ~TY), ('TYRE', tye), ('GLASS', gle), ('SIL', sil)]
    for name, m in layers:
        mm = cv2.resize(m.astype(np.uint8), None, fx=up, fy=up, interpolation=cv2.INTER_NEAREST)
        mm = cv2.dilate(mm, np.ones((max(1, up // 3), max(1, up // 3)), np.uint8))
        big[mm > 0] = COL[name]
    return big
def sheet(width, path):
    up_side = 6; side = view_img('side', up_side); top = view_img('top', up_side)
    fr = view_img('front', up_side); re = view_img('rear', up_side)
    pad = 10
    row2 = np.full((max(fr.shape[0], re.shape[0]), fr.shape[1] + re.shape[1] + pad, 3), 255, np.uint8)
    row2[:fr.shape[0], :fr.shape[1]] = fr; row2[:re.shape[0], fr.shape[1] + pad:] = re
    def fit(a, w): return cv2.resize(a, (w, int(a.shape[0] * w / a.shape[1])), interpolation=cv2.INTER_AREA)
    W = 1800; parts = [('SIDE (nose left)', fit(side, W)), ('TOP (nose left)', fit(top, W)), ('FRONT', fit(row2, W))]
    rear_x = int((fr.shape[1] + pad) * W / row2.shape[1]) + 16
    hdr = 60; leg = 70
    H = hdr + sum(p.shape[0] + 44 for _, p in parts) + leg
    out = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(out, 'BRZ blueprint - every drawn line classified (pass 4 re-trace)', (16, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (20, 20, 20), 3)
    y = hdr
    for t, p in parts:
        cv2.putText(out, t, (16, y + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
        if t == 'FRONT': cv2.putText(out, 'REAR', (rear_x, y + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
        y += 44
        out[y:y + p.shape[0]] = p; y += p.shape[0]
    x = 16
    for name, lab in (('SIL', 'outer silhouette'), ('GLASS', 'glass / DLO edge'), ('FEAT', 'body feature line (belt, shut lines, lamps, trim)'), ('TYRE', 'tyre / wheel')):
        cv2.rectangle(out, (x, y + 18), (x + 40, y + 46), COL[name], -1); cv2.putText(out, lab, (x + 50, y + 42), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
        x += 64 + cv2.getTextSize(lab, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0][0]
    big = out
    cv2.imwrite('renders/clay_raw/bp_line_classification_work.png', big)
    small = cv2.resize(big, (width, int(big.shape[0] * width / big.shape[1])), interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, small, [cv2.IMWRITE_JPEG_QUALITY, 92])
sheet(800, 'renders/brz_bp_line_classification_p4_800.jpg')
print('ok')
