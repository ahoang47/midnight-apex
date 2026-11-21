# python dbg.py out_dir [--before] name:s,d,h:s,d,h[:fov] ...
import json, sys, subprocess, os
from posecore import pt
out = sys.argv[1]; args = sys.argv[2:]; before = '--before' in args; args = [a for a in args if a != '--before']
P = []
for a in args:
    f = a.split(':'); ps = [float(x) for x in f[1].split(',')]; lk = [float(x) for x in f[2].split(',')]
    p = {'name': f[0], 'pos': pt(*ps), 'look': pt(*lk), 'fov': float(f[3]) if len(f) > 3 else 60, 'far': 600}
    if len(f) > 4 and f[4] == 'nofog': p['fog_off'] = True; p['far'] = 2000
    if len(f) > 5: p['car_s'] = float(f[5])
    P.append(p)
json.dump({'out': os.path.abspath(out), 'poses': P}, open('/tmp/dbg.json', 'w'))
cmd = ['timeout', '600', 'xvfb-run', '-a', '-s', '-screen 0 1280x960x24', '/workspace/tools/godot', '--path', '/workspace/touge_env_godot',
       '--rendering-driver', 'opengl3', '--', '--no-menu', '--no-timer'] + ([] if before else ['--authored-env', 'res://assets/env/touge']) + ['--env-shots', '/tmp/dbg.json']
r = subprocess.run(cmd, capture_output=True, text=True)
print([l for l in r.stdout.splitlines() if 'ENV_' in l or 'ERROR' in l][-4:])
