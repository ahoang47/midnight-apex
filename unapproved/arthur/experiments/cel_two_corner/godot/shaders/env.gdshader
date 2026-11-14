// CEL EXPERIMENT copy: unlit vertex-colour environment (lamp posts) + toon ramp; the #F0C894 lamp head stays full-bright.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
#include "res://shaders/cel.gdshaderinc"
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform vec3 fog_color : source_color = vec3(0.043, 0.051, 0.102);
uniform float fog_near = 30.0;
uniform float fog_far = 140.0;
varying float fog_depth; varying vec3 vcol;
void vertex() {
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	vec4 clip = PROJECTION_MATRIX * mv;
	vec2 ndc = clip.xy / clip.w;
	ndc = floor(ndc * snap_res * 0.5 + 0.5) / (snap_res * 0.5);
	clip.xy = ndc * clip.w;
	POSITION = clip;
	vcol = COLOR.rgb;
}
void fragment() {
	if (CEL_GB > 1.5) { ALBEDO = cel_pack_depth(fog_depth); }
	else if (CEL_GB > 0.5) { ALBEDO = cel_pack_normal(cel_face_normal(VERTEX)); }
	else {
		vec3 c = vcol;
		if (cel_on > 0.5 && dot(c, vec3(0.333)) < 0.5) {
			vec3 nw = normalize((INV_VIEW_MATRIX * vec4(cel_face_normal(VERTEX), 0.0)).xyz);
			c = cel_ramp(c, dot(nw, normalize(CEL_KEY)), 0.80, 0.60);
		}
		float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
		ALBEDO = mix(c, fog_color, f);
	}
}
