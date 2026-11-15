"""mods-v1 catalog draft (Barry 2026-11-14): staged mods inside each round, whole points on the 10x scale.

Power model (draft; live sim/ has no per-mod model): every slot holds a stock part worth STOCK_TOTAL / slots points
(the stock car: SP + 600 = live P at L0) until a mod replaces it. Car points = SP + sum(slot values), capped at
min(round / finale-step ceiling, 1.3375 x SP) (the live 1.07 x P cap). Full fill = the live walk's assumption.
Each mod boosts one fixed stat and never changes; the buyer equips the best owned mod per slot of the district's stat
pattern (4 slots: Street PPHE, Wangan PHEE, Touge PPHE; 6 slots: PPHHEE) and rebalances only by buying.
Win rates: live table at the district tune (pattern sets land on the tune for 4 slots, mods-v1 RESULTS; the 6-slot
split penalty is not applied here, see RESULTS). Money: live econ-v1 purses / debt / wholesale (equations.py)."""
import os, sys, json, math, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import equations as E, progression as P

STOCK_TOTAL = 600
RUNGS = E.LADDER_RUNGS
PATTERN = {4: {"street": "PPHE", "wangan": "PHEE", "touge": "PPHE"},
           6: {"street": "PPHHEE", "wangan": "PPHHEE", "touge": "PPHHEE"}}
STATN = {"P": "POW", "H": "HAN", "E": "EN"}
FC = [c for c, _ in P.finale_caps()]      # finale-step ceilings (stat units)

def ceiling_pts(stage):
    return 10 * (E.C_ROUND[stage] if stage < 3 else FC[stage - 3])

def need(L, stage):
    """Points the slots must hold at level L for full fill (stage 0-2 = R1-R3, 3-6 = arc steps to F1-F4)."""
    sp = E.skill_points(L); return max(0.0, min(ceiling_pts(stage), 1.3375 * sp) - sp)

# ── catalog definition: (tier, mk, label (unused; IDs are MOD_<R1|R2|R3|ARC>_<STAT>_<MKn|MYTHn>), fill level the 4 mods must cover, stage of that level, unlock, price) ──
# unlock: (stage, after) with after = rung name in R1-R3 ("open" = round open), or arc race id ("P1", "F1", ...).
TIERS = [
    ("T1", 1, "Street Mk1", 3,   0, {"P": ("open", 0), "*": (0, "kid1")}, 150.0),   # lead stat at open, rest after kid1
    ("T1", 2, "Street Mk2", 9,   0, (0, "kid2"), 500.0),
    ("T1", 3, "Street Mk3", 12,  0, (0, "mat2"), 1000.0),
    ("T2", 1, "Wangan Mk1", 19,  1, {"E": ("open", 1), "*": (1, "kid1")}, 700.0),
    ("T2", 2, "Wangan Mk2", 26,  1, (1, "kid2"), 1500.0),
    ("T2", 3, "Wangan Mk3", 29,  1, (1, "mat2"), 2800.0),
    ("T3", 1, "Touge Mk1", 37,   2, {"P": ("open", 2), "*": (2, "kid1")}, 1200.0),
    ("T3", 2, "Touge Mk2", 44,   2, (2, "kid2"), 2500.0),
    ("T3", 3, "Touge Mk3", 46,   2, (2, "mat2"), 4000.0),
    ("T4", 1, "Myth Mk1", 64,    3, ("arc", "P1"), 2500.0),
    ("T4", 2, "Myth Mk2", 79,    4, ("arc", "F1"), 4000.0),
    ("T4", 3, "Myth Mk3", 94,    5, ("arc", "F2"), 6000.0),
    ("T4", 4, "Myth Mk4", 114,   6, ("arc", "F3"), 8000.0),
]

