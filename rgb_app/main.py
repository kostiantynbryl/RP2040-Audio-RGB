from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from . import __version__
from . import gui
from .windows import check_latest_release, stage_portable_update


def _version_tuple(value):
    value = (value or "").lstrip("vV")
    parts = []
    for token in value.split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple((parts + [0, 0, 0])[:3])


def _check_and_install_update(window):
    try:
        release = check_latest_release()
        tag = release.get("tag", "")
        if not tag:
            QMessageBox.information(window, "Updates", "No GitHub Release has been published yet.")
            return
        if _version_tuple(tag) <= _version_tuple(__version__):
            QMessageBox.information(window, "Updates", f"You already have the latest version ({__version__}).")
            return
        answer = QMessageBox.question(
            window,
            "Update available",
            f"Installed: {__version__}\nAvailable: {tag}\n\nDownload and install the portable update now?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                window,
                "Development mode",
                "Automatic file replacement is enabled in the packaged EXE build. Update the source checkout with Git while running from Python.",
            )
            return
        stage_portable_update(release)
        QMessageBox.information(window, "Updating", "The update is staged. The application will close and restart with the new files.")
        QApplication.quit()
    except Exception as exc:
        QMessageBox.warning(window, "Update failed", str(exc))


def main():
    gui.MainWindow.check_update = _check_and_install_update
    return gui.run()
