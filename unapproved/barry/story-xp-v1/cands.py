import json, camp
def m_of(spec):
    mult = [[1.0] * 7 for _ in range(3)]
    for rnd, (kind, v) in enumerate(spec):
        rungs = {"uniform": range(7), "oh2": (5,), "oh1+oh2": (4, 5), "none": ()}[kind]
        for j in rungs: mult[rnd][j] = v
    return mult
CANDS = {
  "base": [("none", 1)] * 3,
  "A_oh2_half": [("oh2", 0.5)] * 3,
  "B_mixed": [("uniform", 0.90), ("oh1+oh2", 0.70), ("oh2", 0.65)],
  "C_rec": [("uniform", 0.90), ("oh2", 0.60), ("oh2", 0.80)],
  "C_even": [("uniform", 0.90), ("oh1+oh2", 0.70), ("oh2", 0.80)],
  "B2_mixed": [("uniform", 0.90), ("oh1+oh2", 0.70), ("uniform", 0.95)],
}
if __name__ == "__main__":
    out = {}
    for k, spec in CANDS.items():
        s = camp.summary(camp.run_all(m_of(spec))); out[k] = dict(spec=spec, camp=s)
        print("==", k, spec)
        for m in ("story", "mixed", "hard"):
            for i, x in enumerate(s[m]):
                print(f" {m:5} R{i+1} levels {x['levels']} Lend {x['L_end']} bossL {x['boss_L']} r {x['boss_r']} boss {x['boss']} min80 {x['min8080']} wall {x['wall']} {x['wall_grind']}+{x['post']}={x['total']} cap {x['cap']} ${x['money']} debt {x['debt']}")
    json.dump(out, open("cands_campaign.json", "w"), indent=1)
