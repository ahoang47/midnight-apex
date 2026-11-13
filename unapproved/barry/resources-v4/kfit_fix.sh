#!/bin/bash
# kappa fit at cap 1.10 for the fix-screen picks (perf rows use CAPS[0] = 1.10, but perf rows ignore the cap)
export KF_KS=1.25,1.5,1.75,2.0 KF_CAPS=1.10 KF_LENS=20,30
B='"BOSS_REC_FACTOR": 1.0, "BOSS_RELEASE": 0.8, "BOSS_CAP_TURNS": 3.0, "CAP_TURNS": 3.0, "CAP_R_EXP": 1.0, "REC_R_EXP": 1.0, "KAPPA_SCALE": 1.5, "PEN_FLOOR": 0.4, "RES_T": 0.7, "RES_K": 2.0, "RES_LOOK": 0.5, "PLAN_H": 3'
python3 kfit.py "{$B, \"REC_FACTOR\": 1.0, \"RELEASE\": 0.3, \"AGG_STEP\": 1.0, \"PEN_SHAPE\": \"linear\", \"PEN_SLOPE\": 4.0}" F1
python3 kfit.py "{$B, \"REC_FACTOR\": 1.0, \"RELEASE\": 0.3, \"AGG_STEP\": 1.0, \"PEN_SHAPE\": \"linear\", \"PEN_SLOPE\": 2.0}" F2
python3 kfit.py "{$B, \"REC_FACTOR\": 1.0, \"RELEASE\": 0.5, \"AGG_STEP\": 0.75, \"PEN_SHAPE\": \"linear\", \"PEN_SLOPE\": 2.0}" F8
