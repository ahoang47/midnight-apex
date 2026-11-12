"""slots-v2 follow-up (small): complement to econ.py. econ.py only lists rungs that force grind. Here: every mature #2 (j=3)
and crew-boss (j=6) rung that the balanced 2/2/2 loadout clears with NO grind, per profile, with the pooled mid with and
without the newest mod tier (same method as econ.py). Flags any rung where the newest mod is what lifts it over 50.
Writes results_econ_cleared.json (live) or, with --knot067, results_econ_cleared_knot067.json."""
import json
import numpy as np
import sys
import model as M, prog
import parity_after as PA

E, P = M.E, M.P


def main():
    patched = "--knot067" in sys.argv
    if patched:
        PA.patch()                       # proposed KNOT_WINDOW_105 r=1.00 knot 0.67, in-process only
    Rl = P.ladder()[0]; sched = M.S1.schedule("C"); key = {(s["crew"], s["rung"], s["j"]): s for s in sched}
    out = []
    for prof in M.PROFILES:
        rows, _ = prog.run("100/0/0", "balanced", prof)
        for x, r in zip(Rl, rows):
            if x["kind"] == "scripted" or x["crew"] == "Prologue" or x["j"] not in (3, 6) or r["grind"]:
                continue
            s = key[(x["crew"], x["rung"], x["j"])]; idx = sched.index(s)
            st_wo = np.full(3, r["sp"] / 3) + M.default_vec("100/0/0", np.array(sched[idx - 1]["lines"]))
            mid_wo = M.mid(M.wr_batch([(st_wo, 0.0)], x["B"], prof, "pooled")[0])
            out.append(dict(profile=prof, crew=x["crew"], rung=x["rung"], j=x["j"], mid_with_new_mod=r["mid"], mid_without_new_mod=round(mid_wo, 2),
                            new_mod_is_decisive=bool(r["mid"] >= E.CLEAR_THRESHOLD > mid_wo)))
            print(out[-1], flush=True)
    json.dump(out, open("results_econ_cleared_knot067.json" if patched else "results_econ_cleared.json", "w"), indent=0)


if __name__ == "__main__":
    main()
