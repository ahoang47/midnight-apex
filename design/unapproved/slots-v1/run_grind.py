"""slots-v1 part 3: grind counts per scheme / profile for single window sizes and window-mod limits.
Player picks the best loadout at each story rung's skip state (pooled mid); clear rule as official (>= 50). Writes results_grind.json."""
import json
import slots_model as S

CONFIGS = [(w, k) for w in (0.10, 0.20, 0.30, 0.50, 0.75, 1.00) for k in (1, 3)]


def main():
    out = {}
    for prof in S.PROFILES:
        rows, t = S.run(None, prof); out[f"baseline|{prof}"] = t["grind_races"]
    for w, k in CONFIGS:
        S.WINDOW_SIZES = (w,); S.MAX_WINDOW_MODS = k
        for sc in "ABC":
            for prof in S.PROFILES:
                rows, t = S.run(sc, prof)
                picks = [(r["crew"], r["rung"], r["skip_pick"]) for r in rows if r["skip_pick"] not in ("-", "all stat")]
                walls = sum(1 for r in rows if r["skip_pick"] not in ("-", "all stat") and r["clear"] and r["j"] in (3, 6))
                out[f"{sc}|{prof}|+{int(w*100)}%|max{k}"] = dict(grind=t["grind_races"], lost_xp=t["lost_xp"], window_rungs=len(picks),
                                                                 clears_with_window_at_m2_or_boss=walls)
        print(w, k, {kk: v for kk, v in out.items() if kk.endswith(f"+{int(w*100)}%|max{k}")}, flush=True)
    json.dump(out, open("results_grind.json", "w"), indent=1)


if __name__ == "__main__":
    main()
