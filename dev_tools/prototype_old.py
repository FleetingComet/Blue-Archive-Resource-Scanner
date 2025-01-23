import os
import time

import cv2

from locations.search import SearchPattern
from utils.extract_text import extract_text
from utils.preprocess_image_for_ocr import preprocess_image_for_ocr
from utils.adb_controller import ADBController
from utils.jsonHelper import update_name_owned_counts
import utils




def startMatching(
    screenshots_dir,
    owned_counts_file,
    adb_controller: ADBController,
):
    # Ensure results directory exists
    # os.makedirs(results_dir, exist_ok=True)

    screenshot_path = os.path.join(screenshots_dir, "latest_screenshot.png")

    # Starting coordinates and dimensions
    start_x, start_y = 690, 160
    item_width, item_height = 110, 90  # 90
    cols_per_row = 5
    y_padding = 11  # 10

    count = 0
    current_y = start_y
    last_first_item = None
    current_first_item = None

    while True:
        current_x = start_x
        for col in range(cols_per_row):
            x_start = current_x
            y_start = current_y
            x_end = x_start + item_width
            y_end = y_start + item_height

            # this will be screenshot on the emu or video record or what ever
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                break
            image = cv2.imread(screenshot_path)

            # Ensure we don't go out of bounds
            if y_end > image.shape[0] or x_end > image.shape[1]:
                break

            center_w = round((x_start + x_end) / 2)
            center_h = round((y_start + y_end) / 2)

            print(f"Clicking on region center: ({center_w}, {center_h})")
            adb_controller.execute_command(
                f"shell input tap {int(center_w)} {int(center_h)}"
            )

            # screenshot
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                return
            
            time.sleep(0.5)

            # read data on the owned x
            owned_count = searchOwned(screenshot_path)
            item_name = searchOwned(screenshot_path, isName=True)

            print(f"Matched: {item_name} - Owned: x{owned_count}")
            
            if (col == 0 and count == 0):
                current_first_item = item_name

            update_name_owned_counts(owned_counts_file, item_name, owned_count)
            

            count += 1
            # Move to the next column
            current_x += item_width

        # Move to the next row
        current_y += item_height + y_padding
        
        if current_y + item_height > image.shape[0]:
            #qq
            first_item_x = start_x
            first_item_y = start_y
            
            center_w = round(first_item_x + item_width / 2)
            center_h = round(first_item_y + item_height / 2)
            
            print(f"Clicking first item of the final row at: ({center_w}, {center_h})")
            adb_controller.execute_command(f"shell input tap {int(center_w)} {int(center_h)}")
            
            if not adb_controller.capture_screenshot(screenshot_path):
                print("Failed to capture screenshot.")
                break
            
            last_first_item = searchOwned(screenshot_path, isName=True)
            print(f"Current first item of final row: {current_first_item}")
            print(f"First item of final row: {last_first_item}")
            
            if last_first_item == current_first_item:
                print("Reached the end of the list. Exiting.")
                break
            
            current_first_item = last_first_item
            
            swipe_distance = 490 + (item_height + y_padding)

            adb_controller.execute_command(
                f"shell input swipe {start_x + item_width} {swipe_distance} {start_x + item_width} {start_y} 500"
            )
            
            print("Scrolled down to load the next set of items.")
            time.sleep(2)
            current_y = start_y
            count = 0

def searchOwned(image_path: str, isName: bool = False):
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
        return text.replace('\r', '').replace('\n', ' ')
    return 0


if __name__ == "__main__":
    # patterns_dir = "assets/equipments"
    screenshots_dir = "screenshots"
    owned_counts_file = "owned_counts.json"

    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    adb_controller = ADBController()
    if adb_controller.connect():
        # startMatching(patterns_dir, screenshots_dir, owned_counts_file, adb_controller)
        startMatching(screenshots_dir, owned_counts_file, adb_controller)
    else:
        print("Failed to connect to ADB. Exiting.")
