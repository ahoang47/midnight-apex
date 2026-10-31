"""Headless BRZ clay build.  Run:
  blender -b -P build_brz.py -- [--render]
Builds the grey-clay body from parts/brz_geo.py, adds wheels (spoke windows), door mirrors, exhaust tips, underbody, saves brz_clay.blend,
exports brz_clay.glb and (with --render) renders clay views into renders/clay_raw/."""
import bpy, bmesh, sys, os, math, importlib
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'parts'))
import brz_geo as G; importlib.reload(G)
DETAIL=False   # set by build_brz_detail.py
import numpy as np

def to_bl(p):  # car (x fwd, y left, z) -> Blender (X = left, Y = -fwd, Z)
    return Vector((p[1], -p[0], p[2]))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, rgb, rough=0.6):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*rgb,1); return m

def obj_from_bm(name, bm, mats):
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    return ob

def smooth(ob, angle=38):
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle),keep_sharp_edges=True)
    ob.select_set(False)

# ------------------------------------------------------------------ body
def build_body(M):
    X,V,W,P=G.build(); S,C=V.shape[:2]
    bm=bmesh.new(); vv=[[bm.verts.new(to_bl(V[s,c])) for c in range(C)] for s in range(S)]
    xs_ws=(G.env(np.array([0.78]))[0],)
    faces=[]; F=[]   # (face, band_lo, band_hi, x_mid)
    for s in range(S-1):
        for c in range(C-1):
            f=bm.faces.new((vv[s][c],vv[s+1][c],vv[s+1][c+1],vv[s][c+1]))
            i=min(P[s,c],P[s,c+1]); w=min(W[s,c],W[s,c+1],W[s+1,c],W[s+1,c+1])
            F.append((f,i,0.5*(X[s]+X[s+1]),w)); faces.append(f)
    bmesh.ops.recalc_face_normals(bm,faces=faces)
    grille=[]; intake=[]; lamp_f=[]; lamp_r=[]; bar_r=[]; diff=[]; plate=[]
    import brz_bp as BP
    def feat(kind, view, p):
        polys = BP.FEAT[kind].get(view)
        if polys is None: return False
        if not isinstance(polys[0][0], (list, tuple)): polys = [polys]
        return any(BP.inside(pg, p) for pg in polys)
    for f,i,xm,w in F:
        c=f.calc_center_median(); cx,cy,cz=-c.y,abs(c.x),c.z
        n=f.normal; nx=-n.y; ny=abs(n.x); nz=n.z
        xo = 1.65+(xm-1.65)/1.045 if xm>1.65 else xm        # pass-3 station x (front fascia bands are template bands)
        m=0
        # ---- front fascia (template bands, unchanged from pass 3; checked against the blueprint overlay)
        if xo>1.70 and ((i==5 and xo<2.03) or (i==6 and 1.89<xo<2.03) or (i==4 and 1.72<xo<1.84)):
            m=3; lamp_f.append(f)
        elif (i<=1 and xo>2.05) or (i in (2,3) and xo>2.025):
            m=4; grille.append(f)
        elif (1.935<xo<1.98 and i in (1,2,3)) or (1.89<xo<1.935 and i in (1,3)):
            m=4; intake.append(f)
        elif (i==3 and 0.90<xo<1.0) or (i==2 and 0.80<xo<0.90): m=4
        # ---- rear: blueprint feature outlines, tested in the view each face points to
        elif cx < -1.55:
            view = 'rear' if -nx >= max(ny, nz) else ('side' if ny >= nz else 'top')
            p = {'rear': (cy, cz), 'side': (cx, cz), 'top': (cx, cy)}[view]
            if 4 <= i <= 6 and feat('lamp', view, p): m=3; lamp_r.append(f)
            elif view == 'rear' and feat('plate', 'rear', p): m=0; plate.append(f)
            elif i <= 2 and ((view in ('rear', 'side') and feat('trim', view, p)) or (i == 0 and cx < -1.74)): m=4; diff.append(f)
        f.material_index=m
    # crisp intended edges
    def mark(c,s0,s1):
        for cc in (c,C-1-c):
            for s_ in range(s0,s1):
                e=bm.edges.get((vv[s_][cc],vv[s_+1][cc]))
                if e: e.smooth=False
    def ring(s_,c0,c1):
        for c in range(c0,c1):
            e=bm.edges.get((vv[s_][c],vv[s_][c+1]))
            if e: e.smooth=False
    idx=lambda x: int(np.argmin(np.abs(X-x)))
    mark(6,idx(1.80),idx(0.78)); mark(5,idx(1.65),idx(0.95))         # fender ridge
    mark(7,idx(1.65),idx(0.95))                                       # foot of the ridge = hood valley edge
    mark(1,idx(0.78),idx(-0.70)); mark(3,idx(0.78),idx(-0.70))       # rocker blade + door-scoop top
    mark(7,idx(G.REAR_X0)+1,S-1)                                      # ducktail lip edge (deck -> lip)
    mark(4,idx(G.REAR_X0),S-1)                                        # rear bumper crease, round the corners and across
    # bottom plates between left/right p0 where the station is not over a wheel arch
    for s_ in range(S-1):
        if G.arch_z(np.array([X[s_]]))[0]>0 or G.arch_z(np.array([X[s_+1]]))[0]>0: continue
        f=bm.faces.new((vv[s_][0],vv[s_][C-1],vv[s_+1][C-1],vv[s_+1][0])); f.material_index=2
    bmesh.ops.remove_doubles(bm,verts=vv[S-1],dist=1e-4)    # tail collapses onto the centre-line profile
    # recesses as real geometry
    insets=((grille,0.05,0.012),(intake,0.055,0.010),(lamp_f,0.012,0.006),(lamp_r,0.015,0.006),(bar_r,0.012,0.004),(diff,0.025,0.01),(plate,0.012,0.008))
    if DETAIL: insets=((grille,0.05,0.012),(diff,0.025,0.01))   # detail pass: lamps/plate are atlas decals; C-intakes + outlines painted from the blueprint
    for grp,depth,th in insets:
        grp=[f for f in grp if f.is_valid]
        if grp:
            r=bmesh.ops.inset_region(bm,faces=grp,thickness=th,depth=-depth,use_even_offset=True)
            mi=grp[0].material_index
            for f in grp: f.material_index=mi
            for f in r['faces']: f.material_index=4 if mi==4 else 0
    bmesh.ops.remove_doubles(bm,verts=vv[0],dist=1e-4)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    ob=obj_from_bm('BRZ_Body',bm,[M['clay'],M['glass'],M['under'],M['lamp'],M['trim']]); smooth(ob); return ob

