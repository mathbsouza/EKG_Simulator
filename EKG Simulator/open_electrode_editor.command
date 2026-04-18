#!/bin/zsh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x ".venv/bin/python3" ]; then
  exec ".venv/bin/python3" "scripts/electrode_editor.py"
fi

exec python3 "scripts/electrode_editor.py"
