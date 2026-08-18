from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass

import numpy as np
import pyaudiowpatch as pyaudio


@dataclass
class AudioFrame:
    level: float = 0.0
    db: float = -100.0
    bass: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    beat: bool = False
    fps: float = 0.0
    latency_ms: float = 0.0
    dropped: int = 0
    spectrum: tuple = ()


class AudioEngine:
    def __init__(self, settings, callback):
        self.settings = settings
        self.callback = callback
        self.running = False
        self.thread = None
        self.pa = None
        self.stream = None
        self.block = 2048
        self.smooth_level = 0.0
        self.noise_floor = settings.db_min
        self.beat_average = 0.05
        self.dropped = 0

    def list_devices(self):
        pa = pyaudio.PyAudio()
        result = []
        try:
            for index in range(pa.get_device_count()):
                device = pa.get_device_info_by_index(index)
                if device.get("maxInputChannels", 0) > 0 or device.get("isLoopbackDevice", False):
                    result.append((index, device["name"], int(device.get("defaultSampleRate", 48000)), bool(device.get("isLoopbackDevice", False))))
        finally:
            pa.terminate()
        return result

    def _device(self, pa):
        if self.settings.audio_device_index is not None:
            return pa.get_device_info_by_index(int(self.settings.audio_device_index))
        if self.settings.source_mode == "microphone":
            api = pa.get_default_host_api_info()
            return pa.get_device_info_by_index(api["defaultInputDevice"])
        return pa.get_default_wasapi_loopback()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="AudioEngine")
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _run(self):
        self.pa = pyaudio.PyAudio()
        try:
            device = self._device(self.pa)
            rate = int(device["defaultSampleRate"])
            channels = max(1, int(device["maxInputChannels"]))
            self.stream = self.pa.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True,
                                       input_device_index=int(device["index"]), frames_per_buffer=self.block)
            window = np.hanning(self.block)
            freqs = np.fft.rfftfreq(self.block, 1 / rate)
            frames = 0
            fps_started = time.monotonic()

            while self.running:
                started = time.perf_counter()
                try:
                    raw = self.stream.read(self.block, exception_on_overflow=False)
                except Exception:
                    self.dropped += 1
                    continue

                array = np.frombuffer(raw, np.int16)
                if channels > 1:
                    usable = (array.size // channels) * channels
                    array = array[:usable].reshape(-1, channels).astype(np.float32).mean(axis=1)
                else:
                    array = array.astype(np.float32)

                samples = array / 32768.0
                samples -= samples.mean()
                rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
                db = 20 * math.log10(max(rms, 1e-9))

                db_min = self.noise_floor if self.settings.auto_gain else self.settings.db_min
                if self.settings.auto_gain:
                    target_floor = min(-24.0, db - 28.0)
                    self.noise_floor = self.noise_floor * 0.995 + target_floor * 0.005
                    db_min = max(-80.0, min(-35.0, self.noise_floor))

                level = max(0.0, min(1.0, (db - db_min) / (self.settings.db_max - db_min))) ** 0.72
                smoothing = self.settings.attack if level > self.smooth_level else self.settings.release
                self.smooth_level += (level - self.smooth_level) * smoothing

                spectrum = np.abs(np.fft.rfft(samples * window))

                def get_band(name):
                    band = self.settings.bands[name]
                    mask = (freqs >= band.low) & (freqs < band.high)
                    return float(np.sqrt(np.mean(spectrum[mask] ** 2))) * band.gain if mask.any() else 0.0

                values = np.array([get_band("bass"), get_band("mid"), get_band("high")])
                peak = max(float(values.max()), 1e-9)
                bands = (values / peak) ** 0.65

                bass_energy = float(values[0])
                self.beat_average = self.beat_average * 0.93 + bass_energy * 0.07
                beat = bass_energy > self.beat_average * 1.55 and self.smooth_level > 0.12

                frames += 1
                now = time.monotonic()
                elapsed = now - fps_started
                fps = frames / elapsed if elapsed else 0.0
                if elapsed > 1.0:
                    frames = 0
                    fps_started = now

                buckets = np.array_split(spectrum[:min(len(spectrum), 500)], 32)
                bars = tuple(float(np.mean(bucket)) for bucket in buckets)
                bar_peak = max(bars) if bars else 1.0
                bars = tuple(value / bar_peak for value in bars)

                self.callback(AudioFrame(self.smooth_level, db, *map(float, bands), beat, fps,
                                         (time.perf_counter() - started) * 1000, self.dropped, bars))
        finally:
            try:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
            except Exception:
                pass
            if self.pa:
                self.pa.terminate()
