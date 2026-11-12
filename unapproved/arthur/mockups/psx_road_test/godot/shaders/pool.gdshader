shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
uniform sampler2D tex : source_color, filter_nearest, repeat_disable;
uniform float strength = 0.162; // pool_k 0.09 * lane_pool_mul 1.8
void fragment() {
	vec4 t = texture(tex, UV);
	ALBEDO = t.rgb * t.a * strength;
}
