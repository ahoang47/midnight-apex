"""One-shot, headless WRX LEAN pipeline (<= 2,000 tris, detail in texture).  python3 make_lean.py
Needs the pass-2 trace products (bp/curves.json, bp/bp_classes.npz, bp/fair_curves.json: python3 make_all.py, or
bp/extract.py + bp/fair.py).  Leaves the pass-2 clay build (wrx_clay.*, renders/) untouched; writes lean/."""
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BL = os.environ.get('BLENDER', 'blender')
def run(cmd, **env):
    print('>>', ' '.join(cmd)); subprocess.run(cmd, cwd=HERE, check=True, env=dict(os.environ, **env))
run([sys.executable, 'bp/vectorize.py'])
run([sys.executable, 'tex/lamp/trace_lamps.py'])
run([BL, '-b', '--factory-startup', '-P', 'build_wrx_lean.py', '--', '--render'])
run([sys.executable, 'bp/bpcompare.py'], WRX_OUT='lean')
run([sys.executable, 'bp/deliver.py'], WRX_OUT='lean', WRX_PFX='wrx_lean_clay')
run([sys.executable, 'bp/deliver_lean.py'])
