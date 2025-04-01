import pytesseract

from area import Region
from src.locations.search import SearchPattern
from src.utils.color_util import (
    remove_colors,
    remove_non_white,
    retain_colors,
)
from src.utils.matchers import match_star, match_tier
from src.utils.preprocessor import preprocess_image_for_ocr
from src.utils.text_util import is_close_to


def extract_text(image, config="--psm 6 -c tessedit_char_whitelist=0123456789") -> str:
    """Extract text from preprocessed image"""

    # Trained data
    # config += r" --tessdata-dir ./tessdata -l BlueArchive"

    # print(f"Tesseract Config: {config}")

    text: str = pytesseract.image_to_string(image, config=config)
    return text.strip()


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

    if image_type == "gear":
        return match_tier(crop_img, grayscale=True)

    if image_type == "star":
        # hex_colors = ["FFD700"]
        # retained_image, mask = retain_colors(crop_img, hex_colors, tolerance=10)

        # cv2.imshow("Star", retained_image)
        # cv2.imshow("Original Star", crop_img)
        # cv2.waitKey(0)
        return match_star(crop_img)

    if image_type == "ue_star":
        hex_colors = ["e7f1f6", "e6f0f4"]
        crop_img, _ = remove_colors(crop_img, hex_colors, tolerance=5, black_bg=True)

        # cv2.imshow("ue_star", removed_color_image)
        # cv2.waitKey(0)
        # cv2.imwrite("ue_star.png", removed_color_image)
        return match_star(crop_img, blue=True)

    if image_type == "ue_level":
        # hex_colors = ["ffffff"]
        # crop_img, mask = retain_colors(crop_img, hex_colors, tolerance=5)
        crop_img = remove_non_white(crop_img)

    if image_type == "number_in_circle":
        hex_colors = ["3c4e66"]
        crop_img, _ = retain_colors(crop_img, hex_colors, tolerance=20)
        # crop_img, mask = retain_specific_color(crop_img, hex_color="3c4e66")

    preprocessed_crop, config = preprocess_image_for_ocr(
        crop_img, image_type=image_type
    )

    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, config=config)

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
