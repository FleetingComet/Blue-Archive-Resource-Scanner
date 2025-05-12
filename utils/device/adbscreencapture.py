from threading import Lock, Thread
import time
from utils.device.adb_controller import ADBController


class ADBScreenCapture:
    """
    Real-time screenshot capture via ADB.
    It uses an ADBController instance to capture screenshots continuously in a separate thread.
    """

    def __init__(self, adb_controller: ADBController, capture_interval=0.5):
        self.adb = adb_controller
        self.capture_interval = capture_interval  # seconds between captures
        self.lock = Lock()
        self.latest_screenshot = None
        self.stopped = True
        self.thread = None

    def start(self):
        """Start the screenshot capture thread."""
        if self.thread is not None and self.thread.is_alive():
            return  # already running
        self.stopped = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the screenshot capture thread."""
        self.stopped = True
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def run(self):
        """Continuously capture screenshots using the ADBController."""
        while not self.stopped:
            img = self.adb.capture_screenshot()
            if img is not None:
                # If the image has an alpha channel, remove it.
                if img.ndim == 3 and img.shape[2] == 4:
                    img = img[:, :, :3]
                with self.lock:
                    # Only keep a reference to the latest screenshot (no .copy())
                    self.latest_screenshot = img
            time.sleep(self.capture_interval)
        # Small sleep to avoid busy-waiting if stopped
        time.sleep(0.01)

    def get_latest_screenshot(self, copy: bool = False):
        """
        Return the most recently captured screenshot.
        If copy=True, return a copy (for thread safety if caller will modify the image).
        """
        with self.lock:
            if self.latest_screenshot is not None:
                return self.latest_screenshot.copy() if copy else self.latest_screenshot
            else:
                return None