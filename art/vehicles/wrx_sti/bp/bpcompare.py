"""IoU gate: blueprint silhouettes vs clay in the blueprint's own frame (no bbox fitting).
Side/top: x from the blueprint wheel centres, z from the tyre bottoms; front/rear: paint centre line + ground.
Clay = bp/tris_carframe.npy (rest pose, per-part names kept from before the mono join), rasterised at 4x blueprint resolution.
  sets: see EXCL below (sti_mono, sti_aero_masked = gate, no_aero, wrx_base).
Gate: side >= .95, top >= .95, front >= .92, rear >= .92 on 'sti_aero_masked'.  Writes bp/iou_bpframe.json and
renders/clay_raw/bpiou_{set}_{view}.png (grey both, orange blueprint only, red clay only)."""
import numpy as np, cv2, json, os
UP = 4
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']
OUT = os.environ.get('WRX_OUT', '.')          # lean build: WRX_OUT=lean (soup + results under lean/)
T = np.load(f'{OUT}/bp/tris_carframe.npy').reshape(-1, 3, 3); TO = np.load(f'{OUT}/bp/tris_object.npy')
Z = np.load('bp/bp_classes.npz')
# pass 2: the STI build is ONE mono body mesh; the triangle soup keeps the pre-join part names so the sets still work.
#   sti_mono          the car as exported (mono body incl. STI scoop / wing / lip + wheels), full blueprint mask
#   sti_aero_masked   same triangles, but the aero REGION (scoop, rear spoiler / wing, front lip boxes) is masked out of
#                     BOTH the blueprint and the clay  -> this is the gate set
#   no_aero           pass-1 'gate' set (aero parts dropped, blueprint unmasked), kept for continuity
#   wrx_base          the blueprint's own scoop + lip spoiler instead of the STI parts
EXCL = {'sti_mono': ('WRX_Scoop', 'WRX_LipSpoiler'),
        'sti_aero_masked': ('WRX_Scoop', 'WRX_LipSpoiler'),
        'no_aero': ('WRX_Scoop', 'WRX_LipSpoiler', 'STI_Scoop', 'STI_Wing', 'STI_FrontLip'),
        'wrx_base': ('STI_Scoop', 'STI_Wing', 'STI_FrontLip')}
AERO = [((1.15, 1.56), (-0.37, 0.37), (0.90, 1.07)),      # bonnet scoop (WRX and STI)
        ((-2.17, -1.66), (-0.76, 0.76), (1.03, 1.31)),    # boot lip spoiler / STI wing
        ((1.95, 2.26), (-0.86, 0.86), (0.14, 0.27))]      # STI front lip
GATE = dict(side=.95, top=.95, front=.92, rear=.92)
def bpmask(view):
    M = Z[f'{view}_M'].astype(np.uint8)
    return cv2.resize(M, (M.shape[1] * UP, M.shape[0] * UP), interpolation=cv2.INTER_NEAREST) > 0
def raster(view, shape, Tt):
    X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    if view == 'side':
        u = (float(Z['side_CM']) - X0 - Tt[..., 0] / S) * UP; v = (float(Z['side_ZF']) - Y0 - Tt[..., 2] / S) * UP
    elif view == 'top':
        u = (float(Z['top_CM']) - X0 - Tt[..., 0] / S) * UP; v = (float(Z['top_CR']) + Tt[..., 1] / S) * UP
    else:
        sg = 1 if view == 'front' else -1
        u = (float(Z[f'{view}_CC']) + sg * Tt[..., 1] / S) * UP; v = (float(Z[f'{view}_ZF']) - Y0 - Tt[..., 2] / S) * UP
    img = np.zeros(shape, np.uint8)
    for tri in np.stack([u, v], -1): cv2.fillPoly(img, [np.round(tri * 8).astype(np.int32)], 1, shift=3)
    return img > 0
os.makedirs(f'{OUT}/renders/clay_raw', exist_ok=True)
if not np.isin(TO, ('WRX_Scoop', 'WRX_LipSpoiler')).any(): EXCL.pop('wrx_base')   # lean build has no base-WRX parts
def aero_mask(view, shape):
    m = np.zeros(shape, bool)
    for bx, by, bz in AERO:
        P = np.array([[[x, y, z] for x in bx for y in by for z in bz]], float)
        img = raster(view, shape, np.stack([P[0][[0, 1, 3]], P[0][[0, 2, 3]], P[0][[4, 5, 7]], P[0][[4, 6, 7]], P[0][[0, 4, 5]], P[0][[0, 1, 5]],
                                            P[0][[2, 6, 7]], P[0][[2, 3, 7]], P[0][[0, 2, 6]], P[0][[0, 4, 6]], P[0][[1, 3, 7]], P[0][[1, 5, 7]]]))
        m |= img
    return m
res = {}
for sname, ex in EXCL.items():
    Tt = T[~np.isin(TO, ex)]; res[sname] = {}
    for view in ('side', 'top', 'front', 'rear'):
        Bm = bpmask(view); C = raster(view, Bm.shape, Tt)
        if sname == 'sti_aero_masked': am = aero_mask(view, Bm.shape); Bm = Bm & ~am; C = C & ~am
        res[sname][view] = round(float((Bm & C).sum() / (Bm | C).sum()), 4)
        ov = np.full(Bm.shape + (3,), 255, np.uint8); ov[Bm & C] = (190, 190, 190); ov[Bm & ~C] = (0, 140, 255); ov[C & ~Bm] = (0, 0, 230)
        cv2.imwrite(f'{OUT}/renders/clay_raw/bpiou_{sname}_{view}.png', ov)
res['gate'] = res['sti_aero_masked']; res['gate_pass'] = all(res['gate'][v] >= g for v, g in GATE.items()); res['gate_thresholds'] = GATE
json.dump(res, open(f'{OUT}/bp/iou_bpframe.json', 'w'), indent=1); print(json.dumps(res))
