#!/bin/sh
# quick loop: build (no renders) + IoU gate
cd "$(dirname "$0")" && "${BLENDER:-blender}" -b -P build_wrx.py 2>&1 | grep -E "^(TOTAL|body|CLEAR|  )" && python3 bp/bpcompare.py
