"""Sanity check: our per-corner driver (tools/sim_parity.py) uses the same draw order as the
sim's own run_match. run_match takes one district, so we compare on single-district configs."""
import copy, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "_pin" / "sim"))
import sim_parity as SP
from velocity_shift import equations as E
from velocity_shift.match import run_match
from velocity_shift.models import MatchConfig

base = json.load(open(ROOT / "spec" / "race_config.json"))
worst = 0.0; n = 0
for district, corners in [("touge", ["HP", "ES"]), ("street", ["N90", "CH"])]:
    cfg = copy.deepcopy(base)
    cfg["corners"] = [{"district": district, "corner": c, "dir": "L"} for c in corners]
    for seed in range(100, 140):
        inputs = {"seed": seed, "corners": [{"pick": [0, 2, 4], "timing": 7}, {"pick": [5, 1], "timing": 3}]}
        ours = SP.run(inputs, cfg, provisional_w1=True)
        player, opp = SP.stats_from_config(cfg)
        picks_by_turn = {i + 1: c["picks"] for i, c in enumerate(ours["corners"])}
        hands = {}
        def on_deal(t, ph, oh): hands[t] = list(ph)
        def gpc(t, pos, rem, orem, hist):
            card = hands[t][picks_by_turn[t][pos]]
            return next(c for c in rem if c.stance == card.stance)
        mc = MatchConfig(player_stats=player, opponent_stats=opp, max_turns=2, seed=seed,
                         district=district, corners=corners)
        m = run_match(mc, gpc, lambda t: inputs["corners"][t - 1]["timing"] / E.QTE_NORMALIZER,
                      None, None, on_deal=on_deal)
        for tr, oc in zip(m.turn_results, ours["corners"]):
            for a, b in zip(tr.player_clash_progress + tr.opponent_clash_progress, oc["player_clash"] + oc["opponent_clash"]):
                worst = max(worst, abs(a - b)); n += 1
print(f"driver vs run_match: {n} clash values, max |diff| = {worst}")
