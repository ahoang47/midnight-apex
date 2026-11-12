#!/usr/bin/env bash
# Stage a runnable Godot 4.6.3 project from Gordon's two-corner scenes + this mockup's overlays, then render.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
GORDON="${GORDON:-/workspace/midnight-apex/unapproved/gordon/two-corner/godot}"
DEST="$ROOT/godot"
GODOT="${GODOT:-/workspace/tools/godot}"

if [[ ! -d "$GORDON" ]]; then
  echo "missing Gordon two-corner project at $GORDON" >&2
  exit 1
fi

# Symlink (or copy) the real-build pieces we don't own. Overlay our files on top.
link_or_copy() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    return 0
  fi
  rm -f "$dest"
  ln -sfn "$src" "$dest"
}

mkdir -p "$DEST"/{scripts/hud,scenes,shaders,art,fonts,spec,assets}

# Directories we mostly reuse
for d in assets spec; do
  rm -rf "$DEST/$d"
  ln -sfn "$GORDON/$d" "$DEST/$d"
done

# Scripts: link every Gordon script, then overwrite the ones we patched / added
find "$GORDON/scripts" -type f \( -name '*.gd' -o -name '*.uid' \) | while read -r f; do
  rel="${f#"$GORDON/"}"
  # don't clobber our overlays if they already exist as real files
  if [[ -f "$DEST/$rel" && ! -L "$DEST/$rel" ]]; then
    continue
  fi
  mkdir -p "$(dirname "$DEST/$rel")"
  ln -sfn "$f" "$DEST/$rel"
done

# Scenes: link Gordon's, keep our line_preview.tscn
find "$GORDON/scenes" -type f | while read -r f; do
  rel="${f#"$GORDON/"}"
  if [[ -f "$DEST/$rel" && ! -L "$DEST/$rel" ]]; then
    continue
  fi
  mkdir -p "$(dirname "$DEST/$rel")"
  ln -sfn "$f" "$DEST/$rel"
done

# Shaders: link all, then we'll patch a copy of scroll.gdshader
find "$GORDON/shaders" -type f | while read -r f; do
  rel="${f#"$GORDON/"}"
  if [[ "$rel" == "shaders/scroll.gdshader" ]]; then
    continue
  fi
  if [[ -f "$DEST/$rel" && ! -L "$DEST/$rel" ]]; then
    continue
  fi
  mkdir -p "$(dirname "$DEST/$rel")"
  ln -sfn "$f" "$DEST/$rel"
done

# Art / fonts: link Gordon's files, keep our overlays
for d in art fonts; do
  find "$GORDON/$d" -maxdepth 1 -type f | while read -r f; do
    base="$(basename "$f")"
    dest="$DEST/$d/$base"
    if [[ -f "$dest" && ! -L "$dest" ]]; then
      continue
    fi
    ln -sfn "$f" "$dest"
  done
done

# Our scroll shader = Gordon's + a gain uniform (brighter pack road, default 1.0 so verge/rail stay put)
python3 - << PY
from pathlib import Path
src = Path("$GORDON/shaders/scroll.gdshader").read_text()
dst = Path("$DEST/shaders/scroll.gdshader")
if "uniform float gain" not in src:
    src = src.replace("uniform float fog_amount = 1.0;",
                      "uniform float fog_amount = 1.0;\nuniform float gain = 1.0;")
    src = src.replace("ALBEDO = mix(t.rgb, fog_color, f);",
                      "ALBEDO = mix(t.rgb * gain, fog_color, f);")
dst.write_text(src)
print("scroll.gdshader with gain written")
PY

chmod +x "$ROOT/run.sh"

echo "import..."
"$GODOT" --headless --path "$DEST" --import --quit || true

echo "render..."
xvfb-run -a -s "-screen 0 1280x960x24" "$GODOT" --path "$DEST" --rendering-driver opengl3

python3 "$ROOT/make_sheet.py"
echo "done $ROOT"
