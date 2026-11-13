"""Rerun the resource screen with the random-belief misread model (MISREAD="random")."""
import screen
cfgs = []
for mode, rf in (("lap", 0.75), ("lap", 0.5), ("race", 0.0)):
    for tf in (1.0, 1.3, 1.6):
        for se in (1.0, 1.5):
            cfgs.append(dict(TANK_MODE=mode, REFILL=rf, TANK_FACTOR=tf, SHARE_EXPONENT=se, DEMAND_SLANT=1.0, TANK_REF_Q=0.6,
                             SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1))
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_F.json")
