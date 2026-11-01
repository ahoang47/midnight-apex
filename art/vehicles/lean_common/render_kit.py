"""Shared render helpers for the lean cars (headless Blender 4.2).  Cameras are given in the CAR frame
(x fwd, y left, z up) and converted with the car's Frame (leanlib.Frame)."""
import bpy, math, os
from mathutils import Vector
def _cam(name):
    c = bpy.data.objects.get(name)
    if c is None:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    return c
def cam(FR, name, loc, tgt, lens=50, ortho=None, image_right=None):
    """perspective (lens) or ortho (scale) camera at car-frame loc looking at tgt.  For a straight-down view give
    image_right (car-frame direction that should point to the image right)."""
    c = _cam(name); L = FR.to_bl(loc); T = FR.to_bl(tgt); c.location = L
    d = T - L
    if image_right is not None:
        r = FR.to_bl(image_right) - FR.to_bl((0, 0, 0)); c.rotation_euler = (0, 0, math.atan2(r.y, r.x))
    else: c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd = c.data; cd.clip_start = 0.05; cd.clip_end = 200; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.type = 'PERSP'; cd.lens = lens
    bpy.context.scene.camera = c; return c
def shoot(path, res=None):
    sc = bpy.context.scene
    if res: sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100; sc.render.filepath = path; bpy.ops.render.render(write_still=True)
def eevee(bg=(0.20, 0.21, 0.24)):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
    sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bgn = w.node_tree.nodes.get('Background'); bgn.inputs['Color'].default_value = (*bg, 1); bgn.inputs['Strength'].default_value = 1.0
    bpy.context.view_layer.material_override = None
def clay(sil=False):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sc.display.render_aa = 'OFF' if sil else '8'; sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'
    sh.color_type = 'SINGLE'; sh.single_color = (1, 1, 1) if sil else (0.66, 0.66, 0.66)
    if sil: sh.light = 'FLAT'; sh.show_cavity = False; sh.show_object_outline = False; sh.show_specular_highlight = False
    else:
        sh.light = 'STUDIO'; sh.studio_light = 'Default'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
        sh.show_object_outline = True; sh.object_outline_color = (0.08, 0.08, 0.08); sh.show_specular_highlight = True
    sh.show_shadows = False; sh.background_type = 'VIEWPORT'
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.color = (0, 0, 0) if sil else (0.92, 0.92, 0.92)
def raking(FR, path, side_loc, ortho=4.9, res=(1600, 700), zc=0.62):
    """Cycles, grey clay override, one sun grazing the left flank (from ahead, 20 deg outboard, 7 deg up)."""
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = False
    w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.06, 0.06, 0.065, 1)
    m = bpy.data.materials.get('RAKE_CLAY') or bpy.data.materials.new('RAKE_CLAY'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.45
    bpy.context.view_layer.material_override = m
    sun = bpy.data.objects.get('RAKE_SUN')
    if sun is None:
        sun = bpy.data.objects.new('RAKE_SUN', bpy.data.lights.new('RAKE_SUN', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 7.0; sun.data.angle = math.radians(1.0); sun.hide_render = False
    d = FR.to_bl((-0.93, -0.34, -0.12)) - FR.to_bl((0, 0, 0)); sun.rotation_euler = d.normalized().to_track_quat('-Z', 'Y').to_euler()
    cam(FR, 'CAM_rake', side_loc, (side_loc[0], 0, zc), ortho=ortho); shoot(path, res)
    sun.hide_render = True; bpy.context.view_layer.material_override = None
