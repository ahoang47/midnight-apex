// Additive glow billboard (A.4.3 / B.1): camera-facing quad of size `size`, texture alpha drives the additive amount.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
uniform vec2 snap_res = vec2(640.0, 480.0);
uniform sampler2D tex : filter_linear;
uniform vec3 color = vec3(1.0);
uniform float strength = 1.0;
uniform vec2 size = vec2(1.0);
uniform float fog_near = 30.0;
uniform float fog_far = 140.0;
varying float fog_depth;
void vertex() {
	vec4 mv = MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0);
	mv.xy += VERTEX.xy * size;
	fog_depth = -mv.z;
	vec4 clip = PROJECTION_MATRIX * mv;
	vec2 ndc = clip.xy / clip.w;
	ndc = floor(ndc * snap_res * 0.5 + 0.5) / (snap_res * 0.5);
	clip.xy = ndc * clip.w;
	POSITION = clip;
}
void fragment() {
	vec4 t = texture(tex, UV);
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = t.rgb * color * t.a * strength * (1.0 - f);
}
