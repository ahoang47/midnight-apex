import os,json,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
O=Path('/workspace/mockups/pattern_read'); R=O/'raw'
BAYER=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]],np.float32)/16-.5
def rgb555(a):
 h,w=a.shape[:2]; t=np.tile(BAYER,(h//4+1,w//4+1))[:h,:w,None]; return (np.clip(np.floor(a/8+t+.5),0,31)*8.2258).clip(0,255).astype(np.uint8)
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def f(n): return ImageFont.truetype(FN,n)
RED=(232,40,44); GRN=(44,184,74); YEL=(240,200,40); COL={'ATK':RED,'DEF':GRN,'STY':YEL}
WHITE=(220,232,250); EDGE=(85,111,153); AMBER=(255,184,56); INK=(8,8,14); PANEL=(10,14,36)
base=np.asarray(Image.open(R/'raw_entry_blend50.png').convert('RGB')).astype(float)
g=Image.open(R/'glow_entry_blend50.png').convert('RGBA'); a=np.asarray(g).astype(float); lit=Image.fromarray((a[:,:,:3]*a[:,:,3:]/255).astype('uint8')); base=np.clip(base+.22*np.asarray(lit.filter(ImageFilter.GaussianBlur(3))),0,255)
lum=(base*np.array([.299,.587,.114])).sum(-1,keepdims=True); base=np.clip(lum+(base-lum)*1.05,0,255)
A=json.load(open(R/'anchors_entry.json'))
def cut_panel(x,y,x1,y1,c=6): return [(x,y),(x1-c,y),(x1,y+c),(x1,y1),(x+c,y1),(x,y1-c)]

def make(kind):
 frame=base.copy()
 if kind=='B':
  b=np.asarray(Image.open(R/'raw_entry_b_blend50.png').convert('RGB')).astype(float)
  gg=np.asarray(Image.open(R/'glow_entry_b_blend50.png').convert('RGBA')).astype(float)
  ll=Image.fromarray((gg[:,:,:3]*gg[:,:,3:]/255).astype('uint8')); b=np.clip(b+.22*np.asarray(ll.filter(ImageFilter.GaussianBlur(3))),0,255)
  lu=(b*np.array([.299,.587,.114])).sum(-1,keepdims=True);frame=np.clip(lu+(b-lu)*1.05,0,255)
 # Asphalt stencils are perspective-projected 1-bit paint, not floating HUD labels.
 for lab,pts in A['lane_stencils'].items():
  tile=Image.new('RGBA',(80,32)); td=ImageDraw.Draw(tile);td.fontmode='1'; td.text((40,16),lab,font=f(27),fill=(180,181,167,220),anchor='mm')
  dest=[pts[3],pts[2],pts[1],pts[0]];src=[(0,0),(80,0),(80,32),(0,32)]
  M=[];v=[]
  for (x,y),(u,w) in zip(dest,src): M.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-w*x,-w*y]]);v.extend([u,w])
  co=np.linalg.solve(np.array(M),np.array(v)); warped=tile.transform((640,480),Image.Transform.PERSPECTIVE,co,Image.Resampling.NEAREST)
  wa=np.asarray(warped).astype(float);aa=wa[:,:,3:]/255*.5;frame=frame*(1-aa)+wa[:,:,:3]*aa
 semi=Image.new('RGBA',(640,480)); ds=ImageDraw.Draw(semi); solid=Image.new('RGBA',(640,480))
 if kind=='B': solid.paste(Image.open(R/'portrait_focused.png').convert('RGBA'),(20,76))
 d=ImageDraw.Draw(solid); d.fontmode='1'
 def txt(x,y,t,size=12,col=WHITE,anchor='lt'):
  d.text((x+1,y+1),t,font=f(size),fill=INK+(255,),anchor=anchor); d.text((x,y),t,font=f(size),fill=col+(255,),anchor=anchor)
 def panel(x,y,x1,y1,col=EDGE):
  p=cut_panel(x,y,x1,y1); ds.polygon(p,fill=PANEL+(255,)); d.line(p+[p[0]],fill=col+(255,),width=1)
 def chip(x,y,lab,w=58,h=20,col=None):
  c=col or COL[lab]; pts=[(x+5,y),(x+w,y),(x+w-5,y+h),(x,y+h)]; d.polygon(pts,fill=c+(255,)); txt(x+w/2,y+h/2,lab,15,INK if c==YEL else (255,255,255),'mm')
 def tick(x,y): d.line([(x,y+3),(x+3,y+6),(x+8,y)], fill=YEL+(255,),width=2)
 def hand(x,y,counts,label='RIVAL HAND (6)',size=11):
  txt(x,y,label,size,WHITE)
  for i,(st,n) in enumerate(zip(['ATK','DEF','STY'],counts)):
   xx=x+i*65; chip(xx,y+15,st,35,14); txt(xx+39,y+17,'x'+str(n),11,WHITE)
 # Upcoming U-shaped right hairpin icon, one common position / timer language
 panel(214,10,626,53)
 d.line([(226,40),(226,24),(230,20),(242,20),(247,24),(247,39)],fill=AMBER+(255,),width=3)
 d.polygon([(241,34),(253,34),(247,42)],fill=AMBER+(255,))
 txt(260,19,'HAIRPIN R',18); txt(357,42,'LINE LOCK',9,EDGE,'lb')
 for j in range(16): d.polygon([(432+j*9,22),(438+j*9,22),(436+j*9,37),(430+j*9,37)], fill=(AMBER if j<10 else (69,49,38))+(255,))
 txt(609,41,'04.8s',15,AMBER,'rb')
 if kind=='A':
  hand(18,15,[3,2,1])
  # True world-space chevron vertices projected through the shared Blender camera.
  for item in A['road_chevrons']:
   ds.polygon([tuple(v) for v in item['pts']],fill=COL[item['stance']]+(255,))
  pts=A['fork']
  for p,q in zip(pts[:-1],pts[1:]):
   mx=(p[0]+q[0])/2; my=(p[1]+q[1])/2; ds.line([tuple(p),(mx,my)],fill=RED+(95,),width=2)
  txt(pts[-1][0]+4,pts[-1][1]-6,'?',11,(154,117,112))
  # Left-side anchored annotation, road and mesh kept unobscured.
  rx,ry,_=A['rival']; x=18; y=205
  panel(x,y,205,y+56)
  txt(x+8,y+6,'RIVAL LINE: LATE APEX',14)
  chip(x+8,y+27,'DEF',43,17); txt(x+56,y+28,'>',13); chip(x+68,y+27,'DEF',43,17);txt(x+115,y+28,'>',13);chip(x+128,y+27,'ATK',43,17)
  d.line([(205,y+48),(int(rx)-30,int(ry)+24)],fill=EDGE+(255,),width=1)
 else:
  # ENTRY remains a road read: discreet leader only, not an abstract truth chip.
  d.line([(286,172),(286,190),(258,203)],fill=EDGE+(255,),width=1)
  panel(12,66,626,170)
  d.rectangle((19,75,92,148),outline=EDGE+(255,))
  txt(20,153,'RIVAL / FOCUSED',10)
  txt(104,78,'INTENT',17); txt(104,99,'3 CLASHES',11,EDGE); txt(104,115,'27 COMBOS',11,EDGE)
  for i,label in enumerate(['ENTRY','APEX','EXIT']):
   x=226+i*130; txt(x+8,76,label,13); d.line([(x,94),(x+118,94)],fill=EDGE+(255,),width=1)
   if i==0:
    txt(x+8,101,'ON ROAD',14,WHITE); txt(x+8,120,'LANE READ',10,EDGE)
    # Three-lane cross-section: rival sits on the left/mid divider, not a truthful stance chip.
    d.rectangle((x+8,136,x+108,146),fill=(9,12,21,255),outline=EDGE+(255,))
    for xx in [x+41,x+74]: d.line([(xx,137),(xx,145)],fill=WHITE+(255,),width=1)
    d.polygon([(x+34,138),(x+48,136),(x+51,143),(x+37,145)],fill=(94,140,222,255))
    txt(x+109,135,'?',12,AMBER)

   elif i==1:
    d.rectangle((x+8,101,x+109,125), fill=(8,12,24,255))
    for j in range(x+8,x+95,7): d.line([(j,124),(j+16,102)],fill=(32,43,65,255))
    txt(x+59,113,'?',25,WHITE,'mm'); txt(x+8,132,'HIDDEN',11,WHITE)
   else:
    chip(x+8,101,'ATK',70,24); txt(x+95,100,'!',24,AMBER)
    d.line([(x+2,119),(x+2,98),(x+32,98)],fill=AMBER+(255,),width=2);d.line([(x+113,106),(x+113,128),(x+86,128)],fill=AMBER+(255,),width=2)
    txt(x+8,132,'AUDIBLE / FEINT',11,AMBER)
  txt(104,156,'RIVAL HAND (6)',11)
  for i,(st,c) in enumerate(zip(['ATK','DEF','STY'],[2,2,2])):
   x=226+i*130; chip(x+8,155,st,42,13); txt(x+57,156,'x'+str(c),11)
 # Bottom: identical clash column alignment, left hand column mirrors portrait column.
 panel(12,407,626,477)
 txt(20,414,'YOUR LINE LOCK',15)
 txt(20,435,'HAND: ATK x2  DEF x2  STY x1',11)
 txt(20,455,'1 LOCKED / 2 TO SET',11,AMBER)
 for i,label in enumerate(['ENTRY','APEX','EXIT']):
  x=226+i*130; txt(x+8,414,label,12)
  if i==0:
   chip(x+8,432,'STY',64,23);tick(x+86,440);txt(x+8,461,'MID / LOCKED' if kind=='B' else 'LOCKED',10,YEL)
  elif i==1:
   d.line([(x+2,457),(x+2,430),(x+116,430),(x+116,457)],fill=AMBER+(255,),width=1)
   chip(x+9,434,'STY' if kind=='A' else 'ATK',64,20); txt(x+89,439,'< >',12,AMBER)
   txt(x+8,462,'ATK / DEF / STY',11,AMBER)
  else:
   chip(x+8,432,'DEF',64,23);txt(x+8,461,'QUEUED',10,EDGE)
 # shared small in-world hairpin warning, projected ahead and placed over real barrier board zone
 # all UI is crisp opaque pixels over 50/50 panels
 sa=np.asarray(semi).astype(float); al=sa[:,:,3:]/255*.5; frame=frame*(1-al)+sa[:,:,:3]*al
 so=np.asarray(solid); frame=np.where(so[:,:,3:]>127,so[:,:,:3],frame)
 im=Image.fromarray(rgb555(frame)); name='mockup_a_named_lines' if kind=='A' else 'mockup_b_tactical_hud'; im.save(R/(name+'.png')); im.resize((1280,960),Image.Resampling.NEAREST).save(O/(name+'.png'))
 return im
make('A');make('B')
sheet=Image.new('RGB',(2580,1010),(5,8,18));d=ImageDraw.Draw(sheet);d.fontmode='1'
d.text((16,16),'A — NAMED RACING LINES (ROAD-FIRST READ)',font=f(23),fill=WHITE)
d.text((1310,16),'B — 3-SLOT TACTICAL INTENT HUD (ALL 27 COMBOS)',font=f(23),fill=WHITE)
sheet.paste(Image.open(O/'mockup_a_named_lines.png'),(0,50));sheet.paste(Image.open(O/'mockup_b_tactical_hud.png'),(1300,50));sheet.save(O/'compare_a_vs_b.png')
print('WROTE A, B, comparison')
