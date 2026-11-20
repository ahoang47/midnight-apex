#!/bin/bash
# AI-pacing re-pins (Austin 8:11 AM): lock cap + pacing, falloff t 0.5 / 0.7 + pacing. Search (n=1200) then verify.
export SIM=/tmp/pp/sim AI_PACE=1 TARGET=96,90.5,85.5,81,77,72.5,67 SEARCH_N=1200
OUT=pace_lc_search.json python3 repin.py search
python3 repin.py verify pace_lc_search.json pace_lc_verify
for T in 0.5 0.7; do
  FALLOFF_T=$T OUT=pace_fo${T}_search.json python3 repin.py search
  FALLOFF_T=$T python3 repin.py verify pace_fo${T}_search.json pace_fo${T}_verify
done
