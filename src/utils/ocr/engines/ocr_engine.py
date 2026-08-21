from abc import ABC, abstractmethod

import numpy as np


class OcrEngine(ABC):
    """Base interface for OCR backends."""

    @abstractmethod
    def extract(self, image: np.ndarray) -> list[str]:
        """Extract recognized text from an image."""
        raise NotImplementedError
