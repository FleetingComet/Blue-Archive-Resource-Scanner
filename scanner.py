import time

from area import Location, Region, Size
from config import Config
from locations import screens
from locations.search import SearchPattern, StudentSearchPattern
from utils.data.jsonHelper import (
    map_student_data_to_character,
    update_character_data,
    update_name_owned_counts,
)
from utils.device.inputs.input_controller import InputController
from utils.device.swipe_utils import swipe_with_verification
from utils.ocr.extract import (
    extract_from_region,
    extract_item_name,
    extract_owned_count,
)
from utils.ocr.item_util import is_empty_slot

# from src.utils.item_util import is_item_empty


def startMatching(
    input_controller: InputController,
    grid_type: str = "Equipment",
    grid_config: dict = None,
) -> bool:
    """
    Capture a screenshot from the device and perform the ocr.
    Scan the item/equipment grid by iterating page by page, row by row, col by col.

    Flow per cell:
      1. Capture fresh grid screenshot (once per page, reused for all empty checks)
      2. If slot is empty -> end of inventory (items are always packed left-to-right)
      3. Click item -> detail panel updates (the left side)
      4. Capture detail screenshot
      5. Extract name + owned count
      6. update_name_owned_counts
    After all cols in a row -> advance to next row.
    After all rows in a page -> swipe.

    Termination:
      - First empty slot hit (items are contiguous, so empty = tail end)
      - swipe_with_verification returns False (no scroll = truly at end)

    Args:
        input_controller (InputController): Platform-agnostic input controller
        grid_type (str): "Equipment" or "Items".
        grid_config (dict): Grid configuration from screen_config.json
    Returns:
        bool: True if the process is completed, False otherwise.
    """

    config = (
        grid_config
        or {
            # Starting coordinates and dimensions
            "start_x": 701 if grid_type == "Items" else 690,
            "start_y": 160,
            "item_width": 110,
            "item_height": 90,
            "cols_per_row": 5,
            "y_padding": 11,  # the padding is 10 but I need extra 1px because some shenanigans are happening
            # equipment_grid_end_y = 660  # Y-end for equipment grid
            # items_grid_end_y = 560  # Y-end for items grid
            "end_y": 560 if grid_type == "Items" else 660,
            # Perform the swipe
            # "swipe_distance": 450,
            # "rows_per_page": 5 if grid_type == "Equipment" else 4,
        }
    )

    grid_start = Location(config["start_x"], config["start_y"])
    item_size = Size(config["item_width"], config["item_height"])
    cols_per_row = config["cols_per_row"]
    grid_end_y = config["end_y"]
    y_padding = config["y_padding"]
    stride_y = item_size.height + y_padding  # 101px per row

    rows_per_page = config.get(
        "rows_per_page",
        int((grid_end_y - grid_start.y) // stride_y),
    )

    # Auto-calculate swipe distance: exactly one full page scroll
    # Items: 4 rows × 101 = 404px  |  Equipment: 5 rows × 101 = 505px
    swipe_distance = config.get(
        "swipe_distance",
        rows_per_page * stride_y,
    )

    screen_number = 0

    while True:
        screen_number += 1
        print(f"\nScreen {screen_number}")

        # One clean grid screenshot per page — used only for empty-slot detection.
        # We capture a separate detail screenshot per tap for OCR.
        grid_image = input_controller.capture_screenshot()
        if grid_image is None:
            print("Failed to capture grid screenshot.")
            return False

        for row in range(rows_per_page):
            current_y = grid_start.y + row * stride_y
            found_item_in_row = False  # Track if we found any item in this row

            if current_y + item_size.height > grid_end_y:
                print(f"Row {row} exceeds grid end_y — stopping page early.")
                break

            for col in range(cols_per_row):
                current_x = grid_start.x + col * item_size.width

                if current_x + item_size.width > grid_image.shape[1]:
                    print(f"Col {col} exceeds image width — stopping row.")
                    break

                item_region = Region(
                    current_x,
                    current_y,
                    item_size.width,
                    item_size.height,
                )

                # Empty check
                # Items are always packed left-to-right, so the first empty
                # slot we encounter after seeing items in this row is the tail end.
                if is_empty_slot(grid_image, item_region):
                    if found_item_in_row:
                        # Empty slot after we've seen items in this row = end of inventory
                        print(
                            f"\n[screen={screen_number}, row={row}, col={col}] "
                            f"Empty slot after items - end of inventory."
                        )
                        return True
                    else:
                        # Empty at start of row (shouldn't happen per game logic), skip
                        continue

                found_item_in_row = True

                # Tap the item
                center = item_region.center
                print(f"Tapping ({int(center.x)}, {int(center.y)})")
                input_controller.tap(int(center.x), int(center.y))
                time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

                # Capture detail panel
                detail_image = input_controller.capture_screenshot()
                if detail_image is None:
                    print("Failed to capture detail screenshot.")
                    return False
                time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)

                # Extract
                item_name = extract_item_name(detail_image, grid_type=grid_type)
                time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
                owned_count = extract_owned_count(detail_image, grid_type=grid_type)

                # Persist
                if item_name and owned_count:
                    print(
                        f"[screen={screen_number}, row={row}, col={col}] "
                        f"{item_name} — x{owned_count}"
                    )
                    update_name_owned_counts(
                        Config.OWNED["counts"], item_name, owned_count
                    )
                else:
                    print(
                        f"[screen={screen_number}, row={row}, col={col}] "
                        f"Warning: extraction failed "
                        f"(name={item_name!r}, owned={owned_count!r})"
                    )

        # Swipe to next page
        print(f"Swiping {swipe_distance}px to next page...")
        if not swipe_with_verification(
            input_controller,
            swipe_distance,
            grid_start.x,
            grid_start.y,
            item_size.width,
        ):
            print("[Swipe] No movement detected — end of inventory.")
            return True

        time.sleep(2.5 * Config.WAIT_TIME_MULTIPLIER)


def get_student_info(input_controller: InputController) -> bool:
    first_name = None
    iteration = 0

    while True:
        iteration += 1

        image = input_controller.capture_screenshot()

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
        print("Current Data:", current_data)

        update_character_data(Config.OWNED["students"], name, current_data)

        if first_name is None:
            first_name = name
            print("First student name set to:", first_name)

        elif name == first_name:
            print("Encountered the first student again. Ending loop.")
            return True

        input_controller.tap(
            int(screens.StudentInfo.BUTTONS.NEXT.x),
            int(screens.StudentInfo.BUTTONS.NEXT.y),
        )

        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)


def get_currencies(input_controller: InputController) -> bool:
    image = input_controller.capture_screenshot()

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
