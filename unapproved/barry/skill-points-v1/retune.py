"""Hard retune limit study (draft, Barry 2026-11-14). Whole skill points at 10x resolution (S3), each stat kept at
25-50 % of the total, new points free (greedy toward the district tune), and at each district change (R1->R2,
R2->R3, before P1, M11, M21, M31) at most B of the already-spent points may move. Win % at an off-tune split =
live table + [sweep(p) - sweep(p_tune)] (retune_sweep_*.json, common random numbers), p = POW share (HAN 25 %).
Campaign: live progression walk (round-by-round _walk_round). Arc/finale: draft econ-v1 arc walker. In memory only."""
import os, sys, json, math, copy, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "story-xp-v1"))
import schemes as SC
import balance as BAL                 # installs the S3 table into E.sp_at_level / model.sp_at
import arc, camp, core, oracle
E, P = camp.E, camp.P
A = arc.MODS["run_finale_arc"]

TUNE = {"street": (0.50, 0.25, 0.25), "wangan": (0.25, 0.25, 0.50), "touge": (0.45, 0.25, 0.30)}   # POW, HAN, EN
PTS = [int(round(10 * x)) for x in SC.SCHEMES["S3_x10"]["table"]]
TRACK_D = {n: d for d, n in P._table()["tracks"]}
ORIG_TRACK_WIN = P._track_win
ORIG_COMBAT = P.combat_power
LIVE_TRACK = lambda pr, r, T, name: ORIG_TRACK_WIN(pr, r, T, name)

# ── off-tune delta from the sweep ──
SW = None
def load_sweep(tag=os.environ.get("SWEEP", "rt1")):
    global SW
    SW = json.load(open(os.path.join(HERE, f"retune_sweep_{tag}.json")))
    SW["rs_f"] = [float(x) for x in SW["rs"]]; SW["ps_f"] = [float(x) for x in SW["ps"]]

def _interp(xs, x):
    if x <= xs[0]: return 0, 0, 0.0
    if x >= xs[-1]: return len(xs) - 1, len(xs) - 1, 0.0
    i = bisect.bisect_right(xs, x); return i - 1, i, (x - xs[i - 1]) / (xs[i] - xs[i - 1])

def sweep_win(pr, r, T, track, p):
    cell = SW["win"][pr][str(int(T))][track]
    i0, i1, fr = _interp(SW["rs_f"], r); j0, j1, fp = _interp(SW["ps_f"], p)
    g = lambda i, j: cell[f"{SW['rs_f'][i]:.3f}"][f"{SW['ps_f'][j]:.3f}"]
    a = g(i0, j0) * (1 - fp) + g(i0, j1) * fp; b = g(i1, j0) * (1 - fp) + g(i1, j1) * fp
    return a * (1 - fr) + b * fr

def win_at(pr, r, T, track, p):
    d = TRACK_D[track]
    w = LIVE_TRACK(pr, r, T, track) + sweep_win(pr, r, T, track, p) - sweep_win(pr, r, T, track, TUNE[d][0])
    return min(100.0, max(0.0, w))

# ── allocation ──
def band(T):
    return math.ceil(0.25 * T - 1e-9), math.floor(0.50 * T + 1e-9)

def add_points(alloc, n, d):
    """Spend n new points greedily toward TUNE[d] at the new total, inside the 25-50 % band."""
    a = list(alloc); T = sum(a) + n; tgt = [s * T for s in TUNE[d]]; lo, hi = band(T)
    for i in range(3):                                  # floors first
        need = max(0, lo - a[i]); g = min(need, n); a[i] += g; n -= g
    while n > 0:
        cand = [i for i in range(3) if a[i] < hi]
        i = max(cand, key=lambda k: tgt[k] - a[k])
        step = max(1, min(n, int(tgt[i] - a[i]) if tgt[i] - a[i] >= 1 else n, hi - a[i]))
        if tgt[i] - a[i] < 1:                             # everything at target: spread by target share
            for k in range(3):
                g = min(n, int(round(TUNE[d][k] * n)) if k < 2 else n, hi - a[k]); a[k] += g; n -= g
            if n > 0:
                k = min(range(3), key=lambda k: a[k] / T); a[k] += n; n = 0
            break
        a[i] += step; n -= step
    return tuple(a)

