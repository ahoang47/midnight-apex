#!/usr/bin/env python3
"""Numerical frame comparison + GIFs for the selection scroll, corner camera and overtake snap sequences (display-only checks).
usage: frame_compare.py <shots_root> [tag]   e.g. out/shots3 (tag 640)
For each engine dir it reads frames_<look>.json (per-frame metadata written by the build) and the PNGs."""
import json, sys, os, glob, re
import numpy as np
from PIL import Image
root = sys.argv[1]; look = sys.argv[2] if len(sys.argv) > 2 else '640'
# road strips either side of the player car during SELECT (clear of the HUD boxes)
ROAD = [(40, 235, 220, 320), (420, 235, 600, 320)]  # 640x480 base pixels (Godot grabs 640x480, Three.js 1280x960 -> both normalised to 640x480)
def load(p): return np.asarray(Image.open(p).convert('RGB').resize((640, 480), Image.NEAREST), dtype=np.float32)
def mad(a, b, boxes=None):
    if boxes is None: return float(np.abs(a - b).mean())
    return float(np.mean([np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).mean() for x0, y0, x1, y1 in boxes]))
def gif(paths, out, ms):
    ims = [Image.open(p).convert('RGB').resize((640, 480), Image.NEAREST) for p in paths]
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=ms, loop=0)
report = {}
for d in sorted(glob.glob(os.path.join(root, '*'))):
    mf = os.path.join(d, f'frames_{look}.json')
    if not os.path.exists(mf): continue
    meta = json.load(open(mf))['meta']; eng = os.path.basename(d); report[eng] = {}
    seqs = {}
    for k in meta:
        m = re.match(r'(seq_(select|corner|snap)\d+)_(\d+)$', k)
        if m: seqs.setdefault(m.group(1), []).append((int(m.group(3)), k))
    for name, items in sorted(seqs.items()):
        items.sort(); keys = [k for _, k in items]; paths = [os.path.join(d, f'{k}_{look}.png') for k in keys]
        ims = [load(p) for p in paths]
        boxes = ROAD if 'select' in name else None
        diffs = [round(mad(ims[i], ims[i + 1], boxes), 2) for i in range(len(ims) - 1)]
        cams = [np.array(meta[k]['cam']) for k in keys]
        cam_steps = [round(float(np.linalg.norm(cams[i + 1] - cams[i])), 3) for i in range(len(cams) - 1)]
        scroll = [round(meta[k]['scroll_m'], 2) for k in keys]
        ent = {'frames': len(keys), 'mad_consecutive': diffs, 'cam_step_m': cam_steps, 'scroll_m': scroll,
               'rig': sorted({meta[k]['rig'] for k in keys}), 'rival_offset': [meta[k].get('rival_offset') for k in keys]}
        out = os.path.join(d, f'{name}_{look}.gif'); gif(paths, out, 200 if 'select' in name else 250); ent['gif'] = out
        report[eng][name] = ent
engs = list(report)
# cross-engine: same frame names, same look (informational; not expected to be pixel-identical)
cross = {}
for a in engs:
    for b in engs:
        if a < b and a.replace('godot', '') == b.replace('threejs', ''):
            names = [n for n in report[a] if n in report[b]]
            vals = []
            for n in names:
                for i in range(report[a][n]['frames']):
                    pa = os.path.join(root, a, f'{n}_{i}_{look}.png'); pb = os.path.join(root, b, f'{n}_{i}_{look}.png')
                    if os.path.exists(pa) and os.path.exists(pb): vals.append(mad(load(pa), load(pb)))
            cross[f'{a} vs {b}'] = {'frames': len(vals), 'mean_mad': round(float(np.mean(vals)), 2) if vals else None}
json.dump({'per_engine': report, 'cross_engine': cross}, open(os.path.join(root, f'frame_compare_{look}.json'), 'w'), indent=1)
for e, r in report.items():
    for n, v in r.items():
        print(f"{e:28s} {n:16s} rig={','.join(v['rig'])} MAD={v['mad_consecutive']} camstep={v['cam_step_m']} scroll={v['scroll_m'][0]}..{v['scroll_m'][-1]}" + (f" rival={v['rival_offset']}" if 'snap' in n else ''))
for k, v in cross.items(): print('CROSS', k, v)
