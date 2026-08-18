# RP2040 Firmware v2

Arduino sketch:

```text
RP2040_Audio_RGB/RP2040_Audio_RGB.ino
```

The firmware exposes USB CDC serial at **115200 baud** and drives two logical outputs:

1. PWM analog RGB / MOSFET RGB output.
2. WS2812 / NeoPixel output with a configurable pixel count.

## Default pins

```cpp
PIN_RED      = 13
PIN_GREEN    = 14
PIN_BLUE     = 15
PIN_NEOPIXEL = 16
```

If the external RGB wiring differs, change the three PWM pin constants before compiling. Set `RGB_COMMON_ANODE = true` for a common-anode RGB LED.

## Arduino requirements

Install an Arduino RP2040 board core and **Adafruit NeoPixel** from Library Manager. Open the sketch, select the correct RP2040 board/port and upload.

## Protocol v2

```text
L R1 G1 B1 R2 G2 B2
PING
INFO
BRI 0..100
COUNT 1..300
OFF
```

`COUNT` resizes the NeoPixel buffer so the same firmware supports a single onboard WS2812 or an external strip. Output #2 is currently broadcast to every configured pixel.

The original `L ...` RGB frame remains unchanged, so firmware v2 is compatible with the legacy/headless PC client.

## Failsafe

If no valid RGB frame arrives for 3 seconds, both outputs are switched off. This prevents LEDs from remaining frozen at full brightness after a host crash or USB disconnect.

See [`../docs/protocol.md`](../docs/protocol.md) for the complete command reference.
