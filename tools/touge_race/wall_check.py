#!/usr/bin/env python3
"""WALL check (companion to void_check): a race camera must not look into one surface that fills the frame
(pt137u v6: turn 5's terrain skirt hung down over turn 10's road and the t10 views rendered as one dark-green wall, which the
void metric cannot see because no sky shows). Per raw sweep frame: 8x8 blocks that are flat (std < 3) and not sky; the
largest 4-connected region of them as a fraction of the frame. A camera inside / against a wall gives one region over ~90 %;
a gallery (turn 10 under turn 5) or a dark slope next to the road stays under ~75 % because the road, rail and portal break it.
usage: wall_check.py SHOTS [--max 0.8]   prints WALL_CHECK ... PASS/FAIL."""
import sys, glob, os
import numpy as np
from PIL import Image
from scipy import ndimage
d = sys.argv[1]; mx = float(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 0.8
bad = []; rows = []
for f in sorted(glob.glob(os.path.join(d, "void_raw", "*.png"))):
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
    h, w = (a.shape[0] // 8) * 8, (a.shape[1] // 8) * 8
    b = a[:h, :w].reshape(h // 8, 8, w // 8, 8, 3)
    sky = ((b[..., 0] > 200) & (b[..., 1] < 60) & (b[..., 2] > 200)).mean(axis=(1, 3)) > 0.5
    flat = (b.std(axis=(1, 3)).max(axis=-1) < 3.0) & ~sky
    lab, n = ndimage.label(flat)
    fr = float(np.bincount(lab.ravel())[1:].max()) / flat.size if n else 0.0
    nm = os.path.basename(f)[:-4]; rows.append((fr, nm))
    if fr > mx: bad.append((fr, nm))
rows.sort(reverse=True)
print("WALL top:", ", ".join("%s %.2f" % (n, v) for v, n in rows[:8]))
print("WALL_CHECK frames=%d over_%.2f=%d %s %s" % (len(rows), mx, len(bad), ", ".join(n for _, n in bad[:12]), "PASS" if not bad and rows else "FAIL"))
sys.exit(0 if rows and not bad else 1)
