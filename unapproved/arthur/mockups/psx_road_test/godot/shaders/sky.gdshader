shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled, depth_draw_opaque;
uniform sampler2D tex : source_color, filter_nearest, repeat_enable;
uniform int alpha_cut = 0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.090, 0.169);
void fragment() {
	vec4 t = texture(tex, UV);
	if (alpha_cut > 0 && t.a < 0.5) discard;
	ALBEDO = t.rgb;
}
