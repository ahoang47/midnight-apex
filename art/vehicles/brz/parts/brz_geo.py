"""BRZ (ZD8, 2021+) low-poly clay body: pure-numpy geometry, no bpy.
Car frame: x forward (0 = mid-wheelbase), y to the car's left, z up from ground. Metres.
Body = loft of half cross-sections (12 pts each, mirrored) through key stations, monotone-cubic
interpolated along x. Two layers: LOWER (hood / fenders / doors / hips / deck) and UPPER (cabin),
the cabin is pulled down by the measured centre-line envelope (windshield, roof, rear glass)
and the body takes max(lower, upper). Key numbers come from keyline_table.md."""
import numpy as np

WB = 2.575; AXF = WB/2; AXR = -WB/2
X_TIP_F, X_TIP_R = AXF + 0.8575, AXR - 0.8395
TIRE_OD, TIRE_W, RIM_D = 0.632, 0.215, 0.457
TRACK_F, TRACK_R = 1.520, 1.550
ARCH_F = dict(xc=AXF, zc=TIRE_OD/2, r=0.360)
ARCH_R = dict(xc=AXR, zc=TIRE_OD/2, r=0.368)
NP = 12   # points per half section: p0 bottom .. p11 centre-top

# ---------- key stations, LOWER layer: x -> 12 x (y, z[, dx]) ----------
K = {}; KDX = {}
def ks(x, *pts):
    a=np.array([list(p)+[0.0]*(3-len(p)) for p in pts],float).reshape(NP,3)
    K[x]=a[:,:2]; KDX[x]=a[:,2]
CAB = [(.63,.86),(.50,.86),(.34,.86),(.17,.86),(0,.86)]  # lower-layer filler under the cabin
# nose: the tip station is a vertical line on the centre-line, so the front face is a pointed wedge (plan + side)
ks( 2.145, (0,.21,-.11),(0,.27,-.075),(0,.335,-.04),(0,.40,-.012),(0,.455,0),(0,.485,0),(0,.505,-.008),(0,.52,-.02),(0,.532,-.03),(0,.54,-.038),(0,.544,-.044),(0,.546,-.05))
ks( 2.090, (.22,.185),(.29,.24),(.33,.32),(.345,.40),(.335,.465),(.31,.51),(.26,.535),(.20,.548),(.15,.555),(.10,.56),(.05,.563),(0,.565))
ks( 2.040, (.40,.18,-.03),(.46,.24,-.02),(.49,.33,-.01),(.505,.41),(.51,.48),(.48,.535),(.42,.57),(.34,.58),(.26,.585),(.17,.588),(.085,.59),(0,.591))
ks( 1.980, (.52,.175,-.02),(.575,.24,-.012),(.605,.34),(.615,.43),(.62,.49),(.585,.545),(.50,.585),(.44,.598),(.34,.607),(.23,.612),(.115,.614),(0,.615))
ks( 1.890, (.61,.17),(.665,.24),(.69,.35),(.705,.45),(.695,.53),(.66,.585),(.585,.63),(.50,.632),(.39,.638),(.265,.642),(.13,.644),(0,.645))
ks( 1.800, (.71,.17),(.77,.25),(.79,.37),(.79,.48),(.775,.58),(.73,.635),(.655,.68),(.585,.655),(.43,.66),(.29,.663),(.145,.664),(0,.665))
ks( 1.650, (.80,.18),(.84,.27),(.855,.40),(.855,.53),(.84,.645),(.79,.705),(.69,.737),(.625,.700),(.46,.695),(.31,.698),(.155,.70),(0,.701))
ks( 1.450, (.84,.18),(.865,.28),(.878,.42),(.878,.56),(.868,.69),(.81,.79),(.705,.820),(.64,.755),(.47,.745),(.32,.748),(.16,.75),(0,.751))
ks( 1.200, (.85,.18),(.875,.28),(.887,.42),(.887,.58),(.877,.71),(.82,.822),(.715,.852),(.65,.785),(.48,.772),(.33,.775),(.165,.777),(0,.778))
ks( 0.950, (.85,.18),(.875,.28),(.885,.42),(.886,.58),(.876,.73),(.822,.838),(.725,.870),(.655,.805),(.49,.797),(.335,.799),(.17,.80),(0,.801))
ks( 0.780, (.85,.18),(.878,.25),(.858,.34),(.884,.50),(.874,.74),(.825,.842),(.735,.884),(.665,.832),(.50,.826),(.34,.828),(.17,.829),(0,.830))
ks( 0.400, (.85,.185),(.882,.255),(.845,.36),(.886,.54),(.876,.75),(.83,.845),(.745,.882),*CAB)
ks(-0.300, (.85,.19),(.884,.27),(.842,.39),(.887,.58),(.878,.76),(.835,.85),(.75,.885),*CAB)
ks(-0.700, (.855,.20),(.885,.285),(.848,.43),(.893,.62),(.885,.77),(.845,.865),(.755,.91),(.63,.93),(.50,.95),(.34,.96),(.17,.965),(0,.967))
ks(-0.950, (.86,.21),(.885,.30),(.885,.45),(.90,.63),(.89,.775),(.85,.885),(.765,.95),(.64,.98),(.51,.99),(.35,.995),(.175,.998),(0,1.0))
ks(-1.290, (.87,.22),(.895,.31),(.903,.45),(.905,.61),(.89,.775),(.845,.885),(.76,.955),(.63,.975),(.50,.985),(.34,.99),(.17,.993),(0,.995))
ks(-1.550, (.83,.235),(.872,.32),(.893,.46),(.90,.60),(.885,.755),(.835,.865),(.755,.930),(.625,.945),(.49,.952),(.33,.956),(.165,.958),(0,.959))

