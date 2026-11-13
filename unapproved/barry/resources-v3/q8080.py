"""Quick ask (Austin 2026-11-13): win rate at the cap with read 0.8 and raw QTE 0.8. Same seeds/grid as run_v3."""
import json, numpy as np
from multiprocessing import Pool
import resources_v3 as R
import run_v3 as RV
def job(a):
    cand,b,ti,T,st=a
    cfg=RV.CANDS[cand]; c={k:v for k,v in cfg.items() if not k.startswith("_")}
    (d,name),lap=RV.TR[ti]
    o=R.run_new(RV.TUNES,cfg["_cap"],d,lap,T,st,0.8,0.8,RV.N,RV.SEEDS[b],cfg=c)
    return a,o["win"].mean(1)
if __name__=="__main__":
    print("avg profile raw qte at cap:",R.E.raw_qte_score(1.05,profile="average"))
    res={}
    with Pool(8) as p:
        for cand in ["A_mid","B_retune","C_light"]:
            arr=np.zeros((9,len(RV.TR),3,3,len(RV.TUNES)))
            jobs=[(cand,b,ti,T,st) for b in range(9) for ti in range(len(RV.TR)) for T in RV.LENGTHS for st in R.STYLES]
            for (c_,b,ti,T,st),w in p.imap_unordered(job,jobs,chunksize=4):
                arr[b,ti,RV.LENGTHS.index(T),R.STYLES.index(st)]=w
            m=arr.mean(0)  # (tracks,len,style,tunes)
            best=m[...,:-1].max(-1); even=m[...,-1]
            out={"tuned_all":best.mean(),"even_all":even.mean()}
            for k,T in enumerate(RV.LENGTHS):
                out[f"tuned_{T}"]=best[:,k].mean(); out[f"even_{T}"]=even[:,k].mean()
            for dist in ["street","touge","wangan"]:
                idx=[i for i,(dd,_) in enumerate(RV.TR) if dd==dist]
                out[f"tuned_{dist}"]=best[idx].mean()
            res[cand]={k:round(100*float(v),1) for k,v in out.items()}
            print(cand,res[cand],flush=True)
    json.dump(res,open("q8080.json","w"),indent=1)
