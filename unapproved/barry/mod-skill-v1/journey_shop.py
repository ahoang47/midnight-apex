"""PLAYER JOURNEY WITH MOD PURCHASES (Barry, 2026-11-19). Fixes journey.py / journey_setups.py, which assumed the needed mod
tier was owned (no purchase, no cash, no debt). Here, R1 Street:
- Cash: R1 starts at $0 with the $16,000 debt (E.DEBT_AMOUNT); 65 % of every purse goes to the debt while it is open
  (E.DEBT_SHARE), as in walk.py.
- Mods (mods-v1 catalog, E.MOD_SETS, R1 group): Mk1 $150 at round open, Mk2 $500 after the mat1 win, Mk3 $1,000 after the
  mat2 win, one per slot (4 slots, Street PPHE). mod_skill earned-point ceiling per slot by tier, scaled from the mods-v1
  points above the stock part (63 / 68 / 73) to the mod_skill R1 ceiling 133: Mk1 115, Mk2 124, Mk3 133 (Barry mapping,
  draft). Buying a higher Mk keeps the slot's earned points.
- Shop before every attempt and after every win: buy the cheapest available upgrade while cash allows (Mk1 in every slot,
  then Mk2s, then Mk3s). Race XP goes to owned slots with room (spill); XP with no room is LOST from the car but still counts
  in the earned-XP ledger the floors check.
Skill, grind policy, win tables: journey.py. -> journey_shop.json"""
import json, os, random, sys
import journey as J
HERE = os.path.dirname(os.path.abspath(__file__))
CEIL = (0, 115, 124, 133); PRICE = (0, 150.0, 500.0, 1000.0); DEBT0 = 16000.0; SHARE = 0.65


def run(variant, who, runk, M=10000, NM_CAP=15, GOAL=0.5, seed=11):
    seq, sxp = variant["seq"], variant["sxp"]; Q0 = 0.5 if who == "weak" else 0.8
    q = lambda a: min(0.8, Q0 + 0.3 * a / 40); rng = random.Random(seed)
    rows = [dict(race=k, q=0.0, pts=0.0, ledger=0.0, p=0.0, att=0.0, nm=0.0, cash=0.0, debt=0.0, spent=0.0, lost=0.0) for k in seq]
    tot = dict(att=0.0, nm=0.0, lost=0.0, spent=0.0, mk3=0.0, stuck=0.0)
    for _ in range(M):
        st = dict(a=0, money=0.0, debt=DEBT0, spent=0.0, lost=0.0, ledger=3000.0, unlock=1, nmw=0)
        tier = [0] * 4; earned = [0.0] * 4
        pts = lambda: 3000.0 + sum(earned)

        def credit(pay):
            take = min(st["debt"], SHARE * pay) if st["debt"] > 0 else 0.0; st["debt"] -= take; st["money"] += pay - take

        def shop():
            while True:
                opts = [(PRICE[tier[s] + 1], s) for s in range(4) if tier[s] < st["unlock"]]
                if not opts: return
                pr, s = min(opts)
                if pr > st["money"] + 1e-9: return
                st["money"] -= pr; st["spent"] += pr; tier[s] += 1

        def assign(xp):
            st["ledger"] += xp
            for s in sorted(range(4), key=lambda s: earned[s] - CEIL[tier[s]]):
                room = CEIL[tier[s]] - earned[s]
                if room > 0 and xp > 0:
                    t = min(room, xp); earned[s] += t; xp -= t
            st["lost"] += xp

        def race(kind):
            n = 0
            while True:
                shop(); n += 1; st["a"] += 1
                if rng.random() < J.p(kind, q(st["a"] - 1), pts()): return n
                if n >= 400: tot["stuck"] += 1; return n

        for i, k in enumerate(seq):
            row = rows[i]; nm0 = st["nmw"]
            if runk == 2 and k != "we":
                while J.p(k, q(st["a"]), pts()) < GOAL and st["nmw"] < NM_CAP and pts() < 3532 - 1e-9:
                    race("we"); credit(J.WE_CASH); shop(); assign(J.WE_XP); st["nmw"] += 1
            row["nm"] += st["nmw"] - nm0; row["q"] += q(st["a"]); row["pts"] += pts(); row["ledger"] += st["ledger"]
            row["p"] += J.p(k, q(st["a"]), pts())
            row["att"] += race(k)
            credit(J.WE_CASH if k == "we" else J.CASH[k]); shop()
            assign(J.WE_XP if k == "we" else sxp[k])
            if k == "mat1": st["unlock"] = max(st["unlock"], 2)
            if k == "mat2": st["unlock"] = max(st["unlock"], 3)
            shop()
            row["cash"] += st["money"]; row["debt"] += st["debt"]; row["spent"] += st["spent"]; row["lost"] += st["lost"]
        tot["att"] += st["a"]; tot["nm"] += st["nmw"]; tot["lost"] += st["lost"]; tot["spent"] += st["spent"]; tot["mk3"] += (min(tier) == 3)
    for row in rows:
        for key in list(row):
            if key != "race": row[key] = round(row[key] / M, 4 if key in ("q", "p") else 1)
    return dict(variant=variant["name"], who=who, run=runk, rows=rows, **{k: round(v / M, 3) for k, v in tot.items()})


def variant(name, oh2_extra=0):
    import journey_setups as JS
    seq, sxp, fl = JS.setup("M13r"); sxp = dict(sxp); sxp["oh2"] += oh2_extra
    return dict(name=name, seq=seq, sxp=sxp)


if __name__ == "__main__":
    extra = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    V = [variant("M13r", 0)] + ([variant(f"M13r+boss{extra}", extra)] if extra else [])
    out = []
    for v in V:
        for who, rk in (("strong", 1), ("weak", 1), ("weak", 2)):
            o = run(v, who, rk); out.append(o)
            print(v["name"], who, "run", rk, "att", o["att"], "nm", o["nm"], "lost", o["lost"], "spent", o["spent"], "all Mk3", o["mk3"], "stuck", o["stuck"])
            for r in o["rows"]:
                if r["race"] != "we":
                    print("   %-4s q %.3f pts %6.1f ledger %6.1f p1 %5.1f att %4.2f nm %4.2f cash %6.0f debt %6.0f spent %5.0f lost %4.1f" % (
                        r["race"], r["q"], r["pts"], r["ledger"], 100 * r["p"], r["att"], r["nm"], r["cash"], r["debt"], r["spent"], r["lost"]))
    json.dump(out, open(os.path.join(HERE, "journey_shop%s.json" % ("" if not extra else "")), "w"), indent=1)
