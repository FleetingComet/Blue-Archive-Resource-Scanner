import time

from area import Location, Region, Size
from config import Config
import cv2

from src.locations.search import SearchPattern
from src.utils.extract_text import extract_text
from src.utils.preprocess_image_for_ocr import preprocess_image_for_ocr
from src.utils.adb_controller import ADBController
from src.utils.jsonHelper import update_name_owned_counts


def startMatching(adb_controller: ADBController) -> bool:
    """
    Capture a screenshot from the device and perform the ocr.

    Args:
        adb_controller (ADBController): An instance of ADBController to interact with the device.
    Returns:
        bool: True if the process is completed, False otherwise.
    """
    screenshot_path = Config.get_screenshot_path()
    owned_counts_file = Config.OWNED_COUNTS_FILE

    # Starting coordinates and dimensions
    # start_x, start_y = 690, 160
    grid_start = Location(690, 160)
    # item_width, item_height = 110, 90  # 90
    item_size = Size(110, 90)
    y_padding = 11  # the padding is 10 but I need extra 1px because some shenanigans are happening
    cols_per_row = 5

    current_y = grid_start.y
    previous_first_item_name = None

    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        if not adb_controller.capture_screenshot(screenshot_path):
            print("Failed to capture screenshot.")
            return False

        image = cv2.imread(screenshot_path)
        if image is None:
            print("Failed to read screenshot.")
            return False

        for col in range(cols_per_row):
            item_region = Region(
                grid_start.x + col * item_size.width,
                current_y,
                item_size.width,
                item_size.height,
            )

            # Ensure we don't go out of bounds
            if (
                item_region.bottom > image.shape[0]
                or item_region.right > image.shape[1]
            ):
                print("Reached the end of the screen.")
                return True

            center = item_region.center

            print(f"Clicking on region center: ({center.x}, {center.y})")
            adb_controller.execute_command(
                f"shell input tap {int(center.x)} {int(center.y)}"
            )

            # Capture the screen again after tapping
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                return False

            time.sleep(1 * Config.WAIT_TIME_MULTIPLIER)
            # read name
            item_name = extract_item_name(screenshot_path)
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
            # read data on the owned x
            owned_count = extract_owned_count(screenshot_path)
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

            if item_name and owned_count:
                # print(f"Matched: {item_name} - Owned: x{owned_count}")
                update_name_owned_counts(owned_counts_file, item_name, owned_count)
            else:
                print("Failed to extract item name or owned count.")

        first_item_name = extract_item_name(screenshot_path)
        if previous_first_item_name == first_item_name:
            print("No new items found. Stopping...")
            return True

        print(
            f"First Item: {first_item_name}, Previous Item: {previous_first_item_name}"
        )

        # Move to the next row
        current_y += item_size.height + y_padding
        if current_y + item_size.height > image.shape[0]:
            # Reset current_y for the next swipe
            current_y = grid_start.y

            # Perform the swipe
            # swipe_distance_y = start_y + (cols_per_row * (item_height + y_padding))
            # idk why scroll is different everytime
            swipe_distance_y = 490 + (item_size.height + y_padding)
            swipe(
                adb_controller,
                swipe_distance_y,
                grid_start.x,
                grid_start.y,
                item_size.width,
            )
            attempt += 1
            time.sleep(1 * Config.WAIT_TIME_MULTIPLIER)

    print("Reached maximum swipe attempts. Stopping...")
    return True


def swipe(
    adb_controller: ADBController,
    swipe_distance: int,
    start_x: int,
    start_y: int,
    item_width: int,
):
    """
    Perform a swipe gesture to scroll down the screen.

    Args:
        adb_controller (ADBController): An instance of ADBController.
        swipe_distance (int): The vertical distance to swipe.
        start_x (int): The starting x-coordinate.
        start_y (int): The starting y-coordinate.
        item_width (int): The width of an item in the grid.
    """
    adb_controller.execute_command(
        f"shell input swipe {start_x + item_width} {swipe_distance} {start_x + item_width} {start_y} 500"
    )

    print("Scrolled down to load the next set of items.")


def extract_item_name(image_path: str) -> str:
    """
    Extract the item name from a predetermined region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
    Returns:
        str: The extracted item name, or None if extraction fails.
    """
    return extract_from_region(
        image_path, SearchPattern.EQUIPMENT_NAME.value, is_name=True
    )


def extract_owned_count(image_path: str) -> str:
    """
    Extract the owned count from a predetermined region in the screenshot.

    Args:
        image_path (str): Path to the screenshot.
    Returns:
        str: The extracted owned count, or None if extraction fails.
    """
    return extract_from_region(
        image_path, SearchPattern.EQUIPMENT_OWNED.value, is_name=False
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
