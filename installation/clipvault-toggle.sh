#!/bin/bash
# Toggle ClipVault visibility via SIGUSR1.
# Called by the GNOME custom keybinding for Super+V.

PID_FILE="$HOME/.local/share/clipvault/clipvault.pid"

if [ ! -f "$PID_FILE" ]; then
    # App not running — launch it
    "$HOME/.local/bin/clipvault" &
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    # Stale PID file — launch the app
    rm -f "$PID_FILE"
    "$HOME/.local/bin/clipvault" &
    exit 0
fi

# App is running — toggle it
kill -USR1 "$PID"
