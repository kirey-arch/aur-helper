#!/bin/bash
BIN_NAME="aur-helper"
BIN_PATH="~/aur-helper/$BIN_NAME"
DEST_PATH="/usr/local/bin/$BIN_NAME"


echo " 💡 Installing $BIN_NAME in $DEST_PATH, please wait..."

if [ ! -f "$BIN_PATH" ]; then
    echo " ❌ Can't found binary on $BIN_PATH"
    exit 1
fi

sudo cp "$BIN_PATH" "$DEST_PATH"
sudo chmod +x "$DEST_PATH"

echo " ✅ Installation successfully completed."
echo " 👾 Now you can type 'sudo $BIN_NAME' from anywhere to run."
