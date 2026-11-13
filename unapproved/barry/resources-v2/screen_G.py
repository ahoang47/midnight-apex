"""Combat refit screen with MISREAD="random". A = retune-first (lap tank, 75% refill, TANK_FACTOR 1.3);
B = rarely-dry (race tank, TANK_FACTOR 1.6, SHARE_EXPONENT 1.0)."""
import screen
S = dict(SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1, TANK_REF_Q=0.6)
cfgs = []
for se in (1.25, 1.5):
    for g in (0.5, 1.0):
        for ks in (0.5, 0.75, 1.0):
            for te in (2.0, 3.0):
                for cap in (1.05, 1.10):
                    cfgs.append(dict(S, _set="A", TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=1.3, SHARE_EXPONENT=se, DEMAND_SLANT=g,
                                     KAPPA_SCALE=ks, TANK_R_EXP=te, _cap=cap))
for ks in (0.5, 0.75, 1.0):
    for te in (2.0, 3.0):
        for cap in (1.05, 1.10):
            cfgs.append(dict(S, _set="B", TANK_MODE="race", TANK_FACTOR=1.6, SHARE_EXPONENT=1.0, DEMAND_SLANT=1.0,
                             KAPPA_SCALE=ks, TANK_R_EXP=te, _cap=cap))
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_G.json")
