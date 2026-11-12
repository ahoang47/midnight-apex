shader_type canvas_item;
uniform sampler2D scene_tex : filter_nearest;
uniform sampler2D mirror_tex : filter_nearest;
uniform sampler2D glow_tex : filter_linear;
uniform float bloom_k = 0.22;
uniform float sat = 1.05;
uniform vec2 res = vec2(640.0, 480.0);
uniform vec4 mirror_rect = vec4(224.0, 16.0, 192.0, 64.0);
uniform float mirror_on = 1.0;
uniform float quantize = 1.0;
const float B[16] = float[](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);
void fragment() {
	vec2 uv = UV;
	vec2 base = uv * vec2(640.0, 480.0);
	vec2 px = floor(uv * res);
	vec3 c = texture(scene_tex, (px + 0.5) / res).rgb;
	vec3 bl = vec3(0.0); float ws = 0.0;
	for (int j = -3; j <= 3; j++) for (int i = -3; i <= 3; i++) {
		vec2 o = vec2(float(i), float(j)) * 2.0; float w = exp(-dot(o, o) / 18.0);
		bl += texture(glow_tex, (px + 0.5 + o) / res).rgb * w; ws += w;
	}
	c += bloom_k * bl / ws;
	float lum = dot(c, vec3(0.299, 0.587, 0.114)); c = vec3(lum) + (c - vec3(lum)) * sat;
	if (mirror_on > 0.5 && base.x >= mirror_rect.x && base.x < mirror_rect.x + mirror_rect.z && base.y >= mirror_rect.y && base.y < mirror_rect.y + mirror_rect.w) {
		vec2 m = (base - mirror_rect.xy) / mirror_rect.zw;
		c = texture(mirror_tex, vec2(1.0 - m.x, m.y)).rgb;
	}
	if (quantize > 0.5) {
		int bi = int(mod(px.x, 4.0)) + int(mod(px.y, 4.0)) * 4;
		float b = B[bi] / 16.0 - 0.5;
		c = floor(clamp(c, 0.0, 1.0) * 31.0 + 0.5 + b) / 31.0;
	}
	COLOR = vec4(c, 1.0);
}
