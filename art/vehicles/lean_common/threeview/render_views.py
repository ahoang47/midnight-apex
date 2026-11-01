"""Ortho views (side from car-left, front, top, rear) of one lean car at a common scale, from its saved .blend
(opened in place, never saved).  blender -b <car>_lean.blend -P render_views.py -- <tag> <xfwd|xleft>"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
tag, frame = sys.argv[sys.argv.index('--') + 1:][:2]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw'); MPP = 0.0044                         # metres per pixel, same for every view and car
to_bl = (lambda p: Vector(p)) if frame == 'xfwd' else (lambda p: Vector((p[1], -p[0], p[2])))
for im in bpy.data.images:                                             # unpacked images (env map) by absolute path
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        alt = os.path.join(os.path.dirname(bpy.data.filepath), 'tex', os.path.basename(im.filepath))
        if os.path.exists(alt): im.filepath = alt; im.reload()
for o in bpy.data.objects:
    if '_FX_' in o.name or o.name.startswith(('BP', 'Blueprint', 'REF')): o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('TV_CAM', bpy.data.cameras.new('TV_CAM')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 100
VIEWS = {  # name: (eye dir from target (car frame), image-right (car), target (car), size (m) w x h)
    'side': ((0, 1, 0), (-1, 0, 0), (0, 0, 0.75), (4.84, 1.80)),
    'front': ((1, 0, 0), (0, 1, 0), (0, 0, 0.75), (2.20, 1.80)),
    'rear': ((-1, 0, 0), (0, -1, 0), (0, 0, 0.75), (2.20, 1.80)),
    'top': ((0, 0, 1), (-1, 0, 0), (0, 0, 0.0), (4.84, 2.20))}
O = to_bl((0, 0, 0))
for k, (eye, right, tgt, (w, h)) in VIEWS.items():
    b = (to_bl(eye) - O).normalized(); r = (to_bl(right) - O).normalized(); u = b.cross(r)
    R = Matrix((r, u, b)).transposed().to_4x4(); cam.matrix_world = Matrix.Translation(to_bl(tgt) + b * 20) @ R
    W, H = int(round(w / MPP)), int(round(h / MPP)); sc.render.resolution_x, sc.render.resolution_y = W, H
    cam.data.ortho_scale = max(w, h); cam.data.sensor_fit = 'HORIZONTAL' if w >= h else 'VERTICAL'
    sc.render.filepath = os.path.join(OUT, f'{tag}_{k}.png'); bpy.ops.render.render(write_still=True)
