shader_type canvas_item;
uniform sampler2D src : filter_nearest;
uniform vec2 res = vec2(640.0, 480.0);
const float B[16] = float[](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);
void fragment() {
	vec2 px = floor(UV * res);
	vec3 c = texture(src, (px + 0.5) / res).rgb;
	int bi = int(mod(px.x, 4.0)) + int(mod(px.y, 4.0)) * 4;
	float b = B[bi] / 16.0 - 0.5;
	c = floor(clamp(c, 0.0, 1.0) * 31.0 + 0.5 + b) / 31.0;
	COLOR = vec4(c, 1.0);
}
