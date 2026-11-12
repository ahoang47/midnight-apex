"""slots-v2 fix b3 (APPROVED, Austin 2026-11-12): check the LIVE crew-local mod tier floor against the share-aware oracle.

Same progression loop and oracle as the study (unapproved/barry/slots-v2/fixes.py, fix "b3"), but the floor is read from the
live sim (velocity_shift.progression.mod_tier_floor -> equations.MOD_TIER_LEVEL_FLOOR, keyed by (round, play position)) instead
of the study's own LOCAL_L table, and it can run every legal play order. Profiles weak/average/strong x policies
balanced/window/aero10. 'decisive' = a mature #2 / boss rung cleared at the skip state only because of the newest fitted purchase
(mid with the previous rung's lines < 50), as in the study.

Needs numpy, the study modules in unapproved/barry/slots-v2 (+ slots-v1) and the share-grid banks (about 44 MB, not committed) in
/workspace/barry-drafts/slots-v2/counts (override with SLOTS_V2_COUNTS).
Usage (from the repo root): python3 design/notes/slots-v2/b3_check.py [--all-orders] [--no-floor] [--policies balanced,window,aero10] [OUT.json]"""
import itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "unapproved", "barry", "slots-v2"))
import numpy as np                                    # noqa: E402
import model as M, prog, cells as R                   # noqa: E402
M.GRID_DIR = os.environ.get("SLOTS_V2_COUNTS", "/workspace/barry-drafts/slots-v2/counts")
E, P = M.E, M.P
SPLIT = "100/0/0"
POLICIES = ("balanced", "window", "aero10")
_MEMO = {}


def best_mid(sp, lv, B, policy, aero, profile):
    k = (round(sp, 9), tuple(np.round(lv, 9)), round(B, 9), policy, aero, profile)
    if k not in _MEMO:
        _MEMO[k] = prog.best_mid(sp, lv, B, SPLIT, policy, aero, profile)
    return _MEMO[k]


def items(buy):
    if buy is None:
        return []
    if isinstance(buy, tuple) and buy[0] == "initial":
        return [(i, buy[2]) for i in range(buy[1])]
    return [(i, new) for i, _old, new in buy]


def run(policy, profile, order=None):
    """One season under the live floor. Mirrors fixes.run(fix='b3') with floor = live MOD_TIER_LEVEL_FLOOR."""
    saved = E.DEFAULT_CREW_ORDER
    if order is not None:
        E.DEFAULT_CREW_ORDER = order                 # ladder(), the scheme C schedule and aero_ok all read the default order
    try:
        SP, XC, X = P.curves(); Rl, Lf, Lstep, budgets, B_last = P.ladder()
        key = {(s["crew"], s["rung"], s["j"]): s for s in M.S1.schedule("C")}
        xp = 0.0; rows = []; lines = np.zeros(6); prev_lines = None; gated = []; floor = 0; gate = False

        def grind_to(v, cap, j):
            n = 0
            while XC[cap] - v > 1e-9 and n <= 200:
                Ln = P._level(XC, v, cap) + 1
                v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
            return n, v

        def fit(new):
            for i, val in new:
                lines[i] = val

        for i, x in enumerate(Rl):
            cap = x["L"]; xp = min(xp, XC[cap]); L = P._level(XC, xp, cap)
            row = dict(crew=x["crew"], rnd=x.get("rnd"), pos=x.get("pos"), rung=x["rung"], j=x["j"])
            if x["kind"] == "scripted":
                clear = True
            else:
                aero = R.aero_ok(x["crew"])
                if x["crew"] != "Prologue":
                    s = key[(x["crew"], x["rung"], x["j"])]; new = items(s["buy"])
                    if gated and L >= floor:
                        fit(gated); gated = []
                    f = P.mod_tier_floor(x["rnd"], x["pos"], x["j"]); gate = f is not None and L < f
                    if f is not None:
                        row.update(floor=f, level_skip=L)
                    if gate:
                        gated = new; floor = f; new = []
                    fit(new); lv = lines.copy()
                else:
                    lv = np.full(6, x["mods"] / 6)
                m, pick = best_mid(SP[L], lv, x["B"], policy, aero, profile); clear = m >= E.CLEAR_THRESHOLD
                row.update(mid_skip=round(m, 2), locked=gate)
                if prev_lines is not None and x["j"] in (3, 6) and clear and not np.allclose(prev_lines, lv):
                    mp, _ = best_mid(SP[L], prev_lines, x["B"], policy, aero, profile)
                    row["mid_prev_lines"] = round(mp, 2); row["decisive"] = bool(mp < E.CLEAR_THRESHOLD)
            n, v2 = grind_to(xp, cap, max(0, x["j"]))
            g = 0 if clear else n
            if g:
                xp = v2
                if x["crew"] not in ("Prologue",) and x["kind"] != "scripted" and gate:
                    fit(gated); gated = []; gate = False
            if x["kind"] != "scripted" and x["crew"] != "Prologue":
                prev_lines = lines.copy()
            row["grind"] = g; rows.append(row)
            nxt = Rl[i + 1]["L"] if i + 1 < len(Rl) else Lf[0]
            unl = XC[Lstep if i + 1 == len(Rl) else nxt] - XC[cap]
            if x["k"] == 2:
                add = 0.0
            elif x["kind"] == "boss" or x["k"] == 3:
                add = E.STORY_XP_BOSS * unl
            else:
                lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
                add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
            xp = min(xp + add, XC[nxt])
        for (nm, d, B), Lc in zip(E.FINALE, Lf):
            xp = min(xp, XC[Lc]); n, xp = grind_to(xp, Lc, E.TAPER_FINALE_RUNG)
            rows.append(dict(crew="Finale", rung=nm, j=E.TAPER_FINALE_RUNG, grind=n))
        return rows, sum(r["grind"] for r in rows)
    finally:
        E.DEFAULT_CREW_ORDER = saved


def decisive(rows, j=None):
    return [(r["crew"], r["rung"], r["mid_prev_lines"], r["mid_skip"]) for r in rows if r.get("decisive") and (j is None or r["j"] == j)]


def main(argv):
    pols = POLICIES
    for a in argv:
        if a.startswith("--policies"):
            pols = tuple(argv[argv.index(a) + 1].split(","))
    out_path = next((a for a in argv if a.endswith(".json")), None)
    if "--no-floor" in argv:                           # "before": every floor at 0 = the pre-b3 base schedule
        E.MOD_TIER_LEVEL_FLOOR = {k: 0 for k in E.MOD_TIER_LEVEL_FLOOR}
    orders = list(P.all_orders()) if "--all-orders" in argv else [None]
    res = {}
    for pol in pols:
        for prof in M.PROFILES:
            totals = set(); dec = set(); default = None
            for o in orders:
                rows, g = run(pol, prof, o); totals.add(g)
                dec |= {(r["rnd"], r["pos"], r["j"], r["mid_prev_lines"], r["mid_skip"]) for r in rows if r.get("decisive")}
                if o is None or o == E.DEFAULT_CREW_ORDER:
                    default = rows
            res[f"{pol}|{prof}"] = dict(orders=len(orders), grind_totals=sorted(totals), decisive_by_position=sorted(dec),
                                        default_rows=default)
            print(pol, prof, "orders", len(orders), "grind", sorted(totals), "decisive (round, pos, j, mid prev, mid)", sorted(dec), flush=True)
    if out_path:
        json.dump(res, open(out_path, "w"), indent=0, default=float)


if __name__ == "__main__":
    main(sys.argv[1:])
