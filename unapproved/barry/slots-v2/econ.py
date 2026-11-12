"""slots-v2 economy / grind-wall check ([pt210u]): does a freshly unlocked mod make the next wall free?
For every story rung that forces grind (balanced 2/2/2, official progression), the skip-state pooled mid with ALL mods
(including the tier that rung's previous win unlocked) and without that newest tier, per profile. Also per-crew purchase
counts and stat value added, and forced grind races available to fund purchases (cash values are TBD in design/07 §5.1/§6.4,
so no prices are set here). Writes results_econ.json."""
import json
import numpy as np
import model as M, prog

E, P = M.E, M.P


def main():
    SP, XC, X = P.curves(); Rl = P.ladder()[0]
    sched = M.S1.schedule("C"); key = {(s["crew"], s["rung"], s["j"]): s for s in sched}
    out = {"walls": [], "crews": {}}
    for prof in M.PROFILES:
        rows, t = prog.run("100/0/0", "balanced", prof)
        # replay levels at each rung (same as prog.run) to get L at the skip state
        for x, r in zip(Rl, rows):
            if x["kind"] == "scripted" or x["crew"] == "Prologue":
                continue
            s = key[(x["crew"], x["rung"], x["j"])]
            idx = sched.index(s); prev = sched[idx - 1]["mods"] if idx > 0 else 0.0
            new = s["mods"] - prev
            if r["grind"]:
                sp = r["sp"]
                lines_wo = np.array(sched[idx - 1]["lines"]) if idx > 0 else np.array(s["lines"])   # loadout before the newest purchase(s)
                st_wo = np.full(3, sp / 3) + M.default_vec("100/0/0", lines_wo)
                mid_wo = M.mid(M.wr_batch([(st_wo, 0.0)], x["B"], prof, "pooled")[0])
                out["walls"].append(dict(profile=prof, crew=x["crew"], rung=x["rung"], j=x["j"], grind=r["grind"], mid_with_new_mod=r["mid"],
                                         mid_without_new_mod=round(mid_wo, 2), new_mod_pts=round(new, 2), new_mod_pct_of_B=round(100 * new / x["B"], 2),
                                         margin_to_50=round(50 - r["mid"], 2)))
        for x, r in zip(Rl, rows):
            if x["crew"] == "Prologue":
                continue
            c = out["crews"].setdefault(x["crew"], dict(story_wins=0, purchases=0, dead_wins=0, mod_pts_added=0.0, grind=dict()))
            if prof == "average":
                s = key[(x["crew"], x["rung"], x["j"])]
                c["story_wins"] += 1
                c["purchases"] += 0 if s["buy"] is None else (len(s["buy"]) if isinstance(s["buy"], list) else s["buy"][1])
                c["dead_wins"] += s["buy"] is None
            c["grind"][prof] = c["grind"].get(prof, 0) + r["grind"]
    for crew, c in out["crews"].items():
        ss = [s for s in sched if s["crew"] == crew]
        prev = [s for s in sched if s["crew"] != "Finale"]
        i0 = sched.index(ss[0]); c["mod_pts_added"] = round(ss[-1]["mods"] - (sched[i0 - 1]["mods"] if i0 else 0.0), 2)
    json.dump(out, open("results_econ.json", "w"), indent=0)
    for w in out["walls"]:
        print(w)
    for k, v in out["crews"].items():
        print(k, v)


if __name__ == "__main__":
    main()
