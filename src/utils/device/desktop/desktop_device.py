import logging
import time

from src.utils.device.interfaces import DeviceController, DeviceUnavailableError

from .window_manager import (
    BASE_RES,
    FOCUS_WAIT_S,
    WindowManager,
    set_dpi_awareness,
    to_base_resolution,
)

set_dpi_awareness()  # Before pyautogui is imported, see set_dpi_awareness

import pyautogui  # noqa: E402

pyautogui.FAILSAFE = True

logger = logging.getLogger("BA-Scanner")


class DesktopDevice(DeviceController):
    def __init__(self, window_name="Blue Archive"):
        self.window_name = window_name
        self.wm: WindowManager | None = None
        self._size_checked = False

    def connect(self, retries=0):
        """Find the game window, there is nothing else to connect to."""
        try:
            self.wm = WindowManager(self.window_name)
        except RuntimeError as e:
            logger.error(e)
            return False
        return True

    def capture_screenshot(self):
        try:
            image = self.wm.get_screenshot()
        except DeviceUnavailableError:
            raise  # Game gone or never focused: stop rather than scan blank data
        except Exception as e:  # noqa: BLE001
            logger.error(f"Screenshot of '{self.window_name}' failed: {e}")
            return None

        self._check_window_size(image)
        return to_base_resolution(image)

    def _check_window_size(self, image):
        """Warn once about window sizes the 1280x720 search regions can't handle well."""
        if self._size_checked:
            return
        self._size_checked = True

        h, w = image.shape[:2]
        if abs(w / h - BASE_RES.width / BASE_RES.height) > 0.01:
            logger.warning(
                f"Game area is {w}x{h}, not 16:9. Set Screen Ratio to 16:9 in the game options."
            )
        if w < BASE_RES.width:
            logger.warning(
                f"Game area is {w}x{h}, smaller than 1280x720. OCR is less accurate when upscaled."
            )

    def _to_screen(self, x, y):
        """
        Screen point for a 1280x720 coordinate. Never returns a point another
        window would get the click on, waits instead (a toast, a popup).
        """
        deadline = time.monotonic() + FOCUS_WAIT_S
        warned = False
        while True:
            self.wm.activate()
            sx, sy = self.wm.scale_coords(x, y)
            if self.wm.owns_point(sx, sy):
                return sx, sy
            if time.monotonic() > deadline:
                raise DeviceUnavailableError(
                    f"'{self.window_name}' is covered or off-screen at ({sx}, {sy})."
                )
            if not warned:
                logger.warning(
                    f"'{self.window_name}' is covered or off-screen at ({sx}, {sy}), waiting."
                )
                warned = True
            time.sleep(0.5)

    def tap(self, x, y, duration_ms=100):
        sx, sy = self._to_screen(x, y)
        pyautogui.click(sx, sy)
        return True

    def swipe(self, x1, y1, x2, y2, duration_ms=500):
        sx1, sy1 = self._to_screen(x1, y1)
        sx2, sy2 = self._to_screen(x2, y2)
        pyautogui.moveTo(sx1, sy1)
        pyautogui.mouseDown()
        try:
            pyautogui.moveTo(sx2, sy2, duration=duration_ms / 1000)
        finally:
            pyautogui.mouseUp()
        return True
