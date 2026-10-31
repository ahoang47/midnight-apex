"""Body paint texture (1024, PS2-ish): Formula Red + baked AO / soft shading + crisp single panel lines.
Panel lines are vector polylines read off the blueprint views (metres), drawn per texel by distance in the view
plane that 'owns' the texel (dominant normal axis) -> one clean line, no doubled raster tracing.
Input: npz of per-texel world position / normal / material from Blender, optional baked AO png. Run with system python."""
import numpy as np, sys
from PIL import Image, ImageFilter
src, dst = sys.argv[1], sys.argv[2]; ao_png = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load(src); P, N, MK = D['pos'], D['nrm'], D['mask']; TS = P.shape[0]
PAINT = np.array([199, 13, 15], np.float32); LINE = np.array([44, 4, 6], np.float32)
x, y, z = P[..., 0], P[..., 1], P[..., 2]; nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
filled = MK >= 0

def rrect(x0, x1, z0, z1, r, n=6):
    """closed rounded rectangle polyline in a view plane"""
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n); pts.append((cx + r * np.cos(a), cz + r * np.sin(a)))
    return pts + [pts[0]]
mirror = lambda pl: [(a, -b) for a, b in pl]
# ---- side view (x, z); flag: 'both' sides, or 'L' (+y only)
SIDE = [
    ('both', [(0.34, .83), (0.40, .70), (0.41, .47), (0.39, .38), (0.37, .345)]),                 # door front
    ('both', [(0.37, .345), (-0.64, .345)]),                                                      # door bottom
    ('both', [(-0.707, .877), (-0.744, .79), (-0.745, .67), (-0.735, .52), (-0.707, .43), (-0.66, .36), (-0.64, .345)]),  # door rear
    ('both', rrect(-0.659, -0.451, .716, .793, .03)),                                              # door handle recess
    ('L',    rrect(-1.268, -1.122, .757, .853, .025)),                                             # fuel door (left)
    ('both', [(1.57, .585), (1.63, .53), (1.655, .45), (1.66, .30), (1.655, .21)]),               # front bumper / fender seam
]
# ---- top view (x, y), mirrored
hood = [(0.45, .645), (0.50, .636), (1.01, .571), (1.51, .478), (1.81, .375), (1.866, .32), (1.90, .15), (1.905, 0)]
trunk = [(-1.475, 0), (-1.46, .30), (-1.425, .60), (-1.926, .524), (-1.954, .49), (-1.954, 0)]
TOP = [hood, mirror(hood), trunk, mirror(trunk)]
# ---- front view (y, z)
FRONT = [[(-0.56, .55), (-0.40, .545), (0.40, .545), (0.56, .55)],                                  # bumper top seam (between the lamps)
         [(-0.36, .624), (0.36, .624)]]                                                          # hood front edge
# ---- rear view (y, z)
REAR = [[(-0.33, .672), (0.33, .672)],                                                           # trunk lid lower edge
        [(-0.95, .65), (-0.74, .66)], [(0.74, .66), (0.95, .65)],                                # bumper top seam outboard
        [(-0.525, .905), (-0.49, .85), (-0.42, .80)], [(0.525, .905), (0.49, .85), (0.42, .80)]] # trunk lid sides

def dist_to(pl, a, b):
    d = np.full(a.shape, 9.0, np.float32)
    for (a0, b0), (a1, b1) in zip(pl, pl[1:]):
        ea, eb = a1 - a0, b1 - b0; L2 = ea * ea + eb * eb + 1e-12
        t = np.clip(((a - a0) * ea + (b - b0) * eb) / L2, 0, 1)
        d = np.minimum(d, np.hypot(a - a0 - t * ea, b - b0 - t * eb))
    return d
dom = np.argmax(np.stack([np.abs(nx), np.abs(ny), np.abs(nz)]), 0)
own_side = filled & (dom == 1); own_top = filled & (dom == 2) & (nz > 0)
own_front = filled & (dom == 0) & (nx > 0); own_rear = filled & (dom == 0) & (nx < 0)
D2 = np.full(x.shape, 9.0, np.float32)
for flag, pl in SIDE:
    m = own_side & ((y > 0) if flag == 'L' else True)
    D2[m] = np.minimum(D2[m], dist_to(pl, x[m], z[m]))
for pl in TOP:
    D2[own_top] = np.minimum(D2[own_top], dist_to(pl, x[own_top], y[own_top]))
for pl in FRONT:
    D2[own_front] = np.minimum(D2[own_front], dist_to(pl, y[own_front], z[own_front]))
for pl in REAR:
    D2[own_rear] = np.minimum(D2[own_rear], dist_to(pl, y[own_rear], z[own_rear]))
# texel footprint in metres (for anti-aliasing): median spacing of neighbouring filled texels
dpx = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1); ok = filled[:, 1:] & filled[:, :-1]
tex_m = float(np.median(dpx[ok & (dpx < .05)]))
core, aa = .0022, max(tex_m, .002)
line = np.clip(1 - (D2 - core) / aa, 0, 1) * 0.85
gap_shadow = np.clip(1 - (D2 - core) / (aa * 2.5), 0, 1) * 0.18          # soft shoulder either side of the gap
# ---- shading: gentle top-light + baked AO
sh = 0.84 + 0.16 * np.clip((z - 0.15) / 0.5, 0, 1)
sh *= 1 + 0.05 * np.clip(nz, 0, 1)
if ao_png:
    ao = np.flipud(np.asarray(Image.open(ao_png).convert('L').filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0)
    if ao.shape[0] != TS: ao = np.asarray(Image.fromarray((ao * 255).astype(np.uint8)).resize((TS, TS), Image.BILINEAR)) / 255.0
    sh *= 0.40 + 0.60 * np.clip(ao, 0, 1) ** 1.1
col = PAINT[None, None] * (sh * (1 - gap_shadow))[..., None]
col = col * (1 - line[..., None]) + LINE[None, None] * line[..., None]
col[~filled] = 0
# dilate islands outward so bilinear filtering / mips never pull in black across UV seams
img = col.copy(); f = filled.copy()
for _ in range(16):
    s = np.zeros_like(img); c = np.zeros(f.shape, np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        s += np.roll(np.roll(img * f[..., None], dy, 0), dx, 1); c += np.roll(np.roll(f, dy, 0), dx, 1)
    new = (~f) & (c > 0); img[new] = s[new] / c[new][:, None]; f = f | new
img[~f] = PAINT * 0.8
Image.fromarray(np.flipud(np.clip(img, 0, 255).astype(np.uint8))).save(dst)
print('body texture', dst, 'coverage %.2f' % filled.mean(), 'texel %.4f m' % tex_m)
