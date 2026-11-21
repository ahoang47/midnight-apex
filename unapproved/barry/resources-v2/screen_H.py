"""Final combat/resource screen with the live misread rule (MISREAD="live"), around the best screen_D setting.
A = retune-first (lap tank, 75% refill). B = rarely-dry (race tank, TANK_FACTOR 1.6, SHARE_EXPONENT 1.0)."""
import screen
S = dict(SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1, TANK_REF_Q=0.6, MISREAD="live")
cfgs = []
for tf in (1.3, 1.6):
    for g in (0.5, 1.0):
        for ks in (1.0, 1.25, 1.5):
            for te in (2.0, 3.0):
                cfgs.append(dict(S, _set="A", TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=tf, SHARE_EXPONENT=1.5, DEMAND_SLANT=g,
                                 KAPPA_SCALE=ks, TANK_R_EXP=te, _cap=1.05))
for ks in (1.0, 1.25, 1.5):
    for te in (3.0, 4.0):
        for cap in (1.05, 1.10):
            cfgs.append(dict(S, _set="B", TANK_MODE="race", TANK_FACTOR=1.6, SHARE_EXPONENT=1.0, DEMAND_SLANT=0.5,
                             KAPPA_SCALE=ks, TANK_R_EXP=te, _cap=cap))
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_H.json")
