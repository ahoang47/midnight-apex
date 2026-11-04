"""Feature-line check (A.1 / skill rule 1): the drawing's TRANSPORT (magenta) + OUTLINE (black) lines, mapped through the
same car frame as extract.py, drawn over the clay Workbench orthos (out/renders/raw/clay_<view>.png: ortho 5.0 m over
1000 px, centre z .70).  Side ortho is the car's LEFT (nose left), so the drawing (car's right) is mirrored in x.
Writes renders/raw/feature_<view>.png (local only: contains the licensed drawing).  Run from bp/."""
import cv2, numpy as np, json
from frames import to_car
SC = 6; MPP = 5.0 / 1000
lay = {k: cv2.imread(f'raster_{k}.png', 0) > 0 for k in ('outline', 'transport')}
BOX = dict(side=(55, 55, 640, 250), front=(670, 55, 965, 250), rear=(670, 305, 965, 500), top=(55, 290, 640, 590))
def pix(view, P):                 # car frame -> clay ortho pixel (col, row)
    if view == 'side': a, b = -P[:, 0], P[:, 1]
    elif view == 'front': a, b = P[:, 0], P[:, 1]             # camera ahead of the car: car left (+y) on the image right
    elif view == 'rear': a, b = -P[:, 0], P[:, 1]             # camera behind: car left on the image left
    else: a, b = -P[:, 0], -P[:, 1]
    return np.c_[500 + a / MPP, 500 - (b - (0.70 if view != 'top' else 0.0)) / MPP]
out = []
for view in ('side', 'front', 'rear'):
    img = cv2.imread(f'../out/renders/raw/clay_{view}.png'); u0, v0, u1, v1 = BOX[view]
    for k, col in (('transport', (200, 40, 220)), ('outline', (0, 0, 0))):
        rr, cc = np.nonzero(lay[k][v0 * SC:v1 * SC, u0 * SC:u1 * SC]); P = to_car(view, np.c_[cc / SC + u0, rr / SC + v0])
        q = np.round(pix(view, P)).astype(int); ok = (q[:, 0] >= 0) & (q[:, 0] < 1000) & (q[:, 1] >= 0) & (q[:, 1] < 1000)
        img[q[ok, 1], q[ok, 0]] = col
    cv2.imwrite(f'../renders/raw/feature_{view}.png', img); out.append(img)
print('ok')
