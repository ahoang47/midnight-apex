"""SETUP STUDY journeys (Barry, 2026-11-19): R1 Street, Monte Carlo on journey_grid.json (engine), journey.py rules.
G2b: weak improving (q 0.50 -> 0.80 linear over 40 attempts), mandatory + capped non-mandatory (grind until the next story
race is >= 50 % or the cap is hit). Setups: M = 7/10/13/20 fixed race XP (setup_study.py) and M7r / M13r (story XP raised so
the floors equal M20's: same stats, fewer races). Journeys (run 1 mandatory only, run 2 + capped non-mandatory; weak improving
and strong 80/80) for named top setups. -> journey_setups.json"""
import json, os, sys
import journey as J, setup_study as S
HERE = os.path.dirname(os.path.abspath(__file__))
WEXP = 13; ST = S.F.STORY_XP[0]


def setup(name):
    M = int(name[1:].rstrip("r")); g = S.GAPS[M]; retuned = name.endswith("r")
    seq = ["kid1"]; sxp = {}
    for j, rung in enumerate(S.RUNGS[1:]):
        prev = S.RUNGS[j]
        sxp[prev] = ST[j] + ((S.GAPS[20][j] - g[j]) * WEXP if retuned else 0)
        seq += ["we"] * g[j] + [rung]
    sxp["boss"] = 0
    pts = 3000; fl = {}
    for k in seq:
        if k != "we": fl[k] = pts
        pts += WEXP if k == "we" else sxp[k]
    return seq, sxp, fl


def capn(c): return 10 ** 6 if c == "none" else int(c)


if __name__ == "__main__":
    out = dict(g2b={}, journeys={})
    for name in ("M7", "M10", "M13", "M20", "M7r", "M13r"):
        seq, sxp, fl = setup(name)
        for c in ("none", "8", "12", "15"):
            o = J.journey(2, 0.50, 0.80, 40, M=10000, NM_CAP=capn(c), seq=seq, sxp=sxp, floor=fl)
            boss = o["rows"][-1]
            out["g2b"][f"{name}|{c}"] = dict(attempts=o["attempts"], nm_wins=o["nm_wins"], stuck=o["stuck"],
                                             boss_p1=round(100 * boss["p"], 1), boss_q=boss["q"], boss_pts=boss["pts"], cash=boss["cash"])
            print(name, c, out["g2b"][f"{name}|{c}"], flush=True)
    for spec in sys.argv[1:]:                     # e.g. M20:15
        name, c = spec.split(":"); seq, sxp, fl = setup(name)
        for who, q0 in (("weak", 0.50), ("strong", 0.80)):
            for run in (1, 2):
                out["journeys"][f"{name}|{c}|{who}|run{run}"] = J.journey(run, q0, 0.80, 40, M=10000, NM_CAP=capn(c), seq=seq, sxp=sxp, floor=fl)
    json.dump(out, open(os.path.join(HERE, "journey_setups.json"), "w"), indent=1)
