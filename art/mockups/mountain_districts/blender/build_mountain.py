# Blender 4.2 headless: the props for the mountain-district cat-and-mouse frames (Arthur, unapproved mockup).
#   /workspace/tools/blender-4.2.3-linux-x64/blender -b -P blender/build_mountain.py
# From tight_districts (unchanged): wangan_gantry_2l, street_curvemirror. New for the mountain pass:
#   mtn_retain_wall  : 4 m cast-concrete retaining wall, 3 m, battered, coping, U drainage channel at the foot (Wangan uphill side)
#   mtn_stone_wall   : 4 m diagonal-laid stone retaining wall, 4.5 m, battered (onsen-town uphill side)
#   mtn_house        : small two-storey hillside house, tiled gable roof, three lit paper-screen windows (town, downhill)
#   mtn_handrail     : 2 m galvanised pipe handrail on the downhill pavement edge
#   mtn_steps        : a flight of stone steps going down off the street between the houses, with a pipe rail
#   mtn_toll_sign    : roadside toll-road sign on two posts (Wangan skyline)
# Reuses the Builder / mat / export helpers of blender/build_wangan.py (vendored from the deleted wangan_two_corner test; read and
# exec'd up to its asset functions, so the conventions are identical), with this folder's texture / output paths.
#   wangan_gantry_2l  : the Wangan sign gantry re-proportioned for the 7.5 m two-lane deck (two signs, posts outside the walls)
#   street_curvemirror: the orange back-street curve mirror on a pole (painted convex face, never reflective)
# Axes (Blender): +X = away from the road edge (or across the road for centred pieces), Y = along, Z = up.
import bpy, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'build_wangan.py')
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

# ════ PASS 2 (Austin 2026-11-15: "the side assets should be decreasing in height, to achieve perspective"; the street
#      "doesn't feel like city in the mountains"). Regular, real-size verticals and edges for the eye to measure the
#      climb with, and a hillside-city block kit built into the slope.
#   mtn_lattice_slope_g / _c : 4 m module of 法枠 lattice-framed cut slope (2 m x 2.15 m cells, proud cast beams; grass / shotcrete)
#   mtn_retain_wall_p        : the Wangan retaining wall with a pilaster at every 4 m joint and a proud coping
#   mtn_delineator           : 1 m white post with an amber reflector (every 8 m on the guardrail / parapet)
#   mtn_block_up_a..d        : mid-rise blocks entered at road level on the uphill side (3-6 floors, balcony slabs, windows,
#                              ground-floor fronts, a blade sign)
#   mtn_block_dn_a..c        : downhill blocks whose roof or top floors are at road level and 4-6 floors go down the slope
#   mtn_footbridge           : pedestrian bridge over the street from the uphill block's 2nd floor to a pier on the drop side
#   mtn_steps_up             : stair alley climbing between uphill blocks, stone cheeks, pipe rail
import random as _rnd
def mtn_lattice_slope(name, fill):
    reset(); b = Builder(name); f = mat(fill, fill); bm_ = mat('mtn_lattice_beam', 'mtn_lattice_beam')
    run, rise, L = 5.0, 7.0, 4.0; sl = math.hypot(run, rise); n = (-rise / sl, 0.0, run / sl)
    b.quad([(0, L/2, 0), (0, -L/2, 0), (run, -L/2, rise), (run, L/2, rise)], [(L, 0), (0, 0), (0, sl), (L, sl)], f)
    b.quad([(run, L/2, rise), (run, -L/2, rise), (run + 3.0, -L/2, rise + 0.6), (run + 3.0, L/2, rise + 0.6)], [(L, 0), (0, 0), (0, 3), (L, 3)], f)
    o = lambda x, y, z, k=0.13: (x + n[0] * k, y, z + n[2] * k)
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        b.beam(o(run * t, -L/2, rise * t), o(run * t, L/2, rise * t), 0.3, bm_)
    for y in (-L/2, 0.0):
        b.beam(o(0, y, 0), o(run, y, rise), 0.3, bm_)
    b.finish(); export(name)

