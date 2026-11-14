// Cel-shaded experiment (unapproved): shared toon ramp + G-buffer output for the screen-space ink pass.
// cel_gbuf (project global): 0 = colour, 1 = view-space normal pass, 2 = linear depth pass (packed 24-bit).
global uniform float cel_gbuf;
const vec3 CEL_KEY = vec3(0.4, 0.8, 0.3);          // same key direction as the car shading (display.json car_shading.key_dir)
const vec3 CEL_SHADOW_TINT = vec3(0.80, 0.88, 1.06); // shadow band leans to TXR navy, never warm

// The Compatibility colour buffer is not linear in the darks (0.04 reads back as 4/255), so every G-buffer value is
// kept in 0.25..1.0. Depth: log-mapped 0.05..512 m, coarse index (32 levels) in R, fine fraction in G (~0.15 % steps).
vec3 cel_pack_depth(float d) {
	float lx = clamp(log(max(d, 0.05) / 0.05) / log(10240.0), 0.0, 0.9999);
	float i = floor(lx * 32.0);
	return vec3(0.25 + 0.75 * i / 31.0, 0.25 + 0.75 * fract(lx * 32.0), 0.25);
}
vec3 cel_pack_normal(vec3 n) { return 0.25 + 0.75 * (n * 0.5 + 0.5); }
// 3 hard bands: lit 1.0 / mid / shadow. No smoothstep: the steps are the look.
vec3 cel_ramp(vec3 alb, float ndl, float k_mid, float k_shadow) {
	if (ndl > 0.42) return alb;
	if (ndl > -0.05) return alb * k_mid;
	return alb * k_shadow * CEL_SHADOW_TINT;
}
// faceted view-space normal from screen derivatives (works on the normal-less road / band strips too), facing the camera
vec3 cel_face_normal(vec3 vpos) {
	vec3 n = normalize(cross(dFdx(vpos), dFdy(vpos)));
	if (dot(n, -vpos) < 0.0) n = -n;
	return n;
}
// flatten painted albedo (baked AO / gradients) into sqrt-luma steps, hue kept
vec3 cel_poster(vec3 c) {
	float l = max(dot(c, vec3(0.299, 0.587, 0.114)), 1e-4);
	float lq = max(pow(floor(sqrt(l) * 7.0 + 0.5) / 7.0, 2.0), 0.01);
	return c * (lq / l);
}
