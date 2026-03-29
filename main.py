from config import Config
import argparse
from locations.search import StudentSearchPattern
from screen_navigator import ScreenNavigator
from screen_state import ScreenState
from utils.data.jsonHelper import map_student_data_to_character
from utils.device.adb_controller import ADBController
from utils.data.equipment import EquipmentProcessor
from utils.data.item import ItemProcessor
from utils.data.student import StudentProcessor
from utils.device.adbscreencapture import ADBScreenCapture

from utils.device.desktop_controls import DesktopControls
from utils.device.window_capture import WindowCapture
from utils.ocr.extract import extract_from_region
from utils.sync.data_sync_manager import DataSyncManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline", action="store_true", help="Skip data sync and any network calls"
    )
    args = parser.parse_args()

    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Sync Data
    # Sync if CLI is NOT offline AND settings say Enable Sync is True
    if not args.offline and Config.settings.offline_mode:
        try:
            DataSyncManager().update_from_online()
        except Exception:
            pass

    # Connect Device
    if Config.settings.target_platform == "desktop":
        print("Desktop mode selected.")
        desktop()
        return

    # device connected (not emu) example:
    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    # Mumu Emulator is the default
    adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
    screencap = ADBScreenCapture(adb_controller, Config.CAPTURE_INTERVAL)

    if not adb_controller.connect(retries=Config.ADB_RETRIES):
        print("❌ Failed to connect to ADB after multiple attempts.")
        print("Please check your ADB connection settings.")
        screencap.stop()
        exit(1)

    screencap.start()

    navigator = ScreenNavigator(adb_controller, screencap)

    finished = mainpage(navigator)

    if not finished:
        print("⚠️ Matching process failed or was interrupted.")
        screencap.stop()
        exit(1)

    # Process Equipment
    EquipmentProcessor().process()
    # Process Items
    ItemProcessor().process()
    # Process Students
    StudentProcessor().process()
    screencap.stop()


def mainpage(navigator: ScreenNavigator):
    """
    Handles navigation and starts the matching process.
    Logic:
      - If the current screen is None (meaning we're either on Home or on a Page),
        if we're on a Page then go Home.
      - Then loop through each screen defined.
      - Skip already visited screens.
      - If not on the target screen, navigate to it.
        For "Students" and "Student", these are accessed without using the Menu Tab.
      - If navigation is successful, call the matching process (or get info).
    """
    screen_state = ScreenState(navigator)
    return screen_state.run()


def desktop():
    """just temporary"""
    wc = WindowCapture("Blue Archive")
    # ctrl = DesktopControls(wc)
    image = wc.get_screenshot()
    student_data = {
        "Name": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.STUDENT_NAME.value),
            image_type="name",
        ),
        "Level": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.LEVEL.value),
            image_type="level_indicator",
        ),
        "Bond Level": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.BOND_LEVEL.value),
            image_type="number_in_circle",
        ),
        "Rarity": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.STAR_QUANTITY.value),
            image_type="star",
        ),
        "Gear 1 Tier": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.GEAR_1_TIER.value),
            image_type="gear",
        ),
        "Gear 2 Tier": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.GEAR_2_TIER.value),
            image_type="gear",
        ),
        "Gear 3 Tier": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.GEAR_3_TIER.value),
            image_type="gear",
        ),
        "Gear Bond Tier": extract_from_region(
            image,
            wc.translate_from_base_resolution(
                StudentSearchPattern.GEAR_BOND_TIER.value
            ),
            image_type="gear",
        ),
        "Unique Equipment Star Quantity": extract_from_region(
            image,
            wc.translate_from_base_resolution(
                StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value
            ),
            image_type="ue_star",
        ),
        "Unique Equipment Level": extract_from_region(
            image,
            wc.translate_from_base_resolution(
                StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value
            ),
            image_type="ue_level",
        ),
        "Skill EX": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.SKILL_EX.value),
            image_type="skill_level_indicator",
        ),
        "Skill Basic": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.SKILL_BASIC.value),
            image_type="skill_level_indicator",
        ),
        "Skill Enhanced": extract_from_region(
            image,
            wc.translate_from_base_resolution(
                StudentSearchPattern.SKILL_ENHANCED.value
            ),
            image_type="skill_level_indicator",
        ),
        "Skill Sub": extract_from_region(
            image,
            wc.translate_from_base_resolution(StudentSearchPattern.SKILL_SUB.value),
            image_type="skill_level_indicator",
        ),
    }

    name, current_data = map_student_data_to_character(student_data)
    print("Character Name:", name)
    print("Current Data:", current_data)


if __name__ == "__main__":
    main()
