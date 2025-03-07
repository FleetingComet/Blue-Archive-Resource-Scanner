import cv2
import pytesseract

from area import Region
from src.locations.search import SearchPattern
from src.utils.matchers import match_tier
from src.utils.preprocessor import preprocess_image_for_ocr
from src.utils.text_util import is_close_to_max


def extract_text(image, config="--psm 6 -c tessedit_char_whitelist=0123456789") -> str:
    """Extract text from preprocessed image"""

    # Trained data
    # config += r" --tessdata-dir ./tessdata -l BlueArchive"

    # print(f"Tesseract Config: {config}")
    text: str = pytesseract.image_to_string(image, config=config)
    return text.strip()


def extract_item_name(image_path: str, grid_type: str = "Equipment") -> str:
    """
    Extract the item name from a predetermined region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
    Returns:
        str: The extracted item name, or None if extraction fails.
    """
    return extract_from_region(
        image_path,
        SearchPattern.EQUIPMENT_NAME.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM_NAME.value,
        image_type=None,
    )


def extract_owned_count(image_path: str, grid_type: str = "Equipment") -> str:
    """
    Extract the owned count from a predetermined region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
    Returns:
        str: The extracted owned count, or None if extraction fails.
    """
    return extract_from_region(
        image_path,
        SearchPattern.EQUIPMENT_OWNED.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM_OWNED.value,
        image_type=None,
    )


def extract_from_region(image_path: str, region: Region, image_type=None, skill=False):
    """
    Extract text from a specific region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
        region (Region): The region to extract text from.

        soon
    Returns:
        str: The extracted text, or None if extraction fails.
    """

    if image_path is None:
        return None

    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None

    crop_img = image[region.y : region.bottom, region.x : region.right]

    if image_type == "gear":
        return match_tier(crop_img)

    preprocessed_crop, config = preprocess_image_for_ocr(
        crop_img, image_type=image_type
    )

    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, config=config)

        if skill:
            if is_close_to_max(text, threshold=0.65):
                return "MAX"

        return (
            text.replace("\r", "")
            .replace("\n", " ")
            # for replacing left and right single quotes to '
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )
    return None
