import logging

import numpy as np

from rapidocr import RapidOCR
from src.utils.ocr.engines.ocr_engine import OcrEngine

logger = logging.getLogger("BA-Scanner")


class RapidOcrEngine(OcrEngine):
    def __init__(self):
        self._engine = RapidOCR(
            config_path="./rapidocr/config.yaml",
            # params={
            #     "Global.use_det": True,
            #     "Global.use_cls": True,
            #     "Rec.lang_type": LangRec.EN,
            # },
        )

    def extract(self, image: np.ndarray) -> list[str]:
        """Extracts text from an image using RapidOCR. Returns empty string if failed."""

        try:
            result = self._engine(image)

            if not result or not result.txts:
                return []
            return result.txts

        except Exception:
            logger.exception("RapidOCR failed")
            return []
