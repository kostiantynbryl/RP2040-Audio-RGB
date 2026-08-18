# RP2040 Firmware

The repository now includes a configurable Arduino sketch:

- [`RP2040_Audio_RGB/RP2040_Audio_RGB.ino`](RP2040_Audio_RGB/RP2040_Audio_RGB.ino)

## What it does

The firmware exposes a USB serial port at **115200 baud** and accepts frames from the Windows client in this format:

```text
L R1 G1 B1 R2 G2 B2
```

Example:

```text
L 255 80 0 255 80 0
```

- `R1 G1 B1` controls a discrete PWM RGB LED or MOSFET-driven analog RGB output.
- `R2 G2 B2` controls a WS2812 / NeoPixel.
- A 3-second failsafe switches the LEDs off if valid frames stop arriving.

## Default pin configuration

The sketch currently ships with these defaults:

```cpp
PIN_RED      = 13
PIN_GREEN    = 14
PIN_BLUE     = 15
PIN_NEOPIXEL = 16
```

`GP16` matches the onboard WS2812 used by the Waveshare RP2040-Zero. If your external RGB LED is wired differently, edit the three PWM pin constants at the top of the sketch before flashing.

For a common-anode RGB LED set:

```cpp
RGB_COMMON_ANODE = true;
```

For a common-cathode LED leave it `false`.

## Arduino requirements

Install:

1. An Arduino RP2040-compatible board core.
2. **Adafruit NeoPixel** from Arduino Library Manager.

Open `RP2040_Audio_RGB.ino`, select your RP2040 board and USB port, then upload it.

## Serial protocol

See [`../docs/protocol.md`](../docs/protocol.md) for the host-side protocol specification.
