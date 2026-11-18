"""Live baseline (today's level-based progression) on touge-race; read-only use of sim/velocity_shift."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "sim"))
from velocity_shift import progression as P, equations as E

def summarize():
    out = {}
    for mode in ("story", "mixed", "hard"):
        rs = P.run(mode)
        rounds = []
        for w in rs:
            rows = [dict(rung=x["rung"], L=x["arrive_L"], r=x["arrive_r"], c8080=P.hard_win(x["wr"]["c8080"]),
                         c6060=P.hard_win(x["wr"]["c6060"]), c6080=P.hard_win(x["wr"]["c6080"]), c8060=P.hard_win(x["wr"]["c8060"]),
                         grind=x["grind_here"] + x["pre_boss_grind"], money=x["money"], debt=x["debt"]) for x in w["rows"]]
            rounds.append(dict(total_grind=w["total_grind"], end_L=w["L"], money=round(w["money"]), debt=w["debt"],
                               spent=None, rows=rows))
        out[mode] = rounds
    out["boss_at_cap"] = P.boss_check_at_cap()
    return out

if __name__ == "__main__":
    s = summarize()
    json.dump(s, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline_live.json"), "w"), indent=1, default=str)
    for mode in ("story", "mixed", "hard"):
        for i, w in enumerate(s[mode]):
            low = min(x["c8080"] for x in w["rows"]); boss = w["rows"][-1]
            print(mode, f"R{i+1}", "grind", w["total_grind"], "endL", w["end_L"], "low8080", low, "boss", boss["c8080"], boss["c6060"],
                  "money", w["money"], "debt", w["debt"])
    for b in s["boss_at_cap"]:
        print("cap", b["rnd"], b["r"], b["c6060"], b["c8080"], b["pow_share"])
