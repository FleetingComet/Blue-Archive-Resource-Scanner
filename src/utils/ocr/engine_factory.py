from functools import cache

from src.utils.ocr.engines.ocr_engine import OcrEngine
from src.utils.ocr.engines.rapidocr import RapidOcrEngine


@cache
def get_engine(name: str = "rapidocr") -> OcrEngine:
    match name.lower():
        case "rapidocr":
            return RapidOcrEngine()

        case _:
            raise ValueError(f"Unsupported OCR engine: {name}")