def mtn_retain_wall_p():
    reset(); b = Builder('mtn_retain_wall_p'); m = mat('mtn_retain_concrete', 'mtn_retain_concrete'); L, H, bt = 4.0, 3.0, 0.35
    for r in range(2):
        ya, yb = -L/2 + L * r / 2, -L/2 + L * (r + 1) / 2; ua, ub = r / 2, (r + 1) / 2
        b.quad([(0, yb, 0), (0, ya, 0), (bt, ya, H), (bt, yb, H)], [(ub, 1), (ua, 1), (ua, 0.02), (ub, 0.02)], m)
        b.quad([(-0.45, yb, 0.0), (-0.45, ya, 0.0), (-0.45, ya, -0.25), (-0.45, yb, -0.25)], [(ub, 0.95), (ua, 0.95), (ua, 1), (ub, 1)], m)
        b.quad([(-0.45, yb, -0.25), (-0.45, ya, -0.25), (0, ya, -0.25), (0, yb, -0.25)], [(ub, 1), (ua, 1), (ua, 1), (ub, 1)], m)
    b.box((0.12, -L/2, 0), (0.5, 0.5, H + 0.3), m, faces=['-x', '-y', '+y', '+z'], uvscale=4.0)   # pilaster at the joint
    b.box((bt * 0.5 + 0.05, 0, H), (0.7, L, 0.3), m, faces=['-x', '+z'], uvscale=4.0)            # coping
    b.finish(tess=False); export('mtn_retain_wall_p')

def mtn_delineator():
    reset(); b = Builder('mtn_delineator'); e = mat('Emit_delineator', 'emit_delineator')
    b.box((0, 0, 0), (0.07, 0.07, 1.0), e, faces=['-x', '+x', '-y', '+y'])
    b.finish(tess=False); export('mtn_delineator')

F = 3.1
def _win(b, e, rng, x, ya, yb, z, side='-x'):
    n = max(1, round(abs(yb - ya) / 1.6)); u0 = rng.randrange(32) / 32; u1 = u0 + n / 32
    if side == '-x': b.quad([(x, yb, z + 0.95), (x, ya, z + 0.95), (x, ya, z + 2.3), (x, yb, z + 2.3)], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], e)
    else: b.quad([(ya, x, z + 0.95), (yb, x, z + 0.95), (yb, x, z + 2.3), (ya, x, z + 2.3)], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], e)
def _blade(b, s_, cell, x0, x1, y, z0, z1):
    u0, u1 = cell / 6, (cell + 1) / 6
    for yy, flip in ((y + 0.03, False), (y - 0.03, True)):
        vs = [(x1, yy, z0), (x0, yy, z0), (x0, yy, z1), (x1, yy, z1)]
        b.quad(vs, [(u0, 0), (u1, 0), (u1, 1), (u0, 1)] if not flip else [(u1, 0), (u0, 0), (u0, 1), (u1, 1)], s_)
