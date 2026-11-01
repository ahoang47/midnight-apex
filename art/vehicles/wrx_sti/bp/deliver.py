"""Compose the 800-px deliverables from renders/clay_raw (run after build_wrx.py --render and bp/bpcompare.py).
  wrx_clay_orthos_800.jpg            clay orthos with the blueprint silhouette mapped in the blueprint's own frame
                                      (no bbox fitting) + IoU per view: gate / with blueprint scoop+spoiler / STI build
  wrx_clay_front34|rear34|high34_800.jpg
  wrx_clay_suspension_800.jpg        suspension + steering pose sheet
  wrx_clay_steer_clearance_800.jpg   front corner at full lock x full bump / droop (3/4, x-ray top, x-ray side)"""
import cv2, numpy as np, json, os
OUT = os.environ.get('WRX_OUT', '.'); PFX = os.environ.get('WRX_PFX', 'wrx_clay')   # lean: WRX_OUT=lean WRX_PFX=wrx_lean_clay
R = f'{OUT}/renders/clay_raw'; O = f'{OUT}/renders'
d = json.load(open('bp/curves.json')); S = d['scale_m_per_px']; Z = np.load('bp/bp_classes.npz')
iou = json.load(open(f'{OUT}/bp/iou_bpframe.json'))
def lab(i, t, org=(8, 22), s=0.55, col=(0, 0, 0)):
    (w, h), b = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, s, 1); x, y = org
    cv2.rectangle(i, (x - 2, y - h - 3), (x + w + 2, y + b), (255, 255, 255), -1); cv2.putText(i, t, org, cv2.FONT_HERSHEY_SIMPLEX, s, col, 1, cv2.LINE_AA)
def fitw(i, W): return cv2.resize(i, (W, int(round(i.shape[0] * W / i.shape[1]))), interpolation=cv2.INTER_AREA)
def save(img, name): cv2.imwrite(f'{O}/{name}', img, [cv2.IMWRITE_JPEG_QUALITY, 90]); print('wrote', name, img.shape)
# ---------------- orthos with the blueprint silhouette (blueprint frame -> render pixels, 5 mm/px, centre z .65)
def bp_in_render(view):
    M = Z[f'{view}_M']; X0, Y0 = int(Z[f'{view}_X0']), int(Z[f'{view}_Y0'])
    v_, u_ = np.mgrid[0:1000, 0:1000].astype(float)
    if view == 'side':
        x = (500 - u_) * 0.005; z = 0.65 + (500 - v_) * 0.005
        c = float(Z['side_CM']) - X0 - x / S; r = float(Z['side_ZF']) - Y0 - z / S
    elif view == 'top':
        x = (500 - u_) * 0.005; y = (v_ - 500) * 0.005
        c = float(Z['top_CM']) - X0 - x / S; r = float(Z['top_CR']) + y / S
    else:
        sg = 1 if view == 'front' else -1
        y = sg * (u_ - 500) * 0.005; z = 0.65 + (500 - v_) * 0.005
        c = float(Z[f'{view}_CC']) + sg * y / S; r = float(Z[f'{view}_ZF']) - Y0 - z / S
    ri, ci = np.round(r).astype(int), np.round(c).astype(int)
    ok = (ri >= 0) & (ri < M.shape[0]) & (ci >= 0) & (ci < M.shape[1])
    out = np.zeros((1000, 1000), np.uint8); out[ok] = M[ri[ok], ci[ok]]
    return out
