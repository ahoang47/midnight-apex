// Painted sky cylinder (B.1): follows the camera, no fog; the sky strip's lower half is the fog colour.
// The skyline/ridge band is composited here (same cylinder) so draw order can't hide it (Three.js draws it as a second mesh).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, fog_disabled, shadows_disabled;
uniform sampler2D tex : filter_linear, repeat_enable;
uniform sampler2D band_tex : filter_linear, repeat_enable;
uniform float y0 = -125.0;      // sky cylinder extent (v = 1 at y0, 0 at y1)
uniform float y1 = 125.0;
uniform float band_y0 = -3.125; // band (r 240, y -3..22) projected onto the r 250 sky: x 250/240
uniform float band_y1 = 22.917;
uniform float band_rep = 5.0;
void fragment() {
	vec3 c = texture(tex, fract(UV)).rgb;
	float y = mix(y1, y0, UV.y);
	float vb = (band_y1 - y) / (band_y1 - band_y0);
	if (vb >= 0.0 && vb < 1.0) {
		vec4 b = texture(band_tex, vec2(fract(UV.x * band_rep), vb));
		if (b.a >= 0.5) c = b.rgb;
	}
	ALBEDO = c;
}