def mtn_block(name, Wd, floors, below, depth, wall, ground, sign, seed, roof_sign=None, tank=False, side_win=False):
    reset(); b = Builder(name); rng = _rnd.Random(seed)
    w = mat(wall, wall); r = mat('mtn_roof_flat', 'mtn_roof_flat'); e = mat('Emit_mtn_windows', 'emit_mtn_windows')
    g = mat('Emit_mtn_ground', 'emit_mtn_ground'); s_ = mat('Emit_mtn_signs', 'emit_mtn_signs')
    zt, zb = floors * F, -below * F
    b.box((depth / 2, 0, zb), (depth, Wd, zt - zb), w, faces=['-x', '+x', '-y', '+y'], uvscale=4.0)
    b.box((depth / 2, 0, zt), (depth, Wd, 0.01), r, faces=['+z'], uvscale=4.0)
    b.box((0.15, 0, zt), (0.5, Wd + 0.1, 0.45), w, faces=['-x', '+z', '-y', '+y'], uvscale=4.0)   # roof coping
    for f in range(-below, floors):
        z = f * F
        if f == 0 and ground is not None:
            b.quad([(-0.03, Wd/2 - 0.3, 0.0), (-0.03, -Wd/2 + 0.3, 0.0), (-0.03, -Wd/2 + 0.3, 2.7), (-0.03, Wd/2 - 0.3, 2.7)],
                   [(ground * 0.25, 0), ((ground + 1) * 0.25, 0), ((ground + 1) * 0.25, 1), (ground * 0.25, 1)], g)
            b.quad([(0, Wd/2 - 0.2, 2.95), (0, -Wd/2 + 0.2, 2.95), (-0.9, -Wd/2 + 0.2, 2.75), (-0.9, Wd/2 - 0.2, 2.75)], [(0, 0), (1, 0), (1, 1), (0, 1)], r)
            continue
        _win(b, e, rng, -0.03, -Wd/2 + 0.5, Wd/2 - 0.5, z)
        if side_win:
            _win(b, e, rng, -Wd/2 - 0.03, 0.6, depth - 0.6, z, side='-y'); _win(b, e, rng, Wd/2 + 0.03, depth - 0.6, 0.6, z, side='+y')
        if f >= 1 or (f < 0):
            b.box((-0.3, 0, z - 0.12), (0.6, Wd - 0.4, 0.16), w, faces=['-x', '+z', '-z', '-y', '+y'], uvscale=4.0)   # balcony slab
    if sign is not None and floors >= 3:
        _blade(b, s_, sign, -0.15, -0.95, Wd/2 - 0.7, F + 0.3, F + 0.3 + 3.0)
    if roof_sign is not None:
        u0, u1 = roof_sign / 6, (roof_sign + 1) / 6
        b.quad([(0.6, Wd/2 - 1.2, zt + 0.5), (0.6, Wd/2 - 2.2, zt + 0.5), (0.6, Wd/2 - 2.2, zt + 3.4), (0.6, Wd/2 - 1.2, zt + 3.4)], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], s_)
        b.beam((0.7, Wd/2 - 1.7, zt), (0.7, Wd/2 - 1.7, zt + 0.5), 0.1, w)
    if tank:
        b.box((depth * 0.6, -Wd * 0.2, zt), (1.8, 1.8, 1.5), w, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=4.0)
    b.finish(); export(name)

def mtn_footbridge():
    reset(); b = Builder('mtn_footbridge'); fa = mat('mtn_bridge_fascia', 'mtn_bridge_fascia'); rl = mat('mtn_rail', 'mtn_rail')
    w = mat('mtn_block_wall_b', 'mtn_block_wall_b'); e = mat('Emit_sodium', 'emit_sodium')
    x0, x1, z0, z1, hw = 1.0, -12.4, 5.3, 6.0, 1.3   # pier 4.5 m past the downhill kerb, off the middle of the frame
    b.box(((x0 + x1) / 2, 0, z0), (x0 - x1, 2 * hw, z1 - z0), w, faces=['-z', '+z', '-x'], uvscale=4.0, uvfront=None)
    for y in (-hw, hw):
        b.quad([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(0, 0), (6, 0), (6, 1), (0, 1)], fa)
        b.quad([(x0, y, z1), (x1, y, z1), (x1, y, z1 + 1.1), (x0, y, z1 + 1.1)], [(0, 0), (6, 0), (6, 1), (0, 1)], rl)
    b.box((x1 + 0.4, 0, -14.0), (0.7, 0.9, 14.0 + z0), w, faces=['-x', '+x', '-y', '+y'], uvscale=4.0)   # pier on the drop side
    b.quad([(-3.4, 0.25, z0 - 0.02), (-4.4, 0.25, z0 - 0.02), (-4.4, -0.25, z0 - 0.02), (-3.4, -0.25, z0 - 0.02)], [(0, 0), (1, 0), (1, 1), (0, 1)], e)
    b.finish(); export('mtn_footbridge')

