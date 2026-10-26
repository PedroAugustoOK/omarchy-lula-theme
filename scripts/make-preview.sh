#!/bin/bash
# Generate an original minimalist 1800x1012 Omarchy theme preview.
# Usage: ./scripts/make-preview.sh <theme-dir> "<theme name>" <output>
# Example: ./scripts/make-preview.sh . "Lula" preview.png
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/palette.sh"

if (( $# != 3 )); then
  echo "Usage: $0 THEME_DIR NAME OUTPUT" >&2
  exit 2
fi
theme_dir=$1
name=$2
output=$3

rgba() {
  local hex=${1#\#} alpha=$2
  printf 'rgba(%d,%d,%d,%s)' "0x${hex:0:2}" "0x${hex:2:2}" "0x${hex:4:2}" "$alpha"
}

accent=$(color accent)
background=$(color background)
foreground=$(color foreground)
selection=$(color selection)
lighter_bg=$(color lighter_background)
darker_bg=$(color darker_background)
mode=$(color mode)

if [[ $mode == light ]]; then
  a_accent=0.10
  a_selection=0.50
  a_alt=0.35
  ring_alpha=0.16
else
  a_accent=0.30
  a_selection=0.55
  a_alt=0.35
  ring_alpha=0.22
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# Original soft-wash field built from the palette: no wallpaper reused.
magick -size 1800x1012 "xc:$background" \
  \( -size 1800x1012 xc:none -fill "$(rgba "$selection" "$a_selection")" \
     -draw "circle 1420,300 1420,-260" -blur 0x170 \) -compose over -composite \
  \( -size 1800x1012 xc:none -fill "$(rgba "$accent" "$a_accent")" \
     -draw "circle 1500,430 1500,-40" -blur 0x190 \) -compose over -composite \
  \( -size 1800x1012 xc:none -fill "$(rgba "$lighter_bg" "$a_alt")" \
     -draw "circle 320,920 320,380" -blur 0x210 \) -compose over -composite \
  \( -size 1800x1012 xc:none -fill "$(rgba "$darker_bg" "$a_alt")" \
     -draw "circle 880,760 880,300" -blur 0x230 \) -compose over -composite \
  \( -size 1800x1012 xc:none -fill "$(rgba "$accent" 0.08)" \
     -draw "circle 240,930 240,420" -blur 0x210 \) -compose over -composite \
  -stroke "$(rgba "$accent" "$ring_alpha")" -strokewidth 2 -fill none \
  -draw "circle 1500,300 1500,90" \
  -stroke none \
  "$tmp/base.png"

# Wordmark and palette block.
serif=$(fc-match -f "%{file}" "P052")
magick -background none -font "$serif" -pointsize 208 -fill "$foreground" \
  label:"$name" "$tmp/name.png"

# Keep the wordmark within a comfortable measure.
if (( $(magick identify -format '%w' "$tmp/name.png") > 1180 )); then
  magick "$tmp/name.png" -resize 1180x "$tmp/name-scaled.png"
  mv "$tmp/name-scaled.png" "$tmp/name.png"
fi

magick "$tmp/base.png" \
  "$tmp/name.png" -geometry +136+576 -compose over -composite \
  -fill "$accent" -draw "rectangle 142,828 262,832" \
  -fill "$(color red)"     -draw "rectangle 142,872 175,905" \
  -fill "$(color yellow)"  -draw "rectangle 190,872 223,905" \
  -fill "$(color green)"   -draw "rectangle 238,872 271,905" \
  -fill "$(color cyan)"    -draw "rectangle 286,872 319,905" \
  -fill "$(color blue)"    -draw "rectangle 334,872 367,905" \
  -fill "$(color magenta)" -draw "rectangle 382,872 415,905" \
  -depth 8 -strip \
  "$output"

echo "wrote $output"
