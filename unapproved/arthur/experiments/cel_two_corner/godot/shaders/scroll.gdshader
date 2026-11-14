// CEL EXPERIMENT copy of the scrolling-strip / card / prop shader: same PSX vertex snap, affine UVs and fog, plus
// (1) edge-preserving flatten: texture grain pulled toward its local average, strong painted marks (lane lines,
//     signs, window frames) kept; (2) 3-band toon ramp from faceted normals vs one fixed key; (3) G-buffer out.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
#include "res://shaders/cel.gdshaderinc"
uniform vec2 snap_res = vec2(320.0, 240.0);
uniform sampler2D tex : filter_linear, repeat_enable;
uniform float scroll_m = 0.0;
uniform float tile = 8.0;
uniform vec3 fog_color : source_color = vec3(0.043, 0.051, 0.102);
uniform float fog_near = 30.0;
uniform float fog_far = 140.0;
uniform float fog_amount = 1.0;
uniform float gain = 1.0;
uniform float cel_k = 1.0;        // 0 = full-bright (Emit_ surfaces, lamp heads), 1 = toon ramp
uniform float flatten = 1.0;      // 0 = original texture, 1 = flattened
uniform float flat_radius = 4.0;  // texels
uniform float flat_keep = 0.11;   // detail above this contrast is kept (painted marks)
uniform float poster = 10.0;      // sqrt-luma steps on the flattened base (0 = off): flat value blocks, hue kept
uniform float k_mid = 0.80;
uniform float k_shadow = 0.60;
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
	if (t.a < 0.5) discard;
	if (CEL_GB > 1.5) { ALBEDO = cel_pack_depth(fog_depth); }
	else if (CEL_GB > 0.5) { ALBEDO = cel_pack_normal(cel_face_normal(VERTEX)); }
	else {
		vec3 c = t.rgb;
		if (flatten * cel_on > 0.0) {
			// ring of 8 taps at flat_radius texels; taps far from the ring mean are rejected (so a thin painted line
			// near a pixel cannot halo it), the base is posterised in sqrt-luma steps, strong marks are added back.
			vec2 ts = flat_radius / vec2(textureSize(tex, 0));
			vec3 sm[9]; sm[0] = c; vec3 avg = c;
			for (int i = 1; i < 9; i++) {
				float a = float(i) * 0.7853982;
				sm[i] = texture(tex, fract(uv + vec2(cos(a), sin(a)) * ts)).rgb; avg += sm[i];
			}
			avg /= 9.0;
			vec3 base = vec3(0.0); float wsum = 0.0;
			for (int i = 0; i < 9; i++) { float w = step(length(sm[i] - avg), 0.12); base += sm[i] * w; wsum += w; }
			base = wsum > 0.0 ? base / wsum : avg;
			vec3 det = c - base;
			float keep = smoothstep(flat_keep, flat_keep * 1.8, length(det));
			if (poster > 0.0) {
				float l = max(dot(base, vec3(0.299, 0.587, 0.114)), 1e-4);
				float lq = max(pow(floor(sqrt(l) * poster + 0.5) / poster, 2.0), 0.004);
				base *= lq / l;
			}
			c = mix(c, base + det * keep, flatten * cel_on);
		}
		c *= gain;
		if (cel_k * cel_on > 0.0) {
			vec3 nw = normalize((INV_VIEW_MATRIX * vec4(cel_face_normal(VERTEX), 0.0)).xyz);
			c = mix(c, cel_ramp(c, dot(nw, normalize(CEL_KEY)), k_mid, k_shadow), cel_k * cel_on);
		}
		float f = fog_amount * clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
		ALBEDO = mix(c, fog_color, f);
	}
}
