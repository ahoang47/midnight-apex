// CEL EXPERIMENT copy of the district post: same composite (nearest 640x480 scene, glow-only bloom, saturation,
// rear-view inset) plus a screen-space ink pass, then (flavour A) RGB555 + 4x4 Bayer or (flavour B) no dither.
// Ink: per 640x480 pixel, from a view-normal G-buffer and a packed linear-depth G-buffer of the same frame
// (rendered by the same shaders with CEL_GB = 1 / 2, so the rasterisation and PSX snap match exactly).
//   silhouette: a 4-neighbour is clearly farther  -> this pixel (the near side) is inked, so lines are 1 px, never doubled
//   crease    : normal turns hard vs the right/down neighbour at similar depth -> 1 px
// Lines fade into the district fog like everything else. Always 1 px at 640x480 (2 px in the 1280x960 frame).
shader_type canvas_item;
uniform sampler2D scene_tex : filter_nearest;
uniform sampler2D mirror_tex : filter_nearest;
uniform sampler2D glow_tex : filter_linear;
uniform sampler2D gn_tex : filter_nearest;   // main view normals
uniform sampler2D gd_tex : filter_nearest;   // main view depth
uniform sampler2D mn_tex : filter_nearest;   // rear-view normals
uniform sampler2D md_tex : filter_nearest;   // rear-view depth
uniform float bloom_k = 0.22;
uniform float sat = 1.05;
uniform vec2 res = vec2(640.0, 480.0);
uniform vec4 mirror_rect = vec4(224.0, 16.0, 192.0, 64.0);
uniform float mirror_flip = 1.0;
uniform float mirror_on = 1.0;
uniform float ink_on = 1.0;
uniform vec3 ink_col = vec3(0.016, 0.031, 0.063);   // dark navy, not pure black
uniform vec3 fog_color = vec3(0.043, 0.09, 0.169);
uniform float fog_near = 9.0;
uniform float fog_far = 78.0;
uniform float depth_rel = 0.045;
uniform float depth_abs = 0.12;
uniform float crease_dot = 0.72;
uniform float lap_k = 0.03;      // two-corner port: min break in 1/depth (relative) for a silhouette
uniform float ink_debug = 0.0;   // 1 = write the ink mask only (white = ink), for the playtest's flicker measure
uniform float dither_on = 1.0;
const float B[16] = float[](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);

float dec_depth(vec3 c) {
	if (c.b > 0.9) return 1000.0;   // background / sky (white in the G-buffer passes)
	float i = clamp(floor((c.r - 0.25) / 0.75 * 31.0 + 0.5), 0.0, 31.0);
	float f = clamp((c.g - 0.25) / 0.75, 0.0, 1.0);
	return 0.05 * exp((i + f) / 32.0 * log(10240.0));
}
vec3 dec_normal(vec3 c) { return normalize((c - 0.25) / 0.75 * 2.0 - 1.0); }
bool in_mirror(vec2 p) {
	return mirror_on > 0.5 && p.x >= mirror_rect.x && p.x < mirror_rect.x + mirror_rect.z && p.y >= mirror_rect.y && p.y < mirror_rect.y + mirror_rect.w;
}
// depth + normal at a 640x480 pixel, from the main or rear-view G-buffer (mirror flipped like its colour)
vec4 gb(vec2 p, bool mir) {
	vec2 uv;
	if (mir) {
		vec2 m = (p + 0.5 - mirror_rect.xy) / mirror_rect.zw;
		m = clamp(m, vec2(0.0), vec2(1.0));
		uv = vec2(mirror_flip > 0.5 ? 1.0 - m.x : m.x, m.y);
		return vec4(dec_normal(texture(mn_tex, uv).rgb), dec_depth(texture(md_tex, uv).rgb));
	}
	uv = (p + 0.5) / res;
	return vec4(dec_normal(texture(gn_tex, uv).rgb), dec_depth(texture(gd_tex, uv).rgb));
}
void fragment() {
	vec2 px = floor(UV * res);
	vec3 c = texture(scene_tex, (px + 0.5) / res).rgb;
	vec3 bl = vec3(0.0); float ws = 0.0;
	for (int j = -3; j <= 3; j++) for (int i = -3; i <= 3; i++) {
		vec2 o = vec2(float(i), float(j)) * 2.0; float w = exp(-dot(o, o) / 18.0);
		bl += texture(glow_tex, (px + 0.5 + o) / res).rgb * w; ws += w;
	}
	bool mir = in_mirror(px);
	if (mir) {
		vec2 m = (px + 0.5 - mirror_rect.xy) / mirror_rect.zw;
		c = texture(mirror_tex, vec2(mirror_flip > 0.5 ? 1.0 - m.x : m.x, m.y)).rgb;
	}
	float dbg = 0.0;
	if (ink_on > 0.5) {
		vec4 g0 = gb(px, mir);
		float ink = 0.0;
		float i0 = 1.0 / g0.w;
		float thr = max(depth_abs, g0.w * depth_rel);
		// TWO-CORNER PORT FIX: a silhouette also needs a real break in 1/depth (1/z is affine across a plane in screen
		// space, so its second difference is ~0 on any flat surface). Without this the grazing road in the rear-view
		// (and the far road near the horizon) filled solid with ink, because depth climbs fast from row to row there.
		for (int a = 0; a < 2; a++) {
			vec2 e = a == 0 ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
			bool okp = in_mirror(px + e) == mir; bool okn = in_mirror(px - e) == mir;   // never across the inset border
			vec4 gp = okp ? gb(px + e, mir) : g0; vec4 gn = okn ? gb(px - e, mir) : g0;
			float ip = 1.0 / gp.w; float inn = 1.0 / gn.w;
			if (!okp) ip = 2.0 * i0 - inn;
			if (!okn) inn = 2.0 * i0 - ip;
			bool brk = abs(ip + inn - 2.0 * i0) > lap_k * i0;
			if (brk && ((okp && gp.w - g0.w > thr) || (okn && gn.w - g0.w > thr))) ink = 1.0;   // a neighbour is farther: near side inked
			if (okp && abs(gp.w - g0.w) <= thr && dot(normalize(g0.xyz), normalize(gp.xyz)) < crease_dot) ink = 1.0;   // crease
		}
		if (g0.w > 400.0) ink = 0.0;   // sky / background never inked
		float f = clamp((g0.w - fog_near) / (fog_far - fog_near), 0.0, 1.0);
		ink *= 1.0 - smoothstep(0.55, 0.95, f);   // lines thin out into the fog instead of netting the distance
		c = mix(c, mix(ink_col, fog_color, f * 0.6), ink);
		dbg = ink;
	}
	c += bloom_k * bl / ws * (mir ? 0.0 : 1.0);
	float lum = dot(c, vec3(0.299, 0.587, 0.114)); c = vec3(lum) + (c - vec3(lum)) * sat;
	if (dither_on > 0.5) {
		int bi = int(mod(px.x, 4.0)) + int(mod(px.y, 4.0)) * 4;
		float b = B[bi] / 16.0 - 0.5;
		c = floor(clamp(c, 0.0, 1.0) * 31.0 + 0.5 + b) / 31.0;
	} else {
		c = clamp(c, 0.0, 1.0);
	}
	COLOR = ink_debug > 0.5 ? vec4(vec3(dbg), 1.0) : vec4(c, 1.0);
}
