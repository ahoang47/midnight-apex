#!/usr/bin/env bash
# Render unapproved/arthur/t4_mods/t4_shop_compare.png in Godot 4.6.3.
# Flat 1280x960 shop list: T1, T2, T3 and T4 side by side. No prices.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$ROOT/godot"
GODOT="${GODOT:-/workspace/tools/godot}"
FONT_SRC="${FONT_SRC:-/workspace/midnight-apex/unapproved/arthur/mockups/line_preview/godot/fonts}"

mkdir -p "$DEST/fonts"
for f in ArchivoBlack-Regular.ttf NimbusSans-Bold.otf OFL-ArchivoBlack.txt LICENSE-URW-base35.txt; do
  if [[ ! -f "$DEST/fonts/$f" && -f "$FONT_SRC/$f" ]]; then
    cp -L "$FONT_SRC/$f" "$DEST/fonts/$f"
  fi
done
if [[ ! -f "$DEST/fonts/ArchivoBlack-Regular.ttf" || ! -f "$DEST/fonts/NimbusSans-Bold.otf" ]]; then
  echo "missing fonts in $DEST/fonts (need Archivo Black and Nimbus Sans Bold)" >&2
  exit 1
fi

echo "import..."
"$GODOT" --headless --path "$DEST" --import --quit || true

echo "render..."
xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$DEST" --rendering-driver opengl3
echo "done $ROOT/t4_shop_compare.png"
