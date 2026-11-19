#!/usr/bin/env python3
"""Stage the cel-shaded experiment: symlink every file of the staged districts project
(../../mockups/districts/godot, itself staged from resource_meters) into ./godot, except files this
experiment owns (real files already in ./godot: cel shaders, the preview script copy, post, project).
Never edits the source projects."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.realpath(os.path.join(HERE, '..', '..', 'mockups', 'districts', 'godot'))
DST = os.path.join(HERE, 'godot')
n = 0
for root, dirs, files in os.walk(SRC, followlinks=True):
    dirs[:] = [d for d in dirs if d != '.godot']
    rel = os.path.relpath(root, SRC)
    for f in files:
        r = os.path.normpath(os.path.join(rel, f))
        if r == 'project.godot' or r.endswith('.uid') and os.path.exists(os.path.join(DST, r[:-4])) and not os.path.islink(os.path.join(DST, r[:-4])):
            continue  # our overlay owns the script; let Godot give it its own uid
        dst = os.path.join(DST, r)
        if os.path.exists(dst) and not os.path.islink(dst):
            continue  # our overlay
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        real = os.path.realpath(os.path.join(root, f))
        if os.path.islink(dst):
            os.unlink(dst)
        os.symlink(real, dst); n += 1
print('linked', n)
