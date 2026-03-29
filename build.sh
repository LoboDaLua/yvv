#!/usr/bin/env bash
# Build a standalone executable for the current platform.
#
# Usage:
#   ./build.sh          # build in dist/MetodoMurbach/
#   ./build.sh --clean  # clean rebuild
#
# On Windows, run this script with Git Bash or WSL,
# or use the equivalent:  python -m PyInstaller murbach.spec --clean

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi

echo "==> Building Método Murbach standalone executable..."
python -m PyInstaller murbach.spec "$@"

echo ""
echo "==> Build complete!"
echo "    Output: dist/MetodoMurbach/"
echo ""
echo "    To run:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "      dist\\MetodoMurbach\\MetodoMurbach.exe"
else
    echo "      ./dist/MetodoMurbach/MetodoMurbach"
fi
