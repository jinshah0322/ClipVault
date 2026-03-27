#!/bin/bash
# ============================================================
#  ClipVault Uninstaller
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   ClipVault — Uninstaller             ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Stop running instance ─────────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Stopping ClipVault if running...${NC}"
pkill -f "clipvault/app/main.py" 2>/dev/null && echo -e "${GREEN}✓ ClipVault stopped${NC}" || echo -e "${GREEN}✓ ClipVault was not running${NC}"

# ── Remove app files ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/5] Removing app files...${NC}"
rm -rf "$HOME/.local/share/clipvault"
rm -f  "$HOME/.local/bin/clipvault"
echo -e "${GREEN}✓ App files removed${NC}"

# ── Remove desktop entry ──────────────────────────────────────────────────────
echo -e "${YELLOW}[3/5] Removing desktop entry...${NC}"
rm -f "$HOME/.local/share/applications/clipvault.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo -e "${GREEN}✓ Desktop entry removed${NC}"

# ── Remove autostart ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/5] Removing autostart entry...${NC}"
rm -f "$HOME/.config/autostart/clipvault.desktop"
echo -e "${GREEN}✓ Autostart entry removed${NC}"

# ── Optionally remove history ─────────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Clipboard history...${NC}"
if [ -f "$HOME/.clipvault_history.json" ]; then
    read -r -p "  Remove saved clipboard history? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        rm -f "$HOME/.clipvault_history.json"
        echo -e "${GREEN}✓ History removed${NC}"
    else
        echo -e "${GREEN}✓ History kept at ~/.clipvault_history.json${NC}"
    fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  ClipVault uninstalled successfully! ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
