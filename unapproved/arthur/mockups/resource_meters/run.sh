#!/usr/bin/env bash
# Stage a runnable Godot 4.6.3 project from the line-preview mockup, overlay the
# resource-meter HUD, and render the concept frames.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="${SRC:-/workspace/midnight-apex/unapproved/arthur/mockups/line_preview/godot}"
DEST="$ROOT/godot"
GODOT="${GODOT:-/workspace/tools/godot}"

if [[ ! -d "$SRC" ]]; then
  echo "missing line-preview project at $SRC" >&2
  exit 1
fi

# Files we own in this mockup — never replace them with a symlink to line_preview.
# art/touge_road.png is a local override of Gordon's touge road texture with
# the lane lines painted out (lane lines are Street/Wangan only, never touge).
OVERLAY=(
  project.godot
  scenes/resource_preview.tscn
  scripts/resource_preview.gd
  scripts/hud.gd
  scripts/hud/resource_stack.gd
  art/touge_road.png
  art/touge_road.png.import
)

is_overlay() {
  local rel="$1"
  local o
  for o in "${OVERLAY[@]}"; do
    if [[ "$rel" == "$o" ]]; then
      return 0
    fi
  done
  return 1
}

link_tree() {
  local from="$1" to="$2"
  mkdir -p "$to"
  # Link files; recurse into directories. Skip our overlays and the local .godot cache.
  find "$from" -mindepth 1 -maxdepth 1 \( -type f -o -type l -o -type d \) | while read -r p; do
    local base="$(basename "$p")"
    local rel="${p#"$from/"}"
    if [[ "$base" == ".godot" ]]; then
      continue
    fi
    if is_overlay "$rel"; then
      continue
    fi
    if [[ -d "$p" && ! -L "$p" ]]; then
      mkdir -p "$to/$base"
      # recurse with a prefix so overlays like scripts/hud.gd are skipped
      find "$p" -type f -o -type l | while read -r f; do
        local r="${f#"$from/"}"
        if is_overlay "$r"; then
          continue
        fi
        # don't clobber a real overlay file if it already exists
        if [[ -f "$to/$r" && ! -L "$to/$r" ]]; then
          continue
        fi
        mkdir -p "$(dirname "$to/$r")"
        ln -sfn "$f" "$to/$r"
      done
    else
      if [[ -f "$to/$base" && ! -L "$to/$base" ]]; then
        continue
      fi
      ln -sfn "$p" "$to/$base"
    fi
  done
}

link_tree "$SRC" "$DEST"

# Make sure our overlay files are real (not leftover symlinks).
for o in "${OVERLAY[@]}"; do
  if [[ ! -f "$DEST/$o" || -L "$DEST/$o" ]]; then
    echo "missing overlay $DEST/$o" >&2
    exit 1
  fi
done

echo "import..."
"$GODOT" --headless --path "$DEST" --import --quit || true

if [[ "${ICONS:-}" == "1" ]]; then
  echo "icons..."
  xvfb-run -a -s "-screen 0 256x256x24" "$GODOT" --path "$DEST" --rendering-driver opengl3 --scene res://scenes/icon_export.tscn
  python3 "$ROOT/make_e3b_sheets.py"
  echo "done icons $ROOT"
  exit 0
fi

echo "render..."
if [[ -n "${ONLY:-}" ]]; then
  export ONLY
fi
xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$DEST" --rendering-driver opengl3

python3 "$ROOT/make_sheet.py"
python3 "$ROOT/make_e3b_sheets.py"
echo "done $ROOT"
