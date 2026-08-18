import math
import time

import numpy as np
import pyaudiowpatch as pyaudio
import serial
from serial.tools import list_ports


# ============================================================
# CONFIGURATION
# ============================================================

BAUD = 115200
BLOCK_SIZE = 2048

# Audio sensitivity in dBFS.
DB_MIN = -60.0
DB_MAX = -10.0

MAX_BRIGHTNESS = 1.0

# Brightness response.
LEVEL_ATTACK = 0.55
LEVEL_RELEASE = 0.12

# RGB smoothing.
COLOR_SMOOTH = 0.30

# Per-band gain.
BASS_GAIN = 1.30
MID_GAIN = 1.00
TREBLE_GAIN = 1.35

# Frequency bands in Hz.
BASS_RANGE = (35, 250)
MID_RANGE = (250, 2000)
TREBLE_RANGE = (2000, 10000)


# ============================================================
# HELPERS
# ============================================================


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))



def find_rp2040():
    ports = list(list_ports.comports())

    print("COM-порты:")

    for port in ports:
        print(
            f"  {port.device:<6} "
            f"{port.description} "
            f"VID={port.vid} PID={port.pid}"
        )

    # Raspberry Pi / RP2040 USB VID = 0x2E8A.
    for port in ports:
        if port.vid == 0x2E8A:
            return port.device

    # Fallback for custom USB descriptions.
    for port in ports:
        name = (port.description or "").upper()
        if "RP2040" in name or "USB SERIAL" in name:
            return port.device

    return None



def rms_to_level(rms):
    if rms <= 1e-10:
        return 0.0, -100.0

    db = 20.0 * math.log10(rms)
    level = (db - DB_MIN) / (DB_MAX - DB_MIN)
    level = clamp(level)

    # Raise quieter details slightly without hard clipping them.
    level = level**0.72

    return level, db



def band_strength(spectrum, freqs, low, high):
    mask = (freqs >= low) & (freqs < high)

    if not np.any(mask):
        return 0.0

    values = spectrum[mask]
    return float(np.sqrt(np.mean(values * values)))



def get_default_loopback_device(audio):
    """Return the WASAPI loopback device for the default Windows output."""

    # Preferred PyAudioWPatch helper.
    try:
        return audio.get_default_wasapi_loopback()
    except Exception:
        pass

    # Compatibility fallback for older PyAudioWPatch builds.
    wasapi_info = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
    output = audio.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if output.get("isLoopbackDevice", False):
        return output

    output_name = output["name"]

    for device in audio.get_loopback_device_info_generator():
        if output_name in device["name"]:
            return device

    raise RuntimeError(
        "WASAPI Loopback для устройства воспроизведения по умолчанию не найден"
    )


# ============================================================
# RP2040
# ============================================================


port = find_rp2040()

if not port:
    raise RuntimeError("RP2040 не найден")

print()
print(f"RP2040 найден: {port}")
print(f"Открываю {port}")

ser = serial.Serial(port, BAUD, timeout=0.1)

# Some RP2040 firmware resets when USB serial is opened.
time.sleep(1.0)


# ============================================================
# WINDOWS WASAPI LOOPBACK
# ============================================================


print()
print("Поиск системного аудио WASAPI...")

audio = pyaudio.PyAudio()

try:
    speakers = get_default_loopback_device(audio)
except Exception as exc:
    audio.terminate()
    ser.close()
    raise RuntimeError(f"Не удалось открыть WASAPI Loopback: {exc}") from exc


device_index = int(speakers["index"])
channels = int(speakers["maxInputChannels"])
sample_rate = int(speakers["defaultSampleRate"])

if channels < 1:
    audio.terminate()
    ser.close()
    raise RuntimeError("Loopback-устройство не имеет входных каналов")

print()
print("SYSTEM AUDIO:")
print(f"Устройство: {speakers['name']}")
print(f"Device index: {device_index}")
print(f"Sample rate: {sample_rate}")
print(f"Channels: {channels}")


# ============================================================
# DSP / FFT
# ============================================================


window = np.hanning(BLOCK_SIZE).astype(np.float32)
freqs = np.fft.rfftfreq(BLOCK_SIZE, 1.0 / sample_rate)

smooth_level = 0.0
smooth_rgb = np.zeros(3, dtype=np.float32)



def send_rgb(rgb):
    r = int(clamp(float(rgb[0]), 0, 255))
    g = int(clamp(float(rgb[1]), 0, 255))
    b = int(clamp(float(rgb[2]), 0, 255))

    # Protocol: L R1 G1 B1 R2 G2 B2\n
    # Current mode mirrors the same color to both RGB targets.
    command = f"L {r} {g} {b} {r} {g} {b}\n"
    ser.write(command.encode("ascii"))

    return r, g, b


