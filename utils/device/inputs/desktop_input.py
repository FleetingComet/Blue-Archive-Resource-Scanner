from utils.device.inputs.input_controller import InputController
from utils.device.window_capture import WindowCapture
from utils.device.inputs.desktop_controls import DesktopControls
import numpy as np


class DesktopInputController(InputController):
    def __init__(self, window_capture: WindowCapture):
        self.wc = window_capture
        self.controls = DesktopControls(window_capture)

    def tap(self, x: int, y: int, duration_ms: int = 200) -> bool:
        # Convert game coords to screen coords
        # screen_x = self.wc.region.x + x
        # screen_y = self.wc.region.y + y
        # region = self.wc.translate_from_base_resolution(base_region=Region())
        self.controls.tap_xy(x,  y, duration_ms=duration_ms / 1000)
        return True

    def swipe(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 200
    ) -> bool:
        from area import Location

        start = Location(start_x, start_y)
        end = Location(end_x, end_y)
        self.controls.swipe(start.x, start.y, end.x, end.y, duration_ms=duration_ms)
        return True

    def capture_screenshot(self) -> np.ndarray:
        return self.wc.get_screenshot().copy()
