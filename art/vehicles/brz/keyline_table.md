# BRZ clay - key-line table (pass 4)

Units: metres. x = forward from mid-wheelbase (axles +-1.2875), y = left, z = height above ground.
"blueprint" = the traced the-blueprints.com line (14 mm/px; bp/extract.py -> bp/curves.json, renders/brz_bp_line_classification_p4_800.jpg).
Pass 4 takes every number from the blueprint. The photos are used only as a visual check of surface character.

## Lesson (corrects passes 2-3)

Passes 2 and 3 said "the blueprint draws the nose, hood and tail 3-9 cm high, photo wins". That was wrong. The blueprint does not disagree with itself:
- The side photo camera solve reads the car about 4% small: roof 1.256 vs 1.310 published and 1.305 on the blueprint, while the blueprint wheelbase is 2.562 vs 2.575 published. The camera also sits low (0.38 m), so its top edge over the roof is the near roof edge and its hood edge is the fender line seen from below. Heights read through it came out 3-9 cm low everywhere: roof 1.26 vs 1.30, deck .92-.96 vs 1.00-1.03, fender peaks .87 vs .91. The photo-vs-clay sheets still use those cameras, so their red outline now sits outside the photo car; read them for surface character only.
- The window lines were misread. In the side view, the outline over the windshield and rear glass is the silhouette. The windshield shows as a thin white strip under it, and the door glass (DLO) is a separate region whose front tip sits at the A-pillar base (x ~.5, z .90), not under the windshield. The rear glass is a thin white wedge under the outline, with the C-pillar and hips drawn in blue below it. Reading those as one window put the belt 3 cm low, the DLO top 5 cm low and the rear glass base 9 cm low.
- Pass 4 rebuilds the S2000 way. Silhouette and feature curves are traced straight from the four blueprint views. Every station is fitted to plan width W(x), side top/bottom and belt height; the rear zone and greenhouse are generated from blueprint lines. The gate is IoU in the blueprint's own frame (bp/bpcompare.py: no bbox fitting).

