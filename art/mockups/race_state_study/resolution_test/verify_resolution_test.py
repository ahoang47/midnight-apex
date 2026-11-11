from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
O=Path(__file__).resolve().parent
m=json.loads((O/'camera_staging.json').read_text())
old=json.loads(Path('/workspace/mockups/race_state_study/entry_matrix/camera_staging.json').read_text())
CASES=['03_close_behind_center','04_far_behind_outside','04_far_behind_center','04_far_behind_inside','02_ahead_room_center']
checks={}
for name in CASES:
 report={}
 for w,h,mw,mh in [(640,480,192,64),(960,720,288,96)]:
  meta=m[name+'_'+str(w)]
  assert meta['eevee_render_samples']==1 and meta['filter_size']==0 and meta['render_percentage']==100
  for view,dims in [('forward',[w,h]),('rear',[mw,mh])]:
   a=meta[view]; b=old[name][view]
   assert a['resolution']==dims
   for k in ('camera_matrix_world','camera_euler_xyz_radians','lens_mm','sensor_width_mm','player_world_location','rival_world_location'):assert a[k]==b[k],(name,w,view,k)
   assert list(Image.open(O/'raw'/f'{name}_{w}_{view}_base.png').size)==dims
  n=np.asarray(Image.open(O/'native'/f'{name}_{w}_native.png').convert('RGB'))
  assert n.shape==(h,w,3)
  assert all(len(np.unique(n[:,:,i]))<=32 for i in range(3))
  clean=np.asarray(Image.open(O/'display'/f'{name}_{w}_clean.png').convert('RGB'))
  crt=np.asarray(Image.open(O/'display'/f'{name}_{w}_crt.png').convert('RGB'))
  assert clean.shape==crt.shape==(1440,1920,3)
  assert np.array_equal(clean,np.repeat(np.repeat(n,1920//w,0),1920//w,1))
  assert not np.array_equal(clean,crt)
  fp={}
  for view in ('forward','rear'):
   pts=np.array(meta[view]['rival_mesh_projection']); q=pts[pts[:,2]>0]
   fp[view]=[float(x) for x in np.ptp(q[:,:2],axis=0)] if len(q)==len(pts) and len(q) and q[:,2].min()>.1 else None
  report[str(w)]={'native':[w,h],'mirror_native':[mw,mh],'camera_exact_match_entry_matrix':True,'render_samples':1,'filter_size':0,'exact_integer_nearest_clean':True,'projected_unoccluded_mesh_extent_px_NOT_visibility':fp,'full_frame_clean_mean_rgb':float(clean.mean()),'full_frame_crt_mean_rgb':float(crt.mean()),'brightness_ratio_crt_to_clean':float(crt.mean()/clean.mean())}
 old_native=np.asarray(Image.open(Path('/workspace/mockups/race_state_study/entry_matrix/raw')/f'{name}_native.png').convert('RGB'))
 assert np.array_equal(old_native,np.asarray(Image.open(O/'native'/f'{name}_640_native.png').convert('RGB')))
 report['640_native_pixel_identical_to_original_entry_matrix']=True
 if name=='03_close_behind_center':
  report['forward_projection_note']='Whole rival crosses near plane; no finite unclipped projected footprint reported. Genuine lower-edge hood remains, not a complete Entry read.'
  for w in (640,960):
   a=np.array(Image.open(O/'raw'/f'{name}_{w}_forward_base.png'));b=np.array(Image.open(O/'raw'/f'04_far_behind_center_{w}_forward_base.png'));yy,xx=np.nonzero(np.any(a!=b,axis=2))
   report[str(w)]['visible_hood_change_bbox_xyxy_vs_identical_empty_forward_scene']=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
 for view in ('forward','rear'):
  src=Image.open(O/'raw'/f'{name}_640_{view}_base.png').convert('RGB')
  hi=Image.open(O/'raw'/f'{name}_960_{view}_base.png').convert('RGB')
  up=src.resize(hi.size,Image.Resampling.NEAREST)
  assert not np.array_equal(np.asarray(up),np.asarray(hi)),(name,view,'NOT A GENUINE HIGHER RENDER')
  report[view+'_960_differs_from_nearest_scaled_640']=True
  # Framing preserved: normalized per-vertex projected position is unchanged.
  lo_meta=m[name+'_640'][view];hi_meta=m[name+'_960'][view]
  lo_pts=np.array(lo_meta['rival_mesh_projection']);hi_pts=np.array(hi_meta['rival_mesh_projection'])
  assert np.allclose(lo_pts[:,:2]*1.5,hi_pts[:,:2],atol=.00001)
  report[view+'_normalized_vertex_framing_preserved']=True
 # Real painted divider is .11 m wide. Project its width at the rival root's along-road station.
 relevant='forward' if name.startswith('02_') else 'rear'
 for w in (640,960):
  a=m[name+'_'+str(w)][relevant];pw,ph=a['resolution'];inv=np.linalg.inv(np.array(a['camera_matrix_world']));ry=a['rival_world_location'][1]
  def px(x):
   q=inv@np.array([x,ry,.193,1]);return (.5+q[0]/(-q[2])*a['lens_mm']/a['sensor_width_mm'])*pw
  report[str(w)]['projected_0_11m_divider_width_at_rival_station_px']=abs(float(px(-1.65+.055)-px(-1.65-.055)))
 report['divider_width_note']='Geometric projected width; does not guarantee a dash is present at that Y, raster coverage, or visibility through own-car occlusion.'
 checks[name]=report
upstream=Path('/workspace/tools/crt/slang-shaders/crt/shaders/crt-easymode.slang').read_bytes()
assert upstream==(O/'shader'/'crt-easymode.slang').read_bytes()
checks['_shader']={'unchanged_upstream_shader':True,'sha256':hashlib.sha256(upstream).hexdigest(),'preset':'crt_easymode_restrained.slangp','same_parameter_file_all_10_CRT_renders':True}
(O/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print('PASS: five cases, 20 actual view renders, 10 native HUD composites, 20 matching-size clean/CRT outputs, fixed camera matrices and normalized vertex projections, true higher-resolution detail, RGB555, exact integer upscales, unchanged upstream CRT shader.')
