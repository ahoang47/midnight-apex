"""WRX head lamp pocket review: side ortho around the nose (textured, PSX) with the blueprint silhouette (yellow) and
the blueprint side-view lamp lens outline (magenta, tex/lamp/trace_lamps.py 'head_side'), before | after."""
import cv2, numpy as np, json, sys, os
sys.path.insert(0, 'bp'); os.environ.setdefault('WRX_OUT', 'lean')
exec(open('bp/deliver_lean.py').read().split("g = iou['gate']")[0])          # reuse psx() / bp_in_render() / lab()
LO = json.load(open('bp/lamp_outlines.json'))
def crop(path):
    im = psx(path); bp = bp_in_render('side')
    e = cv2.morphologyEx(bp, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; im[e] = (0, 220, 255)
    q = np.asarray(LO['head_side']); P = np.c_[500 - q[:, 0] / 0.005, 500 - (q[:, 1] - 0.65) / 0.005]
    cv2.polylines(im, [np.round(P * 16).astype(np.int32)], True, (255, 0, 255), 1, cv2.LINE_AA, shift=4)
    im = im[400:560, 20:260]; return cv2.resize(im, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
a = crop(os.environ.get('WRX_BEFORE_SIDE', 'lean/renders/clay_raw/tex_side_before.png')); b = crop('lean/renders/clay_raw/tex_side.png')
lab(a, 'before (flat lens on the nose)', s=0.5); lab(b, 'after (light pocket, lens ~3.5 cm back)', s=0.5)
out = np.hstack([a, np.full((a.shape[0], 8, 3), 255, np.uint8), b]); cv2.imwrite('lean/renders/wrx_lean_nose_side_overlay.png', out)
cv2.imwrite('lean/renders/wrx_lean_nose_side_overlay_800.jpg', fitw(out, 800, cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(out.shape)
