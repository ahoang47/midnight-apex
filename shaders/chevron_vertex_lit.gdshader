// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled, depth_draw_always;
#include "res://shaders/cel.gdshaderinc"
#include "res://shaders/vertex_lights.gdshaderinc"
uniform sampler2D tex : filter_nearest, repeat_disable;
uniform vec3 tint : source_color = vec3(1.0);
uniform float gain = 1.0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.09, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform float fog_amount = 1.0;
varying float fog_depth; varying vec3 vlight;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	if (length(wn) < 0.01) wn = vec3(0.0, 1.0, 0.0);
	vlight = (live_light > 0.5) ? vl_eval(wp, wn) : vec3(1.0);
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	POSITION = PROJECTION_MATRIX * mv;
}
void fragment() {
	vec4 t = texture(tex, UV);
	if (t.a < 0.5) discard;
	vec3 c = vl_apply(t.rgb * tint * gain, vlight);
	float f = fog_amount * clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(c, fog_color, f);
	if (CEL_GB > 0.5) discard;
}
