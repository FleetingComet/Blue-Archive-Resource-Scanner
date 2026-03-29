import time
from typing import Optional
from area import Location, Region
from config import Config
from locations.screens import Home, Page, StudentList
from locations.entrypoint import EntryPointButtons, EntryPointTitles
from utils.device.inputs.input_controller import InputController
from utils.ocr.preprocessor import preprocess_image_for_ocr
from utils.ocr.extract import extract_text
from utils.ocr.matchers import match_image_using_file
from utils.screen.screenshot_provider import ScreenshotProvider


class ScreenNavigator:
    def __init__(
        self,
        input_controller: InputController,
        screencap: Optional[ScreenshotProvider] = None,
    ):
        """
        Initialize the ScreenNavigator with an InputController and optional ScreenshotProvider.
        If no screencap is provided, a new one is created and started.
        """
        self.input_controller = input_controller
        self.screencap = screencap

        if (
            self.screencap
            and not hasattr(self.screencap, "thread")
            or (
                hasattr(self.screencap, "thread")
                and (
                    self.screencap.thread is None
                    or not self.screencap.thread.is_alive()
                )
            )
        ):
            if hasattr(self.screencap, "start"):
                self.screencap.start()

    def _get_screenshot(self):
        """Get screenshot from screencap or capture directly"""
        if self.screencap:
            return self.screencap.get_latest_screenshot()
        return self.input_controller.capture_screenshot()

    def where_am_i(self) -> str:
        """
        Detect the current screen by analyzing the latest screenshot.
        Returns the detected screen name (e.g., 'Items', 'Equipment', etc.) or an empty string if undetectable.
        """
        image = self._get_screenshot()
        if image is None:
            print("Failed to capture screenshot.")
            return ""
        return self.search_title(image)

    def search_title(self, image=None) -> str:
        """
        Extract the title from the provided screenshot (or latest if not provided).
        Returns the detected title string or an empty string if not found.
        """
        if image is None:
            image = self._get_screenshot()
        if image is None:
            return ""
        
        title_region = EntryPointTitles.PAGE.value

        title_crop_img = image[
            title_region.y : title_region.bottom,
            title_region.x : title_region.right,
        ]

        preprocessed_crop, config = preprocess_image_for_ocr(
            title_crop_img, image_type="name"
        )
        if preprocessed_crop is None:
            return ""
        text = (
            extract_text(preprocessed_crop, config).replace("\r", "").replace("\n", " ")
        )
        text = text.split()[0] if text.split() else ""
        print(f"Current screen: {text}")
        return text if text in ["Items", "Equipment", "Students", "Student"] else ""

    def determine_button(self, location: str) -> Optional[Location]:
        """
        Map a logical location name to its corresponding button Location object.
        Returns the Location or None if not found.
        """
        button_mapping = {
            "home": EntryPointButtons.HOME.value,
            "menu_students": EntryPointButtons.STUDENTS.value,
            "first_student": StudentList.FIRST_STUDENT,
            "menu": EntryPointButtons.MENU_TAB.value,
            "menu_equipment": EntryPointButtons.MENU_TAB_EQUIPMENT.value,
            "menu_items": EntryPointButtons.MENU_TAB_ITEMS.value,
        }
        return button_mapping.get(location, None)

    def go_home(self):
        """
        Navigate to the home screen by tapping the home button.
        """
        button = self.determine_button("home")
        if button:
            self.input_controller.tap(int(button.x), int(button.y))
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER)

    def go_to_page(self, location: str, in_menu_tab=True):
        """
        Navigate to a specific page by name.
        Optionally ensure the menu tab is open/closed before navigation.
        """
        print(f"goToPage method: {location}")
        self.manage_menu_tab(in_menu_tab)
        button = self.determine_button(location)
        if button:
            print(f"goToPage method button: {button}")
            self.input_controller.tap(int(button.x), int(button.y))
            return

    def manage_menu_tab(self, in_menu_tab: bool) -> None:
        """
        Ensure the menu tab is in the desired open/closed state.
        """
        current_state = self.is_menu_tab_open()
        target_state = in_menu_tab
        sleep_duration = (
            Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER * 1.0
        )
        if current_state == target_state:
            return
        action = "Opening" if target_state else "Closing"
        print(f"🔄 {action} Menu Tab...")
        try:
            if target_state:
                self.press_menu_tab()  # Open if not open
            else:
                self.go_home()  # Close if open
            time.sleep(sleep_duration)
        except Exception as e:
            print(f"❌ Failed to manage menu tab: {str(e)}")
            raise

    def press_menu_tab(self):
        """
        Tap the menu tab button to open the menu tab.
        """
        button = self.determine_button("menu")
        if button:
            self.input_controller.tap(int(button.x), int(button.y))
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER * Config.SCREEN_NAV_MULTIPLIER)
            return

    def is_menu_tab_open(self) -> bool:
        """
        Check if the menu tab is currently open by OCR on the menu tab region.
        Returns True if open, False otherwise.
        """
        image = self._get_screenshot()
        if image is None:
            print("Failed to capture screenshot.")
            return False
        
        menu_region = EntryPointTitles.MENU_TAB.value

        menu_crop_img = image[
            menu_region.y : menu_region.bottom,
            menu_region.x : menu_region.right,
        ]

        preprocessed_crop, config = preprocess_image_for_ocr(
            menu_crop_img, image_type="name"
        )
        if preprocessed_crop is None:
            return False
        text = (
            extract_text(preprocessed_crop, config).replace("\r", "").replace("\n", " ")
        )
        return text == "Menu Tab"

    def at_home(self, threshold=0.45) -> bool:
        """
        Check if the user is currently at the home screen by image matching.
        Returns True if the menu button is detected.
        """
        home_region = Home.MENU_BUTTON
        home_button_asset = r"assets\\images\\menu_button.png"
        print("currently at home method")
        return self.match_where(home_region, home_button_asset, threshold)

    def at_page(self, threshold=0.45) -> bool:
        """
        Check if the user is currently at the main page by image matching.
        Returns True if the home button is detected.
        """
        page_region = Page.HOME_BUTTON
        page_button_asset = r"assets\\images\\home_button.png"
        return self.match_where(page_region, page_button_asset, threshold)

    def match_where(self, region: Region, asset: str, threshold=0.8) -> bool:
        """
        Perform template matching in the given region of the latest screenshot against the provided asset image.
        Returns True if the match exceeds the threshold, False otherwise.
        """
        image = self._get_screenshot()
        if image is None:
            print("No screenshot available for matching.")
            return False
        crop_img = image[region.y : region.bottom, region.x : region.right]
        return match_image_using_file(crop_img, asset, threshold)
