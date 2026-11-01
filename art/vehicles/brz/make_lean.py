"""One-shot, headless BRZ LEAN pipeline (<= 2,000 tris, detail in texture).  python3 make_lean.py
Reads the approved pass-4 build (brz_lowpoly.blend, parts/brz_geo.py, brz_atlas.png, bp/) and never writes to it.
Writes lean/ only."""
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BL = os.environ.get('BLENDER', 'blender')
def run(cmd, **env):
    print('>>', ' '.join(cmd)); subprocess.run(cmd, cwd=HERE, check=True, env=dict(os.environ, **env))
run([BL, '-b', '-P', 'build_brz_lean.py', '--', '--render'])
# light headlamp molding (post-step on the finished lean; see lean/README.md 'Headlamp molding'):
# 3/4 albedo close render -> painted lamp outline -> raised surround ray-cast onto the body -> re-save blend/glb,
# clearance, tri soup; then the textured frames are re-shot.
LC = os.path.join(os.path.dirname(HERE), 'lean_common', 'lamps')
run([BL, '-b', 'lean/brz_lean.blend', '-P', f'{LC}/molding_view.py', '--', os.path.join(HERE, 'lean/molding/view'), 'xleft', *'1.9 0.70 0.71 35 8 0.75'.split()])
run([sys.executable, f'{LC}/molding_outline.py', 'lean/molding/view', *'95-135 10 80 9 hull'.split()])
run([BL, '-b', 'lean/brz_lean.blend', '-P', f'{LC}/molding_ring.py', '--', 'BRZ', 'xleft', os.path.join(HERE, 'lean/molding/view_outline.json'), os.path.join(HERE, 'lean')])
run([BL, '-b', 'lean/brz_lean.blend', '-P', f'{LC}/rerender_textured.py', '--', 'xleft', os.path.join(HERE, 'lean/renders/raw'), 'brz'])
run([sys.executable, 'bp/bpcompare_lean.py'], BRZ_TRIS='lean/bp/tris_carframe.npy', BRZ_IOU='lean/bp/iou_bpframe.json', BRZ_OD='lean/renders/raw')
run([sys.executable, 'bp/deliver_lean.py'], BRZ_OLD_TRIS='4079')