def retune(alloc, B, d):
    """Move at most floor(B x spent) points from surplus to deficit stats (toward TUNE[d]), inside the band."""
    a = list(alloc); T = sum(a); budget = int(math.floor(B * T + 1e-9)); lo, hi = band(T)
    tgt = [s * T for s in TUNE[d]]
    while budget > 0:
        sur = [i for i in range(3) if a[i] - tgt[i] >= 1 and a[i] > lo]
        dfc = [i for i in range(3) if tgt[i] - a[i] >= 1 and a[i] < hi]
        if not sur or not dfc: break
        i = max(sur, key=lambda k: a[k] - tgt[k]); j = max(dfc, key=lambda k: tgt[k] - a[k])
        m = min(budget, int(a[i] - tgt[i]), int(tgt[j] - a[j]), a[i] - lo, hi - a[j])
        if m <= 0: break
        a[i] -= m; a[j] += m; budget -= m
    return tuple(a)

class Seg:
    """A district segment: entry allocation (after the retune) at entry level; split at a level = entry + greedy new points."""
    def __init__(self, d, alloc, L):
        self.d, self.alloc, self.L = d, tuple(alloc), L; self._c = {}
    def at(self, L):
        if L not in self._c:
            self._c[L] = add_points(self.alloc, max(0, PTS[L] - PTS[self.L]), self.d) if L > self.L else self.alloc
        return self._c[L]

def pshare(alloc):
    return alloc[0] / sum(alloc)

# ── hooks ──
CUR = dict(L=0, seg=None)
def combat_hook(level, rnd, mods=True):
    CUR["L"] = int(level); return ORIG_COMBAT(level, rnd, mods)
def track_hook(pr, r, T, name):
    return win_at(pr, r, T, name, pshare(CUR["seg"].at(CUR["L"])))

def walk_campaign(mode, B):
    P.combat_power = combat_hook; P._track_win = track_hook
    try:
        L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT
        alloc = (PTS[0] // 2, PTS[0] // 4, PTS[0] - PTS[0] // 2 - PTS[0] // 4)   # free start on the Street tune
        rounds, splits = [], []
        prev_end_L = 0
        for rnd in range(3):
            d = E.ROUND_DISTRICTS[rnd].lower()
            if rnd > 0:
                alloc = retune(alloc, B, d)                                   # spent points: at most B move
                L, bag = E.CAP_LEVEL[rnd - 1], 0.0                            # live: enter at the previous cap
                alloc = add_points(alloc, max(0, PTS[L] - PTS[prev_end_L]), d)   # flagged: teleport points are new
            seg = Seg(d, alloc, L); CUR["seg"] = seg
            w = P._walk_round(rnd, L, bag, money, debt, mode); rounds.append(w)
            splits.append([(x["rung"], x["arrive_L"], round(100 * pshare(seg.at(x["arrive_L"])), 1)) for x in w["rows"]])
            L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]
            alloc = seg.at(L); prev_end_L = L
        return rounds, splits, alloc
    finally:
        P.combat_power = ORIG_COMBAT; P._track_win = ORIG_TRACK_WIN

def at_cap(alloc_by_round, mode_rounds):
    out = []
    for rnd, d in enumerate(E.ROUND_DISTRICTS):
        d = d.lower(); capL = E.CAP_LEVEL[rnd]; seg = alloc_by_round[rnd]
        r = ORIG_COMBAT(capL, rnd) / E.opponent_budget(rnd, 6); p = pshare(seg.at(capL))
        out.append(dict(r=round(r, 4), p=round(100 * p, 1),
                        **{pr: round(win_at(pr, r, 30, E.BOSS_HARD_TRACK[d], p), 1) for pr in P.PROFILES}))
    return out

# ── arc ──
ARC = {}
ORIG_ORACLE_TRACK = oracle.track_wr
ORIG_CVS = A.combat_vs
def arc_track_hook(pr, r, T, name):
    st = ARC[pr]; d = TRACK_D.get(name) or oracle.MAP.get(name)
    if d != st["seg"].d:                                   # district change: retune spent points, start a new segment
        a = retune(st["seg"].at(st["L"]), st["B"], d); st["seg"] = Seg(d, a, st["L"]); st["log"].append((d, st["L"], round(100 * pshare(a), 1)))
    return win_at(pr, r, T, name, pshare(st["seg"].at(st["L"])))
def cvs_hook(s, content_C):
    ARC[CURPR[0]]["L"] = int(s.L); return ORIG_CVS(s, content_C)
CURPR = [None]