stream = audio.open(
    format=pyaudio.paInt16,
    channels=channels,
    rate=sample_rate,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=BLOCK_SIZE,
)

print()
print("========================================")
print("       MUSIC MODE v3 / SYSTEM AUDIO")
print("========================================")
print()
print("Источник   : звук Windows")
print("Микрофон   : НЕ используется")
print()
print("БАС        -> красный / оранжевый")
print("СЕРЕДИНА   -> зелёный / бирюзовый")
print("ВЫСОКИЕ    -> синий / фиолетовый")
print()
print("Ctrl+C = выход")
print()


# ============================================================
# MAIN LOOP
# ============================================================


try:
    while True:
        raw = stream.read(BLOCK_SIZE, exception_on_overflow=False)
        samples = np.frombuffer(raw, dtype=np.int16)

        # Multi-channel Windows mix -> mono for spectral analysis.
        if channels > 1:
            try:
                samples = samples.reshape(-1, channels)
                samples = np.mean(samples.astype(np.float32), axis=1)
            except ValueError:
                continue
        else:
            samples = samples.astype(np.float32)

        # int16 -> -1.0 ... +1.0
        samples /= 32768.0
        samples -= np.mean(samples)

        # ----------------------------------------------------
        # LOUDNESS
        # ----------------------------------------------------

        rms = float(np.sqrt(np.mean(samples * samples)))
        target_level, db = rms_to_level(rms)

        speed = LEVEL_ATTACK if target_level > smooth_level else LEVEL_RELEASE
        smooth_level += (target_level - smooth_level) * speed
        level = clamp(smooth_level)

        # ----------------------------------------------------
        # FFT
        # ----------------------------------------------------

        fft_data = np.fft.rfft(samples * window)
        spectrum = np.abs(fft_data)

        bass = band_strength(spectrum, freqs, *BASS_RANGE) * BASS_GAIN
        mid = band_strength(spectrum, freqs, *MID_RANGE) * MID_GAIN
        treble = band_strength(spectrum, freqs, *TREBLE_RANGE) * TREBLE_GAIN

        # Normalize the three bands relative to the strongest one.
        maximum = max(bass, mid, treble, 1e-10)

        bass_n = (bass / maximum) ** 0.65
        mid_n = (mid / maximum) ** 0.65
        treble_n = (treble / maximum) ** 0.65

        # ----------------------------------------------------
        # COLOR MIX
        # ----------------------------------------------------

        red = bass_n * 1.00 + mid_n * 0.10 + treble_n * 0.28
        green = bass_n * 0.34 + mid_n * 1.00 + treble_n * 0.10
        blue = bass_n * 0.03 + mid_n * 0.22 + treble_n * 1.00

        target_rgb = np.array([red, green, blue], dtype=np.float32)

        rgb_peak = float(np.max(target_rgb))
        if rgb_peak > 1.0:
            target_rgb /= rgb_peak

        brightness = level * 255.0 * MAX_BRIGHTNESS
        target_rgb *= brightness

        # True silence -> LEDs off.
        if level < 0.018:
            target_rgb[:] = 0

        smooth_rgb += (target_rgb - smooth_rgb) * COLOR_SMOOTH
        r, g, b = send_rgb(smooth_rgb)

        dominant = max(
            [
                ("BASS", bass_n),
                ("MID ", mid_n),
                ("HIGH", treble_n),
            ],
            key=lambda item: item[1],
        )[0]

        # ----------------------------------------------------
        # TERMINAL VISUALIZER
        # ----------------------------------------------------

        bar_length = 30
        filled = int(level * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(
            f"\r{bar} "
            f"level={level:4.2f} "
            f"{db:6.1f}dB "
            f"{dominant} "
            f"B={bass_n:.2f} "
            f"M={mid_n:.2f} "
            f"H={treble_n:.2f} "
            f"RGB=[{r:3},{g:3},{b:3}]",
            end="",
            flush=True,
        )

except KeyboardInterrupt:
    print()
    print("Выход...")

finally:
    try:
        ser.write(b"L 0 0 0 0 0 0\n")
        time.sleep(0.05)
    except Exception:
        pass

    try:
        stream.stop_stream()
        stream.close()
    except Exception:
        pass

    try:
        audio.terminate()
    except Exception:
        pass

    try:
        ser.close()
    except Exception:
        pass

    print("LED выключен.")
