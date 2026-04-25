#!/usr/bin/env bash
# Install philad-cfo dependencies (Unix/macOS)
set -euo pipefail

echo "==> philad-cfo installer"

# Require Python 3.10+
PYTHON=$(command -v python3 || command -v python)
PYVER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYVER < 3.10" | bc -l) -eq 1 ]]; then
    echo "Error: Python 3.10+ required (found $PYVER)" >&2
    exit 1
fi
echo "Using Python $PYVER"

# Install to editable
echo "==> Installing philad-cfo..."
$PYTHON -m pip install --upgrade pip --quiet
$PYTHON -m pip install -e "$(dirname "$0")/.." --quiet

echo "==> Done. Run 'philad-cfo init' to set up your config."
