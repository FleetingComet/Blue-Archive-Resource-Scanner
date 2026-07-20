from locations.search import SearchPattern
from src.core.area import Region
from src.enums.ExtractionMode import ExtractionMode
from src.utils.ocr.color_util import (
    remove_non_white,
    retain_colors,
)
from src.utils.ocr.engine import extract_text, extract_text_talent
from src.utils.ocr.preprocessor import preprocess_image_for_ocr
from src.utils.ocr.star_util import count_blue_stars_adaptive, count_stars
from src.utils.ocr.text_util import get_tier_level, is_close_to


def crop_image(image, region: Region):
    """Crop the image to the specified region."""
    return image[region.y : region.bottom, region.x : region.right]


def extract_from_region(image, region: Region, mode: ExtractionMode = None):
    """
    Extract text from a specific region in the screenshot.

    Args:
        image: OpenCV image (a NumPy array).
        region (Region): The region to extract text from.
        mode (ExtractionMode): The type of image. Supported types include:
            - "number_in_circle": For numeric values inside a circle (like bond level).
            - "skill_level_indicator": For skill level indicators (e.g., "MAX").
            - "level_indicator" or "number": For level indicators or numbers.
            - "multi_line_name": For multi line text labels (e.g. Names on Equipment and Items).
            - "name" or "text": For text labels.
            - "gear": For gear tiers (e.g., "T9", "T7").
            - Otherwise, default processing is applied.

    Returns:
        str: The extracted text, or None if extraction fails.
    """

    crop_img = crop_image(image, region)

    if crop_img is None:
        return None

    # * Non OCR Counting (shape-based, not text-based)
    if mode == ExtractionMode.STAR:
        hex_colors = ["fee424"]
        cleaned, _ = retain_colors(crop_img, hex_colors, tolerance=20)
        return count_stars(cleaned)

    if mode == ExtractionMode.UE_STAR:
        return count_blue_stars_adaptive(crop_img, debug=False)

    processed_img = preprocess_image_for_ocr(crop_img, mode)

    if processed_img is None:
        return None

    if mode == ExtractionMode.TALENT:
        text = extract_text_talent(processed_img)
    else:
        text = extract_text(processed_img)

    if text is None:
        return None

    if mode == ExtractionMode.GEAR:
        return get_tier_level(text)

    if mode == ExtractionMode.SKILL_LEVEL and is_close_to(text, threshold=0.65):
        return "MAX"

    return (
        text.replace("\r", "")
        .replace("\n", " ")
        # for replacing left and right single quotes to '
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )


def extract_item_name(image, grid_type: str = "Equipment") -> str:
    """
    Extract the item name from a predetermined region in the screenshot.
    """
    pattern = (
        SearchPattern.EQUIPMENT_NAME.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM_NAME.value
    )
    return extract_from_region(
        image,
        pattern,
        mode=ExtractionMode.MULTI_LINE_NAME,
    )


def extract_owned_count(image_path: str, grid_type: str = "Equipment") -> str:
    """
    Extract the owned count from a predetermined region in the screenshot.
    """
    pattern = (
        SearchPattern.EQUIPMENT_OWNED.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM_OWNED.value
    )

    return extract_from_region(
        image_path,
        pattern,
    )
