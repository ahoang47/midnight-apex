# Blender 4.2 headless: the props for the mountain-district cat-and-mouse frames (Arthur, unapproved mockup).
#   /workspace/tools/blender-4.2.3-linux-x64/blender -b -P blender/build_mountain.py
# From tight_districts (unchanged): wangan_gantry_2l, street_curvemirror. New for the mountain pass:
#   mtn_retain_wall  : 4 m cast-concrete retaining wall, 3 m, battered, coping, U drainage channel at the foot (Wangan uphill side)
#   mtn_stone_wall   : 4 m diagonal-laid stone retaining wall, 4.5 m, battered (onsen-town uphill side)
#   mtn_house        : small two-storey hillside house, tiled gable roof, three lit paper-screen windows (town, downhill)
#   mtn_handrail     : 2 m galvanised pipe handrail on the downhill pavement edge
#   mtn_steps        : a flight of stone steps going down off the street between the houses, with a pipe rail
#   mtn_toll_sign    : roadside toll-road sign on two posts (Wangan skyline)
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

def mtn_retain_wall(name, tex, H, batter, channel):
    reset(); b = Builder(name); m = mat(tex, tex); L = 4.0
    for r in range(2):   # road face leans back by `batter` (x away from the road); 2 rows along
        ya, yb = -L/2 + L * r / 2, -L/2 + L * (r + 1) / 2; ua, ub = r / 2, (r + 1) / 2
        b.quad([(0, yb, 0), (0, ya, 0), (batter, ya, H), (batter, yb, H)], [(ub, 1), (ua, 1), (ua, 0.02), (ub, 0.02)], m)
        b.quad([(batter, yb, H), (batter, ya, H), (batter + 0.35, ya, H), (batter + 0.35, yb, H)], [(ub, 0.02), (ua, 0.02), (ua, 0), (ub, 0)], m)
        if channel:   # U drainage channel in front of the wall foot (texture foot rows)
            b.quad([(-0.45, yb, 0.0), (-0.45, ya, 0.0), (-0.45, ya, -0.25), (-0.45, yb, -0.25)], [(ub, 0.95), (ua, 0.95), (ua, 1), (ub, 1)], m)
            b.quad([(-0.45, yb, -0.25), (-0.45, ya, -0.25), (0, ya, -0.25), (0, yb, -0.25)], [(ub, 1), (ua, 1), (ua, 1), (ub, 1)], m)
            b.quad([(0, yb, -0.25), (0, ya, -0.25), (0, ya, 0), (0, yb, 0)], [(ub, 1), (ua, 1), (ua, 0.95), (ub, 0.95)], m)
    b.finish(tess=False); export(name)

def mtn_house():
    reset(); b = Builder('mtn_house'); w = mat('mtn_house_wall', 'mtn_house_wall'); r = mat('mtn_roof', 'mtn_roof'); e = mat('Emit_house_window', 'emit_house_window')
    D, Wd, H, rise, eave = 6.0, 7.0, 5.4, 1.6, 0.5    # x = depth away from the street, y = width along, z up
    b.box((D/2, 0, 0), (D, Wd, H), w, faces=['-x', '+x', '-y', '+y'], uvscale=5.0)
    for y in (-Wd/2, Wd/2):
        b.tri([(0, y, H), (D, y, H), (D/2, y, H + rise)], [(0, 0), (1, 0), (0.5, 0.3)], w)
    b.quad([(-eave, -Wd/2 - eave, H - 0.15), (-eave, Wd/2 + eave, H - 0.15), (D/2, Wd/2 + eave, H + rise), (D/2, -Wd/2 - eave, H + rise)], [(0, 0), (1.6, 0), (1.6, 1), (0, 1)], r)
    b.quad([(D + eave, Wd/2 + eave, H - 0.15), (D + eave, -Wd/2 - eave, H - 0.15), (D/2, -Wd/2 - eave, H + rise), (D/2, Wd/2 + eave, H + rise)], [(0, 0), (1.6, 0), (1.6, 1), (0, 1)], r)
    for (y, z) in ((-1.8, 3.6), (1.6, 3.6), (0.6, 1.2)):   # lit windows on the street-facing wall
        b.quad([(-0.02, y + 0.6, z), (-0.02, y - 0.6, z), (-0.02, y - 0.6, z + 1.0), (-0.02, y + 0.6, z + 1.0)], [(1, 0), (0, 0), (0, 1), (1, 1)], e)
    b.finish(tess=False); export('mtn_house')

