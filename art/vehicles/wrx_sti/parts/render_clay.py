"""Clay + silhouette renders for the WRX (Workbench, headless).
Ortho views: 1 px = 5 mm, 1000x1000, camera centred on car frame point (0,0,0.65)/(0,0,0)."""
import bpy, math, os, json
from mathutils import Vector, Euler

ORTHO={  # name: (location in Blender coords, rotation euler deg)
 'side': ((8,0,0.65),(90,0,90)),      # looks at car's left side (+X)
 'front':((0,-8,0.65),(90,0,0)),      # car front faces -Y
 'rear': ((0,8,0.65),(90,0,180)),
 'top':  ((0,0,8),(0,0,90)),          # front of car at image left
}

def setup_scene(sil=False, res=(1000,1000)):
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.resolution_percentage=100
    sh=sc.display.shading
    sc.display.render_aa='OFF' if sil else '8'
    if sil:
        sh.light='FLAT'; sh.color_type='SINGLE'; sh.single_color=(1,1,1); sh.show_cavity=False; sh.show_shadows=False
        sh.background_type='VIEWPORT'
        sc.world=sc.world or bpy.data.worlds.new('W'); sc.world.color=(0,0,0)
        sh.show_object_outline=False; sh.show_specular_highlight=False
    else:
        sh.light='STUDIO'; sh.studio_light='Default'; sh.use_world_space_lighting=False; sh.color_type='MATERIAL'; sh.show_cavity=True; sh.cavity_type='BOTH'; sh.curvature_ridge_factor=1.0; sh.curvature_valley_factor=1.0
        sh.cavity_ridge_factor=1.0; sh.cavity_valley_factor=1.5
        sh.show_shadows=False; sh.show_specular_highlight=True; sh.show_object_outline=True; sh.object_outline_color=(0.08,0.08,0.08)
        sc.world=sc.world or bpy.data.worlds.new('W'); sc.world.color=(0.92,0.92,0.92)
    sc.render.film_transparent=False
    sc.view_settings.view_transform='Standard'
    sc.render.image_settings.file_format='PNG'

def cam(name, loc, rot=None, ortho=None, lens=None, target=None, sensor=36.0):
    c=bpy.data.objects.get(name)
    if c is None:
        c=bpy.data.objects.new(name,bpy.data.cameras.new(name)); bpy.context.collection.objects.link(c)
    c.location=Vector(loc)
    if target is not None:
        d=Vector(target)-c.location; c.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    else:
        c.rotation_euler=Euler([math.radians(a) for a in rot])
    cd=c.data; cd.clip_start=0.1; cd.clip_end=200; cd.sensor_fit='HORIZONTAL'; cd.sensor_width=sensor
    if ortho: cd.type='ORTHO'; cd.ortho_scale=ortho
    else: cd.type='PERSP'; cd.lens=lens
    bpy.context.scene.camera=c; return c

def shoot(path):
    bpy.context.scene.render.filepath=path; bpy.ops.render.render(write_still=True)

def render_all(here, persp_json=None):
    out=os.path.join(here,'renders','clay_raw'); os.makedirs(out,exist_ok=True)
    for sil in (False,True):
        setup_scene(sil)
        for k,(loc,rot) in ORTHO.items():
            cam('CAM_'+k,loc,rot,ortho=5.0); shoot(os.path.join(out,f'{"sil" if sil else "clay"}_{k}.png'))
    pj=persp_json or os.path.join(here,'bp','cameras.json')
    if os.path.exists(pj):
        cams=json.load(open(pj))
        for k,c in cams.items():
            setup_scene(False,(c['w'],c['h']))
            cc=cam('CAM_'+k,c['loc'],ortho=None,lens=c['lens'],target=c['target'],sensor=c.get('sensor',36.0))
            if 'up' in c:
                from mathutils import Matrix
                f=(Vector(c['target'])-Vector(c['loc'])).normalized(); u=Vector(c['up']); u=(u-f*f.dot(u)).normalized(); x=f.cross(u)
                cc.matrix_world=Matrix.Translation(Vector(c['loc']))@Matrix((x,u,-f)).transposed().to_4x4()
            if 'shift' in c: bpy.context.scene.camera.data.shift_x,bpy.context.scene.camera.data.shift_y=c['shift']
            shoot(os.path.join(out,f'clay_{k}.png'))
            setup_scene(True,(c['w'],c['h'])); shoot(os.path.join(out,f'sil_{k}.png'))
