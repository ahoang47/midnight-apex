"""mod_skill, FIXED mod-slot layout (Austin t428u, 2026-11-18): every round runs the same 4 slots, POW, HAN, EN + 1 FLEX.
Spirit meter is CUT: everything here is spirit OFF (live win tables / live SimulationRunner).
Flex options tested:
  free   = the flex mod has no own-stat floor (all its points are freely assignable at Reiko's)
  P/H/E  = the flex mod's own stat (X floor) is set per round; one physical slot, so its earned points carry across rounds
           (no stranding when the district changes).
Everything else as the recommended mod_skill config: X = 0.60, B3 setup base, spill, Mk1 list prices, catch-up.
Ceiling per mod = ceil((10 x cap power - 3000) / 4); total points do not depend on the layout, so the layout only moves the
tune distance (stat shares), which is checked here."""
import json, math, os, sys
import mod_skill as MS, walk as W
from velocity_shift import progression as P, equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
LAYOUT = ("P", "H", "E", "F")


def alloc_flex(base, mods, X, district, flex):
    """mods = [(letter, earned)]; 'F' takes stat `flex` (P/H/E) with the X floor, or no floor if flex == 'free'."""
    floors, free = list(base[0]), base[1]
    for c, p in mods:
        s = MS.SI.get(c if c != "F" else flex)
        if s is None:
            free += p
        else:
            floors[s] += X * p; free += (1 - X) * p
    # reuse MS.alloc with the floors already applied
    return MS.alloc((tuple(floors), free), [], X, district)


class FixedCar(W.Car):
    FLEX = {"street": "P", "wangan": "E", "touge": "P"}

    def kit(self, d):
        return [(c, 1) for c in LAYOUT]

    def equipped(self, d):
        return [(c, self.mods[(c, 1)][1] if (c, 1) in self.mods else 0.0) for c in LAYOUT]

    def points(self, d):
        return MS.STOCK + sum(p for _, p in self.equipped(d))

    def build(self, d):
        return alloc_flex(MS.BASES["B3_setup"], self.equipped(d), self.X, d, self.FLEX[d])


def use(flex):
    FixedCar.FLEX = dict(flex); W.Car = FixedCar


def full_build(rnd, flex, X=0.60, power=None):
    d = MS.DIST[rnd]; e = MS.CEIL[rnd]
    st, dist, ok = alloc_flex(MS.BASES["B3_setup"], [(c, e) for c in LAYOUT], X, d, flex)
    return dict(points=MS.STOCK + 4 * e, shares=[round(100 * x / sum(st), 2) for x in st], tune_dist=round(dist, 3), band_ok=ok)


if __name__ == "__main__":
    out = dict(ceil=MS.CEIL, cap_power=MS.CAP_POWER, c_round=E.C_ROUND if hasattr(E, "C_ROUND") else None,
               ceil_exact_cap=[round((10 * c - MS.STOCK) / 4, 3) for c in MS.CAP_POWER], full_build={})
    for flex in ("free", "P", "H", "E"):
        out["full_build"][flex] = [full_build(r, flex) for r in range(3)]
    print(json.dumps(out, indent=1))
