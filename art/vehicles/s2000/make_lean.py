"""One-shot, headless S2000 LEAN pipeline (<= 2,000 tris, detail in texture).  python3 make_lean.py
Reads the approved build (s2000_lowpoly.blend, build_s2000.py sections, s2000_atlas.png) and never writes to it.
Writes lean/ only."""
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BL = os.environ.get('BLENDER', 'blender')
def run(cmd, **env):
    print('>>', ' '.join(cmd)); subprocess.run(cmd, cwd=HERE, check=True, env=dict(os.environ, **env))
run([sys.executable, 'tex/debrand_atlas.py', 's2000_atlas.png', 'lean/tex/s2000_atlas_lean.png'])
run([BL, '-b', '-P', 'build_s2000_lean.py', '--', '--render'])
# light headlamp molding (post-step on the finished lean; see lean/README.md 'Headlamp molding'):
# 3/4 albedo close render -> painted lamp outline -> raised surround ray-cast onto the body -> re-save blend/glb,
# clearance, tri soup; then the textured frames are re-shot.
LC = os.path.join(os.path.dirname(HERE), 'lean_common', 'lamps')
run([BL, '-b', 'lean/s2000_lean.blend', '-P', f'{LC}/molding_view.py', '--', os.path.join(HERE, 'lean/molding/view'), 'xfwd', *'1.9 0.66 0.64 30 8 0.75'.split()])
run([sys.executable, f'{LC}/molding_outline.py', 'lean/molding/view', *'0-9,165-180 12 80 9'.split()])
run([BL, '-b', 'lean/s2000_lean.blend', '-P', f'{LC}/molding_ring.py', '--', 'S2000', 'xfwd', os.path.join(HERE, 'lean/molding/view_outline.json'), os.path.join(HERE, 'lean')])
run([BL, '-b', 'lean/s2000_lean.blend', '-P', f'{LC}/rerender_textured.py', '--', 'xfwd', os.path.join(HERE, 'lean/renders/raw'), 's2000'])
run([BL, '-b', 'lean/s2000_lean.blend', '-P', 'bp/cmp_from_blend.py'])            # compare silhouettes incl. the molding
run([sys.executable, 'bp/compare_lean.py'], S2K_RD=os.path.join(HERE, 'lean/renders/raw/'))
run([sys.executable, 'bp/deliver_lean.py'])
