from src.core.area import Location, Size
from src.core.game_area import GameAreaManager
from src.utils.device.adb.adb_controller import ADBController
from src.utils.device.interfaces import DeviceController


class ADBDevice(DeviceController):
    def __init__(self, host, port):
        self.adb = ADBController(host, port)
        self._manager = None

    def connect(self, retries=3):
        if not self.adb.connect(retries=retries):
            return False

        # Determine screen size by capturing one dummy screenshot
        img = self.adb.capture_screenshot()
        if img is None:
            return False

        h, w = img.shape[:2]

        self._manager = GameAreaManager(screen_size=Size(w, h))
        return True

    def capture_screenshot(self):
        return self.adb.capture_screenshot()

    def tap(self, x: int, y: int, duration_ms: int = 100):
        if self._manager is None:
            return False
        dx, dy = self._manager.script_to_device(x, y)
        return self.adb.execute_command(f"shell input tap {int(dx)} {int(dy)}")

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        if self._manager is None:
            return False

        dx1, dy1 = self._manager.script_to_device(x1, y1)
        dx2, dy2 = self._manager.script_to_device(x2, y2)

        return self.adb.execute_command(
            f"shell input swipe {dx1} {dy1} {dx2} {dy2} {duration_ms}"
        )
