"""Look up blueprint class masks (bp/bp_classes.npz) at car-frame points, per view.  Used to classify faces:
glass (GL), lamp lenses (HL / LL / R), dark trim (K: grille, intakes, black pillars / sash, opened so 1-px lines drop)."""
import os, numpy as np
from wrx_bp import S, HERE
Z = np.load(os.path.join(HERE, 'bp', 'bp_classes.npz'))
def px(view, p):
    x, y, z = p
    X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    if view == 'side': return (float(Z['side_ZF']) - Y0) - z / S, (float(Z['side_CM']) - X0) - x / S
    if view == 'top': return float(Z['top_CR']) + y / S, (float(Z['top_CM']) - X0) - x / S
    sg = 1 if view == 'front' else -1
    return (float(Z[f'{view}_ZF']) - Y0) - z / S, float(Z[f'{view}_CC']) + sg * y / S
def hit(view, key, p):
    k = f'{view}_{key}'
    if k not in Z.files: return False
    m = Z[k]; r, c = px(view, p); r, c = int(round(r)), int(round(c))
    return 0 <= r < m.shape[0] and 0 <= c < m.shape[1] and bool(m[r, c])
def view_of(n):
    """the blueprint view a face with car-frame normal n is drawn in."""
    nx, ny, nz = n; a = np.abs([nx, ny, nz])
    if a[1] >= a[0] and a[1] >= a[2]: return 'side'
    if a[2] >= a[0]: return 'top'
    return 'front' if nx > 0 else 'rear'
