#!/bin/bash
set -e
export MAMBA_ROOT_PREFIX=/workspace/tools/mamba-root
eval "$(/workspace/tools/mamba/bin/micromamba shell hook -s bash)"
micromamba activate crt
source "$HOME/.cargo/env"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
S=/workspace/tools/crt/slang-shaders
OUT=/workspace/mockups/crt/out
RAW=/workspace/mockups/crt/raw
DIM=1920x1440
FRAMES=3
RT=opengl3

declare -A PRESETS=(
  [royale_kurozumi]="$S/presets/crt-royale-kurozumi.slangp"
  [guest_adv_ntsc]="$S/crt/crt-guest-advanced-ntsc.slangp"
  [guest_advanced]="$S/crt/crt-guest-advanced.slangp"
  [lottes]="$S/crt/crt-lottes.slangp"
  [geom]="$S/crt/crt-geom.slangp"
  [easymode]="$S/crt/crt-easymode.slangp"
  [zfast]="$S/crt/crt-zfast.slangp"
  [hyllian]="$S/crt/crt-hyllian.slangp"
)
# fix zfast path
PRESETS[zfast]="$S/crt/zfast-crt.slangp"

# Raw baseline: 3x nearest of native 640x480
python3 - <<PY
from PIL import Image
for scene in ('entry_blend50','overworld_blend50'):
  im=Image.open(f'$RAW/{scene}_640x480.png').convert('RGB')
  im.resize((1920,1440), Image.NEAREST).save(f'$OUT/{scene}__raw.png')
  print('raw', scene)
PY

SCENES=(entry_blend50 overworld_blend50)
NAMES=(royale_kurozumi guest_adv_ntsc guest_advanced lottes geom easymode zfast hyllian)

for scene in "${SCENES[@]}"; do
  IMG="$RAW/${scene}_640x480.png"
  for name in "${NAMES[@]}"; do
    preset="${PRESETS[$name]}"
    out="$OUT/${scene}__${name}.png"
    if [[ -f "$out" && "$FORCE" != 1 ]]; then echo "skip $out"; continue; fi
    echo "=== $scene / $name ==="
    set +e
    librashader-cli render -r "$RT" -p "$preset" -i "$IMG" -o "$out" -d "$DIM" -f "$FRAMES" >"$OUT/log_${scene}__${name}.txt" 2>&1
    ec=$?
    set -e
    if [[ $ec -ne 0 ]]; then
      echo "FAIL $name ($ec)"; tail -5 "$OUT/log_${scene}__${name}.txt"
      rm -f "$out"
    else
      python3 -c "from PIL import Image; import numpy as np; im=Image.open('$out'); a=np.asarray(im); print('ok', '$name', im.size, 'mean', round(float(a.mean()),2), 'max', int(a.max()))"
    fi
  done
done
echo DONE
