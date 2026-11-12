#!/bin/sh
# Build the pack road texture and render the Entry frame in Godot 4.6.3 (xvfb, GL Compatibility).
# Does not render in-game screens in Blender. before.png is the existing Blender frame, copied in.
set -e
cd "$(dirname "$0")"
B=/workspace/tools/godot
python3 compose_road.py
cp -f tex/road_3lane.png godot/art/road_3lane.png
cp -f tex/concrete_kerb.png godot/art/concrete_kerb.png
# Stage car glbs if needed (from the two-corner prototype or the repo assets)
if [ ! -f godot/cars/car_mx5.glb ]; then
  if [ -f /workspace/prototypes/two-corner/godot/assets/cars/car_mx5.glb ]; then
    cp /workspace/prototypes/two-corner/godot/assets/cars/*.glb /workspace/prototypes/two-corner/godot/assets/cars/*.png godot/cars/
  else
    cp /workspace/midnight-apex/assets/cars/mx5/car_mx5.glb /workspace/midnight-apex/assets/cars/s2000/car_s2000.glb godot/cars/
  fi
fi
# Import resources once, then render on a virtual display (same pattern as prototypes/two-corner/tools/run_shots.sh)
$B --headless --path godot --import >/tmp/psx_road_import.log 2>&1 || true
xvfb-run -a -s "-screen 0 1280x960x24" $B --path godot --rendering-driver opengl3 >/tmp/psx_road_godot.log 2>&1
python3 make_sheet.py
echo "run ok"
