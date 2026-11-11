from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
O=Path('/workspace/mockups/race_state_study/resolution_test');R=O/'raw'
S=1.0
CASES=['03_close_behind_center','04_far_behind_outside','04_far_behind_center','04_far_behind_inside','02_ahead_room_center']
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def font(n):return ImageFont.truetype(FN,round(n*S))
WHITE=(220,230,242);DIM=(140,159,180);EDGE=(71,94,127);AMBER=(255,184,56);PANEL=(10,14,36);INK=(8,10,16)
COL={'ATK':(232,40,44),'DEF':(44,184,74),'STY':(240,200,40)}
STATES=[('01_ahead_pressure','S2000 AHEAD — UNDER PRESSURE',6),('02_ahead_room','S2000 AHEAD — BREATHING ROOM',18),('03_close_behind','S2000 CLOSE BEHIND PLAYER',6),('04_far_behind','S2000 FAR BEHIND PLAYER',18)]
LANES=[('outside','OUTSIDE / ATK'),('center','CENTER / STY'),('inside','INSIDE / DEF')]
BAYER=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]],np.float32)/16-.5

def quant(a):
 h,w=a.shape[:2];t=np.tile(BAYER,(h//4+1,w//4+1))[:h,:w,None];return (np.clip(np.floor(a/8+t+.5),0,31)*8.2258).clip(0,255).astype('uint8')
def base(name):
 b=np.asarray(Image.open(R/(name+'_base.png')).convert('RGB')).astype(float)
 lum=(b*np.array([.299,.587,.114])).sum(-1,keepdims=True);return np.clip(lum+(b-lum)*1.05,0,255)
def cut(x,y,x1,y1,c=5):return[(x,y),(x1-c,y),(x1,y+c),(x1,y1),(x+c,y1),(x,y1-c)]

class NativeDraw:
 # Redraw vector geometry and freshly rasterize fonts at target resolution; never resize a HUD bitmap.
 def __init__(self,im):self.d=ImageDraw.Draw(im);self.d.fontmode='1'
 def xy(self,xy):
  if isinstance(xy[0],(int,float)):return tuple(round(v*S) for v in xy)
  return [tuple(round(v*S) for v in pair) for pair in xy]
 def polygon(self,xy,**kw):self.d.polygon(self.xy(xy),**kw)
 def rectangle(self,xy,**kw):self.d.rectangle(self.xy(xy),**kw)
 def ellipse(self,xy,**kw):self.d.ellipse(self.xy(xy),**kw)
 def line(self,xy,**kw):
  if 'width' in kw:kw['width']=max(1,round(kw['width']*S))
  self.d.line(self.xy(xy),**kw)
 def text(self,xy,*args,**kw):self.d.text(self.xy(xy),*args,**kw)

def gameplay(name,w):
 global S
 S=w/640;h=round(w*.75)
 name=name+'_'+str(w)
 b=base(name+'_forward');mirror=np.flip(base(name+'_rear'),axis=1).copy();b[round(16*S):round(80*S),round(224*S):round(416*S)]=mirror
 semi=Image.new('RGBA',(w,h));sd=NativeDraw(semi);solid=Image.new('RGBA',(w,h));d=NativeDraw(solid)
 def txt(x,y,t,size=12,col=WHITE,anchor='lt'):
  d.text((x+1,y+1),t,font=font(size),fill=INK+(255,),anchor=anchor);d.text((x,y),t,font=font(size),fill=col+(255,),anchor=anchor)
 def panel(x,y,x1,y1,col=EDGE):
  p=cut(x,y,x1,y1);sd.polygon(p,fill=PANEL+(255,));d.line(p+[p[0]],fill=col+(255,),width=1)
 def chip(x,y,st):
  p=[(x+4,y),(x+49,y),(x+45,y+14),(x,y+14)];d.polygon(p,fill=COL[st]+(255,));txt(x+24,y+7,st+' x2',11,INK if st=='STY' else (255,255,255),'mm')
 # Identical top HUD in all twelve. Values are explicitly illustrative in external captions.
 panel(14,12,192,57);txt(23,18,'LINE LOCK',12);txt(183,18,'04.8s',19,AMBER,'rt')
 for j in range(17):d.polygon([(24+j*9,43),(30+j*9,43),(28+j*9,50),(22+j*9,50)],fill=(AMBER if j<10 else (68,52,40))+(255,))
 d.rectangle((221,13,418,82),outline=(110,127,151,255));d.rectangle((222,14,417,81),outline=(15,20,30,255));txt(291,84,'REAR VIEW',9,DIM)
 panel(476,12,628,53);d.line([(489,44),(489,25),(495,21),(507,21),(513,26),(513,39)],fill=(240,200,148,255),width=3);d.polygon([(507,35),(519,35),(513,44)],fill=(240,200,148,255));txt(528,24,'HAIRPIN R',16)
 # Right-side selector intentionally avoids both Miata and possible lower-edge trailing-rival fragments.
 panel(414,107,628,315);txt(422,114,'PLAYER LINE LOCK',15)
 txt(422,133,'HAND (6)',10,DIM)
 chip(473,131,'ATK');chip(523,131,'DEF');chip(573,131,'STY')
 # Entry is a live physical lane choice, not confirmed. Amber cursor and explicit action affordances.
 panel(420,154,622,214,AMBER)
 d.polygon([(425,163),(431,168),(425,173)],fill=AMBER+(255,));txt(438,159,'ENTRY',12,AMBER)
 d.polygon([(475,175),(613,175),(609,193),(471,193)],fill=AMBER+(255,));txt(543,184,'< MID / STY >',15,INK,'mm')
 txt(428,198,'D-PAD LANE',10)
 d.ellipse((538,199,543,204),fill=WHITE+(255,));txt(549,198,'SET',10)
 txt(615,160,'CONFIRM',9,AMBER,'rt')
 # Future player slots are simply empty: no opponent '?' / hidden / feint semantics.
 for lab,y in [('APEX',225),('EXIT',264)]:
  panel(420,y,622,y+31);txt(428,y+9,lab,12);txt(513,y+7,'SET',15,DIM);txt(610,y+11,'NOT SET',9,DIM,'rt')
 txt(422,303,'[L1] / [R1] PHASE',10,DIM);txt(619,303,'0 LOCKED',10,DIM,'rt')
 # All HUD drawing is native 1-bit text/polygons over exact PS1 50/50 panels.
 a=np.asarray(semi).astype(float);al=a[:,:,3:]/255*.5;b=b*(1-al)+a[:,:,:3]*al;p=np.asarray(solid);b=np.where(p[:,:,3:]>127,p[:,:,:3],b)
 native=Image.fromarray(quant(b));native.save(O/'native'/(name+'_native.png'));native.resize((1920,1440),Image.Resampling.NEAREST).save(O/'display'/(name+'_clean.png'))
 Image.fromarray(quant(mirror)).save(O/'native'/(name+'_mirror_native.png'))
 return native


if __name__=='__main__':
 for name in CASES:
  for w in (640,960):gameplay(name,w)
 print('DUAL_RESOLUTION_COMPOSITION_DONE')
