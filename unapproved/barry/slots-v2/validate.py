"""slots-v2 validation: (1) balanced grid point reproduces the official banks (Wangan, Street bit-for-bit; Touge is a fresh
district-layout sample, the official Touge bank is a mask of the mixed final-v1 cache); (2) barycentric interpolation error
vs exact counts at off-grid share points. Writes validate.json."""
import json
import numpy as np
from multiprocessing import Pool
import gen, model as M

E = M.E
TESTS = [(0.2541, 0.4918, 0.2541), (0.3062, 0.3712, 0.3226), (0.4103, 0.2949, 0.2949), (0.3333, 0.3333, 0.3334)]


def exact_bank(sh):
    stats = tuple(300 * np.array(sh))
    return {(d, sd, L): gen.counts(4000, L, 0.6, sd, d, stats) for d in gen.DISTRICTS for sd in gen.SEEDS for L in gen.LENGTHS}


def main():
    out = {"official_match": {}, "interp": []}
    off = dict(np.load("/workspace/barry-drafts/lines-v1/counts_W_SW=IR=AAD.npz")); offs = dict(np.load("/workspace/barry-drafts/lines-v1/counts_S_N90=SSA.npz"))
    b0 = M.bank(0, 0)
    out["official_match"]["wangan"] = all(np.array_equal(b0[("wangan", sd, L)], off[f"{sd}_0.6_{L}"]) for sd in M.SEEDS for L in M.LENGTHS)
    out["official_match"]["street"] = all(np.array_equal(b0[("street", sd, L)], offs[f"{sd}_0.6_{L}"]) for sd in M.SEEDS for L in M.LENGTHS)
    with Pool(4) as p:
        banks = p.map(exact_bank, TESTS)
    for sh, bk in zip(TESTS, banks):
        for r in (1.0355, 1.05):
            for prof in M.PROFILES:
                st = np.array(sh) * 1000 * r; B = 1000.0
                interp = M.wr_batch([(st, 0.0)], B, prof, "pooled")[0]
                qraw = E.expected_hit_quality(E.QTE_SKILL_SIGMA_OVER_A0[prof], M.zone(r, 0.0))
                ex = np.mean([M._wr_from_bank(bk, d, r, np.array(sh) / sum(sh), qraw) for d in M.DISTRICTS], axis=0)
                out["interp"].append(dict(shares=sh, r=r, profile=prof, interp_mean=round(float(interp.mean()), 2), exact_mean=round(float(ex.mean()), 2),
                                          max_abs_bank_diff=round(float(np.abs(interp - ex).max()), 2)))
                print(out["interp"][-1], flush=True)
    out["max_abs_mean_diff"] = max(abs(x["interp_mean"] - x["exact_mean"]) for x in out["interp"])
    out["max_abs_bank_diff"] = max(x["max_abs_bank_diff"] for x in out["interp"])
    print(out["official_match"], out["max_abs_mean_diff"], out["max_abs_bank_diff"])
    json.dump(out, open("validate.json", "w"), indent=1)


if __name__ == "__main__":
    main()
