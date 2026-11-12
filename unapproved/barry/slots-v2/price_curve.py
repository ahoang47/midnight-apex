"""slots-v2 Q6 (arithmetic only, no sim run): placeholder price curves checked against results_econ.json.
Money is in race-income units: 1 unit = one race's payout in that round. Every payout constant in design/07 §5.1 is TBD, so
every race (story win or grind win) is counted as 1 unit; boss purses will be larger once set. Per crew (default order):
forced income = story wins + forced XP grind races (per profile); spend = purchases x price.
Option P1 'strong-safe': single tier 1.1 units, round-opening restock 0.25 units per mod (6 mods).
Option P2 'grind-matched': per-crew price = min(weak, average) forced income / purchases (spend = what a grinder earns).
Also a carried-wallet pass (surplus rolls into the next crew).
Writes results_price.json."""
import json

SINGLE, RESTOCK_EACH, RESTOCK_N = 1.1, 0.25, 6
PROFILES = ("weak", "average", "strong")


def main():
    crews = json.load(open("results_econ.json"))["crews"]
    out = {"units": "race-income units (1 race = 1 unit, placeholder)", "P1": {"single": SINGLE, "restock_each": RESTOCK_EACH, "crews": {}}, "P2": {"crews": {}}}
    for name, c in crews.items():
        n = c["purchases"]; opener = n > RESTOCK_N          # first crew of a round: 6-mod restock + singles
        singles = n - RESTOCK_N if opener else n
        inc = {p: c["story_wins"] + c["grind"][p] for p in PROFILES}
        s1 = round(singles * SINGLE + (RESTOCK_N * RESTOCK_EACH if opener else 0), 2)
        out["P1"]["crews"][name] = dict(purchases=n, opener=opener, spend=s1, income=inc,
                                        surplus={p: round(inc[p] - s1, 2) for p in PROFILES},
                                        races_of_income_per_single=SINGLE)
        s2 = min(inc["weak"], inc["average"]); price = round(s2 / n, 2)
        out["P2"]["crews"][name] = dict(purchases=n, price_per_purchase=price, spend=s2, income=inc,
                                        extra_money_races={p: max(0, s2 - inc[p]) for p in PROFILES})
    for k in ("P1", "P2"):
        print(k)
        for name, v in out[k]["crews"].items():
            print(" ", name, v)
    # wallet carried across crews (default crew order, crew-level granularity): extra money races needed when it would go negative
    for k in ("P1", "P2"):
        cum = {}
        for p in PROFILES:
            bal, extra = 0.0, 0.0
            for v in out[k]["crews"].values():
                bal += v["income"][p] - v["spend"]
                if bal < 0:
                    extra -= bal; bal = 0.0
            cum[p] = dict(extra_money_races=round(extra, 2), wallet_at_end_R3=round(bal, 2))
        out[k]["carried_wallet"] = cum
        print(k, "carried wallet", cum)
    out["P2"]["extra_money_races_total"] = {p: sum(v["extra_money_races"][p] for v in out["P2"]["crews"].values()) for p in PROFILES}
    out["P1"]["min_surplus"] = {p: min(v["surplus"][p] for v in out["P1"]["crews"].values()) for p in PROFILES}
    print(out["P1"]["min_surplus"], out["P2"]["extra_money_races_total"])
    json.dump(out, open("results_price.json", "w"), indent=1)


if __name__ == "__main__":
    main()
