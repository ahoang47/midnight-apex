"""Writes catalog.json + catalog_results.json / .txt: staged catalog, buyer walks (campaign + arc), 4 and 6 slots,
base prices and an aspirational-price variant. Usage (from sim/):
PYTHONPATH=.:../unapproved/barry/skill-points-v1:../unapproved/barry/mods-v1 python3 ../unapproved/barry/mods-v1/catalog_report.py"""
import os, json, io, contextlib
import catalog as C, catalog_arc as X
from catalog import E, P
HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = {"base": ({}, None), "aspire": ({"T2Mk3": 5000.0, "T3Mk3": 8000.0}, None), "canon": ({}, "canon"), "final": ({"T2Mk3": 5000.0, "T3Mk3": 8000.0}, "canon")}

def summarise(slots, prices, tiers=None):
    cat = C.build(slots, prices=prices, tiers=C.TIERS_CANON if tiers == "canon" else None)
    with contextlib.redirect_stdout(io.StringIO()):
        co, walks, ev, logs = X.run(slots, cat)
    o = dict(slots=slots, prices=prices, campaign={}, arc={})
    for m, (out, G, done) in co.items():
        rows = [r for w in out for r in w["rows"]]
        prof = {"story": "c8080", "mixed": "c8080", "hard": "c6060"}[m]
        o["campaign"][m] = dict(
            spent=round(G.spent), owned=len(G.owned), end_money=round(out[-1]["money"]),
            grinds=[w["total_grind"] for w in out], mixed_split=[(w["wall_grind"], w["post_wall_to_cap"]) for w in out],
            min_fill=min(r["fill"] for r in rows),
            story_boss_8080=[next(r for r in w["rows"] if r["rung"] == "boss")["wr"]["c8080"]["district"] for w in out],
            story_boss_8080_hard=[P.hard_win(next(r for r in w["rows"] if r["rung"] == "boss")["wr"]["c8080"]) for w in out],
            min_8080=[min(min(r["wr"]["c8080"]["district"], P.hard_win(r["wr"]["c8080"])) for r in w["rows"]) for w in out],
            boss_check=[next(r for r in w["rows"] if r["rung"] == "boss")["boss_check"] for w in out],
            grind10_min={pr: min(r["grind10"][pr] for r in rows) for pr in P.PROFILES},
            rows=[{k: r[k] for k in ("rnd", "rung", "arrive_L", "fill", "arrive_r", "live_r", "equipped", "owned", "cash_pre", "money_before", "money_after", "debt", "grind_here", "pre_boss_grind")}
                  | {"wr8080": r["wr"]["c8080"]["district"], "wr8080_hard": P.hard_win(r["wr"]["c8080"]), "wr6060": r["wr"]["c6060"]["district"]} for r in rows],
            buys=G.buys)
    for w in walks:
        fin = [x for x in w["log"] if x["billed"]]
        o["arc"][w["pr"]] = dict(grind=[w["grind"][i]["total"] for i in range(4)], finale_hard=[x["wr_hard"] for x in fin],
                                 min_story_hard=min(x["wr_hard"] for x in w["log"] if not x["billed"]),
                                 end_money=w["end_money"], end_L=w["end_L"], log=logs[w["pr"]])
    o["arc_issues_econ_v1"] = ev.get("issues")
    return cat, o

def first_afford(o, cat, mode):
    """Per Mk tier: the rung it unlocks and the first rung the walk's wallet (money_before, after buys) covers one at list."""
    rows = o["campaign"][mode]["rows"]; out = {}
    for m in cat:
        if m["stat"] != "P" or m["tier"] == "T4": continue
        st, after = m["unlock"]; rnd = (after if st == "open" else st) + 1
        idx = [i for i, r in enumerate(rows) if r["rnd"] == rnd]
        i0 = idx[0] if st == "open" else idx[E.LADDER_RUNGS.index(after)] + 1
        first = next((rows[i]["rung"] for i in range(i0, idx[-1] + 1) if rows[i]["cash_pre"] >= m["price"]), None)
        bought = next((b[0] for b in o["campaign"][mode]["buys"] if b[1] == m["id"]), None)
        out[m["id"]] = dict(price=m["price"], cash_at_unlock=rows[i0]["cash_pre"] if i0 <= idx[-1] else None,
                                                first_affordable_rung=first, first_bought=bought)
    return out

if __name__ == "__main__":
    res, cats = {}, {}
    for v, (pr, tiers) in VARIANTS.items():
        for slots in (4, 6):
            cat, o = summarise(slots, pr, tiers); key = f"{v}_{slots}"
            o["afford"] = {m: first_afford(o, cat, m) for m in ("story", "mixed")}
            res[key] = o; cats[key] = cat
    json.dump(cats, open(os.path.join(HERE, "catalog.json"), "w"), indent=1)
    json.dump(res, open(os.path.join(HERE, "catalog_results.json"), "w"), indent=1)
    with open(os.path.join(HERE, "catalog_results.txt"), "w") as f:
        for k, o in res.items():
            print(f"== {k}", file=f)
            for m, c in o["campaign"].items():
                print(f"  {m}: grinds {c['grinds']} split {c['mixed_split']} spent ${c['spent']} owned {c['owned']} end ${c['end_money']} min fill {c['min_fill']}", file=f)
                print(f"     8080 boss {c['story_boss_8080']} hard {c['story_boss_8080_hard']} min {c['min_8080']} grind10 min {c['grind10_min']}", file=f)
                print(f"     boss_check {[(b['c6060'], b['c8080']) if 'c6060' in b else b for b in c['boss_check']]}", file=f)
            for pr, a in o["arc"].items():
                print(f"  arc {pr}: grind {a['grind']} finale {a['finale_hard']} min story {a['min_story_hard']} end ${a['end_money']:.0f} L{a['end_L']}", file=f)
            for m, af in o["afford"].items():
                print(f"  afford {m}: " + "; ".join(f"{k} ${v['price']:.0f} cash@unlock {v['cash_at_unlock']} first {v['first_affordable_rung']} bought {v['first_bought']}" for k, v in af.items()), file=f)
    print(open(os.path.join(HERE, "catalog_results.txt")).read())
