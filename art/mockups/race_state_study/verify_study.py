from pathlib import Path
import json,numpy as np
from PIL import Image
O=Path('/workspace/mockups/race_state_study');M=json.load(open(O/'staging.json'));report={}
ys=[]
for i,(name,s) in enumerate(M.items()):
 n=np.asarray(Image.open(O/'raw'/(name+'_native.png')));a=np.asarray(Image.open(O/(name+'.png')))
 assert n.shape==(480,640,3) and a.shape==(960,1280,3)
 assert np.array_equal(a,np.repeat(np.repeat(n,2,axis=0),2,axis=1))
 assert all(len(np.unique(n[:,:,c]))<=32 for c in range(3))
 assert s['rival_y']==-26 and s['center_separation_m']==([6,18,6,18][i])
 assert (s['rival_y']>s['player_y'])==(i<2)
 for who in ['rival','player']:
  x,y,z=s[who];assert 10<x<630 and 10<y<466 and z>0
 ys.append(s['rival'])
 report[name]={'native':[640,480],'upscaled':[1280,960],'exact_2x_nearest':True,'rgb555_levels':[len(np.unique(n[:,:,c])) for c in range(3)],'rival_y':s['rival_y'],'player_y':s['player_y'],'staging_separation_m':s['center_separation_m'],'both_cars_on_screen':True}
 # Fresh QA filename avoids viewer cache across revisions.
 Image.fromarray(n).save(O/'raw'/(name+'_final_qa.png'))
assert all(np.allclose(ys[0],y) for y in ys)
assert Image.open(O/'four_panel_race_state_study.png').size==(2620,2860)
Image.open(O/'four_panel_race_state_study.png').save(O/'raw'/'comparison_final_qa.png')
json.dump(report,open(O/'verification.json','w'),indent=2)
print('PASS: fixed rival/camera projection, lead ordering, staging gaps, visibility, native dimensions, nearest upscale, RGB555')
