"""Writes car_mx5.tscn: an inherited scene of car_mx5.glb (Godot 4.6; copy of gr_corolla/godot/make_tscn.py).  The glb import hints already make
MX5 a VehicleBody3D and Hub_XX VehicleWheel3D; this scene only sets the rig values from the README, adds a body
collision box, attaches susp_follow.gd to Susp_XX (wheel + steers) and hides the lamp-glow FX.
python3 godot/make_tscn.py <out.tscn> [LIFT]   (rig numbers from detail/bp/rig_meta.json)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); R = json.load(open(os.path.join(HERE, '..', 'detail', 'bp', 'rig_meta.json')))
OUT = sys.argv[1]; LIFT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
D = 'res://assets/cars/mx5'
HX, HZ, HY = R['track'] / 2, R['wheel_x'][0], R['tyre_r']               # glTF/Godot: +X car left, +Y up, +Z forward
COM = (0.0, R['COM'][1], R['COM'][0])
REST, STIFF = 0.15, 80.0
L = ['[gd_scene load_steps=4 format=3]', '',
     f'[ext_resource type="PackedScene" path="{D}/car_mx5.glb" id="1_glb"]',
     f'[ext_resource type="Script" path="{D}/susp_follow.gd" id="2_susp"]', '',
     '[sub_resource type="BoxShape3D" id="BoxShape3D_body"]', 'size = Vector3(1.70, 0.80, 3.85)', '',
     '[node name="car_mx5" instance=ExtResource("1_glb")]', '',
     '[node name="MX5" parent="." index="0"]', 'mass = 1060.0', 'center_of_mass_mode = 1',
     f'center_of_mass = Vector3({COM[0]}, {COM[1]}, {COM[2]})', '',
     '[node name="MX5_FX_LampGlow" parent="MX5" index="1"]', 'visible = false', '']
for c in ('FL', 'FR', 'RL', 'RR'):
    x = HX if c[1] == 'L' else -HX; z = HZ if c[0] == 'F' else -HZ; y = HY + LIFT; front = c[0] == 'F'
    tr = f'Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x:.6f}, {y:.6f}, {z:.6f})'
    L += [f'[node name="Hub_{c}" parent="MX5"]', f'transform = {tr}', f'use_as_traction = {"false" if front else "true"}', f'use_as_steering = {"true" if front else "false"}',
          f'wheel_rest_length = {REST}', f'wheel_radius = {R["tyre_r"]}', f'wheel_friction_slip = 3.0',
          f'suspension_travel = {(R["bump_front"] if front else R["bump_rear"]) + R["droop"]:.3f}', f'suspension_stiffness = {STIFF}',
          'damping_compression = 1.6', 'damping_relaxation = 2.2', '',
          f'[node name="Susp_{c}" parent="MX5" node_paths=PackedStringArray("wheel")]', f'transform = {tr}', 'script = ExtResource("2_susp")', f'wheel = NodePath("../Hub_{c}")',
          f'steers = {"true" if front else "false"}', '']
L += ['[node name="BodyCollision" type="CollisionShape3D" parent="MX5"]', 'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.70, 0)',
      'shape = SubResource("BoxShape3D_body")', '']
open(OUT, 'w').write('\n'.join(L)); print('wrote', OUT, 'LIFT', LIFT)
