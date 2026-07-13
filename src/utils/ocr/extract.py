from src.core.area import Region
from locations.search import SearchPattern
from src.utils.ocr.color_util import (
    remove_non_white,
    retain_colors,
)
from src.utils.ocr.engine import extract_text, extract_text_talent
from src.utils.ocr.matchers import match_star
from src.utils.ocr.preprocessor import preprocess_image_for_ocr
from src.utils.ocr.star_util import count_blue_stars_adaptive
from src.utils.ocr.text_util import is_close_to


def crop_image(image, region: Region):
    """Crop the image to the specified region."""
    return image[region.y : region.bottom, region.x : region.right]


def extract_from_region(image, region: Region, image_type=None):
    """
    Extract text from a specific region in the screenshot.

    Steps:
      1. Crop the image to the specified region.
      2. Process the cropped image based on image_type.
      3. Preprocess the processed image for OCR.
      4. Extract and clean up the text.

    Args:
        image: OpenCV image (a NumPy array).
        region (Region): The region to extract text from.
        image_type: blablbaba

    Returns:
        str: The extracted text, or None if extraction fails.
    """

    crop_img = crop_image(image, region)

    if crop_img is None:
        return None

    # if image_type == "gear":
    #     return match_tier(crop_img, grayscale=True)

    if image_type == "star":
        return match_star(crop_img)

    if image_type == "ue_star":
        return count_blue_stars_adaptive(crop_img, debug=False)

    if image_type == "ue_level":
        crop_img = remove_non_white(crop_img)

    if image_type == "number_in_circle":
        hex_colors = ["3c4e66"]
        crop_img, _ = retain_colors(crop_img, hex_colors, tolerance=20)

    preprocessed_crop = crop_img
    if image_type != "gear" or image_type != "talent":
        preprocessed_crop, config = preprocess_image_for_ocr(
            crop_img, image_type=image_type
        )

    if preprocessed_crop is not None:
        if image_type != "talent":
            text = extract_text(preprocessed_crop)
        else:
            text = extract_text_talent(preprocessed_crop)

        if text is None:
            return None

        if image_type == "skill_level_indicator" and is_close_to(text, threshold=0.65):
            return "MAX"

        return (
            text.replace("\r", "")
            .replace("\n", " ")
            # for replacing left and right single quotes to '
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )
    return None


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
        image_type="multi_line_name",
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
        image_type=None,
    )
