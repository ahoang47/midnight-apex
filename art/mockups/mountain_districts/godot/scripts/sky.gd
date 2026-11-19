## sky.tscn: painted sky cylinder + skyline/ridge band (B.1), fog colour-matched at the horizon; follows the camera at runtime
## (main.gd sets position = camera). The cylinder mesh is generated (r 250, y -125..125, 48 sides, as before the refactor) and the
## district textures are set by main.gd _apply_district. @tool: the editor shows it with the district's textures.
@tool
extends Node3D
const SKY_SH = preload("res://shaders/sky.gdshader")
@export var district := "touge"
var mat: ShaderMaterial

static func cylinder(r: float, y0: float, y1: float, rep: float) -> ArrayMesh:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 48
	for i in n:
		var a0 := TAU * i / n; var a1 := TAU * (i + 1) / n
		var u0 := rep * i / n; var u1 := rep * (i + 1) / n
		var v := [[Vector3(r * sin(a0), y0, r * cos(a0)), Vector2(u0, 1)], [Vector3(r * sin(a1), y0, r * cos(a1)), Vector2(u1, 1)],
			[Vector3(r * sin(a0), y1, r * cos(a0)), Vector2(u0, 0)], [Vector3(r * sin(a1), y1, r * cos(a1)), Vector2(u1, 0)]]
		for k in [0, 2, 1, 1, 2, 3]:
			st.set_uv(v[k][1]); st.add_vertex(v[k][0])
	return st.commit()

## build the material + mesh on the SkyCylinder child (band composited in sky.gdshader: r 240, y -3..22, rep 5, as Three.js)
func build() -> ShaderMaterial:
	mat = ShaderMaterial.new(); mat.shader = SKY_SH
	var sm: MeshInstance3D = $SkyCylinder
	sm.mesh = cylinder(250.0, -125.0, 125.0, 1.0); sm.material_override = mat
	return mat

func set_district(dk: String) -> void:
	mat.set_shader_parameter("tex", load("res://art/%s_sky.png" % dk))
	mat.set_shader_parameter("band_tex", load("res://art/%s.png" % ("street_skyline" if dk == "street" else "touge_ridge")))

func _ready() -> void:
	if Engine.is_editor_hint(): build(); set_district(district)
