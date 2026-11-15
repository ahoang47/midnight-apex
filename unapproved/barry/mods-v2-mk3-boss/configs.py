"""Candidate configs picked from grid3 (one per mandatory-grind count). Grinds sit after the mat1 win, before mat2."""
from velocity_shift import equations as E
L = E.STORY_XP_MULT
def mult(r1_oh1, r1_oh2, r2_oh1, r2_oh2, r3_oh1, r3_oh2):
    m = [list(r) for r in L]
    m[0][4], m[0][5], m[1][4], m[1][5], m[2][4], m[2][5] = r1_oh1, r1_oh2, r2_oh1, r2_oh2, r3_oh1, r3_oh2
    return tuple(tuple(r) for r in m)
CONFIGS = {
    "G1": dict(forced=1, where="mat2",
               fills={("R1", "MK1"): 0, ("R1", "MK2"): 2, ("R2", "MK1"): 15, ("R2", "MK2"): 17, ("R3", "MK1"): 34, ("R3", "MK2"): 36},
               xp=mult(0.63, 0.90, 1.00, 0.30, 1.00, 0.60)),
    "G2": dict(forced=2, where="mat2",
               fills={("R1", "MK1"): 0, ("R1", "MK2"): 2, ("R2", "MK1"): 14, ("R2", "MK2"): 16, ("R3", "MK1"): 34, ("R3", "MK2"): 36},
               xp=mult(0.63, 0.27, 0.40, 0.30, 1.00, 0.30)),
}
