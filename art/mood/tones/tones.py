"""Tone presets for the Midnight Apex mockups. Applied in-scene (fog, sky card, ambient vertex light, lamp-pool tint and
banding, glow-sprite tint) and before quantise (bloom amount, saturation); the HUD and RGB555 + Bayer + 2x post are unchanged.
'sodium' reproduces the current renders exactly."""
TONES = {
    'sodium':  dict(label='1 SODIUM (baseline)', fog='#261F38', zen='#050510', cityglow='#5A3440', amb='#8E90B4', amb_k=1.0,
                    lamps=['#FF9947'], lamp_k=0.85, pool_k=.14, steps=5, pool_tex_steps=4, glow_tex=None, bloom=(.35, .25), sat=1.0, ground_k=1.0, stars=(110, 105, 130)),
    'mercury': dict(label='2 MERCURY', fog='#0C1E22', zen='#010506', cityglow=None, amb='#5C8C98', amb_k=.85,
                    lamps=['#8CF0C4'], lamp_k=0.65, pool_k=.09, steps=3, pool_tex_steps=3, glow_tex='#B4FFDC', bloom=(.22, 0), sat=1.0, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, stars=(70, 100, 100)),
    'txr':     dict(label='3 TXR NAVY', fog='#0A1034', zen='#01020A', cityglow=None, amb='#4E5EA8', amb_k=.8,
                    lamps=['#FFFFFF', '#FF8A2A'], lamp_k=1.0, pool_k=.08, steps=3, pool_tex_steps=3, glow_tex='per-lamp', bloom=(.22, 0), sat=1.15, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, stars=(90, 100, 150)),
    'rain':    dict(label='4 RAIN-COLD', fog='#1C2228', zen='#06080B', cityglow=None, amb='#8894A4', amb_k=.9,
                    lamps=['#E8F0F8'], lamp_k=0.8, pool_k=.06, steps=3, pool_tex_steps=3, glow_tex='#F0F6FF', bloom=(.2, 0), sat=.55, ground_k=.62, ow_ground_lamp=.45, ow_pool_mul=2.6, stars=None),
    'dawn':    dict(label='5 DAWN PURPLE', fog='#2A1C44', zen='#0C0620', cityglow='#7A3458', amb='#8A7CC0', amb_k=1.05,
                    lamps=['#FF9947'], lamp_k=0.6, pool_k=.11, steps=3, pool_tex_steps=3, glow_tex='#FF9947', bloom=(.22, 0), sat=1.0, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, stars=(120, 100, 150)),
    # --- Mercury x TXR base blends: TXR navy world with Mercury teal mixed into fog / ambient / sky; one pale-sodium lamp colour
    'blend25': dict(label='A MOSTLY NAVY', fog='#0A1430', zen='#010309', cityglow=None, amb='#526AA4', amb_k=.8,
                    lamps=['#F0C894'], lamp_k=.85, pool_k=.09, steps=3, pool_tex_steps=3, glow_tex='per-lamp',
                    bloom=(.22, 0), sat=1.05, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, lane_ground_lamp=.55, lane_pool_mul=1.8, stars=(90, 100, 150)),
    'blend50': dict(label='B HALF TEAL', fog='#0B172B', zen='#010408', cityglow=None, amb='#5575A0', amb_k=.8,
                    lamps=['#F0C894'], lamp_k=.85, pool_k=.09, steps=3, pool_tex_steps=3, glow_tex='per-lamp',
                    bloom=(.22, 0), sat=1.05, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, lane_ground_lamp=.55, lane_pool_mul=1.8, stars=(90, 100, 150)),
    'blend75': dict(label='C TEAL-LEANING', fog='#0C1A26', zen='#010407', cityglow=None, amb='#58809C', amb_k=.8,
                    lamps=['#F0C894'], lamp_k=.85, pool_k=.09, steps=3, pool_tex_steps=3, glow_tex='per-lamp',
                    bloom=(.22, 0), sat=1.05, ground_k=1.0, ow_ground_lamp=.45, ow_pool_mul=2.6, lane_ground_lamp=.55, lane_pool_mul=1.8, stars=(90, 100, 150)),
}
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
