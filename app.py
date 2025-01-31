import time

from config import Config
from equipment import process_equipment
from goToLocation import goHome, goToPage, isMenuTabOpen, press_MenuTab, whereAmI
from scanner import startMatching
from src.utils.adb_controller import ADBController


def main():
    # device connected (not emu) example:
    # adb_controller = ADBController(host="192.168.254.156", port=5037)
    # Mumu Emulator is the default
    # adb_controller = ADBController()
    adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)

    if not adb_controller.connect():
        print("❌ Failed to connect to ADB. Exiting.")
        exit(1)

    isFinished = mainpage(adb_controller)

    if not isFinished:
        print("⚠️ Matching process failed or was interrupted.")

    # Process Equipment
    process_equipment()


def mainpage(adb_controller):
    """Handles navigation and starts the matching process."""

    # Define mapping of screen names to their corresponding menu locations and grid types
    screen_mapping = {
        "Equipment": ("menu_equipment", "Equipment"),
        # "Items": ("menu_items", "Items"),
        # not yet implemented
        # "Students": ("menu_students", "Students"),
        # "Student": ("menu_student", "Student"),
    }

    # Track visited screens to ensure all are processed
    visited_screens = set()

    # Determine the current screen
    current_screen = whereAmI(adb_controller)

    # If the current screen is None, navigate to the home screen first
    if current_screen is None:
        print("🔄 Current screen is None. Navigating to Home...")
        goHome(adb_controller)
        time.sleep(10.0 * Config.WAIT_TIME_MULTIPLIER)
        current_screen = whereAmI(adb_controller)

    for screen_name, (menu_location, grid_type) in screen_mapping.items():
        # Skip if the screen has already been processed
        if screen_name in visited_screens:
            continue

        # Navigate to the target screen if not already there
        if current_screen != screen_name:
            print(f"🔄 Navigating to {screen_name}...")
            navigate_to_screen(adb_controller, menu_location)
            time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER)
            current_screen = whereAmI(adb_controller)

        # If navigation was successful, start the matching process
        if current_screen == screen_name:
            print(
                f"✅ Successfully navigated to {screen_name}. Starting matching process..."
            )
            startMatching(adb_controller, grid_type=grid_type)
            visited_screens.add(screen_name)
        else:
            print(f"⚠️ Failed to navigate to {screen_name}. Skipping...")

    # Verify that all screens were processed
    if len(visited_screens) == len(screen_mapping):
        print("🎉 Successfully processed all screens!")
        return True

    print("❌ Failed to process all screens.")
    return False


def navigate_to_screen(adb_controller: ADBController, menu_location: str):
    """
    Navigate to a specific screen by ensuring the Menu Tab is open first.

    Args:
        adb_controller (ADBController): An instance of ADBController.
        menu_location (str): The location to navigate to (e.g., "menu_items").
    """
    goHome(adb_controller)
    time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)

    # Ensure the Menu Tab is open
    if not isMenuTabOpen(adb_controller):
        print("🔄 Opening Menu Tab...")
        press_MenuTab(adb_controller)
        time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER)

    # Navigate to the target location
    print(f"🔄 Navigating to {menu_location}...")
    time.sleep(2.0 * Config.WAIT_TIME_MULTIPLIER)
    goToPage(adb_controller, menu_location)
    time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)


if __name__ == "__main__":
    main()
