#!/usr/bin/env python3
"""Stage the Cel A two-corner reference build: symlink the root Godot project's runtime
trees (assets/, scenes/, scripts/, shaders/, fonts/, spec/, plus icon.svg) into ./godot,
except the files this folder owns (real files already in ./godot: the cel shaders +
cel.gdshaderinc, scripts/main.gd, project.godot). Never edits Gordon's files.

The two-corner test lives at the repo root since 2026-11-19 (3748b4f). Stand-in textures
are at res://assets/tex/kit/; cars load res://assets/cars/mx5 and s2000 .glb. art/ is
Arthur's source art and is not staged (and is hidden from the root project by art/.gdignore).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.realpath(os.path.join(HERE, '..', '..', '..'))
DST = os.path.join(HERE, 'godot')
STAGE_DIRS = ('assets', 'scenes', 'scripts', 'shaders', 'fonts', 'spec')
STAGE_ROOT_FILES = ('icon.svg', 'icon.svg.import', 'export_presets.cfg')

if not os.path.isfile(os.path.join(SRC, 'project.godot')) or not os.path.isdir(os.path.join(SRC, 'scenes')):
    raise SystemExit('missing root Godot project at %s (expected repo-root project.godot + scenes/)' % SRC)

n = 0

def link_file(src, dst):
    global n
    if os.path.exists(dst) and not os.path.islink(dst):
        return  # our overlay
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.islink(dst):
        os.unlink(dst)
    os.symlink(src, dst)
    n += 1

for name in STAGE_ROOT_FILES:
    src = os.path.join(SRC, name)
    if os.path.isfile(src):
        link_file(src, os.path.join(DST, name))

for top in STAGE_DIRS:
    src_top = os.path.join(SRC, top)
    if not os.path.isdir(src_top):
        raise SystemExit('missing root Godot tree %s' % src_top)
    for root, dirs, files in os.walk(src_top):
        dirs[:] = [d for d in dirs if d != '.godot']
        rel = os.path.relpath(root, SRC)
        for f in files:
            r = os.path.normpath(os.path.join(rel, f))
            link_file(os.path.join(root, f), os.path.join(DST, r))

print('linked', n)
