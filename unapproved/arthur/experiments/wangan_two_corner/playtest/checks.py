#!/usr/bin/env python3
"""Wangan two-corner playtest checks (Arthur). Reads the 30 fps frame dumps from ./run.sh playtest ($OUT/gif_on, gif_off,
gif_ink + gif_on/frames.json: phase / corner / rig / mirror per frame) and writes playtest/checks.json + evidence PNGs.
  1 HUD untouched   : bright HUD text pixels identical cel on vs off (same deterministic game frame)
  2 mirror ink      : ink coverage inside the rear-view inset (the touge bug was the inset flooding with ink)
  3 decals inked?   : ink on chevron pixels and on painted lane-line pixels (both must be ~0: decals/paint are never inked)
  4 road specks     : isolated-pixel specks + frame-to-frame change on the near road while it scrolls, on vs off
  5 posterisation   : hard steps in the 4x4-box-filtered luma (the Bayer pattern removed) on the road, sky and bay"""
import os, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.environ.get('OUT', '/tmp/wtc')
G = {k: f'{OUT}/gif_{k}' for k in ('on', 'off', 'ink')}
LOG = json.load(open(f"{G['on']}/frames.json"))
def rgb(k, f): return np.asarray(Image.open(f"{G[k]}/f{f:05d}.png").convert('RGB')).astype(np.float32)
def luma(a): return a @ np.array([0.299, 0.587, 0.114], np.float32)
def box4(l):
    h, w = (l.shape[0] // 4) * 4, (l.shape[1] // 4) * 4
    return l[:h, :w].reshape(h // 4, 4, w // 4, 4).mean((1, 3))
def pick(pred, n=None, step=1):
    fs = [e['n'] for e in LOG if pred(e)][::step]
    return fs if n is None else fs[:n]
res = {}
straight0 = pick(lambda e: e['phase'] == 'SELECT' and e['ci'] == 0 and e['stop'] == 0)[30:150]
straight1 = pick(lambda e: e['phase'] == 'SELECT' and e['ci'] == 1 and e['stop'] == 0)[30:150]
play = pick(lambda e: e['phase'] == 'TIMING' and e['rig'] in ('BCL', 'BCR'))
mirror = pick(lambda e: e['mirror'])
chev = pick(lambda e: e['chev'] and e['stop'] == 0 and not e['mirror'] is False)
# 1 HUD
boxes = {'line_lock': (30, 22, 380, 115), 'plan_panel': (850, 735, 1272, 955), 'plate': (950, 20, 1258, 192), 'gap_bar': (440, 196, 840, 272)}
hud = {}
for nm, (x0, y0, x1, y1) in boxes.items():
    same = tot = 0
    for f in straight0[::20]:
        a, b = rgb('on', f)[y0:y1, x0:x1], rgb('off', f)[y0:y1, x0:x1]
        m = luma(a) > 200; tot += m.sum(); same += (m & (np.abs(a - b).max(2) == 0)).sum()
    hud[nm] = {'bright_px': int(tot), 'identical_pct': round(100 * same / max(tot, 1), 2)}
res['hud_bright_text_identical_on_vs_off'] = hud
# 2 mirror ink (inner inset; frame border excluded)
MX = (452, 36, 828, 156)
mi = [rgb('ink', f)[MX[1]:MX[3], MX[0]:MX[2], 0] > 127 for f in mirror[::3]]
main = [rgb('ink', f)[300:640, 0:1280, 0] > 127 for f in mirror[::3]]
res['mirror_ink'] = {'frames': len(mi), 'inset_ink_pct_mean': round(100 * float(np.mean([m.mean() for m in mi])), 2),
    'inset_ink_pct_max': round(100 * float(np.max([m.mean() for m in mi])), 2), 'main_view_ink_pct_mean': round(100 * float(np.mean([m.mean() for m in main])), 2)}
# 3 decals: chevrons (saturated green / yellow / red on the road) and painted lane lines (pale, unsaturated, on the road)
cs = {'chevron_px': 0, 'chevron_inked': 0, 'lane_px': 0, 'lane_inked': 0}
for f in chev[::6]:
    a = rgb('on', f); k = rgb('ink', f)[..., 0] > 127
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1)
    reg = np.zeros(k.shape, bool); reg[420:730, 0:1280] = True; reg[580:960, 840:1280] = False   # road ahead, not the plan panel
    cm = reg & (sat > 0.55) & (mx > 90) & ~((a[..., 0] > 150) & (a[..., 1] < 90))   # chevrons; car tail lamps (deep red) excluded
    lm = reg & (sat < 0.18) & (luma(a) > 120)
    cs['chevron_px'] += int(cm.sum()); cs['chevron_inked'] += int((cm & k).sum()); cs['lane_px'] += int(lm.sum()); cs['lane_inked'] += int((lm & k).sum())
cs['chevron_inked_pct'] = round(100 * cs['chevron_inked'] / max(cs['chevron_px'], 1), 2); cs['lane_inked_pct'] = round(100 * cs['lane_inked'] / max(cs['lane_px'], 1), 2)
res['decals_inked'] = cs
# 4 road specks + crawl, near road while scrolling (left of the car, clear of the panels)
RD = (40, 700, 520, 960)
def specks(a):
    l = luma(a[RD[1]:RD[3], RD[0]:RD[2]]); b = box4(l); up = np.kron(b, np.ones((4, 4)))
    return float((np.abs(l[:up.shape[0], :up.shape[1]] - up) > 22).mean())
sp = {}
for k in ('off', 'on'):
    s = [specks(rgb(k, f)) for f in straight0[::4]]
    dl = [np.abs(luma(rgb(k, f)[RD[1]:RD[3], RD[0]:RD[2]]) - luma(rgb(k, f + 1)[RD[1]:RD[3], RD[0]:RD[2]])).mean() for f in straight0[::8]]
    sp[k] = {'speck_pct': round(100 * float(np.mean(s)), 3), 'frame_diff_mean': round(float(np.mean(dl)), 2)}
res['near_road_while_scrolling'] = sp
# 5 posterisation: steps > 4/255 between neighbouring 4x4 cells along columns, per 100 cells, on big smooth regions
REG = {'road_ahead_straight': (straight0, (60, 480, 520, 700)), 'sky_band_straight': (straight0, (0, 300, 430, 360)),
       'bay_corner_playback': (play, (0, 620, 400, 960))}
po = {}
for nm, (fs, (x0, y0, x1, y1)) in REG.items():
    st = {}
    for k in ('off', 'on'):
        v = []
        for f in fs[::15]:
            b = box4(luma(rgb(k, f)[y0:y1, x0:x1]))
            v.append(float((np.abs(np.diff(b, axis=0)) > 4.0).mean() * 100))
        st[k] = round(float(np.mean(v)), 2)
    po[nm] = st
res['hard_steps_per_100_cells'] = po
res['frames_used'] = {'straight_c1': len(straight0), 'straight_c2': len(straight1), 'playback': len(play), 'mirror': len(mirror), 'chevron': len(chev)}
json.dump(res, open(f'{H}/checks.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
# evidence: mirror x3 (cel off / cel on / ink mask), from the first straight
f = straight0[60]; bx = (448, 32, 832, 160); z = 3
im = Image.new('RGB', ((bx[2] - bx[0]) * z, (bx[3] - bx[1]) * z * 3 + 30), (11, 23, 43)); d = ImageDraw.Draw(im)
for j, k in enumerate(('off', 'on', 'ink')):
    im.paste(Image.open(f"{G[k]}/f{f:05d}.png").convert('RGB').crop(bx).resize(((bx[2] - bx[0]) * z, (bx[3] - bx[1]) * z), Image.NEAREST), (0, 30 + j * (bx[3] - bx[1]) * z))
d.text((8, 8), f'REAR VIEW x3, frame {f}: cel off / Cel A soft / ink mask (white = ink)', fill=(220, 228, 240))
im.save(f'{H}/mirror_check.png')
a, b = rgb('on', f), rgb('off', f); same = (a == b).all(2)
vis = np.zeros_like(a); vis[..., 1] = same * 140; vis[..., 0] = (~same) * 255
Image.fromarray(vis.astype(np.uint8)).save(f'{H}/hud_check.png')
