#!/bin/bash
# kappa x cap fit for the two retune picks (F2_gentle + overrides)
export KF_KS=1.5,1.75,2.0,2.25,2.5 KF_CAPS=1.07,1.08,1.10 KF_LENS=10,20,30
F2=$(python3 -c "import json;d=json.load(open('../candidates.json'))['F2_gentle'];d={k:v for k,v in d.items() if not k.startswith('_')};print(json.dumps(d)[1:-1])")
python3 kfit_b.py "{$F2, \"DEMAND_SLANT\": 2.0, \"STAT_M_W\": 0.5}" A_sl2_m05
python3 kfit_b.py "{$F2, \"DEMAND_SLANT\": 2.0, \"STAT_M_W\": 1.0}" B_sl2_m10
