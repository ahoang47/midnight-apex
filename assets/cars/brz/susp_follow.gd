# Midnight Apex lean cars - strut/arm follower (Godot 4.x).
# Scene layout after importing <car>_lean.glb:
#   <CAR>-vehicle      -> make it (or replace it with) a VehicleBody3D; <CAR>_Body mesh stays a child.
#   Hub_XX-wheel       -> change type to VehicleWheel3D (keep its transform = static hub centre).
#        Steer_XX / <CAR>_Wheel_XX stay children of the wheel: VehicleWheel3D moves, steers AND spins them.
#   Susp_XX            -> Node3D sibling of the wheels (child of the VehicleBody3D); attach THIS script and set
#                         `wheel` to the matching VehicleWheel3D, `steers` = true on the front pair.
#        <CAR>_Susp_XX mesh (strut + lower arm) stays its child: it follows travel and steering, never the spin.
extends Node3D

@export var wheel: VehicleWheel3D
@export var steers := false

var _rest_basis: Basis

func _ready() -> void:
	_rest_basis = transform.basis

func _physics_process(_delta: float) -> void:
	if wheel == null:
		return
	# same parent as the wheel, so the wheel's local position already carries the suspension travel
	position = wheel.position
	basis = Basis(Vector3.UP, wheel.steering) * _rest_basis if steers else _rest_basis
