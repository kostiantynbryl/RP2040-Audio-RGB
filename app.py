from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon


def _asset_path(name: str) -> Path:
    """Resolve assets both from source checkout and a PyInstaller bundle."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "assets" / name
    return Path(__file__).resolve().parent / "assets" / name


# MainWindow creates the tray internally. Give every tray instance the project
# icon before Qt makes it visible, eliminating QSystemTrayIcon's empty-icon
# warning without coupling the GUI module to packaging paths.
_original_tray_show = QSystemTrayIcon.show


def _tray_show_with_icon(self):
    if self.icon().isNull():
        icon = QIcon(str(_asset_path("icon.svg")))
        if not icon.isNull():
            self.setIcon(icon)
    return _original_tray_show(self)


QSystemTrayIcon.show = _tray_show_with_icon

from rgb_app.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
