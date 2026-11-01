"""Tracing sheet: WRX blueprint views with every drawn line colour-coded by class (from bp/extract.py masks).
red = SIL outer silhouette, cyan = GLASS / DLO edge, yellow = FEAT body feature line (shut lines, beltline, lamp
outlines, bumper/intake edges, scoop, spoiler), green = TYRE. Writes renders/wrx_bp_line_classification_800.jpg."""
import cv2, numpy as np
from scipy import ndimage as ndi
z = np.load('bp/bp_classes.npz'); im = cv2.imread('ref/wrx_blueprint.jpg')
from extract import VIEW
COL = {'SIL': (40, 40, 230), 'GLASS': (230, 200, 0), 'FEAT': (0, 200, 255), 'TYRE': (40, 170, 40)}
def edge(m): return m & ~ndi.binary_erosion(m, np.ones((3, 3)))
def view_img(k, up):
    x0, y0, x1, y1 = VIEW[k]; base = im[y0:y1, x0:x1]
    g = cv2.cvtColor(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    g = (255 - (255 - g.astype(float)) * 0.35).astype(np.uint8)
    big = cv2.resize(g, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    M = z[f'{k}_M']; GL = z[f'{k}_GL']; D = z[f'{k}_D']; R = z[f'{k}_R']; TY = z[f'{k}_TY']
    sil = edge(M); gle = edge(GL) & M
    feat = (D & ~ndi.binary_dilation(sil | gle, np.ones((3, 3))) & ~TY) | edge(R)
    for extra in ('HL', 'LL'):
        if f'{k}_{extra}' in z.files: feat |= edge(z[f'{k}_{extra}'])
    tye = edge(TY) | (TY & D)
    for name, m in [('FEAT', feat & ~TY), ('TYRE', tye), ('GLASS', gle), ('SIL', sil)]:
        mm = cv2.resize(m.astype(np.uint8), None, fx=up, fy=up, interpolation=cv2.INTER_NEAREST)
        big[mm > 0] = COL[name]
    return big
def sheet(width, path):
    up = 3; side, top, fr, re = (view_img(k, up) for k in ('side', 'top', 'front', 'rear'))
    pad = 12
    def fit(a, w): return cv2.resize(a, (w, int(a.shape[0] * w / a.shape[1])), interpolation=cv2.INTER_AREA)
    row2 = np.full((max(fr.shape[0], re.shape[0]), fr.shape[1] + re.shape[1] + pad, 3), 255, np.uint8)
    row2[:fr.shape[0], :fr.shape[1]] = fr; row2[:re.shape[0], fr.shape[1] + pad:] = re
    W = 2000; parts = [('SIDE (nose left, car LEFT side)', fit(side, W)), ('TOP (nose left, image top = car RIGHT)', fit(top, W)), ('FRONT', fit(row2, W))]
    rear_x = int((fr.shape[1] + pad) * W / row2.shape[1]) + 16
    hdr, leg = 64, 76
    out = np.full((hdr + sum(p.shape[0] + 46 for _, p in parts) + leg, W, 3), 255, np.uint8)
    cv2.putText(out, 'Subaru Impreza WRX (GD, 2001) blueprint - every drawn line classified', (16, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 20, 20), 3)
    y = hdr
    for t, p in parts:
        cv2.putText(out, t, (16, y + 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (20, 20, 20), 2)
        if t == 'FRONT': cv2.putText(out, 'REAR', (rear_x, y + 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (20, 20, 20), 2)
        y += 46; out[y:y + p.shape[0]] = p; y += p.shape[0]
    x = 16
    for name, lab in (('SIL', 'SIL outer silhouette'), ('GLASS', 'GLASS / DLO edge'), ('FEAT', 'FEAT body line (belt, shut lines, lamps, scoop, spoiler)'), ('TYRE', 'TYRE')):
        cv2.rectangle(out, (x, y + 20), (x + 44, y + 50), COL[name], -1); cv2.putText(out, lab, (x + 54, y + 46), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (20, 20, 20), 2)
        x += 72 + cv2.getTextSize(lab, cv2.FONT_HERSHEY_SIMPLEX, 0.85, 2)[0][0]
    cv2.imwrite('renders/clay_raw/bp_line_classification_work.png', out)
    cv2.imwrite(path, cv2.resize(out, (width, int(out.shape[0] * width / out.shape[1])), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
if __name__ == '__main__':
    sheet(800, 'renders/wrx_bp_line_classification_800.jpg'); print('ok')
