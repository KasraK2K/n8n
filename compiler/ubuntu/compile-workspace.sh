#!/usr/bin/env bash

set -euo pipefail

PYTHON_BIN="python3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILER_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$COMPILER_DIR")"

SCRIPT_PATH="$COMPILER_DIR/scripts/compile_workspace_spec.py"
SPEC_DIR="$ROOT_DIR/workspace/specs"
OUTPUT_BASE="$ROOT_DIR/workspace/compiled"

if [[ ! -f "$SCRIPT_PATH" ]]; then
  zenity --error --text="Compile script not found:\n$SCRIPT_PATH"
  exit 9001
fi

if [[ ! -d "$SPEC_DIR" ]]; then
  zenity --error --text="Specs folder not found:\n$SPEC_DIR"
  exit 9002
fi

mkdir -p "$OUTPUT_BASE"

INPUT_FILE="$(zenity --file-selection \
  --title="Choose spec JSON file" \
  --filename="${SPEC_DIR}/" \
  --file-filter="JSON files | *.json")" || exit 1

SPEC_NAME="$(basename "$INPUT_FILE" .json)"
OUTPUT_DIR="${OUTPUT_BASE}/${SPEC_NAME}"

"$PYTHON_BIN" "$SCRIPT_PATH" "$INPUT_FILE" --out "$OUTPUT_DIR"

zenity --info \
  --title="Compile finished" \
  --text="Generated files saved to:\n$OUTPUT_DIR"