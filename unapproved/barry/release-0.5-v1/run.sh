#!/bin/bash
# Release 0.5 re-pin: search (n=1200) then verify (rungs 2,000, bosses 6,000). Live crew stats verified at 0.5 too (no re-pin) for reference.
export RELEASE=${RELEASE:-0.5} TARGET=${TARGET:-97.5,92,86.5,81,76,71.5,67} SEARCH_N=1200
OUT=r${RELEASE}_search.json python3 repin.py search
python3 repin.py verify r${RELEASE}_search.json r${RELEASE}_verify
