// CEL EXPERIMENT copy: unchanged look; far depth in the G-buffer passes.
// Painted sky cylinder (B.1): follows the camera, no fog; the sky strip's lower half is the fog colour.
// The skyline/ridge band is composited here (same cylinder) so draw order can't hide it (Three.js draws it as a second mesh).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;
#include "res://shaders/cel.gdshaderinc"
uniform sampler2D tex : filter_linear, repeat_enable;
uniform sampler2D band_tex : filter_linear, repeat_enable;
uniform float y0 = -125.0;      // sky cylinder extent (v = 1 at y0, 0 at y1)
uniform float y1 = 125.0;
uniform float band_y0 = -3.125; // band (r 240, y -3..22) projected onto the r 250 sky: x 250/240
uniform float band_y1 = 22.917;
uniform float band_rep = 5.0;
void fragment() {
	vec3 c = texture(tex, fract(UV)).rgb;
	if (cel_on * cel_soft > 0.5) {   // CEL A SOFT: de-dither the painted 5-bit sky into a smooth gradient (stars kept), so the
		vec2 ts = 1.0 / vec2(textureSize(tex, 0));   // final RGB555 + Bayer pass dithers one smooth ramp, not the texture's steps
		vec3 avg = vec3(0.0);
		for (int j = -2; j <= 2; j++) for (int i = -1; i <= 1; i++) avg += texture(tex, fract(UV + vec2(float(i) * 2.0, float(j) * 1.5) * ts)).rgb;
		avg /= 15.0;
		vec3 det = c - avg;
		c = avg + det * smoothstep(0.08, 0.16, length(det));
	}
	float y = mix(y1, y0, UV.y);
	float vb = (band_y1 - y) / (band_y1 - band_y0);
	if (vb >= 0.0 && vb < 1.0) {
		vec4 b = texture(band_tex, vec2(fract(UV.x * band_rep), vb));
		if (b.a >= 0.5) c = b.rgb;
	}
	ALBEDO = c;
	if (CEL_GB > 1.5) ALBEDO = vec3(1.0);
	else if (CEL_GB > 0.5) ALBEDO = cel_pack_normal(vec3(0.0, 0.0, 1.0));
}
