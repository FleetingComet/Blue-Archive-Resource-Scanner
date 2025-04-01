import time

from area import Location, Region, Size
from config import Config
from src.locations import screens
from src.locations.search import SearchPattern, StudentSearchPattern
from utils.device.adb_controller import ADBController
from utils.ocr.extract import (
    extract_from_region,
    extract_item_name,
    extract_owned_count,
)
from src.utils.jsonHelper import (
    map_student_data_to_character,
    update_character_data,
    update_name_owned_counts,
)
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
        image = adb_controller.capture_screenshot()
        if image is None:
            print("Failed to capture screenshot.")
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
            image = adb_controller.capture_screenshot()
            if image is None:
                print("Failed to capture screenshot.")
                return False

            # time.sleep(1 * Config.WAIT_TIME_MULTIPLIER)
            time.sleep(0.2 * Config.WAIT_TIME_MULTIPLIER)
            # read name
            item_name = extract_item_name(image, grid_type=grid_type)

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
            owned_count = extract_owned_count(image, grid_type=grid_type)
            # time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

            if item_name and owned_count:
                # print(f"Matched: {item_name} - Owned: x{owned_count}")
                update_name_owned_counts(Config.OWNED["counts"], item_name, owned_count)
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


def get_student_info(adb_controller: ADBController) -> bool:
    first_name = None
    iteration = 0

    while True:
        iteration += 1

        image = adb_controller.capture_screenshot()

        if image is None:
            return False

        student_data = {
            "Name": extract_from_region(
                image,
                StudentSearchPattern.STUDENT_NAME.value,
                image_type="name",
            ),
            "Level": extract_from_region(
                image,
                StudentSearchPattern.LEVEL.value,
                image_type="level_indicator",
            ),
            "Bond Level": extract_from_region(
                image,
                StudentSearchPattern.BOND_LEVEL.value,
                image_type="number_in_circle",
            ),
            "Rarity": extract_from_region(
                image,
                StudentSearchPattern.STAR_QUANTITY.value,
                image_type="star",
            ),
            "Gear 1 Tier": extract_from_region(
                image,
                StudentSearchPattern.GEAR_1_TIER.value,
                image_type="gear",
            ),
            "Gear 2 Tier": extract_from_region(
                image,
                StudentSearchPattern.GEAR_2_TIER.value,
                image_type="gear",
            ),
            "Gear 3 Tier": extract_from_region(
                image,
                StudentSearchPattern.GEAR_3_TIER.value,
                image_type="gear",
            ),
            "Gear Bond Tier": extract_from_region(
                image,
                StudentSearchPattern.GEAR_BOND_TIER.value,
                image_type="gear",
            ),
            "Unique Equipment Star Quantity": extract_from_region(
                image,
                StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value,
                image_type="ue_star",
            ),
            "Unique Equipment Level": extract_from_region(
                image,
                StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value,
                image_type="ue_level",
            ),
            "Skill EX": extract_from_region(
                image,
                StudentSearchPattern.SKILL_EX.value,
                image_type="skill_level_indicator",
            ),
            "Skill Basic": extract_from_region(
                image,
                StudentSearchPattern.SKILL_BASIC.value,
                image_type="skill_level_indicator",
            ),
            "Skill Enhanced": extract_from_region(
                image,
                StudentSearchPattern.SKILL_ENHANCED.value,
                image_type="skill_level_indicator",
            ),
            "Skill Sub": extract_from_region(
                image,
                StudentSearchPattern.SKILL_SUB.value,
                image_type="skill_level_indicator",
            ),
        }

        name, current_data = map_student_data_to_character(student_data)
        print(f"Student {iteration}")
        print("Character Name:", name)
        # print("Current Data:", current_data)

        update_character_data(Config.OWNED["students"], name, current_data)

        if first_name is None:
            first_name = name
            print("First student name set to:", first_name)

        elif name == first_name:
            print("Encountered the first student again. Ending loop.")
            return True

        adb_controller.execute_command(
            f"shell input tap {int(screens.StudentInfo.BUTTONS.NEXT.x)} {int(screens.StudentInfo.BUTTONS.NEXT.y)}"
        )
        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)


def get_currencies(adb_controller: ADBController) -> bool:
    image = adb_controller.capture_screenshot()

    if image is None:
        return False

    currencies = [SearchPattern.AP, SearchPattern.CREDIT, SearchPattern.PYROXENE]
    owned_currencies_file = Config.OWNED["currencies"]

    for currency in currencies:
        how_many = extract_from_region(
            image, currency.value, image_type="level_indicator"
        )  # reuse
        print(f"Currency {currency.name}: {how_many}")
        if currency.name == "AP":
            AP = how_many.split("/", 1)
            AP = {"Remaining": AP[0], "Max": AP[-1]}
            update_name_owned_counts(owned_currencies_file, currency.name.title(), AP)
        else:
            update_name_owned_counts(
                owned_currencies_file, currency.name.title(), how_many
            )