# ---------- rear zone (pass 3): generated, not hand-keyed ----------
# Every section column p_i runs from x0 (just behind the rear arch) round the corner and across the rear face to the
# centre line, following one plan curve (REAR_PLAN: blueprint top-view outline at bumper height, ending in a convex
# ~3 cm bow) scaled to the column's own half-width W and tail end x_e. Columns therefore run horizontally across the
# rear face (crease, taillight band, lip are column lines) and the last station collapses onto the centre-line
# tail profile (side photo), like the nose.  Tail profile x_e / z per column is the side photo's centre-line tail.
import brz_bp as BP
REAR_X0 = -1.60
# plan = blueprint top-view half-width from the hips to the tail (incl. the bumper / trim tip at -2.12)
REAR_PLAN = np.array([(-1.60,.912),(-1.65,.893),(-1.70,.866),(-1.75,.838),(-1.80,.812),(-1.85,.788),(-1.90,.760),
    (-1.95,.722),(-2.00,.655),(-2.04,.590),(-2.07,.525),(-2.09,.455),(-2.105,.37),(-2.115,.27),(-2.12,.15),(-2.122,.07),(-2.123,0.0)])
# hip section at the start of the rear zone = blueprint rear-view outline (half-width per height), all heights blueprint:
#   z .17-.45 hw .90, .57-.65 .925, .73 .90, .77 .887, .85 .873, .93 .816, .97 .746 (cabin flank / deck edge)
HIP = [(.858,.160),(.900,.300),(.915,.450),(.925,.600),(.905,.720),(.872,.800),(.858,.872),(.812,.930),
       (.745,.972),(.500,1.012),(.250,1.026),(.000,1.030)]
#            z(tail)  x_e     plan exponent (<1 = squarer corner)   tail = blueprint side view at the centre line
REAR_COL = [(.225, -2.050, 1.00),   # p0 diffuser bottom
            (.300, -2.115, 1.00),   # p1 grey lower trim tip
            (.450, -2.123, 1.00),   # p2
            (.580, -2.105, 0.95),   # p3 bumper top
            (.665, -2.090, 0.85),   # p4 bumper top ledge -> rear face
            (.775, -2.036, 0.62),   # p5 taillight bottom (side view: slants .83 -> .77)
            (.895, -2.032, 0.52),   # p6 taillight top / trunk shut line
            (.985, -2.030, 0.40),   # p7 ducktail lip edge (deck .99, rear face vertical .99 -> .67)
            (None, -2.026, 0.42),   # p8..p11 deck (REAR_DECK + crossfall)
            (None, -2.026, 0.50),
            (None, -2.026, 0.50),
            (None, -2.026, 0.50)]
# detail pass: optional rear-face rake / rounder-corner override {"p5": [x_e, exponent], ...} (set by build_brz_detail.py)
import os as _os, json as _json
for _k, (_xe, _ex) in _json.loads(_os.environ.get('BRZ_REAR_TWEAK', '{}') or '{}').items():
    REAR_COL[int(_k[1:])] = (REAR_COL[int(_k[1:])][0], _xe, _ex)
