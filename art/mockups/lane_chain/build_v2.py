import bpy, math, bmesh
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
R=30.0; W=12.0; LANE=4.0
# centerline samples: s -> (pos, tangent)
def center(s):
    # s in metres: approach 0..40, arc 40..40+pi/2*R, exit after
    L1=40; La=math.pi/2*R
    if s<L1: return Vector((0,s-L1,0)), Vector((0,1,0))
    if s<L1+La:
        a=(s-L1)/R
        p=Vector((R-R*math.cos(a), R*math.sin(a),0))
        t=Vector((math.sin(a),math.cos(a),0)); return p,t
    d=s-L1-La
    return Vector((R+d,R,0)), Vector((1,0,0))
S_END=40+math.pi/2*R+40
def right(t): return Vector((t.y,-t.x,0))
def pt(s,off,z=0):
    p,t=center(s); return p+right(t)*off+Vector((0,0,z))
def mat(name,col,emit=0,rough=.8):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough
    if emit: b.inputs['Emission Color'].default_value=(*col,1); b.inputs['Emission Strength'].default_value=emit
    return m
def ribbon(name,s0,s1,o0,o1,z,m,n=120,offf=None):
    bm=bmesh.new(); prev=None
    for i in range(n+1):
        s=s0+(s1-s0)*i/n
        if offf: c=offf(s); a,b_=c-(o1-o0)/2,c+(o1-o0)/2
        else: a,b_=o0,o1
        v1=bm.verts.new(pt(s,a,z)); v2=bm.verts.new(pt(s,b_,z))
        if prev: bm.faces.new((prev[0],prev[1],v2,v1))
        prev=(v1,v2)
    me=bpy.data.meshes.new(name); bm.to_mesh(me)
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob); ob.data.materials.append(m); return ob
def box(name,loc,size,rotz,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object
    o.scale=size; o.rotation_euler[2]=rotz; o.name=name; o.data.materials.append(m); return o
asph=mat('asph',(.035,.037,.045),rough=.55)
grass=mat('ground',(.012,.014,.018))
white=mat('paint',(.8,.8,.78),emit=.4)
red=mat('kerbR',(.7,.04,.04),emit=.3); wht=mat('kerbW',(.85,.85,.85),emit=.3)
yel=mat('chev',(1,.75,.05),emit=1.5); blk=mat('blk',(.01,.01,.01))
rail=mat('rail',(.5,.52,.55),rough=.3)
line=mat('line',(0.1,.9,1.0),emit=6)
padon=mat('padon',(0.1,.9,1.0),emit=3); padoff=mat('padoff',(.25,.3,.35),emit=.25)
# ground
bpy.ops.mesh.primitive_plane_add(size=400,location=(20,0,-.02)); bpy.context.object.data.materials.append(grass)
ribbon('road',0,S_END,-W/2,W/2,0,asph,240)
# edge lines + dashed lane lines
ribbon('edgeL',0,S_END,-W/2+.15,-W/2+.35,.01,white,240); ribbon('edgeR',0,S_END,W/2-.35,W/2-.15,.01,white,240)
s=0
while s<S_END:
    for o in(-2,2): ribbon('dash',s,min(s+3,S_END),o-.1,o+.1,.01,white,6)
    s+=7
# arc range
A0=40; A1=40+math.pi/2*R; AM=(A0+A1)/2
# kerbs on inside (right) of arc
s=A0-4; i=0
while s<A1+4:
    ribbon('kerb',s,s+1.5,W/2,W/2+1.0,.03,red if i%2==0 else wht,4); s+=1.5; i+=1
# guardrail + chevrons on outside (left)
ribbon('rail',A0-15,A1+15,-W/2-2.2,-W/2-2.0,.6,rail,120)
for k in range(7):
    sk=A0+ (A1-A0)*k/6; p,t=center(sk); pos=pt(sk,-W/2-2.6,1.0)
    rz=math.atan2(t.y,t.x)
    b=box('chevB',pos,(.2,2.4,1.6),rz+math.pi/2*0,yel)
    # orient board facing incoming traffic: board normal = -t
    b.rotation_euler[2]=math.atan2(t.y,t.x)+math.pi/2
    # black chevron shape pointing right (direction of turn)
    me=bpy.data.meshes.new('chv'); bm=bmesh.new()
    pts=[(-.6,.7),(0,.7),(.6,0),(0,-.7),(-.6,-.7),(0,0)]
    vs=[bm.verts.new((x,0,y)) for x,y in pts]; bm.faces.new(vs); bm.to_mesh(me)
    c=bpy.data.objects.new('chv',me); sc.collection.objects.link(c); c.data.materials.append(blk)
    c.location=pos-t*0.09; c.rotation_euler[2]=math.atan2(t.y,t.x)+math.pi/2+math.pi
# plan: entry outside(left), apex inside(right), exit outside(left)
SE=A0; SA=AM; SX=A1
LO={'L':-LANE,'C':0,'R':LANE}
plan=[(SE,'L'),(SA,'R'),(SX,'L')]
def plan_off(s):
    keys=[(SE-30,LO['L'])]+[(a,LO[l]) for a,l in plan]+[(SX+30,LO['L'])]
    for (a,oa),(b,ob) in zip(keys,keys[1:]):
        if a<=s<=b:
            u=(s-a)/(b-a); u=(1-math.cos(math.pi*u))/2; return oa+(ob-oa)*u
    return keys[-1][1]
ribbon('plan',SE-28,SE+1,-.35,.35,.04,line,60,offf=lambda s:LO['L'])
# pads at 3 points
for sP,l in plan[:1]:
    for ln,o in LO.items():
        on=(ln==l)
        ribbon('pad',sP-1.2,sP+1.2,o-1.4,o+1.4,.03 if not on else .05,padon if on else padoff,4)
# labels
def label(txt,s,size=2.2):
    bpy.ops.object.text_add(location=pt(s,-W/2-5.5,.05)); o=bpy.context.object
    o.data.body=txt; o.data.size=size; o.data.align_x='CENTER'
    o.rotation_euler[2]=math.atan2(-44,-38)+math.pi/2
    o.data.materials.append(mat('lbl',(.85,.95,1),emit=2)); return o
label('ENTRY',SE)
# car
bpy.ops.import_scene.gltf(filepath='/workspace/midnight-apex/assets/cars/gr_corolla/car_gr_corolla.glb')
roots=[o for o in bpy.context.selected_objects if o.parent is None]
for r in roots: r.location=pt(SE-8,LO['L']); r.rotation_euler[2]+=0
# lights
bpy.ops.object.light_add(type='SUN',location=(0,0,50)); su=bpy.context.object; su.data.energy=1.2; su.data.color=(.5,.6,1); su.rotation_euler=(math.radians(40),0,math.radians(30))
for sl in [10,40,AM,A1,A1+25]:
    p=pt(sl,-W/2-3,8); bpy.ops.object.light_add(type='POINT',location=p); L=bpy.context.object; L.data.energy=6000; L.data.color=(1,.62,.3); L.data.shadow_soft_size=1
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(.03,.035,.06,1)
# camera: high overhead perspective ~58 deg down, behind-left
cam=bpy.data.cameras.new('cam'); cam.lens=28; co=bpy.data.objects.new('cam',cam); sc.collection.objects.link(co); sc.camera=co
tgt=pt(AM-8,0); co.location=tgt+Vector((-38,-44,62))
d=tgt-co.location; co.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=1600; sc.render.resolution_y=900
sc.eevee.use_bloom=True if hasattr(sc.eevee,'use_bloom') else None
sc.view_settings.view_transform='AgX'
sc.render.filepath='/workspace/mockups/lane_chain/entry_scene.png'
bpy.ops.render.render(write_still=True)
