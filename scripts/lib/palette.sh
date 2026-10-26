#!/bin/bash
# Shared development helpers; installed themes use checked-in assets.
if command -v magick >/dev/null 2>&1; then
  IMAGEMAGICK_BIN=$(command -v magick)
elif command -v convert >/dev/null 2>&1; then
  IMAGEMAGICK_BIN=$(command -v convert)
else
  echo "ImageMagick 6 or 7 is required" >&2
  exit 1
fi
magick() {
  if [[ $IMAGEMAGICK_BIN == */convert && ${1:-} == identify ]]; then
    shift
    command identify "$@"
  else
    "$IMAGEMAGICK_BIN" "$@"
  fi
}
color() {
  python3 - "$theme_dir/colors.toml" "$1" <<'PYTHON'
import sys, tomllib
from pathlib import Path
palette = tomllib.loads(Path(sys.argv[1]).read_text())
print(palette[sys.argv[2]])
PYTHON
}
