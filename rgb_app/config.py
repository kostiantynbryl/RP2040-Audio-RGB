from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "RP2040-Audio-RGB"
CONFIG_PATH = APP_DIR / "config.json"


@dataclass
class Band:
    low: int
    high: int
    color: list[int]
    gain: float = 1.0


@dataclass
class Settings:
    source_mode: str = "system"
    audio_device_index: int | None = None
    brightness: int = 100
    db_min: float = -60.0
    db_max: float = -10.0
    attack: float = 0.55
    release: float = 0.12
    smoothness: float = 0.30
    auto_gain: bool = True
    mode: str = "spectrum"
    preset: str = "Gaming"
    idle_mode: str = "breathing"
    idle_timeout: float = 2.0
    night_mode: bool = False
    night_start: str = "23:00"
    night_end: str = "07:00"
    night_brightness: int = 25
    separate_outputs: bool = False
    second_output_mode: str = "mirror"
    rgb_order: str = "RGB"
    ws2812_count: int = 1
    autostart: bool = False
    start_minimized: bool = False
    minimize_to_tray: bool = True
    global_hotkeys: bool = True
    hotkey_toggle: str = "ctrl+alt+l"
    hotkey_next_preset: str = "ctrl+alt+p"
    hotkey_brightness_up: str = "ctrl+alt+up"
    hotkey_brightness_down: str = "ctrl+alt+down"
    check_updates: bool = True
    app_profiles: dict[str, str] = field(default_factory=dict)
    custom_presets: dict[str, dict] = field(default_factory=dict)
    bands: dict[str, Band] = field(default_factory=lambda: {
        "bass": Band(35, 250, [255, 72, 8], 1.30),
        "mid": Band(250, 2000, [0, 255, 170], 1.00),
        "high": Band(2000, 10000, [110, 60, 255], 1.35),
    })


def load_settings() -> Settings:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        return Settings()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        bands = data.pop("bands", None)
        allowed = Settings.__dataclass_fields__
        settings = Settings(**{k: v for k, v in data.items() if k in allowed})
        if bands:
            settings.bands = {k: Band(**v) for k, v in bands.items()}
        return settings
    except Exception:
        return Settings()


def save_settings(settings: Settings) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


PRESETS = {
    "Gaming": {"mode": "spectrum", "brightness": 100, "attack": 0.65, "release": 0.10, "smoothness": 0.24},
    "EDM": {"mode": "bass_pulse", "brightness": 100, "attack": 0.80, "release": 0.08, "smoothness": 0.18},
    "Rock": {"mode": "spectrum", "brightness": 95, "attack": 0.62, "release": 0.13, "smoothness": 0.26},
    "Chill": {"mode": "gradient", "brightness": 70, "attack": 0.35, "release": 0.20, "smoothness": 0.45},
    "Movie": {"mode": "spectrum", "brightness": 55, "attack": 0.35, "release": 0.22, "smoothness": 0.40},
    "Night": {"mode": "spectrum", "brightness": 22, "attack": 0.30, "release": 0.30, "smoothness": 0.55},
}
