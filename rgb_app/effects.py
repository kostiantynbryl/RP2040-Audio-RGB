from __future__ import annotations

import colorsys
import math
import time
import numpy as np


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def scale(rgb, factor):
    return tuple(int(clamp(channel * factor, 0, 255)) for channel in rgb)


def mix(colors, weights):
    weights = np.array(weights, dtype=float)
    colors = np.array(colors, dtype=float)
    total = float(weights.sum()) or 1.0
    return tuple(np.clip((colors * weights[:, None]).sum(axis=0) / total, 0, 255).astype(int))


class EffectEngine:
    def __init__(self):
        self.phase = 0.0
        self.last = time.monotonic()

    def rainbow(self, speed=0.10):
        now = time.monotonic()
        self.phase = (self.phase + (now - self.last) * speed) % 1.0
        self.last = now
        return tuple(int(value * 255) for value in colorsys.hsv_to_rgb(self.phase, 1.0, 1.0))

    def breathing(self, color=(70, 90, 255), speed=1.2):
        value = 0.12 + 0.88 * (0.5 + 0.5 * math.sin(time.monotonic() * speed))
        return scale(color, value)

    def pulse(self, color=(255, 80, 20), speed=4.0):
        value = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(time.monotonic() * speed))
        return scale(color, value)

    def gradient(self, bands, level):
        rgb = mix(([255, 50, 5], [0, 255, 180], [100, 50, 255]), bands)
        return scale(rgb, 0.2 + 0.8 * level)

    def spectrum(self, bands, level, band_colors):
        return scale(mix(band_colors, bands), level)

    def bass_pulse(self, bands, level, beat, color=(255, 65, 5)):
        boost = 1.0 if beat else 0.35 + 0.65 * bands[0]
        return scale(color, clamp(level * boost))

    def render(self, mode, bands=(0.0, 0.0, 0.0), level=0.0, beat=False,
               band_colors=None, static_color=(90, 60, 255)):
        band_colors = band_colors or ([255, 72, 8], [0, 255, 170], [110, 60, 255])
        if mode == "static":
            return tuple(static_color)
        if mode == "breathing":
            return self.breathing(static_color)
        if mode == "rainbow":
            return self.rainbow()
        if mode == "pulse":
            return self.pulse(static_color)
        if mode == "bass_pulse":
            return self.bass_pulse(bands, level, beat, static_color)
        if mode == "gradient":
            return self.gradient(bands, level)
        return self.spectrum(bands, level, band_colors)
