#!/usr/bin/env python3
"""Stage the districts Godot project: symlink every file of the E3B resource-meter project
(resource_meters/godot, itself staged from line_preview + Gordon's scenes) into ./godot, except
files this mockup owns (real files already in ./godot). Never edits the source projects."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'resource_meters', 'godot')
DST = os.path.join(HERE, 'godot')
SRC = os.path.realpath(SRC)
n = 0
for root, dirs, files in os.walk(SRC, followlinks=True):
    dirs[:] = [d for d in dirs if d != '.godot']
    rel = os.path.relpath(root, SRC)
    for f in files:
        r = os.path.normpath(os.path.join(rel, f))
        if r in ('project.godot',):
            continue
        dst = os.path.join(DST, r)
        if os.path.exists(dst) and not os.path.islink(dst):
            continue  # our overlay
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        real = os.path.realpath(os.path.join(root, f))
        if os.path.islink(dst):
            os.unlink(dst)
        os.symlink(real, dst); n += 1
print('linked', n)
