"""Run 1: next-tier stock A (= previous cap) vs B (= previous cap - half the previous tier's earned room) [PH].
Story-only walk (no grinds), car points = tier stock + mod_skill story XP (+ catch-up where the rules give it), capped at the tier
ceiling; win % from the live tables (shown cell), c6060 / c8080 / standard reading curve. Old car = the capped previous-tier car
(previous district tune, now off tune). No spirit / driver tree here (they shift A and B alike). -> run1.json"""
import json, os
from common import CN, ROUNDS, RUNGS, TURNS, TUNE, win, B_of, HERE

CAPPTS = [3532, 4044, 4628]
VARIANTS = {"A": {1: 3532, 2: 4044}, "B": {1: 3266, 2: 3788}}   # B: 3532 - 532/2, 4044 - 512/2 [PH]


def walk(stock, catchup=True):
    rows = []; pts_end_r1 = 3000 + sum(CN["STORY_XP"][0][:6])
    for rnd in (1, 2):
        d = ROUNDS[rnd]; pts = stock[rnd]
        short = max(0.0, 10 * CN["CAP_POWER"][rnd - 1] - pts) if catchup else 0.0
        for j in range(7):
            power = min(CN["CAP_POWER"][rnd], pts / 10); r = power / B_of(rnd, j); s = 0.6 + 0.2 * j / 6
            old = CAPPTS[rnd - 1] / 10 / B_of(rnd, j)     # previous-tier car, capped, previous district tune
            ps_old = TUNE[ROUNDS[rnd - 1]][0]
            rows.append(dict(rnd=rnd + 1, rung=RUNGS[j], pts=round(pts, 1), r=round(r, 4), r_old=round(old, 4),
                             **{f"new_{p}": round(win(p, r, TURNS[j], d, TUNE[d][0], s), 1) for p in ("c6060", "c8080", "curve")},
                             **{f"old_{p}": round(win(p, old, TURNS[j], d, ps_old, s), 1) for p in ("c6060", "c8080", "curve")}))
            xp = CN["STORY_XP"][rnd][j] + CN["CATCHUP"]["k"] * CN["CATCHUP"]["share"][j] * short
            pts = min(CAPPTS[rnd], pts + xp)
    return rows


out = {"A": walk(VARIANTS["A"]), "B": walk(VARIANTS["B"]), "B_nocatchup": walk(VARIANTS["B"], False), "stocks": VARIANTS}
json.dump(out, open(os.path.join(HERE, "run1.json"), "w"), indent=1)
for k in ("A", "B", "B_nocatchup"):
    print("==", k)
    for x in out[k]:
        print(f"R{x['rnd']} {x['rung']:5} pts {x['pts']:7} r {x['r']:.4f}  new 60/60 {x['new_c6060']:5} 80/80 {x['new_c8080']:5} curve {x['new_curve']:5}"
              + (f" | old car r {x['r_old']:.4f} 60 {x['old_c6060']:5} 80 {x['old_c8080']:5} curve {x['old_curve']:5}" if k != "A" else ""))
