from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
O=Path(__file__).resolve().parent
FN='/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf'
def font(n):return ImageFont.truetype(FN,n)
WHITE=(220,230,242);DIM=(140,159,180);AMBER=(240,200,148)
CASES=[('03_close_behind_center','S2000 CLOSE BEHIND / CENTER-STY / 6 m'),('04_far_behind_outside','S2000 FAR BEHIND / OUTSIDE-ATK / 18 m'),('04_far_behind_center','S2000 FAR BEHIND / CENTER-STY / 18 m'),('04_far_behind_inside','S2000 FAR BEHIND / INSIDE-DEF / 18 m'),('02_ahead_room_center','S2000 AHEAD WITH ROOM / CENTER-STY / 18 m')]
COLS=[(640,'clean'),(640,'crt'),(960,'clean'),(960,'crt')]
manifest=[]
for name,title in CASES:
 sh=Image.new('RGB',(2640,1560),(5,10,19));d=ImageDraw.Draw(sh);d.fontmode='1'
 def text(x,y,t,n=26,col=WHITE):d.text((x,y),t,font=font(n),fill=col)
 text(20,12,'RESOLUTION EXPERIMENT ONLY — '+title,37)
 text(20,58,'Rival perspective. Yellow Miata = PLAYER / Red S2000 = RIVAL. 6 / 18 m staging only, NOT thresholds.',27,AMBER)
 text(20,94,'Fixed cameras and geometry. PROPOSED UI + MIRROR, not implemented. No future stance tells. 960 is NOT an approved project standard.',25,DIM)
 text(20,133,'OVERVIEW ONLY: previews below are reduced; judge CRT mask / lamp detail using the 1:1 display-space crops and full-size files.',24,DIM)
 for i,(w,kind) in enumerate(COLS):
  x=20+i*650
  label=f'{w} x {w*3//4} / '+('CLEAN NEAREST' if kind=='clean' else 'CRT-EASYMODE')
  text(x,172,label,28,AMBER)
  path=O/'display'/f'{name}_{w}_{kind}.png'
  im=Image.open(path).convert('RGB');assert im.size==(1920,1440)
  sh.paste(im.resize((640,480),Image.Resampling.NEAREST),(x,213))
  text(x,713,'MIRROR — 1:1 DISPLAY PIXELS / 576 x 192',24)
  mirror=im.crop((672,48,1248,240));sh.paste(mirror,(x+32,750))
  mirror.save(O/'comparisons'/f'{name}_{w}_{kind}_mirror_display_1to1.png')
  text(x,961,'NATIVE MIRROR — 1:1 SOURCE PIXELS',23,DIM)
  native=Image.open(O/'native'/f'{name}_{w}_mirror_native.png')
  sh.paste(native,(x+(640-native.width)//2,997))
  text(x,1109,'MAIN VIEW DETAIL — 1:1 DISPLAY PIXELS',24)
  if name.startswith('03_'):box=(0,1120,640,1440)
  elif name.startswith('02_'):box=(580,580,1220,900)
  else:box=(350,780,990,1100)
  crop=im.crop(box);sh.paste(crop,(x,1145));crop.save(O/'comparisons'/f'{name}_{w}_{kind}_main_display_1to1.png')
  text(x,1477,'Crop origin '+str(box[:2])+'; no enlargement or relocation.',22,DIM)
 text(20,1522,json.loads((O/'visual_findings.json').read_text())[name],24,AMBER)
 path=O/'comparisons'/f'{name}_resolution_comparison.png';sh.save(path)
 manifest.append({'case':name,'comparison':path.as_uri(),'frames':{f'{w}_{kind}':(O/'display'/f'{name}_{w}_{kind}.png').as_uri() for w,kind in COLS},'native':{str(w):(O/'native'/f'{name}_{w}_native.png').as_uri() for w in (640,960)}})
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('FIVE_COMPARISON_SHEETS_DONE')

# Accessible vertically stacked crops retain exactly one final display pixel per file pixel.
for name,title in CASES:
 for what,width,height in [('mirror',576,192),('main',640,320)]:
  out=Image.new('RGB',(width,4*(height+34)),(5,10,19));d=ImageDraw.Draw(out);d.fontmode='1'
  for i,(w,kind) in enumerate(COLS):
   y=i*(height+34);d.text((5,y+4),f'{w} x {w*3//4} / {kind.upper()} / 1:1 DISPLAY PIXELS',font=font(22),fill=AMBER)
   out.paste(Image.open(O/'comparisons'/f'{name}_{w}_{kind}_{what}_display_1to1.png'),(0,y+34))
  out.save(O/'comparisons'/f'{name}_{what}_1to1_stack.png')
# Explicitly marked enlarged QA proof is NOT used in gameplay frames.
a=Image.open(O/'raw'/'03_close_behind_center_640_rear_base.png').convert('RGB').resize((288,96),Image.Resampling.NEAREST).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
b=Image.open(O/'raw'/'03_close_behind_center_960_rear_base.png').convert('RGB').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
proof=Image.new('RGB',(1000,490),(5,10,19));d=ImageDraw.Draw(proof);d.fontmode='1'
d.text((16,12),'PROVENANCE DETAIL / 8X QA ZOOM, NOT GAMEPLAY',font=font(32),fill=WHITE)
for i,(im,title) in enumerate([(a,'640 rear source -> 1.5x NEAREST'),(b,'ACTUAL 960 rear render / 288 x 96')]):
 x=16+i*490;d.text((x,62),title,font=font(26),fill=AMBER);proof.paste(im.crop((115,35,173,73)).resize((464,304),Image.Resampling.NEAREST),(x,103))
d.text((16,426),'Same camera / same crop coordinates. New silhouette, texture and lamp samples are not enlarged 640 pixels.',font=font(23),fill=DIM)
d.text((16,457),'Primary gameplay frames never use this QA zoom. Raw sources and render settings retained.',font=font(23),fill=DIM)
proof.save(O/'comparisons'/'verification_genuine_960_detail.png')

# Explicit links to exact source/native renders and practical 1:1 inspection sheets.
manifest=json.loads((O/'manifest.json').read_text())
for row in manifest:
 name=row['case']
 row['mirror_1to1_stack']=(O/'comparisons'/f'{name}_mirror_1to1_stack.png').as_uri()
 row['main_1to1_stack']=(O/'comparisons'/f'{name}_main_1to1_stack.png').as_uri()
 row['native_mirrors']={str(w):(O/'native'/f'{name}_{w}_mirror_native.png').as_uri() for w in (640,960)}
 row['exact_source_renders']={f'{w}_{view}':(O/'raw'/f'{name}_{w}_{view}_base.png').as_uri() for w in (640,960) for view in ('forward','rear')}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
