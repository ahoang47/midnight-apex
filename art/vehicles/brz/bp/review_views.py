"""Extra review cameras (high rear/front 3/4, low rear 3/4, top cabin, high rear). usage: blender -b brz_clay.blend -P bp/review_views.py -- OUTDIR TAG"""
import bpy,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'parts')); import render_clay as R
out,tag=sys.argv[sys.argv.index('--')+1:][:2]
R.setup_scene(res=(900,700))
bl=lambda p:(p[1],-p[0],p[2])
V={'hr34':((-5.0,3.6,3.4),(-0.7,0,0.75),55),'hf34':((4.8,3.8,3.2),(0.2,0,0.75),55),
   'r34lo':((-5.2,2.6,1.1),(-1.2,0,0.6),50),'topcab':((-0.4,0,7),(-0.4,0.001,0),60),'rearhi':((-6,0,2.6),(-1.5,0,0.7),70)}
for k,(l,t,lens) in V.items():
    R.cam('V_'+k,bl(l),lens=lens,target=bl(t)); R.shoot(os.path.join(out,f'{k}_{tag}.png'))
