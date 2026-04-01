#!/usr/bin/env bash
# Generate example images for README documentation.
# Run from project root: bash docs/generate-examples.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR/examples"
DEMO="$SCRIPT_DIR/demo.py"

mkdir -p "$EXAMPLES_DIR"

echo "Generating dark theme example (catppuccin-mocha)..."
uv run codepicture "$DEMO" -o "$EXAMPLES_DIR/highlight-dark.png" \
  --theme catppuccin-mocha \
  --highlight '1-3:highlight' \
  --highlight '5-6:add' \
  --highlight '8-9:remove' \
  --highlight '11-12:focus' \
  --no-shadow

echo "Generating light theme example (catppuccin-latte)..."
uv run codepicture "$DEMO" -o "$EXAMPLES_DIR/highlight-light.png" \
  --theme catppuccin-latte \
  --highlight '1-3:highlight' \
  --highlight '5-6:add' \
  --highlight '8-9:remove' \
  --highlight '11-12:focus' \
  --no-shadow

echo "Generating focus mode example..."
uv run codepicture "$DEMO" -o "$EXAMPLES_DIR/highlight-focus.png" \
  --theme catppuccin-mocha \
  --highlight '5-9:focus' \
  --no-shadow

echo "Done. Images saved to $EXAMPLES_DIR/"
ls -la "$EXAMPLES_DIR/"
