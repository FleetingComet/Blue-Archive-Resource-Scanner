import cv2
import pytesseract

from area import Region
from src.locations.search import SearchPattern
from src.utils.preprocessor import preprocess_image_for_ocr


def extract_text(image, isName: bool = False) -> str:
    """Extract text from preprocessed image"""
    if isName:
        #  ? for the FAQ Icon
        config = "--psm 6 tessedit_char_blacklist=?"
        # config = "--psm 7"  # single word 8, 7 for single line
    else:
        config = "--psm 6 -c tessedit_char_whitelist=0123456789"
        # config = "--psm 8 -c tessedit_char_whitelist=0123456789"
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
        isName=True,
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
        isName=False,
    )


def extract_from_region(image_path: str, region: Region, isName: bool = False):
    """
    Extract text from a specific region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
        region (Region): The region to extract text from.
        is_name (bool): Whether to extract a name (uses different OCR settings).
    Returns:
        str: The extracted text, or None if extraction fails.
    """
    if image_path is None:
        return None

    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None

    crop_img = image[region.y : region.bottom, region.x : region.right]

    preprocessed_crop = preprocess_image_for_ocr(crop_img)

    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, isName)
        return text.replace("\r", "").replace("\n", " ")
    return None
