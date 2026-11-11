"""Run the SIM side of the two-corner test with the pinned sim's real functions.

Usage: python3 tools/sim_parity.py <inputs.json> [--out out.json] [--no-provisional-w1]

Draw order is the same as velocity_shift.match.run_match (playable engine, line tables):
per corner/turn  1) pick_line(district, corner, rng)  2) draw_weighted_hand(player stats, rng)
then the player's 3 cards (scripted), then resolve_turn(..., race_length=max_turns).
The opponent's cards are its line (hand never blocks it), opponent q_time = OPPONENT_QTE.
Player q_time = timing / QTE_NORMALIZER (qte_factor()).

PROVISIONAL (Austin via Desmond, 2026-11-10): player window W = 1. We patch
equations.knot_window -> 1.0 for the run (clash_progress looks it up at call time).
--no-provisional-w1 runs the sim's real knot_window instead.

Timer-expiry auto-fill (guide §4.2, Godot-only UX): remaining slots take the stance with
the highest remaining count; ties broken in index order Attack, Neutral (letter S), Defend. No RNG.
"""
import argparse, json, sys
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_pin" / "sim"))
from velocity_shift import equations as E  # noqa: E402
from velocity_shift.combat import pick_line, draw_weighted_hand, resolve_turn, line_triples, parse_line  # noqa: E402
from velocity_shift.models import CombatantStats, TurnState, Stance  # noqa: E402

LET = {Stance.ATTACK: "A", Stance.NEUTRAL: "S", Stance.DEFEND: "D"}
ORDER = [Stance.ATTACK, Stance.NEUTRAL, Stance.DEFEND]


class CountingRandom(Random):
    """Python's Random, counting random() calls (for the state token's rng_draws)."""
    draws = 0
    def random(self):
        self.draws += 1
        return super().random()


def autofill(hand_letters, picked_idx):
    used = set(picked_idx)
    out = list(picked_idx)
    while len(out) < 3:
        rem = [i for i in range(len(hand_letters)) if i not in used]
        counts = {s: sum(1 for i in rem if hand_letters[i] == s) for s in "ASD"}
        best = max("ASD", key=lambda s: (counts[s], -"ASD".index(s)))
        i = next(i for i in rem if hand_letters[i] == best)
        out.append(i); used.add(i)
    return out


def stats_from_config(cfg):
    opp_total = getattr(E, cfg["stats"]["opp_total_const"])
    r = E.LADDER_R[cfg["stats"]["ladder_rung"]]
    p_stat = opp_total * r / 3.0
    o_stat = opp_total / 3.0
    return (CombatantStats("Player", p_stat, p_stat, p_stat), CombatantStats("Opponent", o_stat, o_stat, o_stat))


def run(inputs, cfg, provisional_w1=True):
    if provisional_w1:
        E.knot_window = lambda r: 1.0  # PROVISIONAL W=1 hook (see docstring)
    player, opp = stats_from_config(cfg)
    rng = CountingRandom(inputs["seed"])
    out = {"engine": "python-sim", "commit": cfg["pin_commit"], "seed": inputs["seed"],
           "provisional_w1": provisional_w1, "corners": []}
    cum_p = cum_o = 0.0
    for t, (corner_cfg, inp) in enumerate(zip(cfg["corners"], inputs["corners"]), start=1):
        d, c = corner_cfg["district"], corner_cfg["corner"]
        line = pick_line(d, c, rng)
        line_s = "".join(LET[s] for s in line)
        hand = draw_weighted_hand(player.pow, player.en, player.han, rng)
        hand_l = [LET[h.stance] for h in hand]
        picks = autofill(hand_l, inp.get("pick", []))
        p_cards = [hand[i] for i in picks]
        q = inp["timing"] / E.QTE_NORMALIZER
        ts = TurnState(turn_number=t, player_cards=p_cards, opponent_cards=[s for s in line],
                       player_qte=q, opponent_qte=E.OPPONENT_QTE)
        res = resolve_turn(ts, player, opp, race_length=cfg["max_turns"])
        cum_p += res.player_progress; cum_o += res.opponent_progress
        out["corners"].append({
            "district": d, "corner": c, "line": line_s,
            "line_index": line_triples(d, c).index(line_s), "hand": "".join(hand_l),
            "picks": picks, "player_line": "".join(hand_l[i] for i in picks),
            "timing": inp["timing"], "q_time": q,
            "outcomes": [o.value for o in res.battle_outcomes],
            "player_clash": res.player_clash_progress, "opponent_clash": res.opponent_clash_progress,
            "cum_player": cum_p, "cum_opponent": cum_o, "rng_draws_after": rng.draws,
        })
    out["player_total"] = cum_p; out["opponent_total"] = cum_o
    out["winner"] = "Player" if cum_p > cum_o else "Opponent" if cum_o > cum_p else "Tie"
    out["rng_draws"] = rng.draws
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs"); ap.add_argument("--out"); ap.add_argument("--no-provisional-w1", action="store_true")
    ap.add_argument("--config", default=str(ROOT / "spec" / "race_config.json"))
    a = ap.parse_args()
    inp = json.load(open(a.inputs)); cfg = json.load(open(a.config))
    if "races" in inp:
        res = {"races": [run(x, cfg, not a.no_provisional_w1) for x in inp["races"]]}
    else:
        res = run(inp, cfg, not a.no_provisional_w1)
    s = json.dumps(res, indent=1)
    if a.out: Path(a.out).write_text(s)
    print(s)
