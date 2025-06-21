# AUR Helper 🧠🐧

A smart, interactive CLI tool for managing packages on Arch Linux.  
Install, remove, purge, and even find similarly named packages with fuzzy matching — all from a single command.

## ✨ Features

1. Intelligent fuzzy search for similar packages (e.g. google-ch → google-chrome)
2. Install packages with yay, paru, or pacman
3. Remove packages with optional dependency cleanup
4. Full purge mode (orphans + cache cleanup)
5. Auto-installs missing helpers (yay/paru) if needed
6. Interactive package selection with up to 10 fuzzy matches

## 📦 Installation

### 🔹 Option 1: One-liner (Recommended)

curl -sSL https://github.com/kirey-arch/aur-helper/releases/latest/download/install.sh | bash

> Downloads the latest binary and installs it to /usr/local/bin.


### 🔹 Option 2: Manual Download

Get the binary from the latest release page, then:

chmod +x aur-helper && sudo mv aur-helper /usr/local/bin/

Or:

chmod +x install.sh
./install.sh

### 🔹 Option 3: Run from Source

git clone https://github.com/kirey-arch/aur-helper && cd aur-helper && sudo python3 aur-helper.py

### 🔹 Option 4: Build from Source (requires pyinstaller)

yay -S pyinstaller
git clone https://github.com/kirey-arch/aur-helper
cd aur-helper
pyinstaller --onefile aur-helper.py

The compiled binary will be in the dist/ folder.

### 🧪 Dependencies

Python 3.x

git, makepkg (required to build AUR helpers like yay or paru)

> The bundled binary includes everything you need.

### 📜 License

This project is licensed under the GNU General Public License v3.0.

You are free to use, modify, and redistribute this software — as long as any modified version remains free and open-source under the same license.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY — not even that it works.

See the full license in the LICENSE file or read it online at: https://www.gnu.org/licenses/gpl-3.0.html

### 💖 Credits

Built with love, by Kirey (https://github.com/kirey-arch).
