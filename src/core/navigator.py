import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from locations.entrypoint import EntryPointButtons, EntryPointTitles
from locations.screens import Home, Page, StudentList
from src.core.area import Region
from src.core.config import Config
from src.utils.data.text_matcher import find_closest
from src.utils.device.interfaces import DeviceController
from src.utils.ocr.engine import extract_text
from src.utils.ocr.matchers import match_image_using_file
from src.utils.ocr.preprocessor import preprocess_image_for_ocr

logger = logging.getLogger("BA-Scanner")


@dataclass
class NavigationResult:
    success: bool
    screen_detected: str = ""
    error_msg: Optional[str] = None


class ScreenNavigator:
    def __init__(self, device: DeviceController):
        """
        Initialize the ScreenNavigator with an DeviceController.
        """
        self.device = device

    def _get_screenshot(self):
        """Get screenshot from DeviceController"""
        return self.device.capture_screenshot()

    def identify_screen(self) -> str:
        """
        Returns the detected title string or an empty string if not found.
        """
        time.sleep(
            0.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
        )
        image = self._get_screenshot()

        if image is None:
            return ""

        title_region = EntryPointTitles.PAGE.value

        title_crop = image[
            title_region.y : title_region.bottom,
            title_region.x : title_region.right,
        ]

        preprocessed = preprocess_image_for_ocr(title_crop, image_type="name")
        if preprocessed is None:
            return ""

        text = extract_text(preprocessed).replace("\r", "").replace("\n", " ")
        text = text.split()[0] if text.split() else ""
        known_screens = ["Items", "Equipment", "Students", "Student"]

        matched = find_closest(text, known_screens)
        return matched

    def ensure_at_home(self) -> NavigationResult:
        """
        Ensure device is on the Home screen. Returns result with verification.
        """
        if self.at_home():
            return NavigationResult(success=True, screen_detected="Home")

        button = self.determine_button("home")

        if button:
            self.device.tap(int(button.random_point().x), int(button.random_point().y))
            time.sleep(
                0.5
                * Config.WAIT_TIME_MULTIPLIER
                * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
            )

        time.sleep(
            1.5 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
        )

        if self.at_home():
            return NavigationResult(success=True, screen_detected="Home")
        return NavigationResult(success=False, error_msg="Failed to reach Home screen")

    def ensure_menu_state(self, should_open: bool) -> NavigationResult:
        """Open or close menu tab to match desired state."""
        current_open = self.is_menu_tab_open()
        logger.debug(f"is Menu Tab open?: {current_open}")
        if current_open == should_open:
            return NavigationResult(success=True, screen_detected="MenuStateOK")

        if should_open:
            logger.info("Opening Menu Tab...")
            self.press_menu_tab()
        else:
            logger.info("Closing Menu Tab (Pressing Home)...")
            self.ensure_at_home()

        time.sleep(
            1.0 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
        )
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
        self.device.tap(int(center.x), int(center.y))
        time.sleep(
            2.0 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
        )

        detected = self.identify_screen()
        return NavigationResult(success=bool(detected), screen_detected=detected)

    def press_menu_tab(self):
        """
        Tap the menu tab button to open the menu tab.
        """
        button: Region = self.determine_button("menu")
        if button:
            point = button.random_point(2)
            self.device.tap(int(point.x), int(point.y))
            time.sleep(
                0.8
                * Config.WAIT_TIME_MULTIPLIER
                * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
            )

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
        preprocessed = preprocess_image_for_ocr(crop, image_type="name")
        if preprocessed is None:
            return False

        text = (
            extract_text(preprocessed)
            .replace("\r", "")
            .replace("\n", " ")
            .strip()
            .lower()
        )

        return "menu" in text

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

        home_button_asset = Path("assets/images/menu_button.png")
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

        page_button_asset = Path("assets/images/home_button.png")
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
