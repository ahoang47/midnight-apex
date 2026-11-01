"""3-car lineup of the textured lean exports (WRX, S2000, BRZ), from the .glb files exactly as Godot will import them
(Principled materials carrying the same baked textures; no fake-shine nodes).  blender -b -P render_lineup.py"""
import bpy, math, os, sys
from mathutils import Vector
OUT = os.path.dirname(os.path.abspath(__file__)); _VEH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
CARS = [('WRX', os.path.join(_VEH, 'wrx_sti', 'lean', 'wrx_lean.glb'), -2.35), ('S2000', os.path.join(_VEH, 's2000', 'lean', 's2000_lean.glb'), 0.0), ('BRZ', os.path.join(_VEH, 'brz', 'lean', 'brz_lean.glb'), 2.35)]
for name, p, x in CARS:
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    new = set(bpy.data.objects) - before
    for o in new:
        if '_FX_' in o.name: o.hide_render = True          # FX sprites (WRX head lamp glow) are off by default
    roots = [o for o in new if o.parent is None]
    for r in roots: r.location.x += x
bpy.ops.mesh.primitive_plane_add(size=40); fl = bpy.context.object
m = bpy.data.materials.new('floor'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.05, 0.05, 0.06, 1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6; fl.data.materials.append(m)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.34, 0.40, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 40
cam.location = (4.6, -9.6, 2.6); d = Vector((0, 0, 0.55)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x, sc.render.resolution_y = 1280, 640
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = os.path.join(OUT, 'lean_lineup_raw.png'); bpy.ops.render.render(write_still=True)
