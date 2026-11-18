"""mod_skill campaign races (mod-skill-v1 results.json, recommended config) and the batch helper."""
import json, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
import st_match as M
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
TUNE = {"street": (0.5, 0.25, 0.25), "wangan": (0.25, 0.25, 0.5), "touge": (0.45, 0.25, 0.3)}
CAP = {"street": 1.044, "wangan": 1.0548, "touge": 1.0702}
RES = json.load(open(os.path.join(HERE, "..", "..", "mod-skill-v1", "results.json")))["configs"]["recommended"]["runs"]
PROF = lambda prof, j: {"c6060": (0.6, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}.get(prof) or (lambda s: (s, s, s))(0.6 + 0.2 * j / 6)


def races():
    out = []
    for mode in ("story", "mixed"):
        for rd in RES[mode]:
            d = rd["district"]
            for j, x in enumerate(rd["rows"]):
                out.append(dict(mode=mode, rnd=rd["rnd"], d=d, rung=x["rung"], j=j, T=x["turns"], r=x["r"], ps=x["pow_share"] / 100,
                                hard=x["rung"] == "boss" or d == "touge"))
    for i, d in enumerate(CAP):
        out.append(dict(mode="cap", rnd=i + 1, d=d, rung="boss", j=6, T=30, r=CAP[d], ps=TUNE[d][0], hard=True))
    return out


def cfg_of(d, track, T, style, sk, r, tune, seed):
    q, qt, pace = sk; tot = 300.0 * r; sp, sh, se = tune
    return MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                       opponent_stats=CombatantStats(name="Opponent", pow=100.0, en=100.0, han=100.0, level=50),
                       max_turns=T, seed=seed, district=d, corners=list(C.official_tracks()[d][track]), player_read=q,
                       player_timing=qt, player_pacing=pace, boss_style=style, encounter_type="boss")


def wv(m):
    a, b = m.player_total_progress, m.opponent_total_progress
    return 1.0 if a > b else 0.5 if a == b else 0.0


def batch(rc, prof, variants, n, seed0):
    """variants: list of (spirit or None, Driver). Paired seeds; returns per-variant win %, and paired delta vs variant 0 with SE."""
    sk = PROF(prof, rc["j"]); tune = (rc["ps"], 0.25, 1 - rc["ps"] - 0.25)
    tracks = [HARD[rc["d"]]] if rc["hard"] else list(C.official_tracks()[rc["d"]])
    acc = [[0.0, 0.0, 0.0] for _ in variants]; N = 0
    for ti, tr in enumerate(tracks):
        for si, st in enumerate(E.BOSS_STYLES):
            for k in range(n):
                seed = seed0 + rc["T"] * 1_000_000 + ti * 100_000 + si * 10_000 + k
                c = cfg_of(rc["d"], tr, rc["T"], st, sk, rc["r"], tune, seed)
                ws = [wv(M.Runner(c, sp, dv).run()) for sp, dv in variants]; N += 1
                for a, w in zip(acc, ws):
                    a[0] += w; a[1] += w - ws[0]; a[2] += (w - ws[0]) ** 2
    out = []
    for a in acc:
        md = a[1] / N
        out.append(dict(win=100 * a[0] / N, delta=100 * md, se=100 * math.sqrt(max(a[2] / N - md * md, 0) / N)))
    return N, out
