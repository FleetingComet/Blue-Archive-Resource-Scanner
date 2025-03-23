import time
import cv2
from config import Config
from src.locations import screens
from src.locations.search import StudentSearchPattern
from src.utils.adb_controller import ADBController
from src.utils.extract_text import extract_from_region
from src.utils.jsonHelper import map_student_data_to_character, update_character_data


def get_student_info(adb_controller: ADBController) -> bool:
    first_name = None
    iteration = 0

    while True:
        iteration += 1
        screenshot_path = Config.get_screenshot_path()

        if not adb_controller.capture_screenshot(screenshot_path):
            print("Failed to capture screenshot.")
            return False

        image = cv2.imread(screenshot_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            return False

        student_data = {
            "Name": extract_from_region(
                screenshot_path,
                StudentSearchPattern.STUDENT_NAME.value,
                image_type="name",
            ),
            "Level": extract_from_region(
                screenshot_path,
                StudentSearchPattern.LEVEL.value,
                image_type="level_indicator",
            ),
            "Bond Level": extract_from_region(
                screenshot_path,
                StudentSearchPattern.BOND_LEVEL.value,
                image_type="number_in_circle",
            ),
            "Rarity": extract_from_region(
                screenshot_path,
                StudentSearchPattern.STAR_QUANTITY.value,
                image_type="star",
            ),
            "Gear 1 Tier": extract_from_region(
                screenshot_path,
                StudentSearchPattern.GEAR_1_TIER.value,
                image_type="gear",
            ),
            "Gear 2 Tier": extract_from_region(
                screenshot_path,
                StudentSearchPattern.GEAR_2_TIER.value,
                image_type="gear",
            ),
            "Gear 3 Tier": extract_from_region(
                screenshot_path,
                StudentSearchPattern.GEAR_3_TIER.value,
                image_type="gear",
            ),
            "Gear Bond Tier": extract_from_region(
                screenshot_path,
                StudentSearchPattern.GEAR_BOND_TIER.value,
                image_type="gear",
            ),
            "Unique Equipment Star Quantity": extract_from_region(
                screenshot_path,
                StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value,
                image_type="ue_star",
            ),
            "Unique Equipment Level": extract_from_region(
                screenshot_path,
                StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value,
                image_type="ue_level",
            ),
            "Skill EX": extract_from_region(
                screenshot_path,
                StudentSearchPattern.SKILL_EX.value,
                image_type="skill_level_indicator",
            ),
            "Skill Basic": extract_from_region(
                screenshot_path,
                StudentSearchPattern.SKILL_BASIC.value,
                image_type="skill_level_indicator",
            ),
            "Skill Enhanced": extract_from_region(
                screenshot_path,
                StudentSearchPattern.SKILL_ENHANCED.value,
                image_type="skill_level_indicator",
            ),
            "Skill Sub": extract_from_region(
                screenshot_path,
                StudentSearchPattern.SKILL_SUB.value,
                image_type="skill_level_indicator",
            ),
        }

        name, current_data = map_student_data_to_character(student_data)
        print(f"\nIteration {iteration}")
        print("Character Name:", name)
        print("Current Data:", current_data)

        update_character_data(Config.OWNED["students"], name, current_data)

        if first_name is None:
            first_name = name
            print("First student name set to:", first_name)

        elif name == first_name:
            print("Encountered the first student again. Ending loop.")
            # break

        adb_controller.execute_command(
            f"shell input tap {int(screens.StudentInfo.BUTTONS.NEXT.x)} {int(screens.StudentInfo.BUTTONS.NEXT.y)}"
        )
        # time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)


def main():
    adb_controller = ADBController(host="127.0.0.1", port=Config.ADB_PORT)
    # adb_controller = ADBController()
    # adb_controller = ADBController(host="localhost", port=Config.ADB_PORT)

    get_student_info(adb_controller)


if __name__ == "__main__":
    main()
