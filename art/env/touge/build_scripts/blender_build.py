# headless: blender -b -P blender_build.py   (Arthur: Touge course env export)
import bpy, bmesh, json, math, os
import numpy as np
W = '/workspace/touge_env_work/'
B = '/workspace/touge_env_build/'
ENV = B + 'assets/env/touge/'; KIT = ENV + 'kit/'; TEX = B + 'assets/tex/kit/env/'
REPO_TEX = '/workspace/touge_env_godot/assets/tex/kit/env/'
os.makedirs(KIT, exist_ok=True); os.makedirs(B + 'art/env/touge', exist_ok=True)
D = np.load(W + 'build_data.npz'); M = json.load(open(W + 'build_meta.json'))
bpy.ops.wm.read_factory_settings(use_empty=True)
TEXFILE = {'touge_hill': TEX + 'touge_hill.png', 'touge_cutface': TEX + 'touge_cutface.png', 'touge_concrete': TEX + 'touge_concrete.png',
           'line_chevron': TEX + 'line_chevron.png', 'touge_cutrock': REPO_TEX + 'touge_cutrock.png', 'touge_gravel': REPO_TEX + 'touge_gravel.png',
           'touge_guardrail': REPO_TEX + 'touge_guardrail.png', 'Emit_reflector': REPO_TEX + 'emit_reflector.png',
           'asphalt': '/workspace/touge_env_godot/assets/env/turnout_lot/lot_floor_lot_asphalt.png'}
MATS = {}
def mat(n):
    if n in MATS: return MATS[n]
    m = bpy.data.materials.new(n); m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = 1.0
    bs.inputs['Specular IOR Level'].default_value = 0.0
    if n in TEXFILE:
        im = bpy.data.images.load(TEXFILE[n]); im.name = n.lower()
        tn = m.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = im; tn.interpolation = 'Closest'
        m.node_tree.links.new(tn.outputs['Color'], bs.inputs['Base Color'])
        if n == 'line_chevron':
            m.node_tree.links.new(tn.outputs['Alpha'], bs.inputs['Alpha']); m.blend_method = 'BLEND'
    elif n == 'lamp_post':
        vc = m.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        m.node_tree.links.new(vc.outputs['Color'], bs.inputs['Base Color'])
    MATS[n] = m; return m
def g2b(P): return np.c_[P[:, 0], -P[:, 2], P[:, 1]]
def build(name, mats, colors=False, angle=50.0):
    P = D[name + '__P'].astype(float); UV = D[name + '__UV'].astype(float); MI = D[name + '__M']; COL = D[name + '__C']
    n = len(P) // 3
    me = bpy.data.meshes.new(name)
    me.from_pydata(g2b(P).tolist(), [], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)])
    uvl = me.uv_layers.new(name='UVMap')
    uv = np.c_[UV[:, 0], 1.0 - UV[:, 1]]
    uvl.data.foreach_set('uv', uv.ravel())
    if colors:
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER'); ca.data.foreach_set('color', COL.ravel())
    for m in mats: me.materials.append(mat(m))
    me.polygons.foreach_set('material_index', MI)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(me); bm.free()
    me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(angle))
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob
def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_vertex_color='ACTIVE', export_normals=True, export_texcoords=True, export_materials='EXPORT',
                              export_image_format='NONE', export_cameras=False, export_lights=False, export_extras=False)
report = {}
for name, info in M['objects'].items():
    ob = build(name, info['mats'], colors='lamp_post' in info['mats'])
    objs = [ob]
    if 'lamp_post' in info['mats']:
        # lamp posts to their own child mesh (env_vertex_lit, vertex colour); the scroll_vertex_lit terrain mesh carries UV0 only
        li = info['mats'].index('lamp_post')
        lp = ob.copy(); lp.data = ob.data.copy(); lp.name = name + '_lamps'; lp.data.name = name + '_lamps'
        bpy.context.scene.collection.objects.link(lp)
        for o, keep_lamp in ((lp, True), (ob, False)):
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.material_index == li) != keep_lamp], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            bm.to_mesh(o.data); bm.free()
        ob.data.color_attributes.remove(ob.data.color_attributes['Col'])
        lmi = lp.data.materials[li]; lp.data.materials.clear(); lp.data.materials.append(lmi)
        lp.data.polygons.foreach_set('material_index', [0] * len(lp.data.polygons)); lp.data.update()
        lp.parent = ob; objs.append(lp)
    for mk, pos, s in M['markers'].get(name, []):
        e = bpy.data.objects.new(mk, None); e.location = (pos[0], -pos[2], pos[1]); bpy.context.scene.collection.objects.link(e); objs.append(e)
    export(objs, ENV + name + '.glb')
    if name == 'touge_backdrop':   # far scenery: no collision proxy
        report[name] = {'tris': len(ob.data.polygons), 'mats': info['mats'], 'col_tris': 0}; continue
    # collision proxy: terrain / deck / walls only (no lamps, rails, reflectors), decimated
    cp = ob.copy(); cp.data = ob.data.copy(); cp.name = name + '_col'; cp.data.name = name + '_col'; bpy.context.scene.collection.objects.link(cp)
    bm = bmesh.new(); bm.from_mesh(cp.data)
    drop = {i for i, m in enumerate(info['mats']) if m in ('lamp_post', 'touge_guardrail', 'Emit_reflector')}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.0), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(cp.data); bm.free()
    cp.data.materials.clear()
    for a in list(cp.data.color_attributes): cp.data.color_attributes.remove(a)
    for u in list(cp.data.uv_layers): cp.data.uv_layers.remove(u)
    export([cp], ENV + name + '_col.glb')
    report[name] = {'tris': sum(len(o.data.polygons) for o in objs if o.type == 'MESH'), 'mats': info['mats'], 'col_tris': sum(len(p.vertices) - 2 for p in cp.data.polygons)}
for name, info in M['kit'].items():
    ob = build(name, info['mats'], colors=(name == 'lamp_post'), angle=30.0)
    export([ob], KIT + name + '.glb')
    report['kit/' + name] = {'tris': len(ob.data.polygons), 'mats': info['mats']}
bpy.ops.wm.save_as_mainfile(filepath=B + 'art/env/touge/touge_env.blend')
json.dump(report, open(W + 'export_report.json', 'w'), indent=1)
print('EXPORT_DONE', json.dumps(report))
