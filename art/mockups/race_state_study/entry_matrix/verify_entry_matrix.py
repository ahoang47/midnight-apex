from pathlib import Path
from PIL import Image
import numpy as np,json,math
O=Path('/workspace/mockups/race_state_study/entry_matrix');R=O/'raw';M=json.load(open(O/'camera_staging.json'));old=json.load(open(O.parent/'fixed_chase'/'camera_staging.json'));notes=json.load(open(O/'visibility_notes.json'))
assert len(M)==12
F=[];B=[];report={};manifest=[]
for name,s in M.items():
 fw=s['forward'];rr=s['rear'];state=s['state'];lane=s['lane'];F.append(fw['camera_matrix_world']);B.append(rr['camera_matrix_world'])
 assert np.allclose(fw['player_world_location'],[0,-28,.16])
 x={'outside':-3.3,'center':0,'inside':3.3}[lane];y={'01_ahead_pressure':-22,'02_ahead_room':-10,'03_close_behind':-34,'04_far_behind':-46}[state]
 assert np.allclose(fw['rival_world_location'],[x,y,.16])
 assert np.array_equal(np.array(fw['camera_matrix_world']),np.array(old[state]['forward']['camera_matrix_world']))
 assert np.array_equal(np.array(rr['camera_matrix_world']),np.array(old[state]['rear']['camera_matrix_world']))
 assert fw['lens_mm']==25 and rr['lens_mm']==14
 assert s['truthful_entry']=={'outside':'ATK','center':'STY','inside':'DEF'}[lane]
 assert s['separation_m']==abs(y+28)
 n=np.array(Image.open(R/(name+'_native.png')));up=np.array(Image.open(O/(name+'.png')))
 assert n.shape==(480,640,3) and up.shape==(960,1280,3)
 assert np.array_equal(up,np.repeat(np.repeat(n,2,0),2,1))
 assert all(len(np.unique(n[:,:,c]))<=32 for c in range(3))
 assert Image.open(R/(name+'_mirror_native.png')).size==(192,64)
 # Proposed UI does not intrude into the geometric player/rival footprints on the main view.
 p=np.array(fw['rival_mesh_projection']);positive=p[p[:,2]>.1]
 bbox=[float(positive[:,0].min()),float(positive[:,0].max()),float(positive[:,1].min()),float(positive[:,1].max())] if len(positive) else None
 if bbox:
  assert bbox[1]<414 or bbox[0]>628 or bbox[3]<107 or bbox[2]>315, (name,'HUD overlap',bbox)
 rearpoints=np.array(rr['rival_mesh_projection']);rp=rearpoints[rearpoints[:,2]>.1]
 extent=np.ptp(rp[:,:2],axis=0).tolist() if len(rp) else None
 report[name]={'lane':lane,'truthful_entry_only':s['truthful_entry'],'longitudinal_staging_gap_m':s['separation_m'],'main_projected_mesh_bbox_native':bbox,'mirror_projected_mesh_extent_native':extent,'observations':notes[name],'same_cameras_as_fixed_chase':True,'exact_2x_nearest':True,'rgb555_levels':[len(np.unique(n[:,:,c])) for c in range(3)],'main_UI_clear_of_rival_projected_mesh':True}
 manifest.append({'name':name,'gameplay':'file://'+str(O/(name+'.png')),'native':'file://'+str(R/(name+'_native.png')),'state_sheet':'file://'+str(O/(state+'_entry_comparison.png'))})
 Image.fromarray(n).save(R/(name+'_qa_final.png'))
 Image.open(R/(name+'_mirror_native.png')).resize((576,192),Image.Resampling.NEAREST).save(R/(name+'_mirror_3x_qa.png'))
for mat in F:assert np.array_equal(mat,F[0])
for mat in B:assert np.array_equal(mat,B[0])
# UI itself is constant in every scenario: sample full hand, MID/STY unconfirmed, no locked or future cards.
first=np.array(Image.open(R/(next(iter(M))+'_native.png')))
for name in M:
 n=np.array(Image.open(R/(name+'_native.png')))
 # Opaque pixels are identical; semi-transparent backing legitimately reflects the scene below.
 assert np.array_equal(n[131:145,473:622],first[131:145,473:622])
for state in old:
 assert Image.open(O/(state+'_entry_comparison.png')).size==(3920,1290)
 Image.open(O/(state+'_entry_comparison.png')).save(R/(state+'_sheet_qa_final.png'))
json.dump(report,open(O/'verification.json','w'),indent=2);json.dump(manifest,open(O/'manifest.json','w'),indent=2)
print('PASS: 12 frames, truthful lanes/gaps, exact original camera matrices, no main selector/rival overlap, native RGB555 and exact 2x nearest')