REAR_XB = [1.0,1.0,1.0,1.0,0.95,0.80,0.70,0.65,0.65,0.65,0.65,0.65]
REAR_DECK = np.array([(-2.026,.993),(-1.95,.993),(-1.85,.995),(-1.75,1.004),(-1.66,1.020),(-1.60,1.030)])  # side silhouette
REAR_N = 11
def rear_zone():
    P_=REAR_PLAN; seg=np.hypot(np.diff(P_[:,0]),np.diff(P_[:,1])); cum=np.r_[0,np.cumsum(seg)]
    L_ref=REAR_X0-P_[-1,0]; out=[]
    for k in range(REAR_N+1):
        sa=cum[-1]*k/REAR_N; xr=np.interp(sa,cum,P_[:,0]); yr=np.interp(sa,cum,P_[:,1])
        xi=(REAR_X0-xr)/L_ref; yn=yr/P_[0,1]
        pts=[]
        for (zr,xe,ex),xb,(W,z0) in zip(REAR_COL,REAR_XB,HIP):
            W=W*float(P_[0,1])/0.925
            x=REAR_X0-xi**xb*(REAR_X0-xe); y=W*yn**ex if yn>0 else 0.0
            if zr is None:
                d=REAR_DECK; zc=float(pchip(d[:,0],d[:,1],np.array([x]))[0])
                z=zc-(REAR_DECK[-1,1]-z0)*(1-xi)
            else:
                t=min(xi/0.75,1.0); t=t*t*(3-2*t); z=z0+(zr-z0)*t
            pts.append((y,z,x))
        out.append((xr,pts))
    return out

for _x, _dz in ((1.98, .012), (1.89, .022), (1.80, .028), (1.65, .022)):   # hood sits lower between the front fender peaks
    for _i, _w in ((7, .5), (8, .9), (9, 1.0), (10, 1.0), (11, 1.0)):
        K[_x][_i,1] -= _dz * _w
for _x in [k for k in K if 0.70 < k < 1.85]:
    _c = K[_x][11,1]
    for _i, _d in ((7, .010), (8, .022), (9, .012), (10, .003)):
        K[_x][_i,1] = min(K[_x][_i,1], _c - _d) if _i > 7 else K[_x][_i,1] - _d
# ---------- pass 4: every station re-fitted to the blueprint (S2000 method) ----------
# The section templates above only carry the *shape* (fender peaks, hood valley, door scoop, rocker blade); width and
# height are re-derived per station from the blueprint: plan half-width W(x) (top view), bottom ZB(x) and top ZT(x)
# (side view) ahead of the windshield, and the beltline (side DLO bottom, z .90-.93) under the cabin.
BELT = np.array([(0.78,.915),(0.40,.892),(-0.30,.895),(-0.70,.915),(-0.95,.950),(-1.29,.965)])
def _fit():
    out={}; outdx={}
    for x in sorted(K):
        sec=K[x].copy(); dx=KDX[x].copy()
        xn = 1.65+(x-1.65)*1.045 if x>1.65 else x          # nose tip x 2.168 (blueprint side + top)
        if x>1.65: dx=dx*1.045
        zb0=sec[:,1].min()
        zb=float(np.clip(BP.ZB(xn),0.150,0.40)) if xn>1.62 or xn<-1.62 else 0.152
        if xn>=0.75: ref=sec[:,1].max(); tgt=float(BP.ZT(xn))
        else: ref=sec[6,1]; tgt=float(np.interp(xn,BELT[::-1,0],BELT[::-1,1]))
        sec[:,1]=zb+(sec[:,1]-zb0)*(tgt-zb)/(ref-zb0)
        m_=sec[:7,0].max()
        if m_>1e-6: sec[:,0]*=float(BP.W(xn))/m_
        if xn>=0.75:     # hood centre: blueprint front view hides the windshield bottom below z .93 -> the cowl sits at
                         # ~.915 and the hood runs only 1-3 cm under the fender peaks (pass-3 photo sink was 7 cm)
            zc=float(BP.ZT(xn))-float(np.interp(xn,[0.78,0.95,1.2,1.45,1.65,1.8,1.9,2.0,2.2],[.005,.012,.022,.028,.030,.030,.025,.015,.010]))
            dlt=zc-sec[11,1]
            if dlt>0:
                for _i,_w in ((7,.6),(8,1.0),(9,1.0),(10,1.0),(11,1.0)): sec[_i,1]+=dlt*_w
        out[round(xn,4)]=sec; outdx[round(xn,4)]=dx
    K.clear(); K.update(out); KDX.clear(); KDX.update(outdx)
