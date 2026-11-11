from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
O=Path('/workspace/mockups/race_state_study/entry_matrix');R=O/'raw'
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def font(n):return ImageFont.truetype(FN,n)
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

def gameplay(name):
 b=base(name+'_forward');mirror=np.flip(base(name+'_rear'),axis=1).copy();b[16:80,224:416]=mirror
 semi=Image.new('RGBA',(640,480));sd=ImageDraw.Draw(semi);solid=Image.new('RGBA',(640,480));d=ImageDraw.Draw(solid);d.fontmode='1'
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
 native=Image.fromarray(quant(b));native.save(R/(name+'_native.png'));native.resize((1280,960),Image.Resampling.NEAREST).save(O/(name+'.png'))
 Image.fromarray(quant(mirror)).save(R/(name+'_mirror_native.png'))
 return native

def wrap(d,text,f,w):
 lines=[];line=''
 for word in text.split():
  n=(line+' '+word).strip()
  if d.textlength(n,font=f)>w:lines.append(line);line=word
  else:line=n
 if line:lines.append(line)
 return lines

# Observation notes are updated after inspecting real rendered occlusion, not assumed from projection alone.
notes=json.load(open(O/'visibility_notes.json')) if (O/'visibility_notes.json').exists() else {}
for state,*_ in STATES:
 for lane,*_ in LANES:gameplay(state+'_'+lane)
for state,title,gap in STATES:
 sh=Image.new('RGB',(3920,1290),(5,10,19));d=ImageDraw.Draw(sh);d.fontmode='1'
 d.text((20,12),title+' — RIVAL S2000\'S PERSPECTIVE',font=font(37),fill=WHITE)
 d.text((20,57),'Yellow Miata = PLAYER / Red S2000 = RIVAL | '+str(gap)+' m along-road centre gap: illustrative staging only, not a threshold.',font=font(27),fill=(240,200,148))
 d.text((20,93),'PROPOSED UI + MIRROR, NOT IMPLEMENTED | Sample full hand / timer. Player stays CENTER; Entry unconfirmed; Apex / Exit empty. No bluff or future intent tells.',font=font(25),fill=DIM)
 for i,(lane,label) in enumerate(LANES):
  x=20+i*1300;name=state+'_'+lane
  d.text((x,131),label+' — TRUTHFUL ENTRY ONLY',font=font(30),fill=WHITE)
  sh.paste(Image.open(O/(name+'.png')),(x,170))
  yy=1144
  for text in notes.get(name,['Inspect actual forward visibility and reflected road; no lane label is injected into gameplay.']):
   for line in wrap(d,text,font(26),1260):d.text((x,yy),line,font=font(26),fill=WHITE);yy+=31
  d.line([(x,1261),(x+1280,1261)],fill=EDGE,width=1)
 sh.save(O/(state+'_entry_comparison.png'))
# Optional overview uses 1:1 native panels (not an illegible replacement for the individual upscales).
ov=Image.new('RGB',(1960,2300),(5,10,19));d=ImageDraw.Draw(ov);d.fontmode='1'
d.text((10,12),'ENTRY-ONLY MATRIX / PROPOSED PLAYER LINE LOCK + MIRROR',font=font(31),fill=WHITE)
d.text((10,50),'Fixed player/cameras; no bluff. Column labels are external ground truth, not rival HUD tells.',font=font(23),fill=DIM)
for j,(state,title,gap) in enumerate(STATES):
 y=100+j*545;d.text((10,y),title+' / '+str(gap)+' m staging only',font=font(25),fill=(240,200,148))
 for i,(lane,label) in enumerate(LANES):
  x=10+i*650;d.text((x,y+30),label,font=font(21),fill=WHITE);ov.paste(Image.open(R/(state+'_'+lane+'_native.png')),(x,y+58))
ov.save(O/'entry_matrix_overview.png')
print('ENTRY_MATRIX_COMPOSITION_DONE')
