import pyautogui

from src.core.area import Size
from src.core.game_area import GameAreaManager
from src.core.script_transform import SCRIPT
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
        )
        SCRIPT.set_manager(self._manager)
        return True

    def capture_screenshot(self):
        return self.wm.get_screenshot()

    def tap(self, x, y, _duration_ms=100):
        if self._manager is None:
            return False

        dx, dy = self._manager.script_to_device(x, y)

        # Add window position on monitor
        client = self.wm.get_client_region()
        monitor_x = client.x + dx
        monitor_y = client.y + dy

        pyautogui.click(monitor_x, monitor_y)
        return True

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        if self._manager is None:
            return False

        dx1, dy1 = self._manager.script_to_device(x1, y1)
        dx2, dy2 = self._manager.script_to_device(x2, y2)

        # Add window position on monitor
        client = self.wm.get_client_region()
        mon_x1, mon_y1 = client.x + dx1, client.y + dy1
        mon_x2, mon_y2 = client.x + dx2, client.y + dy2

        pyautogui.moveTo(mon_x1, mon_y1)
        pyautogui.dragTo(mon_x2, mon_y2, duration=duration_ms / 1000, button="left")
        return True
