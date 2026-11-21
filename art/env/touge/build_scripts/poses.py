import json, numpy as np, sys
from roadload import load
d,S,L,R,lot=load()
C=(L+R)/2; NH=(R-L)[:,[0,2]]; NH/=np.linalg.norm(NH,axis=1,keepdims=True)
def pt(s,dd=0.0,h=0.0):
    i=int(np.argmin(abs(S-s))); c=C[i]; p=[c[0]+NH[i][0]*dd, c[1]+h, c[2]+NH[i][1]*dd]; return p
P=[]
P.append({'name':'overview_top','pos':[-183,420,140],'look':[-183,-30,22],'fov':48,'far':2000,'fog_off':True})
P.append({'name':'overview_oblique','pos':[-150,170,-260],'look':[-180,-30,30],'fov':50,'far':2000,'fog_off':True})
a,b=501.24,563.24; mid=(a+b)/2
P.append({'name':'lot_overview','pos':pt(a-10,14,22),'look':pt(mid,-(3.75+4)),'fov':55})
P.append({'name':'lot_from_exit_high','pos':pt(b+12,10,18),'look':pt(mid,-(3.75+8)),'fov':55})
P.append({'name':'lot_across_low','pos':pt(mid,3.75+0.5,1.6),'look':pt(mid,-(3.75+14)),'fov':70})
P.append({'name':'gallery_inside','pos':pt(912,-1.5,2.2),'look':pt(945,0.5,2.0),'fov':60})
P.append({'name':'gallery_exit','pos':pt(960,-1.0,2.2),'look':pt(995,0,1.5),'fov':60})
P.append({'name':'gallery_outside','pos':pt(945,-30,10),'look':pt(945,4,10),'fov':60})
P.append({'name':'stack_side_high','pos':pt(935,-60,30),'look':pt(935,4,10),'fov':55,'far':600,'fog_off':True})
P.append({'name':'crossover_t4_under','pos':pt(1055,-1.0,2.2),'look':pt(1090,0,4),'fov':60})
P.append({'name':'crossover_t4_side','pos':pt(1060,2,2.5),'look':pt(1080,0,30),'fov':70})
P.append({'name':'crossover_t5_from_above','pos':pt(440,0,3),'look':pt(470,0,0),'fov':60})
for s in (60,240,520,700,950):
    P.append({'name':'chase_s%d'%s,'chase_s':s,'car_s':s+7,'pos':[0,0,0],'look':[0,0,1],'fov':56.74})
P.append({'name':'flip_s975_wing','pos':pt(966,3,3),'look':pt(978,-6,2),'fov':60})
P.append({'name':'gallery_b_lattice','pos':pt(982,4,3),'look':pt(996,-8,3),'fov':70})
P.append({'name':'canyon_t4_terraces','pos':pt(1080,0,2),'look':pt(1082,-12,14),'fov':80})
P.append({'name':'canyon_t4_down','pos':pt(1100,0,3),'look':pt(1060,0,6),'fov':60})
P.append({'name':'bridge_t4_lamp','pos':pt(380,0,3),'look':pt(386,-8,0),'fov':70})
for s in range(0,1100,100):
    P.append({'name':'sweep_s%04d'%s,'chase_s':s,'car_s':s+7,'pos':[0,0,0],'look':[0,0,1],'fov':56.74})
P.append({'name':'chevrons','car_s':190,'chev_s':[156.0,158.6,161.2,163.8,166.4,169.0,171.6,174.2,176.8],'pos':pt(150,0,3.2),'look':pt(168,0,0),'fov':60})
json.dump({'out':sys.argv[1],'poses':P},open(sys.argv[2],'w'),indent=1)
print(len(P))