def ortho(view):
    im = cv2.imread(f'{R}/clay_{view}.png'); bp = bp_in_render(view)
    e = cv2.morphologyEx(bp, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; im[e] = (255, 150, 0)
    ys, xs = np.nonzero(bp | (cv2.imread(f'{R}/sil_{view}.png', 0) > 127)); m = 20
    return im[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]
def tag(v): return f'{v}  IoU aero-masked (gate) {iou["gate"][v]:.3f} | mono STI full {iou["sti_mono"][v]:.3f} | no aero parts {iou["no_aero"][v]:.3f}  (min {iou["gate_thresholds"][v]:.2f})'
sd, tp, fr, rr = (ortho(k) for k in ('side', 'top', 'front', 'rear'))
sd = fitw(sd, 800); tp = fitw(tp, 800)
h = max(fr.shape[0], rr.shape[0]); pad = lambda i: cv2.copyMakeBorder(i, 0, h - i.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
fr2 = fitw(np.hstack([pad(fr), np.full((h, 30, 3), 255, np.uint8), pad(rr)]), 800)
lab(sd, tag('side'), s=0.42); lab(tp, tag('top'), s=0.42)
lab(fr2, f'front {iou["gate"]["front"]:.3f} / {iou["sti_mono"]["front"]:.3f} / {iou["no_aero"]["front"]:.3f}', s=0.42)
lab(fr2, f'rear {iou["gate"]["rear"]:.3f} / {iou["sti_mono"]["rear"]:.3f} / {iou["no_aero"]["rear"]:.3f}', (412, 22), s=0.42)
foot = np.full((44, 800, 3), 255, np.uint8)
cv2.putText(foot, 'blue line = blueprint silhouette in its own frame (wheel centres + ground), 5 mm/px, no fitting', (8, 17), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
cv2.putText(foot, f'gate = mono body + wheels with the aero region (scoop / wing / lip boxes) masked in blueprint AND clay: {"PASS" if iou["gate_pass"] else "FAIL"}', (8, 36), 0, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
save(np.vstack([sd, tp, fr2, foot]), f'{PFX}_orthos_800.jpg')
# ---------------- beauty 3/4s
for k in ('front34', 'rear34', 'high34'):
    im = cv2.imread(f'{R}/clay_{k}.png'); im = fitw(im, 800); lab(im, f'WRX STI (GDB 2001-02) grey clay ' + ('LEAN ' if OUT != '.' else 'pass 2 ') + f'- {k}  (mono body; STI scoop / wing / lip estimated)', s=0.45)
    save(im, f'{PFX}_{k}_800.jpg')
# ---------------- suspension + steering pose sheet
meta = json.load(open(f'{OUT}/bp/pose_meta.json'))
names = [('static', 'static ride height'), ('full_bump', 'full bump (heave)'), ('full_droop', 'full droop (heave)'),
         ('roll_right', 'roll: leans right'), ('roll_left', 'roll: leans left'), ('dive', 'brake dive'),
         ('squat', 'accel squat'), ('left_lock_roll', 'FULL LEFT LOCK + roll'), ('right_lock_roll', 'FULL RIGHT LOCK + roll')]
cells = []
for n, t in names:
    a = cv2.imread(f'{R}/pose_{n}_34.png'); b = cv2.imread(f'{R}/pose_{n}_front.png')
    b = b[130:560, 110:790]
    b = cv2.resize(b, (int(b.shape[1] * a.shape[0] / b.shape[0] * 0.42), int(a.shape[0] * 0.42)))
    c = a.copy(); c[c.shape[0] - b.shape[0]:, c.shape[1] - b.shape[1]:] = b
    cv2.rectangle(c, (c.shape[1] - b.shape[1], c.shape[0] - b.shape[0]), (c.shape[1] - 1, c.shape[0] - 1), (160, 160, 160), 1)
    tr = meta[n]['travel']; lab(c, t, (10, 30), 0.85)
    lab(c, 'travel vs body (m): ' + '  '.join(f'{k} {v:+.3f}' for k, v in tr.items()), (10, 62), 0.6)
    st = meta[n].get('steer', 0); ro = meta[n].get('roll', 0)
    if st or ro: lab(c, f'steer {st:+.0f} deg   roll {ro:+.1f} deg', (10, 92), 0.6)
    cells.append(cv2.copyMakeBorder(c, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255)))
grid = np.vstack([np.hstack(cells[i:i + 3]) for i in range(0, 9, 3)])
hdr = np.full((70, grid.shape[1], 3), 255, np.uint8)
cv2.putText(hdr, 'WRX STI clay - suspension + steering rig poses (wheels planted, body moves; inset = front ortho)', (14, 30), 0, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
cl = json.load(open(f'{OUT}/bp/clearance.json'))
cv2.putText(hdr, f'travel +{cl["spec"]["bump"]:.3f} / -{cl["spec"]["droop"]:.3f} m, lock +-{cl["spec"]["lock_deg"]:.0f} deg, roll {cl["spec"]["roll_deg"]:.0f} deg | clearance check: {"ALL CLEAR" if cl["all_clear"] else "INTERFERENCE"}', (14, 60), 0, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
save(fitw(np.vstack([hdr, grid]), 800), f'{PFX}_suspension_800.jpg')
# ---------------- steering clearance sheet
rows = []
for n, t in (('lockL_bump', 'left lock 30 + full bump'), ('lockR_bump', 'right lock 30 + full bump'), ('lockL_droop', 'left lock 30 + full droop'), ('lockR_droop', 'right lock 30 + full droop')):
    ims = [cv2.imread(f'{R}/clr_{n}_{k}.png') for k in ('34', 'top_xray', 'side_xray')]
    row = np.hstack([cv2.copyMakeBorder(i, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for i in ims])
    lab(row, f'FL corner: {t}', (12, 34), 1.0); lab(row, 'x-ray top, nose left (body 35 %)', (918, 34), 0.8); lab(row, 'x-ray side', (1824, 34), 0.8)
    rows.append(row)
sheet = np.vstack(rows)
tt = cl['tightest']
hdr = np.full((80, sheet.shape[1], 3), 255, np.uint8)
cv2.putText(hdr, 'Steering clearance: tyre vs body / wheel-well liners / underbody (BVH overlap, all corners, 9 lock x travel combos)', (14, 32), 0, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
tf = cl['tightest_front']
cv2.putText(hdr, f'result: {"NO INTERFERENCE" if cl["all_clear"] else "INTERFERENCE"} - tightest front tyre gap {tf["gap_m"]*1000:.0f} mm ({tf["corner"]}, {tf["pose"]}, vs {tf["against"]}); overall {tt["gap_m"]*1000:.0f} mm ({tt["corner"]})', (14, 66), 0, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
save(fitw(np.vstack([hdr, sheet]), 800), f'{PFX}_steer_clearance_800.jpg')

# ---------------- pass 2 surface checks: raking light (Cycles) + reflection-stripe zebra
def crop_bg(im, thr=12):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(int); bg = np.median(np.r_[g[0], g[-1], g[:, 0], g[:, -1]])
    ys, xs = np.nonzero(np.abs(g - bg) > thr); m = 16
    return im[max(ys.min() - m, 0):ys.max() + m, max(xs.min() - m, 0):xs.max() + m]
a = fitw(crop_bg(cv2.imread(f'{R}/clay_raking_side_fwd.png')), 800); b = fitw(crop_bg(cv2.imread(f'{R}/clay_raking_side_rear.png')), 800)
lab(a, 'raking light from ahead, 7 deg up, 20 deg outboard (Cycles) - door / flank ripple would show as vertical bands', s=0.42)
lab(b, 'raking light from behind', s=0.42)
save(np.vstack([a, np.full((6, 800, 3), 255, np.uint8), b]), f'{PFX}_raking_side_800.jpg')
z1 = fitw(crop_bg(cv2.imread(f'{R}/clay_zebra_side.png')), 800); z2 = crop_bg(cv2.imread(f'{R}/clay_zebra_top.png')); z3 = crop_bg(cv2.imread(f'{R}/clay_zebra_34.png'))
h = 300; z2 = cv2.resize(z2, (int(z2.shape[1] * h / z2.shape[0]), h)); z3 = cv2.resize(z3, (int(z3.shape[1] * h / z3.shape[0]), h))
row = np.hstack([z2, np.full((h, 8, 3), 255, np.uint8), z3]); row = fitw(row, 800)
lab(z1, 'zebra (horizontal reflection stripes, view-space matcap) - side: stripes should run unbroken nose to tail', s=0.42)
lab(row, 'top (nose left)', s=0.42); lab(row, '3/4', (row.shape[1] // 2 + 10, 22), s=0.42)
save(np.vstack([z1, np.full((6, 800, 3), 255, np.uint8), row]), f'{PFX}_zebra_800.jpg')
