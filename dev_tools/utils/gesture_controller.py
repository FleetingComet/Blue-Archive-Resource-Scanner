from typing import Tuple
import logging

from region import Size
from utils.adb_controller import ADBController


class GestureController:
    def __init__(self, screen_dimensions: Size):
        self.screen = screen_dimensions
        self.adb = ADBController()
        self.logger = logging.getLogger(__name__)

    def swipe(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        duration: int = 300,
    ) -> bool:
        """
        Perform a swipe gesture using relative coordinates (0-1).
        0.0 represents the left edge of the screen.
        1.0 represents the right edge of the screen.
        """
        start_x = int(start_pos[0] * self.screen.width)
        start_y = int(start_pos[1] * self.screen.height)
        end_x = int(end_pos[0] * self.screen.width)
        end_y = int(end_pos[1] * self.screen.height)

        command = f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
        return self.adb.execute_command(command)

    def scroll_down(self, distance_factor: float = 0.5) -> bool:
        """
        Scroll down by a relative distance (0-1).
        0.0 represents the left edge of the screen.
        1.0 represents the right edge of the screen.
        """
        start_pos = (0.8, 0.7)  # Start from 70% down the screen
        end_pos = (0.8, 0.7 - distance_factor)  # Scroll up by distance_factor
        return self.swipe(start_pos, end_pos)
