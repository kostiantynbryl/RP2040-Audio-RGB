# RP2040 Audio RGB

Real-time audio-reactive RGB lighting for RP2040 boards, driven from Windows system audio.

The PC captures the actual Windows playback stream through WASAPI loopback, performs FFT analysis, splits the signal into bass / mid / treble bands, converts them into RGB values, and sends the result to an RP2040 over USB serial.

## Features

- Windows system-audio capture via WASAPI loopback
- No microphone required
- Automatic RP2040 COM-port detection
- Real-time FFT analysis with three frequency bands
- Bass -> red / orange
- Mids -> green / cyan
- Treble -> blue / violet
- Attack / release smoothing for brightness
- Smooth RGB transitions
- Live terminal visualization of level, dB, dominant band and RGB output
- Serial protocol suitable for driving two synchronized RGB targets

## Signal path

```text
Windows audio
    |
    v
WASAPI loopback
    |
    v
FFT analysis
    |
    +--> Bass   35-250 Hz
    +--> Mid   250-2000 Hz
    +--> High 2000-10000 Hz
    |
    v
RGB mixer + smoothing
    |
    v
USB Serial @ 115200 baud
    |
    v
RP2040
    |
    +--> RGB output #1
    +--> RGB output #2
```

## Requirements

- Windows 10/11
- Python 3.10+
- RP2040 board with USB serial firmware compatible with the protocol below

Python packages:

```text
numpy
pyserial
PyAudioWPatch
```

## Installation

Clone the repository and install dependencies:

```bat
git clone https://github.com/kostiantynbryl/RP2040-Audio-RGB.git
cd RP2040-Audio-RGB
py -m pip install -r requirements.txt
```

Run:

```bat
py led.py
```

Expected startup output is similar to:

```text
RP2040 найден: COM5
SYSTEM AUDIO:
Устройство: Динамики (...) [Loopback]
Sample rate: 48000
Channels: 2

MUSIC MODE v3 / SYSTEM AUDIO
```

## Serial protocol

The current PC client sends one ASCII line per RGB update:

```text
L R1 G1 B1 R2 G2 B2\n
```

Example:

```text
L 255 90 10 255 90 10
```

The current client mirrors the same color to both RGB targets. This makes it possible to keep an onboard LED and an external RGB LED/strip synchronized.

See [`docs/protocol.md`](docs/protocol.md) for details.

## Audio mapping

| Band | Frequency | Main color |
|---|---:|---|
| Bass | 35-250 Hz | Red / Orange |
| Mid | 250-2000 Hz | Green / Cyan |
| Treble | 2000-10000 Hz | Blue / Violet |

The final RGB value is a weighted mix of all three bands rather than a hard switch, so transitions remain smooth.

## Main tuning parameters

Inside `led.py`:

```python
DB_MIN = -60.0
DB_MAX = -10.0
MAX_BRIGHTNESS = 1.0
LEVEL_ATTACK = 0.55
LEVEL_RELEASE = 0.12
COLOR_SMOOTH = 0.30
```

If the LEDs are almost always at maximum brightness, lower sensitivity by increasing `DB_MIN` or moving `DB_MAX` closer to 0 dB.

## Firmware

The PC side is ready to use with firmware that accepts the serial command format described above. Firmware source will live under `firmware/`.

The exact GPIO and LED-driver implementation depends on whether the target is:

- a discrete RGB LED,
- an addressable WS2812/NeoPixel,
- or a larger LED strip through external power switching / level shifting.

## Project status

Current stage: working Windows audio-reactive prototype with WASAPI loopback and synchronized dual RGB output.

Planned improvements:

- selectable visualization presets
- automatic gain control
- beat detection
- spectrum / VU modes
- tray application or GUI
- per-device audio source selection
- configurable serial protocol and LED count
- saved profiles

## License

MIT License. See [`LICENSE`](LICENSE).
