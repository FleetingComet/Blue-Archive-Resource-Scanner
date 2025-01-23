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

    row = 0
    first_item_name = None

    while True:
        current_x = grid_start.x

        for col in range(cols_per_row):
            item_region = Region(
                current_x, current_y, item_size.width, item_size.height
            )

            # this will be screenshot on the emu or video record or what ever
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                return False

            image = cv2.imread(screenshot_path)

            # Ensure we don't go out of bounds
            if (
                item_region.bottom > image.shape[0]
                or item_region.right > image.shape[1]
            ):
                break

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
            item_name = searchOwned(screenshot_path, isName=True)
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
            # read data on the owned x
            owned_count = searchOwned(screenshot_path)
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

            # If this is the first column and row, update the first_item_name
            if col == 4 and row == 0:
                first_item_name = item_name

            # print(f"Matched: {item_name} - Owned: x{owned_count}")
            update_name_owned_counts(owned_counts_file, item_name, owned_count)

            # Move to the next column
            current_x += item_size.width

        row += 1
        # I want to improve the logic of this -_-
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
            row = 0
            time.sleep(1 * Config.WAIT_TIME_MULTIPLIER)

            if previous_first_item_name == first_item_name:
                print("No new items found. Stopping...")
                return True
            else:
                # Update previous_first_item_name for the next swipe
                previous_first_item_name = first_item_name


def swipe(adb_controller, swipe_distance, start_x, start_y, item_width):
    adb_controller.execute_command(
        f"shell input swipe {start_x + item_width} {swipe_distance} {start_x + item_width} {start_y} 500"
    )

    print("Scrolled down to load the next set of items.")


def searchOwned(image_path: str, isName: bool = False):
    """Extract owned count or name from a predetermined region."""
    if image_path is None:
        return None

    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if isName:
        predetermined_region = SearchPattern.EQUIPMENT_NAME.value
    else:
        predetermined_region = SearchPattern.EQUIPMENT_OWNED.value

    crop_img = image[
        predetermined_region.y : predetermined_region.bottom,
        predetermined_region.x : predetermined_region.right,
    ]

    preprocessed_crop = preprocess_image_for_ocr(crop_img)

    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, isName)
        return text.replace("\r", "").replace("\n", " ")
    return 0
