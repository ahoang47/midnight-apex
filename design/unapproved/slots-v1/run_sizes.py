"""slots-v1 part 2: larger window-mod sizes and every ladder rung (not only the key cells), plus grind counts with
the larger sizes. Writes results_sizes.json. Same oracle, banks, seeds and thresholds as run.py."""
import json, collections
import numpy as np
import slots_model as S
import run as RUN

SIZES = (0.10, 0.20, 0.30, 0.50, 0.75, 1.00)


def all_cells():
    rows, _ = S.run(None, "average")
    out = []
    for r in rows:
        if r["crew"] == "Prologue":
            continue
        d = (r.get("district") or r["crew"].split()[1]).lower()
        for kind, rv in (("skip", r["r_skip"]), ("target", r["r_tgt"])):
            out.append(dict(cell=f"{r['rung']} #{r['j'] + 1 if r['crew'] != 'Finale' else ''} {kind}".replace(" # ", " "), j=r["j"], kind=kind,
                            crew=r["crew"], rung=r["rung"], r=rv, district=d))
    return out


def main():
    S.WINDOW_SIZES = SIZES
    cells = all_cells()
    res = dict(sizes=SIZES, trades={}, grind={})
    for sc in "ABC":
        sched = {(s["crew"], s["rung"], s["j"]): s for s in S.schedule(sc)}
        T = []
        for c in cells:
            s = sched[(c["crew"], c["rung"], c["j"])]; dr = min(s["lines"]) / s["B"]
            for prof in S.PROFILES:
                base = S.wr_vec(c["r"], prof, 0.0, c["district"])
                for w in SIZES:
                    v = S.wr_vec(c["r"] - dr, prof, w, c["district"]); d = v - base
                    T.append(dict(crew=c["crew"], rung=c["rung"], j=c["j"], kind=c["kind"], profile=prof, size=w, r=round(c["r"], 4), dr=round(dr, 4),
                                  zone_after=round(S.E.qte_zone_width(c["r"] - dr, w), 3), base_mid=round(S.mid(base), 2), mid=round(S.mid(v), 2),
                                  delta_mean=round(float(d.mean()), 2), delta_min=round(float(d.min()), 2), delta_max=round(float(d.max()), 2),
                                  verdict=RUN.classify(d)))
        res["trades"][sc] = T
        for prof in S.PROFILES:
            rows, t = S.run(sc, prof)
            res["grind"][f"{sc}|{prof}"] = dict(total=t, window_picks=[(r["crew"], r["rung"], r["skip_pick"], round(r["skip_mid"], 2)) for r in rows
                                                                       if r["skip_pick"] not in ("-", "all stat")])
            print(sc, prof, t, len(res["grind"][f"{sc}|{prof}"]["window_picks"]), flush=True)
    json.dump(res, open("results_sizes.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
