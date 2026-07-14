import pyautogui
from src.utils.device.interfaces import DeviceController
from .window_manager import WindowManager

pyautogui.FAILSAFE = True

class DesktopDevice(DeviceController):
    def __init__(self, window_name="Blue Archive"):
        self.wm = WindowManager(window_name)

    def connect(self, retries=0):
        """Desktop doesn't need this so we return True"""
        return True

    def capture_screenshot(self):
        return self.wm.get_screenshot().copy()

    def tap(self, x, y, duration_ms=100):
        sx, sy = self.wm.scale_coords(x, y)
        pyautogui.click(sx, sy)
        return True

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        sx1, sy1 = self.wm.scale_coords(x1, y1)
        sx2, sy2 = self.wm.scale_coords(x2, y2)
        pyautogui.moveTo(sx1, sy1)
        pyautogui.dragTo(sx2, sy2, duration=duration_ms / 1000, button="left")
        return True
