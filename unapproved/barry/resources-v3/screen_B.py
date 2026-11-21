"""Screen B: release threshold (hysteresis) and penalty-curve shape around the screen-A combat fits, plus steeper
stat-share curves and cap 1.10 for the high-recovery fit. Includes the rationing-vs-greedy pacing gap."""
import screen3
PEN = {"lin": dict(PEN_SHAPE="linear", PEN_SLOPE=2.0, PEN_FLOOR=0.4), "quad": dict(PEN_SHAPE="quadratic", PEN_SLOPE=4.0, PEN_FLOOR=0.4)}
BASES = [(3.0, 1.0, 1.0, 1.5), (4.5, 0.9, 1.0, 1.5), (2.0, 1.0, 1.0, 1.0), (4.5, 1.15, 2.0, 1.5)]
cfgs = []
for ct, rf, rx, ks in BASES:
    for rel in (0.6, 0.8):
        for pn, pv in PEN.items():
            cfgs.append(dict(CAP_TURNS=ct, REC_FACTOR=rf, CAP_R_EXP=rx, REC_R_EXP=rx, KAPPA_SCALE=ks, RELEASE=rel, _pen=pn, **pv, _cap=1.05, _pacing=True))
for ct, rf, rx, ks in [(4.5, 1.15, 2.0, 1.5), (3.0, 1.15, 2.0, 1.25)]:
    cfgs.append(dict(CAP_TURNS=ct, REC_FACTOR=rf, CAP_R_EXP=rx, REC_R_EXP=rx, KAPPA_SCALE=ks, RELEASE=0.7, CAP_SHARE_EXP=2.5, REC_SHARE_EXP=2.5, _cap=1.05, _pacing=True))
for ks in (1.25, 1.5):
    cfgs.append(dict(CAP_TURNS=4.5, REC_FACTOR=1.15, CAP_R_EXP=2.0, REC_R_EXP=2.0, KAPPA_SCALE=ks, RELEASE=0.7, _cap=1.10, _pacing=True))
if __name__ == "__main__":
    screen3.sweep(cfgs, "screen_B.json")
