#!/bin/bash
BIN_NAME="aur-helper"
BIN_PATH="~/usr/local/bin/$BIN_NAME"

echo " 💡 Uninstalling $BIN_NAME in $DEST_PATH, please wait..."

if [ -f "$BIN_PATH" ]; then
    sudo rm "$BIN_PATH"
    echo " ✅ Installation successfully completed."
else
    echo " ❌ Can't found binary on $BIN_PATH"
fi

echo " ✅ Installation successfully completed."