def build(slots, price_scale=None, prices=None, tiers=None):
    """Catalog for a slot count: points = ceil(need(fill level) / slots); price scaled by 4 / slots (same spend per set)."""
    k = 4.0 / slots if price_scale is None else price_scale
    out = []
    for tier, mk, name, fillL, st, unl, price in (tiers or TIERS):
        price = (prices or {}).get(f"{tier}Mk{mk}", price)
        pts = int(math.ceil(need(fillL, st) / slots - 1e-9))
        for s in "PHE":
            u = unl.get(s, unl["*"]) if isinstance(unl, dict) else unl
            rid = {"T1": "R1", "T2": "R2", "T3": "R3", "T4": "ARC"}[tier]; mkl = f"MYTH{mk}" if tier == "T4" else f"MK{mk}"
            out.append(dict(id=f"MOD_{rid}_{STATN[s]}_{mkl}", tier=tier, mk=mk, stat=s, pts=pts,
                            price=round(price * k, 0), unlock=u, fills_to_L=fillL, aero_id=f"MOD_{rid}_{STATN[s]}_{mkl}_AERO",
                            aero_price=round(1.75 * price * k, 0)))
    return out

def unlocked(cat, done):
    """done = set of unlock tokens reached: ("open", stage), (stage, rung) for R1-R3 wins, ("arc", race) for arc wins."""
    return [m for m in cat if tuple(m["unlock"]) in done]

class Garage:
    def __init__(self, slots, cat):
        self.slots, self.cat, self.owned, self.spent, self.buys = slots, cat, [], 0.0, []
    def equipped(self, district):
        pat = PATTERN[self.slots][district]; eq = []
        for s in "PHE":
            n = pat.count(s); mine = sorted([m for m in self.owned if m["stat"] == s], key=lambda m: -m["pts"])
            eq += mine[:n] + [None] * max(0, n - len(mine))
        return eq
    def slot_points(self, district):
        stock = STOCK_TOTAL / self.slots
        return sum((m["pts"] if m else stock) for m in self.equipped(district))
    def power(self, L, stage, district):
        sp = E.skill_points(L); return min(ceiling_pts(stage), 1.3375 * sp, sp + self.slot_points(district)) / 10.0
    def fill(self, L, stage, district):
        n = need(L, stage); return min(1.0, self.slot_points(district) / n) if n else 1.0
    def shop(self, wallet, L, stage, district, done, wholesale, tag):
        """Realistic buyer: while the car is under full fill, buy the affordable unlocked mod with the largest gain
        (ties: cheaper); never buys power it can't use. Returns the new wallet."""
        while True:
            deficit = need(L, stage) - self.slot_points(district)
            if deficit <= 1e-9: return wallet
            eq = self.equipped(district); pat = PATTERN[self.slots][district]; stock = STOCK_TOTAL / self.slots
            # weakest equipped value per stat
            weakest = {}
            idx = 0
            for s in "PHE":
                vals = [(m["pts"] if m else stock) for m in eq[idx: idx + pat.count(s)]]; idx += pat.count(s)
                if vals: weakest[s] = min(vals)
            best = None
            for m in unlocked(self.cat, done):
                if m["stat"] not in weakest: continue
                price = m["price"] * (1 - E.WHOLESALE_DISCOUNT if wholesale and m["tier"] in ("T1", "T2", "T3") else 1)
                if price > wallet + 1e-9: continue
                gain = min(deficit, m["pts"] - weakest[m["stat"]])
                if gain <= 0: continue
                key = (round(gain, 6), -price)
                if best is None or key > best[0]: best = (key, m, price)
            if best is None: return wallet
            _, m, price = best; self.owned.append(m); wallet -= price; self.spent += price; self.buys.append((tag, m["id"], price))

# Canon-aligned staging option (design/07: lieutenant wins expand Reiko's stock): Mk2 after mat1, Mk1 sized larger.
TIERS_CANON = [
    ("T1", 1, "Street Mk1", 6,   0, ("open", 0), 150.0),
    ("T1", 2, "Street Mk2", 9,   0, (0, "mat1"), 500.0),
    ("T1", 3, "Street Mk3", 12,  0, (0, "mat2"), 1000.0),
    ("T2", 1, "Wangan Mk1", 22,  1, ("open", 1), 700.0),
    ("T2", 2, "Wangan Mk2", 26,  1, (1, "mat1"), 1500.0),
    ("T2", 3, "Wangan Mk3", 29,  1, (1, "mat2"), 2800.0),
    ("T3", 1, "Touge Mk1", 40,   2, ("open", 2), 1200.0),
    ("T3", 2, "Touge Mk2", 44,   2, (2, "mat1"), 2500.0),
    ("T3", 3, "Touge Mk3", 46,   2, (2, "mat2"), 4000.0),
] + TIERS[9:]