| group | key line | x | clay | blueprint | d (cm) | note |
|---|---|---:|---:|---:|---:|---|
| greenhouse | roof centre line | -0.300 | 1.305 | 1.305 | +0.0 | side silhouette 1.30-1.31 from x 0 to -0.65 (rear view 1.29-1.30) |
| greenhouse | windshield header, centre (x) | +0.140 | 0.140 | 0.140 | +0.0 | top view: glass ends x .13-.14 at the centre, (.25, .61) at the corners |
| greenhouse | windshield top corner z | +0.250 | 1.202 | 1.190 | +1.2 | front view: glass hw .53 at z 1.19 |
| greenhouse | windshield base, centre (x) | +0.765 | 0.765 | 0.760 | +0.5 | top view base arc: centre .76, (.73, .35), (.70, .45), (.62, .65), corner (.59, .67) |
| greenhouse | windshield base corner (y) | +0.600 | 0.680 | 0.670 | +1.0 | top view: max glass hw .67-.68 at x .45-.59 |
| greenhouse | DLO front tip (A-pillar base) x | +0.500 | 0.500 | 0.500 | +0.0 | side: A-pillar inner edge meets the belt at x ~.5 (the mirror sits on that corner) |
| greenhouse | beltline / DLO bottom | +0.000 | 0.902 | 0.902 | +0.0 | side: .90-.915 from x .5 to -.35 |
| greenhouse | beltline / DLO bottom | -0.450 | 0.915 | 0.915 | +0.0 | side: .915-.93 from -.35 to -.8 |
| greenhouse | DLO bottom at the quarter-glass tail | -0.920 | 0.985 | 0.985 | +0.0 | side: belt kicks up to .985 at x -.915 |
| greenhouse | DLO top over the door | -0.200 | 1.200 | 1.196 | +0.4 | side: 1.196 from -.15 to -.4 |
| greenhouse | DLO top at the quarter-glass tail | -0.925 | 1.040 | 1.042 | -0.2 | side: falls 1.17 (-.55) -> 1.11 (-.75) -> 1.04 (-.915) |
| greenhouse | side glass plan y, outer (base) | -0.450 | 0.735 | 0.732 | +0.3 | top view outer edge .725-.739 |
| greenhouse | side glass plan y, inner (glass top) | -0.450 | 0.645 | 0.645 | +0.0 | top view inner edge .64-.655 |
| greenhouse | rear glass top, centre z | -0.970 | 1.229 | 1.235 | -0.6 | side outline at x -.97; rear view glass top 1.20 |
| greenhouse | rear glass base, centre (x) | -1.580 | -1.580 | -1.577 | -0.3 | top view |
| greenhouse | rear glass base, centre z | -1.580 | 1.024 | 1.035 | -1.1 | rear view glass bottom 1.035; side 1.028-1.036 |
| greenhouse | rear glass half-width | -1.200 | 0.480 | 0.490 | -1.0 | top view .49-.50 from -1.03 to -1.37; rear view .47-.50 |
| greenhouse | rear-view cabin half-width at z 1.13 |  | 0.686 | 0.690 | -0.4 | rear outline |
| greenhouse | rear-view cabin half-width at z 1.01 |  | 0.732 | 0.746 | -1.4 | cabin flank flows into the hips (no shelf) |
| body | fender peak (p6) | +1.800 | 0.754 | 0.756 | -0.2 | hood centre 0.723 = 3.1 cm under the peak |
| body | fender peak (p6) | +1.650 | 0.820 | 0.820 | -0.0 | hood centre 0.790 = 3.0 cm under the peak |
| body | fender peak (p6) | +1.450 | 0.841 | 0.841 | +0.0 | hood centre 0.813 = 2.8 cm under the peak |
| body | fender peak (p6) | +1.200 | 0.883 | 0.883 | +0.0 | hood centre 0.861 = 2.2 cm under the peak |
| body | fender peak (p6) | +0.950 | 0.911 | 0.911 | +0.0 | hood centre 0.899 = 1.2 cm under the peak |
| body | cowl / hood centre at the windshield | +0.780 | 0.906 | 0.930 | -2.4 | front view: the windshield bottom is hidden below z ~.93-.96 |
| body | nose tip x |  | 2.167 | 2.168 | -0.1 | side + top |
| body | nose top at x 2.05 | +2.050 | 0.635 | 0.634 | +0.0 |  |
| body | rocker bottom | +0.000 | 0.152 | 0.155 | -0.3 | side .148-.162 |
| body | deck centre | -1.750 | 0.999 | 1.009 | -1.0 |  |
| body | ducktail lip | -2.000 | 0.993 | 0.992 | +0.1 | rear face vertical at x -2.03 from .99 down to .67 |
| body | tail tip x (lower trim) |  | -2.123 | -2.126 | +0.3 | bumper -2.10 at z .49-.66, trim -2.12 at .30-.45 |
| plan | half-width, front fenders | +1.000 | 0.908 | 0.915 | -0.7 | top view (incl. stroke) |
| plan | half-width, doors / cabin | +0.000 | 0.894 | 0.901 | -0.7 | top view (incl. stroke) |
| plan | half-width, hips | -1.450 | 0.922 | 0.929 | -0.7 | top view (incl. stroke) |
| plan | half-width, tail | -1.900 | 0.764 | 0.774 | -1.1 | top view (incl. stroke) |
| plan | half-width, tail | -2.000 | 0.651 | 0.647 | +0.4 | top view (incl. stroke) |
| plan | rear-view hip half-width at z .61 |  | 0.918 | 0.915 | +0.4 | widest body point |
| plan | rear-view shoulder half-width at z .93 |  | 0.830 | 0.816 | +1.4 | hip shoulder |
| features | taillight, side view z (bottom..top at x -1.75) | -1.750 |  |  |  | wedge (-1.62,.885)-(-1.90,.893)-(-1.975,.80)-(-1.95,.765)-(-1.64,.855); band rows p5/p6 run .80->.775 / .872->.895 |
| features | taillight, rear view |  |  |  |  | y .40-.775, z .775-.90, inner end droops; body colour between the lamps |
| features | plate / diffuser, rear view |  |  |  |  | plate y +-.12 z .42-.56; diffuser y +-.66 z .20-.44; exhausts y +-.45 z .30-.39 |
| features | headlight, front view |  |  |  |  | y .44-.775, z .615-.755 (front kept from pass 3: template bands, checked on the overlay) |

