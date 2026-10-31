"""Pass 4: blueprint curves (bp/curves.json, traced by bp/extract.py) as smooth functions of x, plus the
feature outlines read off the zoomed blueprint crops (renders/brz_bp_line_classification_p4_800.jpg).
Everything here is blueprint geometry; nothing comes from the photos."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(HERE, 'bp', 'curves.json')))
STROKE = 0.004            # half the drawn outline stroke: the silhouette edge sits mid-stroke

def _med(a, k=3):
    a = np.asarray(a, float); out = a.copy(); h = k // 2
    for i in range(len(a)): out[i] = np.median(a[max(0, i - h):i + h + 1])
    return out

def _fn(pts, k=3, skip=None):
    p = np.array(pts, float); p = p[np.argsort(p[:, 0])]
    if skip is not None:
        m = ~((p[:, 0] > skip[0]) & (p[:, 0] < skip[1])); p = p[m]
    return p[:, 0], _med(p[:, 1], k)

_Wx, _Wy = _fn(D['top_halfwidth'], 3, skip=(0.08, 0.42))      # mirrors removed from the plan outline
_Tx, _Ty = _fn(D['side_sil_top'], 3, skip=(-0.88, -0.68))     # shark fin removed from the roof line
_Bx, _By = _fn(D['side_sil_bot'], 3)

def W(x):  return np.interp(x, _Wx, _Wy) - STROKE                     # plan half-width (top view)
def ZT(x): return np.interp(x, _Tx, _Ty) - STROKE                     # side silhouette top
def ZB(x): return np.interp(x, _Bx, _By) + STROKE                     # side silhouette bottom

# ---- greenhouse lines (side + top + front/rear views), car frame x fwd, y left, z up
# centre-line roof / glass profile = side silhouette (fin removed)
ENV = np.array([(0.80,.900),(0.75,.920),(0.70,.956),(0.60,1.026),(0.50,1.086),(0.40,1.142),(0.30,1.188),(0.20,1.230),
    (0.10,1.264),(0.00,1.282),(-0.15,1.294),(-0.30,1.297),(-0.45,1.295),(-0.60,1.284),(-0.75,1.266),(-0.90,1.241),
    (-1.00,1.214),(-1.10,1.187),(-1.20,1.159),(-1.30,1.130),(-1.40,1.100),(-1.50,1.063),(-1.58,1.036),(-1.70,1.005),
    (-1.85,0.995),(-2.20,0.990)])

# ---- feature outlines, one polygon per view in that view's own 2D frame:
#  side (x, z)  |  rear (y, z) (left half, mirrored)  |  front (y, z)  |  top (x, y)
FEAT = {
 'lamp': {
   'side':  [(-1.62,.885),(-1.90,.893),(-1.975,.80),(-1.95,.765),(-1.64,.855)],          # swept wedge, narrow to the front
   'rear':  [(.395,.815),(.45,.893),(.76,.900),(.775,.84),(.72,.80),(.42,.775)],          # inner end droops
   'front': [(.44,.635),(.47,.69),(.76,.755),(.775,.705),(.72,.645),(.50,.615)],          # headlight eye
   'side_f':[(2.02,.62),(1.97,.665),(1.62,.785),(1.60,.735),(1.80,.672),(2.00,.605)],     # headlight in side view
   'top':   [(-1.78,.665),(-1.95,.47),(-2.0,.44),(-1.86,.68)],                            # taillight top wrap
   'top_f': [(2.02,.40),(1.92,.62),(1.66,.80),(1.62,.76),(1.88,.56),(2.0,.38)],            # headlight in plan
 },
 'trim': {   # black: grille, corner intakes, diffuser, fender vent, plate recess (dark in the drawing)
   'front': [[(0,.215),(.60,.215),(.62,.30),(.52,.46),(0,.46)],                            # wide hex grille
             [(.69,.24),(.80,.25),(.80,.47),(.72,.47)]],                                   # corner intake slots
   'side':  [[(1.86,.27),(1.95,.27),(1.97,.47),(1.89,.47)],                                # intake seen from the side
             [(.84,.30),(.90,.30),(.97,.60),(.92,.60)],                                    # fender vent
             [(-2.0,.20),(-2.20,.20),(-2.20,.46),(-2.05,.46)]],                            # diffuser corner
   'rear':  [[(0,.20),(.66,.20),(.68,.44),(0,.44)]],                                       # diffuser
 },
 'plate': {'rear': [[(0,.42),(.12,.42),(.12,.56),(0,.56)]], 'front': [[(0,.39),(.16,.39),(.16,.47),(0,.47)]]},
}

def inside(poly, p):
    poly = np.asarray(poly, float); x, y = p; n = len(poly); c = False
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
