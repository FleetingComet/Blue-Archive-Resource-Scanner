from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class DeviceController(ABC):
    """Unified interface for Device Interaction (Capture + Input)"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        Captures the current screen on demand.

        Returns:
            np.ndarray: Screenshot image or None if failed
        """
        pass

    @abstractmethod
    def tap(self, x: int, y: int, duration_ms: int = 100) -> bool:
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
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> bool:
        """
        Swipe from start to end coordinates.

        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
            duration_ms: Duration of swipe in milliseconds

        Returns:
            bool: True if successful
        """
        pass
