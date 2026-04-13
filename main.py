import argparse

from config import Config
from screen_navigator import ScreenNavigator
from screen_state import ScreenState
from utils.data.equipment import EquipmentProcessor
from utils.data.item import ItemProcessor
from utils.data.student import StudentProcessor
from utils.screen.capture_backend import (
    get_adb_components,
    get_desktop_components,
)
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

    global sc

    # Create input controller based on platform
    if (
        Config.settings.target_platform == "emulator"
        or Config.settings.target_platform == "device"
    ):
        screencap, input_controller, adb_controller = get_adb_components()
        sc = screencap
        # device connected (not emu) example:
        # adb_controller = ADBController(host="192.168.254.156", port=5037)
        # Mumu Emulator is the default
        if not adb_controller.connect(retries=Config.ADB_RETRIES):
            print("❌ Failed to connect to ADB after multiple attempts.")
            print("Please check your ADB connection settings.")
            screencap.stop()
            exit(1)
    else:
        screencap, input_controller, wc = get_desktop_components()
        sc = screencap

    sc.start()

    navigator = ScreenNavigator(input_controller, screencap)

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
        if we're on a Page then a. go Home if that certain screen is finished, b. start immediately.
      - Then loop through each screen defined.
      - Skip already visited screens.
      - If not on the target screen, navigate to it.
        For "Students" and "Student", these are accessed without using the Menu Tab.
      - If navigation is successful, call the matching process (or get info).
    """
    screen_state = ScreenState(navigator)
    return screen_state.run()

if __name__ == "__main__":
    main()
