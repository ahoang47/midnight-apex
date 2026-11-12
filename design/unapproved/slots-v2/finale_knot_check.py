"""slots-v2 follow-up (small): finale cells (Myth #2 / Summit skipped) re-scored live vs the proposed KNOT_WINDOW_105 r=1.00
knot 0.67 (in-process only), all splits and profiles, to check whether aero (pool 10/20/30%) clears the Summit without grinding.
Same cell definition and oracle as cells.py. Writes results_finale_knot.json."""
import json
import model as M, cells as R
import parity_after as PA


def summ(res):
    f = res["fixed_best"]["mid"]
    return dict(cell=res["cell"], split=res["split"], profile=res["profile"], r=res["r"], fixed_best_mid=f, window_mid=res["window_best"]["mid"],
                aero_mid={p: round(f + a["delta_vs_best_fixed"], 2) for p, a in res["aero"].items()},
                aero_window_mid={p: round(f + a["with_window"]["delta_vs_best_fixed"], 2) for p, a in res["aero"].items()})


if __name__ == "__main__":
    cells = [c for c in R.key_cells() if c["crew"] == "Finale"]
    out = {}
    for tag in ("live_0.68", "patched_0.67"):
        if tag.startswith("patched"):
            PA.patch()
        out[tag] = [summ(R.analyse_cell(c, s, p)) for c in cells for s in M.SPLITS for p in ("average", "strong")]
        for x in out[tag]:
            print(tag, x, flush=True)
    json.dump(out, open("results_finale_knot.json", "w"), indent=0)
