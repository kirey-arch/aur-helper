#!/bin/bash

BIN_NAME="aur-helper"
DEST_PATH="/usr/local/bin/$BIN_NAME"
RELEASE_URL="https://github.com/kirey-arch/aur-helper/releases/latest/download/$BIN_NAME"

echo "💡 Downloading $BIN_NAME from latest release..."
curl -L "$RELEASE_URL" -o "$BIN_NAME"

if [ ! -f "$BIN_NAME" ]; then
    echo "❌ Failed to download $BIN_NAME."
    exit 1
fi

echo "🔧 Installing $BIN_NAME to $DEST_PATH..."
chmod +x "$BIN_NAME"
sudo mv "$BIN_NAME" "$DEST_PATH"

echo "✅ Installation completed successfully!"
echo "🚀 You can now run '$BIN_NAME' from anywhere in your terminal."
