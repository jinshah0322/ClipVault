# ClipVault — Installation Guide

## Quick Install

Run from the **project root** (one level above this folder):

```bash
chmod +x installation/install.sh
./installation/install.sh
```

The script auto-detects the project root, so it works regardless of where you cloned the repo.

---

## What the installer does

| Step | Action |
|------|--------|
| 1 | Installs system packages via `apt-get` (PyQt5, PIL, xdotool, xclip) |
| 2 | Installs Python packages via `pip3 --user` (pynput, pyperclip, Pillow) |
| 3 | Copies the `app/` package to `~/.local/share/clipvault/` and creates the `clipvault` launcher in `~/.local/bin/` |
| 4 | Creates a `.desktop` entry so ClipVault appears in your app menu |
| 5 | Adds an autostart entry so ClipVault launches on login |

---

## Requirements

- Ubuntu 20.04+ or Debian 11+
- X11 display server (Wayland: hotkey limited — use tray icon instead)
- `sudo` access (only needed for `apt-get` in step 1)

---

## Manual install (without the script)

```bash
# 1. System deps
sudo apt install python3 python3-pyqt5 python3-pil xdotool xclip

# 2. Python deps (from pyproject.toml)
pip install -e ".[dev]"

# 3. Run directly from the project root
python3 app/main.py
```

---

## Uninstall

```bash
chmod +x installation/uninstall.sh
./installation/uninstall.sh
```

The script removes all installed files and optionally deletes saved clipboard history.
