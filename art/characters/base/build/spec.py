"""Shared data for the Midnight Apex base character (pure python: used by Blender build + PIL painter).
Blender coords: Z up, character faces -Y, character LEFT = +X. Units: metres. T-pose, feet at Z=0.
A loft = rings along an axis. Ring = (cx, cy, cz, rx, ry, extra).
axis 'z'  : e1=+X (width), e2=+Y (depth)   theta=0 -> front (-Y)
axis 'x'  : e1=+Z, e2=+Y (arms, either side)
axis 'y'  : e1=+X, e2=-Z (shoes; theta=0 -> top, seam under the sole)
UV: u = 0..1 around (front at u=0.5, seam at the back/sole), v runs along the loft inside its rect.
"""
import os as _os
_BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))          # .../art/characters/base in the repo
_GAME = _os.path.normpath(_os.path.join(_BASE, "..", "..", "..", "assets", "characters", "base"))
IN_REPO = _os.path.isdir(_os.path.join(_BASE, "..", "..", "..", "assets"))
GAMEDIR = _GAME if IN_REPO else _BASE                       # game-ready glbs
TEXDIR = _os.path.join(GAMEDIR, "textures")                  # textures/{m,f}/*.png
P = "mixamorig:"

# name, parent, head, tail, deform   (male, tune-up pass: bigger head / shorter neck, shorter arms)
BONES = [
    ("Hips", None, (0, 0, 0.95), (0, 0, 1.03), True),
    ("Spine", "Hips", (0, 0, 1.03), (0, 0, 1.17), True),
    ("Spine1", "Spine", (0, 0, 1.17), (0, 0, 1.31), True),
    ("Spine2", "Spine1", (0, 0, 1.31), (0, 0, 1.47), True),
    ("Neck", "Spine2", (0, 0, 1.47), (0, 0.0, 1.582), True),
    ("Head", "Neck", (0, 0.0, 1.582), (0, 0.0, 1.829), True),
    ("HeadTop_End", "Head", (0, 0.0, 1.829), (0, 0.0, 1.896), False),
]
for S, s in (("Left", 1), ("Right", -1)):
    BONES += [
        (S + "Shoulder", "Spine2", (0.05 * s, 0, 1.44), (0.17 * s, 0, 1.45), True),
        (S + "Arm", S + "Shoulder", (0.17 * s, 0, 1.45), (0.44 * s, 0, 1.45), True),
        (S + "ForeArm", S + "Arm", (0.44 * s, 0, 1.45), (0.71 * s, 0, 1.45), True),
        (S + "Hand", S + "ForeArm", (0.71 * s, 0, 1.45), (0.87 * s, 0, 1.45), True),
        (S + "UpLeg", "Hips", (0.095 * s, 0, 0.90), (0.103 * s, 0, 0.49), True),
        (S + "Leg", S + "UpLeg", (0.103 * s, 0, 0.49), (0.11 * s, 0.02, 0.09), True),
        (S + "Foot", S + "Leg", (0.11 * s, 0.02, 0.09), (0.11 * s, -0.09, 0.02), True),
        (S + "ToeBase", S + "Foot", (0.11 * s, -0.09, 0.02), (0.11 * s, -0.17, 0.02), True),
        (S + "Toe_End", S + "ToeBase", (0.11 * s, -0.17, 0.02), (0.11 * s, -0.21, 0.02), False),
    ]

# ---------------- male tune-up warp (loft definitions + weights stay in the original reference space) ----------------
HEAD_S, HEAD_PIV, HEAD_DZ = 1.12, 1.58, -0.02       # head +12 %, dropped 2 cm onto a shorter neck
def _ax(a):     # shorter arms: upper arm .29->.27, forearm .30->.27, hand x0.94
    if a <= .17: return a
    if a <= .46: return .17 + (a - .17) * (.27 / .29)
    if a <= .76: return .44 + (a - .46) * .90
    return .71 + (a - .76) * .94
def warp_point(x, y, z, group):
    if group == "head": return (x * HEAD_S, y * HEAD_S, HEAD_PIV + (z - HEAD_PIV) * HEAD_S + HEAD_DZ)
    if group in ("arm", "hand"): return ((1 if x >= 0 else -1) * _ax(abs(x)), y, z)
    return (x, y, z)

