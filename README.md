# AUR Helper 🧠🐧

A smart, interactive CLI tool for managing packages on Arch Linux.  
Install, remove, purge, and even find similarly named packages with fuzzy matching — all from a single command.

---

## ✨ Features

1. Intelligent fuzzy search for similar packages (google-ch → google-chrome)
2. Install packages with yay, paru, or pacman
3. Remove packages with optional dependency cleanup
4. Full purge mode with orphan + cache cleaning
5. Auto-installs missing helpers (yay/paru) if not found
6. Interactive package selection menu with up to 10 results

---

## 📦 Installation

### Option 1: Download Executable (Recommended)

Just grab the binary from the latest release (https://github.com/kirey-arch/aur-helper/releases), then:

sudo chmod +x aur-helper
sudo mv aur-helper /usr/local/bin/

Or just run:

sudo chmod +x install.sh && ./install.sh

---

Option 2: Run from source

git clone https://github.com/kirey-arch/aur-helper
cd aur-helper
sudo python3 aur-helper.py

---

Option 3: Build binary from source (requires pyinstaller)

yay -S pyinstaller
git clone https://github.com/kirey-arch/aur-helper
cd aur-helper
pyinstaller --onefile aur-helper.py

The compiled binary will be inside the dist/ folder.

---

🧪 Dependencies

 - Python 3.x

 - git, makepkg (for building AUR helpers like yay or paru)

> The precompiled binary bundles everything needed.

---

📜 License

MIT License.
You can read the code if you want. Or just trust the binary. I’m not a cop.

---

💖 Credits

Made with love by [Kirey](https://github.com/kirey-arch).
