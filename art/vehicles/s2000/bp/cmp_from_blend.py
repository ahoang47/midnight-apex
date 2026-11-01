"""Compare silhouettes (bp/compare_lean.py frames) from the saved lean .blend: blender -b lean/s2000_lean.blend -P bp/cmp_from_blend.py"""
import bpy, sys, os
_CAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, _CAR); sys.argv = sys.argv[:1]
import build_s2000_lean as S
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('S2000_') and '_Susp_' not in o.name]
S.cmp_renders(objs, os.path.join(_CAR, 'lean', 'renders', 'raw'))
