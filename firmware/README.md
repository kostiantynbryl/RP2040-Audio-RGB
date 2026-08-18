# RP2040 Firmware

This directory is reserved for the RP2040 firmware used by the project.

The current Windows client expects firmware that exposes a USB serial port and accepts commands in this format:

```text
L R1 G1 B1 R2 G2 B2
```

Example:

```text
L 255 80 0 255 80 0
```

For now, the exact firmware source is intentionally not included because the GPIO / LED implementation depends on the connected hardware:

- discrete common-anode/common-cathode RGB LED,
- onboard addressable RGB LED,
- WS2812 / NeoPixel,
- external RGB strip with MOSFET drivers,
- or a combination of two outputs.

When the hardware pinout is finalized, firmware can be added here without changing the Windows-side audio analyzer or serial protocol.

See [`../docs/protocol.md`](../docs/protocol.md) for the full command specification.
