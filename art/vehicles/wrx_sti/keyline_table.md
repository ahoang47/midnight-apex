# WRX STI (GD, 2001-02) - key-line table (clay vs blueprint)

Blueprint: the-blueprints.com "Subaru Impreza WRX (2001)", 1280x906 px, 1:25; S = 4.405 m / 770 px = 5.721 mm/px.
All "blueprint" values are traced lines (bp/curves.json). Nothing is from photos. ESTIMATED marks every invented number.

IoU (blueprint frame): aero region masked (gate) {'side': 0.984, 'top': 0.9777, 'front': 0.9613, 'rear': 0.9606} - mono STI as exported, unmasked {'side': 0.9731, 'top': 0.9747, 'front': 0.9603, 'rear': 0.9469} - no aero parts {'side': 0.9757, 'top': 0.9783, 'front': 0.9619, 'rear': 0.9488} - base WRX scoop+spoiler {'side': 0.981, 'top': 0.9783, 'front': 0.9619, 'rear': 0.9488}. Gate PASS.

Steering/suspension clearance: all clear; tightest {'gap_m': 0.0181, 'pose': 'steer -30 deg, travel +0.065', 'corner': 'RL', 'against': 'WRX_Liner_RL'}

| group | line | clay | blueprint | note |
|---|---|---|---|---|
| overall | length (m) | 4.395 | 4.405 | sheet L 4405 = scale reference (5.721 mm/px over 770 px) |
| overall | wheelbase (m) | 2.494 | 2.494 | traced from the contact patches; sheet says 2.525 (drawing is 1.2 % short) - traced value kept for the IoU gate |
| overall | body width (m) | 1.743 | 1.730 | front/rear views .87 half-width; top view reads .90 at the flares (clamped to .872) |
| overall | roof height (m) | 1.468 | 1.493 | side silhouette 1.465-1.47 (+ a 2.5 cm roof nub at x -.15..-.3 not modelled); sheet H 1440 (drawing ~2 % tall) |
| overall | front overhang (m) | 0.933 | 0.935 |  |
| overall | rear overhang (m) | 0.968 | 0.970 |  |
| overall | track F / R (m) | 1.485 / 1.475 | 1.485-1.490 / 1.475-1.480 | sheet values |
| hood / fender | hood line z at x 1.8 | 0.861 | 0.861 | side paint top (scoop + mirror are dark so excluded) |
| hood / fender | hood line z at x 1.4 | 0.922 | 0.911 | side paint top (scoop + mirror are dark so excluded) |
| hood / fender | hood line z at x 1.0 | 0.961 | 0.958 | side paint top (scoop + mirror are dark so excluded) |
| greenhouse | DLO bottom / top at x 0.3 | 0.952 / 1.315 | 0.955/1.356 | side glass columns, smoothed; pillars interpolated |
| greenhouse | DLO bottom / top at x 0.0 | 0.965 / 1.319 | 0.967/1.333 | side glass columns, smoothed; pillars interpolated |
| greenhouse | DLO bottom / top at x -0.5 | 0.986 / 1.332 | 0.984/1.350 | side glass columns, smoothed; pillars interpolated |
| greenhouse | DLO bottom / top at x -0.9 | 1.003 / 1.340 | 1.007/1.230 | side glass columns, smoothed; pillars interpolated |
| greenhouse | side glass region ws x | 0.295..0.861 | same | classification boundary (cabin faces) |
| greenhouse | side glass region rear_door x | -1.010..-0.318 | same | classification boundary (cabin faces) |
| greenhouse | side glass region front_door x | -0.283..0.449 | same | classification boundary (cabin faces) |
| greenhouse | side glass region rear_glass x | -1.559..-1.073 | same | classification boundary (cabin faces) |
| greenhouse | windshield base x (centre) | 0.930 | 0.924 | top view glass |
| greenhouse | rear glass base x / z | -1.575 / 1.060 | -1.565 / 1.06 | top view glass end / side view deck |
| greenhouse | roof z at x -0.5 | 1.468 | 1.470 |  |
| body | sill z at x 0 | 0.187 | 0.199 |  |
| body | front arch circle (xc, zc, r) | 1.245, 0.349, 0.378 | fit | least-squares fit to the arch paint edge x 0.88..1.62 |
| body | rear arch circle (xc, zc, r) | -1.251, 0.344, 0.362 | fit | least-squares fit to the arch paint edge x -1.61..-0.90 |
| body | deck z at x -1.85 (under spoiler) | 1.058 | ~1.06 | side: lip spoiler removed, deck read under it (ESTIMATE where the spoiler hides it) |
| lamps | front lens (y, z) | -0.70..-0.49, 0.59..0.80 | decal = blueprint hull | round headlamps z .6-.8, fogs z .37-.50 |
| lamps | front lens (y, z) | 0.49..0.71, 0.59..0.80 | decal = blueprint hull | round headlamps z .6-.8, fogs z .37-.50 |
| lamps | front lens (y, z) | -0.68..-0.55, 0.37..0.50 | decal = blueprint hull | round headlamps z .6-.8, fogs z .37-.50 |
| lamps | front lens (y, z) | 0.57..0.68, 0.38..0.49 | decal = blueprint hull | round headlamps z .6-.8, fogs z .37-.50 |
| parts | WRX scoop (blueprint) | x 1.25-1.48, y +-.30, h .062 | side x 1.23-1.48 top .98, top view y +-.30 | base-WRX part, hidden in the STI build |
| parts | WRX lip spoiler (blueprint) | x -1.70..-2.075, top 1.135, span +-.66 | side tip (-2.065, 1.135) | span ESTIMATED from the rear view band |
| parts | STI scoop | x 1.19-1.515, y +-.34, h .088 | - | ESTIMATED (GDB scoop larger than the GD WRX one; not on the sheet) |
| parts | STI wing | chord x -1.87..-2.145, top 1.258, span +-.70, uprights y +-.52 | - | ESTIMATED (tall pedestal wing, proportions only) |
| parts | STI front lip | 3 cm proud of the bumper bottom, z ZB-.022..+.012 | - | ESTIMATED |
| wheels | tyre | OD 0.634 / W 0.225 / rim 0.432 | blueprint wheel ~.63 OD | STI 225/45R17 (WRX 205/55R16 would be OD .632) |
| rig | travel bump / droop | +0.065 / -0.08 | - | ESTIMATED: front arch lip gap .095 over the tyre |
| rig | steering lock | +-30 deg | - | brief value (GD real ~33/28 deg in/out, ~10.6 m kerb circle) |
