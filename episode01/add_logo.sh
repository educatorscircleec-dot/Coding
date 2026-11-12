#!/usr/bin/env bash
# Usage: ./add_logo.sh path/to/EduCrew_logo.png
# Overlays the supplied logo, unchanged, in the lower-right corner for the full 60 s.
# Logo is scaled to 180 px wide (aspect preserved), 48 px from the right edge, 150 px from the bottom
# (clear of Instagram's caption area).
set -euo pipefail
LOGO="$1"; DIR="$(cd "$(dirname "$0")" && pwd)"
ffmpeg -y -i "$DIR/EduCrew_E01_A_Little_World_of_Happiness_NO_LOGO.mp4" -i "$LOGO" \
  -filter_complex "[1:v]scale=180:-1:flags=lanczos,format=rgba[lg];[0:v][lg]overlay=W-w-48:H-h-150:format=auto" \
  -c:v libx264 -preset slow -b:v 7M -maxrate 9M -bufsize 14M -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$DIR/EduCrew_E01_A_Little_World_of_Happiness.mp4"
