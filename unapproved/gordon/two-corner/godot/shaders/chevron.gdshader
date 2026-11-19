// Flat road chevrons (B.5d): unlit, hard alpha, linear fog, no glow, no soft edges.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled, depth_draw_always;
uniform sampler2D tex : filter_nearest, repeat_disable;
uniform vec3 tint : source_color = vec3(1.0);
uniform float gain = 1.0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.09, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform float fog_amount = 1.0;
varying float fog_depth;
void vertex() {
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	POSITION = PROJECTION_MATRIX * mv;
}
void fragment() {
	vec4 t = texture(tex, UV);
	if (t.a < 0.5) discard;
	vec3 c = t.rgb * tint * gain;
	float f = fog_amount * clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(c, fog_color, f);
}
