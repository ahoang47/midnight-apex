#!/bin/sh
# Full rebuild of the MX-5 (ND, soft top) from the SVG: clay (out/, signed off 2026-11-04) then the detail pass (detail/). Run from this folder.
# BLENDER = Blender 4.2 binary (default: blender on PATH). System python3 needs numpy, opencv, PIL, scipy, svgpathtools, cairosvg.
# The SVG (bp/mx5_dimensions.svg) is local only (gitignored, Dimensions.com licence): download it first, see README.
set -e
cd "$(dirname "$0")"
B=${BLENDER:-blender}
(cd bp && python3 rast.py && python3 extract.py && python3 fair.py)
$B -b --factory-startup -P build_mx5.py
$B -b out/mx5_clay.blend -P render_only.py
(cd bp && python3 iou.py && python3 deliver.py && python3 feature_check.py)
$B -b out/mx5_clay.blend -P threeview/render_views.py -- mx5 xleft
python3 threeview/compose.py
(cd bp && python3 deliver_check.py)                                       # 3/4 clay + blueprint checks sheet (local only)
# ---- detail pass (same stage as gr_corolla/make_all.sh)
(cd bp && python3 vectors.py)                                            # vector feature lines + region polys for the painters
$B -b --factory-startup -P build_mx5_detail.py -- --geo-only                # geometry, clearance, clay renders (detail/renders/raw)
$B -b --factory-startup -P build_mx5_detail.py -- --render                  # UVs, AO bake, painted textures, .blend/.glb, textured renders
(cd bp && MX5_OUT=detail python3 iou.py && python3 deliver_detail.py)
$B -b detail/mx5_detail.blend -P threeview/render_views_detail.py -- mx5d xleft
python3 threeview/compose_detail.py
(cd lineup && $B -b -P render_lineup_mx5.py && python3 finish_lineup_mx5.py)
cp detail/mx5_detail.glb ../../../assets/cars/mx5/car_mx5.glb
python3 godot/make_tscn.py ../../../assets/cars/mx5/car_mx5.tscn 0.0985
