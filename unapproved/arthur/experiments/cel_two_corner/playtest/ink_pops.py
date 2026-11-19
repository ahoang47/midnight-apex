import numpy as np, json
from PIL import Image
def hudmask(f):
    a=np.asarray(Image.open(f'gif_ink/f{f:05d}.png').convert('RGB'))[::2,::2].astype(int)
    o=np.asarray(Image.open(f'gif_off/f{f:05d}.png').convert('RGB'))[::2,::2].astype(int)
    bw=((a.max(2)-a.min(2))==0)&((a[...,0]==0)|(a[...,0]==255))
    return a[...,0]==255, (o.min(2)>200)|(~bw), o
def edges(o):   # baseline: 1-px luminance edges of the cel-OFF colour frame (what any outline would follow)
    l=o@np.array([0.299,0.587,0.114])
    gx=np.abs(np.diff(l,axis=1,append=l[:,-1:])); gy=np.abs(np.diff(l,axis=0,append=l[-1:]))
    return np.maximum(gx,gy)>18
segs={'c1_entry_straight_scroll':(20,150),'c1_playback':(380,780),'c2_entry_straight_scroll':(850,980),'c2_playback':(1160,1560)}
res={}
for name,(s,e) in segs.items():
    M=[]
    for f in range(s-1,e+2):
        ink,hud,o=hudmask(f); M.append((ink&~hud, edges(o)&~hud))
    st={}
    for k,lab in [(0,'ink'),(1,'baseline_edges_cel_off')]:
        pops=tot=0; up=[0,0]
        for i in range(1,len(M)-1):
            p,c,n=M[i-1][k],M[i][k],M[i+1][k]
            pop=(c&~p&~n)|(~c&p&n); pops+=pop.sum(); tot+=c.sum(); up[0]+=pop[:240].sum(); up[1]+=c[:240].sum()
        st[lab]=dict(px_per_frame=int(tot/(len(M)-2)), one_frame_pop_pct=round(100*pops/max(tot,1),1), upper_half_pop_pct=round(100*up[0]/max(up[1],1),1))
    res[name]=st; print(name, st, flush=True)
json.dump(res,open('ink_pops.json','w'),indent=1)
