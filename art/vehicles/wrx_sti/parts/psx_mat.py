"""PSX fake-shine material (art direction A.3: fixed ambient + one key light + Blinn + painted env x fresnel,
env <= 0.45, output = Emission, no scene lights).  Copied from the BRZ detail build (build_brz_detail.py) so every
car shares one shader formula.  Call set_env(image) before fake_mat()."""
import bpy
from mathutils import Vector
def to_bl(p): return Vector((p[1], -p[0], p[2]))
KEY_L = Vector(to_bl((0.45, 0.55, 0.70))).normalized()   # key from front-left-above (car frame)
ENV_IMG = None
def set_env(img):
    global ENV_IMG; ENV_IMG = img
def fake_mat(name, rgb=(1, 1, 1), img=None, ambient=0.42, key=0.70, spec=0.35, shin=40.0, env=0.30, env_tint=(1, 1, 1),
             emit=0.0, interp='Closest'):
    """colour = albedo*(ambient + key*N.L) + spec*(N.H)^shin + env(reflect(V,N))*tint*fres,
    fres = env*(1-max(N.V,0))^2 + 0.08 (scaled by env so matte parts stay matte) ; output = Emission (no scene lights).
    A Principled BSDF with the same albedo is kept in the tree (unlinked) and swapped in for the glb/obj/fbx export."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nd = nt.nodes; L = nt.links.new
    pb = nd['Principled BSDF']; out = nd['Material Output']
    pb.inputs['Base Color'].default_value = (*rgb, 1); pb.inputs['Roughness'].default_value = 0.45 if env > 0.2 else 0.8
    m.diffuse_color = (*rgb, 1)
    if img is not None:
        t = nd.new('ShaderNodeTexImage'); t.image = img; t.interpolation = interp; t.name = 'ALBEDO'
        L(t.outputs['Color'], pb.inputs['Base Color']); alb = t.outputs['Color']
    else:
        c = nd.new('ShaderNodeRGB'); c.outputs[0].default_value = (*rgb, 1); alb = c.outputs[0]
    geo = nd.new('ShaderNodeNewGeometry'); N, V = geo.outputs['Normal'], geo.outputs['Incoming']
    def vm(op, a, b=None, val=None):
        n = nd.new('ShaderNodeVectorMath'); n.operation = op; L(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list, Vector)): n.inputs[1].default_value = tuple(b)
            else: L(b, n.inputs[1])
        if val is not None: n.inputs[3].default_value = val
        return n
    def mm(op, a, b=None, c=None, clamp=False):
        n = nd.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    ndl = mm('MAXIMUM', vm('DOT_PRODUCT', N, KEY_L).outputs['Value'], 0.0)
    dif = mm('MULTIPLY_ADD', ndl, key, ambient)
    lit = vm('SCALE', alb); L(dif, lit.inputs['Scale'])
    H = vm('NORMALIZE', vm('ADD', V, KEY_L).outputs[0])
    ndh = mm('MAXIMUM', vm('DOT_PRODUCT', N, H.outputs[0]).outputs['Value'], 0.0)
    sp = mm('MULTIPLY', mm('POWER', ndh, shin), spec)
    if img is not None:      # painted black trim on the shared paint texture: dimmer spec + env than the clear coat
        lum = nd.new('ShaderNodeRGBToBW'); L(alb, lum.inputs[0]); kpaint = mm('MULTIPLY_ADD', lum.outputs[0], 8.0, 0.22, clamp=True)
        sp = mm('MULTIPLY', sp, kpaint)
    ndv = mm('MAXIMUM', vm('DOT_PRODUCT', N, V).outputs['Value'], 0.0)
    fres = mm('MULTIPLY_ADD', mm('POWER', mm('SUBTRACT', 1.0, ndv), 2.0), env, 0.08 * min(env / 0.3, 1.0))
    R = vm('REFLECT', vm('SCALE', V, val=-1.0).outputs[0], N)
    et = nd.new('ShaderNodeTexEnvironment'); et.image = ENV_IMG; et.interpolation = 'Linear'; L(R.outputs[0], et.inputs['Vector'])
    envc = vm('MULTIPLY', et.outputs['Color'], tuple(env_tint))
    if img is not None: fres = mm('MULTIPLY', fres, kpaint)
    envs = vm('SCALE', envc.outputs[0]); L(fres, envs.inputs['Scale'])
    acc = vm('ADD', lit.outputs[0], envs.outputs[0])
    spv = nd.new('ShaderNodeCombineXYZ'); [L(sp, spv.inputs[i]) for i in range(3)]
    acc = vm('ADD', acc.outputs[0], spv.outputs[0])
    if emit:
        ee = vm('SCALE', alb, val=emit); acc = vm('ADD', acc.outputs[0], ee.outputs[0])
    em = nd.new('ShaderNodeEmission'); em.name = 'FAKESHINE'; L(acc.outputs[0], em.inputs['Color'])
    L(em.outputs[0], out.inputs['Surface']); return m
def use_principled(on):
    for m in bpy.data.materials:
        if not m.use_nodes or 'FAKESHINE' not in m.node_tree.nodes or 'Principled BSDF' not in m.node_tree.nodes: continue
        nt = m.node_tree; out = nt.nodes['Material Output']
        src = nt.nodes['Principled BSDF'] if on else nt.nodes['FAKESHINE']
        nt.links.new(src.outputs[0], out.inputs['Surface'])

