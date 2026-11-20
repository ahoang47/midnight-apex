// B.2b live night lighting (Arthur, design/art/art_direction.md). Ported from turnout_godot_scratch.
uniform mat4 lamps0;
uniform mat4 lamps1;
uniform mat4 lamps2;
uniform mat4 lamps3;
uniform float lamp_count = 0.0;
uniform vec3 lamp_color : source_color = vec3(0.941176, 0.784314, 0.580392); // #F0C894 sodium
uniform vec3 mercury_color : source_color = vec3(0.658824, 0.878431, 0.831373); // #A8E0D4 mercury vapor
uniform float lamp_intensity = 1.05;
uniform float lamp_range = 16.0;
uniform vec3 ambient_col : source_color = vec3(0.333333, 0.458824, 0.627451); // #5575A0 night navy
uniform float ambient_k = 0.56;
uniform float unbake = 0.0; // 1 = equalize baked pool luma on soft surfaces before live light
uniform float live_light = 1.0; // 0 = skip (Emit_ heads stay full-bright)
uniform float light_mix = 1.0; // 1 = full Gouraud, <1 keeps some unlit albedo (paint)
// Fixed moon: cool blue-white directional fill / rim. Sodium stays the key light.
uniform vec3 moon_dir = vec3(0.383, 0.643, -0.663); // 40° elevation, 30° behind valley side
uniform vec3 moon_color : source_color = vec3(0.561, 0.659, 0.847); // #8FA8D8
uniform float moon_k = 1.30; // B.2b approved fill (script also sets this)

vec3 vl_pos(int i) {
	int b = i / 4;
	int c = i - b * 4;
	mat4 m = lamps0;
	if (b == 1) m = lamps1;
	else if (b == 2) m = lamps2;
	else if (b == 3) m = lamps3;
	return m[c].xyz;
}

float vl_kind(int i) {
	int b = i / 4;
	int c = i - b * 4;
	mat4 m = lamps0;
	if (b == 1) m = lamps1;
	else if (b == 2) m = lamps2;
	else if (b == 3) m = lamps3;
	return m[c].w;
}

vec3 vl_eval(vec3 wp, vec3 wn) {
	vec3 n = normalize(wn);
	vec3 lit = ambient_col * ambient_k;
	int nlamps = int(lamp_count + 0.5);
	nlamps = clamp(nlamps, 0, 16);
	for (int i = 0; i < 16; i++) {
		if (i >= nlamps) break;
		vec3 L = vl_pos(i) - wp;
		float d = length(L);
		vec3 ld = L / max(d, 1e-4);
		float x = d / max(lamp_range, 0.01);
		float att = 1.0 / (1.0 + 1.8 * x * x);
		att *= 1.0 - smoothstep(0.84, 1.20, x);
		float ndl = 0.50 + 0.50 * max(dot(n, ld), 0.0);
		// w of the packed position selects sodium (0) or mercury (1)
		float kind = vl_kind(i);
		vec3 lcol = mix(lamp_color, mercury_color, kind);
		lit += lcol * lamp_intensity * att * ndl;
	}
	// Directional moon fill with a little wrap (moon is a large sky source, not a hard sun).
	// Facing surfaces and the ground plane lift; sodium pools stay the warm key.
	vec3 md = normalize(moon_dir);
	float ndm = max(dot(n, md), 0.0);
	float moon_term = 0.20 + 0.80 * ndm;
	lit += moon_color * moon_k * moon_term;
	return lit;
}

vec3 vl_unbake(vec3 c, float target_luma) {
	if (unbake < 0.01) return c;
	float l = max(dot(c, vec3(0.299, 0.587, 0.114)), 1e-4);
	return c * mix(1.0, target_luma / l, unbake);
}

vec3 vl_apply(vec3 alb, vec3 lit) {
	return alb * mix(vec3(1.0), lit, light_mix);
}