# ------------------------------------------------------------------ greenhouse
def build_cabin(M):
    """greenhouse: 26-point ring loft (base footprint -> roof edge) closed by a 7x7 roof grid that shares the roof-edge
    loop, so the windshield header, roof and rear-glass top are one surface with evenly spaced loops."""
    R=G.gh_rings(); nR,nJ=R.shape[0],R.shape[1]          # 6 rings x 14 left-half columns
    bm=bmesh.new()
    order=list(range(nJ))+list(range(nJ-2,0,-1))         # j0..j12 (left), j11..j1 (right)
    sgn=[1]*nJ+[-1]*(nJ-2); n=len(order)
    loops=[[bm.verts.new(to_bl(R[k,j]*[1,s_,1])) for j,s_ in zip(order,sgn)] for k in range(nR)]
    kind=G.gh_kind
    for k in range(nR-1):
        for q in range(n):
            ja,jb=order[q],order[(q+1)%n]
            f=bm.faces.new((loops[k][q],loops[k][(q+1)%n],loops[k+1][(q+1)%n],loops[k+1][q]))
            lo,hi=min(ja,jb),max(ja,jb)
            ws_rg=(hi<=3) or (lo>=10)
            side=(lo>=4 and hi<=8)
            f.material_index=1 if ((ws_rg and k<G.GH_GLASS_TOP) or (side and 1<=k<G.GH_GLASS_TOP)) else 0
    # roof grid: row r, column c (0 = left edge, 3 = centre, 6 = right edge)
    RR=G.roof_rows(); nr,nc=RR.shape[0],RR.shape[1]; top=loops[-1]
    def ring_vert(j,left): return top[j] if (left or j in (0,nJ-1)) else top[n-j]
    grid=[[None]*nc for _ in range(nr)]
    for r in range(nr):
        for c in range(nc):
            left=c<3; m=abs(c-3)          # m = index into GH_F
            if r==0: grid[r][c]=ring_vert(m,left)
            elif r==nr-1: grid[r][c]=ring_vert(nJ-1-m,left)
            elif m==3: grid[r][c]=ring_vert(3+r,left)
            else: grid[r][c]=bm.verts.new(to_bl(RR[r,c]))
    for r in range(nr-1):
        for c in range(nc-1):
            f=bm.faces.new((grid[r][c],grid[r][c+1],grid[r+1][c+1],grid[r+1][c])); f.material_index=0
    # shark fin antenna (blueprint side view: x -.68..-.86, top 1.325)
    zr=lambda x: float(G.genv(np.array([x]))[0])-0.004
    A=bm.verts.new(to_bl((-0.66,0,zr(-0.66)))); Bl=bm.verts.new(to_bl((-0.87,0.035,zr(-0.87)))); Br=bm.verts.new(to_bl((-0.87,-0.035,zr(-0.87))))
    Tp=bm.verts.new(to_bl((-0.835,0,1.325)))
    for fv in ((A,Bl,Tp),(Br,A,Tp),(Bl,Br,Tp)): bm.faces.new(fv).material_index=0
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    ob=obj_from_bm('BRZ_Cabin',bm,[M['clay'],M['glass']]); smooth(ob,62); return ob