def mtn_steps_up():
    reset(); b = Builder('mtn_steps_up'); m = mat('mtn_steps', 'mtn_steps'); sw = mat('mtn_stonewall', 'mtn_stonewall'); g = mat('wangan_galv', 'wangan_galv')
    n, run, rise, Wd = 14, 0.36, 0.3, 1.6
    for i in range(n):
        x0, x1, z = i * run, (i + 1) * run, (i + 1) * rise
        b.quad([(x0, -Wd/2, z - rise), (x0, Wd/2, z - rise), (x0, Wd/2, z), (x0, -Wd/2, z)], [(0, i / n), (1, i / n), (1, (i + 0.2) / n), (0, (i + 0.2) / n)], m)
        b.quad([(x0, -Wd/2, z), (x0, Wd/2, z), (x1, Wd/2, z), (x1, -Wd/2, z)], [(0, (i + 0.2) / n), (1, (i + 0.2) / n), (1, (i + 1) / n), (0, (i + 1) / n)], m)
    for y in (-Wd/2 - 0.02, Wd/2 + 0.02):
        b.quad([(0, y, 0), (n * run, y, n * rise), (n * run, y, n * rise + 2.6), (0, y, 2.6)], [(0, 0), (1.2, 0), (1.2, 0.8), (0, 0.8)], sw)
    b.beam((0.1, Wd/2 - 0.12, 0.95), (n * run, Wd/2 - 0.12, n * rise + 0.95), 0.05, g)
    b.finish(); export('mtn_steps_up')

mtn_lattice_slope('mtn_lattice_slope_g', 'mtn_lattice_fill_g'); mtn_lattice_slope('mtn_lattice_slope_c', 'mtn_lattice_fill_c')
mtn_retain_wall_p(); mtn_delineator()
mtn_block('mtn_block_up_a', 9.0, 5, 0, 10.0, 'mtn_block_wall_a', 0, 0, 11, tank=True)
mtn_block('mtn_block_up_b', 7.5, 4, 0, 9.0, 'mtn_block_wall_b', 1, 3, 12)
mtn_block('mtn_block_up_c', 11.0, 6, 0, 11.0, 'mtn_block_wall_c', 3, 1, 13, tank=True)
mtn_block('mtn_block_up_d', 8.0, 3, 0, 9.0, 'mtn_block_wall_a', 2, 4, 14)
mtn_block('mtn_block_dn_a', 9.0, 1, 5, 10.0, 'mtn_block_wall_b', None, None, 21, roof_sign=0, side_win=True)
mtn_block('mtn_block_dn_b', 10.0, 0, 6, 11.0, 'mtn_block_wall_a', None, None, 22, roof_sign=2, side_win=True)
mtn_block('mtn_block_dn_d', 10.0, 0, 6, 11.0, 'mtn_block_wall_b', None, None, 24, side_win=True)   # roof at road level, no rooftop board (beside the camera)
mtn_block('mtn_block_dn_c', 8.0, 2, 4, 9.0, 'mtn_block_wall_c', None, None, 23, roof_sign=5, side_win=True, tank=True)
mtn_block('mtn_block_tier_a', 12.0, 6, 3, 10.0, 'mtn_block_wall_a', None, None, 31, roof_sign=1, side_win=True, tank=True)
mtn_block('mtn_block_tier_b', 9.0, 4, 3, 9.0, 'mtn_block_wall_c', None, None, 32, side_win=True)
mtn_block('mtn_block_tier_c', 14.0, 8, 3, 12.0, 'mtn_block_wall_b', None, None, 33, roof_sign=0, side_win=True, tank=True)
mtn_footbridge(); mtn_steps_up()

json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts_mountain.json'), 'w'), indent=1)

print('STATS', STATS)

# ── pass 3 (Austin 2026-11-15): the Wangan cut gets its own expressway vocabulary, the touge keeps the 法枠 lattice.
#   mtn_soundwall      : 4 m module of louvred steel noise barrier, 2 m, an H-post on the joint (lines up with the wall pilaster)
#   mtn_shotcrete_net  : 4 m module of low shotcrete slope with rock netting, run 3.2 m / rise 3.0 m (v2 lattice: 5 / 7 m),
#                        a horizontal berm strip on top and a thin crest drain lip: horizontal-dominant, no diagonal beams
def mtn_soundwall():
    reset(); b = Builder('mtn_soundwall'); p = mat('mtn_soundwall', 'mtn_soundwall'); st = mat('wangan_steel', 'wangan_steel'); L, H = 4.0, 1.6
    b.quad([(0, L/2, 0), (0, -L/2, 0), (0, -L/2, H), (0, L/2, H)], [(1, 1), (0, 1), (0, 0), (1, 0)], p)
    b.box((0.02, -L/2, 0), (0.22, 0.22, H + 0.12), st, faces=['-x', '-y', '+y', '+z'], uvscale=3.0)   # H-post on the joint
    b.box((0.02, 0, H), (0.14, L, 0.1), st, faces=['-x', '+z'], uvscale=3.0)                          # top rail
    b.finish(tess=False); export('mtn_soundwall')

