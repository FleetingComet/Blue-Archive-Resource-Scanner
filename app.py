import time

from config import Config
from screen_navigator import ScreenNavigator
from screen_state import ScreenState
from utils.device.adb_controller import ADBController
from utils.data.equipment import EquipmentProcessor
from utils.data.item import ItemProcessor
from utils.data.student import StudentProcessor
from utils.device.adbscreencapture import ADBScreenCapture

from utils.sync.data_sync_manager import DataSyncManager


def main():
    path_init()
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


def path_init():
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    Config.OWNED_DIR.mkdir(parents=True, exist_ok=True)
    Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DataSyncManager().update_from_online()


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


if __name__ == "__main__":
    main()
