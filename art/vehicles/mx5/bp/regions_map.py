"""Seed-picking aid: label free regions between TRANSPORT+OUTLINE ink, write per-view maps with region centroids (SVG units)."""
import cv2, numpy as np
from scipy import ndimage as ndi
SC=6
T=cv2.imread('raster_transport.png',0)>0; O=cv2.imread('raster_outline.png',0)>0
LAB,n=ndi.label(~(T|O)); rng=np.random.default_rng(1); col=rng.integers(90,255,(n+1,3)).astype(np.uint8); col[0]=0
img=col[LAB]; img[T]=(0,0,0); img[O]=(0,0,255)
sz=ndi.sum(np.ones_like(LAB),LAB,range(n+1)); com=ndi.center_of_mass(np.ones_like(LAB),LAB,range(n+1))
bg=LAB[5,5]
for i in range(1,n+1):
    if i==bg or sz[i]<150 or sz[i]>3e6: continue
    y,x=com[i]; cv2.putText(img,f'{x/SC:.0f},{y/SC:.0f}',(int(x)-40,int(y)+5),0,0.7,(0,0,0),2)
for nm,(u0,v0,u1,v1) in dict(side=(55,55,640,250),top=(55,290,640,590),front=(670,55,965,250),rear=(670,305,965,500)).items():
    cv2.imwrite(f'work_reg_{nm}.png',img[v0*SC:v1*SC,u0*SC:u1*SC])
