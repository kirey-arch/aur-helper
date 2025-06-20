#!/bin/bash

REPO="https://github.com/kirey-arch/aur-helper.git"
TMP_DIR="/tmp/aur-helper-install"
BIN_NAME="aur-helper"
DEST_PATH="/usr/local/bin/$BIN_NAME"

echo "💡 Cloning repository..."
git clone --depth=1 "$REPO" "$TMP_DIR" || { echo "❌ Failed to clone repository."; exit 1; }

cd "$TMP_DIR" || { echo "❌ Failed to enter repo directory."; exit 1; }

# Check if precompiled binary exists
if [ -f "$BIN_NAME" ]; then
    echo "🔧 Found binary. Installing to $DEST_PATH..."
    chmod +x "$BIN_NAME"
    sudo mv "$BIN_NAME" "$DEST_PATH"
    echo "✅ Installed binary successfully."
else
    echo "❌ Binary '$BIN_NAME' not found in repository."
    echo "   Try building from source instead."
    exit 1
fi

echo "🧹 Cleaning up..."
cd ~
rm -rf "$TMP_DIR"

echo "🚀 Done! You can now run '$BIN_NAME' from anywhere."
