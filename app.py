import time

from config import Config
from screen_navigator import ScreenNavigator
from scanner import get_currencies, get_student_info, startMatching
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
    # Define mapping of screen names to their corresponding menu locations and grid types
    screen_mapping = {
        "Equipment": ("menu_equipment", "Equipment"),
        "Items": ("menu_items", "Items"),
        "Students": ("menu_students", "Students"),
        "Student": ("first_student", "Student"),
    }
    # Track visited screens to ensure all are processed
    visited_screens = set()
    unvisited = list(screen_mapping.keys())

    # # get AP, Pyrox, Credits
    # get_currencies(navigator.adb_controller)

    def safe_go_home():
        if navigator.at_page():
            print("🔄 Detected at a page. Going home...")
            navigator.go_home()
            time.sleep(10.0 * Config.WAIT_TIME_MULTIPLIER)

    # Detect current screen and process immediately if it's valid
    current_screen = navigator.where_am_i()
    if current_screen in screen_mapping:
        _, grid_type = screen_mapping[current_screen]
        print(f"✅ Currently at {current_screen}. Starting processing immediately.")
        process_screen(navigator, current_screen, grid_type)
        visited_screens.add(current_screen)
        unvisited.remove(current_screen)
        if current_screen == "Students":
            # After tapping first student, It's on Student page
            current_screen = "Student"
            if current_screen not in visited_screens:
                process_screen(navigator, current_screen, None)
                visited_screens.add(current_screen)
                unvisited.remove(current_screen)
    else:
        print(f"🔄 Not at a valid screen. Current screen: {current_screen}. Going home...")
        safe_go_home()
        current_screen = navigator.where_am_i()

    for screen_name, (menu_location, grid_type) in screen_mapping.items():
        # Skip if the screen has already been processed
        if screen_name in visited_screens:
            continue
        # Navigate to the target screen if not already there
        # For Students and Student, they are not accessed via the Menu Tab.
        is_menu_free = screen_name in ["Students", "Student"]
        if is_menu_free:
            print(f"📴 {screen_name} is accessed via Menu Tab. Ensuring menu is closed.")
            safe_go_home()
        else:
            navigator.manage_menu_tab(True)

        print(f"🔄 Navigating to {screen_name}...")
        navigate_to_screen(
            navigator,
            menu_location=menu_location,
            in_menu_tab=(not is_menu_free),
            ignore_page_check=is_menu_free,
        )

        time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER)
        current_screen = navigator.where_am_i()

        # If navigation was successful, start the matching process
        if current_screen == screen_name:
            print(f"✅ Successfully navigated to {screen_name}. Processing...")
            process_screen(navigator, screen_name, grid_type)
            visited_screens.add(screen_name)
            if screen_name == "Students":
                # After tapping first student, It's on Student page
                current_screen = "Student"
                if current_screen not in visited_screens:
                    process_screen(navigator, current_screen, screen_mapping[current_screen][1])
                    visited_screens.add(current_screen)
                    unvisited.remove(current_screen)
        else:
            print(f"⚠️ Failed to navigate to {screen_name}. Skipping...")

    # Verify that all screens were processed
    if not unvisited:
        print("🎉 Successfully processed all screens!")
        return True
    else:
        print(f"❌ Not all screens processed. Missing: {unvisited}")
        return False



def process_screen(navigator: ScreenNavigator, screen_name, grid_type):
    """
    Process a screen by starting the matching process or getting info,
    depending on the screen name.
    """
    if screen_name in ["Equipment", "Items"]:
        print(f"🔄 {screen_name}: Starting matching process...")
        startMatching(navigator.adb_controller, grid_type=grid_type)
    elif screen_name == "Students":
        print("🔄 Pressing First Student in the Student List.")
        navigate_to_screen(
            navigator, "first_student", in_menu_tab=False, ignore_page_check=True
        )
    elif screen_name == "Student":
        print("🔄 Getting Student Infos...")
        get_student_info(navigator.adb_controller)


def navigate_to_screen(
    navigator: ScreenNavigator,
    menu_location: str,
    in_menu_tab=True,
    ignore_page_check=False,
):
    """
    Navigate to a specific screen by ensuring you are at Home
    and opening the Menu Tab if required, then calling go_to_page.

    Args:
        navigator (ScreenNavigator): An instance of ScreenNavigator.
        menu_location (str): The location to navigate to (e.g., "menu_items").
        in_menu_tab (bool): If it's needed to access the menu tab to navigate to (e.g., "menu_items").
    """
    if not ignore_page_check:
        if navigator.at_page():
            navigator.go_home()
            time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)
    # Navigate to the target location
    print(f"🔄 Navigating to {menu_location}...")
    time.sleep(2.0 * Config.WAIT_TIME_MULTIPLIER)
    navigator.go_to_page(location=menu_location, in_menu_tab=in_menu_tab)
    time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)


if __name__ == "__main__":
    main()
