import numpy as np

from src.core.config import Config
from src.utils.data.student_skill_helper import get_talent_level
from src.utils.ocr.engine_factory import get_engine


def extract_text(image: np.ndarray) -> str:
    texts = get_engine(Config.OCR_ENGINE).extract(image)
    return " ".join(texts).strip()


def extract_text_talent(image: np.ndarray) -> str:
    texts = get_engine(Config.OCR_ENGINE).extract(image)
    return get_talent_level("".join(texts))
