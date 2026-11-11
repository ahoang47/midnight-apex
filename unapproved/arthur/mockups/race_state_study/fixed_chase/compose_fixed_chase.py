from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
import numpy as np,json,math
O=Path('/workspace/mockups/race_state_study/fixed_chase');R=O/'raw'
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def f(n):return ImageFont.truetype(FN,n)
WHITE=(220,230,242);DIM=(140,159,180);EDGE=(71,94,127);AMBER=(240,200,148)
BAYER=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]],np.float32)/16-.5
STATES=[('01_ahead_pressure','1  S2000 AHEAD — UNDER PRESSURE','6 m centre separation'),('02_ahead_room','2  S2000 AHEAD — BREATHING ROOM','18 m centre separation'),('03_close_behind','3  S2000 CLOSE BEHIND PLAYER','6 m centre separation'),('04_far_behind','4  S2000 FAR BEHIND PLAYER','18 m centre separation')]
def quant(a):
 h,w=a.shape[:2];t=np.tile(BAYER,(h//4+1,w//4+1))[:h,:w,None];return (np.clip(np.floor(a/8+t+.5),0,31)*8.2258).clip(0,255).astype('uint8')
def base(name):
 b=np.asarray(Image.open(R/(name+'_base.png')).convert('RGB')).astype(float);g=np.asarray(Image.open(R/(name+'_glow.png')).convert('RGBA')).astype(float)
 lit=Image.fromarray((g[:,:,:3]*g[:,:,3:]/255).astype('uint8'));b=np.clip(b+(0 if name.endswith('_rear') else .22)*np.asarray(lit.filter(ImageFilter.GaussianBlur(3))),0,255)
 lum=(b*np.array([.299,.587,.114])).sum(-1,keepdims=True);return np.clip(lum+(b-lum)*1.05,0,255)
def cut(x,y,x1,y1):return[(x,y),(x1-5,y),(x1,y+5),(x1,y1),(x+5,y1),(x,y1-5)]
def make(name,mirror=False):
 frame=base(name+'_forward');s=Image.new('RGBA',(640,480));sd=ImageDraw.Draw(s);p=Image.new('RGBA',(640,480));d=ImageDraw.Draw(p);d.fontmode='1'
 def text(x,y,t,size=12,col=WHITE):
  d.text((x+1,y+1),t,font=f(size),fill=(5,8,15,255));d.text((x,y),t,font=f(size),fill=col+(255,))
 pts=cut(476,12,628,53);sd.polygon(pts,fill=(10,14,36,255));d.line(pts+[pts[0]],fill=EDGE+(255,),width=1)
 d.line([(489,44),(489,25),(495,21),(507,21),(513,26),(513,39)],fill=AMBER+(255,),width=3);d.polygon([(507,35),(519,35),(513,44)],fill=AMBER+(255,));text(528,24,'HAIRPIN R',16)
 # No rival marker or Entry label: the lane must be read from actual visible geometry.
 text(15,458,'PLAYER / MIATA',11,(240,200,40))
 if mirror:
  # Native 192x64 render, one-to-one in gameplay. Flip the genuine rear-camera image; never relocate/scale the rival.
  m=np.flip(base(name+'_rear'),axis=1).copy()
  frame[16:80,224:416]=m
  d.rectangle((221,13,418,82),outline=(110,127,151,255),width=1)
  d.rectangle((222,14,417,81),outline=(15,20,30,255),width=1)
  text(291,84,'REAR VIEW',9,DIM)
 a=np.asarray(s).astype(float);al=a[:,:,3:]/255*.5;frame=frame*(1-al)+a[:,:,:3]*al;pa=np.asarray(p);frame=np.where(pa[:,:,3:]>127,pa[:,:,:3],frame)
 native=Image.fromarray(quant(frame));suffix='_mirror' if mirror else '_unassisted';native.save(R/(name+suffix+'_native.png'));native.resize((1280,960),Image.Resampling.NEAREST).save(O/(name+suffix+'.png'))
 if mirror:Image.fromarray(quant(m)).save(R/(name+'_mirror_insert.png'))

NOTES=[
('Forward: rival visible in the outside lane; near spacing is legible.','Mirror: no trailing rival; it is ahead of the rear camera.'),
('Forward: rival visible, smaller and farther up the outside lane.','Mirror: no trailing rival; it is ahead of the rear camera.'),
('Forward: rival outside forward view — Entry unavailable unaided.','Mirror: actual trailing headlights and reflected lane markings; assess at native size.'),
('Forward: rival outside forward view — Entry unavailable unaided.','Mirror: rival is only about 9 x 6 native pixels; far-gap lane precision is limited.')]
def wrap(d,t,ft,w):
 lines=[];s=''
 for word in t.split():
  new=(s+' '+word).strip()
  if d.textlength(new,font=ft)>w:lines.append(s);s=word
  else:s=new
 if s:lines.append(s)
 return lines
for name,*_ in STATES:make(name,False);make(name,True)
for assisted in [False,True]:
 sh=Image.new('RGB',(2620,2690),(5,10,19));d=ImageDraw.Draw(sh);d.fontmode='1'
 title='FIXED CHASE / TOP-CENTRE REAR-VIEW MIRROR' if assisted else 'FIXED CHASE / UNASSISTED FORWARD VIEW'
 d.text((20,15),title,font=f(40),fill=WHITE)
 d.text((20,63),'RIVAL S2000\'S PERSPECTIVE | Yellow Miata = PLAYER / Red S2000 = RIVAL',font=f(28),fill=AMBER)
 d.text((20,99),'Mirror is a visual proposal — NOT IMPLEMENTED. Actual rear geometry, horizontally flipped; no relocated cars.' if assisted else 'No mirror, ghost, x-ray, offscreen marker or camera adaptation. Same player-relative camera in every frame.',font=f(25),fill=DIM)
 for i,(name,title,gap) in enumerate(STATES):
  x=20+(i%2)*1300;y=150+(i//2)*1240
  d.text((x,y),title,font=f(31),fill=WHITE);d.text((x,y+36),'RIVAL\'S PERSPECTIVE | '+gap+' — illustrative staging only, not a threshold',font=f(22),fill=DIM)
  suffix='_mirror' if assisted else '_unassisted';sh.paste(Image.open(O/(name+suffix+'.png')),(x,y+70))
  yy=y+1044
  lines=[NOTES[i][0]]+([NOTES[i][1]] if assisted else [])
  if assisted and i>=2:lines+=['Read lane against the reflected road, not a fixed screen-left/right stance rule.']
  for text in lines:
   for ln in wrap(d,text,f(26),1260):d.text((x,yy),ln,font=f(26),fill=WHITE);yy+=31
  d.line([(x,y+1226),(x+1280,y+1226)],fill=EDGE,width=1)
 d.text((20,2642),'Entry is clean Outside = ATK in every case; player stays Center. No Apex/Exit tells, stance table, bluff or specialization claim.',font=f(24),fill=DIM)
 sh.save(O/('comparison_with_mirror.png' if assisted else 'comparison_unassisted.png'))
print('FIXED_CHASE_COMPOSITION_DONE')
