# User Guide

## 1. Install from source

```bat
git clone https://github.com/kostiantynbryl/RP2040-Audio-RGB.git
cd RP2040-Audio-RGB
setup.bat
run.bat
```

The GUI starts from `app.py`. `led.py` is retained as the legacy/headless prototype.

## 2. Connect RP2040

Plug the board into USB. The application searches for Raspberry Pi/RP2040 USB VID `0x2E8A` and reconnects when a serial write fails.

For firmware v2 the RP2040 tab can display firmware information, configure the WS2812 count and send device commands.

## 3. Reactive audio

Open **Reactive** and choose:

- `system` for Windows playback through WASAPI loopback;
- `microphone` for a physical recording device.

Select the audio device and a mode: Spectrum, Bass Pulse, Gradient, Static, Breathing, Pulse or Rainbow.

## 4. Tune the response

- **Sensitivity** controls the dB floor.
- **Brightness** controls the host-side output level.
- **Attack** changes how quickly brightness rises.
- **Release** changes how quickly it falls.
- **Smoothness** controls RGB transition speed.
- **Automatic gain** adapts to quiet and loud sources.

The Bass/Mid/High editor lets you change each frequency range, gain and color.

## 5. Presets

Built-in presets: Gaming, EDM, Rock, Chill, Movie and Night. Use **Save current as preset** to store custom tuning in `%APPDATA%`.

## 6. Application profiles

In **App Profiles**, map a foreground process such as `spotify.exe`, `chrome.exe` or a game executable to a preset. The application checks the foreground process and switches presets automatically.

## 7. Screen Ambient

Enable **Screen Ambient Mode** to bypass audio. The display is split into left and right halves:

- left average color → RGB output #1;
- right average color → RGB output #2.

## 8. RGB calibration

Use Red/Green/Blue tests in the RP2040 tab. If the physical channels are swapped, choose one of `RGB`, `RBG`, `GRB`, `GBR`, `BRG`, or `BGR`.

## 9. WS2812 strips

Firmware v2 accepts `COUNT 1..300`. Set the pixel count in the RP2040 tab. Output #2 is written to all configured pixels.

## 10. Firmware update

1. Hold BOOTSEL while connecting the RP2040 so Windows mounts the `RPI-RP2` drive.
2. Open the RP2040 tab.
3. Select **Flash firmware .UF2**.
4. Choose a compiled `.uf2` file.
5. The app copies it to the BOOTSEL drive; the board reboots automatically.

The Arduino source is under `firmware/RP2040_Audio_RGB/`.

## 11. Tray and hotkeys

Default global hotkeys:

```text
Ctrl+Alt+L       Toggle LEDs
Ctrl+Alt+P       Next preset
Ctrl+Alt+Up      Brightness +10%
Ctrl+Alt+Down    Brightness -10%
```

The tray menu can show the window, toggle LEDs or exit completely.

## 12. Night and idle modes

Night Mode limits brightness during the configured night window. Idle Mode changes to Off, Breathing, Rainbow or Static after audio activity stops.

## 13. Build the Windows app

Portable build:

```bat
build.bat
```

Outputs:

```text
dist\RP2040AudioRGB\RP2040AudioRGB.exe
dist\RP2040AudioRGB-portable.zip
```

For the installer, build the portable directory first and compile `installer.iss` with Inno Setup.

## 14. GitHub Releases

Pushing a tag matching `v*` triggers `.github/workflows/release.yml`, builds the portable ZIP and installer, and attaches them to a GitHub Release.

## 15. Diagnostics

Dashboard shows FFT spectrum, level, audio dB, beat state, processing FPS, processing latency, dropped audio blocks, RGB output and serial frame count. Persistent logs are stored in `%APPDATA%\RP2040-Audio-RGB\app.log`.
