"""Shared table model (mod-skill-v1 rules, live win tables). Imports sim/ read-only."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "sim"))
from velocity_shift import progression as P, equations as E  # noqa: E402
CN = json.load(open(os.path.join(ROOT, "unapproved", "barry", "mod-skill-v1", "planner", "constants.json")))
ROUNDS = CN["ROUNDS"]; RUNGS = CN["RUNGS"]; TURNS = CN["TURNS"]
TUNE = {d: tuple(v) for d, v in CN["TUNE"].items()}


def blend(s):
    a = min(1.0, max(0.0, (s - 0.6) / 0.2))
    return [("c6060", (1 - a) ** 2), ("c6080", (1 - a) * a), ("c8060", a * (1 - a)), ("c8080", a * a)]


def win(prof, r, T, d, ps=None, s=None):
    """Shown cell (hardest track where the walk reports it), %; prof 'curve' blends at skill s."""
    if prof == "curve":
        return sum(k * P.hard_win(P.win_pack(p, r, T, d, ps)) for p, k in blend(s) if k > 0)
    return P.hard_win(P.win_pack(prof, r, T, d, ps))


def B_of(rnd, j):
    return CN["C_ROUND"][rnd] / CN["TARGET_R"][ROUNDS[rnd]][j]
