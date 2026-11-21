#!/bin/bash
# build -> copy into the scratch project -> import -> render after shots
cd /workspace/touge_env_work
/workspace/tools/blender-4.2.3-linux-x64/blender -b -P blender_build.py 2>&1 | grep -E "Traceback|Error" | cut -c1-300
G=/workspace/touge_env_godot
rm -rf $G/assets/env/touge; mkdir -p $G/assets/env/touge
cp -r /workspace/touge_env_build/assets/env/touge/* $G/assets/env/touge/
cp /workspace/touge_env_build/assets/tex/kit/env/*.png $G/assets/tex/kit/env/
cd $G
timeout 600 xvfb-run -a -s "-screen 0 1280x960x24" /workspace/tools/godot --headless --path . --import > /workspace/touge_env_work/import.log 2>&1
. /workspace/touge_env_work/.venv/bin/activate
python /workspace/touge_env_work/poses.py ${1:-/workspace/touge_env_work/shots_after} /workspace/touge_env_work/after.json >/dev/null
timeout 900 xvfb-run -a -s "-screen 0 1280x960x24" /workspace/tools/godot --path . --rendering-driver opengl3 -- --no-menu --no-timer --authored-env res://assets/env/touge --env-shots /workspace/touge_env_work/after.json > /workspace/touge_env_work/after.log 2>&1
grep -E "ENV_SWAP|ERROR|SCRIPT ERROR|ENV_SHOTS_DONE" /workspace/touge_env_work/after.log | head -20
