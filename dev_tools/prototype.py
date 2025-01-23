import os
import time

import cv2
import pytesseract

from locations.equipments import EquipmentPattern
from locations.search import SearchPattern
from matcher import create_region_from_match
from region import Region
from utils.adb_controller import ADBController
from utils.jsonHelper import update_owned_counts


def startMatching(
    patterns_dir,
    screenshots_dir,
    #   results_dir,
    owned_counts_file,
    adb_controller: ADBController,
    threshold=0.99,
):
    """
    Automates testing of image patterns against screenshots.

    Args:
        patterns_dir (str): Path to the directory containing patterns.
        screenshots_dir (str): Path to the directory containing screenshots.
        results_dir (str): Directory to save test results (visualizations/logs).
        threshold (float): Confidence threshold for template matching.
    """
    # Ensure results directory exists
    # os.makedirs(results_dir, exist_ok=True)
    # this will be screenshot on the emu or video record or what ever
    screenshot_path = os.path.join(screenshots_dir, "latest_screenshot.png")
    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return

    # !!TODO: this will be on while loop to check if the grid still have items to scroll down
    # I'm gonna implement scrolling soon so temporary name is scroll_down()
    # Load all patterns
    for category in EquipmentPattern:
        category_enum = category.value
        for tier, pattern_path in category_enum.__members__.items():
            pattern_file = os.path.join(patterns_dir, pattern_path.value)
            if not os.path.exists(pattern_file):
                print(f"Pattern file missing: {pattern_file}")
                continue

            print(f"\nTesting pattern: {category.name.lower()} {tier.lower()}")

            # Match template
            region: Region = create_region_from_match(
                pattern_file, screenshot_path, threshold
            )

            if region is None:
                print("Region not found")
                continue

            # click on region's center
            # this on adb but yeah temporary
            print(f"Clicking on region center: {region.center}")
            adb_controller.execute_command(
                f"shell input tap {int(region.center.x)} {int(region.center.y)}"
            )
            # screenshot the owned
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                return
            # read data on the left
            time.sleep(3)
            owned_count = searchOwned(screenshot_path)
            print(
                f"Matched: {category.name.lower()} {tier.lower()} - Owned: x{owned_count}"
            )

            update_owned_counts(
                owned_counts_file, category.name.lower(), tier.lower(), owned_count
            )


def extract_text(image: cv2.typing.MatLike) -> str:
    """Extract text from preprocessed image"""
    config = "--psm 6 -c tessedit_char_whitelist=0123456789"
    text: str = pytesseract.image_to_string(image, config=config)
    return text.strip()


def preprocess_image_for_ocr(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Noise removal
    denoised = cv2.fastNlMeansDenoising(binary, h=30)
    return denoised


def searchOwned(image_path: str):
    if image_path is None:
        return None
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    crop_img = image[
        SearchPattern.EQUIPMENT_OWNED.value.y : SearchPattern.EQUIPMENT_OWNED.value.bottom,
        SearchPattern.EQUIPMENT_OWNED.value.x : SearchPattern.EQUIPMENT_OWNED.value.right,
    ]
    preprocessed_crop = preprocess_image_for_ocr(crop_img)
    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop)
        return text
    return 0


if __name__ == "__main__":
    patterns_dir = "assets/equipments"
    screenshots_dir = "screenshots"
    owned_counts_file = "owned_counts.json"

    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    adb_controller = ADBController()
    if adb_controller.connect():
        startMatching(patterns_dir, screenshots_dir, owned_counts_file, adb_controller)
    else:
        print("Failed to connect to ADB. Exiting.")
