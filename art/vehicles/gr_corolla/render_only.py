"""Re-render from out/gr_corolla_clay.blend without rebuilding:  blender -b out/gr_corolla_clay.blend -P render_only.py"""
import bpy, sys, os, importlib
HERE = os.path.normpath(os.path.join(os.path.dirname(bpy.data.filepath), '..')); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'parts'))
import build_gr_corolla as B, render_gr as R
from mathutils import Vector
ob = bpy.data.objects
rig = dict(body=ob['GRC_Body'], hub={k: ob[f'Hub_{k}-wheel'] for k in ('FL', 'FR', 'RL', 'RR')}, steer={k: ob[f'Steer_{k}'] for k in ('FL', 'FR')},
           susp={k: ob[f'Susp_{k}'] for k in ('FL', 'FR', 'RL', 'RR')})
rig['hub_rest'] = {k: tuple(h.location) for k, h in rig['hub'].items()}
R.render_all(os.path.join(HERE, 'out'), rig, B.set_pose, dict(BUMP=B.BUMP_F, DROOP=B.DROOP, LOCK=B.LOCK, ROLL=B.ROLL))
