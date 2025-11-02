import json
import os
import time
from config import Config
from screen_navigator import ScreenNavigator
from scanner import get_currencies, get_student_info, startMatching


class ScreenState:
    """
    A state machine that manages screen navigation and triggers
    data collection/matching processes for each defined screen.
    """

    def __init__(self, navigator: ScreenNavigator, config_path=None):
        if config_path is None:
            config_path = os.path.join("config", "screen_config.json")

        self.navigator = navigator

        self.screen_mapping = self.load_config(config_path)

        self.visited = set()
        self.unvisited = set(self.screen_mapping.keys())

    def load_config(self, path: str) -> dict:
        with open(path, "r") as file:
            data = json.load(file)

        screens = data.get("screens", {})

        # Only keep enabled screens
        return {
            name: {
                "menu_location": info["menu_location"],
                "grid_type": info["grid_type"],
                "uses_menu_tab": info["uses_menu_tab"],
            }
            for name, info in screens.items()
            if info.get("enabled", False)
        }

    def go_to(self, screen: str):
        """
        Transitions to the given screen and initiates its associated process.

        Args:
            screen (str): Name of the screen to go to (must be in self.screen_mapping).
        """

        screen_data = self.screen_mapping[screen]
        menu_location = screen_data["menu_location"]
        grid_type = screen_data["grid_type"]
        uses_menu = screen_data["uses_menu_tab"]

        # Menu-free screens (like "Students" or "Student") require going Home.
        if not uses_menu:
            self.navigator.go_home()
        else:
            self.navigator.manage_menu_tab(True)

        print(f"🔄 Navigating to {screen}...")

        self.navigate_to_screen(
            menu_location=menu_location,
            in_menu_tab=uses_menu,
            ignore_page_check=not uses_menu,
        )

        new_screen = self.navigator.where_am_i()
        if new_screen == screen:
            self.process_screen(screen, grid_type)
            self.visited.add(screen)
            self.unvisited.discard(screen)

            if (
                screen == "Students"
                and "Student" in self.screen_mapping
                and "Student" not in self.visited
            ):
                self.go_to("Student")
        else:
            print(f"⚠️ Failed to navigate to {screen}.")

    def run(self) -> bool:
        """
        Runs the screen navigation flow until all target screens are processed.

        Returns:
            bool: True if all screens processed, False otherwise.
        """
        current = self.navigator.where_am_i()

        if current in self.screen_mapping:
            self.go_to(current)
        else:
            # If stuck on a page, reset to Home
            if self.navigator.at_page():
                self.navigator.go_home()

        # Continue with remaining screens
        for screen in self.screen_mapping:
            if screen not in self.visited:
                self.go_to(screen)

        # Final status
        if not self.unvisited:
            print("🎉 All screens completed.")
            return True
        else:
            print(f"❌ Incomplete: {self.unvisited}")
            return False

    def process_screen(self, screen_name: str, grid_type: str):
        """
        Handles what to do after navigating to a given screen.

        Args:
            screen_name (str): Name of the screen.
            grid_type (str): Grid category/type (used for matching).
        """
        if screen_name in ["Currencies"]:
            print("🔄 Getting Currencies...")
            get_currencies(self.navigator.adb_controller)

        if screen_name in ["Equipment", "Items"]:
            print(f"🔄 {screen_name}: Starting matching process...")
            startMatching(self.navigator.adb_controller, grid_type=grid_type)

        elif screen_name == "Students":
            print("🔄 Pressing First Student in the Student List.")
            self.navigate_to_screen(
                menu_location="first_student", in_menu_tab=False, ignore_page_check=True
            )

        elif screen_name == "Student":
            print("🔄 Getting Student Infos...")
            get_student_info(self.navigator.adb_controller)

    def navigate_to_screen(
        self, menu_location: str, in_menu_tab: bool, ignore_page_check: bool
    ):
        """
        Navigate to a specific page using the ADB controller.

        Args:
            menu_location (str): Button identifier (e.g., 'menu_items').
            in_menu_tab (bool): Whether this screen requires the menu tab to be opened and accessed.
            ignore_page_check (bool): Skip checking if currently on a page.
        """
        if not ignore_page_check and self.navigator.at_page():
            print("🔁 Currently on a page. Returning Home before proceeding...")
            self.navigator.go_home()
            time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER)

        # Proceed to target screen
        print(f"➡️ Tapping button for {menu_location}...")
        time.sleep(2.0 * Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER)

        self.navigator.go_to_page(location=menu_location, in_menu_tab=in_menu_tab)
        time.sleep(5.0 * Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER)
