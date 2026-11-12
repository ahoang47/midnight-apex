"""Rebuild sim/config/winrate_n4000.json with the repo's KNOT_WINDOW_105 (Barry, 2026-11-11).
Same method as /workspace/barry-drafts/lines-v1/build_repo_table.py (lines-v1 S-A + W-A banks, N=4000, seeds 20261113-15 x
10/20/30 turns, kappa 1.55/1.35/1.20, opponent QTE 1.0, a=0.65; pooled = equal-weight mean of districts per (seed, length);
rows = 0.80..1.40 step 0.0025 + every exact r the repo progression evaluates over all 216 play orders, forced + never).
Only the hidden-window knots differ: they are read from the repo's equations.KNOT_WINDOW_105 (single source).
Usage: python3 rebuild_winrate_table.py OUT.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, "/workspace/barry-drafts/lines-v1")
cwd = os.getcwd()
import lib, progress_run as PR   # noqa: E402 (lib chdirs to final-v1)
os.chdir(cwd)
sys.path.insert(0, "/workspace/midnight-apex/sim")
from velocity_shift import progression as P, equations as E   # noqa: E402

lib.WIN = lib.f.knot_window(list(E.KNOT_WINDOW_105))
OUT = sys.argv[1]
T = PR.touge_from_cache(); S = PR.load_counts("S_N90=SSA"); W = PR.load_counts("W_SW=IR=AAD")
PACK = {"touge": T, "wangan": W, "street": S}
_c = {}


def rates(r, q):
    key = (round(r, 4), q)
    if key not in _c:
        per = {d: {(sd, L): lib.wr_counts(P_[(sd, q, L)], key[0], q, L) for sd in lib.SEEDS for L in lib.LENGTHS} for d, P_ in PACK.items()}
        out = {d: (round(min(v.values()), 1), round(max(v.values()), 1)) for d, v in per.items()}
        pooled = [np.mean([per[d][k] for d in PACK]) for k in per["touge"]]
        out["pooled"] = (round(min(pooled), 1), round(max(pooled), 1))
        _c[key] = out
    return _c[key]


keys = {round(x, 4) for x in np.arange(0.80, 1.40001, 0.0025)}
PROV = ("Build sim/config/winrate_n4000.json for the repo with the lines-v1 S-A + W-A tables (Barry, 2026-11-10; rebuilt 2026-11-11 for\n"
        "KNOT_WINDOW_105 r=1.00 knot 0.68 -> 0.67, Austin approved; design/notes/slots-v2/rebuild_winrate_table.py).\n"
        "District rates: Touge = official counts_n4000 cache masked to Touge tracks (unchanged lines); Street = counts_S_N90=SSA.npz,\n"
        "Wangan = counts_W_SW=IR=AAD.npz (N=4000 each on that district's own 5 tracks). Seeds 20261113-15 x 10/20/30 turns, knot window\n"
        f"{tuple(E.KNOT_WINDOW_105)}, kappa 1.55/1.35/1.20, opponent QTE 1.0, a=0.65. Pooled = equal-weight mean of the three district win rates per\n"
        "(seed, length), then min/max. Values rounded to 0.1. Rows: 0.80..1.40 step 0.0025 grid plus every exact r (4 dp) the repo\n"
        "progression evaluates over all 216 play orders (forced + never).")


def table():
    o = {"_provenance": PROV, "q": {}}
    for q in (0.6, 0.8):
        o["q"][str(q)] = {}
        rs = sorted(keys)
        for d in ("pooled", "touge", "wangan", "street"):
            v = [rates(r, q)[d] for r in rs]
            o["q"][str(q)][d] = dict(r=rs, min=[a for a, b in v], max=[b for a, b in v])
    return o


for it in range(8):
    P._TABLE = table()["q"]
    miss = set(); orig = P.win_rate

    def wr(r, q, d="pooled"):
        k = round(r, 4)
        if k not in keys:
            miss.add(k)
        return orig(r, q, d)
    P.win_rate = wr
    for order in P.all_orders():
        for pol in ("forced", "never"):
            P.run(pol, order)
    P.win_rate = orig
    print("iteration", it, "new exact r keys:", len(miss), flush=True)
    if not miss:
        break
    keys |= miss
tab = table()
json.dump(tab, open(OUT, "w"), separators=(",", ":"))
print("rows per series:", len(tab["q"]["0.6"]["pooled"]["r"]))
