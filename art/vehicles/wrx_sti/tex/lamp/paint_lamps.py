"""Paint the WRX lean headlamp + fog lamp into the spare bottom-left quadrant of the 256^2 parts atlas, and write the
64^2 RGBA headlamp glow sprite.  Everything is vector-drawn from the projected blueprint outline (lean/tex/lamp_uv.json,
written by parts/lamps_lean.py) and simple circles placed relative to it; no raster is copied.
Head lamp (PSX painted, value-capped so RGB555 + fake shine never clips to white):
  dark chrome bezel (lit top edge, shadowed bottom) | dark reflector cavity | main round reflector bowl with
  facet rings and a small hotspot (inboard / low) | secondary round lamp in the outboard-upper taper |
  lens highlight crescent + streak.
Fog lamp: chrome rim, fluted lens (horizontal flutes), round reflector, hotspot.
python3 tex/lamp/paint_lamps.py atlas.png lamp_uv.json glow.png"""
import sys, os, json, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); from quant import rgb555_bayer
atlas_p, uv_p, glow_p = sys.argv[1:4]
A = np.asarray(Image.open(atlas_p).convert('RGB')).astype(np.float32).copy(); J = json.load(open(uv_p))
SS = 8; VMAX = 232.0
def tile_canvas(tile):
    x0, y0, x1, y1 = tile; W, H = (x1 - x0) * SS, (y1 - y0) * SS
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); return x0, y0, W, H, (xx + 0.5) / SS + x0, (yy + 0.5) / SS + y0
def poly_mask(px, x0, y0, W, H):
    m = np.zeros((H, W), np.uint8); P = np.round((np.asarray(px) - [x0, y0]) * SS * 16).astype(np.int32)
    cv2.fillPoly(m, [P], 1, cv2.LINE_8, shift=4); return m
def put(tile, col, mask):
    x0, y0, x1, y1 = tile; W, H = x1 - x0, y1 - y0
    c = cv2.resize(col, (W, H), interpolation=cv2.INTER_AREA); a = cv2.resize(mask.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)
    bg = A[y0:y1, x0:x1]; A[y0:y1, x0:x1] = bg * (1 - a[..., None]) + c * a[..., None]
def mix(col, m, c, a=1.0):
    m = (m.astype(np.float32) * a)[..., None]; col[:] = col * (1 - m) + np.asarray(c, np.float32) * m
# ------------------------------------------------------------------ head lamp
h = J['head']; x0, y0, W, H, X, Y = tile_canvas(h['tile'])
M = poly_mask(h['outline_px'], x0, y0, W, H)
d = cv2.distanceTransform(M, cv2.DIST_L2, 5) / SS                      # atlas px from the outline (inside)
O = np.asarray(h['outline_px']); cx, cy = O.mean(0); w_ = O[:, 0].max() - O[:, 0].min(); h_ = O[:, 1].max() - O[:, 1].min(); S_ = max(w_, h_)
col = np.zeros((H, W, 3), np.float32)
ang = np.arctan2(-(Y - cy), X - cx)                                    # +y up
# bezel (dark chrome): lit along the top, shadowed below
BZ = 0.075 * S_
lit = 0.5 + 0.5 * np.sin(ang)                                          # 1 at the top
bez = np.array([40, 43, 50]) + (np.array([92, 98, 110]) - np.array([40, 43, 50])) * lit[..., None]
col[:] = bez
mix(col, (d > 0.6) & (d < 1.6) & (lit > 0.55), (168, 174, 186), 0.85)   # chrome edge catch-light (top)
mix(col, (d > BZ - 1.2) & (d < BZ), (24, 26, 30))                       # inner shadow line of the bezel
cav = d >= BZ
mix(col, cav, (46, 54, 68))                                             # reflector cavity (dark blue-grey)
mix(col, cav & ((Y - cy) > 0), (38, 44, 56), 0.6)
# main reflector bowl (inboard, slightly low), secondary lamp (outboard-upper taper)
def bowl(cxb, cyb, R, base, mid, hot, rings, hot_r=0.13, hot_off=(-0.22, -0.22)):
    r = np.hypot(X - cxb, Y - cyb) / R; m = cav & (r <= 1.0)
    mix(col, m & (r > 0.90), (30, 33, 40))                              # bowl rim
    t = np.clip((0.90 - r) / 0.65, 0, 1)[..., None]
    g = np.asarray(base, np.float32) * (1 - t) + np.asarray(mid, np.float32) * t
    mm = m & (r <= 0.90); col[mm] = g[mm]
    for rr in rings: mix(col, m & (np.abs(r - rr) < 0.035), (0, 0, 0), 0.18)   # reflector facet rings
    rh = np.hypot(X - (cxb + hot_off[0] * R), Y - (cyb + hot_off[1] * R)) / R
    mix(col, m & (rh < hot_r * 1.8), np.asarray(hot) * 0.92, 0.55); mix(col, m & (rh < hot_r), hot)
