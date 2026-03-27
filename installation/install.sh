#!/bin/bash
# ============================================================
#  ClipVault Installer — Windows-style Clipboard Manager
#  for Ubuntu / Debian-based Linux
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   ClipVault — Clipboard Manager       ║"
echo "  ║   Windows Win+V experience for Ubuntu ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Resolve the project root (parent of this script's directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Step 1: System packages ───────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Installing system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-pyqt5 \
    python3-pil \
    xdotool \
    xclip \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxkbcommon-x11-0

echo -e "${GREEN}✓ System packages ready${NC}"

# ── Step 2: Python packages ───────────────────────────────────────────────────
# PyQt5 is installed via apt above — do NOT install it via pip
# as the pip wheel breaks the xcb platform plugin on Ubuntu.
echo -e "${YELLOW}[2/5] Installing Python packages...${NC}"
pip3 install --quiet --user \
    pyperclip \
    pynput \
    Pillow

echo -e "${GREEN}✓ Python packages ready${NC}"

# ── Step 3: Install app files ─────────────────────────────────────────────────
echo -e "${YELLOW}[3/5] Installing ClipVault...${NC}"
INSTALL_DIR="$HOME/.local/share/clipvault"

# Clean previous install if present
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy the modular app package and project metadata
cp -r "$PROJECT_ROOT/app"            "$INSTALL_DIR/"
cp    "$PROJECT_ROOT/pyproject.toml" "$INSTALL_DIR/"

# Create launcher script
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/clipvault" << 'LAUNCHER'
#!/bin/bash
export DISPLAY="${DISPLAY:-:0}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
python3 "$HOME/.local/share/clipvault/app/main.py" "$@"
LAUNCHER
chmod +x "$HOME/.local/bin/clipvault"

# Make sure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
    export PATH="$HOME/.local/bin:$PATH"
fi

echo -e "${GREEN}✓ ClipVault installed to $INSTALL_DIR${NC}"

# ── Step 4: Desktop entry ─────────────────────────────────────────────────────
echo -e "${YELLOW}[4/5] Creating desktop entry...${NC}"
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/clipvault.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Name=ClipVault
Comment=Windows-style Clipboard Manager for Ubuntu
Exec=$HOME/.local/bin/clipvault
Icon=edit-paste
Terminal=false
Type=Application
Categories=Utility;
Keywords=clipboard;copy;paste;history;
StartupNotify=false
DESKTOP

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo -e "${GREEN}✓ Desktop entry created${NC}"

# ── Step 5: Autostart ─────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Setting up autostart...${NC}"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/clipvault.desktop" << AUTOSTART
[Desktop Entry]
Type=Application
Name=ClipVault
Exec=$HOME/.local/bin/clipvault
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Clipboard Manager
AUTOSTART

echo -e "${GREEN}✓ Autostart configured (starts on login)${NC}"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  ClipVault installed successfully!   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}How to use:${NC}"
echo -e "  • Run now:     ${YELLOW}clipvault${NC}"
echo -e "  • Toggle UI:   ${YELLOW}Super+V  (Win+V)${NC}"
echo -e "  • Or click the ${YELLOW}system tray icon${NC}"
echo ""
echo -e "  ${BLUE}Features:${NC}"
echo -e "  ✓ Clipboard history (text + images)"
echo -e "  ✓ Pin important items"
echo -e "  ✓ Search through history"
echo -e "  ✓ One-click paste"
echo -e "  ✓ Auto-starts on login"
echo ""
echo -e "  ${YELLOW}Note:${NC} Open a new terminal or run ${YELLOW}source ~/.bashrc${NC} if 'clipvault' is not found."
echo ""
