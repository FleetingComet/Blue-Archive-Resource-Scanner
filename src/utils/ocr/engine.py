import re

import numpy as np

from rapidocr import LangRec, RapidOCR

# Lazy init to avoid slowing down scanner startup
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR(
            config_path="./rapidocr/config.yaml",
            # params={
            #     "Global.use_det": True,
            #     "Global.use_cls": True,
            #     "Rec.lang_type": LangRec.EN,
            # },
        )
    return _engine


def extract_text(image: np.ndarray) -> str:
    """Extracts text from an image using RapidOCR. Returns empty string if failed."""
    try:
        engine = get_engine()
        result = engine(image)

        # Handle the result object structure
        if result and hasattr(result, "txts") and result.txts:
            # Join multiple lines if detected, otherwise return single line
            return " ".join(result.txts).strip()
        return ""

    except Exception as e:
        print(f"[RapidOCR] Error: {e}")
        return ""


def extract_text_talent(image: np.ndarray) -> str:
    """SPECIAL: Extracts talent level."""
    try:
        engine = get_engine()
        result = engine(image)

        # Handle the result object structure
        if result and hasattr(result, "txts") and result.txts:
            # Join multiple lines if detected, otherwise return single line
            joined = "".join(result.txts).strip()
            return get_talent_level(joined)
        return ""

    except Exception as e:
        print(f"[RapidOCR] Error: {e}")
        return ""


def get_talent_level(text: str):
    """
    Extract the number after "Lv."

    Args:
        text (str): extract text from ocr

    Returns:
        _str_: stripped text
    """
    match = re.search(r"\[?\s*Lv\.?\s*(\d+)", text, re.IGNORECASE)
    return str(match.group(1)) if match else None
