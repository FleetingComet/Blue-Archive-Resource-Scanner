from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class InputController(ABC):
    """
    Abstract interface for device input operations.
    Allows scanner.py and screen_navigator.py to work on both ADB and Desktop.
    """

    @abstractmethod
    def tap(self, x: int, y: int, duration_ms: int = 200) -> bool:
        """
        Tap at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration_ms: Duration of tap in milliseconds

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def swipe(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 200
    ) -> bool:
        """
        Swipe from start to end coordinates.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Duration of swipe in milliseconds

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        Capture current screen.

        Returns:
            np.ndarray: Screenshot image or None if failed
        """
        pass