def walk_arc(entries, end_alloc, B):
    oracle.track_wr = arc_track_hook; A.combat_vs = cvs_hook
    A.wr_pack = lambda pr, r, T, district: A.wr_cell(pr, r, T, district, True)   # no cache: split varies
    try:
        races = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL)
        walks = []
        for pr in P.PROFILES:
            e = entries[pr]; a0 = retune(end_alloc[pr], B, "touge")          # before P1
            ARC[pr] = dict(B=B, L=int(e.L), seg=Seg("touge", a0, int(e.L)), log=[("touge", int(e.L), round(100 * pshare(a0), 1))])
            CURPR[0] = pr
            walks.append(A.walk_profile(pr, e, races, arc.MODE[pr]))
        ev = A.evaluate(walks)
        return walks, ev, {pr: ARC[pr]["log"] for pr in P.PROFILES}
    finally:
        oracle.track_wr = ORIG_ORACLE_TRACK; A.combat_vs = ORIG_CVS

MODE_OF = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}

def run_B(B):
    BAL.install(SC.SCHEMES["S3_x10"]["table"])
    try:
        res, spl, end = {}, {}, {}
        segs = {}
        for m in ("story", "mixed", "hard"):
            rounds, splits, alloc = walk_campaign(m, B); res[m] = rounds; spl[m] = splits; end[m] = alloc
        s = camp.summary(res)
        # at-cap boss: grinders' split at the cap (mixed for 60/80, 80/60, 80/80; hard for 60/60)
        caps = {}
        for m in ("mixed", "hard"):
            P.combat_power = combat_hook; P._track_win = track_hook
            segs_m = []
            L, alloc = 0, (PTS[0] // 2, PTS[0] // 4, PTS[0] - PTS[0] // 2 - PTS[0] // 4); prev = 0
            for rnd in range(3):
                d = E.ROUND_DISTRICTS[rnd].lower()
                if rnd > 0:
                    alloc = retune(alloc, B, d); L = E.CAP_LEVEL[rnd - 1]; alloc = add_points(alloc, max(0, PTS[L] - PTS[prev]), d)
                sg = Seg(d, alloc, L); segs_m.append(sg); L = E.CAP_LEVEL[rnd]; alloc = sg.at(L); prev = L
            P.combat_power = ORIG_COMBAT; P._track_win = ORIG_TRACK_WIN
            caps[m] = at_cap(segs_m, None)
        ent = arc.entries_for(s)
        raw = res["story"][2]; ent["c8080"].L = raw["L"]; ent["c8080"].bag = raw["bag"]
        walks, ev, alog = walk_arc(ent, {pr: end[MODE_OF[pr]] for pr in P.PROFILES}, B)
        return dict(B=B, campaign=s, splits=spl, at_cap=caps, arc=arc.brief(walks), arc_issues=ev.get("issues"), arc_splits=alog,
                    arc_grind_split={w["pr"]: [(w["grind"][i]["wall"], w["grind"][i]["to_cap"]) for i in range(4)] for w in walks})
    finally:
        BAL.install(None)

if __name__ == "__main__":
    load_sweep()
    out = {}
    for B in [float(x) for x in os.environ.get("BS", "1.0,0.20,0.15,0.10,0.05,0.0").split(",")]:
        o = run_B(B); out[f"{B:.2f}"] = o
        c = o["campaign"]
        print(f"== B={B:.2f}")
        print("  story split@boss", [x[-1] for x in o["splits"]["story"]], "mixed split@kid1/boss", [(x[0][2], x[-1][2]) for x in o["splits"]["mixed"]])
        print("  story boss", [(x["boss_L"], x["boss"]["c8080"]) for x in c["story"]], "min80", [x["min8080"] for x in c["story"]])
        print("  mixed", [(x["wall"], x["wall_grind"], x["post"]) for x in c["mixed"]], "hard", [x["total"] for x in c["hard"]], [x["cap"] for x in c["mixed"] + c["hard"]])
        print("  at-cap mixed", [(x["p"], x["c6080"], x["c8060"], x["c8080"]) for x in o["at_cap"]["mixed"]], "hard", [(x["p"], x["c6060"]) for x in o["at_cap"]["hard"]])
        for pr, a in o["arc"].items():
            print("  arc", pr, a["grind"], o["arc_grind_split"][pr], a["billed"], a["billed_L"], a["min_story"], a["end_money"])
        print("  arc splits", o["arc_splits"])
        print("  issues", o["arc_issues"])
    json.dump(out, open(os.path.join(HERE, f"retune_results_{os.environ.get('SWEEP', 'rt1')}.json"), "w"), indent=1, default=str)
