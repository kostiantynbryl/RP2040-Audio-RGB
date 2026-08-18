from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import winreg
import zipfile
from pathlib import Path

import psutil

REPO_API = "https://api.github.com/repos/kostiantynbryl/RP2040-Audio-RGB/releases/latest"


def current_executable():
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.argv[0]).resolve())


def set_autostart(enabled):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, "RP2040AudioRGB", 0, winreg.REG_SZ,
                              f'"{current_executable()}" --minimized')
        else:
            try:
                winreg.DeleteValue(key, "RP2040AudioRGB")
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def foreground_process():
    try:
        import win32gui
        import win32process
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return ""


def find_bootsel_drive():
    for partition in psutil.disk_partitions(all=False):
        root = Path(partition.mountpoint)
        if (root / "INFO_UF2.TXT").exists():
            return root
    return None


def flash_uf2(path):
    drive = find_bootsel_drive()
    if not drive:
        raise RuntimeError("RPI-RP2 BOOTSEL drive not found")
    destination = drive / Path(path).name
    shutil.copy2(path, destination)
    return str(destination)


def check_latest_release(timeout=3):
    request = urllib.request.Request(REPO_API, headers={"User-Agent": "RP2040-Audio-RGB"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    return {
        "tag": data.get("tag_name", ""),
        "url": data.get("html_url", ""),
        "assets": data.get("assets", []),
    }


def stage_portable_update(release):
    """Download the portable ZIP and prepare an updater BAT that replaces the current frozen build after exit."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Automatic replacement is available in the packaged EXE build only")
    asset = next((item for item in release.get("assets", []) if item.get("name", "").endswith("portable.zip")), None)
    if not asset:
        raise RuntimeError("Portable update asset was not found in the latest release")
    temp_root = Path(tempfile.mkdtemp(prefix="rp2040-audio-rgb-update-"))
    archive = temp_root / "update.zip"
    request = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "RP2040-Audio-RGB"})
    with urllib.request.urlopen(request, timeout=30) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    extracted = temp_root / "new"
    extracted.mkdir()
    with zipfile.ZipFile(archive) as package:
        package.extractall(extracted)
    install_dir = Path(current_executable()).resolve().parent
    updater = temp_root / "apply_update.bat"
    updater.write_text(
        "@echo off\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        f'xcopy /E /Y /I "{extracted}\\*" "{install_dir}\\" >nul\r\n'
        f'start "" "{install_dir / "RP2040AudioRGB.exe"}"\r\n'
        f'rmdir /S /Q "{temp_root}"\r\n',
        encoding="utf-8",
    )
    subprocess.Popen(["cmd", "/c", "start", "", str(updater)], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return True


class Hotkeys:
    def __init__(self, settings, actions):
        self.settings = settings
        self.actions = actions
        self.registered = []

    def start(self):
        if not self.settings.global_hotkeys:
            return
        try:
            import keyboard
            pairs = [
                (self.settings.hotkey_toggle, "toggle"),
                (self.settings.hotkey_next_preset, "next_preset"),
                (self.settings.hotkey_brightness_up, "brightness_up"),
                (self.settings.hotkey_brightness_down, "brightness_down"),
            ]
            for hotkey, name in pairs:
                keyboard.add_hotkey(hotkey, self.actions[name])
                self.registered.append(hotkey)
        except Exception:
            pass

    def stop(self):
        try:
            import keyboard
            for hotkey in self.registered:
                keyboard.remove_hotkey(hotkey)
        except Exception:
            pass
        self.registered.clear()
