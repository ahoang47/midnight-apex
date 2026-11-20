// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
#include "res://shaders/cel.gdshaderinc"
#include "res://shaders/vertex_lights.gdshaderinc"
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform sampler2D tex : filter_linear, repeat_enable;
uniform float scroll_m = 0.0;
uniform float tile = 8.0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.09, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform float fog_amount = 1.0;
uniform float gain = 1.0;
uniform float cel_k = 1.0;
uniform float flatten = 1.0;
uniform float flat_radius = 4.0;
uniform float flat_keep = 0.11;
uniform float poster = 10.0;
uniform float soft_surface = 0.0;
uniform float soft_radius = 12.0;
uniform float soft_clamp_u = 0.0;
uniform float k_mid = 0.80;
uniform float k_shadow = 0.60;
varying float fog_depth; varying vec3 uvw; varying vec3 vlight;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	if (length(wn) < 0.01) wn = vec3(0.0, 1.0, 0.0);
	vlight = (live_light > 0.5) ? vl_eval(wp, wn) : vec3(1.0);
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
	if (t.a < 0.5) discard;
	if (CEL_GB > 1.5) { ALBEDO = cel_pack_depth(fog_depth); }
	else if (CEL_GB > 0.5) { ALBEDO = cel_pack_normal(cel_face_normal(VERTEX)); }
	else {
		vec3 c = t.rgb;
		float sk = soft_surface * cel_soft * cel_on;
		if (flatten * cel_on > 0.0) {
			float r = mix(flat_radius, soft_radius, sk);
			vec2 tsz = vec2(textureSize(tex, 0));
			vec2 ts = r / tsz;
			vec3 sm[17]; sm[0] = c; vec3 avg = c;
			int nt = sk > 0.5 ? 17 : 9;
			for (int i = 1; i < 17; i++) {
				if (i >= nt) break;
				float a = float(i) * 0.7853982 + (i > 8 ? 0.3927 : 0.0);
				vec2 q = uv + vec2(cos(a), sin(a)) * ts * (i > 8 ? 0.5 : 1.0);
				q = soft_clamp_u > 0.5 && sk > 0.5 ? vec2(clamp(fract(uv.x) + (q.x - uv.x), 0.5 / tsz.x, 1.0 - 0.5 / tsz.x), fract(q.y)) : fract(q);
				sm[i] = texture(tex, q).rgb; avg += sm[i];
			}
			avg /= float(nt);
			vec3 base = vec3(0.0); float wsum = 0.0;
			for (int i = 0; i < 17; i++) { if (i >= nt) break; float w = step(length(sm[i] - avg), 0.12); base += sm[i] * w; wsum += w; }
			base = wsum > 0.0 ? base / wsum : avg;
			vec3 det = c - base;
			float keep = smoothstep(flat_keep, flat_keep * 1.8, length(det));
			if (poster > 0.0 && sk < 0.5) {
				float l = max(dot(base, vec3(0.299, 0.587, 0.114)), 1e-4);
				float lq = max(pow(floor(sqrt(l) * poster + 0.5) / poster, 2.0), 0.004);
				base *= lq / l;
			}
			c = mix(c, base + det * keep, flatten * cel_on);
		}
		c *= gain;
		if (sk > 0.5) {
			c = vl_unbake(c, 0.14);
		}
		if (cel_k * cel_on * (1.0 - sk) > 0.0) {
			vec3 nw = normalize((INV_VIEW_MATRIX * vec4(cel_face_normal(VERTEX), 0.0)).xyz);
			c = mix(c, cel_ramp(c, dot(nw, normalize(CEL_KEY)), k_mid, k_shadow), cel_k * cel_on * (1.0 - sk));
		}
		c *= vlight;
		float f = fog_amount * clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
		ALBEDO = mix(c, fog_color, f);
	}
}
