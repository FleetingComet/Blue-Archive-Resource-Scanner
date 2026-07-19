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
from src.utils.ocr.text_util import is_close_to


def crop_image(image, region: Region):
    """Crop the image to the specified region."""
    return image[region.y : region.bottom, region.x : region.right]


def extract_from_region(image, region: Region, mode: ExtractionMode = None):
    """
    Extract text from a specific region in the screenshot.

    Steps:
      1. Crop the image to the specified region.
      2. Process the cropped image based on Extraction Mode.
      3. Preprocess the processed image for OCR.
      4. Extract and clean up the text.

    Args:
        image: OpenCV image (a NumPy array).
        region (Region): The region to extract text from.
        mode (ExtractionMode): The type of image. Supported types include:
            - "number_in_circle": For numeric values inside a circle (like bond level).
            - "skill_level_indicator": For skill level indicators (e.g., "MAX").
            - "level_indicator" or "number": For level indicators or numbers.
            - "multi_line_name": For multi line text labels (e.g. Names on Equipment and Items).
            - "name" or "text": For text labels.
            - Otherwise, default processing is applied.

    Returns:
        str: The extracted text, or None if extraction fails.
    """

    crop_img = crop_image(image, region)

    if crop_img is None:
        return None

    if mode == ExtractionMode.STAR:
        hex_colors = ["fee424"]
        cleaned, _ = retain_colors(crop_img, hex_colors, tolerance=20)
        return count_stars(cleaned)

    if mode == ExtractionMode.UE_STAR:
        return count_blue_stars_adaptive(crop_img, debug=False)

    if mode == ExtractionMode.UE_LEVEL:
        crop_img = remove_non_white(crop_img)

    if mode == ExtractionMode.BOND_LEVEL:
        hex_colors = ["3c4e66"]
        crop_img, _ = retain_colors(crop_img, hex_colors, tolerance=20)

    # preprocessed_crop = crop_img

    # if image_type != "gear" or image_type != "talent":
    #     preprocessed_crop = preprocess_image_for_ocr(crop_img, image_type=image_type)

    processed_img = preprocess_image_for_ocr(crop_img, mode)

    if processed_img is None:
        return None

    if mode == ExtractionMode.TALENT:
        text = extract_text_talent(processed_img)
    else:
        text = extract_text(processed_img)

    if text is None:
        return None

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
