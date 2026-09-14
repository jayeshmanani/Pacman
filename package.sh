#!/usr/bin/env bash
# ==============================================================================
# 42 Pac-Man Packaging Script
# Builds a standalone, reproducible distribution of Pac-Man.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo " Packaging 42 Pac-Man Distributable"
echo "=================================================="

# Check if uv is installed
if command -v uv >/dev/null 2>&1; then
    RUNNER="uv run"
else
    RUNNER="python3 -m"
fi

# Clean previous build artifacts
echo "[1/4] Cleaning previous build artifacts..."
rm -rf build dist

# Run PyInstaller using root specification
echo "[2/4] Freezing application with PyInstaller..."
$RUNNER pyinstaller --clean --noconfirm pacman.spec

# Ensure permissions and required runtime files in dist/pacman/
echo "[3/4] Preparing package directory..."
chmod +x dist/pacman/pacman
cp config.json dist/pacman/config.json
# Note: highscores.json is omitted from release packages so fresh installs
# start with an empty leaderboard and automatically generate a new highscores.json
# upon the player's first completed game.

# If INSTRUCTIONS.txt exists at root, copy it; otherwise create minimal instructions
if [ -f INSTRUCTIONS.txt ]; then
    cp INSTRUCTIONS.txt dist/pacman/INSTRUCTIONS.txt
fi

# Create compressed release archives (tar.gz and zip for Itch.io)
echo "[4/4] Creating distribution archives..."
ARCHIVE_NAME="pacman-linux-x86_64.tar.gz"
ZIP_NAME="pacman-linux-x86_64.zip"
tar -czf "dist/$ARCHIVE_NAME" -C dist pacman
python3 -c "import shutil; shutil.make_archive('dist/pacman-linux-x86_64', 'zip', 'dist', 'pacman')"

echo "=================================================="
echo " [SUCCESS] Distributable built successfully!"
echo " Directory: dist/pacman/"
echo " Archives:  dist/$ARCHIVE_NAME"
echo "            dist/$ZIP_NAME (Recommended for Itch.io)"
echo ""
echo " To run the packaged game:"
echo "   cd dist/pacman && ./pacman config.json"
echo "=================================================="