_fit()
K.pop(-1.55,None); KDX.pop(-1.55,None)
_h=np.array(HIP); _h[:,0]*=float(BP.W(-1.45))/0.925; K[-1.45]=_h; KDX[-1.45]=np.zeros(NP)
_h=np.array(HIP); _h[:,0]*=float(BP.W(-1.29))/0.925; _h[7:,1]=[.94,.975,1.0,1.01,1.012]; _h[6,1]=.875
K[-1.29][:]=np.where(np.arange(NP)[:,None]>=5,_h,K[-1.29]); 

# ---------- centre-line glass/roof envelope (side photo, solved camera) ----------
_ex=np.arange(0.80,-2.21,-0.05); _ez=BP.ZT(_ex); _ez=np.convolve(np.r_[_ez[0],_ez,_ez[-1]],np.ones(3)/3,'valid')
_ez[_ex<-1.95]=0.99
ENV = np.c_[_ex,_ez]                       # centre-line roof/glass line = blueprint side silhouette (fin removed)
ROOF_C = 1.276
LAG_F, LAG_R = 0.28, 0.30
USE_UPPER = False   # cabin is now the separate greenhouse ring-loft below   # windshield sides swept back / rear glass sides drop sooner (per y^2)

def pchip(xk, yk, x):
    """Fritsch-Carlson monotone cubic, xk ascending."""
    xk=np.asarray(xk,float); yk=np.asarray(yk,float); x=np.atleast_1d(np.asarray(x,float))
    h=np.diff(xk); d=np.diff(yk,axis=0)/h.reshape(-1,*([1]*(yk.ndim-1)))
    m=np.zeros_like(yk)
    m[0]=d[0]; m[-1]=d[-1]
    for i in range(1,len(xk)-1):
        a,b=d[i-1],d[i]; w1=2*h[i]+h[i-1]; w2=h[i]+2*h[i-1]
        with np.errstate(divide='ignore',invalid='ignore'):
            mm=(w1+w2)/(w1/a+w2/b)
        m[i]=np.where((a*b)>0,mm,0.0)
    i=np.clip(np.searchsorted(xk,x)-1,0,len(xk)-2)
    t=((x-xk[i])/h[i]).reshape(-1,*([1]*(yk.ndim-1)))
    hh=h[i].reshape(t.shape)
    h00=2*t**3-3*t**2+1; h10=t**3-2*t**2+t; h01=-2*t**3+3*t**2; h11=t**3-t**2
    return h00*yk[i]+h10*hh*m[i]+h01*yk[i+1]+h11*hh*m[i+1]

# rear zone stations need pchip
for _xr,_pts in rear_zone()[1:]:
    ks(_xr,*[(y,z,x-_xr) for y,z,x in _pts])
ks(REAR_X0,*[(y,z) for y,z,x in rear_zone()[0][1]])

def env(x):
    e=ENV[::-1]; return pchip(e[:,0],e[:,1],np.clip(x,e[0,0],e[-1,0]))

def lower_section(x):
    xs=np.array(sorted(K)); arr=np.stack([K[k] for k in xs])
    return pchip(xs,arr,np.clip(x,xs[0],xs[-1]))[0]

def section_dx(x):
    xs=np.array(sorted(K)); arr=np.stack([KDX[k] for k in xs])
    return pchip(xs,arr,np.clip(x,xs[0],xs[-1]))[0]

def cabin_section(x):
    """uncut cabin p7..p11 (y,z), centre at ROOF_C; tapers in plan toward the rear (coke-bottle cabin)."""
    taper=np.interp(x,[-1.6,-0.9,-0.3,0.4,0.9],[0.80,0.90,0.985,1.0,1.0])
    belt=np.interp(x,[-1.2,-0.9,-0.6,0.9],[1.00,0.975,0.89,0.885])
    p=np.array([(0.700,0.5*(belt+ROOF_C-.110)),(0.620,ROOF_C-.110),(0.570,ROOF_C-.060),(0.300,ROOF_C-.013),(0.0,ROOF_C)])
    p[:,0]*=taper
    return p

def section(x):
    """returns (12,2) final half-section and per-point flags (cabin weight)."""
    lo=lower_section(x).copy(); out=lo.copy(); wcab=np.zeros(NP)
    if USE_UPPER and -1.75 < x < 0.95:
        up=cabin_section(x)
        for j in range(5):
            i=7+j; y=up[j,0]
            xe = x + LAG_F*y*y if x > -0.5 else x - LAG_R*y*y
            drop=max(0.0, ROOF_C-float(env(xe)[0]))
            zu=up[j,1]-drop
            t=np.clip((zu-lo[i,1])/0.05,0,1); t=t*t*(3-2*t)
            out[i,0]=lo[i,0]+(up[j,0]-lo[i,0])*t
            out[i,1]=max(lo[i,1],zu); wcab[i]=t
        # keep columns ordered (outside -> centre), and z monotone up the side
        for i in range(7,NP): out[i,0]=min(out[i,0],out[i-1,0]-0.004)
    return out, wcab

