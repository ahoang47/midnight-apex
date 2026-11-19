#!/usr/bin/env python3
"""Check that two 2.0 m-wide cars can pass in the through-aisle, and that
the P sign is clear of every drive path. Reads layout.json (LotArt metres)."""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
layout_path = os.path.join(HERE, 'layout.json')
if not os.path.exists(layout_path):
    sys.exit('missing layout.json — run ./run.sh first')
L = json.load(open(layout_path))

CAR_W = 2.0
aisle0, aisle1 = L['aisle_x_m']
aisle_w = aisle1 - aisle0
# Gordon's two through-lot lanes (display.json turnout placeholders), from the road edge.
NEAR, DEEP = 2.4, 4.9
near = (NEAR - CAR_W / 2, NEAR + CAR_W / 2)
deep = (DEEP - CAR_W / 2, DEEP + CAR_W / 2)

def overlaps(a, b):
    return not (a[1] <= b[0] or b[1] <= a[0])

ok = True
def check(name, cond, detail):
    global ok
    status = 'PASS' if cond else 'FAIL'
    if not cond:
        ok = False
    print(f'{status}  {name}: {detail}')

check('aisle width', aisle_w + 1e-9 >= 6.0,
      f'aisle x {aisle0:.6f} to {aisle1:.6f}  ({aisle_w:.6f} m, need ≥ 6.0)')
check('near car in aisle', near[0] >= aisle0 - 1e-9 and near[1] <= aisle1 + 1e-9,
      f'near lane x={NEAR} box [{near[0]:.2f}, {near[1]:.2f}]')
check('deep car in aisle', deep[0] >= aisle0 - 1e-9 and deep[1] <= aisle1 + 1e-9,
      f'deep lane x={DEEP} box [{deep[0]:.2f}, {deep[1]:.2f}]')
gap = deep[0] - near[1]
check('cars do not overlap', not overlaps(near, deep),
      f'gap between boxes = {gap:.3f} m')

# Sign on the island, out of the taper mouth and out of the aisle / lanes / stalls.
sign = L.get('sign_m', {})
sx, sz = float(sign.get('x', 0)), float(sign.get('z', 0))
pw = float(sign.get('plate_w_m', 0.52))
sign_x = (sx - pw / 2, sx + pw / 2)
island = L.get('island_d_m', [0.1, 0.7])
taper = float(L.get('taper_m', 14.0))
check('sign on the island (x)', sign_x[0] >= island[0] - 1e-9 and sign_x[1] <= island[1] + 1e-9,
      f'sign x={sx:.3f} plate [{sign_x[0]:.3f}, {sign_x[1]:.3f}], island {island}')
check('sign out of the taper mouth (z)', sz >= taper,
      f'sign z={sz:.3f}, taper ends at {taper:.3f}')
check('sign clear of the aisle', not overlaps(sign_x, (aisle0, aisle1)),
      f'sign x vs aisle [{aisle0:.3f}, {aisle1:.3f}]')
check('sign clear of both car boxes', not overlaps(sign_x, near) and not overlaps(sign_x, deep),
      'island post vs 2.0 m near/deep boxes')

print(f"pocket_w_m={L['pocket_w_m']:.12f}  stalls {L['n_stalls_per_row']} / row at {L['stall_angle_deg']}°")
sys.exit(0 if ok else 1)
