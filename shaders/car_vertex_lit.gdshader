// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
shader_type spatial;
render_mode unshaded, cull_back, fog_disabled;
#include "res://shaders/cel.gdshaderinc"
#include "res://shaders/vertex_lights.gdshaderinc"
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D env_equirect : source_color, filter_linear;
uniform bool has_tex = true;
uniform vec3 key_dir = vec3(0.4, 0.8, 0.3);
uniform float ambient = 0.55;
uniform float spec_power = 48.0;
uniform float env_strength = 0.45;
uniform float spec_scale = 0.2;
uniform vec3 tint = vec3(1.0);
uniform vec3 env_tint = vec3(1.0);
uniform vec3 base_col = vec3(0.6);
uniform bool emissive = false;
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform vec3 fog_color : source_color = vec3(0.043, 0.09, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
varying vec3 uvw; varying vec3 wn; varying vec3 wv; varying float fog_depth; varying vec3 vlight;
void vertex() {
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wv = wp - CAMERA_POSITION_WORLD;
	vlight = (live_light > 0.5) ? vl_eval(wp, wn) : (ambient_col * ambient_k);
	vec4 mv = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	fog_depth = -mv.z;
	vec4 clip = PROJECTION_MATRIX * mv;
	vec2 ndc = clip.xy / clip.w;
	ndc = floor(ndc * snap_res * 0.5 + 0.5) / (snap_res * 0.5);
	clip.xy = ndc * clip.w;
	POSITION = clip;
	uvw = vec3(UV * clip.w, clip.w);
}
void fragment() {
	if (CEL_GB > 1.5) { ALBEDO = cel_pack_depth(fog_depth); }
	else if (CEL_GB > 0.5) { ALBEDO = cel_pack_normal(normalize((VIEW_MATRIX * vec4(normalize(wn), 0.0)).xyz)); }
	else {
	vec2 uv = uvw.xy / uvw.z;
	vec3 n = normalize(wn); vec3 l = normalize(key_dir); vec3 v = -normalize(wv);
	vec3 alb = (has_tex ? texture(albedo_tex, uv).rgb : base_col) * tint;
	vec3 col;
	if (emissive) { col = alb * 1.4; }
	else if (cel_on < 0.5) {
		vec3 lit = vlight;
		float spec = pow(max(dot(n, normalize(l + v)), 0.0), spec_power) * spec_scale;
		vec3 r = reflect(-v, n);
		vec2 euv = vec2(atan(r.z, r.x) / 6.2831853 + 0.5, acos(clamp(r.y, -1.0, 1.0)) / 3.1415927);
		float fres = env_strength * pow(1.0 - max(dot(n, v), 0.0), 2.0) + 0.08;
		col = alb * lit + vec3(spec) + texture(env_equirect, euv).rgb * fres * env_tint;
	}
	else {
		// Keep the 3 hard bands: key ndl plus a lamp lift so a sodium nearby can push a face up a band.
		float lamp_l = max(dot(vlight - ambient_col * ambient_k, vec3(0.299, 0.587, 0.114)), 0.0);
		float ndl = dot(n, l) + lamp_l * 1.15;
		col = cel_ramp(cel_poster(alb), ndl, 0.72, 0.52);
		col += alb * max(vlight - ambient_col * ambient_k, vec3(0.0)) * 0.28; // lamp chroma (sodium and/or mercury), bands stay
		// Cool moon fill/rim on facing faces (top, valley side). Separate from sodium so it actually reads.
		col += alb * moon_color * moon_k * max(dot(n, normalize(moon_dir)), 0.0);
		float spec = pow(max(dot(n, normalize(l + v)), 0.0), spec_power);
		col += vec3(step(0.55, spec) * 0.32 * min(spec_scale, 1.0));
		vec3 r = reflect(-v, n);
		vec2 euv = vec2(atan(r.z, r.x) / 6.2831853 + 0.5, acos(clamp(r.y, -1.0, 1.0)) / 3.1415927);
		float fres = env_strength * pow(1.0 - max(dot(n, v), 0.0), 2.0) + 0.08;
		vec3 e = texture(env_equirect, euv).rgb * fres * env_tint;
		col += floor(e * 3.0 + 0.35) / 3.0 * 0.6;
	}
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(col, fog_color, f);
	}
}
