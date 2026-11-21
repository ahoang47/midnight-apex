"""Does sizing tanks on a perfect reader's demand (TANK_REF_Q 1.0) with the raw district mix (DEMAND_SLANT 1.0)
let a demand-matched / low-dry car beat an even spread? Same cells as screen.py."""
import screen
cfgs = [dict(TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=tf, SHARE_EXPONENT=se, DEMAND_SLANT=1.0, TANK_REF_Q=1.0,
             SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1) for tf in (1.0, 1.2, 1.5) for se in (1.0, 1.5)]
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_E.json")