# Shape keys. Factors (slim e1, slim e2, bulky e1, bulky e2); radial about each ring centre ('head': about the vertical axis).
SHAPE = {
    "neck": (0.86, 0.86, 1.32, 1.32),
    "arm": (0.80, 0.80, 1.34, 1.34),
    "hand": (0.92, 0.92, 1.12, 1.12),
    "leg": (0.80, 0.80, 1.32, 1.32),
    "head": (0.98, 0.98, 1.06, 1.06),
    "shoe": (0.96, 1.0, 1.08, 1.0),
}
# trunk factors vary with height (male reference z): belly + chest get the most depth when bulky
TRUNK_SLIM = [(.86, (.86, .84)), (1.10, (.80, .78)), (1.36, (.84, .84)), (1.53, (.88, .88))]
TRUNK_BULKY = [(.86, (1.34, 1.30)), (.95, (1.36, 1.36)), (1.05, (1.42, 1.55)), (1.20, (1.40, 1.50)), (1.36, (1.36, 1.42)),
               (1.45, (1.30, 1.30)), (1.53, (1.25, 1.22))]
SHIFT = {"arm": (-.012, .040), "hand": (-.012, .040), "leg": (-.008, .022), "shoe": (-.008, .022), "foot": (-.008, .022)}   # sideways (slim, bulky)
def trunk_factor(z, which):
    keys = TRUNK_SLIM if which == "slim" else TRUNK_BULKY
    return tuple(_interp(z, [(k, v[i]) for k, v in keys]) for i in (0, 1))

def _arm(name, piece, side, rings, rect, sides=8, cap1=False, group="arm", chain="arm"):
    s = 1 if side == "L" else -1
    return dict(name=name + "_" + side, piece=piece, axis="x", side=side, sides=sides, group=group, chain=chain,
                rings=[(x * s, 0.0, 1.45, rx, ry, {}) for (x, rx, ry) in rings], rect=rect, cap0=False, cap1=cap1)

def _leg(name, piece, side, rings, rect, sides=8):
    s = 1 if side == "L" else -1
    return dict(name=name + "_" + side, piece=piece, axis="z", side=side, sides=sides, group="leg", chain="leg",
                rings=[(x * s, y, z, rx, ry, {}) for (x, y, z, rx, ry) in rings], rect=rect, cap0=False, cap1=False)

# ---- Body atlas layout (UV units, v up). One 256 px outfit atlas covers the body + the outfit add-on ----
ATLAS = {
    "torso": (0, .50, .625, 1.0), "neck": (.625, .90, 1, 1),
    "arm_L": (.625, .52, .8125, .90), "arm_R": (.8125, .52, 1, .90),
    "hand_L": (.625, .40, .8125, .52), "hand_R": (.8125, .40, 1, .52),
    "thumb_L": (.625, .36, .8125, .40), "thumb_R": (.8125, .36, 1, .40),
    "leg_L": (0, .04, .3125, .50), "leg_R": (.3125, .04, .625, .50),
    "shoe_L": (.625, .10, .8125, .36), "shoe_R": (.8125, .10, 1, .36),
    "addon": (.625, 0, 1, .10),
}
# z / x landmarks used by the painter (male reference space)
HEM_Z, WAIST_Z, SLEEVE_X, JEANS_HEM_Z = .955, .94, .305, .12

