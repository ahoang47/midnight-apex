"""Run the SIM side of the two-corner test with the pinned sim's real functions.

Usage: python3 tools/sim_parity.py <inputs.json> [--out out.json]

Draw order is the same as velocity_shift.match.run_match (playable engine, line tables):
per corner/turn  1) pick_line(district, corner, rng)  2) draw_weighted_hand(player stats, rng)
then the player's 3 cards (scripted), then resolve_turn(..., race_length=max_turns).
The opponent's cards are its line (hand never blocks it), opponent q_time = OPPONENT_QTE.
Player QTE (pin f0efecf, Austin approved the re-pin 2026-11-11 10:56 PM PT): per corner "qte": [entry, apex, exit]
raw scores, each null (unplayed = 0), a number, or "0x<16 hex>" IEEE-754 bits. Fed exactly as match.py:201-215 feeds a
3-tuple callback: TurnState(player_qte_phases=[phase_raw_qte(v)...], player_qte=mean_phase_qte(cb)). No W patch: clash
math has no knot_window factor at this pin (the old PROVISIONAL W=1 hook is retired). The zone width the game shows is
qte_zone_width(r, qte_window_mod) at the race's fixed r (match.py:190-192), reported per corner.

Timer-expiry auto-fill (guide §4.2, Godot-only UX): remaining slots take the stance with
the highest remaining count; ties broken in index order Attack, Neutral (letter S), Defend. No RNG.
"""
import argparse, json, struct, sys
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_pin" / "sim"))
from velocity_shift import equations as E  # noqa: E402
from velocity_shift.equations import phase_raw_qte, mean_phase_qte, qte_zone_width  # noqa: E402
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


def fdec(v):
    if isinstance(v, str): return struct.unpack("<d", struct.pack("<Q", int(v, 16)))[0]
    return v if v is None else float(v)


def run(inputs, cfg):
    player, opp = stats_from_config(cfg)
    p_tot = player.pow + player.en + player.han; o_tot = opp.pow + opp.en + opp.han
    r = p_tot / o_tot if o_tot else 1.0
    zw = qte_zone_width(r, cfg.get("qte_window_mod", 0.0))
    rng = CountingRandom(inputs["seed"])
    out = {"engine": "python-sim", "commit": cfg["pin_commit"], "seed": inputs["seed"],
           "zone_width": zw, "corners": []}
    cum_p = cum_o = 0.0
    for t, (corner_cfg, inp) in enumerate(zip(cfg["corners"], inputs["corners"]), start=1):
        d, c = corner_cfg["district"], corner_cfg["corner"]
        line = pick_line(d, c, rng)
        line_s = "".join(LET[s] for s in line)
        hand = draw_weighted_hand(player.pow, player.en, player.han, rng)
        hand_l = [LET[h.stance] for h in hand]
        picks = autofill(hand_l, inp.get("pick", []))
        p_cards = [hand[i] for i in picks]
        cb = tuple(fdec(v) for v in inp["qte"])
        assert len(cb) == 3
        ts = TurnState(turn_number=t, player_cards=p_cards, opponent_cards=[s for s in line],
                       player_qte=mean_phase_qte(cb), opponent_qte=E.OPPONENT_QTE,
                       player_qte_phases=[phase_raw_qte(v) for v in cb])
        res = resolve_turn(ts, player, opp, race_length=cfg["max_turns"])
        cum_p += res.player_progress; cum_o += res.opponent_progress
        out["corners"].append({
            "district": d, "corner": c, "line": line_s,
            "line_index": line_triples(d, c).index(line_s), "hand": "".join(hand_l),
            "picks": picks, "player_line": "".join(hand_l[i] for i in picks),
            "qte_in": list(cb), "qte_phases": res.player_qte_phases, "q_time": res.player_qte, "zone_width": zw,
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
    ap.add_argument("inputs"); ap.add_argument("--out")
    ap.add_argument("--config", default=str(ROOT / "spec" / "race_config.json"))
    a = ap.parse_args()
    inp = json.load(open(a.inputs)); cfg = json.load(open(a.config))
    if "races" in inp:
        res = {"races": [run(x, cfg) for x in inp["races"]]}
    else:
        res = run(inp, cfg)
    s = json.dumps(res, indent=1)
    if a.out: Path(a.out).write_text(s)
    print(s)