# ------------------------------------------------------------------ wheels
def build_wheel(name, x, y, M, seg=16):
    """tyre with a bulged sidewall, a dark bead groove separating it from the rim lip, a dished rim face and
    seg/2 recessed spoke windows (alloy read in clay)."""
    side=1 if y>0 else -1; r=G.TIRE_OD/2; rr=G.RIM_D/2; w=G.TIRE_W; h=w/2
    prof=[(r,-h+0.03),(r,h-0.03),(r*0.95,h),(r*0.84,h+0.006),(rr*1.06,h-0.004),   # tyre
          (rr*1.02,h-0.028),                                                                   # bead groove
          (rr*0.99,h-0.006),(rr*0.93,h-0.006),                                                 # rim lip
          (rr*0.88,h-0.034),(rr*0.30,h-0.034),(rr*0.17,h-0.016)]                               # dish, spoke band, hub
    MAT=[0,0,0,0,0,0,1,1,1,1]
    bm=bmesh.new(); rings=[]
    for k in range(seg):
        a=2*math.pi*(k+0.5)/seg
        rings.append([bm.verts.new(to_bl((x+rad*math.cos(a), y+side*off, G.TIRE_OD/2+rad*math.sin(a)))) for rad,off in prof])
    win=[]
    for k in range(seg):
        a=rings[k]; b=rings[(k+1)%seg]
        for i in range(len(prof)-1):
            f=bm.faces.new((a[i],b[i],b[i+1],a[i+1])); f.material_index=MAT[i]
            if i==len(prof)-3 and k%2: win.append(f)
    hub=bm.faces.new([rg[-1] for rg in rings]); hub.material_index=1
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    r_=bmesh.ops.inset_individual(bm,faces=win,thickness=0.012,depth=-0.045,use_even_offset=True)
    for f in win: f.material_index=2
    bmesh.ops.triangulate(bm,faces=[hub])
    ob=obj_from_bm(name,bm,[M['tire'],M['rim'],M['under']]); smooth(ob,50); return ob

# ------------------------------------------------------------------ mirrors
def build_mirror(name, side, M):
    """door-mounted: short stalk from the door skin just behind the A-pillar base (beltline height)
    out to a tapered, rounded-front housing."""
    s=side; bm=bmesh.new()
    def loft(secs):   # list of (x, [(y,z)...]) closed 6-gon rings -> tube with end caps
        R=[[bm.verts.new(to_bl((x+dx, s*y, z))) for (y,z,dx) in pts] for x,pts in secs]
        n=len(R[0])
        for a,b in zip(R[:-1],R[1:]):
            for k in range(n): bm.faces.new((a[k],a[(k+1)%n],b[(k+1)%n],b[k]))
        bm.faces.new(R[0]); bm.faces.new(R[-1][::-1])
    # blueprint: housing x .25-.44 (side) / out to y 1.0 (top, front), z .925-1.03; stalk to the DLO front tip
    loft([(0.455,[(0.735,0.905,0),(0.735,0.945,0),(0.735,0.945,-0.070),(0.735,0.905,-0.070)]),
          (0.440,[(0.860,0.940,0),(0.860,0.965,0),(0.860,0.965,-0.055),(0.860,0.940,-0.055)])])
    def ring(x,yi,yo,z0,z1,tr=0.0): return (x,[(yi,z0+tr,0),(yo-0.012,z0,0),(yo,0.5*(z0+z1),0),(yo-0.012,z1,0),(yi,z1-tr,0),(yi-0.012,0.5*(z0+z1),0)])
    loft([ring(0.445,0.850,0.950,0.950,1.010,0.010),ring(0.415,0.835,0.995,0.925,1.030),ring(0.255,0.835,0.995,0.928,1.027)])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    ob=obj_from_bm(name,bm,[M['clay']]); smooth(ob,50); return ob

