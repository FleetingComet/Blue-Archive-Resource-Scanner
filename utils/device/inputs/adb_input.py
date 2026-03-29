from utils.device.inputs.input_controller import InputController
from utils.device.adb_controller import ADBController
import numpy as np


class ADBInputController(InputController):
    """ADB implementation of InputController"""

    def __init__(self, adb_controller: ADBController):
        self.adb = adb_controller

    def tap(self, x: int, y: int, duration_ms: int = 200) -> bool:
        return self.adb.execute_command(f"shell input tap {x} {y}")

    def swipe(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 200
    ) -> bool:
        return self.adb.execute_command(
            f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}"
        )

    def capture_screenshot(self) -> np.ndarray:
        return self.adb.capture_screenshot()
