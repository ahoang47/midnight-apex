import sys, os
from PIL import Image, ImageDraw
d=sys.argv[1]; out=sys.argv[2]; names=sys.argv[3].split(',') if len(sys.argv)>3 else sorted(f[:-4] for f in os.listdir(d) if f.endswith('.png'))
cols=3; w,h=640,480; sc=0.5
rows=(len(names)+cols-1)//cols
S=Image.new('RGB',(int(w*sc)*cols,int((h*sc+14))*rows),(0,0,0)); dr=ImageDraw.Draw(S)
for k,n in enumerate(names):
    im=Image.open(os.path.join(d,n+'.png')).convert('RGB').resize((int(w*sc),int(h*sc)))
    x=(k%cols)*int(w*sc); y=(k//cols)*int(h*sc+14); S.paste(im,(x,y+14)); dr.text((x+2,y),n,fill=(255,255,0))
S.save(out)
