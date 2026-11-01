"""Head lamp close-ups (read-only, never saves): front ortho, front 3/4 (persp) and pure side ortho of the LEFT lamp.
blender -b <car>_lean.blend -P lamp_closeups.py -- <out_prefix> <xfwd|xleft> cx cy cz [ortho_size]
(cx, cy, cz) = lamp centre in the car frame (x fwd, y left, z up).  Glow FX hidden."""
import bpy, os, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; pre, frame = a[0], a[1]; C = tuple(map(float, a[2:5])); OS = float(a[5]) if len(a) > 5 else 0.62
to_bl = (lambda p: Vector(p)) if frame == 'xfwd' else (lambda p: Vector((p[1], -p[0], p[2])))
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        alt = os.path.join(os.path.dirname(bpy.data.filepath), 'tex', os.path.basename(im.filepath))
        if os.path.exists(alt): im.filepath = alt; im.reload()
for o in bpy.data.objects:
    if '_FX_' in o.name: o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
sc.render.resolution_x, sc.render.resolution_y = 640, 448; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = False
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (0.20, 0.21, 0.24, 1)
c = bpy.data.objects.new('CAM_lc', bpy.data.cameras.new('CAM_lc')); sc.collection.objects.link(c); sc.camera = c
def shot(eye, name, ortho=None, lens=None):
    loc = to_bl(eye); tgt = to_bl(C); c.location = loc
    c.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    else: c.data.type = 'PERSP'; c.data.lens = lens
    sc.render.filepath = f'{pre}_{name}.png'; bpy.ops.render.render(write_still=True)
x, y, z = C
shot((x + 4.0, y, z), 'front', ortho=OS)
shot((x + 1.30, y + 1.15, z + 0.30), 'front34', lens=55)
shot((x - 0.15, y + 4.0, z), 'side', ortho=OS)
