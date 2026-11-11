from pathlib import Path
import json,math,numpy as np
from PIL import Image
O=Path('/workspace/mockups/race_state_study/fixed_chase');R=O/'raw';M=json.load(open(O/'camera_staging.json'));F=[];B=[];report={}
for i,(n,s) in enumerate(M.items()):
 fw=s['forward'];rr=s['rear'];F.append(np.array(fw['camera_matrix_world']));B.append(np.array(rr['camera_matrix_world']))
 assert np.allclose(fw['player_world_location'],[0,-28,.16])
 assert np.allclose(fw['rival_world_location'],[-3.3,[-22,-10,-34,-46][i],.16])
 assert fw['lens_mm']==25 and rr['lens_mm']==14 and fw['resolution']==[640,480] and rr['resolution']==[192,64]
 assert s['separation_m']==[6,18,6,18][i]
 for typ in ['unassisted','mirror']:
  a=np.asarray(Image.open(O/(n+'_'+typ+'.png')));b=np.asarray(Image.open(R/(n+'_'+typ+'_native.png')))
  assert a.shape==(960,1280,3) and b.shape==(480,640,3)
  assert np.array_equal(a,np.repeat(np.repeat(b,2,axis=0),2,axis=1))
  assert all(len(np.unique(b[:,:,c]))<=32 for c in range(3))
  Image.fromarray(b).save(R/(n+'_'+typ+'_final_qa.png'))
 # Main frames differ ONLY at mirror rectangle/frame/caption.
 u=np.asarray(Image.open(R/(n+'_unassisted_native.png')));m=np.asarray(Image.open(R/(n+'_mirror_native.png')))
 allowed=np.zeros((480,640),bool);allowed[12:99,220:420]=True
 assert not np.any(np.any(u!=m,axis=2)&~allowed)
 p=np.array(fw['rival_mesh_projection']);p=p[p[:,2]>.1]
 box=[float(p[:,0].min()),float(p[:,0].max()),float(p[:,1].min()),float(p[:,1].max())] if len(p) else None
 mat=np.array(rr['camera_matrix_world']);inv=np.linalg.inv(mat);f=192*14/36
 lights=[]
 for dx in [-.61,.61]:
  pt=inv@np.array([-3.3+dx,rr['rival_world_location'][1]+2.1,.80,1]);z=-pt[2]
  lights.append([float(191-(96+pt[0]/z*f)),float(32-pt[1]/z*f),float(z)])
 report[n]={'gap_m_staging_only':s['separation_m'],'forward_visible':i<2,'forward_mesh_bbox_native':box,'mirror_rival_visible':i>=2,'reference_FX_attachment_centres_flipped_mirror':lights,'reference_FX_spacing_px_not_measured_lamp_centroids':abs(lights[0][0]-lights[1][0]) if i>=2 else None,'rival_mirror_mesh_extent_native_px':np.ptp(np.array(rr['rival_mesh_projection'])[:,:2],axis=0).tolist() if i>=2 else None,'exact_2x_nearest':True,'RGB555':True}
for v in F:assert np.allclose(v,F[0])
for v in B:assert np.allclose(v,B[0])
assert np.array_equal(np.asarray(Image.open(R/'03_close_behind_unassisted_native.png')),np.asarray(Image.open(R/'04_far_behind_unassisted_native.png')))
for n in ['comparison_with_mirror','comparison_unassisted']:
 Image.open(O/(n+'.png')).save(R/(n+'_final_qa.png'))
report['camera']={'player_world':[0,-28,.16],'forward_world':[1.4,-35.6,3.1],'offset_from_player_root_world_axes':[1.4,-7.6,2.94],'target_world':[3.6,-6,-.9],'lens_mm':25,'horizontal_FOV_deg':math.degrees(2*math.atan(36/50)),'vertical_FOV_deg':math.degrees(2*math.atan(27/50)),'euler_XYZ_deg':np.degrees(next(iter(M.values()))['forward']['camera_euler_xyz_radians']).tolist(),'identical_all_four':True,'mirror_world':[0,-28,1.6],'mirror_lens_mm':14,'mirror_horizontal_FOV_deg':math.degrees(2*math.atan(36/28)),'mirror_render':[192,64],'mirror_horizontal_flip':True}
json.dump(report,open(O/'verification.json','w'),indent=2)
print(json.dumps(report,indent=2))
