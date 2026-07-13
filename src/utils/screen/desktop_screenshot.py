import platform
import time
from threading import Lock, Thread
from typing import Any

from src.utils.device.window_capture import WindowCapture
from src.utils.device.window_capture_mss import WindowCaptureMSS
from src.utils.screen.screenshot_provider import ScreenshotProvider


class DesktopScreenCapture(ScreenshotProvider):
    def __init__(
        self, window_name=None, capture_interval=0.5, window_capture_backend=None
    ):
        # Allow external window_capture_backend to be passed (for sharing)
        if window_capture_backend is not None:
            self.window_capture_backend = window_capture_backend
        else:
            self.window_capture_backend = _get_window_capture_backend(window_name)
        self.capture_interval = capture_interval
        self.latest_screenshot = None
        self.lock = Lock()
        self.stopped = True
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stopped = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join()
            self.thread = None

    def run(self):
        while not self.stopped:
            img = self.window_capture_backend.get_screenshot()
            with self.lock:
                self.latest_screenshot = img
            time.sleep(self.capture_interval)

    def get_latest_screenshot(self, copy: bool = False):
        with self.lock:
            return (
                self.latest_screenshot.copy()
                if copy and self.latest_screenshot is not None
                else self.latest_screenshot
            )


def _get_window_capture_backend(window_name: str) -> Any:
    """Function that returns the right window capture backend."""
    if platform.system() == "Windows":
        return WindowCapture(window_name)
    else:
        return WindowCaptureMSS(window_name)
