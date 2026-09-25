import pyautogui

from src.core.area import Location, Size
from src.core.game_area import GameAreaManager
from src.utils.device.desktop.window_manager import WindowManager
from src.utils.device.interfaces import DeviceController

pyautogui.FAILSAFE = True


class DesktopDevice(DeviceController):
    def __init__(self, window_name="Blue Archive"):
        self.wm = WindowManager(window_name)
        self._manager = None

    def connect(self, _retries=0):
        """Desktop doesn't need this so we return True"""
        client = self.wm.get_client_region()
        self._manager = GameAreaManager(
            screen_size=Size(client.width, client.height),
            window_pos=Location(client.x, client.y),
        )
        return True

    def capture_screenshot(self):
        return self.wm.get_screenshot()

    def tap(self, x, y, _duration_ms=100):
        if self._manager is None:
            return False

        dx, dy = self._manager.script_to_device(x, y)
        pyautogui.click(dx, dy)
        return True

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        if self._manager is None:
            return False
        # sx1, sy1 = self.wm.scale_coords(x1, y1)
        # sx2, sy2 = self.wm.scale_coords(x2, y2)
        # pyautogui.moveTo(sx1, sy1)
        # pyautogui.dragTo(sx2, sy2, duration=duration_ms / 1000, button="left")
        dx1, dy1 = self._manager.script_to_device(x1, y1)
        dx2, dy2 = self._manager.script_to_device(x2, y2)

        pyautogui.moveTo(dx1, dy1)
        pyautogui.dragTo(dx2, dy2, duration=duration_ms / 1000, button="left")
        return True
