"""slots-v1 part 4: scheme C, one window mod of +75% of w(r), with and without qte-v1's total-width cap (1.15 x w0).
Every ladder rung (target and skip), three profiles, plus grind counts. Writes results_cap.json."""
import json, collections
import numpy as np
import slots_model as S
import run as RUN
import run_sizes as RS

E = S.E
_zone = E.qte_zone_width


def capped(r, window_mod=0.0, cap=1.15):
    return min(_zone(r, window_mod), max(cap, _zone(r, 0.0)))


def main():
    out = {}
    S.WINDOW_SIZES = (0.75,); S.MAX_WINDOW_MODS = 1
    cells = RS.all_cells()
    for label, capv in (("nocap", None), ("cap1.15", 1.15)):
        E.qte_zone_width = _zone if capv is None else (lambda r, wm=0.0, c=capv: capped(r, wm, c))
        sched = {(s["crew"], s["rung"], s["j"]): s for s in S.schedule("C")}
        T = []
        for c in cells:
            s = sched[(c["crew"], c["rung"], c["j"])]; dr = min(s["lines"]) / s["B"]
            for prof in S.PROFILES:
                base = S.wr_vec(c["r"], prof, 0.0, c["district"]); v = S.wr_vec(c["r"] - dr, prof, 0.75, c["district"]); d = v - base
                T.append(dict(crew=c["crew"], rung=c["rung"], j=c["j"], kind=c["kind"], profile=prof, base_mid=round(S.mid(base), 2),
                              mid=round(S.mid(v), 2), delta_mean=round(float(d.mean()), 2), verdict=RUN.classify(d)))
        g = {}
        for prof in S.PROFILES:
            rows, t = S.run("C", prof); g[prof] = t["grind_races"]
        out[label] = dict(trades=T, grind=g)
        summ = collections.defaultdict(collections.Counter)
        for t in T:
            summ[(t["j"] if t["crew"] != "Finale" else t["rung"], t["kind"], t["profile"])][t["verdict"]] += 1
        print(label, g)
        for k in sorted(summ, key=str):
            print("  ", k, dict(summ[k]))
    E.qte_zone_width = _zone
    json.dump(out, open("results_cap.json", "w"), indent=1)


if __name__ == "__main__":
    main()
