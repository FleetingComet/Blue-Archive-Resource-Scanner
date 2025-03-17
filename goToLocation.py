import time
import cv2
from area import Location, Region
from config import Config
from src.locations.screens import Home, Page, StudentList
from src.locations.entrypoint import EntryPointButtons, EntryPointTitles
from src.utils.preprocessor import preprocess_image_for_ocr
from src.utils.extract_text import extract_text
from src.utils.adb_controller import ADBController
from src.utils.matchers import match_image_using_file

screenshot_path = Config.get_screenshot_path()


def whereAmI(adb_controller: ADBController) -> str:
    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return None
    return searchTitle()


def searchTitle() -> str:
    if screenshot_path is None:
        return None

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.PAGE.value.y : EntryPointTitles.PAGE.value.bottom,
        EntryPointTitles.PAGE.value.x : EntryPointTitles.PAGE.value.right,
    ]

    preprocessed_crop, config = preprocess_image_for_ocr(
        title_crop_img, image_type="name"
    )
    if preprocessed_crop is None:
        return None

    text = extract_text(preprocessed_crop, config).replace("\r", "").replace("\n", " ")
    text = text.split()[0]  # only first detected text
    print(f"Current screen: {text}")
    # Students: Student List
    # Student: Student Info
    return text if text in ["Items", "Equipment", "Students", "Student"] else None


def determineButton(location: str) -> Location:
    button_mapping = {
        "home": EntryPointButtons.HOME.value,
        "menu_students": EntryPointButtons.STUDENTS.value,
        "first_student": StudentList.FIRST_STUDENT,
        "menu": EntryPointButtons.MENU_TAB.value,
        "menu_equipment": EntryPointButtons.MENU_TAB_EQUIPMENT.value,
        "menu_items": EntryPointButtons.MENU_TAB_ITEMS.value,
    }

    return button_mapping.get(location, None) if location in button_mapping else None


def goHome(adb_controller: ADBController):
    """Navigate to the home screen."""

    if button := determineButton("home"):
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")
        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)


def goToPage(adb_controller: ADBController, location: str, in_menu_tab=True):
    """Navigate to a specific page."""

    print(f"goToPage method: {location}")

    manage_menu_tab(adb_controller, in_menu_tab)

    if button := determineButton(location):
        print(f"goToPage method button: {button}")
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")
        return

def manage_menu_tab(adb_controller: ADBController, in_menu_tab: bool) -> None:
    """Manage menu tab state."""
    current_state = isMenuTabOpen(adb_controller)
    target_state = in_menu_tab
    sleep_duration = Config.WAIT_TIME_MULTIPLIER * 1.0

    if current_state == target_state:
        return

    action = "Opening" if target_state else "Closing"
    print(f"🔄 {action} Menu Tab...")
    
    try:
        if target_state:
            press_MenuTab(adb_controller)  # Open if not open
        else:
            goHome(adb_controller) # Close if open
            
        time.sleep(sleep_duration)
        
    except Exception as e:
        print(f"❌ Failed to manage menu tab: {str(e)}")
        raise

def press_MenuTab(adb_controller: ADBController):
    """Press the Menu Tab button."""

    if button := determineButton("menu"):
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")
        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
        return


def isMenuTabOpen(adb_controller: ADBController) -> bool:
    """Check if the Menu Tab is currently open."""

    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return False

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.MENU_TAB.value.y : EntryPointTitles.MENU_TAB.value.bottom,
        EntryPointTitles.MENU_TAB.value.x : EntryPointTitles.MENU_TAB.value.right,
    ]

    preprocessed_crop, config = preprocess_image_for_ocr(
        title_crop_img, image_type="name"
    )
    if preprocessed_crop is None:
        return False

    text = extract_text(preprocessed_crop, config).replace("\r", "").replace("\n", " ")

    return text == "Menu Tab"


def at_home(threshold=0.45) -> bool:
    """Check if the user is currently at home
    it will check for menu button

    Args:
        threshold: A float between 0 and 1 representing the minimum
                 similarity ratio required.

    Returns:
        bool: True if the menu button is detected, False otherwise.
    """
    home_region = Home.MENU_BUTTON
    home_button_asset = r"assets\images\menu_button.png"
    print("currently at home method")

    return match_where(home_region, home_button_asset, threshold)


def at_page(threshold=0.45) -> bool:
    page_region = Page.HOME_BUTTON
    page_button_asset = r"assets\images\home_button.png"
    return match_where(page_region, page_button_asset, threshold)


def match_where(region: Region, asset: str, threshold=0.8) -> bool:
    image = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    crop_img = image[region.y : region.bottom, region.x : region.right]
    # cv2.namedWindow("Image", cv2.WINDOW_AUTOSIZE)
    # cv2.imshow("Image", image)
    # cv2.waitKey(0)
    # cv2.imshow("Image", crop_img)
    # cv2.waitKey(0)

    return match_image_using_file(crop_img, asset, threshold)
