# Serial Protocol

The Windows client communicates with the RP2040 over a USB CDC serial port at **115200 baud**.

## RGB update command

```text
L R1 G1 B1 R2 G2 B2\n
```

Where each color channel is an integer from `0` to `255`.

Example:

```text
L 255 120 20 255 120 20
```

This sets both RGB targets to the same orange color.

## Field meaning

| Field | Meaning |
|---|---|
| `L` | LED update command |
| `R1 G1 B1` | RGB target #1 |
| `R2 G2 B2` | RGB target #2 |

The current `led.py` mirrors one calculated color to both outputs, but the protocol already supports independent colors for two targets.

## Turn LEDs off

```text
L 0 0 0 0 0 0
```

The Python client sends this command when it exits normally.

## Firmware parser requirements

The RP2040 firmware should:

1. Read one newline-terminated ASCII command.
2. Check that the first token is `L`.
3. Parse six integer values.
4. Clamp every channel to `0..255`.
5. Update both RGB outputs.
6. Ignore malformed commands instead of blocking the main loop.

## Timing

The PC updates the color continuously based on the audio block size. The firmware should avoid long blocking delays so serial data can be consumed reliably.

## Future protocol extensions

Possible additions:

```text
B <brightness>
M <mode>
S <speed>
P <preset>
```

These commands are not implemented in the current Windows client yet.
