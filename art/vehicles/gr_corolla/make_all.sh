#!/bin/sh
# Full rebuild of the GR Corolla from the SVG: clay (out/) then the detail pass (detail/). Run from this folder.
# BLENDER = Blender 4.2 binary (default: blender on PATH). System python3 needs numpy, opencv, PIL, scipy, svgpathtools.
set -e
cd "$(dirname "$0")"
B=${BLENDER:-blender}
# ---- clay (signed off 2026-11-02)
(cd bp && python3 rast.py && python3 extract.py && python3 fair.py)
$B -b --factory-startup -P build_gr_corolla.py
$B -b out/gr_corolla_clay.blend -P render_only.py
(cd bp && python3 iou.py && python3 deliver.py)
$B -b out/gr_corolla_clay.blend -P threeview/render_views.py -- gr_corolla xleft
python3 threeview/compose.py
# ---- detail pass
(cd bp && python3 vectors.py)                                            # vector feature lines + region polys for the painters
$B -b --factory-startup -P build_gr_detail.py -- --geo-only                 # geometry, clearance, clay renders (detail/renders/raw)
$B -b --factory-startup -P build_gr_detail.py -- --render                   # UVs, AO bake, painted textures, .blend/.glb, textured renders
(cd bp && GRC_OUT=detail python3 iou.py && python3 deliver_detail.py)
$B -b detail/gr_corolla_detail.blend -P threeview/render_views_detail.py -- gr xleft
python3 threeview/compose_detail.py
(cd lineup && $B -b -P render_lineup_gr.py && python3 finish_lineup_gr.py)
python3 godot/make_tscn.py ../../../assets/cars/gr_corolla/car_gr_corolla.tscn 0.0985
