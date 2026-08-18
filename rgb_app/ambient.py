from __future__ import annotations

import threading
import time
import numpy as np


class AmbientEngine:
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="AmbientEngine")
        self.thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        import mss

        with mss.mss() as capture:
            monitor = capture.monitors[1]
            while self.running:
                image = np.array(capture.grab(monitor))[:, :, :3][:, :, ::-1]
                height, width, _ = image.shape
                left = image[:, :width // 2].reshape(-1, 3).mean(axis=0)
                right = image[:, width // 2:].reshape(-1, 3).mean(axis=0)
                self.callback(tuple(left.astype(int)), tuple(right.astype(int)))
                time.sleep(0.05)
