"""BRZ body paint texture (1024^2, PSX/early-PS2): WR-style blue + baked AO + painted form shading + painted black trim
(hex grille with fang corners, C-intakes, fender vent, side-skirt blade, diffuser) + crisp vector panel lines.
Panel lines / outlines are vector polylines in car metres, taken from the blueprint's classified feature lines
(parts/brz_bp.py FEAT + the pass-4 key-line table), drawn per texel in the view plane that owns the texel (dominant
normal axis) -> one clean anti-aliased line, smooth even where the mesh edge is stepped.
Input: npz with per-texel car-frame pos / nrm / material class (0 paint 1 glass 2 under 3 lamp 4 trim), AO png.
Car frame: x forward, y left, z up.  Run with system python:  python3 tex/make_body.py texels.npz out.png ao.png"""
import numpy as np, sys, os
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parts'))
from quant import rgb555_bayer
import brz_bp as BP
src, dst = sys.argv[1], sys.argv[2]; ao_png = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load(src); P, N, MK = D['pos'], D['nrm'], D['mask']; TS = P.shape[0]
PAINT = np.array([28, 78, 196], np.float32)      # WR-style blue (reference photos: side + rear34)
LINE = np.array([8, 18, 52], np.float32); BLACK = np.array([13, 13, 15], np.float32); GREY = np.array([58, 60, 66], np.float32)
x, y, z = P[..., 0], P[..., 1], P[..., 2]; ay = np.abs(y); nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]; any_ = np.abs(ny)
filled = MK >= 0
dom = np.argmax(np.stack([np.abs(nx), any_, np.abs(nz)]), 0)
own_side = filled & (dom == 1); own_top = filled & (dom == 2) & (nz > 0); own_bot = filled & (dom == 2) & (nz <= 0)
own_front = filled & (dom == 0) & (nx > 0); own_rear = filled & (dom == 0) & (nx < 0)
sm = lambda e0, e1, v: (lambda t: t * t * (3 - 2 * t))(np.clip((v - e0) / (e1 - e0), 0, 1))
def poly_in(pg, a, b):
    """even-odd point-in-polygon, vectorised"""
    pg = np.asarray(pg, np.float32); r = np.zeros(a.shape, bool); n = len(pg)
    for i in range(n):
        (a0, b0), (a1, b1) = pg[i], pg[(i + 1) % n]
        c = ((b0 > b) != (b1 > b)) & (a < (a1 - a0) * (b - b0) / (b1 - b0 + 1e-12) + a0); r ^= c
    return r
def dist_to(pl, a, b):
    d = np.full(a.shape, 9.0, np.float32)
    for (a0, b0), (a1, b1) in zip(pl, pl[1:]):
        ea, eb = a1 - a0, b1 - b0; L2 = ea * ea + eb * eb + 1e-12
        t = np.clip(((a - a0) * ea + (b - b0) * eb) / L2, 0, 1)
        d = np.minimum(d, np.hypot(a - a0 - t * ea, b - b0 - t * eb))
    return d
def closed(pg): return list(pg) + [pg[0]]
def rrect(x0, x1, z0, z1, r, n=5):
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n); pts.append((cx + r * np.cos(a), cz + r * np.sin(a)))
    return pts + [pts[0]]
def circle(cx, cz, r, n=20): return [(cx + r * np.cos(2 * np.pi * k / n), cz + r * np.sin(2 * np.pi * k / n)) for k in range(n + 1)]
dpx = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1); ok = filled[:, 1:] & filled[:, :-1]
tex_m = float(np.median(dpx[ok & (dpx < .05)])); aa = max(tex_m, .002)
cover = lambda d, w=0.0: np.clip(0.5 - (d - w) / aa, 0, 1)          # AA coverage of a region given signed-ish distance

