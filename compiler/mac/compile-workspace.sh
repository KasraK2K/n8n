#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILER_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$COMPILER_DIR")"

SCRIPT_PATH="$COMPILER_DIR/scripts/compile_workspace_spec.py"
SPEC_DIR="$ROOT_DIR/workspace/specs"
OUTPUT_BASE="$ROOT_DIR/workspace/compiled"

PYTHON_BIN=""

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif [[ -x "/opt/homebrew/bin/python3" ]]; then
  PYTHON_BIN="/opt/homebrew/bin/python3"
elif [[ -x "/usr/local/bin/python3" ]]; then
  PYTHON_BIN="/usr/local/bin/python3"
else
  osascript -e 'display dialog "Python 3 was not found. Please install Python 3 and try again." buttons {"OK"} default button "OK" with icon stop'
  exit 9009
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
  osascript -e "display dialog \"Compile script not found:\n$SCRIPT_PATH\" buttons {\"OK\"} default button \"OK\" with icon stop"
  exit 9001
fi

if [[ ! -d "$SPEC_DIR" ]]; then
  osascript -e "display dialog \"Specs folder not found:\n$SPEC_DIR\" buttons {\"OK\"} default button \"OK\" with icon stop"
  exit 9002
fi

mkdir -p "$OUTPUT_BASE"

INPUT_FILE="$(
  osascript <<EOF
set specFolder to POSIX file "$SPEC_DIR"
tell application "System Events"
  activate
  try
    set chosenFile to choose file with prompt "Choose spec JSON file" default location specFolder
    POSIX path of chosenFile
  on error number -128
    return ""
  end try
end tell
EOF
)"

if [[ -z "$INPUT_FILE" ]]; then
  exit 1
fi

DEFAULT_NAME="$(basename "$INPUT_FILE" .json)"

SAVE_PATH="$(
  osascript <<EOF
set outputFolder to POSIX file "$OUTPUT_BASE"
tell application "System Events"
  activate
  try
    set chosenFile to choose file name with prompt "Choose output folder name" default name "$DEFAULT_NAME" default location outputFolder
    POSIX path of chosenFile
  on error number -128
    return ""
  end try
end tell
EOF
)"

if [[ -z "$SAVE_PATH" ]]; then
  exit 2
fi

OUTPUT_DIR="${SAVE_PATH%.*}"

echo ""
echo "Python: $PYTHON_BIN"
echo "Script: $SCRIPT_PATH"
echo "Input : $INPUT_FILE"
echo "Output: $OUTPUT_DIR"
echo ""

"$PYTHON_BIN" "$SCRIPT_PATH" "$INPUT_FILE" --out "$OUTPUT_DIR"
CODE=$?

osascript -e "display dialog \"Compile finished.\n\nOutput:\n$OUTPUT_DIR\" buttons {\"OK\"} default button \"OK\" with icon note"

exit "$CODE"