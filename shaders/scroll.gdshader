// Scrolling textured strips + static cut-out cards (guide §14.2 UV offset), PSX vertex snap, affine UVs, linear fog.
// UV.y carries metres along the road; scroll_m = RoadScroller.uv_offset * road_uv_length_m.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform sampler2D tex : filter_linear, repeat_enable; // raw numbers, like the Three.js NoColorSpace texture
uniform float scroll_m = 0.0;
uniform float tile = 8.0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.051, 0.102);
uniform float fog_near = 30.0;
uniform float fog_far = 140.0;
uniform float fog_amount = 1.0;
varying float fog_depth; varying vec3 uvw;
void vertex() {
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	vec4 clip = PROJECTION_MATRIX * mv;
	vec2 ndc = clip.xy / clip.w;
	ndc = floor(ndc * snap_res * 0.5 + 0.5) / (snap_res * 0.5);
	clip.xy = ndc * clip.w;
	POSITION = clip;
	vec2 t = vec2(UV.x, (UV.y + scroll_m) / tile);
	uvw = vec3(t * clip.w, clip.w);
}
void fragment() {
	vec2 uv = uvw.xy / uvw.z;
	vec4 t = texture(tex, fract(uv));
	if (t.a < 0.5) discard;  // alpha cut-out cards (B.1)
	float f = fog_amount * clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(t.rgb, fog_color, f);
}
