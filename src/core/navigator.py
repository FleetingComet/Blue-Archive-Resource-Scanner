import logging
from dataclasses import dataclass
from pathlib import Path

from locations.entrypoint import EntryPointButtons, EntryPointTitles
from locations.screens import Home, Page, StudentList
from src.core.area import Region
from src.enums.ExtractionMode import ExtractionMode
from src.utils.data.text_matcher import find_closest
from src.utils.device.interfaces import DeviceController
from src.utils.ocr.matchers import find_template_location
from src.utils.ocr.ocr_helper import extract_text
from src.utils.ocr.preprocessor import preprocess_image_for_ocr
from src.utils.wait_utils import wait, wait_until

logger = logging.getLogger("BA-Scanner")


@dataclass
class NavigationResult:
    success: bool
    screen_detected: str = ""
    error_msg: str | None = None


class ScreenNavigator:

    def __init__(self, device: DeviceController):
        """
        Initialize the ScreenNavigator with an DeviceController.
        """
        self.device = device
        self.BUTTON_MAP = {
            "home": EntryPointButtons.HOME.value,
            "menu_students": EntryPointButtons.STUDENTS.value,
            "first_student": StudentList.FIRST_STUDENT,
            "menu": EntryPointButtons.MENU_TAB.value,
            "menu_equipment": EntryPointButtons.MENU_TAB_EQUIPMENT.value,
            "menu_items": EntryPointButtons.MENU_TAB_ITEMS.value,
            "currencies": None,
        }

        self.KNOWN_SCREENS = ["Items", "Equipment", "Students", "Student"]

    def _get_screenshot(self):
        """Get screenshot from DeviceController"""
        return self.device.capture_screenshot()

    def identify_screen(self) -> str:
        """
        Returns the detected title string (fuzzy matched) or an empty string if not found.
        """
        wait(0.5, nav=True)
        image = self._get_screenshot()

        if image is None:
            return ""

        title_region = EntryPointTitles.PAGE.value

        crop = image[
            title_region.y : title_region.bottom,
            title_region.x : title_region.right,
        ]

        preprocessed = preprocess_image_for_ocr(crop, mode=ExtractionMode.TEXT)
        if preprocessed is None:
            return ""

        text = extract_text(preprocessed).replace("\r", "").replace("\n", " ")
        text = text.split()[0] if text.split() else ""
        detected = find_closest(text, self.KNOWN_SCREENS)
        logger.debug(
            f"[dim]identify_screen: raw={text!r} -> matched={detected!r}[/dim]"
        )
        return detected

    def _check_asset_in_region(
        self, region: Region, asset_name: str, threshold: float
    ) -> bool:
        """Generic helper for template matching in a specific region."""
        img = self._get_screenshot()
        if img is None:
            return False

        crop = img[region.y : region.bottom, region.x : region.right]
        asset_path = Path(f"assets/images/{asset_name}.png")

        return find_template_location(crop, asset_path, threshold)

    def at_home(self) -> bool:
        """
        Check if the user is currently at the home screen by image matching.
        Returns True if the menu button is detected.
        """
        return self._check_asset_in_region(Home.MENU_REGION, "menu_button", 0.7)

    def at_page(self) -> bool:
        """
        Check if the user is currently at the main page by image matching.
        Returns True if the home button is detected.
        """
        return self._check_asset_in_region(Page.MENU_REGION, "home_button", 0.8)

    def ensure_at_home(self) -> NavigationResult:
        """
        Ensure device is on the Home screen.
        Repeatedly taps the home button until the Home screen is confirmed.
        """
        if self.at_home():
            return NavigationResult(success=True, screen_detected="Home")

        button = self.determine_button("home")

        max_attempts = 10

        for attempt in range(max_attempts):
            self.device.tap(int(button.random_point().x), int(button.random_point().y))
            # wait(2.0, nav=True)

            # if self.at_home():
            if wait_until(self.at_home, timeout=5.0, nav=True):
                logger.debug(
                    f"[green]ensure_at_home: reached Home on attempt {attempt}[/green]"
                )
                return NavigationResult(success=True, screen_detected="Home")

        logger.debug(f"[red]ensure_at_home: failed after {max_attempts} attempts[/red]")
        return NavigationResult(success=False, error_msg="Failed to reach Home")

    def ensure_menu_state(
        self, should_open: bool, max_attempts: int = 5
    ) -> NavigationResult:
        """Toggles the Menu Tab until the target state is reached."""
        if self.is_menu_tab_open() == should_open:
            return NavigationResult(success=True, screen_detected="MenuStateOK")

        action = "Opening" if should_open else "Closing"
        logger.info(f"[bold yellow]{action} Menu Tab[/bold yellow]")

        for _ in range(max_attempts):
            self.press_menu_tab()
            # wait(1.5, nav=True)

            # if self.is_menu_tab_open() == should_open:
            if wait_until(
                lambda: self.is_menu_tab_open() == should_open, timeout=3, nav=True
            ):
                logger.info(
                    f"[green]Successfully {'opened' if should_open else 'closed'} Menu Tab[/green]"
                )
                return NavigationResult(
                    success=True, screen_detected="MenuStateAdjusted"
                )

        error_msg = f"Failed to {'open' if should_open else 'close'} Menu Tab after {max_attempts} attempts"
        logger.error(f"[red]{error_msg}[/red]")
        return NavigationResult(success=False, error_msg=error_msg)

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

        p = button.random_point()
        self.device.tap(int(p.x), int(p.y))
        wait(2.0, nav=True)

        detected = self.identify_screen()
        logger.debug(
            f"[dim]navigate_to_target: wanted={location!r}, detected={detected!r}[/dim]"
        )
        return NavigationResult(success=bool(detected), screen_detected=detected)

    def press_menu_tab(self):
        """
        Tap the menu tab button to open the menu tab.
        """
        button: Region = self.determine_button("menu")
        if button:
            point = button.random_point(2)
            self.device.tap(int(point.x), int(point.y))
            # wait(0.8, nav=True)
            wait_until(self.is_menu_tab_open, timeout=3, nav=True)

    def is_menu_tab_open(self) -> bool:
        """
        Checks if 'Menu Tab' text is visible in the menu tab region.
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
        preprocessed = preprocess_image_for_ocr(crop, mode=ExtractionMode.TEXT)
        if preprocessed is None:
            return False

        text = (
            extract_text(preprocessed)
            .replace("\r", "")
            .replace("\n", " ")
            .strip()
            .lower()
        )
        is_open = "menu" in text
        logger.debug(f"[dim]is_menu_tab_open: text={text!r} -> {is_open}[/dim]")
        return is_open

    def determine_button(self, name: str) -> Region | None:
        return self.BUTTON_MAP.get(name)
