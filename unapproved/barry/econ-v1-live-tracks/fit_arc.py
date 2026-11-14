"""Re-fit the pre-finale arc on the live-track oracle: wall r_design (P3, M12, M22, M32), optional gate P4, with
B = 80/80-reference combat / r_design (econ-v1 set_budgets_from_8080 logic), finale r* given. Draft."""
import json, os, sys, itertools, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

WALLS = ("P3", "M12", "M22", "M32")


def build(M, mods, entries, rd):
    A = mods["run_finale_arc"]
    spec = [dict(x, r_design=rd.get(x["id"], x["r_design"])) for x in core.LIVE_ARC]
    races = core.arc_races(spec, M)
    for rc in races:
        if not rc["billed"]:
            rc["B"] = None
    A.set_budgets_from_8080(races, entries["c8080"])
    return races


def evaluate_arc(M, mods, entries, rd):
    races = build(M, mods, entries, rd)
    _, walks, ev = core.run_arc(mods, races, entries)
    return races, walks, ev


def billed_cells(walks):
    w = {x["pr"]: x for x in walks}
    out = []
    for i in range(4):
        row = {pr: next(x for x in w[pr]["log"] if x["id"] == f"F{i+1}") for pr in core.PROFILES}
        out.append({pr: (row[pr]["L"], row[pr]["r"], row[pr]["wr_dist"], row[pr]["wr_hard"]) for pr in row})
    return out


def penalty(walks, ev):
    pen = 10 * len(ev["issues"])
    w = {x["pr"]: x for x in walks}
    for pr in ("c6080", "c8060"):
        for i in range(4):
            g = w[pr]["grind"][i]
            pen += max(0, g["total"] - 10) * 3 + max(0, g["wall"] - 6) * 3
    walls = sum(1 for pr in ("c6080", "c8060") for i in range(4) if 3 <= w[pr]["grind"][i]["wall"] <= 6)
    pen -= 0.5 * min(walls, 4)   # econ-v1 preference: a 3-6 wall on most steps
    return pen


def fit(M, mods, entries, grid=None, base=None):
    base = base or {x["id"]: x["r_design"] for x in core.LIVE_ARC if x["id"] in WALLS}
    grid = grid or [round(0.98 + 0.005 * i, 3) for i in range(21)]   # 0.980 .. 1.080
    best = None
    rd = dict(base)
    # coordinate passes (steps are nearly independent; repeat twice)
    for _ in range(2):
        for wid in WALLS:
            for v in grid:
                t = dict(rd); t[wid] = v
                races, walks, ev = evaluate_arc(M, mods, entries, t)
                key = (penalty(walks, ev), sum(abs(t[k] - base[k]) for k in WALLS))
                if best is None or key < best[0]:
                    best = (key, dict(t)); rd = dict(t)
            rd = dict(best[1])
    races, walks, ev = evaluate_arc(M, mods, entries, best[1])
    return best[1], races, walks, ev