def arch_z(x):
    z=np.full_like(np.atleast_1d(x),-1.0,dtype=float)
    for A in (ARCH_F,ARCH_R):
        d=np.abs(x-A['xc']); m=d<A['r']
        z[m]=np.maximum(z[m],A['zc']+np.sqrt(A['r']**2-d[m]**2))
    return z

def stations():
    xs=list(sorted(K,reverse=True))
    extra=list(np.arange(AXF+0.34,AXF-0.36,-0.06))+list(np.arange(AXR+0.36,AXR-0.37,-0.06))
    extra+=list(np.arange(0.70,-0.92,-0.16))+[2.118,2.065,2.012,1.935,1.85]
    keys=np.array(xs)
    extra=[e for e in np.round(extra,4) if np.min(np.abs(keys-e))>=(0.02 if abs(e)>1.8 else 0.045) and e>REAR_X0]
    return np.array(sorted(set(list(keys)+extra),reverse=True))

def build():
    """returns verts (N,3), quads list, per-vertex tags, grid shape."""
    X=stations(); S=len(X); C=2*NP-1
    V=np.zeros((S,C,3)); W=np.zeros((S,C)); P=np.zeros((S,C),int)
    for s,x in enumerate(X):
        sec,wc=section(x); dx=section_dx(x)
        az=arch_z(np.array([x]))[0]
        if az>0:   # wheel arch: lift the lower side points over the arch, flush lip at max width
            ymax=sec[:4,0].max(); off=[0.0,0.012,0.03,0.055,0.085]
            for i in range(5):
                if sec[i,1] < az+off[i]:
                    sec[i,1]=az+off[i]; sec[i,0]=ymax-(0.006 if i==0 else 0)
            for i in range(1,7): sec[i,1]=max(sec[i,1],sec[i-1,1]+0.01)
        for i in range(NP):
            for c,sign in ((i,1),(C-1-i,-1)):
                V[s,c]=(x+dx[i],sign*sec[i,0],sec[i,1]); W[s,c]=wc[i]; P[s,c]=i
    return X,V,W,P

# ======================= greenhouse (pass 4: every line from the blueprint glass outlines) =======================
# Columns j (left half, front centre -> rear centre); each column carries four blueprint points:
#   base (on the body), belt (glass bottom), gtop (glass top), and its roof-edge point from GH_ROWS.
#  windshield j0..j3 : base = top-view windshield base arc (x .765 centre -> corner (.60,.68)); top = header row
#  side DLO   j4..j8 : base y = top-view outer side-glass edge (.735), belt z = side DLO bottom (.90 -> .93, kick-up to
#                      .985 at the quarter-glass tail x -.92); gtop = side DLO top line (A-pillar inner edge from the
#                      front tip (.50,.90) to (0,1.19), top 1.20 over the door, falling to 1.04 at the quarter tail),
#                      y = top-view inner side-glass edge (.645-.68)
#  C-pillar   j9     : no glass
#  rear glass j10..j13: top-view rear glass base (corner (-1.45,.48), centre -1.58), z on the deck (1.03); sides +-.48
# Roof rows (x_edge, y_edge, x_centre): header (windshield top corners (.25,.60), centre .14), roof rail above the
# DLO (y .615-.63), rear-glass top (corners (-1.0,.47), centre -.97). Edge heights from the rear/front views
# (roof edge .05-.06 below the 1.30 centre at y .6; windshield / rear-glass top corners 1.19).
GH_ROWS = [(0.25,.600,0.14),(-0.03,.625,-0.03),(-0.20,.630,-0.20),(-0.45,.630,-0.45),(-0.68,.615,-0.68),
           (-0.88,.570,-0.88),(-0.94,.525,-0.94),(-1.00,.470,-0.97)]
