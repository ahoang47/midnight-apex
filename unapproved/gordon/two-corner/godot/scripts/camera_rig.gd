## camera_rig.tscn: the main 3D camera + the authored corner camera path (guide §13.3, Path3D / PathFollow3D).
## The poses (B.5b Entry chase / Apex / Exit stops, LINE LOCKED return, playback path) are still computed by main.gd
## _update_camera exactly as before the scene refactor; this scene only owns the nodes so they can be inspected in the editor.
## Austin 2026-11-12: the Entry camera and Entry selection screen are final; do not change their placement, framing, motion or timing.
@tool
extends Node3D
@onready var cam: Camera3D = $Cam
@onready var path: Path3D = $CornerPath
@onready var follow: PathFollow3D = $CornerPath/Follow
