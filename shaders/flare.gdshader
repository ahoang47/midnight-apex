// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
#include "res://shaders/cel.gdshaderinc"
uniform sampler2D tex : filter_linear, repeat_disable;
uniform vec3 color : source_color = vec3(0.941176, 0.784314, 0.580392);
uniform float strength = 0.55;
uniform vec2 size = vec2(6.0, 3.2);
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform vec3 fog_color : source_color = vec3(0.043137, 0.090196, 0.168627); // #0B172B (unused; additive fades to 0)
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform vec3 local_forward = vec3(0.0, 0.0, 1.0);
uniform float facing_k = 0.0; // 0 = omni (lamps), 1 = fade by view angle (head/tail)
varying float fog_depth;
varying float vface;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 fwd = normalize((MODEL_MATRIX * vec4(local_forward, 0.0)).xyz);
	vec3 view = CAMERA_POSITION_WORLD - wp;
	float vl = length(view);
	view = view / max(vl, 1e-4);
	// lamps (facing_k=0) stay on; car lights fade when the camera is off-axis / behind the lens.
	float face = max(dot(fwd, view), 0.0);
	vface = mix(1.0, pow(face, 1.15), facing_k);
	vec4 mv = MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0);
	// modest size-over-distance so distant flares stay readable but don't balloon
	float sc = mix(1.0, 0.85, clamp(( -mv.z - 12.0) / 60.0, 0.0, 1.0));
	mv.xy += VERTEX.xy * size * sc;
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
	if (CEL_GB > 0.5) { ALBEDO = vec3(0.0); }
	else { ALBEDO = t.rgb * color * t.a * strength * vface * (1.0 - f); }
}
