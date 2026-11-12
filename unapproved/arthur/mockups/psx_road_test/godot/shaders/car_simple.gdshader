// Visible unlit car with linear fog. No vertex snap (snap was discarding the mesh in this pass).
shader_type spatial;
render_mode unshaded, cull_back, fog_disabled;
uniform sampler2D albedo_tex : source_color, filter_linear;
uniform bool has_tex = true;
uniform vec3 base_col = vec3(0.6);
uniform vec3 tint = vec3(1.0);
uniform bool emissive = false;
uniform vec3 fog_color : source_color = vec3(0.043, 0.090, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform vec3 key_dir = vec3(-0.35, 0.82, -0.45);
uniform float ambient = 0.55;
varying float fog_depth;
varying vec3 wn;
void vertex() {
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	POSITION = PROJECTION_MATRIX * mv;
}
void fragment() {
	vec3 alb = (has_tex ? texture(albedo_tex, UV).rgb : base_col) * tint;
	vec3 col;
	if (emissive) {
		col = alb * 1.4;
	} else {
		float diff = ambient + max(dot(normalize(wn), normalize(key_dir)), 0.0) * (1.0 - ambient);
		col = alb * diff;
	}
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(col, fog_color, f);
}
