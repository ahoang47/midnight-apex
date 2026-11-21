"""Combat refit screen on the chosen resource settings (lap tank, 75% refill, TANK_FACTOR 1.6, DEMAND_SLANT 0.5)."""
import itertools, screen
BASE = dict(TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=1.6, DEMAND_SLANT=0.5, SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1)
cfgs = [dict(BASE, SHARE_EXPONENT=se, KAPPA_SCALE=ks, TANK_R_EXP=te, _cap=cap)
        for se in (1.25, 1.5) for ks in (0.75, 1.0, 1.25) for te in (1.0, 3.0, 5.0) for cap in (1.05, 1.10)]
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_D.json")
