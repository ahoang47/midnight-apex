"""SVG <-> car-frame mapping for the Dimensions.com drawing (same frames as extract.py; read back from curves.json so
every script agrees).  Car frame: x fwd (0 = mid-wheelbase), y left, z up (0 = ground), metres."""
import xml.etree.ElementTree as ET, json, os, numpy as np
from svgpathtools import parse_path
HERE = os.path.dirname(os.path.abspath(__file__))
NS = '{http://www.w3.org/2000/svg}'; ROOT = ET.parse(os.path.join(HERE, 'gr_dimensions.svg')).getroot()
D = json.load(open(os.path.join(HERE, 'curves.json'))); S = D['S_m_per_unit']
def layer(i): return [g for g in ROOT.iter(NS + 'g') if g.get('id') == i][0]
def path_pts(d, k=4):
    p = parse_path(d); pts = []
    for seg in p: pts += [seg.point(t) for t in np.linspace(0, 1, max(2, int(seg.length() * k)), endpoint=False)]
    if len(p): pts.append(p[-1].end)
    return np.array([(c.real, c.imag) for c in pts])
_polys = [path_pts(e.get('d')) for e in layer('_x32_D_x24_AG-OUTLINE').iter(NS + 'path')]
def which(P):
    x0, y0 = np.asarray(P).min(0); return ('side' if y0 < 300 else 'top') if x0 < 600 else ('front' if y0 < 300 else 'rear')
SV = {which(P): P for P in _polys}; GZ = {'side': 259.76, 'front': 259.76, 'rear': 541.198}
UM = SV['side'][:, 0].min() - np.array(D['sil']['side'])[:, 0].min() / S
VC = 0.5 * (SV['top'][:, 1].min() + SV['top'][:, 1].max()); UC = {k: 0.5 * (SV[k][:, 0].min() + SV[k][:, 0].max()) for k in ('front', 'rear')}
def to_car(view, P):
    P = np.asarray(P, float); u, v = P[:, 0], P[:, 1]
    if view == 'side': return np.c_[(u - UM) * S, (GZ['side'] - v) * S]
    if view == 'top': return np.c_[(u - UM) * S, (VC - v) * S]
    sg = 1 if view == 'front' else -1; return np.c_[sg * (u - UC[view]) * S, (GZ[view] - v) * S]
def to_svg(view, A, B):
    if view == 'side': return A / S + UM, GZ['side'] - B / S
    if view == 'top': return A / S + UM, VC - B / S
    sg = 1 if view == 'front' else -1; return UC[view] + sg * A / S, GZ[view] - B / S
