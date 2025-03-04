import time

import cv2

from area import Location, Region, Size
from config import Config
from src.utils.adb_controller import ADBController
from src.utils.extract_text import extract_item_name, extract_owned_count
from src.utils.jsonHelper import update_name_owned_counts
from src.utils.swipe_utils import swipe
# from src.utils.item_util import is_item_empty


def startMatching(adb_controller: ADBController, grid_type: str = "Equipment") -> bool:
    """
    Capture a screenshot from the device and perform the ocr.

    Args:
        adb_controller (ADBController): An instance of ADBController to interact with the device.
        grid_type (str): "Equipment" or "Items".
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
    # y_padding = 10
    cols_per_row = 5

    equipment_grid_end_y = 660  # Y-end for equipment grid
    items_grid_end_y = 560  # Y-end for items grid

    # Set the grid end based on the grid type
    grid_end_y = equipment_grid_end_y if grid_type == "Equipment" else items_grid_end_y

    current_y = grid_start.y
    # Track the first item in the first row
    row = 0
    previous_first_item_name = None
    first_item_name = None

    while True:
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

            # skip other items (for debugging)
            # if col > 0:
            #     continue

            # Ensure we don't go out of bounds
            if item_region.bottom > grid_end_y or item_region.right > image.shape[1]:
                print("Reached the end of the grid.")
                return True

            # # If region is empty, skip tapping/extracting until it finds a non-empty slot
            # if is_item_empty(image, item_region):
            #     print(f"Skipping empty slot at row {row}, col {col}.")
            #     continue

            center = item_region.center

            print(f"Clicking on region center: ({center.x}, {center.y})")
            adb_controller.execute_command(
                f"shell input tap {int(center.x)} {int(center.y)}"
            )

            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
            # Capture the screen again after tapping
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                return False

            # time.sleep(1 * Config.WAIT_TIME_MULTIPLIER)
            time.sleep(0.2 * Config.WAIT_TIME_MULTIPLIER)
            # read name
            item_name = extract_item_name(screenshot_path, grid_type=grid_type)

            if row == 0 and col == 0:
                first_item_name = item_name
                print(f"First Item: {first_item_name}")

                if (
                    item_name == previous_first_item_name
                    and previous_first_item_name is not None
                ):
                    print("No new items found. Stopping...")
                    return True

            time.sleep(0.2 * Config.WAIT_TIME_MULTIPLIER)
            # read data on the owned x
            owned_count = extract_owned_count(screenshot_path, grid_type=grid_type)
            # time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

            if item_name and owned_count:
                # print(f"Matched: {item_name} - Owned: x{owned_count}")
                update_name_owned_counts(owned_counts_file, item_name, owned_count)
            else:
                print("Failed to extract item name or owned count.")

        # Move to the next row
        current_y += item_size.height + y_padding
        row += 1
        if (test := current_y + item_size.height) > grid_end_y:
            print(f"current y: {test} image shape: {grid_end_y}")
            # Update the previous first item name
            previous_first_item_name = first_item_name
            print(f"Previous First Item: {previous_first_item_name}")

            # Reset current_y for the next swipe
            current_y = grid_start.y
            row = 0

            # Perform the swipe
            # swipe_distance_y = start_y + (cols_per_row * (item_height + y_padding))
            # idk why scroll is different everytime
            # swipe_distance_y = 490 + (item_size.height + y_padding)
            # swipe_distance_y = (grid_end_y - grid_start.y) - (y_padding * row)
            swipe_distance_y = (grid_end_y - grid_start.y) - y_padding
            swipe(
                adb_controller,
                swipe_distance_y,
                grid_start.x,
                grid_start.y,
                item_size.width,
            )

            # Wait for the screen to update after swiping
            time.sleep(2.5 * Config.WAIT_TIME_MULTIPLIER)
