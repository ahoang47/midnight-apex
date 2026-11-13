#!/bin/bash
B='"BOSS_REC_FACTOR": 1.0, "BOSS_RELEASE": 0.8, "BOSS_CAP_TURNS": 3.0, "CAP_TURNS": 3.0, "CAP_R_EXP": 1.0, "REC_R_EXP": 1.0, "KAPPA_SCALE": 1.5, "PEN_FLOOR": 0.4, "RES_T": 0.7, "RES_K": 2.0, "RES_LOOK": 0.5, "PLAN_H": 3'
python3 kfit.py "{$B, \"REC_FACTOR\": 0.9, \"RELEASE\": 0.3, \"AGG_STEP\": 1.0, \"PEN_SHAPE\": \"linear\", \"PEN_SLOPE\": 4.0}" M1
python3 kfit.py "{$B, \"REC_FACTOR\": 0.9, \"RELEASE\": 0.3, \"AGG_STEP\": 0.75, \"PEN_SHAPE\": \"linear\", \"PEN_SLOPE\": 4.0}" M2
python3 kfit.py "{$B, \"REC_FACTOR\": 0.9, \"RELEASE\": 0.3, \"AGG_STEP\": 1.0, \"PEN_SHAPE\": \"quadratic\", \"PEN_SLOPE\": 8.0}" M3