def lofts(sex="m"):
    L = []
    A = ATLAS
    # ---------------- Body: one mesh, clothes are painted on; silhouette steps at tee hem, sleeve hem, jeans hem, shoes
    L.append(dict(name="torso", piece="Body", axis="z", sides=10, group="trunk", chain="trunk",
                  rings=[(0, 0, .86, .172, .110, {}), (0, 0, .94, .166, .108, {}), (0, 0, .965, .178, .117, {}),
                         (0, -.004, 1.12, .158, .110, {}), (0, -.008, 1.25, .168, .118, {}), (0, 0, 1.36, .178, .118, {}),
                         (0, .004, 1.45, .178, .110, {}), (0, .006, 1.505, .150, .095, {}), (0, .008, 1.53, .072, .066, {})],
                  rect=A["torso"], cap0=True, cap1=False, cap0_c=(0, 0, .835)))
    L.append(dict(name="neck", piece="Body", axis="z", sides=8, group="neck", chain="trunk",
                  rings=[(0, 0, 1.50, .060, .055, {}), (0, 0, 1.64, .053, .051, {})], rect=A["neck"], cap0=False, cap1=False))
    arm = [(.14, .067, .076), (.19, .078, .076), (.30, .069, .067), (.31, .055, .053), (.46, .047, .047), (.755, .035, .033)]
    for sd in ("L", "R"): L.append(_arm("arm", "Body", sd, arm, A["arm_" + sd]))
    hand = [(.75, .031, .034), (.83, .025, .052), (.925, .016, .042)]
    for sd in ("L", "R"): L.append(_arm("hand", "Body", sd, hand, A["hand_" + sd], sides=6, cap1=True, group="hand"))
    for side, s in (("L", 1), ("R", -1)):
        L.append(dict(name="thumb_" + side, piece="Body", axis="d", side=side, sides=4, group="hand", chain="arm",
                      d=(0.6 * s, -0.8, 0.0),
                      rings=[(.785 * s, -.025, 1.447, .0143, .0165, {}), (.815 * s, -.068, 1.447, .0121, .0132, {})],
                      rect=A["thumb_" + side], cap0=False, cap1=True))
    lg = [(.11, .02, .07, .046, .050), (.110, .01, .12, .064, .066), (.105, -.005, .47, .060, .062), (.103, 0, .55, .064, .066),
          (.097, 0, .86, .080, .080), (.093, 0, .93, .070, .070)]
    for sd in ("L", "R"): L.append(_leg("leg", "Body", sd, lg, A["leg_" + sd]))
    for side, s in (("L", 1), ("R", -1)):
        L.append(dict(name="shoe_" + side, piece="Body", axis="y", side=side, sides=6, group="shoe", chain="foot",
                      rings=[(.11 * s, y, ry, rx, ry, {}) for (y, rx, ry) in
                             [(.085, .040, .048), (.02, .054, .055), (-.10, .054, .036), (-.165, .040, .028)]],
                      rect=A["shoe_" + side], cap0=True, cap1=True, cap0_c=(.11 * s, .095, .04), cap1_c=(.11 * s, -.178, .024)))
    # ---------------- Head (face painted) ----------------
    L.append(dict(name="head", piece="Head", axis="z", sides=10, group="head", chain="head",
                  rings=[(0, -.025, 1.565, .040, .045, {}), (0, -.012, 1.60, .068, .078, {}), (0, -.004, 1.645, .080, .095, {}),
                         (0, 0, 1.70, .086, .100, {}), (0, .003, 1.75, .085, .099, {}), (0, .005, 1.785, .068, .083, {})],
                  rect=(0, .12, 1, 1), cap0=True, cap1=True, cap0_c=(0, -.02, 1.556), cap1_c=(0, .005, 1.805)))
    # ---------------- Hair (silhouette pieces) ----------------
    if sex == "m":
        L.append(dict(name="hair_a", piece="Hair_A", axis="z", sides=10, group="head", chain="head",
                      rings=[(0, .004, 1.715, .092, .106, {"tilt": .045}), (0, .004, 1.765, .094, .108, {"tilt": .02}),
                             (0, .006, 1.795, .077, .091, {}), (0, .006, 1.815, .042, .052, {})],
                      rect=(0, 0, 1, 1), cap0=False, cap1=True, cap1_c=(0, .006, 1.823)))
        L.append(dict(name="hair_b", piece="Hair_B", axis="z", sides=10, group="head", chain="head",
                      rings=[(0, .012, 1.655, .098, .114, {"tilt": .075}), (0, .008, 1.73, .101, .116, {"tilt": .04}),
                             (0, .006, 1.785, .092, .106, {"tilt": .015}), (0, 0, 1.828, .060, .070, {"push": (-.035, .012)})],
                      rect=(0, 0, 1, 1), cap0=False, cap1=True, cap1_c=(0, -.01, 1.842)))
        # hoodie outfit add-on: hood bunched round the neck (uses the outfit atlas)
        L.append(dict(name="hood", piece="Hood", axis="z", sides=10, group="trunk", chain="trunk",
                      rings=[(0, .02, 1.47, .165, .135, {}), (0, .05, 1.53, .135, .125, {}), (0, .03, 1.56, .100, .100, {})],
                      rect=A["addon"], cap0=False, cap1=False))
    else:
        # A: chin-length bob (front opens above the brows, sides hang to the jaw)
        L.append(dict(name="hair_a", piece="Hair_A", axis="z", sides=10, group="head", chain="head",
                      rings=[(0, .006, 1.645, .103, .117, {"tilt": .07, "tilt2": .045}), (0, .006, 1.70, .100, .114, {"tilt": .05, "tilt2": .03}),
                             (0, .006, 1.765, .095, .109, {"tilt": .02}), (0, .006, 1.80, .075, .089, {}), (0, .006, 1.818, .040, .050, {})],
                      rect=(0, 0, 1, 1), cap0=False, cap1=True, cap1_c=(0, .006, 1.826)))
        # B: side-swept fringe over the brow, hair over ears/temples, high ponytail swinging out to the left
        L.append(dict(name="hair_b", piece="Hair_B", axis="z", sides=10, group="head", chain="head",
                      rings=[(0, .008, 1.655, .101, .116, {"tilt": .052, "tilt2": .03, "sweep": -.018}),
                             (0, .006, 1.725, .099, .113, {"tilt": .018}), (0, .006, 1.778, .093, .107, {}),
                             (0, .006, 1.806, .074, .088, {}), (0, .006, 1.822, .040, .050, {})],
                      rect=(0, .30, 1, 1), cap0=False, cap1=True, cap1_c=(0, .006, 1.83)))
        L.append(dict(name="ponytail", piece="Hair_B", axis="path", e1=(0.6, -0.8, 0), sides=6, group="head", chain="head",
                      rings=[(.01, .07, 1.80, .030, .030, {}), (.04, .135, 1.805, .044, .042, {}), (.085, .175, 1.74, .046, .044, {}),
                             (.12, .17, 1.64, .038, .036, {}), (.135, .15, 1.56, .020, .019, {})],
                      rect=(0, 0, 1, .28), cap0=False, cap1=True, cap1_c=(.137, .145, 1.535)))
        # jacket outfit add-on: stand-up collar (uses the outfit atlas)
        L.append(dict(name="collar", piece="Collar", axis="z", sides=10, group="trunk", chain="trunk",
                      rings=[(0, .01, 1.47, .175, .120, {}), (0, .02, 1.548, .100, .094, {})],
                      rect=A["addon"], cap0=False, cap1=False))
    return L