def build_exhaust(name, y, M, seg=8):
    """exhaust tip recessed into the diffuser: short dark tube, open end."""
    bm=bmesh.new(); r=0.045; xs=(-2.085,-2.0)
    R=[[bm.verts.new(to_bl((x, y+r*math.cos(2*math.pi*k/seg), 0.345+r*math.sin(2*math.pi*k/seg)))) for k in range(seg)] for x in xs]
    for k in range(seg): f=bm.faces.new((R[0][k],R[0][(k+1)%seg],R[1][(k+1)%seg],R[1][k])); f.material_index=0
    end=bm.faces.new(R[1]); end.material_index=1
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); bmesh.ops.triangulate(bm,faces=[end])
    return obj_from_bm(name,bm,[M['rim'],M['under']])

# ------------------------------------------------------------------ underbody / wheel wells (dark, hides the open bottom)
def build_under(M):
    bm=bmesh.new()
    def box(x0,x1,y0,y1,z0,z1):
        r=bmesh.ops.create_cube(bm,size=1.0)['verts']
        for v in r:
            v.co=Vector(((y0 if v.co.x<0 else y1),(-x0 if v.co.y<0 else -x1),(z0 if v.co.z<0 else z1)))
    box(-1.55,1.78,-0.58,0.58,0.17,0.45)
    for xc in (G.AXF,G.AXR): box(xc-0.36,xc+0.36,-0.80,0.80,0.30,0.66)
    ob=obj_from_bm('BRZ_Under',bm,[M['under']]); return ob

def main():
    reset()
    M=dict(clay=mat('clay',(0.66,0.66,0.66),0.55), glass=mat('clay_glass',(0.16,0.17,0.19),0.3),
           tire=mat('tire',(0.05,0.05,0.05),0.9), rim=mat('rim',(0.62,0.62,0.64),0.4), under=mat('under',(0.02,0.02,0.02),1.0),
           lamp=mat('clay_lamp',(0.30,0.32,0.36),0.2), trim=mat('clay_trim',(0.08,0.08,0.085),0.8))
    body=build_body(M); build_cabin(M)
    for nm,x,y in (('FL',G.AXF,G.TRACK_F/2),('FR',G.AXF,-G.TRACK_F/2),('RL',G.AXR,G.TRACK_R/2),('RR',G.AXR,-G.TRACK_R/2)):
        build_wheel('BRZ_Wheel_'+nm,x,y,M)
    build_mirror('BRZ_Mirror_L',1,M); build_mirror('BRZ_Mirror_R',-1,M)
    build_under(M)
    build_exhaust('BRZ_Exhaust_L',0.45,M); build_exhaust('BRZ_Exhaust_R',-0.45,M)
    tris=0
    for ob in bpy.data.objects:
        if ob.type=='MESH':
            ob.data.calc_loop_triangles(); n=len(ob.data.loop_triangles); tris+=n; print(f'  {ob.name:16s} {n:5d} tris')
    print('TOTAL TRIS',tris)
    open(os.path.join(HERE,'tri_count.txt'),'w').write('\n'.join(f'{o.name} {len(o.data.loop_triangles)}' for o in bpy.data.objects if o.type=='MESH')+f'\nTOTAL {tris}\n')
    # triangle soup (car frame) for camera refinement / silhouette checks outside Blender
    T=[]; TM=[]
    for ob in bpy.data.objects:
        if ob.type!='MESH': continue
        me=ob.data; me.calc_loop_triangles(); mw=ob.matrix_world
        for t in me.loop_triangles:
            T.append([[-(mw@me.vertices[i].co).y,(mw@me.vertices[i].co).x,(mw@me.vertices[i].co).z] for i in t.vertices])
            TM.append(me.materials[t.material_index].name if me.materials else 'clay')
    np.save(os.path.join(HERE,'bp','tris_carframe.npy'),np.array(T,np.float32))
    np.save(os.path.join(HERE,'bp','tris_material.npy'),np.array(TM))
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'brz_clay.blend'),compress=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE,'brz_clay.glb'),export_format='GLB')
    if '--render' in sys.argv:
        import render_clay; importlib.reload(render_clay); render_clay.render_all(HERE)

if __name__=='__main__': main()
