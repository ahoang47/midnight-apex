// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
#include "res://shaders/cel.gdshaderinc"
uniform vec3 color : source_color = vec3(1.0, 0.12, 0.08);
uniform float strength = 0.9;
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
varying float fog_depth;
varying vec4 vcol;
void vertex() {
	vcol = COLOR;
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	POSITION = PROJECTION_MATRIX * mv;
}
void fragment() {
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	if (CEL_GB > 0.5) { ALBEDO = vec3(0.0); }
	else { ALBEDO = color * vcol.rgb * vcol.a * strength * (1.0 - f); }
}