def ring_vs(lf):
    """v coordinate of every ring (by cumulative centre distance), plus cap v's, inside the loft rect."""
    u0, v0, u1, v1 = lf["rect"]
    pts = [r[:3] for r in lf["rings"]]
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5)
    pad0 = 0.06 if lf.get("cap0") else 0.01
    pad1 = 0.06 if lf.get("cap1") else 0.01
    span = (v1 - v0) * (1 - pad0 - pad1)
    vs = [v0 + (v1 - v0) * pad0 + span * (x / d[-1]) for x in d]
    return vs, v0 + 0.004, v1 - 0.004

OUTFITS = {"m": ("outfit_tee", "outfit_hoodie"), "f": ("outfit_tee", "outfit_jacket")}   # body atlases (256 px)
ADDON = {"m": "Hood", "f": "Collar"}         # add-on shown only with the alt outfit
PIECES = {"Body": 256, "Head": 128, "Hair_A": 128, "Hair_B": 128, "Hood": 256, "Collar": 256}
EARS = {"rect": (0.0, 0.0, 0.14, 0.10)}   # head texture area used by the ear quads

# ======================= Female reshaping (from the same male-space definitions) =======================
H_F = 0.93            # female height factor: 1.82 m -> ~1.69 m
HEAD_F = 0.92         # smaller head (about the neck/head joint)
NECKTOP = 1.582       # head joint after the tune-up

def _interp(x, keys):
    if x <= keys[0][0]: return keys[0][1]
    for (a, fa), (b, fb) in zip(keys, keys[1:]):
        if x <= b: return fa + (fb - fa) * (x - a) / (b - a)
    return keys[-1][1]

