from __future__ import annotations

import json
import shutil
import sys
import urllib.request
import winreg
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
