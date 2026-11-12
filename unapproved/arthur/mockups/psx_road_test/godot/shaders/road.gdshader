shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
uniform sampler2D tex_lin : source_color, filter_linear, repeat_enable;
uniform sampler2D tex_near : source_color, filter_nearest, repeat_enable;
uniform int use_nearest = 0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.090, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform int alpha_cut = 0;
varying float fog_depth;
varying vec4 vcol;
void vertex() {
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	POSITION = PROJECTION_MATRIX * mv;
	vcol = COLOR;
}
void fragment() {
	vec4 t = use_nearest > 0 ? texture(tex_near, UV) : texture(tex_lin, UV);
	if (alpha_cut > 0 && t.a < 0.5) discard;
	vec3 c = t.rgb * vcol.rgb * 2.0;
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(c, fog_color, f);
}