TRUNK_RX = [(0.84, 1.05), (0.95, 1.04), (1.10, 0.84), (1.25, 0.90), (1.36, 0.85), (1.52, 0.86)]
TRUNK_RY = [(0.84, 1.07), (0.95, 1.04), (1.10, 0.92), (1.25, 1.12), (1.36, 0.95), (1.52, 0.90)]
TRUNK_DY = [(1.14, 0.0), (1.25, -0.013), (1.34, 0.0)]

def fem_point(x, y, z, group):
    """map a male-space point to female space (used for ring centres, cap centres and bones)"""
    if group == "head":
        return (x * HEAD_F, y * HEAD_F, NECKTOP * H_F + (z - NECKTOP) * HEAD_F)
    if group in ("arm", "hand"):
        s = 1 if x >= 0 else -1
        return (s * (abs(x) * 0.93 - 0.008), y * 0.95, z * H_F)
    if group in ("leg", "shoe", "foot"):
        return (x * 0.95, y * (0.9 if group in ("shoe", "foot") else 1.0), z * (H_F if group != "shoe" else 0.92))
    return (x, y + (_interp(z, TRUNK_DY) if group == "trunk" else 0.0), z * H_F)


def fem_ring(lf, r, zref=None):
    x, y, z, rx, ry, ex = r
    zr = z if zref is None else zref
    g = lf["group"]
    cx, cy, cz = fem_point(x, y, z, g)
    if g == "trunk": rx, ry = rx * _interp(zr, TRUNK_RX) * 0.97, ry * _interp(zr, TRUNK_RY) * 0.97
    elif g == "neck": rx, ry = rx * 0.85, ry * 0.85
    elif g in ("arm", "hand"): rx, ry = rx * 0.85, ry * 0.85
    elif g == "leg": f = 0.97 if zr > 0.6 else 0.92; rx, ry = rx * f, ry * f
    elif g == "head":
        rx, ry = rx * HEAD_F, ry * HEAD_F
        if lf["name"] == "head" and zr < 1.65: rx *= 0.90          # softer, narrower jaw
        ex = dict(ex); ex = {k: (tuple(t * HEAD_F for t in v) if isinstance(v, tuple) else v * HEAD_F) for k, v in ex.items()}
    elif g == "shoe": rx, ry = rx * 0.9, ry * 0.92
    if lf["axis"] == "y": cz = ry       # keep the sole on the ground
    return (cx, cy, cz, rx, ry, ex)

def bones(sex="m"):
    if sex == "m": return BONES
    grp = lambda n: ("head" if n in ("Head", "HeadTop_End") else "arm" if any(k in n for k in ("Arm", "Hand")) else
                     "foot" if any(k in n for k in ("Foot", "Toe")) else "leg" if "Leg" in n else "spine")
    out = []
    for n, par, h, t, d in BONES:
        g = grp(n)
        if n == "Head": h2 = fem_point(*h, "spine")
        elif "Shoulder" in n: h2 = (h[0] * 0.9, h[1], h[2] * H_F)
        else: h2 = fem_point(*h, g)
        t2 = fem_point(*t, g if n != "Neck" else "spine")
        if n == "Neck": t2 = fem_point(*t, "spine")
        if "Shoulder" in n: t2 = fem_point(*t, "arm")
        out.append((n, par, h2, t2, d))
    return out


# ---------------- full mapping: male reference definition -> final (warp, then female reshaping) ----------------
def map_point(x, y, z, group, sex):
    p = warp_point(x, y, z, group)
    return p if sex == "m" else fem_point(*p, group)

def map_ring(lf, r, sex):
    x, y, z, rx, ry, ex = r; g = lf["group"]
    cx, cy, cz = warp_point(x, y, z, g)
    if g == "head":
        rx, ry = rx * HEAD_S, ry * HEAD_S
        ex = {k: (tuple(t * HEAD_S for t in v) if isinstance(v, tuple) else v * HEAD_S) for k, v in ex.items()}
    w = (cx, cy, cz, rx, ry, ex)
    return w if sex == "m" else fem_ring(lf, w, zref=z)
