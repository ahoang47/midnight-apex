"""Re-render the textured detail build from detail/mx5_detail.blend without rebuilding:
blender -b detail/mx5_detail.blend -P render_detail_only.py"""
import bpy, sys, os, importlib
HERE = os.path.normpath(os.path.join(os.path.dirname(bpy.data.filepath), '..'))                 # blend lives in detail/
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'parts'))
import build_mx5 as B, render_detail as R
ob = bpy.data.objects
rig = dict(body=ob['MX5_Body'], hub={k: ob[f'Hub_{k}-wheel'] for k in ('FL', 'FR', 'RL', 'RR')}, steer={k: ob[f'Steer_{k}'] for k in ('FL', 'FR')},
           susp={k: ob[f'Susp_{k}'] for k in ('FL', 'FR', 'RL', 'RR')})
rig['hub_rest'] = {k: tuple(h.location) for k, h in rig['hub'].items()}
R.render_textured(os.path.join(HERE, 'detail'), rig, B.set_pose)
