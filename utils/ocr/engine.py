import numpy as np
from rapidocr import LangRec, RapidOCR

# Lazy init to avoid slowing down scanner startup
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR(
            config_path="./rapidocr/config.yaml",
            params={
                "Global.text_score": 0.8,
                "Global.use_cls": False,
                "Global.use_det": False,  
                "Rec.lang_type": LangRec.EN,
            }
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
