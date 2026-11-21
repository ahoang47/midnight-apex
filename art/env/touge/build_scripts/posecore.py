import json, numpy as np, sys
from roadload import load
d,S,L,R,lot=load()
C=(L+R)/2; NH=(R-L)[:,[0,2]]; NH/=np.linalg.norm(NH,axis=1,keepdims=True)
def pt(s,dd=0.0,h=0.0):
    i=int(np.argmin(abs(S-s))); c=C[i]; p=[c[0]+NH[i][0]*dd, c[1]+h, c[2]+NH[i][1]*dd]; return p
