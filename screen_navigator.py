import time
from dataclasses import dataclass
from typing import Optional

from area import Region
from config import Config
from locations.entrypoint import EntryPointButtons, EntryPointTitles
from locations.screens import Home, Page, StudentList
from utils.device.inputs.input_controller import InputController
from utils.ocr.extract import extract_text
from utils.ocr.matchers import match_image_using_file
from utils.ocr.preprocessor import preprocess_image_for_ocr
from utils.screen.screenshot_provider import ScreenshotProvider


@dataclass
class NavigationResult:
    success: bool
    screen_detected: str = ""
    error_msg: Optional[str] = None


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

        # Ensure background capture thread is running if provided
        if self.screencap and (
            not hasattr(self.screencap, "thread")
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

    def identify_screen(self) -> str:
        """
        Returns the detected title string or an empty string if not found.
        """
        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)
        image = self._get_screenshot()

        if image is None:
            return ""

        title_region = EntryPointTitles.PAGE.value

        title_crop = image[
            title_region.y : title_region.bottom,
            title_region.x : title_region.right,
        ]

        preprocessed, config = preprocess_image_for_ocr(title_crop, image_type="name")
        if preprocessed is None:
            return ""

        text = extract_text(preprocessed, config).replace("\r", "").replace("\n", " ")
        text = text.split()[0] if text.split() else ""
        known_screens = ["Items", "Equipment", "Students", "Student"]
        return text if text in known_screens else ""

    def ensure_at_home(self) -> NavigationResult:
        """
        Ensure device is on the Home screen. Returns result with verification.
        """
        if self.at_home():
            return NavigationResult(success=True, screen_detected="Home")

        button = self.determine_button("home")

        if button:
            self.input_controller.tap(
                int(button.random_point().x), int(button.random_point().y)
            )
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)

        time.sleep(1.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)

        if self.at_home():
            return NavigationResult(success=True, screen_detected="Home")
        return NavigationResult(success=False, error_msg="Failed to reach Home screen")

    def ensure_menu_state(self, should_open: bool) -> NavigationResult:
        """Open or close menu tab to match desired state."""
        current_open = self.is_menu_tab_open()
        print(f"is menu tab open?: {current_open}")
        if current_open == should_open:
            return NavigationResult(success=True, screen_detected="MenuStateOK")

        if should_open:
            print("Opening Menu Tab...")
            self.press_menu_tab()
        else:
            print("Closing Menu Tab (Pressing Home)...")
            self.ensure_at_home()

        time.sleep(1.0 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)
        return NavigationResult(success=True, screen_detected="MenuStateAdjusted")

    def navigate_to_target(self, location: str, in_menu_tab: bool) -> NavigationResult:
        """Navigate to a target button location with state verification."""
        button = self.determine_button(location)
        if not button:
            return NavigationResult(
                success=False, error_msg=f"Unknown button: {location}"
            )

        if in_menu_tab:
            res = self.ensure_menu_state(True)
            if not res.success:
                return res

        center = button.random_point()
        self.input_controller.tap(int(center.x), int(center.y))
        time.sleep(2.0 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)

        detected = self.identify_screen()
        return NavigationResult(success=bool(detected), screen_detected=detected)

    def press_menu_tab(self):
        """
        Tap the menu tab button to open the menu tab.
        """
        button: Region = self.determine_button("menu")
        if button:
            point = button.random_point(2)
            self.input_controller.tap(int(point.x), int(point.y))
            time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER)

    def is_menu_tab_open(self) -> bool:
        """
        Check if the menu tab is currently open by OCR on the menu tab region.
        Returns True if open, False otherwise.
        """
        image = self._get_screenshot()
        if image is None:
            return False

        menu_region = EntryPointTitles.MENU_TAB.value
        crop = image[
            menu_region.y : menu_region.bottom,
            menu_region.x : menu_region.right,
        ]
        preprocessed, config = preprocess_image_for_ocr(crop, image_type="name")
        if preprocessed is None:
            return False

        text = extract_text(preprocessed, config).replace("\r", "").replace("\n", " ")
        return text == "Menu Tab"

    def at_home(self, threshold: float = 0.45) -> bool:
        """
        Check if the user is currently at the home screen by image matching.
        Returns True if the menu button is detected.
        """

        img = self._get_screenshot()
        if img is None:
            return False

        crop = img[
            Home.MENU_BUTTON.y : Home.MENU_BUTTON.bottom,
            Home.MENU_BUTTON.x : Home.MENU_BUTTON.right,
        ]

        home_button_asset = r"assets\\images\\menu_button.png"
        return match_image_using_file(crop, home_button_asset, threshold)

    def at_page(self, threshold: float = 0.45) -> bool:
        """
        Check if the user is currently at the main page by image matching.
        Returns True if the home button is detected.
        """
        img = self._get_screenshot()
        if img is None:
            return False

        crop = img[
            Page.HOME_BUTTON.y : Page.HOME_BUTTON.bottom,
            Page.HOME_BUTTON.x : Page.HOME_BUTTON.right,
        ]

        page_button_asset = r"assets\\images\\home_button.png"
        return match_image_using_file(crop, page_button_asset, threshold)

    def determine_button(self, region: str) -> Optional[Region]:
        """
        Map a logical location name to its corresponding button Region object.
        Returns the Region or None if not found.
        """
        button_mapping = {
            "home": EntryPointButtons.HOME.value,
            "menu_students": EntryPointButtons.STUDENTS.value,
            "first_student": StudentList.FIRST_STUDENT,
            "menu": EntryPointButtons.MENU_TAB.value,
            "menu_equipment": EntryPointButtons.MENU_TAB_EQUIPMENT.value,
            "menu_items": EntryPointButtons.MENU_TAB_ITEMS.value,
            # Currencies doesn't need navigation, but added for safety
            "currencies": None,
        }
        return button_mapping.get(region, None)
