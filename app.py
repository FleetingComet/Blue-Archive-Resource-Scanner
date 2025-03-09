import time

from config import Config
from equipment import process_equipment
from goToLocation import (
    at_page,
    goHome,
    goToPage,
    whereAmI,
)
from item import process_items
from scanner import get_student_info, startMatching
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

    finished = mainpage(adb_controller)

    if not finished:
        print("⚠️ Matching process failed or was interrupted.")

    # Process Equipment
    process_equipment()
    # Process Items
    process_items()


def mainpage(adb_controller):
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

    # Determine the current screen
    current_screen = whereAmI(adb_controller)
    if current_screen is None:
        print("🔄 Current screen is None.")
        # If on a Page (and not Home), go Home.
        if at_page():
            print("🔄 The user is on certain page. Going home")
            goHome(adb_controller)
            time.sleep(10.0 * Config.WAIT_TIME_MULTIPLIER)
        current_screen = whereAmI(adb_controller)

    if current_screen in screen_mapping:
        _, grid_type = screen_mapping[current_screen]
        print(f"✅ Immediately processing {current_screen} screen.")
        process_screen(adb_controller, current_screen, grid_type)
        visited_screens.add(current_screen)
        # Update current_screen after processing
        current_screen = whereAmI(adb_controller)

    for screen_name, (menu_location, grid_type) in screen_mapping.items():
        # Skip if the screen has already been processed
        if screen_name in visited_screens:
            continue

        # Navigate to the target screen if not already there
        if current_screen != screen_name:
            # print(f"🔄 Navigating to {screen_name}...")
            # For Students and Student, they are not accessed via the Menu Tab.
            in_menu_tab = False if screen_name in ["Students", "Student"] else True

            navigate_to_screen(
                adb_controller, menu_location=menu_location, in_menu_tab=in_menu_tab
            )
            time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER)
            current_screen = whereAmI(adb_controller)

        # If navigation was successful, start the matching process
        if current_screen == screen_name:
            print(f"✅ Successfully navigated to {screen_name}.")
            process_screen(adb_controller, screen_name, grid_type)
            visited_screens.add(screen_name)
        else:
            print(f"⚠️ Failed to navigate to {screen_name}. Skipping...")

    # Verify that all screens were processed
    if len(visited_screens) == len(screen_mapping):
        print("🎉 Successfully processed all screens!")
        return True

    print("❌ Failed to process all screens.")
    return False


def process_screen(adb_controller, screen_name, grid_type):
    """
    Process a screen by starting the matching process or getting info,
    depending on the screen name.
    """
    if screen_name in ["Equipment", "Items"]:
        print(f"🔄 {screen_name}: Starting matching process...")
        startMatching(adb_controller, grid_type=grid_type)
    elif screen_name == "Students":
        print("🔄 Pressing First Student in the Student List.")
        navigate_to_screen(
            adb_controller, "first_student", in_menu_tab=False, ignore_page_check=True
        )
    elif screen_name == "Student":
        print("🔄 Getting Student Infos...")
        get_student_info(adb_controller)


def navigate_to_screen(
    adb_controller: ADBController,
    menu_location: str,
    in_menu_tab=True,
    ignore_page_check=False,
):
    """
    Navigate to a specific screen by ensuring you are at Home
    and opening the Menu Tab if required, then calling goToPage.

    Args:
        adb_controller (ADBController): An instance of ADBController.
        menu_location (str): The location to navigate to (e.g., "menu_items").
        in_menu_tab (bool): If it's needed to access the menu tab to navigate to (e.g., "menu_items").
    """
    if not ignore_page_check:
        if at_page():
            goHome(adb_controller)
            time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)

    # Ensure the Menu Tab is open
    # if not isMenuTabOpen(adb_controller):
    #     print("🔄 Opening Menu Tab...")
    #     press_MenuTab(adb_controller)
    #     time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER)

    # Navigate to the target location
    print(f"🔄 Navigating to {menu_location}...")
    time.sleep(2.0 * Config.WAIT_TIME_MULTIPLIER)
    goToPage(
        adb_controller=adb_controller, location=menu_location, in_menu_tab=in_menu_tab
    )
    time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER)


if __name__ == "__main__":
    main()
