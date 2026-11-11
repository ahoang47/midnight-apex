import json,math,textwrap
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
O=Path('/workspace/mockups/race_state_study');R=O/'raw';M=json.load(open(O/'staging.json'))
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def font(n):return ImageFont.truetype(FN,n)
NAVY=(9,16,29);WHITE=(220,230,242);DIM=(141,159,178);EDGE=(65,87,113);RED=(232,40,44);YELLOW=(240,200,40);AMBER=(240,200,148)
BAYER=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]],np.float32)/16-.5
def quant(a):
 h,w=a.shape[:2];t=np.tile(BAYER,(h//4+1,w//4+1))[:h,:w,None];return (np.clip(np.floor(a/8+t+.5),0,31)*8.2258).clip(0,255).astype('uint8')
def panel(x,y,x1,y1):return [(x,y),(x1-5,y),(x1,y+5),(x1,y1),(x+5,y1),(x,y1-5)]
STATES=[
('01_ahead_pressure','1  S2000 AHEAD — UNDER PRESSURE','Miata close behind | 6 m centre separation',
'Tighter apex, accept an exit-speed cost.',
'From the same outside entry, a tighter mid-corner radius could make following harder, at the cost of speed and a less open exit. Not a guaranteed defence.'),
('02_ahead_room','2  S2000 AHEAD — BREATHING ROOM','Miata farther behind | 18 m centre separation',
'Late apex, open the exit.',
'With space behind, one possible continuation is to delay the apex and straighten the car earlier on exit. Available grip and the next section still matter.'),
('03_close_behind','3  S2000 CLOSE BEHIND MIATA','Miata just ahead | 6 m centre separation',
'Delay apex; crossover only if the opening appears.',
'If the Miata runs wide after apex, the S2000 could cross behind its line toward a cleaner exit. The outside entry alone does not promise that opening or a pass.'),
('04_far_behind','4  S2000 FAR BEHIND MIATA','Miata farther ahead | 18 m centre separation',
'Preserve momentum; prioritise a clean exit.',
'A smooth, unforced arc and a clean exit may preserve momentum better than tightening the line to force an unlikely pass. This is a candidate, not an optimum.')]

def gameplay(name):
 b=np.asarray(Image.open(R/(name+'_base.png')).convert('RGB')).astype(float);g=np.asarray(Image.open(R/(name+'_glow.png')).convert('RGBA')).astype(float)
 lit=Image.fromarray((g[:,:,:3]*g[:,:,3:]/255).astype('uint8'));b=np.clip(b+.22*np.asarray(lit.filter(ImageFilter.GaussianBlur(3))),0,255)
 l=(b*np.array([.299,.587,.114])).sum(-1,keepdims=True);b=np.clip(l+(b-l)*1.05,0,255)
 semi=Image.new('RGBA',(640,480));sd=ImageDraw.Draw(semi);solid=Image.new('RGBA',(640,480));d=ImageDraw.Draw(solid);d.fontmode='1'
 def text(x,y,t,size=12,col=WHITE):
  d.text((x+1,y+1),t,font=font(size),fill=(5,8,15,255));d.text((x,y),t,font=font(size),fill=col+(255,))
 p=panel(477,12,628,53);sd.polygon(p,fill=(10,14,36,255));d.line(p+[p[0]],fill=EDGE+(255,),width=1)
 d.line([(490,44),(490,25),(496,21),(508,21),(514,26),(514,39)],fill=AMBER+(255,),width=3);d.polygon([(508,35),(520,35),(514,44)],fill=AMBER+(255,));text(529,24,'HAIRPIN R',16)
 for who in ['rival','player']:
  x,y,z=M[name][who];x=int(x);y=int(y)
  if who=='rival':
   lx=max(12,x-125);ly=y-17;w=104;h=32;lab='RIVAL S2000';sub='OUTSIDE / ATK';col=RED
   end=(lx+w,ly+20);start=(x-9,y+3)
  else:
   lx=min(510,x+20);ly=y-8;w=108;h=21;lab='PLAYER MIATA';sub=None;col=YELLOW
   end=(lx,ly+13);start=(x+9,y+4)
  p=panel(lx,ly,lx+w,ly+h);sd.polygon(p,fill=(10,14,36,255));d.line(p+[p[0]],fill=EDGE+(255,),width=1)
  d.line([start,end],fill=col+(255,),width=1);text(lx+6,ly+4,lab,12,col)
  if sub:text(lx+6,ly+18,sub,10,WHITE)
 # No portrait, hand, true route, Apex/Exit readout, reaction badge or motion cue.
 a=np.asarray(semi).astype(float);al=a[:,:,3:]/255*.5;b=b*(1-al)+a[:,:,:3]*al;s=np.asarray(solid);b=np.where(s[:,:,3:]>127,s[:,:,:3],b)
 im=Image.fromarray(quant(b));im.save(R/(name+'_native.png'));im.resize((1280,960),Image.Resampling.NEAREST).save(O/(name+'.png'))
 return im

def cubic(p0,p1,p2,p3,n=40):
 return [tuple((1-t)**3*np.array(p0)+3*(1-t)**2*t*np.array(p1)+3*(1-t)*t*t*np.array(p2)+t**3*np.array(p3)) for t in np.linspace(0,1,n)]
def dashed(d,pts,col,width=3,on=9,off=6):
 phase=0;last=None
 for a,b in zip(pts[:-1],pts[1:]):
  a=np.array(a);b=np.array(b);dist=np.linalg.norm(b-a)
  for t in np.arange(0,dist,.7):
   p=a+(b-a)*t/max(dist,1e-9)
   if int(phase)%(on+off)<on:
    if last is not None:d.line([tuple(last),tuple(p)],fill=col,width=width)
    last=p
   else:last=None
   phase+=.7

def diagram(i):
 im=Image.new('RGB',(340,274),(10,17,29));d=ImageDraw.Draw(im);d.fontmode='1'
 # Heading lives in the empty infield, not over the corner path.
 # U-shaped right hairpin; car positions at selection are schematic, not predicted future positions.
 pts=[(70,y) for y in range(253,129,-2)]+[(160-90*math.cos(t),130-90*math.sin(t)) for t in np.linspace(0,math.pi,70)]+[(250,y) for y in range(130,254,2)]
 d.line(pts,fill=(48,59,71),width=48);dashed(d,pts,(94,109,123),1,6,7)
 d.line([(45,254),(45,130)],fill=(124,128,125),width=1);d.line([(95,254),(95,130)],fill=(124,128,125),width=1)
 common=[(50,y) for y in range(251,129,-2)]
 if i==0:
  route=common+cubic((50,130),(50,80),(99,64),(160,62))+cubic((160,62),(213,59),(252,89),(252,135))+cubic((252,135),(251,168),(264,212),(263,249))
 elif i==1:
  route=common+cubic((50,130),(47,59),(105,17),(165,24))+cubic((165,24),(230,25),(250,59),(231,96))+cubic((231,96),(228,137),(242,193),(245,250))
 elif i==2:
  route=common+cubic((50,130),(47,52),(110,18),(168,25))+cubic((168,25),(229,27),(252,64),(231,108))+cubic((231,108),(226,143),(235,202),(240,250))
 else:
  route=common+cubic((50,130),(48,67),(104,25),(162,27))+cubic((162,27),(220,28),(261,74),(258,132))+cubic((258,132),(258,174),(255,218),(254,250))
 dashed(d,route,RED,3,8,6)
 # Fixed outside Entry marker, not improper placement. Same orientation in every condition.
 d.polygon([(45,196),(50,190),(55,196),(55,210),(45,210)],fill=RED,outline=(245,153,148))
 my=[215,245,185,155][i]
 d.polygon([(74,my-7),(79,my-13),(84,my-7),(84,my+7),(74,my+7)],fill=YELLOW,outline=(255,236,160))
 d.text((5,194),'S2000',font=font(12),fill=RED);d.text((103,my-8),'MIATA',font=font(15),fill=YELLOW)
 d.text((108,110),'DESIGN DIAGRAM',font=font(16),fill=DIM)
 d.text((128,129),'NOT HUD',font=font(16),fill=DIM)
 d.text((10,255),'Same outside Entry; arrows travel upward',font=font(16),fill=DIM)
 return im

def wrap(d,text,ft,width):
 words=text.split();lines=[];line=''
 for w in words:
  n=(line+' '+w).strip()
  if d.textlength(n,font=ft)>width:lines.append(line);line=w
  else:line=n
 if line:lines.append(line)
 return lines

for state in STATES:gameplay(state[0])
W,H=2620,2860;sheet=Image.new('RGB',(W,H),(5,10,19));d=ImageDraw.Draw(sheet);d.fontmode='1'
d.text((20,15),'SAME ENTRY. DIFFERENT RACE STATE.',font=font(42),fill=WHITE)
d.text((20,65),'RIVAL S2000\'S PERSPECTIVE  |  Yellow Miata = PLAYER  /  Red S2000 = RIVAL',font=font(28),fill=AMBER)
d.text((20,102),'Fixed right hairpin. Outside = ATK in all four. Gap values are illustrative staging, not design thresholds.',font=font(25),fill=DIM)
for i,(name,title,sub,tech,body) in enumerate(STATES):
 x=20+(i%2)*1300;y=150+(i//2)*1345
 d.text((x,y),title,font=font(31),fill=WHITE)
 d.text((x,y+36),'RIVAL\'S PERSPECTIVE  |  '+sub+' (staging only)',font=font(23),fill=DIM)
 sheet.paste(Image.open(O/(name+'.png')),(x,y+70))
 d.line([(x,y+1030),(x+1280,y+1030)],fill=EDGE,width=2)
 di=diagram(i);di.save(R/(name+'_diagram.png'));sheet.paste(di,(x,y+1045))
 tx=x+365;ty=y+1046
 d.text((tx,ty),'ILLUSTRATIVE CONTINUATION — NOT A STANCE TABLE',font=font(25),fill=AMBER)
 d.text((tx,ty+35),tech,font=font(29),fill=WHITE)
 yy=ty+77
 for line in wrap(d,body,font(26),900):d.text((tx,yy),line,font=font(26),fill=WHITE);yy+=30
 d.text((tx,yy+10),'Red dashes = possible rival route; yellow car = Miata at selection.',font=font(21),fill=DIM)
 d.text((tx,yy+37),'Diagram is schematic. No future stance labels or guaranteed best choice.',font=font(21),fill=DIM)
 d.line([(x,y+1332),(x+1280,y+1332)],fill=EDGE,width=1)
d.text((20,2830),'No specialization-specific habit table assumed. Apex/Exit mapping remains unresolved. Full player line locks before playback.',font=font(22),fill=DIM)
sheet.save(O/'four_panel_race_state_study.png')
print('STUDY_COMPOSITION_DONE')
