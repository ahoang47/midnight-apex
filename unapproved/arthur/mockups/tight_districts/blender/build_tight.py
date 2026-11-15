# Blender 4.2 headless: the two new props for the tight-district cat-and-mouse frames (Arthur, unapproved mockup).
#   /workspace/tools/blender-4.2.3-linux-x64/blender -b -P blender/build_tight.py
# Reuses the Builder / mat / export helpers of ../../../experiments/wangan_two_corner/blender/build_wangan.py (read and
# exec'd up to its asset functions, so the conventions are identical), with this folder's texture / output paths.
#   wangan_gantry_2l  : the Wangan sign gantry re-proportioned for the 7.5 m two-lane deck (two signs, posts outside the walls)
#   street_curvemirror: the orange back-street curve mirror on a pole (painted convex face, never reflective)
# Axes (Blender): +X = away from the road edge (or across the road for centred pieces), Y = along, Z = up.
import bpy, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'experiments', 'wangan_two_corner', 'blender', 'build_wangan.py'))
code = open(SRC).read().split('# --- copied from districts')[0]
exec(code)   # defines reset / mat / Builder / export and the TEX / OUT / STATS globals ...
TEX = os.path.normpath(os.path.join(HERE, '..', 'godot', 'art', 'env'))      # ... re-pointed at this folder
OUT = os.path.normpath(os.path.join(HERE, '..', 'godot', 'assets', 'env'))
os.makedirs(OUT, exist_ok=True); STATS.clear()

def wangan_gantry_2l():
    reset(); b = Builder('wangan_gantry_2l'); st = mat('wangan_steel', 'wangan_steel'); e = mat('Emit_sodium', 'emit_sodium')
    s0 = mat('wangan_sign_0', 'wangan_sign_0'); s2 = mat('wangan_sign_2', 'wangan_sign_2')
    X = 4.7; z0, z1 = 6.6, 7.3           # posts stand just outside the 7.5 m deck walls
    for x in (-X, X):
        b.box((x, 0, -1.2), (0.4, 0.4, z1 + 0.3 + 1.2), st, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=3.0)
    for z in (z0, z1):
        for y in (-0.28, 0.28): b.beam((-X, y, z), (X, y, z), 0.15, st)
    n = 6
    for y in (-0.28, 0.28):
        for i in range(n):
            xa, xb = -X + 2 * X * i / n, -X + 2 * X * (i + 1) / n
            b.beam((xa, y, z0 if i % 2 == 0 else z1), (xb, y, z1 if i % 2 == 0 else z0), 0.075, st)
    def panel(cx, w, h, top, tex):
        y = 0.40; xa, xb = cx - w/2, cx + w/2; zb = top - h
        b.quad([(xb, y, zb), (xa, y, zb), (xa, y, top), (xb, y, top)], [(1, 0), (0, 0), (0, 1), (1, 1)], tex)
        b.quad([(xa, y - 0.06, zb), (xb, y - 0.06, zb), (xb, y - 0.06, top), (xa, y - 0.06, top)], [(0, 0), (1, 0), (1, 1), (0, 1)], st)
        b.quad([(xa, y + 0.5, zb - 0.05), (xb, y + 0.5, zb - 0.05), (xb, y, zb - 0.05), (xa, y, zb - 0.05)], [(0, 0), (1, 0), (1, 1), (0, 1)], st)
        for lx in (cx - w/4, cx + w/4):
            b.quad([(lx - 0.16, y + 0.48, zb - 0.04), (lx + 0.16, y + 0.48, zb - 0.04), (lx + 0.16, y + 0.32, zb - 0.04), (lx - 0.16, y + 0.32, zb - 0.04)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    panel(-1.2, 4.6, 1.75, z1 + 0.15, s0)     # route sign over the lanes (湾岸線 BAYSHORE RTE 東 EAST)
    panel(2.9, 1.5, 0.75, z1 - 0.1, s2)       # small blue CURVE board
    b.finish(); export('wangan_gantry_2l')

def street_curvemirror():
    reset(); b = Builder('street_curvemirror'); m = mat('street_curvemirror', 'street_curvemirror')
    pole_uv = [(0.02, 0.02), (0.1, 0.02), (0.1, 0.1), (0.02, 0.1)]
    r = 0.04; H = 2.6
    for (xa, ya), (xb, yb) in [((-r, -r), (r, -r)), ((r, -r), (r, r)), ((r, r), (-r, r)), ((-r, r), (-r, -r))]:   # square pole
        b.quad([(xa, ya, 0), (xb, yb, 0), (xb, yb, H), (xa, ya, H)], pole_uv, m)
    # round head, 0.6 m, an 8-gon facing the road (toward Blender -X, tilted down a touch), back plate behind it
    cz, R_, n = H + 0.25, 0.32, 8
    pts = [(math.cos(2 * math.pi * k / n) * R_, math.sin(2 * math.pi * k / n) * R_) for k in range(n)]
    for k in range(n):
        (ya, za), (yb, zb) = pts[k], pts[(k + 1) % n]
        uv = lambda y, z: (0.5 + y / (2 * R_) * 0.95, 0.5 + z / (2 * R_) * 0.95)
        b.tri([(-0.08, 0, cz), (-0.06 - za * 0.05, ya, cz + za), (-0.06 - zb * 0.05, yb, cz + zb)], [uv(0, 0), uv(ya, za), uv(yb, zb)], m)
        b.tri([(0.0, 0, cz), (0.0, yb, cz + zb), (0.0, ya, cz + za)], [(0.94, 0.06), (0.94, 0.06), (0.94, 0.06)], m)
    b.finish(tess=False); export('street_curvemirror')

wangan_gantry_2l(); street_curvemirror()
json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts_tight.json'), 'w'), indent=1)
print('STATS', STATS)