GH_EDGE_DROP = [0.022, 0.050, 0.052, 0.052, 0.050, 0.046, 0.040, 0.025]
GH_F = [0.0, 0.3, 0.65, 1.0]
GH_BUBBLE = 0.004
GH_GLASS_TOP = 3
SIDE_BULGE = 0.022
#        base (x, y)          belt z    gtop (x, y, z)            kind
GH_COL = [((0.765,0.000), None, None, 'ws'), ((0.735,0.330), None, None, 'ws'), ((0.690,0.500), None, None, 'ws'),
          ((0.600,0.680), None, None, 'ws'),
          ((0.500,0.737), 0.900, (0.000,0.655,1.190), 'side'),
          ((0.000,0.739), 0.902, (-0.200,0.650,1.200), 'side'),
          ((-0.450,0.735), 0.915, (-0.450,0.645,1.195), 'side'),
          ((-0.690,0.725), 0.930, (-0.660,0.655,1.135), 'side'),
          ((-0.920,0.712), 0.985, (-0.925,0.685,1.040), 'side'),
          ((-1.250,0.745), None, None, 'cp'),
          ((-1.450,0.480), None, None, 'rg'), ((-1.520,0.360), None, None, 'rg'), ((-1.560,0.200), None, None, 'rg'),
          ((-1.580,0.000), None, None, 'rg')]
GH_BASE = [c[0] for c in GH_COL]
NJ = len(GH_COL)

def body_top_z(x, y):
    sec = lower_section(x)[5:]               # p5..p11, y decreasing
    return float(np.interp(y, sec[::-1, 0], sec[::-1, 1]))

def genv(x):
    return env(np.atleast_1d(np.asarray(x, float)))

def roof_point(row, f):
    xe, ye, xc = GH_ROWS[row]
    x = xc + (xe - xc) * f * f
    ze = float(genv(np.array([xe]))[0]) - GH_EDGE_DROP[row]
    zc = float(genv(np.array([xc]))[0])
    z = ze + (zc - ze) * np.sqrt(max(0.0, 1 - f * f)) + GH_BUBBLE * np.sin(np.pi * f) ** 2
    return np.array([x, ye * f, z])

def roof_rows():
    out = []
    for r in range(len(GH_ROWS)):
        half = [roof_point(r, f) for f in GH_F]
        row = [p * [1, -1, 1] for p in half[::-1]] + half[1:]
        out.append(row[::-1])
    return np.array(out)

def gh_top_loop_left():
    top = [roof_point(0, f) for f in GH_F]
    top += [roof_point(r, 1.0) for r in range(1, len(GH_ROWS) - 1)]
    top += [roof_point(len(GH_ROWS) - 1, f) for f in GH_F[::-1]]
    return np.array(top)

def gh_kind(j):
    return GH_COL[j][3]

def _arc(b, tp, t):
    """point at fraction t (of centre-line arc height) between base b and top tp, following ENV."""
    p = b + (tp - b) * t
    xs = np.array([b[0], p[0], tp[0]]); e = genv(xs)
    g = (e[1] - e[0]) / (e[2] - e[0]) if abs(e[2] - e[0]) > 1e-6 else t
    p[2] = b[2] + (tp[2] - b[2]) * g
    return p

def gh_rings():
    """(6, NJ, 3) left-half rings: k0 base, k1 belt, k2 mid glass, k3 glass top, k4 rail, k5 roof edge."""
    T_ = gh_top_loop_left()
    R = np.zeros((6, NJ, 3))
    for j, ((bx, by), belt, gt, kind) in enumerate(GH_COL):
        b = np.array([bx, by, body_top_z(bx, by) - 0.006]); tp = T_[j]
        if kind in ('ws', 'rg'):
            pts = [b, _arc(b, tp, 0.03), _arc(b, tp, 0.5), _arc(b, tp, 0.955), _arc(b, tp, 0.985), tp]
        else:
            if kind == 'cp':     # C-pillar: interpolate the neighbouring side / rear-glass columns
                gt = (0.5 * (GH_COL[8][2][0] + -1.0) - 0.08, 0.60, 1.10); belt = max(b[2] + 0.01, 0.99)
            bl = np.array([b[0], b[1], max(belt, b[2] + 0.004)])
            g = np.array(gt, float)
            mid = 0.5 * (bl + g)
            d = g - bl; n = np.array([0.0, d[2], -d[1]]); n /= np.linalg.norm(n); mid = mid + n * SIDE_BULGE
            rail = g + 0.55 * (tp - g); d2 = tp - g; n2 = np.array([0.0, d2[2], -d2[1]]); n2 /= max(np.linalg.norm(n2), 1e-6)
            rail = rail + n2 * 0.010
            pts = [b, bl, mid, g, rail, tp]
        R[:, j] = np.array(pts)
    return R
