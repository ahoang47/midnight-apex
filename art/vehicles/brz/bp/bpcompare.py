"""Pass 4 gate: blueprint silhouettes vs clay in the blueprint's own frame (no bbox fitting).
Side/top: x from the blueprint wheel centres, z from the tyre bottoms; front/rear: body centre line + ground.
The clay is rasterised straight from bp/tris_carframe.npy (written by build_brz.py) at 4x blueprint resolution.
Writes bp/iou_bpframe.json and renders/clay_raw/bpiou_{view}.png (grey both, blue blueprint only, red clay only)."""
import numpy as np, cv2, json, sys
from scipy import ndimage as ndi
UP = 4
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']; s = S / UP
T = np.load('bp/tris_carframe.npy').reshape(-1, 3, 3)
def bpmask(view):
    import importlib.util
    z = np.load('bp/bp_classes.npz'); M = z[f'{view}_M'].astype(np.uint8)
    return cv2.resize(M, (M.shape[1] * UP, M.shape[0] * UP), interpolation=cv2.INTER_NEAREST) > 0, z
FR = {}
def frame(view):
    z = np.load('bp/bp_classes.npz')
    X0, Y0 = int(z[f'{view}_X0']), int(z[f'{view}_Y0'])
    return X0, Y0
def raster(view, shape):
    X0, Y0 = frame(view); z = np.load('bp/bp_classes.npz')
    img = np.zeros(shape, np.uint8)
    if view in ('side', 'top'):
        CM = float(z['side_CM']) if view == 'side' else float(z['top_CM'])
        u = ((CM - X0) - T[..., 0] / S + 0.0) * UP
        if view == 'side': v = ((float(z['side_ZF']) - Y0) - T[..., 2] / S) * UP
        else: v = (((float(z['top_CR'])+Y0) - Y0) - T[..., 1] / S) * UP
    else:
        cc = (float(z[f'{view}_CC'])+X0); zf = float(z[f'{view}_ZF'])
        sgn = 1 if view == 'front' else -1          # front view: car's left (+y) on the image right
        u = ((cc - X0) + sgn * T[..., 1] / S) * UP
        v = ((zf - Y0) - T[..., 2] / S) * UP
    P = np.stack([u, v], -1)
    for tri in P: cv2.fillPoly(img, [np.round(tri * 8).astype(np.int32)], 1, shift=3)
    return img > 0
import os; os.makedirs('renders/clay_raw', exist_ok=True)
res = {}
for view in ('side', 'top', 'front', 'rear'):
    B, _ = bpmask(view); C = raster(view, B.shape)
    iou = (B & C).sum() / (B | C).sum(); res[view] = round(float(iou), 4)
    ov = np.full(B.shape + (3,), 255, np.uint8); ov[B & C] = (190, 190, 190); ov[B & ~C] = (255, 140, 0); ov[C & ~B] = (0, 0, 230)
    cv2.imwrite(f'renders/clay_raw/bpiou_{view}.png', ov)
json.dump(res, open('bp/iou_bpframe.json', 'w'), indent=1); print(res)
