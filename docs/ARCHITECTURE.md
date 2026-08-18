# Architecture

```text
Windows playback / microphone          Screen
            |                            |
            v                            v
     PyAudioWPatch                    MSS capture
            |                            |
            v                            v
      AudioEngine                   AmbientEngine
   FFT / AGC / beat                  two zones
            |                            |
            +------------+---------------+
                         v
                    MainWindow
                         |
                EffectEngine / presets
                         |
            +------------+------------+
            |                         |
            v                         v
       RGB output #1             RGB output #2
            |                         |
            +------------+------------+
                         v
                   RP2040Device
                         |
                 USB CDC 115200
                         |
                         v
                  RP2040 firmware v2
                 /                  \
        PWM analog RGB          WS2812 strip
```

## Modules

- `rgb_app/audio.py` — system/microphone capture, FFT, automatic gain, beat detection and diagnostics.
- `rgb_app/ambient.py` — screen capture worker and left/right color extraction.
- `rgb_app/effects.py` — reactive and autonomous color effects.
- `rgb_app/device.py` — COM discovery, reconnect and protocol transport.
- `rgb_app/config.py` — persisted configuration, frequency bands and presets.
- `rgb_app/windows.py` — foreground-app profiles, autostart, global hotkeys, BOOTSEL flashing and release updater helpers.
- `rgb_app/widgets.py` — dark UI styling and spectrum widget.
- `rgb_app/gui.py` — desktop UI and orchestration.

## Threading model

The PySide6 GUI remains on the Qt main thread. Audio capture/FFT and screen capture run in background worker threads. Results are passed back through Qt signals. This prevents the visual interface from blocking the audio loop and keeps serial frames responsive under normal UI activity.

## Configuration

User configuration is stored at:

```text
%APPDATA%\RP2040-Audio-RGB\config.json
```

Diagnostics are written to:

```text
%APPDATA%\RP2040-Audio-RGB\app.log
```

## Firmware compatibility

Protocol v2 extends the original RGB-frame protocol instead of replacing it. A legacy board can still receive RGB frames; status, brightness and pixel-count commands become available after flashing firmware v2.
