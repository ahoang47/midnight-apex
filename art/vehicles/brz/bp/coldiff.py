"""Column/row-wise blueprint vs clay edges in the blueprint frame (uses bpcompare's rasteriser).
side: top/bottom z per x; top: half-width per x; front/rear: half-width per z."""
import numpy as np, json, sys
sys.argv=[sys.argv[0]]
import importlib.util
spec=importlib.util.spec_from_file_location('bc','bp/bpcompare.py')
src=open('bp/bpcompare.py').read().split('res = {}')[0]
g={}; exec(src,g)
S=g['S']; UP=g['UP']; z=np.load('bp/bp_classes.npz')
def edges(view):
    B,_=g['bpmask'](view); C=g['raster'](view,B.shape); return B,C
out={}
B,C=edges('side'); X0,Y0=g['frame']('side'); CM=float(z['side_CM']); zf=float(z['side_ZF'])
rows=[]
for x in np.arange(2.15,-2.15,-0.05):
    u=int(round(((CM-X0)-x/S)*UP))
    if not (0<=u<B.shape[1]): continue
    def tb(M):
        r=np.nonzero(M[:,u])[0]
        return (None,None) if not len(r) else (((zf-Y0)-r.min()/UP)*S, ((zf-Y0)-(r.max()+1)/UP)*S)
    bt,bb=tb(B); ct,cb=tb(C); rows.append((round(x,2),bt,ct,bb,cb))
out['side']=rows
B,C=edges('top'); X0,Y0=g['frame']('top'); yc=(float(z['top_CR'])+Y0)
rows=[]
for x in np.arange(2.15,-2.15,-0.05):
    u=int(round(((CM-X0)-x/S)*UP))
    if not (0<=u<B.shape[1]): continue
    def hw(M):
        r=np.nonzero(M[:,u])[0]
        return None if not len(r) else max((yc-Y0)-r.min()/UP, (r.max()+1)/UP-(yc-Y0))*S
    rows.append((round(x,2),hw(B),hw(C)))
out['top']=rows
for view in ('front','rear'):
    B,C=edges(view); X0,Y0=g['frame'](view); cc=(float(z[f'{view}_CC'])+X0); zf=float(z[f'{view}_ZF'])
    rows=[]
    for zz in np.arange(1.33,0.0,-0.04):
        v=int(round(((zf-Y0)-zz/S)*UP))
        if not (0<=v<B.shape[0]): continue
        def hw(M):
            from scipy import ndimage as ndi
            lab,n=ndi.label(M[v]); c0=int(round((cc-X0)*UP))
            if lab[c0]==0: return None
            r=np.nonzero(lab==lab[c0])[0]; return max((cc-X0)-r.min()/UP,(r.max()+1)/UP-(cc-X0))*S
        rows.append((round(zz,2),hw(B),hw(C)))
    out[view]=rows
f=lambda v: '  -  ' if v is None else f'{v:.3f}'
if __name__=='__main__':
    print('SIDE x | bp top | clay top | d | bp bot | clay bot | d')
    for x,bt,ct,bb,cb in out['side']:
        print(x,f(bt),f(ct),f(None if bt is None or ct is None else ct-bt),f(bb),f(cb),f(None if bb is None or cb is None else cb-bb))
    print('TOP x | bp hw | clay hw | d')
    for x,b,c in out['top']: print(x,f(b),f(c),f(None if b is None or c is None else c-b))
    for view in ('front','rear'):
        print(view.upper(),'z | bp hw | clay hw | d')
        for zz,b,c in out[view]: print(zz,f(b),f(c),f(None if b is None or c is None else c-b))
