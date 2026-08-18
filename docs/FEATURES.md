# RP2040 Audio RGB — Feature Matrix

This document maps the original 40-point v1 scope to the implementation in the repository.

| # | Feature | Implementation |
|---:|---|---|
| 1 | Modern GUI | PySide6 dark desktop application |
| 2 | Dashboard | Device, audio, performance, RGB and log cards |
| 3 | System Audio / Microphone | Switchable WASAPI loopback and input capture |
| 4 | Audio device selector | Enumerates PyAudioWPatch devices |
| 5 | Spectrum Analyzer | 32-bar live FFT widget |
| 6 | Music Reactive | Real-time FFT → RGB engine |
| 7 | Bass Pulse | Dedicated bass/beat effect |
| 8 | Spectrum Color | Bass/Mid/High weighted colors |
| 9 | Color Gradient | Frequency-weighted gradient effect |
| 10 | Beat Detection | Adaptive bass-energy detector |
| 11 | Static Color | Color picker + static mode |
| 12 | Breathing / Pulse / Rainbow | Built-in non-audio effects |
| 13 | Sensitivity | dB floor slider |
| 14 | Brightness | 1–100% master brightness |
| 15 | Attack / Release / Smoothness | Live controls |
| 16 | Bass/Mid/High Editor | Frequency, gain and color editor |
| 17 | Auto Gain | Adaptive noise-floor/level mapping |
| 18 | Presets | Gaming, EDM, Rock, Chill, Movie, Night |
| 19 | Custom profiles | Save current tuning as a preset |
| 20 | Profiles per application | Foreground `.exe` → preset mapping |
| 21 | Screen Ambient Mode | Two-zone screen capture |
| 22 | LED Test | Red/Green/Blue/White test buttons |
| 23 | Calibration Wizard | RGB order calibration UI |
| 24 | RP2040 Manager | Status, reconnect, firmware info and frame counter |
| 25 | Firmware Update | BOOTSEL `.uf2` copy manager |
| 26 | Protocol v2 | `PING`, `INFO`, `BRI`, `COUNT`, `OFF` + RGB frames |
| 27 | Auto reconnect | Serial device reconnect on failed writes |
| 28 | System Tray | Show, toggle LEDs, exit |
| 29 | Autostart with Windows | HKCU Run integration |
| 30 | Global Hotkeys | Toggle, next preset, brightness ± |
| 31 | Idle Mode | Off / breathing / rainbow / static |
| 32 | Night Mode | Scheduled brightness cap |
| 33 | Independent outputs | Mirror, complement or reverse-spectrum output #2 |
| 34 | WS2812 strip support | Firmware `COUNT 1..300` and multi-pixel output |
| 35 | Installer / Portable EXE | PyInstaller + Inno Setup build definitions |
| 36 | GitHub Releases / updater | Tag-driven release workflow + staged portable updater helper |
| 37 | Diagnostics | FPS, processing latency, dropped blocks, frame counter, log file |
| 38 | Low UI latency | Audio and screen capture run outside the GUI thread |
| 39 | No console window | PyInstaller `console=False` |
| 40 | Logo / icon | Project SVG application mark in `assets/icon.svg` |

## Notes

The desktop application is designed for Windows 10/11. Firmware v2 remains backward-compatible with the original `L R1 G1 B1 R2 G2 B2` frame command, so the GUI can still drive a board running the earlier sketch.

The SVG files under `docs/screenshots/` are **documentation UI previews**, not captured runtime screenshots. Real Windows screenshots should replace or supplement them after the first packaged build is run on the target PC.
