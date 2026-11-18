"""mod_skill v1 model (Barry draft, 2026-11-18). Read-only on sim/velocity_shift; nothing here is live.

Car = fixed stock car (2400 SP + 4 stock parts x 150 = 3000 points = 300.0 stat units, today's L0 car) plus the EARNED
points of the 4 equipped mods. Each mod starts at 0 earned points and fills with race XP up to the ceiling of the tier
the player has bought (tier n = round n; buying tier n+1 raises the ceiling, earned points carry). Each mod's earned
points are freely assignable across POW/HAN/EN at Reiko's (re-assignable for free) but at least X go to the mod's own
stat. Ceiling_n = (today's cap power_n x 10 - 3000) / 4, so a full tier-n kit = today's cap power exactly.
"""
import itertools, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "sim"))
from velocity_shift import progression as P, equations as E

STATS = ("POW", "HAN", "EN")
SI = {"P": 0, "H": 1, "E": 2}
STOCK = E.skill_points(0) + E.MOD_SLOTS * E.MOD_STOCK_PART_POINTS          # 3000
CAP_POWER = tuple(P.combat_power(L, n) for n, L in enumerate(E.CAP_LEVEL))  # live cap power (353.1, 404.19, 462.51)
CEIL = tuple(math.ceil((10 * c - STOCK) / E.MOD_SLOTS) for c in CAP_POWER)   # earned-point ceiling per mod, tiers R1-R3
DIST = tuple(d.lower() for d in E.ROUND_DISTRICTS)

# Base (stock-car) allocation options. B1 = today's L0 car locked (street tune 1500/750/750), B2 = locked even,
# B3 = "setup": the stock car's 3000 points are re-set per race at Reiko's inside 25-50 % of 3000 (750 floor each).
BASES = {"B1_locked_street": ((1500, 750, 750), 0), "B2_locked_even": ((1000, 1000, 1000), 0),
         "B3_setup": ((750, 750, 750), 750)}


def alloc(base, mods, X, district):
    """Best stats toward DISTRICT_TUNE. base = (floors, free); mods = [(stat_idx, earned)]. Returns (stats, dist, band_ok).
    dist = sum |share - tune| / 2 in share points (0 = exact tune)."""
    floors, free = list(base[0]), base[1]
    for s, p in mods:
        floors[s] += X * p; free += (1 - X) * p
    T = sum(floors) + free; t = [x * T for x in E.DISTRICT_TUNE[district]]
    d = [max(0.0, t[i] - floors[i]) for i in range(3)]; D = sum(d)
    st = [floors[i] + (d[i] * free / D if D > 0 else free / 3) for i in range(3)] if D > free + 1e-9 or D == 0 \
        else [floors[i] + d[i] for i in range(3)]
    if D <= free + 1e-9 and D > 0:
        rest = free - D                                   # only when floors already match the tune on every stat
        st = [st[i] + rest * E.DISTRICT_TUNE[district][i] for i in range(3)]
    sh = [x / T for x in st]
    dist = 50 * sum(abs(sh[i] - E.DISTRICT_TUNE[district][i]) for i in range(3))
    ok = all(E.BUILD_STAT_MIN_SHARE - 1e-9 <= x <= E.BUILD_STAT_MAX_SHARE + 1e-9 for x in sh)
    return st, dist, ok


KITS = sorted({"".join(sorted(k, key="PHE".index)) for k in itertools.product("PHE", repeat=4)}, key=lambda k: [ "PHE".index(c) for c in k])
