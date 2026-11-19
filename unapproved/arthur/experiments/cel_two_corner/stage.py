#!/usr/bin/env python3
"""Stage the Cel A two-corner experiment: symlink every file of Gordon's two-corner Godot project
(../../../gordon/two-corner/godot) into ./godot, except the files this experiment owns (real files already in
./godot: the cel shaders + cel.gdshaderinc, scripts/main.gd, project.godot). Never edits Gordon's folder."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.realpath(os.path.join(HERE, '..', '..', '..', 'gordon', 'two-corner', 'godot'))
DST = os.path.join(HERE, 'godot')
n = 0
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d != '.godot']
    rel = os.path.relpath(root, SRC)
    for f in files:
        r = os.path.normpath(os.path.join(rel, f))
        dst = os.path.join(DST, r)
        if os.path.exists(dst) and not os.path.islink(dst):
            continue  # our overlay
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.islink(dst):
            os.unlink(dst)
        os.symlink(os.path.join(root, f), dst); n += 1
print('linked', n)
