import itertools, screen
cfgs = [dict(TANK_MODE="lap", REFILL=rf, TANK_FACTOR=tf, SHARE_EXPONENT=se, SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1)
        for rf in (0.5, 0.75) for tf in (1.6, 2.0) for se in (1.0, 1.5, 2.0)]
cfgs += [dict(TANK_MODE="race", TANK_FACTOR=tf, SHARE_EXPONENT=se, SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1) for tf in (1.3, 1.6) for se in (1.0, 1.5, 2.0)]
if __name__ == "__main__":
    screen.sweep(cfgs, "screen_B.json")
