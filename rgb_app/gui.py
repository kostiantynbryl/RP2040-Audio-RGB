from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QFileDialog, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QSlider,
    QSpinBox, QSystemTrayIcon, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from . import __version__
from .ambient import AmbientEngine
from .audio import AudioEngine
from .config import APP_DIR, PRESETS, load_settings, save_settings
from .device import RP2040Device
from .effects import EffectEngine
from .widgets import STYLE, Spectrum, status_card
from .windows import Hotkeys, check_latest_release, flash_uf2, foreground_process, set_autostart


class Bridge(QObject):
    audio = Signal(object)
    ambient = Signal(object, object)
    hotkey = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.device = RP2040Device()
        self.effects = EffectEngine()
        self.bridge = Bridge()
        self.bridge.audio.connect(self.on_audio)
        self.bridge.ambient.connect(self.on_ambient)
        self.bridge.hotkey.connect(self.on_hotkey)
        self.audio = AudioEngine(self.settings, self.bridge.audio.emit)
        self.ambient = AmbientEngine(self.bridge.ambient.emit)
        self.enabled = True
        self.static_color = (100, 60, 255)
        self.last_audio = time.monotonic()
        self.last_profile_process = ""
        self.smoothed_rgb = [0.0, 0.0, 0.0]
        self.firmware_info = ""

        self.setWindowTitle(f"RP2040 Audio RGB {__version__}")
        self.resize(1180, 800)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._build_tray()
        self._build_hotkeys()

        self.device.connect()
        if self.device.connected:
            self.firmware_info = self.device.info()
        self.refresh_status()
        self.audio.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(500)

    def slider(self, low, high, value, callback):
        widget = QSlider(Qt.Horizontal)
        widget.setRange(low, high)
        widget.setValue(value)
        widget.valueChanged.connect(callback)
        return widget

    def _build_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self._dashboard_tab(), "Dashboard")
        tabs.addTab(self._reactive_tab(), "Reactive")
        tabs.addTab(self._effects_tab(), "Effects")
        tabs.addTab(self._ambient_tab(), "Ambient")
        tabs.addTab(self._profiles_tab(), "App Profiles")
        tabs.addTab(self._device_tab(), "RP2040")
        tabs.addTab(self._settings_tab(), "Settings")

    def _dashboard_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        cards = QHBoxLayout()
        card, self.device_label = status_card("RP2040", "Connecting…")
        cards.addWidget(card)
        card, self.audio_label = status_card("Audio", "Starting…")
        cards.addWidget(card)
        card, self.fps_label = status_card("Performance", "0 FPS")
        cards.addWidget(card)
        card, self.rgb_label = status_card("Output", "0, 0, 0")
        cards.addWidget(card)
        layout.addLayout(cards)
        self.spectrum = Spectrum()
        layout.addWidget(self.spectrum)
        self.level = QProgressBar()
        self.level.setRange(0, 1000)
        layout.addWidget(self.level)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(160)
        layout.addWidget(self.log_box)
        return page

    def _reactive_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self.source = QComboBox()
        self.source.addItems(["system", "microphone"])
        self.source.setCurrentText(self.settings.source_mode)
        self.source.currentTextChanged.connect(self.change_source)
        form.addRow("Audio source", self.source)

        self.audio_devices = QComboBox()
        self.refresh_audio_devices()
        self.audio_devices.currentIndexChanged.connect(self.change_audio_device)
        form.addRow("Audio device", self.audio_devices)

        self.mode = QComboBox()
        self.mode.addItems(["spectrum", "bass_pulse", "gradient", "static", "breathing", "pulse", "rainbow"])
        self.mode.setCurrentText(self.settings.mode)
        self.mode.currentTextChanged.connect(lambda value: setattr(self.settings, "mode", value))
        form.addRow("Reactive mode", self.mode)

        self.preset = QComboBox()
        self.refresh_preset_combo()
        self.preset.currentTextChanged.connect(self.apply_preset)
        form.addRow("Preset", self.preset)

        preset_buttons = QHBoxLayout()
        save = QPushButton("Save current as preset")
        save.clicked.connect(self.save_custom_preset)
        preset_buttons.addWidget(save)
        form.addRow(preset_buttons)

        self.brightness = self.slider(1, 100, self.settings.brightness,
                                      lambda value: setattr(self.settings, "brightness", value))
        form.addRow("Brightness", self.brightness)
        self.sensitivity = self.slider(-80, -20, int(self.settings.db_min),
                                       lambda value: setattr(self.settings, "db_min", float(value)))
        form.addRow("Sensitivity / dB floor", self.sensitivity)
        self.attack = self.slider(1, 100, int(self.settings.attack * 100),
                                  lambda value: setattr(self.settings, "attack", value / 100))
        form.addRow("Attack", self.attack)
        self.release = self.slider(1, 100, int(self.settings.release * 100),
                                   lambda value: setattr(self.settings, "release", value / 100))
        form.addRow("Release", self.release)
        self.smoothness = self.slider(1, 100, int(self.settings.smoothness * 100),
                                      lambda value: setattr(self.settings, "smoothness", value / 100))
        form.addRow("Color smoothness", self.smoothness)
        auto_gain = QCheckBox("Automatic gain")
        auto_gain.setChecked(self.settings.auto_gain)
        auto_gain.toggled.connect(lambda value: setattr(self.settings, "auto_gain", value))
        form.addRow(auto_gain)
        color = QPushButton("Choose main effect color")
        color.clicked.connect(self.choose_color)
        form.addRow(color)
        layout.addLayout(form)
        layout.addWidget(self._band_editor())
        return page

    def _band_editor(self):
        box = QGroupBox("Bass / Mid / High editor")
        grid = QGridLayout(box)
        grid.addWidget(QLabel("Band"), 0, 0)
        grid.addWidget(QLabel("Low Hz"), 0, 1)
        grid.addWidget(QLabel("High Hz"), 0, 2)
        grid.addWidget(QLabel("Gain %"), 0, 3)
        grid.addWidget(QLabel("Color"), 0, 4)
        for row, name in enumerate(("bass", "mid", "high"), start=1):
            band = self.settings.bands[name]
            grid.addWidget(QLabel(name.title()), row, 0)
            low = QSpinBox(); low.setRange(20, 18000); low.setValue(band.low)
            low.valueChanged.connect(lambda value, n=name: setattr(self.settings.bands[n], "low", value))
            high = QSpinBox(); high.setRange(30, 20000); high.setValue(band.high)
            high.valueChanged.connect(lambda value, n=name: setattr(self.settings.bands[n], "high", value))
            gain = QSpinBox(); gain.setRange(10, 400); gain.setValue(int(band.gain * 100))
            gain.valueChanged.connect(lambda value, n=name: setattr(self.settings.bands[n], "gain", value / 100))
            color = QPushButton("Select")
            color.clicked.connect(lambda _, n=name: self.choose_band_color(n))
            grid.addWidget(low, row, 1); grid.addWidget(high, row, 2); grid.addWidget(gain, row, 3); grid.addWidget(color, row, 4)
        return box

    def _effects_tab(self):
        page = QWidget()
        grid = QGridLayout(page)
        for index, name in enumerate(["static", "breathing", "pulse", "rainbow", "spectrum", "bass_pulse", "gradient"]):
            button = QPushButton(name.replace("_", " ").title())
            button.setMinimumHeight(70)
            button.clicked.connect(lambda _, selected=name: self.set_mode(selected))
            grid.addWidget(button, index // 3, index % 3)
        return page

    def _ambient_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.ambient_toggle = QCheckBox("Screen Ambient Mode")
        self.ambient_toggle.toggled.connect(self.toggle_ambient)
        layout.addWidget(self.ambient_toggle)
        layout.addWidget(QLabel("Two-zone capture: left half of the display → output #1, right half → output #2."))
        layout.addWidget(QLabel("This mode bypasses audio and is suitable for games, movies and desktop Ambilight."))
        layout.addStretch()
        return page

    def _profiles_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.profile_table = QTableWidget(0, 2)
        self.profile_table.setHorizontalHeaderLabels(["Executable", "Preset"])
        layout.addWidget(self.profile_table)
        row = QHBoxLayout()
        self.profile_exe = QLineEdit()
        self.profile_exe.setPlaceholderText("spotify.exe / chrome.exe / game.exe")
        self.profile_pick = QComboBox()
        self.profile_pick.addItems(list(PRESETS))
        add = QPushButton("Add / update profile")
        add.clicked.connect(self.add_profile)
        row.addWidget(self.profile_exe); row.addWidget(self.profile_pick); row.addWidget(add)
        layout.addLayout(row)
        self.refresh_profiles()
        return page

    def _device_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.device_info = QLabel("—")
        layout.addWidget(self.device_info)
        tests = QHBoxLayout()
        reconnect = QPushButton("Reconnect"); reconnect.clicked.connect(self.reconnect); tests.addWidget(reconnect)
        for text, rgb in [("Red", (255, 0, 0)), ("Green", (0, 255, 0)), ("Blue", (0, 0, 255)), ("White", (255, 255, 255))]:
            button = QPushButton(f"{text} test")
            button.clicked.connect(lambda _, color=rgb: self.test_color(color))
            tests.addWidget(button)
        layout.addLayout(tests)

        order = QHBoxLayout()
        order.addWidget(QLabel("RGB order"))
        self.rgb_order = QComboBox()
        self.rgb_order.addItems(["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"])
        self.rgb_order.setCurrentText(self.settings.rgb_order)
        self.rgb_order.currentTextChanged.connect(lambda value: setattr(self.settings, "rgb_order", value))
        order.addWidget(self.rgb_order)
        calibration = QPushButton("Calibration wizard")
        calibration.clicked.connect(self.calibrate)
        order.addWidget(calibration)
        layout.addLayout(order)

        separate = QCheckBox("Separate RGB output #1 and #2")
        separate.setChecked(self.settings.separate_outputs)
        separate.toggled.connect(lambda value: setattr(self.settings, "separate_outputs", value))
        layout.addWidget(separate)
        second = QComboBox(); second.addItems(["mirror", "complement", "reverse_spectrum"])
        second.setCurrentText(self.settings.second_output_mode)
        second.currentTextChanged.connect(lambda value: setattr(self.settings, "second_output_mode", value))
        layout.addWidget(second)

        pixel_row = QHBoxLayout()
        pixel_row.addWidget(QLabel("WS2812 pixel count"))
        self.pixel_count = QSpinBox(); self.pixel_count.setRange(1, 300); self.pixel_count.setValue(self.settings.ws2812_count)
        self.pixel_count.valueChanged.connect(self.set_pixel_count)
        pixel_row.addWidget(self.pixel_count)
        layout.addLayout(pixel_row)

        flash = QPushButton("Flash firmware .UF2 (BOOTSEL)")
        flash.clicked.connect(self.flash_firmware)
        layout.addWidget(flash)
        layout.addStretch()
        return page

    def _settings_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        autostart = QCheckBox("Start with Windows")
        autostart.setChecked(self.settings.autostart)
        autostart.toggled.connect(self.autostart_changed)
        form.addRow(autostart)
        tray = QCheckBox("Minimize to tray")
        tray.setChecked(self.settings.minimize_to_tray)
        tray.toggled.connect(lambda value: setattr(self.settings, "minimize_to_tray", value))
        form.addRow(tray)
        hotkeys = QCheckBox("Global hotkeys")
        hotkeys.setChecked(self.settings.global_hotkeys)
        hotkeys.toggled.connect(lambda value: setattr(self.settings, "global_hotkeys", value))
        form.addRow(hotkeys)
        form.addRow("Toggle LEDs", QLabel(self.settings.hotkey_toggle))
        form.addRow("Next preset", QLabel(self.settings.hotkey_next_preset))
        form.addRow("Brightness ±", QLabel(f"{self.settings.hotkey_brightness_up} / {self.settings.hotkey_brightness_down}"))
        night = QCheckBox("Night brightness limit")
        night.setChecked(self.settings.night_mode)
        night.toggled.connect(lambda value: setattr(self.settings, "night_mode", value))
        form.addRow(night)
        self.night_brightness = self.slider(1, 100, self.settings.night_brightness,
                                            lambda value: setattr(self.settings, "night_brightness", value))
        form.addRow("Night max brightness", self.night_brightness)
        idle = QComboBox(); idle.addItems(["off", "breathing", "rainbow", "static"]); idle.setCurrentText(self.settings.idle_mode)
        idle.currentTextChanged.connect(lambda value: setattr(self.settings, "idle_mode", value))
        form.addRow("Idle mode", idle)
        update = QPushButton("Check for application update")
        update.clicked.connect(self.check_update)
        form.addRow(update)
        form.addRow("Logs", QLabel(str(APP_DIR / "app.log")))
        return page

    def refresh_audio_devices(self):
        self.audio_devices.clear()
        try:
            for index, name, rate, loopback in self.audio.list_devices():
                suffix = "Loopback" if loopback else "Input"
                self.audio_devices.addItem(f"{name} — {rate} Hz — {suffix}", index)
        except Exception as exc:
            logging.exception("Audio device enumeration failed")

    def refresh_preset_combo(self):
        current = self.settings.preset
        self.preset.clear()
        self.preset.addItems(list(PRESETS) + list(self.settings.custom_presets))
        self.preset.setCurrentText(current)

    def change_source(self, value):
        self.settings.source_mode = value
        self.settings.audio_device_index = None
        self.restart_audio()

    def change_audio_device(self, index):
        if index >= 0:
            self.settings.audio_device_index = self.audio_devices.itemData(index)

    def restart_audio(self):
        self.audio.stop()
        self.audio = AudioEngine(self.settings, self.bridge.audio.emit)
        self.audio.start()
        self.refresh_audio_devices()

    def apply_preset(self, name):
        if not name:
            return
        self.settings.preset = name
        data = PRESETS.get(name) or self.settings.custom_presets.get(name)
        if not data:
            return
        for key, value in data.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.mode.setCurrentText(self.settings.mode)
        self.brightness.setValue(self.settings.brightness)

    def save_custom_preset(self):
        name, ok = QInputDialog.getText(self, "Save preset", "Preset name")
        if not ok or not name.strip():
            return
        self.settings.custom_presets[name.strip()] = {
            "mode": self.settings.mode,
            "brightness": self.settings.brightness,
            "attack": self.settings.attack,
            "release": self.settings.release,
            "smoothness": self.settings.smoothness,
            "db_min": self.settings.db_min,
        }
        self.settings.preset = name.strip()
        self.refresh_preset_combo()
        save_settings(self.settings)

    def set_mode(self, name):
        self.settings.mode = name
        self.mode.setCurrentText(name)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(*self.static_color), self)
        if color.isValid():
            self.static_color = (color.red(), color.green(), color.blue())

    def choose_band_color(self, name):
        band = self.settings.bands[name]
        color = QColorDialog.getColor(QColor(*band.color), self)
        if color.isValid():
            band.color = [color.red(), color.green(), color.blue()]

    def output_brightness(self):
        brightness = self.settings.brightness
        if self.settings.night_mode:
            now = time.strftime("%H:%M")
            if now >= self.settings.night_start or now < self.settings.night_end:
                brightness = min(brightness, self.settings.night_brightness)
        return brightness / 100.0

    def reorder(self, rgb):
        values = dict(zip("RGB", rgb))
        return tuple(values[channel] for channel in self.settings.rgb_order)

    def second_output(self, rgb, bands, level, colors):
        if not self.settings.separate_outputs or self.settings.second_output_mode == "mirror":
            return rgb
        if self.settings.second_output_mode == "complement":
            return tuple(255 - value for value in rgb)
        return self.effects.render("spectrum", tuple(reversed(bands)), level, False, list(reversed(colors)), self.static_color)

    def on_audio(self, frame):
        if self.ambient_toggle.isChecked():
            return
        self.last_audio = time.monotonic()
        bands = (frame.bass, frame.mid, frame.high)
        colors = [self.settings.bands[name].color for name in ("bass", "mid", "high")]
        target = self.effects.render(self.settings.mode, bands, frame.level, frame.beat, colors, self.static_color)
        k = max(0.01, min(1.0, self.settings.smoothness))
        for index in range(3):
            self.smoothed_rgb[index] += (target[index] - self.smoothed_rgb[index]) * k
        factor = self.output_brightness()
        rgb1 = self.reorder(tuple(int(value * factor) for value in self.smoothed_rgb))
        rgb2 = self.second_output(rgb1, bands, frame.level, colors)
        if self.enabled:
            self.device.send_frame(rgb1, rgb2)
        self.level.setValue(int(frame.level * 1000))
        self.spectrum.set_values(frame.spectrum)
        self.fps_label.setText(f"{frame.fps:.0f} FPS · {frame.latency_ms:.1f} ms · drop {frame.dropped}")
        self.rgb_label.setText(f"{rgb1[0]}, {rgb1[1]}, {rgb1[2]}")
        self.audio_label.setText(f"{frame.db:.1f} dB · {'BEAT' if frame.beat else self.settings.source_mode.upper()}")

    def on_ambient(self, left, right):
        if not self.enabled:
            return
        factor = self.output_brightness()
        left = self.reorder(tuple(int(value * factor) for value in left))
        right = self.reorder(tuple(int(value * factor) for value in right))
        self.device.send_frame(left, right)
        self.rgb_label.setText(f"L {left} · R {right}")

    def toggle_ambient(self, enabled):
        if enabled:
            self.ambient.start()
        else:
            self.ambient.stop()

    def tick(self):
        self.refresh_status()
        process = foreground_process()
        if process and process != self.last_profile_process and process in self.settings.app_profiles:
            self.last_profile_process = process
            self.preset.setCurrentText(self.settings.app_profiles[process])
            self.log_message(f"App profile: {process} → {self.settings.app_profiles[process]}")
        if not self.ambient_toggle.isChecked() and time.monotonic() - self.last_audio > self.settings.idle_timeout:
            if self.settings.idle_mode != "off":
                rgb = self.effects.render(self.settings.idle_mode, static_color=self.static_color)
                factor = self.output_brightness()
                rgb = self.reorder(tuple(int(value * factor) for value in rgb))
                if self.enabled:
                    self.device.send_frame(rgb, rgb)

    def refresh_status(self):
        state = "Connected" if self.device.connected else "Disconnected"
        self.device_label.setText(f"{self.device.port or 'Not found'} · {state}")
        info = self.firmware_info or "Legacy/v1 firmware"
        self.device_info.setText(f"Port: {self.device.port or '—'} | {state} | {info} | Frames: {self.device.frames}")

    def reconnect(self):
        self.device.connect()
        self.firmware_info = self.device.info() if self.device.connected else ""
        if self.device.connected:
            self.device.command(f"COUNT {self.settings.ws2812_count}", False)
        self.refresh_status()

    def test_color(self, rgb):
        self.device.send_frame(rgb, rgb)

    def calibrate(self):
        QMessageBox.information(self, "Calibration wizard",
            "Press Red, Green and Blue test buttons. If the physical colors do not match, choose the RGB order that maps them correctly. The selection is saved in the profile.")

    def set_pixel_count(self, value):
        self.settings.ws2812_count = value
        self.device.command(f"COUNT {value}", False)

    def flash_firmware(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select UF2 firmware", "", "UF2 firmware (*.uf2)")
        if not path:
            return
        try:
            destination = flash_uf2(path)
            QMessageBox.information(self, "Firmware", f"Copied to {destination}. RP2040 will reboot automatically.")
        except Exception as exc:
            QMessageBox.critical(self, "Firmware", str(exc))

    def add_profile(self):
        executable = self.profile_exe.text().strip().lower()
        if not executable:
            return
        self.settings.app_profiles[executable] = self.profile_pick.currentText()
        self.profile_exe.clear()
        self.refresh_profiles()
        save_settings(self.settings)

    def refresh_profiles(self):
        self.profile_table.setRowCount(len(self.settings.app_profiles))
        for row, (executable, preset) in enumerate(sorted(self.settings.app_profiles.items())):
            self.profile_table.setItem(row, 0, QTableWidgetItem(executable))
            self.profile_table.setItem(row, 1, QTableWidgetItem(preset))

    def autostart_changed(self, enabled):
        self.settings.autostart = enabled
        try:
            set_autostart(enabled)
        except Exception as exc:
            self.log_message(str(exc))

    def check_update(self):
        try:
            release = check_latest_release()
            QMessageBox.information(self, "Updates", f"Installed: {__version__}\nLatest release: {release['tag'] or 'No release yet'}")
        except Exception as exc:
            QMessageBox.warning(self, "Updates", str(exc))

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("RP2040 Audio RGB")
        menu = QMenu()
        show = QAction("Show", self); show.triggered.connect(self.showNormal); menu.addAction(show)
        toggle = QAction("Toggle LEDs", self); toggle.triggered.connect(self.toggle_enabled); menu.addAction(toggle)
        quit_action = QAction("Exit", self); quit_action.triggered.connect(QApplication.quit); menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda *_: self.showNormal())
        self.tray.show()

    def _build_hotkeys(self):
        actions = {
            "toggle": lambda: self.bridge.hotkey.emit("toggle"),
            "next_preset": lambda: self.bridge.hotkey.emit("next_preset"),
            "brightness_up": lambda: self.bridge.hotkey.emit("brightness_up"),
            "brightness_down": lambda: self.bridge.hotkey.emit("brightness_down"),
        }
        self.hotkeys = Hotkeys(self.settings, actions)
        self.hotkeys.start()

    def on_hotkey(self, action):
        if action == "toggle":
            self.toggle_enabled()
        elif action == "next_preset":
            index = (self.preset.currentIndex() + 1) % max(1, self.preset.count())
            self.preset.setCurrentIndex(index)
        elif action == "brightness_up":
            self.brightness.setValue(min(100, self.brightness.value() + 10))
        elif action == "brightness_down":
            self.brightness.setValue(max(1, self.brightness.value() - 10))

    def toggle_enabled(self):
        self.enabled = not self.enabled
        self.log_message(f"LEDs {'enabled' if self.enabled else 'disabled'}")
        if not self.enabled:
            self.device.off()

    def log_message(self, message):
        text = time.strftime("%H:%M:%S") + "  " + message
        self.log_box.append(text)
        logging.info(message)

    def closeEvent(self, event):
        save_settings(self.settings)
        if self.settings.minimize_to_tray:
            event.ignore()
            self.hide()
        else:
            self.shutdown()
            event.accept()

    def shutdown(self):
        save_settings(self.settings)
        self.audio.stop()
        self.ambient.stop()
        self.device.off()
        self.device.disconnect()
        self.hotkeys.stop()


def run():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=APP_DIR / "app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    if "--minimized" not in sys.argv:
        window.show()
    app.aboutToQuit.connect(window.shutdown)
    return app.exec()
