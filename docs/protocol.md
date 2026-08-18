# Serial Protocol v2

RP2040 Audio RGB uses a newline-terminated ASCII protocol over USB CDC serial at **115200 baud**.

## RGB frame

```text
L R1 G1 B1 R2 G2 B2
```

Each channel is `0..255`. Output #1 is intended for the PWM RGB output; output #2 is the WS2812/NeoPixel channel.

Example:

```text
L 255 120 20 40 70 255
```

## Device discovery and health

```text
PING
```

Response:

```text
PONG
```

Firmware information:

```text
INFO
```

Example response:

```text
INFO RP2040-Audio-RGB 2.0.0 PIXELS=16 BRI=100
```

## Global firmware brightness

```text
BRI 0..100
```

The desktop application normally performs brightness scaling on the PC, but firmware-level brightness is available as a safety/power limit.

## WS2812 pixel count

```text
COUNT 1..300
```

The firmware resizes the NeoPixel buffer and applies output #2 to all configured pixels. This makes the same firmware usable with the onboard LED or an external strip.

## Immediate off

```text
OFF
```

The firmware also has a **3 second failsafe**: if valid RGB frames stop arriving, both outputs are switched off.

## Compatibility

The desktop application can still drive the original v1 firmware because the `L ...` frame format is unchanged. `PING`, `INFO`, `BRI`, and `COUNT` require firmware v2.

## Timing

Audio processing and the UI run independently from serial I/O. The host sends frames continuously while a reactive mode is active. Firmware code must avoid blocking delays so the USB receive buffer remains responsive.
