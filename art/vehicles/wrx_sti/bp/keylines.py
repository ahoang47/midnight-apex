"""Key-line table: clay (parts/wrx_geo.py + bp/tris_carframe.npy) vs the traced blueprint (bp/curves.json), line by
line, plus what is estimated.  Run after build_wrx.py + bp/bpcompare.py.  Writes keyline_table.md."""
import sys, json, numpy as np
sys.path.insert(0, 'parts')
import wrx_bp as B, wrx_geo as G
T = np.load('bp/tris_carframe.npy').reshape(-1, 3, 3); TO = np.load('bp/tris_object.npy')
body = T[np.isin(TO, ('WRX_Body', 'WRX_Cabin'))].reshape(-1, 3)
iou = json.load(open('bp/iou_bpframe.json')); cl = json.load(open('bp/clearance.json'))
D = B.D; rows = []
def add(g, name, model, bp, note=''): rows.append((g, name, model, bp, note))
f = lambda v: '-' if v is None else (f'{v:.3f}' if isinstance(v, (float, np.floating)) else str(v))
# overall
add('overall', 'length (m)', float(body[:, 0].max() - body[:, 0].min()), 4.405, 'sheet L 4405 = scale reference (5.721 mm/px over 770 px)')
add('overall', 'wheelbase (m)', float(G.WB), float(D['wheelbase_px_m']), f'traced from the contact patches; sheet says 2.525 (drawing is {100*(1-D["wheelbase_px_m"]/2.525):.1f} % short) - traced value kept for the IoU gate')
add('overall', 'body width (m)', float(2 * np.abs(body[body[:, 2] < 0.9][:, 1]).max()), 1.730, 'front/rear views .87 half-width; top view reads .90 at the flares (clamped to .872)')
add('overall', 'roof height (m)', float(body[:, 2].max()), float(np.array(D['side_sil_top'])[:, 1].max()), 'side silhouette 1.465-1.47 (+ a 2.5 cm roof nub at x -.15..-.3 not modelled); sheet H 1440 (drawing ~2 % tall)')
add('overall', 'front overhang (m)', float(body[:, 0].max() - G.AXF), float(B.X_NOSE - B.AXF), '')
add('overall', 'rear overhang (m)', float(G.AXR - body[:, 0].min()), float(B.AXR - B.X_TAIL), '')
add('overall', 'track F / R (m)', f'{G.TRACK_F:.3f} / {G.TRACK_R:.3f}', '1.485-1.490 / 1.475-1.480', 'sheet values')
# side lines
for x in (1.8, 1.4, 1.0):
    add('hood / fender', f'hood line z at x {x}', G.ZTB(x), float(B.BLUE_TOP(x)) if x < 1.5 else float(B.SIL_TOP(x)), 'side paint top (scoop + mirror are dark so excluded)')
for x in (0.3, 0.0, -0.5, -0.9):
    gb, gt = G.dlo(x); add('greenhouse', f'DLO bottom / top at x {x}', f'{gb:.3f} / {gt:.3f}', '/'.join(f'{v:.3f}' for v in sorted([c[2] for c in D['side_glass_cols'] if abs(c[0] - x) < .006][:1] + [c[1] for c in D['side_glass_cols'] if abs(c[0] - x) < .006][:1])), 'side glass columns, smoothed; pillars interpolated')
for k, r in B.GLASS.items(): add('greenhouse', f'side glass region {k} x', f'{r["x"][0]:.3f}..{r["x"][1]:.3f}', 'same', 'classification boundary (cabin faces)')
add('greenhouse', 'windshield base x (centre)', G.XWS, 0.924, 'top view glass')
add('greenhouse', 'rear glass base x / z', f'{G.XRG} / {G.ZTB(G.XRG):.3f}', '-1.565 / 1.06', 'top view glass end / side view deck')
add('greenhouse', 'roof z at x -0.5', G.GT(-0.5), float(B.SIL_TOP(-0.5)), '')
add('body', 'sill z at x 0', G.ZB(0.0), float(B.SIL_BOT(0.0)), '')
for nm, A in (('front', B.ARCH_F), ('rear', B.ARCH_R)):
    add('body', f'{nm} arch circle (xc, zc, r)', f'{A["xc"]:.3f}, {A["zc"]:.3f}, {A["r"]:.3f}', 'fit', f'least-squares fit to the arch paint edge x {A["x0"]:.2f}..{A["x1"]:.2f}')
