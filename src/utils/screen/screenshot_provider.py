from abc import ABC, abstractmethod

import numpy as np


class ScreenshotProvider(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_latest_screenshot(self, copy: bool = False) -> np.ndarray:
        pass
