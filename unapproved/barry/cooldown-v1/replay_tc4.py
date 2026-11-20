"""Replay of Austin's TC4 Touge playtest (Gordon relay 2026-11-20) on the live sim (83b98d8 engine pieces), Godot rules
(race_core.gd _resolve: rival first under the boss heat rule, player under player heat; HAND = P,H,E x3).
Player WRX draft block POW/HAN/EN 750/750/1500 (Wangan shape), opponent MX-5 1350/750/900 (Touge shape), r = 1."""
import json, struct, sys
sys.path.insert(0, "../../../sim")
from random import Random
from velocity_shift.models import Stance, CombatantStats, TurnState
from velocity_shift.combat import pick_line, resolve_turn, parse_line
from velocity_shift.heat import HeatGauges, track_wear, boss_stance
from velocity_shift import equations as E

d = json.load(open("tc4.json")); f = lambda h: struct.unpack(">d", bytes.fromhex(h[2:]))[0]
cfg = json.load(open("../../../spec/race_config.json")); corners = [c["corner"] for c in cfg["corners"]]
HAND = "PHEPHEPHE"; S = {"P": Stance.POW, "H": Stance.HAN, "E": Stance.EN}


def replay(pl, op, turns, seed, verbose=True):
    rng = Random(seed); ro = Random(seed + E.OPPONENT_QTE_SEED_OFFSET); wear = track_wear("touge", corners)
    P = CombatantStats(name="P", pow=pl[0], han=pl[1], en=pl[2], level=50); O = CombatantStats(name="O", pow=op[0], han=op[1], en=op[2], level=50)
    r = (pl[0] + pl[1] + pl[2]) / sum(op)
    pg = HeatGauges.for_player(P.pow, P.en, P.han, r, wear); og = HeatGauges.for_boss(O.pow, O.en, O.han, wear)
    cp = co = 0.0; rows = []
    for t, (corner, tr) in enumerate(zip(corners, turns), 1):
        line = parse_line(pick_line("touge", corner, rng)) if isinstance(pick_line("touge", corner, Random(0)), str) else pick_line("touge", corner, rng)
        pg.begin_turn(); og.begin_turn(); want = [HAND[i] for i in tr["picks"]]
        ps, os_, pm, om, pl_, ol = [], [], [], [], [], []
        for ci in range(3):
            o_s = boss_stance(og, line[ci]); m, _, l = og.play(o_s, corner); os_.append(o_s); om.append(m); ol.append(l)
            p_s = pg.least_loaded(False) if pg.all_locked() else S[want[ci]]
            m, x, l = pg.play(p_s, corner); ps.append(p_s); pm.append(m); pl_.append(l)
        mid_p = [round(v, 2) for v in pg.fill()]; lock_mid = list(pg.locked)
        pg.end_turn(corner); og.end_turn(corner)
        oq = E.round_qte_score(min(E.OPPONENT_QTE_MAX, max(E.OPPONENT_QTE_MIN, ro.gauss(E.OPPONENT_QTE, E.OPPONENT_QTE_SD))))
        q = [f(x) for x in tr["qte"]] if isinstance(tr["qte"][0], str) else tr["qte"]
        res = resolve_turn(TurnState(turn_number=t, player_stances=ps, opponent_stances=os_, player_qte=0.0, opponent_qte=oq,
                                     player_heat_mults=pm, opponent_heat_mults=om, player_qte_phases=q), P, O, race_length=10)
        cp += res.player_progress; co += res.opponent_progress
        rows.append(dict(turn=t, corner=corner, picks="".join(want), played="".join(s.value[0] for s in ps), ai_line="".join(s.value[0] for s in line),
                         ai_played="".join(s.value[0] for s in os_), p_mults=[round(v, 3) for v in pm], p_limp=pl_,
                         p_fill_after_clashes=mid_p, p_locked_after_clashes=lock_mid,
                         p_fill_end=[round(v, 2) for v in pg.fill()], p_locked_end=list(pg.locked),
                         o_fill_end=[round(v, 2) for v in og.fill()], o_locked_end=list(og.locked), o_mults=[round(v, 3) for v in om],
                         ai_qte=oq, cum_p=round(cp, 4), cum_o=round(co, 4)))
    if verbose:
        print("caps P/H/E player", [round(c, 2) for c in pg.cap], "rec", [round(c, 2) for c in pg.rec], "| ai", [round(c, 2) for c in og.cap], [round(c, 2) for c in og.rec])
    return rows, cp, co


if __name__ == "__main__":
    rows, cp, co = replay((750, 750, 1500), (1350, 750, 900), d["turns"], d["seed"])
    for r in rows: print(r)
    print("cum", cp, co, "TC4", f(d["cum_player"]), f(d["cum_opponent"]))
    json.dump(rows, open("replay_tc4.json", "w"), indent=1)