cxi = 1 if O[O[:, 1].argmin(), 0] > cx else -1                          # which way the taper (outboard-up) points in px
mb = (cx - cxi * 0.07 * S_, cy + 0.05 * S_); R1 = 0.30 * S_
bowl(*mb, R1, (78, 88, 104), (170, 178, 192), (226, 228, 232), (0.45, 0.66))
sb = (cx + cxi * 0.25 * S_, cy - 0.20 * S_); R2 = 0.115 * S_
bowl(*sb, R2, (88, 96, 110), (176, 182, 194), (222, 224, 228), (0.55,), hot_r=0.22, hot_off=(-0.15, -0.2))
# lens highlight: crescent just inside the bezel on the upper-inboard side + a soft diagonal streak
cres = cav & (d < BZ + 0.06 * S_) & (np.sin(ang - (np.pi * 0.62 if cxi > 0 else np.pi * 0.38)) > 0.55)
mix(col, cres, (196, 206, 222), 0.22)
u = ((X - cx) * 0.707 * -cxi + (Y - cy) * 0.707) / S_; v = ((X - cx) * 0.707 + (Y - cy) * 0.707 * cxi) / S_
mix(col, cav & (np.abs(u + 0.16) < 0.018) & (np.abs(v) < 0.20), (210, 218, 230), 0.22)
col = np.minimum(col, VMAX)
put(h['tile'], col, M)
# ------------------------------------------------------------------ fog lamp
f = J['fog']; x0, y0, W, H, X, Y = tile_canvas(f['tile'])
M = poly_mask(f['outline_px'], x0, y0, W, H); d = cv2.distanceTransform(M, cv2.DIST_L2, 5) / SS
O = np.asarray(f['outline_px']); cx, cy = O.mean(0); S_ = max(np.ptp(O[:, 0]), np.ptp(O[:, 1]))
ang = np.arctan2(-(Y - cy), X - cx); lit = 0.5 + 0.5 * np.sin(ang)
col = np.zeros((H, W, 3), np.float32) + (np.array([38, 41, 47]) + np.array([50, 54, 62]) * lit[..., None])
BZ = 0.10 * S_; lens = d >= BZ
mix(col, (d > 0.4) & (d < 1.0) & (lit > 0.6), (150, 156, 166), 0.8)
mix(col, lens, (128, 136, 148))
r = np.hypot(X - cx, Y - cy) / (S_ / 2)
t = np.clip((0.75 - r) / 0.6, 0, 1)[..., None]; g = np.array([128, 136, 148]) * (1 - t) + np.array([186, 192, 202]) * t
col[lens] = g[lens]
mix(col, lens & ((np.floor((Y - y0) * 1.0) % 3) == 0), (0, 0, 0), 0.20)      # horizontal flutes
mix(col, lens & (np.hypot(X - cx + 0.12 * S_, Y - cy + 0.12 * S_) < 0.09 * S_), (214, 216, 222))
mix(col, lens & (d < BZ + 1.2) & (lit > 0.75), (190, 198, 212), 0.5)
col = np.minimum(col, VMAX); put(f['tile'], col, M)
out = rgb555_bayer(Image.fromarray(np.clip(A, 0, 255).astype(np.uint8))); out.save(atlas_p)
# ------------------------------------------------------------------ glow sprite (RGBA 64^2), warm white, soft falloff
yy, xx = np.mgrid[0:64, 0:64].astype(np.float32) + 0.5; r = np.hypot(xx - 32, yy - 32) / 32
a = np.clip(1 - r, 0, 1) ** 2.2 * 0.80; rgb = np.zeros((64, 64, 3)) + (255, 240, 214)
Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(glow_p)
print('lamps painted into', atlas_p, '| glow', glow_p)
