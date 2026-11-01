"""Sheets for the lean cars (system python: cv2 + numpy + PIL).  PSX review look = RGB555 + 4x4 Bayer, nearest x2."""
import cv2, numpy as np, os
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5
def psx(path):
    a = cv2.imread(path)[..., :3].astype(float) / 255.0; H, W, _ = a.shape
    t = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
    return (np.clip(np.floor(a * 31 + 0.5 + t * 0.9), 0, 31) * 255 / 31).astype(np.uint8)
def lab(i, t, org=(8, 22), s=0.5, col=(0, 0, 0)):
    (w, h), b = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, s, 1); x, y = org
    cv2.rectangle(i, (x - 2, y - h - 3), (x + w + 2, y + b), (255, 255, 255), -1); cv2.putText(i, t, org, cv2.FONT_HERSHEY_SIMPLEX, s, col, 1, cv2.LINE_AA)
def fitw(i, W, interp=cv2.INTER_AREA): return cv2.resize(i, (W, int(round(i.shape[0] * W / i.shape[1]))), interpolation=interp)
def fith(i, H, interp=cv2.INTER_AREA): return cv2.resize(i, (int(round(i.shape[1] * H / i.shape[0])), H), interpolation=interp)
def save(img, path): cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 92]); print('wrote', path, img.shape)
def hcat(ims, gap=8):
    H = max(i.shape[0] for i in ims); ims = [cv2.copyMakeBorder(i, 0, H - i.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims]
    return np.hstack(sum([[i, np.full((H, gap, 3), 255, np.uint8)] for i in ims], [])[:-1])
def vcat(ims, gap=8):
    W = max(i.shape[1] for i in ims); ims = [cv2.copyMakeBorder(i, 0, 0, 0, W - i.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims]
    return np.vstack(sum([[i, np.full((gap, W, 3), 255, np.uint8)] for i in ims], [])[:-1])
def overlay(tex_path, bpmask, crop_to=None, col=(0, 220, 255)):
    from scipy import ndimage as ndi
    bpmask = ndi.binary_fill_holes(bpmask)
    im = psx(tex_path); e = cv2.morphologyEx(bpmask.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    im[e] = col
    if crop_to is not None:
        ys, xs = np.nonzero(crop_to | bpmask); m = 14
        im = im[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]
    return im
def crop_bg(im, pad=10):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(int); bg = np.median(g[0]); ys, xs = np.nonzero(np.abs(g - bg) > 10)
    return im[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]
def ref_frame(raw, out_ref, out_800, label):
    q = psx(raw); ref = cv2.resize(q, (q.shape[1] * 2, q.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(out_ref, ref); im = fitw(ref, 800, cv2.INTER_NEAREST); lab(im, label, s=0.42); save(im, out_800)
