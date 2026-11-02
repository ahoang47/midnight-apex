import json, numpy as np, cv2
V = json.load(open('feature_vectors.json')); RES = 0.004
EXT = dict(side=((-2.4, 2.4), (-0.1, 1.6)), top=((-2.4, 2.4), (-1.1, 1.1)), front=((-1.1, 1.1), (-0.1, 1.6)), rear=((-1.1, 1.1), (-0.1, 1.6)))
ims = []
for v, ((u0, u1), (v0, v1)) in EXT.items():
    W, H = int((u1 - u0) / RES), int((v1 - v0) / RES); im = np.full((H, W, 3), 255, np.uint8)
    px = lambda P: np.round(np.c_[(np.asarray(P)[:, 0] - u0) / RES, (v1 - np.asarray(P)[:, 1]) / RES]).astype(np.int32)
    rng = np.random.default_rng(1)
    for k, ps in V[v]['polys'].items():
        c = tuple(int(x) for x in rng.integers(80, 230, 3))
        for p in ps: cv2.fillPoly(im, [px(p)], c); cv2.putText(im, k, tuple(px(p).mean(0).astype(int)), 0, 0.3, (0, 0, 0), 1)
    for p in V[v]['lines']: cv2.polylines(im, [px(p)], False, (0, 0, 0), 1, cv2.LINE_AA)
    for p in V[v]['details']: cv2.polylines(im, [px(p)], False, (255, 0, 0), 1, cv2.LINE_AA)
    ims.append(im)
top = np.hstack([ims[0], ims[1][:ims[0].shape[0]] if ims[1].shape[0] >= ims[0].shape[0] else np.vstack([ims[1], np.full((ims[0].shape[0]-ims[1].shape[0], ims[1].shape[1], 3), 255, np.uint8)])])
bot = np.hstack([ims[2], ims[3]]); bot = np.hstack([bot, np.full((bot.shape[0], top.shape[1] - bot.shape[1], 3), 255, np.uint8)])
cv2.imwrite('../work/vec_preview.png', np.vstack([top, bot]))
