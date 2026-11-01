"""Stage A of the light headlamp molding (S2000 / BRZ): ortho close render of the LEFT headlamp along a 3/4 view
(yaw outboard from straight ahead, small pitch down) + the camera basis, for outline segmentation.
blender -b <car>_lean.blend -P molding_view.py -- out_prefix xfwd|xleft cx cy cz yaw_deg pitch_deg size"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; pre, frame = a[0], a[1]; C = list(map(float, a[2:5])); yaw, pitch, size = map(float, a[5:8])
to_bl = (lambda p: Vector(p)) if frame == 'xfwd' else (lambda p: Vector((p[1], -p[0], p[2])))
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        alt = os.path.join(os.path.dirname(bpy.data.filepath), 'tex', os.path.basename(im.filepath))
        if os.path.exists(alt): im.filepath = alt; im.reload()
for o in bpy.data.objects:
    if '_FX_' in o.name: o.hide_render = True
# unlit albedo (texture only): no shine / env highlights, so paint vs lamp art segments cleanly
cache = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for sl in o.material_slots:
        m = sl.material
        if m is None: continue
        if m.name not in cache:
            img = next((n.image for n in (m.node_tree.nodes if m.use_nodes else []) if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] >= 256), None)
            nm = bpy.data.materials.new('ALB_' + m.name); nm.use_nodes = True; nt = nm.node_tree; nt.nodes.clear()
            out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
            if img is not None:
                tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Closest'; nt.links.new(tx.outputs[0], em.inputs[0])
            else: em.inputs[0].default_value = (0.02, 0.02, 0.02, 1)
            cache[m.name] = nm
        sl.material = cache[m.name]
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
R = 1000; sc.render.resolution_x = sc.render.resolution_y = R; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
ya, pa = math.radians(yaw), math.radians(pitch)
d = [math.cos(ya) * math.cos(pa), math.sin(ya) * math.cos(pa), math.sin(pa)]       # car frame, eye direction from target
O = to_bl((0, 0, 0)); b = (to_bl(d) - O).normalized(); up = Vector((0, 0, 1)); r = up.cross(b).normalized(); u = b.cross(r)
cam = bpy.data.objects.new('MV', bpy.data.cameras.new('MV')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size; cam.data.clip_end = 50
tgt = to_bl(C); cam.matrix_world = Matrix.Translation(tgt + b * 10) @ Matrix((r, u, b)).transposed().to_4x4()
sc.render.filepath = pre + '.png'; bpy.ops.render.render(write_still=True)
json.dump(dict(tgt_bl=list(tgt), right_bl=list(r), up_bl=list(u), back_bl=list(b), size=size, res=R, frame=frame, C=C, yaw=yaw, pitch=pitch), open(pre + '.json', 'w'))
