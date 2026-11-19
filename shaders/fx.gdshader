// Car FX glow quads (MX5_FX_LampGlow): additive, unshaded, texture alpha drives the amount (A.4.3).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
uniform sampler2D tex : filter_linear;
uniform float strength = 1.0;
void fragment() { vec4 t = texture(tex, UV); ALBEDO = t.rgb * t.a * strength; }
