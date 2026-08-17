from src.utils.device.adb.adb_controller import ADBController
from src.utils.device.interfaces import DeviceController


class ADBDevice(DeviceController):
    def __init__(self, host, port):
        self.adb = ADBController(host, port)

    def connect(self, retries=3):
        return self.adb.connect(retries=retries)

    def capture_screenshot(self):
        return self.adb.capture_screenshot().copy()

    def tap(self, x: int, y: int, duration_ms: int = 100):
        return self.adb.execute_command(f"shell input tap {x} {y}")

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        return self.adb.execute_command(
            f"shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"
        )