def mtn_handrail():
    reset(); b = Builder('mtn_handrail'); g = mat('wangan_galv', 'wangan_galv'); L = 2.0
    b.box((0, -L/2 + 0.05, 0), (0.06, 0.06, 1.05), g, faces=['-x', '+x', '-y', '+y'])
    for z in (1.0, 0.55): b.beam((0, -L/2, z), (0, L/2, z), 0.05, g)
    b.finish(tess=False); export('mtn_handrail')

def mtn_steps():
    reset(); b = Builder('mtn_steps'); m = mat('mtn_steps', 'mtn_steps'); g = mat('wangan_galv', 'wangan_galv')
    n, run, rise, Wd = 10, 0.42, 0.30, 1.4         # descends away from the street along +x
    for i in range(n):
        x0, x1, z = i * run, (i + 1) * run, -i * rise
        b.quad([(x0, -Wd/2, z), (x0, Wd/2, z), (x1, Wd/2, z), (x1, -Wd/2, z)], [(0, i / n), (1, i / n), (1, (i + 0.8) / n), (0, (i + 0.8) / n)], m)
        b.quad([(x1, -Wd/2, z), (x1, Wd/2, z), (x1, Wd/2, z - rise), (x1, -Wd/2, z - rise)], [(0, (i + 0.8) / n), (1, (i + 0.8) / n), (1, (i + 1) / n), (0, (i + 1) / n)], m)
    for y in (-Wd/2, Wd/2):
        b.quad([(0, y, 0), (n * run, y, -n * rise), (n * run, y, -n * rise - 0.6), (0, y, -0.6)], [(0, 0), (1, 0), (1, 0.1), (0, 0.1)], m)
    b.beam((0.1, Wd/2 - 0.1, 0.95), (n * run, Wd/2 - 0.1, -n * rise + 0.95), 0.05, g)
    b.finish(tess=False); export('mtn_steps')

def mtn_toll_sign():
    # single-post cantilever: post at x 0.6 (behind the drainage channel), board out over the lane edge, facing the
    # oncoming car (Blender +Y = back down the road), 2.55 x 0.8 m, bottom 2.7 m up
    reset(); b = Builder('mtn_toll_sign'); st = mat('wangan_steel', 'wangan_steel'); sg = mat('mtn_sign_toll', 'mtn_sign_toll')
    b.box((0.6, 0, 0), (0.14, 0.14, 3.75), st, faces=['-x', '+x', '-y', '+y', '+z'])
    b.beam((0.6, 0.0, 3.55), (-2.0, 0.0, 3.55), 0.08, st)
    xa, xb, zb, zt = -2.0, 0.55, 2.7, 3.5
    b.quad([(xb, 0.1, zb), (xa, 0.1, zb), (xa, 0.1, zt), (xb, 0.1, zt)], [(1, 0), (0, 0), (0, 1), (1, 1)], sg)
    b.quad([(xa, 0.05, zb), (xb, 0.05, zb), (xb, 0.05, zt), (xa, 0.05, zt)], [(0, 0), (1, 0), (1, 1), (0, 1)], st)
    b.finish(tess=False); export('mtn_toll_sign')

wangan_gantry_2l(); street_curvemirror()
mtn_retain_wall('mtn_retain_wall', 'mtn_retain_concrete', 3.0, 0.35, True)
mtn_retain_wall('mtn_stone_wall', 'mtn_stonewall', 4.5, 0.6, False)
mtn_house(); mtn_handrail(); mtn_steps(); mtn_toll_sign()
json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts_mountain.json'), 'w'), indent=1)

print('STATS', STATS)