# ================================================================ shading (painted form, then AO)
sh = 0.80 + 0.20 * sm(0.12, 0.75, z)                                # top light falls off toward the sills
sh *= 1 + 0.10 * np.clip(nz, -1, 1)                                # up-facing brighter, down-facing (scoop top, haunch underside) darker
side = own_side | (filled & (any_ > 0.35))
# door scoop: concave band under the rising crease (mesh column p3: z .515 at x .5 -> .605 at x -.9), lit crease lip,
# shadow just under it, slight bounce light low on the scoop above the rocker blade
zc = np.interp(-x, [-0.95, -0.5, 0.0, 0.5, 0.9, 1.0], [0.50, 0.515, 0.548, 0.597, 0.605, 0.62])
dc = zc - z
scoop = side & (x > -1.00) & (x < 0.95) & (z > 0.24)
taper = sm(0.95, 0.80, x) * sm(-1.00, -0.85, x)
sh[scoop] *= (1 + taper * (0.42 * np.exp(-((dc + 0.006) / 0.009) ** 2) - 0.32 * np.exp(-((dc - 0.07) / 0.05) ** 2)
                           + 0.06 * np.exp(-((z - 0.27) / 0.03) ** 2)))[scoop]
# rear haunch: soft highlight over the rear arch, shadow where it rolls under toward the shoulder
hx = np.exp(-(((x + 1.30) / 0.40) ** 2 + ((z - 0.80) / 0.09) ** 2))
sh[side] *= (1 + 0.20 * hx - 0.10 * np.exp(-(((x + 1.30) / 0.45) ** 2 + ((z - 0.66) / 0.05) ** 2)))[side]
# front fender crest highlight (top of the wheel arch shoulder)
fx = np.exp(-(((x - 1.28) / 0.35) ** 2 + ((z - 0.74) / 0.06) ** 2)); sh[side] *= (1 + 0.14 * fx)[side]
# hood valley between the fender ridges: darker trough at the ridge foot, lit crest on the ridge
hood = own_top & (x > 0.80) & (x < 2.0) & (ay < 0.72)
sh[hood] *= (1 - 0.10 * np.exp(-((ay - 0.46) / 0.07) ** 2) + 0.14 * np.exp(-((ay - 0.62) / 0.035) ** 2) - 0.04 * sm(0.40, 0.0, ay))[hood]
# rear face: rounded corners (darken toward the outboard edge), darker low, lit bumper crease
rear = own_rear | (filled & (x < -1.93) & (nx < -0.3))
sh[rear] *= (1 - 0.30 * sm(0.55, 0.92, ay) - 0.12 * sm(0.70, 0.45, z))[rear]
sh[rear] *= (1 + 0.20 * np.exp(-((z - 0.672) / 0.012) ** 2))[rear]
# rear corners in plan: the rear 3/4 wrap darkens as it turns away -> reads round, not boxy
wrap = filled & (x < -1.75) & (any_ > 0.25) & (nx < -0.15)
sh[wrap] *= (1 - 0.16 * np.clip(-nx, 0, 1))[wrap]
# ducktail lip: bright line on the lip edge, shadow under it on the rear face
duck = filled & (x < -1.92) & (np.abs(z - 0.986) < 0.014)
sh[duck] *= (1 + 0.45 * (1 - np.abs(z - 0.986) / 0.014))[duck]
under_lip = rear & (z < 0.975) & (z > 0.92); sh[under_lip] *= (1 - 0.20 * sm(0.92, 0.975, z))[under_lip]
if ao_png:
    ao = np.flipud(np.asarray(Image.open(ao_png).convert('L').filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0)
    if ao.shape[0] != TS: ao = np.asarray(Image.fromarray((ao * 255).astype(np.uint8)).resize((TS, TS), Image.BILINEAR)) / 255.0
    sh *= 0.42 + 0.58 * np.clip(ao, 0, 1) ** 1.1
col = PAINT[None, None] * sh[..., None]

# ================================================================ black trim / openings (smooth vector outlines)
blk = np.zeros(x.shape, np.float32); fin = np.zeros(x.shape, np.float32)
fr = filled & (x > 1.70) & (nx > -0.2)
def region(mask, pg, a, b):
    m = mask & poly_in(pg, a, b); inside = m.astype(np.float32)
    d = dist_to(closed(pg), a, b); edge = mask & (d < 2 * aa)
    inside[edge] = np.where(poly_in(pg, a[edge], b[edge]), np.clip(0.5 + d[edge] / aa, 0, 1), np.clip(0.5 - d[edge] / aa, 0, 1))
    return inside
mir = lambda pg: [(-a, b) for a, b in pg][::-1]
# low, wide hexagonal grille (front view y,z) with the fang corners dropping toward the C-intakes
GR = [(-0.50, .46), (0.50, .46), (0.62, .33), (0.66, .225), (0.58, .23), (0.55, .15), (-0.55, .15), (-0.58, .23), (-0.66, .225), (-0.62, .33)]
g = region(fr, GR, y, z); blk = np.maximum(blk, g)
# hex mesh inside the grille: honeycomb lines in dark grey, lit top edges
hw, hh = 0.034, 0.026
qy = y / hw; qz = z / hh; row = np.floor(qz); qy2 = qy + 0.5 * (row % 2)
dy = np.abs(qy2 - np.round(qy2)); dz = np.abs(qz - row - 0.5)
hexline = np.clip(1 - np.abs(np.maximum(dy * 1.0 + dz * 0.6, dz * 1.15) - 0.52) / 0.09, 0, 1)
fin = np.maximum(fin, g * hexline * (z < 0.445) * (z > 0.225))
# C-intakes at the bumper corners (front view + side wrap)
CI = [(0.69, .24), (0.80, .25), (0.93, .27), (0.93, .45), (0.81, .47), (0.72, .47), (0.70, .44), (0.735, .43), (0.765, .36), (0.735, .29), (0.70, .28)]
ci = np.maximum(region(fr & (y > 0), CI, y, z), region(fr & (y < 0), [(-a, b) for a, b in CI], y, z)); blk = np.maximum(blk, ci)
# front lip splitter: black band along the bottom of the fascia
blk = np.maximum(blk, fr * sm(0.195, 0.175, z) * (ay < 0.85))
# fender vent (side view x,z) with two horizontal fins
FV = [(0.84, .30), (0.90, .30), (0.99, .60), (0.93, .60)]
fv = region(own_side & (x > 0.7) & (x < 1.1), FV, x, z); blk = np.maximum(blk, fv)
fin = np.maximum(fin, fv * ((np.abs(z - 0.40) < 0.008) | (np.abs(z - 0.50) < 0.008)))
# side-skirt blade: black lower blade under the rocker, lit top edge
sk = filled & (x > -0.95) & (x < 0.92) & (any_ > 0.2) & (z < 0.235)
skr = sk * sm(0.240, 0.226, z); blk = np.maximum(blk, skr)
fin = np.maximum(fin, sk * np.exp(-((z - 0.228) / 0.004) ** 2) * 1.2)
blk = np.maximum(blk, (filled & (z < 0.20) & (x > -0.95) & (x < 0.95) & (nz < -0.3)).astype(np.float32))
# rear diffuser (rear view y,z) with vertical fins, grey surround trim
rr = filled & (x < -1.85) & (nx < 0.2)
DF = [(-0.66, .20), (0.66, .20), (0.68, .44), (-0.68, .44)]
df = region(rr, DF, y, z); blk = np.maximum(blk, df)
fin = np.maximum(fin, df * (np.abs(((y + 0.6) / 0.15) % 1.0 - 0.5) > 0.44) * (z < 0.30))
fin = np.maximum(fin, rr * np.clip(1 - dist_to(closed(DF), y, z) / 0.006, 0, 1) * 0.9)
# rear reflector strips at the bumper corners (dark red), side intake shape on the rear bumper side
refl = rr & (ay > 0.70) & (ay < 0.86) & (np.abs(z - 0.47) < 0.012)
# class masks from the mesh: trim-class texels black, lamp-class texels = dark housing under the lamp decals
# trim-class mesh faces stay black only inside the real recesses (grille, diffuser); the stepped template faces of the
# fender vent / intake bands are ignored so the painted blueprint outlines define those edges smoothly
trimMK = (MK == 4) & (((x > 1.90) & (ay < 0.62) & (z < 0.50)) | (x < -1.50))
blk = np.maximum(blk, trimMK.astype(np.float32))
col = col * (1 - blk[..., None]) + BLACK * blk[..., None]
col = col * (1 - fin[..., None]) + GREY * fin[..., None]
col[refl] = (110, 12, 12)
# black window surround / B-pillar trim along the glass edge on the cabin (side view)
win = filled & (MK == 0) & (z > 0.90) & (z < 0.935) & (x > -1.05) & (x < 0.80) & (any_ > 0.6)
col[win] = col[win] * 0.25 + BLACK * 0.75

# ================================================================ vector panel lines
F = BP.FEAT
SIDE = [('both', [(0.74, .885), (0.72, .75), (0.71, .50), (0.71, .28)]),                              # door front cut
        ('both', [(0.71, .27), (-0.60, .27)]),                                                         # door bottom
        ('both', [(-0.60, .27), (-0.645, .45), (-0.655, .70), (-0.63, .89)]),                         # door rear cut
        ('both', rrect(-0.50, -0.33, .725, .76, .015)),                                                # door handle
        ('both', [(1.63, .74), (1.60, .60)]),                                                          # front bumper / fender split
        ('both', [(-1.66, .77), (-1.62, .62)]),                                                        # rear bumper split
        ('both', closed(FV)),                                                                          # fender vent edge
        ('both', [(0.92, .236), (-0.95, .236)]),                                                       # side-skirt blade edge
        ('R',    circle(-1.05, .80, .075)),                                                            # fuel door (car's right only)
        ('both', closed(F['lamp']['side'])), ('both', closed(F['lamp']['side_f']))]                    # lamp outlines (smooth edge)
hood = [(0.80, .665), (1.2, .655), (1.45, .64), (1.65, .625), (1.80, .59), (1.92, .52), (2.0, .40), (2.04, .25), (2.055, 0)]
mirror_y = lambda pl: [(a, -b) for a, b in pl]
TOP = [hood, mirror_y(hood), [(0.80, -0.665), (0.80, 0.665)],                                           # hood shut + cowl
       [(-1.62, -.55), (-1.62, .55)], [(-1.62, .58), (-1.95, .58)], [(-1.62, -.58), (-1.95, -.58)]]    # trunk lid
FRONT = [[(-.45, .66), (.45, .66)], closed(GR), closed(CI), closed([(-a, b) for a, b in CI])[::-1],
         closed(F['lamp']['front']), closed([(-a, b) for a, b in F['lamp']['front']])]
REAR = [[(-.40, .775), (.40, .775)], [(.40, .775), (.44, .89), (.55, .99)], [(-.40, .775), (-.44, .89), (-.55, .99)],
        [(.76, .78), (.90, .74)], [(-.76, .78), (-.90, .74)],
        closed(F['lamp']['rear']), closed([(-a, b) for a, b in F['lamp']['rear']])]
D2 = np.full(x.shape, 9.0, np.float32)
for flag, pl in SIDE:
    m = own_side & ((y < 0) if flag == 'R' else True)
    D2[m] = np.minimum(D2[m], dist_to(pl, x[m], z[m]))
for pl in TOP: D2[own_top] = np.minimum(D2[own_top], dist_to(pl, x[own_top], y[own_top]))
for pl in FRONT: D2[own_front] = np.minimum(D2[own_front], dist_to(pl, y[own_front], z[own_front]))
for pl in REAR: D2[own_rear] = np.minimum(D2[own_rear], dist_to(pl, y[own_rear], z[own_rear]))
core = .0022
line = np.clip(1 - (D2 - core) / aa, 0, 1) * 0.85 * (MK != 1)
gap = np.clip(1 - (D2 - core) / (aa * 2.5), 0, 1) * 0.18
col = col * (1 - gap[..., None]); col = col * (1 - line[..., None]) + LINE * line[..., None]
col[MK == 1] = (14, 18, 26); col[MK == 2] = (8, 8, 9)
col[~filled] = 0
img = col.copy(); f = filled.copy()
for _ in range(16):                                                 # seam dilation
    s = np.zeros_like(img); c = np.zeros(f.shape, np.float32)
    for dy_, dx_ in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        s += np.roll(np.roll(img * f[..., None], dy_, 0), dx_, 1); c += np.roll(np.roll(f, dy_, 0), dx_, 1)
    new = (~f) & (c > 0); img[new] = s[new] / c[new][:, None]; f = f | new
img[~f] = PAINT * 0.8
out = rgb555_bayer(Image.fromarray(np.flipud(np.clip(img, 0, 255).astype(np.uint8))))
out.save(dst); print('body texture', dst, 'coverage %.2f' % filled.mean(), 'texel %.4f m' % tex_m)
