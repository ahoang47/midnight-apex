#!/bin/sh
# Reproduce every slots-v1 output (needs numpy and the count banks under /workspace/barry-drafts/{final-v1,lines-v1}).
set -e
cd "$(dirname "$0")"
python3 run.py && python3 run_sizes.py && python3 run_grind.py > /dev/null && python3 run_cap.py > /dev/null
python3 -c "
import json
for f in ['results.json','results_sizes.json','results_cap.json','results_grind.json']:
    d=json.load(open(f)); json.dump(d,open(f,'w'),separators=(',',':'))"
