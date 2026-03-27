# ClipVault — Windows-style Clipboard Manager for Ubuntu

A pixel-perfect recreation of Windows **Win+V clipboard history** for Ubuntu Linux, built with PyQt5.

---

## Features

| Feature | Windows Win+V | ClipVault |
|---------|--------------|-----------|
| Clipboard History | Yes | Yes |
| Text support | Yes | Yes |
| Image support | Yes | Yes |
| Pin items | Yes | Yes |
| Search history | Yes | Yes |
| Global hotkey | Win+V | Super+V |
| One-click paste | Yes | Yes |
| Dark UI | Yes | Yes |
| System tray | Yes | Yes |
| Auto-start on login | Yes | Yes |
| Tabs (All/Pinned/Text/Images) | Yes | Yes |
| Cross-device sync | Yes (MS account) | No |

---

## Project structure

```
clipboard_manager/
├── app/                        # Application package
│   ├── main.py                 # Entry point
│   ├── shared/
│   │   └── constants.py        # Colors, file paths, limits
│   ├── models/
│   │   └── clip_item.py        # ClipItem data model
│   ├── core/
│   │   ├── history_manager.py  # Load/save/search clipboard history
│   │   └── clipboard_watcher.py# QThread — polls system clipboard
│   ├── workers/
│   │   └── hotkey_listener.py  # Daemon thread — global Super+V hotkey
│   └── ui/
│       ├── main_window.py      # ClipVaultWindow (main UI)
│       ├── tray_icon.py        # System tray icon + context menu
│       └── widgets/
│           └── clip_item_widget.py  # Per-item card widget
├── installation/
│   ├── install.sh              # One-shot installer for Ubuntu/Debian
│   └── README.md               # Installation guide
├── requirements.txt
└── README.md
```

---

## Quick install

```bash
chmod +x installation/install.sh
./installation/install.sh
```

Then launch:

```bash
clipvault
```

See [installation/README.md](installation/README.md) for the full installation guide and manual install instructions.

To uninstall:

```bash
chmod +x installation/uninstall.sh
./installation/uninstall.sh
```

---

## Running without installing

```bash
# From the project root
python3 app/main.py
```

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Super+V` | Toggle clipboard window |
| `Escape` | Close window |
| Click item | Paste immediately |
| Pin button | Pin / Unpin item |
| X button | Delete item |

---

## Configuration

History is stored at `~/.clipvault_history.json`.

To change the max history size, edit `app/shared/constants.py`:

```python
MAX_HISTORY = 50  # change this number
```

---

## Compatibility

- Ubuntu 20.04+
- Debian 11+
- Any GNOME / KDE / XFCE desktop on X11
- Wayland: hotkey limited — use the tray icon instead