def mtn_shotcrete_net():
    reset(); b = Builder('mtn_shotcrete_net'); f = mat('mtn_shotcrete_net', 'mtn_shotcrete_net'); c = mat('mtn_retain_concrete', 'mtn_retain_concrete')
    run, rise, L = 3.2, 3.0, 4.0; sl = math.hypot(run, rise)
    b.quad([(0, L/2, 0), (0, -L/2, 0), (run, -L/2, rise), (run, L/2, rise)], [(L / 2, 0), (0, 0), (0, sl / 2), (L / 2, sl / 2)], f)
    b.box((run + 0.15, 0, rise), (0.3, L, 0.25), c, faces=['-x', '+z'], uvscale=4.0)                    # crest drain lip
    b.quad([(run + 0.3, L/2, rise + 0.25), (run + 0.3, -L/2, rise + 0.25), (run + 4.0, -L/2, rise + 0.9), (run + 4.0, L/2, rise + 0.9)], [(L / 2, 0), (0, 0), (0, 2), (L / 2, 2)], f)
    b.finish(tess=False); export('mtn_shotcrete_net')
mtn_soundwall(); mtn_shotcrete_net()
json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts_mountain.json'), 'w'), indent=1)
print('STATS v3', {k: STATS[k] for k in ('mtn_soundwall', 'mtn_shotcrete_net') if k in STATS})

# ── pass 4 (Austin 2026-11-15: a Key West sea bridge for Wangan, tight canyon streets for Street) ─────────────────────────
#   mtn_sea_pier      : improved wangan_pier for the 7.5 m deck: twin battered columns, a crosshead under the girder (top at
#                       the soffit, -1.8 m), columns run 40 m down (the water plane cuts them at whatever height the deck is)
#   mtn_sea_pilecap   : the pile cap at the waterline (placed at the water level, not the deck), a lighter tide band
#   mtn_old_span      : one 20 m span of the old Overseas-railway bridge alongside (concrete arch faces, pier at one end)
#   mtn_alley_walkway : enclosed lit walkway across the 4.8 m canyon street between the 2nd floors
#   mtn_block_al_a..d : narrow-frontage (5-7 m) canyon blocks, 3-6 floors, every one with a lit shopfront and a blade sign
def mtn_sea_pier():
    # hammerhead crosshead 11.6 m wide under the 8.7 m deck, twin columns stood just outboard of the deck edge so they read beside
    # the girder from the deck (a little artistic licence on the Seven Mile Bridge's under-deck piers)
    reset(); b = Builder('mtn_sea_pier'); m = mat('wangan_pier', 'wangan_pier')
    soffit = -1.8; X = 5.0
    for x in (-X, X):
        b.quad([(x - 0.75, 0.75, -40.0), (x - 0.75, -0.75, -40.0), (x - 0.6, -0.6, soffit - 1.3), (x - 0.6, 0.6, soffit - 1.3)], [(0, 6), (0.4, 6), (0.4, 0), (0, 0)], m)
        b.quad([(x + 0.75, -0.75, -40.0), (x + 0.75, 0.75, -40.0), (x + 0.6, 0.6, soffit - 1.3), (x + 0.6, -0.6, soffit - 1.3)], [(0, 6), (0.4, 6), (0.4, 0), (0, 0)], m)
        b.quad([(x - 0.75, -0.75, -40.0), (x + 0.75, -0.75, -40.0), (x + 0.6, -0.6, soffit - 1.3), (x - 0.6, -0.6, soffit - 1.3)], [(0, 6), (0.4, 6), (0.4, 0), (0, 0)], m)
        b.quad([(x + 0.75, 0.75, -40.0), (x - 0.75, 0.75, -40.0), (x - 0.6, 0.6, soffit - 1.3), (x + 0.6, 0.6, soffit - 1.3)], [(0, 6), (0.4, 6), (0.4, 0), (0, 0)], m)
    b.box((0, 0, soffit - 1.3), (2 * X + 1.6, 2.0, 1.3), m, faces=['-x', '+x', '-y', '+y', '-z', '+z'], uvscale=6.0)   # crosshead
    b.finish(tess=False); export('mtn_sea_pier')

