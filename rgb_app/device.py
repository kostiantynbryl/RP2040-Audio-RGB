from __future__ import annotations

import threading
import time
import serial
from serial.tools import list_ports

RP2040_VID = 0x2E8A


class RP2040Device:
    def __init__(self, baud=115200):
        self.baud = baud
        self.ser = None
        self.port = None
        self.lock = threading.RLock()
        self.last_error = ""
        self.connected_since = 0.0
        self.frames = 0

    @staticmethod
    def ports():
        return list(list_ports.comports())

    @classmethod
    def find_port(cls):
        ports = cls.ports()
        for port in ports:
            if port.vid == RP2040_VID:
                return port.device
        for port in ports:
            text = f"{port.description} {port.manufacturer}".lower()
            if "rp2040" in text or "raspberry pi pico" in text:
                return port.device
        return None

    def connect(self, port=None):
        self.disconnect()
        self.port = port or self.find_port()
        if not self.port:
            self.last_error = "RP2040 not found"
            return False
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.15, write_timeout=0.15)
            time.sleep(0.25)
            self.connected_since = time.monotonic()
            self.last_error = ""
            return True
        except Exception as exc:
            self.ser = None
            self.last_error = str(exc)
            return False

    def disconnect(self):
        with self.lock:
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.ser = None

    @property
    def connected(self):
        return bool(self.ser and self.ser.is_open)

    def ensure_connected(self):
        return self.connected or self.connect()

    def send_frame(self, rgb1, rgb2=None):
        if rgb2 is None:
            rgb2 = rgb1
        if not self.ensure_connected():
            return False
        values = [max(0, min(255, int(v))) for v in (*rgb1, *rgb2)]
        line = "L " + " ".join(map(str, values)) + "\n"
        try:
            with self.lock:
                self.ser.write(line.encode("ascii"))
            self.frames += 1
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self.disconnect()
            return False

    def command(self, text, expect_reply=True):
        if not self.ensure_connected():
            return ""
        try:
            with self.lock:
                self.ser.reset_input_buffer()
                self.ser.write((text.strip() + "\n").encode("ascii"))
                if expect_reply:
                    return self.ser.readline().decode("utf-8", "replace").strip()
            return ""
        except Exception as exc:
            self.last_error = str(exc)
            self.disconnect()
            return ""

    def ping(self):
        return self.command("PING") == "PONG"

    def info(self):
        return self.command("INFO")

    def set_brightness(self, value):
        return self.command(f"BRI {int(value)}", False)

    def off(self):
        return self.command("OFF", False)
