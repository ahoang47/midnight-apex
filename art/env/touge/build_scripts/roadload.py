import json, numpy as np, trimesh
EXP='/workspace/gordon-touge/unapproved/gordon/road_export/'
def load():
    d=json.load(open(EXP+'road_centreline.json'))
    sc=trimesh.load(EXP+'road_surface.glb')
    rows={}
    for name in sc.graph.nodes_geometry:
        tf,gn=sc.graph[name]; g=sc.geometry[gn]
        if name=='LotFloor': lot=g.copy(); lot.apply_transform(tf); continue
        v=trimesh.transform_points(g.vertices,tf); uv=g.visual.uv
        s=np.round(1-uv[:,1],3); u=np.round(uv[:,0],3)
        for k in range(len(v)):
            rows.setdefault(s[k],{})[u[k]]=v[k]
    S=np.array(sorted(rows))
    L=np.array([rows[x][0.0] for x in S]); R=np.array([rows[x][1.0] for x in S])
    return d,S,L,R,lot
if __name__=='__main__':
    d,S,L,R,lot=load()
    print(len(S),S[:5],S[-5:], np.unique(np.diff(S)))
    smp={x['s']:x for x in d['samples']}
    for s in [490,500,510,530,560,570]:
        i=np.where(S==s)[0][0]; w=np.linalg.norm((R[i]-L[i])[[0,2]]); print(s,w, smp[s]['left_width']+smp[s]['right_width'])
    print('lot bounds',lot.bounds)