def mtn_sea_pilecap():
    reset(); b = Builder('mtn_sea_pilecap'); m = mat('wangan_pier', 'wangan_pier'); c = mat('mtn_retain_concrete', 'mtn_retain_concrete')
    b.box((0, 0, -0.6), (12.4, 3.0, 1.5), c, faces=['-x', '+x', '-y', '+y', '+z'], uvscale=4.0)
    b.finish(tess=False); export('mtn_sea_pilecap')

def mtn_old_span():
    reset(); b = Builder('mtn_old_span'); m = mat('mtn_retain_concrete', 'mtn_retain_concrete'); L, hw = 20.0, 3.0
    b.box((0, 0, -1.0), (2 * hw, L, 1.0), m, faces=['-x', '+x', '+z'], uvscale=4.0)   # deck slab
    n = 8
    for i in range(n):   # arch faces both sides: wall from the deck down to the intrados (springing -7 m, crown -1.2 m)
        ya, yb = -L/2 + L * i / n, -L/2 + L * (i + 1) / n
        za, zb = -7.0 + 5.8 * (1 - (ya / (L/2)) ** 2), -7.0 + 5.8 * (1 - (yb / (L/2)) ** 2)
        for x, flip in ((-hw, False), (hw, True)):
            vs = [(x, ya, za), (x, yb, zb), (x, yb, -1.0), (x, ya, -1.0)]
            if flip: vs = [vs[1], vs[0], vs[3], vs[2]]
            b.quad(vs, [(0, 1), (1, 1), (1, 0), (0, 0)], m)
        b.quad([(-hw, yb, zb), (-hw, ya, za), (hw, ya, za), (hw, yb, zb)], [(0, 0), (1, 0), (1, 1), (0, 1)], m)   # soffit
    b.box((0, -L/2, -30.0), (2 * hw + 0.6, 2.2, 23.0), m, faces=['-x', '+x', '-y', '+y'], uvscale=4.0)   # pier
    b.finish(tess=False); export('mtn_old_span')

def mtn_alley_walkway():
    reset(); b = Builder('mtn_alley_walkway'); w = mat('mtn_block_wall_b', 'mtn_block_wall_b'); e = mat('Emit_mtn_windows', 'emit_mtn_windows')
    x0, x1, z0, hw = 0.4, -5.9, 6.2, 1.2
    b.box(((x0 + x1) / 2, 0, z0), (x0 - x1, 2 * hw, 0.6), w, faces=['-z', '-y', '+y'], uvscale=4.0)
    b.box(((x0 + x1) / 2, 0, z0 + 2.6), (x0 - x1, 2 * hw + 0.2, 0.4), w, faces=['-z', '+z', '-y', '+y'], uvscale=4.0)
    for y in (-hw, hw):   # glazed sides: window strip between the slabs
        u1 = 3 / 32
        vs = [(x0, y, z0 + 0.6), (x1, y, z0 + 0.6), (x1, y, z0 + 2.6), (x0, y, z0 + 2.6)]
        if y > 0: vs = [vs[1], vs[0], vs[3], vs[2]]
        b.quad(vs, [(0, 0), (u1, 0), (u1, 1), (0, 1)], e)
    b.finish(tess=False); export('mtn_alley_walkway')

mtn_sea_pier(); mtn_sea_pilecap(); mtn_old_span(); mtn_alley_walkway()
mtn_block('mtn_block_al_a', 5.5, 6, 0, 9.0, 'mtn_block_wall_a', 0, 0, 41)
mtn_block('mtn_block_al_b', 6.5, 5, 0, 9.0, 'mtn_block_wall_b', 2, 3, 42, tank=True)
mtn_block('mtn_block_al_c', 5.0, 4, 0, 8.0, 'mtn_block_wall_c', 3, 5, 43)
mtn_block('mtn_block_al_d', 7.0, 3, 0, 8.0, 'mtn_block_wall_a', 1, 4, 44)
json.dump(dict(STATS), open(os.path.join(OUT, 'tri_counts_mountain.json'), 'w'), indent=1)
