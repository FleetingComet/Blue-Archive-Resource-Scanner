import argparse

from src.core.config import Config
from src.core.navigator import ScreenNavigator
from src.core.state import ScreenState
from src.utils.data.equipment import EquipmentProcessor
from src.utils.data.item import ItemProcessor
from src.utils.data.student import StudentProcessor
from src.utils.device.inputs.input_controller import InputController
from src.utils.screen.capture_backend import (
    get_adb_components,
    get_desktop_components,
)
from src.utils.sync.data_sync_manager import DataSyncManager


def run_post_processing(visited_screens):
    """
    Only runs processors if the corresponding screen
    was actually successfully scanned.
    """
    processor_map = {
        "Equipment": EquipmentProcessor,
        "Items": ItemProcessor,
        "Students": StudentProcessor,
    }

    for screen_name, ProcessorClass in processor_map.items():
        if screen_name in visited_screens:
            try:
                print(f"Post-processing {screen_name} data...")
                ProcessorClass().process()
            except Exception as e:
                print(f"Failed to process {screen_name}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline", action="store_true", help="Skip data sync and any network calls"
    )
    args = parser.parse_args()

    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Sync Data
    # Sync if CLI is NOT offline AND settings say Enable Sync is True
    if not args.offline and Config.settings.enable_sync:
        try:
            DataSyncManager().update_from_online()
        except Exception:
            pass

    global sc, input_c

    # Create input controller based on platform
    if (
        Config.settings.target_platform == "emulator"
        or Config.settings.target_platform == "device"
    ):
        screencap, input_controller, adb_controller = get_adb_components()
        sc = screencap
        input_c = input_controller
        # device connected (not emu) example:
        # adb_controller = ADBController(host="192.168.254.156", port=5037)
        # Mumu Emulator is the default
        if not adb_controller.connect(retries=Config.ADB_RETRIES):
            print("❌ Failed to connect to ADB after multiple attempts.")
            print("Please check your ADB connection settings.")
            screencap.stop()
            exit(1)
    else:
        print("Desktop mode selected.")
        screencap, input_controller, wc = get_desktop_components()
        sc = screencap
        input_c = input_controller

    sc.start()
    mainpage(input_c, sc)
    sc.stop()
    exit(1)


def mainpage(input_controller: InputController, screencap):
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
    navigator = ScreenNavigator(input_controller, screencap)
    state = ScreenState(navigator)
    finished = state.run()

    if finished:
        run_post_processing(state.visited)
    else:
        print("⚠️ Matching process failed or was interrupted.")


if __name__ == "__main__":
    main()