## Blueprint silhouette IoU

"bp frame" = bp/bpcompare.py: the clay is rasterised straight into each blueprint view, x from the wheel centres, z from the ground line, y from the centre line, with no fitting. This is the pass 4 gate. "bbox" = bp/compare.py (5 mm/px, bbox-aligned), the metric used in passes 1-3.

| view | p1 bbox | p2 bbox | p3 bbox | p3 bp frame | **p4 bp frame** | p4 bbox | gate | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| side | 0.9122 | 0.9062 | 0.8988 | 0.8932 | **0.9660** | 0.9669 | 0.95 | pass |
| top | 0.9796 | 0.9822 | 0.9810 | 0.9773 | **0.9811** | 0.9779 | 0.95 | pass |
| front | 0.9297 | 0.9301 | 0.9265 | 0.9053 | **0.9432** | 0.9495 | 0.92 | pass |
| rear | 0.9125 | 0.9084 | 0.9041 | 0.8925 | **0.9253** | 0.9151 | 0.92 | pass |

In the bp frame the side gains +0.073, front +0.038 and rear +0.033 over pass 3. On the bbox metric the rear is 0.915. The bbox fit stretches the clay to the blueprint mask's bbox, and the blueprint rear mask drops the light-grey mirror backs and adds the dark under-car parts down to the ground (both visible in renders/clay_raw/bpiou_rear.png).

## Triangles

| object | pass 3 | pass 4 |
|---|---:|---:|
| BRZ_Body | 2898 | 2654 |
| BRZ_Cabin | 312 | 347 |
| BRZ_Exhaust_L | 22 | 22 |
| BRZ_Exhaust_R | 22 | 22 |
| BRZ_Mirror_L | 44 | 44 |
| BRZ_Mirror_R | 44 | 44 |
| BRZ_Under | 36 | 36 |
| BRZ_Wheel_FL | 398 | 398 |
| BRZ_Wheel_FR | 398 | 398 |
| BRZ_Wheel_RL | 398 | 398 |
| BRZ_Wheel_RR | 398 | 398 |
| TOTAL | 4970 | 4761 |

Cabin 312 -> 347: 14 ring columns instead of 13 (the DLO now has 5 columns so its top line follows the blueprint), plus a 3-triangle shark fin.

## Known gaps (pass 4)

- Front fascia is kept from pass 3, rescaled to the blueprint: hood/fender heights, nose tip x 2.168. Grille, fang and C-intakes are recessed loft-grid bands, so their outlines are stepped. The front-view windshield bottom still shows ~2-3 cm lower than the blueprint, which hides it below z ~.93.
- Front vs rear view disagree in the blueprint itself at z .93 (front hw .77, rear .82). The clay follows the rear view and the top view.
- The door glass and quarter glass are one dark band. The blueprint's blacked-out B-pillar (x -.6..-.7) is not split out.
- Taillights and headlights are face classes on the loft grid, tested against the blueprint lamp outlines (magenta on the overlay). Their edges are as fine as the grid: ~6-9 cm steps along x at the corners.
- The rear-view IoU loses most where the blueprint mask is not body: under-car parts drawn down to the ground between the tyres, and the light mirror backs the extractor reads as paper.
- Width: the blueprint top/front/rear views give a body half-width of .90-.925, a 1.80-1.85 m body, against the published 1.775 m. The side view matches the published length, height and wheelbase within 0.5%. The clay follows the blueprint as instructed, so it is ~2.5 cm per side wider than the published figure.
- Wheels: 8 recessed spoke windows (the real wheel has 10 twin spokes).
