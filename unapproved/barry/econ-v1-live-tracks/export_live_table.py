"""Export the live-track win-rate oracle (exactly what the draft walks used) to sim/config/winrate_g2_live_tracks_v1.json."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("ORACLE_FILES", "sweep_main.json,sweep_confirm30.json")
os.environ.setdefault("ORACLE_POINTS", "point_confirm.json,point_confirm_T3.json,point_confirm_S1.json,point_confirm_hardest.json")
sys.path.insert(0, HERE)
import oracle
D = oracle.load()
q = {pr: {str(T): {n: [[r, round(v, 3)] for r, v in sorted(pts.items())] for n, pts in byT.items()}
          for T, byT in byL.items()} for pr, byL in D["data"].items()}
out = dict(_comment=("Live engine (G2 heat, live QTE mapping), live stand-in tracks config/tracks_v1.json. Win % (ties half), "
                     "mean of 3 boss styles. Sources: unapproved/barry/econ-v1-live-tracks/ " + ", ".join(D["files"]) +
                     ". sweep_main N=300/track/style r 0.94-1.24 step 0.01 (10/20/30 turns); sweep_confirm30 N=1500 30-turn "
                     "r 1.034-1.072; point checks N=1500-3000 (30-turn) override grid points. Linear interpolation in r, flat outside."),
           tracks=[list(t) for t in D["tracks"]],
           tunes={"street": [0.5, 0.25, 0.25], "wangan": [0.25, 0.25, 0.5], "touge": [0.45, 0.25, 0.3]},
           profiles={"c6060": [0.6, 0.6, 0.6], "c6080": [0.6, 0.8, 0.8], "c8060": [0.8, 0.6, 0.6], "c8080": [0.8, 0.8, 0.8]},
           q=q)
path = os.path.abspath(os.path.join(HERE, "..", "..", "..", "sim", "config", "winrate_g2_live_tracks_v1.json"))
json.dump(out, open(path, "w"), separators=(",", ":"))
print(path, os.path.getsize(path))