add('body', 'deck z at x -1.85 (under spoiler)', G.ZTB(-1.85), '~1.06', 'side: lip spoiler removed, deck read under it (ESTIMATE where the spoiler hides it)')
# lamps
for r in D['front_light_regions']: add('lamps', 'front lens (y, z)', f'{r["y"][0]:.2f}..{r["y"][1]:.2f}, {r["z"][0]:.2f}..{r["z"][1]:.2f}', 'decal = blueprint hull', 'round headlamps z .6-.8, fogs z .37-.50')
# parts
add('parts', 'WRX scoop (blueprint)', 'x 1.25-1.48, y +-.30, h .062', 'side x 1.23-1.48 top .98, top view y +-.30', 'base-WRX part, hidden in the STI build')
add('parts', 'WRX lip spoiler (blueprint)', 'x -1.70..-2.075, top 1.135, span +-.66', 'side tip (-2.065, 1.135)', 'span ESTIMATED from the rear view band')
add('parts', 'STI scoop', 'x 1.19-1.515, y +-.34, h .088', '-', 'ESTIMATED (GDB scoop larger than the GD WRX one; not on the sheet)')
add('parts', 'STI wing', 'chord x -1.87..-2.145, top 1.258, span +-.70, uprights y +-.52', '-', 'ESTIMATED (tall pedestal wing, proportions only)')
add('parts', 'STI front lip', '3 cm proud of the bumper bottom, z ZB-.022..+.012', '-', 'ESTIMATED')
add('wheels', 'tyre', f'OD {G.TIRE_OD} / W {G.TIRE_W} / rim {G.RIM_D}', 'blueprint wheel ~.63 OD', 'STI 225/45R17 (WRX 205/55R16 would be OD .632)')
add('rig', 'travel bump / droop', f'+{cl["spec"]["bump"]} / -{cl["spec"]["droop"]}', '-', 'ESTIMATED: front arch lip gap .095 over the tyre')
add('rig', 'steering lock', f'+-{cl["spec"]["lock_deg"]:.0f} deg', '-', 'brief value (GD real ~33/28 deg in/out, ~10.6 m kerb circle)')
md = ['# WRX STI (GD, 2001-02) - key-line table (clay vs blueprint)', '',
      'Blueprint: the-blueprints.com "Subaru Impreza WRX (2001)", 1280x906 px, 1:25; S = 4.405 m / 770 px = 5.721 mm/px.',
      'All "blueprint" values are traced lines (bp/curves.json). Nothing is from photos. ESTIMATED marks every invented number.', '',
      f'IoU (blueprint frame): aero region masked (gate) {iou["sti_aero_masked"]} - mono STI as exported, unmasked {iou["sti_mono"]} - no aero parts {iou["no_aero"]} - base WRX scoop+spoiler {iou["wrx_base"]}. Gate {"PASS" if iou["gate_pass"] else "FAIL"}.', '',
      f'Steering/suspension clearance: {"all clear" if cl["all_clear"] else "INTERFERENCE"}; tightest {cl["tightest"]}', '',
      '| group | line | clay | blueprint | note |', '|---|---|---|---|---|']
md += [f'| {g} | {n} | {f(m)} | {f(b)} | {no} |' for g, n, m, b, no in rows]
open('keyline_table.md', 'w').write('\n'.join(md) + '\n'); print('\n'.join(md[:8])); print(len(rows), 'rows')
