// District mockup copy of car.gdshader + one faked rear light (a chasing car's headlights, touge mouse view).
// Faked shine (art_direction A.4/A.8) + PSX vertex snap + affine UVs. Unshaded: no scene lights.
shader_type spatial;
render_mode unshaded, cull_back, fog_disabled;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;  // Q4 resolved 2026-11-11: smooth filtering (A.8 sketch samples with mipmaps)
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
uniform vec3 fog_color : source_color = vec3(0.043, 0.051, 0.102);
uniform float fog_near = 30.0;
uniform float fog_far = 140.0;
uniform vec3 rear_pos = vec3(0.0, -1000.0, 0.0);   // world position of the chaser's headlight pair centre
uniform vec3 rear_dir = vec3(0.0, 0.0, -1.0);       // chaser's forward (unit, world)
uniform vec3 rear_col = vec3(1.0, 0.94, 0.82);      // halogen white, not the sodium street colour
uniform float rear_k = 0.0;
uniform float rear_range = 14.0;
varying vec3 uvw; varying vec3 wn; varying vec3 wv; varying vec3 wp; varying float fog_depth;
void vertex() {
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wv = wp - CAMERA_POSITION_WORLD;
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
	vec2 uv = uvw.xy / uvw.z;
	vec3 n = normalize(wn); vec3 l = normalize(key_dir); vec3 v = -normalize(wv);
	vec3 alb = (has_tex ? texture(albedo_tex, uv).rgb : base_col) * tint;
	vec3 col;
	if (emissive) { col = alb * 1.4; }
	else {
		float diff = ambient + max(dot(n, l), 0.0) * (1.0 - ambient);
		float spec = pow(max(dot(n, normalize(l + v)), 0.0), spec_power) * spec_scale;
		vec3 r = reflect(-v, n);
		vec2 euv = vec2(atan(r.z, r.x) / 6.2831853 + 0.5, acos(clamp(r.y, -1.0, 1.0)) / 3.1415927);
		float fres = env_strength * pow(1.0 - max(dot(n, v), 0.0), 2.0) + 0.08;
		col = alb * diff + vec3(spec) + texture(env_equirect, euv).rgb * fres * env_tint;  // cool env tint on glass + paint (A.4.2, car READMEs)
	}
	if (rear_k > 0.0 && !emissive) {
		// faked headlight from behind: lambert toward the lamp x cone around the chaser's forward x distance falloff,
		// stepped into 3 bands so it reads as painted PSX light, not a smooth modern spot.
		vec3 tl = rear_pos - wp; float dist = length(tl); vec3 ld = tl / max(dist, 0.001);
		float lam = max(dot(n, ld), 0.0);
		float cone = smoothstep(0.55, 0.95, dot(-ld, normalize(rear_dir)));
		float fall = clamp(1.0 - dist / rear_range, 0.0, 1.0);
		float k = lam * cone * fall;
		k = floor(k * 3.0 + 0.5) / 3.0;
		col += alb * rear_col * rear_k * k + rear_col * rear_k * 0.25 * k * pow(max(dot(reflect(-ld, n), v), 0.0), 12.0);
	}
	float f = clamp((fog_depth - fog_near) / (fog_far - fog_near), 0.0, 1.0);
	ALBEDO = mix(col, fog_color, f);
}
