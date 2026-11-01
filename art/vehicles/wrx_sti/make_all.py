"""One-shot, headless, reproducible WRX clay pipeline (run from anywhere):  python3 make_all.py
trace -> classification sheet -> Blender build + rig + clearance check + renders -> IoU gate -> sheets -> key-line table."""
import subprocess, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BL = os.environ.get('BLENDER', 'blender')
env = dict(os.environ, PYTHONPATH=os.path.join(HERE, 'bp'))
def run(cmd):
    print('>>', ' '.join(cmd)); subprocess.run(cmd, cwd=HERE, check=True, env=env)
run([sys.executable, 'bp/extract.py'])
run([sys.executable, 'bp/classify_sheet.py'])
run([sys.executable, 'bp/fair.py'])                      # pass 2: fair the traced curves (bp/fair_curves.json)
run([BL, '-b', '--factory-startup', '-P', 'build_wrx.py', '--', '--render'])
run([sys.executable, 'bp/bpcompare.py'])
run([sys.executable, 'bp/feature_overlay.py'])
run([sys.executable, 'bp/deliver.py'])
run([sys.executable, 'bp/keylines.py'])
