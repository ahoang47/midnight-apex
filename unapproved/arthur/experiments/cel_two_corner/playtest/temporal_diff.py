import numpy as np, json, sys
from PIL import Image
def L(d,f): return np.asarray(Image.open(f'{d}/f{f:05d}.png').convert('L')).astype(float)
regions={'left_forest_mid':(0,330,330,560),'right_forest_mid':(1000,320,1280,560),'near_road':(80,700,560,960),'far_road_horizon':(420,330,860,420)}
segs={'c1_entry_straight':(20,150),'c1_playback':(380,780),'c2_entry_straight':(850,980),'c2_playback':(1160,1560)}
out={}
for sn,(s,e) in segs.items():
    acc={r:{'off':0.0,'on':0.0} for r in regions}
    prev={}
    for f in range(s,e,2):
        for d in ('gif_off','gif_on'):
            a=L(d,f); b=L(d,f+1)
            for r,(x0,y0,x1,y1) in regions.items():
                acc[r]['on' if d=='gif_on' else 'off']+=np.abs(a[y0:y1,x0:x1]-b[y0:y1,x0:x1]).mean()
    n=len(range(s,e,2))
    out[sn]={r:{'off':round(v['off']/n,2),'on':round(v['on']/n,2),'ratio':round(v['on']/max(v['off'],1e-6),2)} for r,v in acc.items()}
    print(sn,out[sn],flush=True)
json.dump(out,open(sys.argv[1] if len(sys.argv)>1 else 'temporal_diff.json','w'),indent=1)
